import json
import logging
import os
import re
from datetime import datetime, timezone
from itertools import islice
from typing import Any, Dict, Optional

from azure.storage.blob import BlobServiceClient
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel, Field

from app.dependencies import get_pipeline_execution_service, get_pipeline_service
from app.models import ExecutionStatus, PipelineExecution
from app.services.pipeline_execution_service import PipelineExecutionService
from app.services.pipeline_service import PipelineService
from app.settings import get_settings
from contentflow.utils import get_azure_credential

router = APIRouter(prefix="/sarsp", tags=["sarsp"])
logger = logging.getLogger("contentflow.api.routers.sarsp")

CASE_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]{2,64}$")
NEW_LICENSE_CONTAINER = "sql-fetch-data"
RENEWAL_LICENSE_CONTAINER = "farmacia-nueva-renewal"


class StartCaseValidationRequest(BaseModel):
    pipeline_id: Optional[str] = Field(default=None, description="Optional pipeline id override")
    pipeline_name: Optional[str] = Field(default=None, description="Optional pipeline name override")
    configuration: Optional[Dict[str, Any]] = Field(default=None)


class StartCaseValidationResponse(BaseModel):
    case_id: str
    execution_id: str
    status: str
    message: str


class CaseExecutionStatusResponse(BaseModel):
    case_id: str
    execution_id: str
    status: str
    platform_status: str
    message: str
    recommendation: Optional[str] = None
    confidence: Optional[float] = None
    completed_at: Optional[str] = None
    checks: list[Dict[str, Any]] = Field(default_factory=list)
    missing_documents: list[Dict[str, Any]] = Field(default_factory=list)
    findings: list[Dict[str, Any]] = Field(default_factory=list)
    results_available: bool = False
    report: Optional[Dict[str, Any]] = None


def _normalize_case_id(case_id: str) -> str:
    normalized = case_id.strip().upper()
    if not CASE_ID_PATTERN.match(normalized):
        raise HTTPException(status_code=400, detail="Invalid case_id format")
    return normalized


def _render_template(template: str, *, case_id: str, execution_id: Optional[str] = None) -> str:
    rendered = template.replace("{caseId}", case_id)
    rendered = rendered.replace("{case_id}", case_id)
    if execution_id:
        rendered = rendered.replace("{executionId}", execution_id)
        rendered = rendered.replace("{execution_id}", execution_id)
    return rendered


def _resolve_case_prefix(case_id: str, license_type: Optional[str], default_template: str) -> str:
    """Resolve the source prefix for a case based on requested license type."""
    normalized_license = (license_type or "").strip().lower()
    if normalized_license == "new":
        new_case_id = case_id if case_id.startswith("SALUD-") else f"SALUD-{case_id}"
        return f"input/{new_case_id}/"
    if normalized_license == "renewal":
        return f"input/{case_id}/"
    return _render_template(default_template, case_id=case_id)


def _resolve_case_container(license_type: Optional[str], default_container: str) -> str:
    normalized_license = (license_type or "").strip().lower()
    if normalized_license == "new":
        return NEW_LICENSE_CONTAINER
    if normalized_license == "renewal":
        return RENEWAL_LICENSE_CONTAINER
    return default_container


def _resolve_case_status(execution: PipelineExecution) -> str:
    # Execution status may be an ExecutionStatus enum or a raw string.
    status = (
        execution.status.value.lower()
        if isinstance(execution.status, ExecutionStatus)
        else str(execution.status).lower()
    )
    if status == ExecutionStatus.PENDING.value:
        return "Queued"
    if status == ExecutionStatus.RUNNING.value:
        for event in execution.events[-40:]:
            signal = f"{event.event_type or ''} {event.executor_id or ''}".lower()
            if "validat" in signal or "rule" in signal or "check" in signal:
                return "Validating"
        return "Running"
    if status == ExecutionStatus.COMPLETED.value:
        return "Completed"
    if status == ExecutionStatus.FAILED.value:
        return "Failed"
    if status == ExecutionStatus.CANCELLED.value:
        return "Cancelled"
    return "Queued"


