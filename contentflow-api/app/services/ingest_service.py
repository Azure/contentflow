"""
Ingest service for handling document uploads and ProvidedDetails.json generation.
"""
import json
import logging
import re
from typing import List

from fastapi import UploadFile

from app.models import IngestPayload
from app.utils.blob_storage import BlobStorageService

logger = logging.getLogger("contentflow.api.services.ingest_service")

# Characters allowed in case_id: alphanumeric, hyphens, underscores
CASE_ID_PATTERN = re.compile(r"^[a-zA-Z0-9_\-]{1,128}$")


class IngestService:
    """Service for document ingestion: upload, ProvidedDetails generation, validation."""

    def __init__(self, blob_service: BlobStorageService):
        self.blob_service = blob_service

    def validate_case_id(self, case_id: str) -> None:
        """Validate case_id format. Raises ValueError on invalid format."""
        if not case_id or not case_id.strip():
            raise ValueError("case_id is required and cannot be empty.")
        if not CASE_ID_PATTERN.match(case_id):
            raise ValueError(
                f"Invalid case_id format: '{case_id}'. "
                "Only alphanumeric characters, hyphens, and underscores are allowed (max 128 chars)."
            )

    def sanitize_filename(self, filename: str) -> str:
        """Sanitize a filename to prevent path traversal and invalid characters."""
        # Remove any path components
        name = filename.replace("\\", "/").split("/")[-1]
        # Remove leading dots
        name = name.lstrip(".")
        # Remove null bytes
        name = name.replace("\x00", "")
        # Replace other problematic characters
        name = re.sub(r'[<>:"|?*]', "_", name)
        if not name:
            raise ValueError(f"Invalid filename after sanitization: '{filename}'")
        return name

    def generate_provided_details(self, payload: IngestPayload) -> bytes:
        """
        Generate ProvidedDetails.json content from the ingest payload.

        Uses the simple approach: all relevant fields are included in a single
        details block. The validation rules engine selects which fields to check
        per document type.
        """
        # Field names must match rules.json / FetchedDetails conventions
        # (PascalCase, matching Azure Content Understanding output fields)
        full_name = f"{payload.firstName} {payload.lastName}".strip()
        details = {
            "FirstName": payload.firstName,
            "LastName": payload.lastName,
            "FullName": full_name,
            "Address": payload.mailingAddress,
            "BirthDate": payload.dateOfBirth,
        }

        provided_details = {
            "caseId": payload.caseId,
            "details": details,
        }

        return json.dumps(provided_details, indent=2, ensure_ascii=False).encode("utf-8")

    async def upload_files(
        self, folder_prefix: str, files: List[UploadFile]
    ) -> List[str]:
        """
        Upload document files to blob storage under the given folder prefix.

        Returns list of uploaded blob paths.
        """
        uploaded_paths = []
        for file in files:
            sanitized_name = self.sanitize_filename(file.filename)
            blob_name = f"{folder_prefix}{sanitized_name}"
            content = await file.read()
            await self.blob_service.upload_file(
                file_content=content,
                blob_name=blob_name,
                content_type=file.content_type,
            )
            uploaded_paths.append(blob_name)
            logger.info(f"Uploaded file: {blob_name}")
        return uploaded_paths

    async def upload_provided_details(
        self, folder_prefix: str, content: bytes
    ) -> str:
        """Upload generated ProvidedDetails.json to the case folder."""
        blob_name = f"{folder_prefix}ProvidedDetails.json"
        await self.blob_service.upload_file(
            file_content=content,
            blob_name=blob_name,
            content_type="application/json",
        )
        logger.info(f"Uploaded ProvidedDetails.json: {blob_name}")
        return blob_name
