"""
Azure Blob Storage connector for document storage and retrieval.

This connector provides access to Azure Blob Storage for reading and
writing documents during workflow execution.
"""

import asyncio
import logging
from pathlib import Path
from typing import AsyncGenerator, Optional, List, Dict, Any

from azure.storage.blob.aio import BlobServiceClient, ContainerClient

from ..utils.credential_provider import get_azure_credential_async
from .base import ConnectorBase

logger = logging.getLogger("contentflow.lib.connectors.azure_blob")


class AzureBlobConnector(ConnectorBase):
    """
    Azure Blob Storage connector.
    
    Provides async access to Azure Blob Storage for document operations.
    Supports both Azure Key Credential and Default Azure Credential authentication.
    
    Configuration settings:
        - account_name: Storage account name (supports ${ENV_VAR})
        - credential_type: 'azure_key_credential' or 'default_azure_credential'
        - credential_key: Storage account key (required for azure_key_credential)
    
    Example:
        ```python
        connector = BlobConnector(
            name="storage",
            settings={
                "account_name": "${STORAGE_ACCOUNT}",
                "credential_type": "default_azure_credential"
            }
        )
        
        await connector.initialize()
        
        # Download blob
        content = await connector.download_blob("container", "path/to/file.pdf")
        
        # Upload blob
        await connector.upload_blob("container", "output.json", content_bytes)
        
        # List blobs
        blobs = await connector.list_blobs("container", prefix="documents/")
        ```
    """
    
    def __init__(self, name: str, settings: Dict[str, Any], **kwargs):
        super().__init__(name=name, connector_type="blob_storage", settings=settings, **kwargs)
        
        # Validate and resolve settings
        self.storage_account_name = self._resolve_setting("account_name", required=True)
        self.credential_type = self._resolve_setting("credential_type", required=True)
        
        # Validate credential type
        if self.credential_type not in ['azure_key_credential', 'default_azure_credential']:
            raise ValueError(
                f"Unsupported credential type: {self.credential_type}. "
                f"Supported types are 'azure_key_credential' and 'default_azure_credential'."
            )
        
        # Get credential key if using key-based auth
        self.credential_key = None
        if self.credential_type == 'azure_key_credential':
            self.credential_key = self._resolve_setting("credential_key", required=True)
        
        # Initialize client references
        self.blob_service_client: Optional[BlobServiceClient] = None
        self.credential = None
        self._is_initialized: bool = False
        self._initialization_lock = asyncio.Lock()
        self._file_locks: Dict[str, asyncio.Lock] = {}
        self._file_locks_lock = asyncio.Lock()
        self._active_operations = 0
        self._operations_lock = asyncio.Lock()
    
    async def initialize(self) -> None:
        """Initialize the blob service client."""
        if self._is_initialized:
            return
        
        async with self._initialization_lock:
            if self._is_initialized:
                return
            
            account_url = f"https://{self.storage_account_name}.blob.core.windows.net"
            
            if self.credential_type == 'azure_key_credential':
                self.blob_service_client = BlobServiceClient(
                    account_url=account_url,
                    credential=self.credential_key
                )
            else:  # default_azure_credential
                self.credential = await get_azure_credential_async()
                self.blob_service_client = BlobServiceClient(
                    account_url=account_url,
                    credential=self.credential
                )
            
            self._is_initialized = True
            logger.info(f"Initialized BlobConnector '{self.name}' for account '{self.storage_account_name}'")
    
    async def test_connection(self) -> bool:
        """Test the blob storage connection."""
        try:
            if not self._is_initialized:
                await self.initialize()
            
            # Try to list containers (limited to 1 to minimize overhead)
            async for _ in self.blob_service_client.list_containers(results_per_page=1):
                break
            
            logger.info(f"BlobConnector '{self.name}' connection test successful")
            return True
            
        except Exception as e:
            logger.error(f"BlobConnector '{self.name}' connection test failed: {e}")
            raise
    
    async def download_blob(
        self,
        container_name: str,
        blob_path: str
    ) -> bytes:
        """
        Download a blob from storage.
        
        Args:
            container_name: Container containing the blob
            blob_path: Path to the blob within the container
            
        Returns:
            Blob content as bytes
        """
        if not self._is_initialized:
            await self.initialize()
        
        try:
            async with self._operations_lock:
                self._active_operations += 1
            
            container_client = self.blob_service_client.get_container_client(container_name)
            blob_client = container_client.get_blob_client(blob_path)
            
            download_stream = await blob_client.download_blob()
            content = await download_stream.readall()
            
            logger.debug(f"Downloaded blob: {container_name}/{blob_path} ({len(content)} bytes)")
            return content
            
        finally:
            async with self._operations_lock:
                self._active_operations -= 1
    
    async def upload_blob(
        self,
        container_name: str,
        blob_path: str,
        data: bytes,
        overwrite: bool = True,
        metadata: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Upload a blob to storage.
        
        Args:
            container_name: Container to upload to
            blob_path: Path for the blob within the container
            data: Blob content as bytes
            overwrite: Whether to overwrite existing blob
            metadata: Optional metadata dict
            
        Returns:
            Dict with upload result metadata
        """
        if not self._is_initialized:
            await self.initialize()
        
        try:
            async with self._operations_lock:
                self._active_operations += 1
            
            container_client = self.blob_service_client.get_container_client(container_name)
            blob_client = container_client.get_blob_client(blob_path)
            
            result = await blob_client.upload_blob(
                data,
                overwrite=overwrite,
                metadata=metadata
            )
            
            logger.debug(f"Uploaded blob: {container_name}/{blob_path} ({len(data)} bytes)")
            
            return {
                "etag": result.get('etag'),
                "last_modified": result.get('last_modified'),
                "version_id": result.get('version_id')
            }
            
        finally:
            async with self._operations_lock:
                self._active_operations -= 1
    
    async def list_blobs(
        self,
        container_name: str,
        prefix: Optional[str] = None,
        max_results: Optional[int] = None,
        batch_size: int = 10
    ) -> AsyncGenerator[List[Dict[str, Any]], None]:
        """
        List blobs in a container.
        
        Args:
            container_name: Container to list from
            prefix: Optional prefix filter
            max_results: Maximum number of results
            
        Returns:
            List of blob metadata dicts
        """
        if not self._is_initialized:
            await self.initialize()
        
        container_client = self.blob_service_client.get_container_client(container_name)
        
        total_fetched = 0
        blobs = []
        async for blob_page in container_client.list_blobs(name_starts_with=prefix, results_per_page=batch_size).by_page():
                         
            async for blob in blob_page:
                blobs.append({
                    "name": blob.name,
                    "size": blob.size,
                    "last_modified": blob.last_modified,
                    "content_type": blob.content_settings.content_type if blob.content_settings else None,
                    "metadata": blob.metadata
                })
                
                total_fetched += 1
                
                # Yield when we have a full batch
                if len(blobs) >= batch_size:
                    batch_to_yield = blobs[:batch_size]
                    logger.debug(f"Yielding batch of {len(batch_to_yield)} blobs from {container_name} (prefix: {prefix})")
                    yield batch_to_yield
                    blobs = blobs[batch_size:]
                
                # Stop fetching if we've reached max_results
                if max_results and max_results > 0 and total_fetched >= max_results:
                    break

            if max_results and max_results > 0 and total_fetched >= max_results:
                break
            
        # Yield any remaining blobs (less than batch_size)
        if blobs:
            remaining = blobs[:max_results - total_fetched + len(blobs)] if max_results and max_results > 0 else blobs
            logger.debug(f"Yielding final batch of {len(remaining)} blobs from {container_name} (prefix: {prefix})")
            yield remaining
        
        logger.info(f"Completed listing blobs from {container_name} (prefix: {prefix}). Total blobs listed: {total_fetched}")
    
    async def blob_exists(self, container_name: str, blob_path: str) -> bool:
        """Check if a blob exists."""
        if not self._is_initialized:
            await self.initialize()
        
        container_client = self.blob_service_client.get_container_client(container_name)
        blob_client = container_client.get_blob_client(blob_path)
        
        return await blob_client.exists()
    
    async def delete_blob(self, container_name: str, blob_path: str) -> None:
        """Delete a blob."""
        if not self._is_initialized:
            await self.initialize()
        
        container_client = self.blob_service_client.get_container_client(container_name)
        blob_client = container_client.get_blob_client(blob_path)
        
        await blob_client.delete_blob()
        logger.debug(f"Deleted blob: {container_name}/{blob_path}")
    
    async def cleanup(self) -> None:
        """Cleanup connector resources."""
        if self.blob_service_client:
            await self.blob_service_client.close()
        
        if self.credential:
            await self.credential.close()
        
        self._is_initialized = False
        logger.info(f"Cleaned up BlobConnector '{self.name}'")
