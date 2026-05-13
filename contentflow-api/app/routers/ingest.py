"""
Ingest router for multipart document submission API.
"""
import logging
import os
from typing import List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile

from app.models import IngestPayload, IngestResponse, ExecutionStatus
from app.services.pipeline_service import PipelineService
from app.services.pipeline_execution_service import PipelineExecutionService
from app.services.ingest_service import IngestService
from app.dependencies import (
    get_pipeline_service,
    get_pipeline_execution_service,
    get_ingest_service,
)
from app.settings import get_settings

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
    date_of_death: Optional[str] = Form("", alias="dateOfDeath"),
    father_first_name: Optional[str] = Form("", alias="fatherFirstName"),
    father_last_name: Optional[str] = Form("", alias="fatherLastName"),
    mother_first_name: Optional[str] = Form("", alias="motherFirstName"),
    mother_last_name: Optional[str] = Form("", alias="motherLastName"),
    # Pipeline
    pipeline_id: str = Form(..., description="Pipeline ID to execute"),
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

    # --- Validate pipeline ---
    pipeline = await pipeline_service.get_pipeline_by_id(pipeline_id)
    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline not found.")
    if not pipeline.enabled:
        raise HTTPException(status_code=400, detail="Pipeline is disabled.")

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
        dateOfDeath=date_of_death or "",
        fatherFirstName=father_first_name or "",
        fatherLastName=father_last_name or "",
        motherFirstName=mother_first_name or "",
        motherLastName=mother_last_name or "",
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
