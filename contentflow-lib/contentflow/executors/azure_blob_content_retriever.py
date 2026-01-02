"""Content retriever executor for downloading content from sources."""

from datetime import datetime
import logging
import os
import tempfile
from pathlib import Path
from typing import Dict, Any, List, Optional, Union

from . import ParallelExecutor
from ..models import Content, ContentIdentifier, ExecutorLogEntry
from ..connectors import AzureBlobConnector
    
logger = logging.getLogger("contentflow.executors.azure_blob_content_retriever")


class AzureBlobContentRetrieverExecutor(ParallelExecutor):
    """
    Retrieve and download content from azure blob storage sources.
    
    This executor downloads content from blob storage. Must be used as the next step after AzureBlobInputDiscoveryExecutor,
    optionally saving to temporary files for downstream processing.
    
    Configuration (settings dict):
        - include_content_bytes_as_field (bool): Include raw bytes in content.data
          Default: False
        - use_temp_file_for_content (bool): Save content to temp file
          Default: True
        - temp_folder (str): Folder for temp files
          Default: "./tmp/docproc_downloads"
        
        Also setting from ParallelExecutor and BaseExecutor apply.
        
    Example:
        ```python
        executor = AzureBlobContentRetrieverExecutor(
            settings={
                "use_temp_file_for_content": True,
                "temp_folder": "./downloads",
                "max_concurrent": 5,
                "continue_on_error": True
            },
        )
    
    Input:
        Content or List[Content] each with (ContentIdentifier) id containing:
        - canonical_id: Unique content ID of the blob
        - source_name: Source type ("azure_blob")
        - path: Path to blob file
        - container: Blob container name
    
    Output:
        Content or List[Content] with added fields:
        - data['temp_file_path']: Path to downloaded temp file (if use_temp_file_for_content)
        - data['content']: Raw content bytes (if include_content_bytes_as_field)
        - data['metadata']: Source metadata (size, content_type, etc.)
    """
    
    def __init__(
        self,
        id: str,
        settings: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        super().__init__(
            id=id,
            settings=settings,
            **kwargs
        )
        
        # Extract configuration
        self.include_content_bytes = self.get_setting("include_content_bytes_as_field", default=False)
        self.use_temp_file = self.get_setting("use_temp_file_for_content", default=True)
        self.temp_folder = self.get_setting("temp_folder", default="./tmp/contentflow")
        
        # Ensure temp folder exists
        if self.use_temp_file and self.temp_folder:
            os.makedirs(self.temp_folder, exist_ok=True)
        
        self._blob_connector_registry: Dict[str, AzureBlobConnector] = {}
        
        if self.debug_mode:
            logger.debug(
                f"ContentRetrieverExecutor with id {self.id} initialized: "
                f"temp_folder={self.temp_folder}, "
                f"use_temp_file={self.use_temp_file}"
            )
    
    async def process_content_item(
        self,
        content: Content
    ) -> Content:
        """Process a single content item to retrieve content.
           Implements the abstract method from ParallelExecutor.
        """
        
        _identifier: ContentIdentifier = content.id
        
        try:
            if not _identifier.canonical_id or not _identifier.source_name:
                raise ValueError(
                    "Document identifier must have canonical_id and source_name"
                )
            
            if self.debug_mode:
                logger.debug(
                    f"Retrieving content: {_identifier.canonical_id} "
                    f"from {_identifier.source_name}"
                )
            
            # Process only azure_blob source type
            if _identifier.source_type == "azure_blob":
                content_bytes = await self._retrieve_blob(_identifier)
            else:
                raise ValueError(
                    f"Unsupported source type: {_identifier.source_type}. "
                    f"Supported: 'azure_blob'"
                )
            
            # Write to temp file if configured
            if content_bytes and self.use_temp_file:
                temp_file_path = self._write_temp_file(_identifier, content_bytes)
                content.data['temp_file_path'] = temp_file_path
                
                if self.debug_mode:
                    logger.debug(f"Content written to: {temp_file_path}")
            
            # Include raw bytes if configured
            if self.include_content_bytes and content_bytes:
                content.data['content'] = content_bytes
            
            if self.debug_mode:
                logger.debug(
                    f"Retrieved {len(content_bytes) if content_bytes else 0} bytes "
                    f"for {_identifier.canonical_id}"
                )
        except Exception as e:
            logger.error(
                f"Failed to retrieve content for document "
                f"{_identifier.canonical_id if _identifier else 'unknown'}: {str(e)}",
                exc_info=True
            )
            logger.exception(e)
            
            # raise the exception to be handled upstream if needed
            raise
        
        return content
    
    async def _get_blob_connector_for_storage_account(self, storage_account_name: str) -> AzureBlobConnector:
        """Get or create AzureBlobConnector for given storage account."""
        
        # For simplicity, assume a single connector instance; in real code, manage multiple connectors as needed
        if storage_account_name not in self._blob_connector_registry:
            blob_connector = AzureBlobConnector(
                name="blob_input_connector",
                settings={
                    "account_name": storage_account_name,
                    "credential_type": "default_azure_credential",
                    "credential_key": ""
                }
            )
            await blob_connector.initialize()
            self._blob_connector_registry[storage_account_name] = blob_connector
        
        return self._blob_connector_registry[storage_account_name]
    
    async def _retrieve_blob(
        self,
        content_id: ContentIdentifier
    ) -> bytes:
        """Retrieve content from blob storage."""
        
        # validate content_id fields
        if not content_id.container or not content_id.path:
            raise ValueError("ContentIdentifier must have container and path for blob retrieval")
        
        # Get blob connector for this content item, extract storage account name from canonical_id
        storage_account_name = content_id.source_name if content_id.source_name else None
        if not storage_account_name:
            # try to parse from canonical_id assuming format "https://<account>.blob.core.windows.net/..."
            try:
                parts = content_id.canonical_id.split('.')
                storage_account_name = parts[0].split('//')[1]
                if not storage_account_name:
                    raise ValueError("Storage account name not found in canonical_id")
            except Exception:
                raise ValueError("Storage account name not found in content identifier source name or canonical_id")
        
        blob_connector: AzureBlobConnector = await self._get_blob_connector_for_storage_account(
            storage_account_name=storage_account_name
        )
        
        # Download blob
        content_bytes = await blob_connector.download_blob(
            container_name=content_id.container,
            blob_path=content_id.path
        )
        
        return content_bytes
    
    def _write_temp_file(
        self,
        content_id: ContentIdentifier,
        content: bytes
    ) -> str:
        """Write content to temporary file."""
        
        # Create safe filename from path
        safe_name = content_id.path.replace('/', '_').replace('\\', '_')
        temp_file_path = os.path.join(self.temp_folder, safe_name)
        
        # Write file
        with open(temp_file_path, 'wb') as f:
            f.write(content)
        
        return temp_file_path
