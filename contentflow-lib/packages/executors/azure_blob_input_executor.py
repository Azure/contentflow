"""Azure Blob Input executor for discovering and listing content files from blob storage."""

from datetime import datetime
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Union

from agent_framework import WorkflowContext

from .base import BaseExecutor
from ..models import Content, ContentIdentifier, ExecutorLogEntry
from ..connectors import BlobConnector

logger = logging.getLogger(__name__)


class AzureBlobInputExecutor(BaseExecutor):
    """
    Discover and list content files from Azure Blob Storage.
    
    This executor scans Azure Blob Storage containers to discover content files,
    creating Content objects for each discovered blob. It supports filtering by
    prefix, file extensions, traversal depth, and result limits.
    
    Configuration (settings dict):
        - blob_storage_account (str): Azure Blob Storage account name
          Required: True
        - blob_storage_credential_type (str): Credential type for blob storage
          Default: "default_azure_credential"
          Options: "default_azure_credential", "azure_key_credential"
        - blob_storage_account_key (str): Storage account key (if using azure_key_credential)
          Default: None
        - blob_container_name (str): Container name to scan
          Required: True
        - prefix (str): Blob path prefix filter (e.g., "documents/2024/")
          Default: "" (root)
        - file_extensions (list): File extensions to include (e.g., [".pdf", ".docx", ".txt"])
          Default: [] (all files)
        - max_depth (int): Maximum folder depth to traverse (0 = unlimited)
          Default: 0 (unlimited)
        - max_results (int): Maximum number of blobs to return (0 = unlimited)
          Default: 0 (unlimited)
        - include_metadata (bool): Include blob metadata in content data
          Default: True
        - sort_by (str): Sort results by field
          Default: "name"
          Options: "name", "last_modified", "size"
        - sort_ascending (bool): Sort in ascending order
          Default: True
        - min_size_bytes (int): Minimum file size in bytes (0 = no minimum)
          Default: 0
        - max_size_bytes (int): Maximum file size in bytes (0 = no maximum)
          Default: 0
        - modified_after (str): Only include files modified after this date (ISO format)
          Default: None
        - modified_before (str): Only include files modified before this date (ISO format)
          Default: None
    
    Example:
        ```yaml
        - id: blob_input
          type: azure_blob_input
          settings:
            blob_storage_account: "${STORAGE_ACCOUNT}"
            blob_storage_credential_type: "default_azure_credential"
            blob_container_name: "documents"
            prefix: "invoices/2024/"
            file_extensions: [".pdf", ".docx"]
            max_depth: 3
            max_results: 100
            min_size_bytes: 1024
            sort_by: "last_modified"
            sort_ascending: false
        ```
    
    Input:
        None (this is typically a source/input executor)
    
    Output:
        List[Content] with ContentIdentifier for each discovered blob:
        - id.canonical_id: Unique blob identifier
        - id.source_name: "blob"
        - id.path: Full blob path
        - data['blob_name']: Blob name
        - data['blob_path']: Full blob path
        - data['container_name']: Container name
        - data['size']: File size in bytes
        - data['last_modified']: Last modified timestamp
        - data['content_type']: Content type
        - data['metadata']: Blob metadata (if include_metadata is True)
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
        
        # Blob storage configuration
        self.blob_storage_account = self.get_setting("blob_storage_account", required=True)
        self.blob_storage_credential_type = self.get_setting(
            "blob_storage_credential_type", 
            default="default_azure_credential"
        )
        self.blob_storage_account_key = self.get_setting("blob_storage_account_key", default=None)
        self.blob_container_name = self.get_setting("blob_container_name", required=True)
        
        # Filtering and traversal configuration
        self.prefix = self.get_setting("prefix", default="")
        self.file_extensions = self.get_setting("file_extensions", default=[])
        self.max_depth = self.get_setting("max_depth", default=0)
        self.max_results = self.get_setting("max_results", default=0)
        
        # Metadata and sorting
        self.include_metadata = self.get_setting("include_metadata", default=True)
        self.sort_by = self.get_setting("sort_by", default="name")
        self.sort_ascending = self.get_setting("sort_ascending", default=True)
        
        # Size filters
        self.min_size_bytes = self.get_setting("min_size_bytes", default=0)
        self.max_size_bytes = self.get_setting("max_size_bytes", default=0)
        
        # Date filters
        self.modified_after = self.get_setting("modified_after", default=None)
        self.modified_before = self.get_setting("modified_before", default=None)
        
        # Validate settings
        if self.sort_by not in ["name", "last_modified", "size"]:
            raise ValueError(
                f"Invalid sort_by value: {self.sort_by}. "
                f"Must be one of: name, last_modified, size"
            )
        
        # Normalize file extensions
        if self.file_extensions:
            self.file_extensions = [
                ext if ext.startswith('.') else f'.{ext}' 
                for ext in self.file_extensions
            ]
        
        # Parse date filters
        self.modified_after_dt = None
        self.modified_before_dt = None
        if self.modified_after:
            self.modified_after_dt = datetime.fromisoformat(self.modified_after)
        if self.modified_before:
            self.modified_before_dt = datetime.fromisoformat(self.modified_before)
        
        # Initialize blob connector
        self.blob_connector = BlobConnector(
            name="blob_input_connector",
            settings={
                "account_name": self.blob_storage_account,
                "credential_type": self.blob_storage_credential_type,
                "credential_key": self.blob_storage_account_key
            }
        )
        
        if self.debug_mode:
            logger.debug(
                f"AzureBlobInputExecutor initialized: "
                f"container={self.blob_container_name}, "
                f"prefix={self.prefix}, "
                f"extensions={self.file_extensions}, "
                f"max_depth={self.max_depth}, "
                f"max_results={self.max_results}"
            )
    
    async def process_input(
        self,
        input: Union[Content, List[Content]],
        ctx: WorkflowContext[Union[Content, List[Content]], Union[Content, List[Content]]]
    ) -> List[Content]:
        """
        Discover and list blobs from Azure Blob Storage.
        
        Args:
            input: Ignored for this executor (source executor)
            ctx: Workflow context
            
        Returns:
            List[Content]: List of Content objects for discovered blobs
        """
        start_time = datetime.now()
        
        try:
            # Initialize blob connector
            await self.blob_connector.initialize()
            
            if self.debug_mode:
                logger.debug(
                    f"Scanning container '{self.blob_container_name}' "
                    f"with prefix '{self.prefix}'"
                )
            
            # List all blobs with prefix
            blobs = await self.blob_connector.list_blobs(
                container_name=self.blob_container_name,
                prefix=self.prefix if self.prefix else None,
                max_results=None  # We'll filter ourselves
            )
            
            if self.debug_mode:
                logger.debug(f"Found {len(blobs)} total blobs before filtering")
            
            # Filter blobs
            filtered_blobs = self._filter_blobs(blobs)
            
            if self.debug_mode:
                logger.debug(f"After filtering: {len(filtered_blobs)} blobs")
            
            # Sort blobs
            sorted_blobs = self._sort_blobs(filtered_blobs)
            
            # Limit results
            if self.max_results > 0:
                sorted_blobs = sorted_blobs[:self.max_results]
            
            # Create Content objects
            content_items = []
            for blob in sorted_blobs:
                content = self._create_content_from_blob(blob)
                content_items.append(content)
            
            elapsed = (datetime.now() - start_time).total_seconds()
            
            logger.info(
                f"Discovered {len(content_items)} content items from "
                f"container '{self.blob_container_name}' in {elapsed:.2f}s"
            )
            
            return content_items
            
        except Exception as e:
            elapsed = (datetime.now() - start_time).total_seconds()
            logger.error(
                f"Failed to list blobs from container '{self.blob_container_name}' "
                f"after {elapsed:.2f}s: {str(e)}",
                exc_info=True
            )
            raise
    
    def _filter_blobs(self, blobs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Filter blobs based on configuration.
        
        Args:
            blobs: List of blob metadata dicts
            
        Returns:
            Filtered list of blob metadata dicts
        """
        filtered = []
        
        for blob in blobs:
            blob_name = blob['name']
            
            # Skip if it's a virtual directory marker
            if blob_name.endswith('/'):
                continue
            
            # Check depth
            if self.max_depth > 0:
                # Count directory separators
                depth = blob_name.count('/')
                # Adjust for prefix depth
                prefix_depth = self.prefix.count('/') if self.prefix else 0
                relative_depth = depth - prefix_depth
                
                if relative_depth > self.max_depth:
                    continue
            
            # Check file extension
            if self.file_extensions:
                blob_ext = Path(blob_name).suffix.lower()
                if blob_ext not in [ext.lower() for ext in self.file_extensions]:
                    continue
            
            # Check size filters
            blob_size = blob.get('size', 0)
            if self.min_size_bytes > 0 and blob_size < self.min_size_bytes:
                continue
            if self.max_size_bytes > 0 and blob_size > self.max_size_bytes:
                continue
            
            # Check date filters
            last_modified = blob.get('last_modified')
            if last_modified:
                # Ensure timezone-aware comparison
                if last_modified.tzinfo is None:
                    # If blob timestamp is naive, make it timezone-aware (UTC)
                    from datetime import timezone
                    last_modified = last_modified.replace(tzinfo=timezone.utc)
                
                if self.modified_after_dt:
                    # Make filter timezone-aware if needed
                    modified_after = self.modified_after_dt
                    if modified_after.tzinfo is None:
                        from datetime import timezone
                        modified_after = modified_after.replace(tzinfo=timezone.utc)
                    
                    if last_modified < modified_after:
                        continue
                
                if self.modified_before_dt:
                    # Make filter timezone-aware if needed
                    modified_before = self.modified_before_dt
                    if modified_before.tzinfo is None:
                        from datetime import timezone
                        modified_before = modified_before.replace(tzinfo=timezone.utc)
                    
                    if last_modified > modified_before:
                        continue
            
            filtered.append(blob)
        
        return filtered
    
    def _sort_blobs(self, blobs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Sort blobs based on configuration.
        
        Args:
            blobs: List of blob metadata dicts
            
        Returns:
            Sorted list of blob metadata dicts
        """
        if self.sort_by == "name":
            key_func = lambda b: b['name']
        elif self.sort_by == "last_modified":
            key_func = lambda b: b.get('last_modified', datetime.min)
        elif self.sort_by == "size":
            key_func = lambda b: b.get('size', 0)
        else:
            key_func = lambda b: b['name']
        
        return sorted(blobs, key=key_func, reverse=not self.sort_ascending)
    
    def _create_content_from_blob(self, blob: Dict[str, Any]) -> Content:
        """
        Create a Content object from blob metadata.
        
        Args:
            blob: Blob metadata dict
            
        Returns:
            Content object
        """
        blob_name = blob['name']
        filename = blob_name.split('/')[-1] if '/' in blob_name else blob_name
        
        # Generate unique ID
        unique_id = self.generate_sha1_hash(
            f"{self.blob_storage_account}/{self.blob_container_name}/{blob_name}"
        )
        
        # Create ContentIdentifier
        identifier = ContentIdentifier(
            canonical_id=f"https://{self.blob_storage_account}.blob.core.windows.net/{self.blob_container_name}/{blob_name}",
            unique_id=unique_id,
            source_name=self.blob_storage_account,
            source_type="azure_blob",
            container=self.blob_container_name,
            path=blob_name,
            filename=filename
        )
        
        # Build content data
        content_data = {
            'size': blob.get('size', 0),
            'last_modified': blob.get('last_modified'),
            'content_type': blob.get('content_type'),
        }
        
        # Include metadata if requested
        if self.include_metadata and blob.get('metadata'):
            content_data['metadata'] = blob['metadata']
        
        # Create Content object
        content = Content(
            id=identifier,
            data=content_data
        )
        
        # Add executor log entry
        content.executor_logs.append(ExecutorLogEntry(
            executor_id=self.id,
            start_time=datetime.now(),
            end_time=datetime.now(),
            status="completed",
            details={
                'blob_discovered': blob_name,
                'container': self.blob_container_name
            },
            errors=[]
        ))
        
        return content
