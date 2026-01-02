"""Azure Blob Storage output executor for writing content to blob storage."""

import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
import gzip
import zipfile
import io

from . import ParallelExecutor
from ..models import Content
from ..connectors import AzureBlobConnector
from ..utils import make_safe_json

logger = logging.getLogger("contentflow.executors.azure_blob_output_executor")

class AzureBlobOutputExecutor(ParallelExecutor):
    """
    Write content entries as JSON files to Azure Blob Storage.
    
    This executor writes Content items to Azure Blob Storage with support for
    path templating, metadata preservation, compression, batching, and various
    write modes for enterprise data archival and backup scenarios.
    
    Configuration (settings dict):
        - storage_account_name (str): Azure Storage account name
          Required: True
        - credential_type (str): Authentication type
          Default: "default_azure_credential"
          Options: "default_azure_credential", "azure_key_credential"
        - credential_key (str): Storage account key (required for azure_key_credential)
          Default: None
        - container_name (str): Target blob container name
          Required: True
        - path_template (str): Path pattern for organizing blobs (supports {field} placeholders)
          Default: "{category}/{year}/{month}/"
          Example: "{category}/{created_year}/{created_month}/"
        - filename_template (str): Filename pattern (supports {field} placeholders)
          Default: "{document_id}_{timestamp}.json"
          Example: "{id.canonical_id}_{timestamp}.json"
        - content_field (str): Field containing content to write (null = write entire Content item)
          Default: None
        - metadata_fields (str): Content fields to store as blob metadata, comma separated (null = no metadata)
          Default: None
          Example: "title,author,category"
        - compression (str): Compression type
          Default: None
          Options: None, "gzip", "zip"
        - overwrite_existing (bool): Whether to overwrite existing blobs
          Default: True
        - add_timestamp (bool): Add written_at timestamp to blob metadata
          Default: True
        - pretty_print (bool): Pretty print JSON output
          Default: True
        
        Also setting from ParallelExecutor and BaseExecutor apply.

    
    Used Connectors:
        - AzureBlobConnector: For Azure Blob Storage operations
    
    Example:
        ```python
        # Basic blob writer with default settings
        executor = AzureBlobOutputExecutor(
            id="blob_writer",
            settings={
                "storage_account_name": "mystorageaccount",
                "credential_type": "default_azure_credential",
                "container_name": "processed-content",
                "path_template": "{pipeline_name}/{year}/{month}/{day}/",
                "filename_template": "{id.unique_id}.json"
            }
        )
        
        # Writer with compression and custom metadata
        executor = AzureBlobOutputExecutor(
            id="blob_writer",
            settings={
                "storage_account_name": "mystorageaccount",
                "credential_type": "default_azure_credential",
                "container_name": "archived-docs",
                "path_template": "{content_type}/{year}/{month}/",
                "filename_template": "{id.canonical_id}_{timestamp}.json",
                "compression": "gzip",
                "metadata_fields": "title,author,category,source",
                "overwrite_existing": True,
                "pretty_print": False
            }
        )
        
        # Writer for specific content field
        executor = AzureBlobOutputExecutor(
            id="blob_writer",
            settings={
                "storage_account_name": "mystorageaccount",
                "credential_type": "default_azure_credential",
                "container_name": "processed-results",
                "path_template": "{status}/",
                "filename_template": "{id.unique_id}.json",
                "content_field": "processed_data",
                "compression": "none",
                "add_timestamp": True
            }
        )
        ```
    
    Input:
        Content or List[Content] with:
        - id: Content identifier
        - data: Dict containing content to write
        - summary_data: Dict containing metadata
        
    Output:
        Content or List[Content] with added summary_data:
        - blob_path: Path where blob was written
        - blob_size: Size of written blob in bytes
        - blob_etag: ETag of written blob
        - write_status: "success" or "error"
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
        
        # Storage configuration
        self.storage_account_name = self.get_setting("storage_account_name", required=True)
        self.credential_type = self.get_setting("credential_type", default="default_azure_credential")
        self.credential_key = self.get_setting("credential_key", default=None)
        self.container_name = self.get_setting("container_name", required=True)
        
        # Path and filename configuration
        self.path_template = self.get_setting("path_template", default="{pipeline_name}/{year}/{month}/{day}")
        self.filename_template = self.get_setting("filename_template", default="{id.unique_id}_{timestamp}.json")
        
        # Content configuration
        self.content_field = self.get_setting("content_field", default=None)
        self.metadata_fields = self.get_setting("metadata_fields", default=None)
        
        # Write options
        self.compression = self.get_setting("compression", default=None)
        if self.compression is not None:
            self.compression = self.compression.lower().strip()
        
        self.overwrite_existing = self.get_setting("overwrite_existing", default=True)
        self.add_timestamp = self.get_setting("add_timestamp", default=True)
        self.pretty_print = self.get_setting("pretty_print", default=True)
        
        # Connector instance (will be initialized on first use)
        self._connector = None
        
        if self.debug_mode:
            logger.debug(
                f"AzureBlobOutputExecutor {self.id} initialized: "
                f"account={self.storage_account_name}, "
                f"container={self.container_name}, "
                f"compression={self.compression}"
            )
    
    def _get_nested_value(self, data: Dict[str, Any], field_path: str) -> Any:
        """
        Get value from nested dictionary using dot notation.
        
        Args:
            data: Dictionary to extract value from
            field_path: Dot-separated path (e.g., "id.unique_id" or "metadata.author")
        
        Returns:
            Value at the field path, or None if not found
        """
        if not field_path:
            return None
        
        keys = field_path.split('.')
        value = data
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return None
        
        return value
    
    def _format_template(self, template: str, content: Content) -> str:
        """
        Format a template string with content field values.
        
        Args:
            template: Template string with {field} placeholders
            content: Content item to extract values from
        
        Returns:
            Formatted string
        """
        # Create combined source data
        source_data = {}
        if content.id:
            source_data['id'] = {
                'unique_id': content.id.unique_id,
                'canonical_id': content.id.canonical_id,
                'filename': content.id.filename
            }
            # Add convenience fields
            source_data['document_id'] = content.id.canonical_id or content.id.unique_id
        
        source_data.update(content.data)
        source_data.update(content.summary_data)
        
        # Add date/time and special fields
        now = datetime.now(timezone.utc)
        source_data['timestamp'] = now.strftime("%Y%m%d_%H%M%S")
        source_data['year'] = now.strftime("%Y")
        source_data['month'] = now.strftime("%m")
        source_data['day'] = now.strftime("%d")
        source_data['date'] = now.strftime("%Y-%m-%d")
        source_data['executor_id'] = self.id
        
        # Extract created date if available
        if 'created_at' in source_data:
            try:
                created = datetime.fromisoformat(str(source_data['created_at']).replace('Z', '+00:00'))
                source_data['created_year'] = created.strftime("%Y")
                source_data['created_month'] = created.strftime("%m")
                source_data['created_day'] = created.strftime("%d")
            except (ValueError, AttributeError):
                pass
        
        # Format template - handle nested paths
        result = template
        import re
        
        # Find all {field} patterns including nested paths
        pattern = r'\{([^}]+)\}'
        matches = re.findall(pattern, template)
        
        for field_path in matches:
            value = self._get_nested_value(source_data, field_path)
            if value is not None:
                # Convert to string, handling special characters
                str_value = str(value).replace('/', '_').replace('\\', '_')
                result = result.replace(f'{{{field_path}}}', str_value)
            else:
                # Replace with 'unknown' if field not found
                result = result.replace(f'{{{field_path}}}', 'unknown')
        
        return result
    
    def _extract_metadata(self, content: Content) -> Dict[str, str]:
        """
        Extract metadata from content based on configured metadata_fields.
        
        Args:
            content: Content item to extract metadata from
        
        Returns:
            Dictionary of metadata (all values as strings for blob metadata)
        """
        metadata = {}
        
        if self.metadata_fields is None:
            return metadata
        
        # Create combined source data
        source_data = {}
        if content.id:
            source_data['id'] = {
                'unique_id': content.id.unique_id,
                'canonical_id': content.id.canonical_id,
                'filename': content.id.filename
            }
        source_data.update(content.data)
        source_data.update(content.summary_data)
        
        # Extract requested metadata fields
        for field_path in self.metadata_fields:
            value = self._get_nested_value(source_data, field_path)
            if value is not None:
                # Convert to string (blob metadata must be strings)
                metadata[field_path.replace('.', '_')] = str(value)
        
        # Add timestamp if configured
        if self.add_timestamp:
            metadata['written_at'] = datetime.now(timezone.utc).isoformat()
        
        return metadata
    
    def _serialize_content(self, content: Content) -> bytes:
        """
        Serialize content to JSON bytes.
        
        Args:
            content: Content item to serialize
        
        Returns:
            Serialized content as bytes
        """
        # Determine what to write
        if self.content_field:
            # Write specific field
            data = self._get_nested_value(content.data, self.content_field)
            if data is None:
                logger.warning(
                    f"Content field '{self.content_field}' not found in content "
                    f"{content.id.canonical_id if content.id else 'unknown'}"
                )
                data = {}
        else:
            # Write entire content
            data = content.model_dump()
        
        if data:
            data = make_safe_json(data)
        
        # Serialize to JSON
        if self.pretty_print:
            json_str = json.dumps(data, indent=2, ensure_ascii=False)
        else:
            json_str = json.dumps(data, ensure_ascii=False)
        
        # Encode to bytes
        json_bytes = json_str.encode(encoding='utf-8')
        
        # Apply compression if configured
        if self.compression == "gzip":
            buffer = io.BytesIO()
            with gzip.GzipFile(fileobj=buffer, mode='wb') as gz:
                gz.write(json_bytes)
            return buffer.getvalue()
        
        elif self.compression == "zip":
            buffer = io.BytesIO()
            # Use filename from template without .json extension for zip entry
            zip_entry_name = "content.json"
            with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
                zf.writestr(zip_entry_name, json_bytes)
            return buffer.getvalue()
        
        else:
            return json_bytes
    
    async def _get_connector(self) -> AzureBlobConnector:
        """
        Get or initialize the Blob connector.
        
        Returns:
            BlobConnector instance
        """
        if self._connector is None:
            connector_settings = {
                "account_name": self.storage_account_name,
                "credential_type": self.credential_type
            }
            
            if self.credential_key:
                connector_settings["credential_key"] = self.credential_key
            
            self._connector = AzureBlobConnector(
                name=f"blob_connector_{self.id}",
                settings=connector_settings
            )
            
            # Ensure connector is initialized
            await self._connector.initialize()
        
        return self._connector
    
    async def process_content_item(
        self,
        content: Content
    ) -> Content:
        """Write content item to Azure Blob Storage."""
        
        if not content or not content.data:
            raise ValueError("Content must have data")
        
        # Get blob connector
        blob_connector = await self._get_connector()
        
        try:
            # Generate blob path
            path = self._format_template(self.path_template, content)
            filename = self._format_template(self.filename_template, content)
            
            # Add compression extension if needed
            if self.compression == "gzip" and not filename.endswith('.gz'):
                filename += '.gz'
            elif self.compression == "zip" and not filename.endswith('.zip'):
                filename += '.zip'
            
            blob_path = path + filename
            
            # Extract metadata
            metadata = self._extract_metadata(content)
            
            # Serialize content
            content_bytes = self._serialize_content(content)
            
            # Upload to blob storage
            result = await blob_connector.upload_blob(
                container_name=self.container_name,
                blob_path=blob_path,
                data=content_bytes,
                overwrite=self.overwrite_existing,
                metadata=metadata
            )
            
            blob_output_summary = {
                "blob_path": blob_path,
                "blob_size": len(content_bytes),
                "blob_etag": result.get('etag'),
                "blob_last_modified": result.get('last_modified').isoformat() if result.get('last_modified') else None,
                "write_status": "success"
            }
            
            # Update content with write results
            content.summary_data['blob_output'] = blob_output_summary
            
            if self.debug_mode:
                logger.debug(
                    f"Wrote blob {blob_path} ({len(content_bytes)} bytes) "
                    f"for content {content.id.canonical_id if content.id else 'unknown'}"
                )
            
        except Exception as e:
            content_id = content.id.canonical_id if content.id else 'unknown'
            logger.error(f"Error writing content {content_id} to blob: {e}")
            logger.exception(e)
            content.summary_data['write_status'] = "error"
            content.summary_data['write_error'] = str(e)
            
            # Re-raise the exception to be handled upstream if needed
            raise
        
        return content
