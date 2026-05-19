"""
Ingest router for multipart document submission API.
"""
import json
import logging
import os
from typing import List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from azure.core.exceptions import ResourceNotFoundError

from app.models import IngestPayload, IngestResponse, IngestResultsResponse, ExecutionStatus
from app.services.pipeline_service import PipelineService
from app.services.pipeline_execution_service import PipelineExecutionService
from app.services.ingest_service import IngestService
from app.dependencies import (
    get_pipeline_service,
    get_pipeline_execution_service,
    get_ingest_service,
)
from app.settings import get_settings
from app.utils.blob_storage import BlobStorageService, get_blob_storage_service

logger = logging.getLogger("contentflow.api.routers.ingest")

router = APIRouter(prefix="/ingest", tags=["ingest"])


@router.post("/", response_model=IngestResponse, status_code=202)
async def ingest_documents(
    background_tasks: BackgroundTasks,
    # Payload fields
    case_id: str = Form(..., alias="caseId", description="Client's unique case identifier"),
    first_name: str = Form(..., alias="firstName"),
    last_name: str = Form(..., alias="lastName"),
    mailing_address: str = Form(..., alias="mailingAddress"),
    date_of_birth: str = Form(..., alias="dateOfBirth"),
    # Files
    files: List[UploadFile] = File(..., description="Document files to process"),
    # Dependencies
    pipeline_service: PipelineService = Depends(get_pipeline_service),
    execution_service: PipelineExecutionService = Depends(get_pipeline_execution_service),
    ingest_service: IngestService = Depends(get_ingest_service),
):
    """
    Submit documents for processing through a ContentFlow pipeline.

    Accepts multipart form data with case details and document files.
    Generates ProvidedDetails.json from the payload, uploads everything
    to blob storage, and triggers the pipeline.

    Returns 202 Accepted with an execution_id for polling.
    """
    settings = get_settings()

    # --- Validate case_id ---
    try:
        ingest_service.validate_case_id(case_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # --- Validate files ---
    if not files:
        raise HTTPException(status_code=400, detail="At least one file is required.")

    if len(files) > settings.INGEST_MAX_FILE_COUNT:
        raise HTTPException(
            status_code=400,
            detail=f"Too many files. Maximum allowed: {settings.INGEST_MAX_FILE_COUNT}",
        )

    allowed_extensions = settings.INGEST_ALLOWED_EXTENSIONS
    max_file_bytes = settings.INGEST_MAX_FILE_SIZE_MB * 1024 * 1024
    max_total_bytes = settings.INGEST_MAX_TOTAL_SIZE_MB * 1024 * 1024
    total_size = 0

    for f in files:
        # Validate extension
        fname = f.filename or ""
        ext = os.path.splitext(fname)[1].lower()
        if ext not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"File type '{ext}' not allowed for file '{fname}'. Allowed: {allowed_extensions}",
            )
        # Validate size (if known)
        if f.size is not None:
            if f.size > max_file_bytes:
                raise HTTPException(
                    status_code=413,
                    detail=f"File '{fname}' exceeds maximum size of {settings.INGEST_MAX_FILE_SIZE_MB} MB.",
                )
            total_size += f.size

    if total_size > max_total_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"Total upload size exceeds maximum of {settings.INGEST_MAX_TOTAL_SIZE_MB} MB.",
        )

    # --- Resolve pipeline by name (abstracted from client) ---
    pipeline_name = settings.INGEST_PIPELINE_NAME
    pipeline = await pipeline_service.get_pipeline_by_name(pipeline_name)
    if not pipeline:
        logger.error(f"Ingest pipeline not found by name: '{pipeline_name}'")
        raise HTTPException(
            status_code=503,
            detail="Processing pipeline is not available. Please contact support.",
        )
    if not pipeline.enabled:
        raise HTTPException(
            status_code=503,
            detail="Processing pipeline is temporarily disabled. Please try again later.",
        )

    # --- Create execution record first (to get execution_id for folder name) ---
    try:
        execution = await execution_service.create_execution(
            pipeline=pipeline,
            inputs={},  # will be updated after folder name is determined
            created_by=None,
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to create execution record: {e}"
        )

    execution_id = execution.id
    folder_prefix = f"input/{case_id}_{execution_id}/"

    # --- Build payload model ---
    payload = IngestPayload(
        caseId=case_id,
        firstName=first_name,
        lastName=last_name,
        mailingAddress=mailing_address,
        dateOfBirth=date_of_birth,
    )

    # --- Upload files and ProvidedDetails.json ---
    try:
        # Generate and upload ProvidedDetails.json
        provided_details_bytes = ingest_service.generate_provided_details(payload)
        await ingest_service.upload_provided_details(folder_prefix, provided_details_bytes)

        # Upload document files
        uploaded_paths = await ingest_service.upload_files(folder_prefix, files)
    except Exception as e:
        # Mark execution as failed if upload fails
        await execution_service.update_execution_status(
            execution_id, ExecutionStatus.FAILED, error=f"File upload failed: {e}"
        )
        raise HTTPException(status_code=500, detail=f"File upload failed: {e}")

    # --- Update execution inputs with case_prefix ---
    try:
        exec_record = await execution_service.get_execution(execution_id)
        if exec_record:
            exec_record.inputs = {
                "case_id": case_id,
                "case_prefix": folder_prefix,
                "execution_id": execution_id,
            }
            await execution_service.update(
                exec_record.model_dump(by_alias=True, exclude_none=False)
            )
    except Exception as e:
        logger.warning(f"Failed to update execution inputs: {e}")

    # --- Trigger pipeline execution in background ---
    background_tasks.add_task(
        execution_service.start_execution,
        execution_id=execution_id,
        pipeline=pipeline,
    )

    return IngestResponse(
        execution_id=execution_id,
        case_id=case_id,
        status="pending",
        files_uploaded=len(uploaded_paths),
        blob_prefix=folder_prefix,
        pipeline_id=pipeline.id,
        pipeline_name=pipeline.name,
    )


