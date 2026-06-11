"""
Ingest API models for multipart document submission.
"""
from typing import Optional
from pydantic import BaseModel


class IngestPayload(BaseModel):
    """Form fields submitted by the client that become ProvidedDetails.json"""
    caseId: str
    firstName: str
    lastName: str
    mailingAddress: str
    dateOfBirth: str


class IngestResponse(BaseModel):
    """Response returned to client on successful ingest (202 Accepted)"""
    execution_id: str
    case_id: str
    status: str
    files_uploaded: int
    blob_prefix: str
    pipeline_id: str
    pipeline_name: str


class IngestResultsResponse(BaseModel):
    """Response for GET /ingest/{execution_id}/results"""
    execution_id: str
    status: str
    results: Optional[dict] = None
    error: Optional[str] = None
