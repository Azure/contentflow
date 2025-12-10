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
    
logger = logging.getLogger(__name__)


class ContentRetrieverExecutor(ParallelExecutor):
    """
    Retrieve and download content from storage sources.
    
    This executor downloads content from blob storage or local files,
    optionally saving to temporary files for downstream processing.
    
    Configuration (settings dict):
        - include_content_bytes_as_field (bool): Include raw bytes in content.data
          Default: False
        - use_temp_file_for_content (bool): Save content to temp file
          Default: True
        - temp_folder (str): Folder for temp files
          Default: "./tmp/docproc_downloads"
        - max_concurrent (int): Maximum concurrent downloads
          Default: 1
        - continue_on_error (bool): Continue if a content item fails
          Default: True
        - blob_storage_account (str): Blob storage account name
          Default: None
        - blob_storage_account_credential_type (str): Credential type for blob storage
          Default: "default_azure_credential"
        - blob_storage_account_key (str): Credential key for blob storage
          Default: None
        - blob_container_name (str): Blob container name (for blob storage)
          Required for blob storage sources
        
    Example:
        ```python
        executor = ContentRetrieverExecutor(
            settings={
                "use_temp_file_for_content": True,
                "temp_folder": "./downloads",
                "max_concurrent": 5,
                "continue_on_error": True,
                "blob_storage_account": "myaccount",
                "blob_storage_account_credential_type": "default_azure_credential",
                "blob_container_name": "documents"
            },
        )
    
    Input:
        Content or List[Content] each with (ContentIdentifier) id containing:
        - canonical_id: Unique content ID
        - source_name: Source type ("blob", "local_file")
        - path: Path to content
    
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
        enabled: bool = True,
        fail_on_error: bool = False,
        debug_mode: bool = False,
        **kwargs
    ):
        super().__init__(
            id=id,
            settings=settings,
            enabled=enabled,
            fail_on_error=fail_on_error,
            debug_mode=debug_mode,
            **kwargs
        )
        
        # Extract configuration
        self.include_content_bytes = self.get_setting("include_content_bytes_as_field", default=False)
        self.use_temp_file = self.get_setting("use_temp_file_for_content", default=True)
        self.temp_folder = self.get_setting("temp_folder", default="./tmp/contentflow")
        
        self.blob_storage_account = self.get_setting("blob_storage_account", default=None)
        self.blob_storage_account_credential_type = self.get_setting("blob_storage_account_credential_type", default="default_azure_credential")
        self.blob_storage_account_key = self.get_setting("blob_storage_account_key", default=None)
        self.blob_container_name = self.get_setting("blob_container_name", default="documents")
        
        # Setup blob connector
        self.blob_connector: AzureBlobConnector = None
        if self.blob_storage_account:
            self.blob_connector = AzureBlobConnector('storage', settings={
                "account_name": self.blob_storage_account,
                "credential_type": self.blob_storage_account_credential_type,
                "credential_key": self.blob_storage_account_key
            })
        
        # Ensure temp folder exists
        if self.use_temp_file and self.temp_folder:
            os.makedirs(self.temp_folder, exist_ok=True)
        
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
            
            # Process based on source type
            if _identifier.source_type == "local_file":
                content_bytes, metadata = await self._retrieve_local_file(_identifier)
            elif _identifier.source_type == "azure_blob":
                content_bytes, metadata = await self._retrieve_blob(_identifier)
            else:
                raise ValueError(
                    f"Unsupported source type: {_identifier.source_name}. "
                    f"Supported: 'local_file', 'blob'"
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
            
            # Add metadata
            content.data['metadata'] = metadata
            
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
    
    async def _retrieve_local_file(
        self,
        content_id: ContentIdentifier
    ) -> tuple[bytes, Dict[str, Any]]:
        """Retrieve content from local file system."""
        
        local_path = content_id.path
        
        if not os.path.isfile(local_path):
            raise FileNotFoundError(
                f"Local file '{local_path}' not found for document '{content_id.canonical_id}'"
            )
        
        # Read file
        with open(local_path, 'rb') as f:
            content_bytes = f.read()
        
        # Build metadata
        stat = os.stat(local_path)
        metadata = {
            "source": "local_file",
            "path": local_path,
            "size": stat.st_size,
            "modified": stat.st_mtime
        }
        
        return content_bytes, metadata
    
    async def _retrieve_blob(
        self,
        content_id: ContentIdentifier
    ) -> tuple[bytes, Dict[str, Any]]:
        """Retrieve content from blob storage."""
        
        if not self.blob_connector:
            raise ValueError("BlobConnector not initialized. Cannot retrieve blob content.")
        
        # Ensure connector is initialized
        await self.blob_connector.initialize()
        
        # Download blob
        content_bytes = await self.blob_connector.download_blob(
            container_name=content_id.container or self.blob_container_name,
            blob_path=content_id.path
        )
        
        # Build metadata
        metadata = {
            "source": "blob",
            "container": content_id.container,
            "path": content_id.path,
            "size": len(content_bytes),
        }
        
        return content_bytes, metadata
    
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