def _extract_report_from_execution_outputs(outputs: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if not outputs:
        return None

    if isinstance(outputs, dict) and isinstance(outputs.get("report"), dict):
        return outputs.get("report")

    if isinstance(outputs, dict) and isinstance(outputs.get("results"), dict):
        return outputs.get("results")

    return None


def _collect_blob_candidates(report: Dict[str, Any]) -> list[str]:
    candidates: list[str] = []
    for key, value in report.items():
        if not isinstance(value, str):
            continue
        lowered_key = key.lower()
        lowered_value = value.lower()
        if "blob" in lowered_key and lowered_value.endswith(".json"):
            candidates.append(value)
        elif lowered_key.endswith("_path") and lowered_value.endswith(".json"):
            candidates.append(value)
    return candidates


def _get_blob_service_client(account_name: str) -> BlobServiceClient:
    account_url = f"https://{account_name}.blob.core.windows.net"
    return BlobServiceClient(account_url=account_url, credential=get_azure_credential())


def _case_prefix_exists(account_name: str, container_name: str, prefix: str) -> bool:
    blob_client = _get_blob_service_client(account_name)
    container_client = blob_client.get_container_client(container_name)
    blobs = container_client.list_blobs(name_starts_with=prefix)
    return any(islice(blobs, 1))


def _download_json_blob(account_name: str, container_name: str, blob_name: str) -> Optional[Dict[str, Any]]:
    blob_client = _get_blob_service_client(account_name)
    blob = blob_client.get_blob_client(container=container_name, blob=blob_name)
    if not blob.exists():
        return None

    payload = blob.download_blob().readall()
    return json.loads(payload.decode("utf-8"))


def _load_report(
    *,
    case_id: str,
    execution_id: str,
    execution: PipelineExecution,
    results_account_name: str,
    results_container_name: str,
    results_blob_template: str,
    results_prefix_template: str,
) -> Optional[Dict[str, Any]]:
    inline_report = _extract_report_from_execution_outputs(execution.outputs)
    if inline_report:
        return inline_report

    if execution.outputs:
        for candidate in _collect_blob_candidates(execution.outputs):
            try:
                report = _download_json_blob(results_account_name, results_container_name, candidate)
                if report:
                    return report
            except Exception:
                logger.warning("Failed reading candidate report blob '%s'", candidate, exc_info=True)

    execution_case_prefix = ""
    if isinstance(execution.configuration, dict):
        execution_case_prefix = str(execution.configuration.get("case_prefix") or "").strip()
    if execution_case_prefix:
        try:
            blob_client = _get_blob_service_client(results_account_name)
            container_client = blob_client.get_container_client(results_container_name)
            blobs = list(islice(container_client.list_blobs(name_starts_with=execution_case_prefix), 40))
            for blob in blobs:
                if blob.name.lower().endswith("results.json"):
                    report = _download_json_blob(results_account_name, results_container_name, blob.name)
                    if report:
                        return report
        except Exception:
            logger.debug("No result report found under execution case prefix '%s'", execution_case_prefix)

    rendered_blob = _render_template(results_blob_template, case_id=case_id, execution_id=execution_id)
    try:
        report = _download_json_blob(results_account_name, results_container_name, rendered_blob)
        if report:
            return report
    except Exception:
        logger.debug("Result blob not available at template path '%s'", rendered_blob)

    rendered_prefix = _render_template(results_prefix_template, case_id=case_id, execution_id=execution_id)
    try:
        blob_client = _get_blob_service_client(results_account_name)
        container_client = blob_client.get_container_client(results_container_name)
        blobs = list(islice(container_client.list_blobs(name_starts_with=rendered_prefix), 40))
        for blob in blobs:
            if blob.name.lower().endswith("results.json"):
                report = _download_json_blob(results_account_name, results_container_name, blob.name)
                if report:
                    return report
    except Exception:
        logger.debug("No result report found under prefix '%s'", rendered_prefix)

    return None


async def _resolve_pipeline(
    request: StartCaseValidationRequest,
    pipeline_service: PipelineService,
) -> tuple[str, Any]:
    configured_id = os.getenv("SARSP_PIPELINE_ID", "").strip()
    configured_name = os.getenv("SARSP_PIPELINE_NAME", "").strip()

    pipeline_id = request.pipeline_id or configured_id
    pipeline_name = request.pipeline_name or configured_name

    pipeline = None
    if pipeline_id:
        pipeline = await pipeline_service.get_pipeline_by_id(pipeline_id)
    if not pipeline and pipeline_name:
        pipeline = await pipeline_service.get_pipeline_by_name(pipeline_name)

    if not pipeline:
        raise HTTPException(
            status_code=404,
            detail="No SARSP pipeline found. Set SARSP_PIPELINE_ID or SARSP_PIPELINE_NAME and ensure the pipeline exists.",
        )

    return pipeline.id, pipeline


@router.post("/cases/{case_id}/validate", response_model=StartCaseValidationResponse)
async def start_case_validation(
    case_id: str,
    request: StartCaseValidationRequest,
    background_tasks: BackgroundTasks,
    pipeline_service: PipelineService = Depends(get_pipeline_service),
    execution_service: PipelineExecutionService = Depends(get_pipeline_execution_service),
):
    normalized_case_id = _normalize_case_id(case_id)
    app_settings = get_settings()

    storage_account_name = os.getenv("SARSP_INPUT_STORAGE_ACCOUNT", app_settings.BLOB_STORAGE_ACCOUNT_NAME).strip()
    default_container = os.getenv("SARSP_INPUT_CONTAINER", RENEWAL_LICENSE_CONTAINER).strip()
    input_prefix_template = os.getenv("SARSP_INPUT_PREFIX_TEMPLATE", "input/{caseId}/").strip()
    requested_license_type = (
        str((request.configuration or {}).get("license_type")).strip().lower()
        if (request.configuration or {}).get("license_type") is not None
        else None
    )
    container_name = _resolve_case_container(requested_license_type, default_container)

    if not storage_account_name:
        raise HTTPException(status_code=500, detail="Storage account is not configured")

    input_prefix = _resolve_case_prefix(normalized_case_id, requested_license_type, input_prefix_template)
    if not _case_prefix_exists(storage_account_name, container_name, input_prefix):
        raise HTTPException(
            status_code=404,
            detail=f"No source documents found for case '{normalized_case_id}' under '{container_name}/{input_prefix}'",
        )

    _, pipeline = await _resolve_pipeline(request, pipeline_service)

    if not pipeline.enabled:
        raise HTTPException(status_code=400, detail="Configured SARSP pipeline is disabled")

    execution_configuration = {
        **(request.configuration or {}),
        "case_id": normalized_case_id,
        "case_number": normalized_case_id,
        "case_prefix": input_prefix,
        "case_container": container_name,
        "requested_at": datetime.now(timezone.utc).isoformat(),
    }

    execution_inputs = {
        "case_id": normalized_case_id,
        "case_number": normalized_case_id,
        "blob_account": storage_account_name,
        "blob_container": container_name,
        "blob_prefix": input_prefix,
    }

    execution = await execution_service.create_execution(
        pipeline=pipeline,
        inputs=execution_inputs,
        configuration=execution_configuration,
        created_by="sarsp-case-assistant",
    )

    background_tasks.add_task(
        execution_service.start_execution,
        execution_id=execution.id,
        pipeline=pipeline,
        inputs=execution_inputs,
        configuration=execution_configuration,
        created_by="sarsp-case-assistant",
    )

    return StartCaseValidationResponse(
        case_id=normalized_case_id,
        execution_id=execution.id,
        status="Queued",
        message=f"Pipeline execution started for case {normalized_case_id}",
    )


@router.get("/cases/{case_id}/executions/{execution_id}", response_model=CaseExecutionStatusResponse)
async def get_case_validation_status(
    case_id: str,
    execution_id: str,
    execution_service: PipelineExecutionService = Depends(get_pipeline_execution_service),
):
    normalized_case_id = _normalize_case_id(case_id)
    app_settings = get_settings()

    execution = await execution_service.get_execution(execution_id)
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")

    execution_case_id = str((execution.inputs or {}).get("case_id", "")).upper()
    if execution_case_id and execution_case_id != normalized_case_id:
        raise HTTPException(status_code=400, detail="Execution does not belong to the requested case_id")

    case_status = _resolve_case_status(execution)
    response = CaseExecutionStatusResponse(
        case_id=normalized_case_id,
        execution_id=execution_id,
        status=case_status,
        platform_status=str(execution.status),
        message="Execution in progress" if case_status in ["Queued", "Running", "Validating"] else "Execution finished",
        completed_at=execution.completed_at,
        results_available=False,
    )

    if case_status not in ["Completed", "Failed", "Cancelled"]:
        return response

    if case_status in ["Failed", "Cancelled"]:
        response.message = execution.error or f"Execution {case_status.lower()}"
        return response

    results_account_name = os.getenv("SARSP_RESULTS_STORAGE_ACCOUNT", app_settings.BLOB_STORAGE_ACCOUNT_NAME).strip()
    execution_container = ""
    if isinstance(execution.configuration, dict):
        execution_container = str(execution.configuration.get("case_container") or "").strip()
    results_container_name = execution_container or os.getenv(
        "SARSP_RESULTS_CONTAINER",
        os.getenv("SARSP_INPUT_CONTAINER", RENEWAL_LICENSE_CONTAINER),
    ).strip()
    results_blob_template = os.getenv("SARSP_RESULTS_BLOB_TEMPLATE", "results/{caseId}/results.json").strip()
    results_prefix_template = os.getenv("SARSP_RESULTS_PREFIX_TEMPLATE", "results/{caseId}/").strip()

    report = _load_report(
        case_id=normalized_case_id,
        execution_id=execution_id,
        execution=execution,
        results_account_name=results_account_name,
        results_container_name=results_container_name,
        results_blob_template=results_blob_template,
        results_prefix_template=results_prefix_template,
    )

    if not report:
        response.message = "Execution completed, awaiting results report publication"
        return response

    response.results_available = True
    response.report = report
    response.message = "Execution completed"

    recommendation = report.get("recommendation")
    if isinstance(recommendation, str):
        response.recommendation = recommendation

    confidence = report.get("confidence")
    if isinstance(confidence, (int, float)):
        response.confidence = float(confidence)

    checks = report.get("checks")
    if isinstance(checks, list):
        response.checks = [item for item in checks if isinstance(item, dict)]

    missing_documents = report.get("missingDocuments") or report.get("missing_documents")
    if isinstance(missing_documents, list):
        response.missing_documents = [item for item in missing_documents if isinstance(item, dict)]

    findings = report.get("findings")
    if isinstance(findings, list):
        response.findings = [item for item in findings if isinstance(item, dict)]

    document_results = report.get("documentResults") or report.get("document_results")
    if isinstance(document_results, list):
        for document in document_results:
            if not isinstance(document, dict):
                continue

            document_status = str(document.get("status", "info")).lower()
            finding_status = {
                "passed": "Accepted",
                "failed": "Needs Correction",
                "exempt": "Accepted",
                "info": "Accepted",
            }.get(document_status, "Needs Correction")

            rule_results = document.get("ruleResults") or document.get("rule_results") or []
            failed_rules = [
                rule for rule in rule_results
                if isinstance(rule, dict) and str(rule.get("result", "")).lower() in {"fail", "failed"}
            ]
            details = []
            for rule in failed_rules:
                message = rule.get("message_en") or rule.get("message") or rule.get("correction")
                if message:
                    details.append(str(message))

            response.findings.append({
                "document": document.get("filename") or document.get("documentType") or "Unspecified document",
                "status": finding_status,
                "finding": "; ".join(details) or (
                    "Document passed all applicable validation rules."
                    if finding_status == "Accepted"
                    else "Document requires correction."
                ),
                "guidance": "; ".join(
                    str(rule.get("correction")) for rule in failed_rules if rule.get("correction")
                ) or "No correction required.",
            })

            for rule in rule_results:
                if not isinstance(rule, dict):
                    continue
                rule_result = str(rule.get("result", "")).lower()
                if rule_result not in {"pass", "passed", "fail", "failed"}:
                    continue
                response.checks.append({
                    "name": rule.get("rule_id") or "Validation rule",
                    "result": "Passed" if rule_result in {"pass", "passed"} else "Failed",
                    "detail": rule.get("message_en") or rule.get("correction") or "Rule evaluated.",
                })

    return response