@router.get("/{execution_id}/results", response_model=IngestResultsResponse)
async def get_ingest_results(
    execution_id: str,
    execution_service: PipelineExecutionService = Depends(get_pipeline_execution_service),
):
    """
    Retrieve validation results for a completed ingest execution.

    - **200**: Execution completed — returns results.json content.
    - **202**: Execution is still running — retry later.
    - **404**: Execution ID not found.
    - **422**: Execution failed — returns error details.
    """
    # --- Validate execution_id format ---
    if not execution_id or not execution_id.strip():
        raise HTTPException(status_code=400, detail="execution_id is required.")

    # --- Fetch execution record from Cosmos DB ---
    try:
        execution = await execution_service.get_execution(execution_id)
    except Exception as e:
        logger.error(f"Failed to look up execution {execution_id}: {e}")
        raise HTTPException(status_code=500, detail="Unable to retrieve execution record.")

    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found.")

    # --- Handle non-terminal states ---
    status = execution.status
    if isinstance(status, ExecutionStatus):
        status = status.value

    if status in (ExecutionStatus.PENDING.value, ExecutionStatus.RUNNING.value):
        return JSONResponse(
            status_code=202,
            content=IngestResultsResponse(
                execution_id=execution_id,
                status=status,
            ).model_dump(),
        )

    # --- Handle failed / cancelled ---
    if status in (ExecutionStatus.FAILED.value, ExecutionStatus.CANCELLED.value):
        raise HTTPException(
            status_code=422,
            detail={
                "execution_id": execution_id,
                "status": status,
                "error": execution.error or "Execution did not complete successfully.",
            },
        )

    # --- Execution completed — download results.json from blob ---
    case_prefix = (execution.inputs or {}).get("case_prefix")
    if not case_prefix:
        raise HTTPException(
            status_code=500,
            detail="Execution record is missing case_prefix — cannot locate results.",
        )

    results_blob_path = f"{case_prefix}results.json"

    settings = get_settings()
    try:
        blob_service = await get_blob_storage_service(
            account_name=settings.BLOB_STORAGE_ACCOUNT_NAME,
            container_name=settings.BLOB_STORAGE_CONTAINER_NAME,
        )
        raw_bytes = await blob_service.download_file(results_blob_path)
        results_data = json.loads(raw_bytes)
    except ResourceNotFoundError:
        raise HTTPException(
            status_code=404,
            detail=f"Results file not found at {results_blob_path}. The pipeline may not have produced results.",
        )
    except json.JSONDecodeError:
        logger.error(f"Malformed results.json at {results_blob_path}")
        raise HTTPException(
            status_code=500,
            detail="Results file exists but contains invalid JSON.",
        )
    except Exception as e:
        logger.error(f"Error downloading results for {execution_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve results from storage.",
        )

    return IngestResultsResponse(
        execution_id=execution_id,
        status=status,
        results=results_data,
    )
