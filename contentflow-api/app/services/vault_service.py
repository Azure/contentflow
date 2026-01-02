import logging
from typing import Any, Dict, List, Optional
import uuid
from datetime import datetime, timezone

from fastapi import UploadFile, HTTPException


from .base_service import BaseService
from app.database.cosmos import CosmosDBClient
from app.models import (
    Vault, 
    VaultCreateRequest,
    VaultUpdateRequest
)

logger = logging.getLogger("contentflow.api.services.vault_service")

class VaultService(BaseService):
    """Service for managing document vaults"""

    def __init__(self, cosmos: CosmosDBClient, 
                       container_name: str = "vaults",
                       content_container_name: str = "vault_content"):
        """
        Initialize VaultService with database connection and configuration.
        Args:
            cosmos (CosmosDBClient): The Cosmos database instance for data persistence.
            container_name (str, optional): The name of the container to use for vault storage. 
                Defaults to "vaults".
            content_container_name (str, optional): The name of the container for vault content.
                Defaults to "vault_content".
        """
        super().__init__(cosmos=cosmos, container_name=container_name)
        self.content_container_name = content_container_name

    async def create_vault(self, request: VaultCreateRequest, pipeline_name: Optional[str] = None) -> Vault:
        """Create a new vault"""
        logger.info(f"Creating vault: {request.name}")
        
        # Check if a vault with the same name already exists
        existing_vaults = await self.query(
            query="SELECT * FROM c WHERE c.name = @name",
            parameters=[{"name": "@name", "value": request.name}]
        )
        
        if existing_vaults:
            raise ValueError(f"A vault with the name '{request.name}' already exists.")
        
        # Create the vault model
        vault = Vault(
            name=request.name,
            description=request.description,
            pipeline_id=request.pipeline_id,
            pipeline_name=pipeline_name,
            tags=request.tags,
            storage_config=request.storage_config,
            enabled=True,
        )
        
        saved_vault = await self.create(vault.model_dump())
        logger.info(f"Vault created with ID: {saved_vault['id']}")
        
        return Vault(**saved_vault)

    async def get_vault(self, vault_id: str) -> Optional[Vault]:
        """Get vault by ID"""
        vault_data = await self.get_by_id(vault_id)
        return Vault(**vault_data) if vault_data else None

    async def list_vaults(self, search: Optional[str] = None, tags: Optional[List[str]] = None) -> List[Vault]:
        """List all vaults with optional search and tag filtering"""
        logger.debug("Listing vaults")
        
        # Build query dynamically
        query_parts = ["SELECT * FROM c"]
        parameters = []
        where_clauses = []
        
        if search:
            where_clauses.append("(CONTAINS(LOWER(c.name), @search) OR CONTAINS(LOWER(c.description), @search))")
            parameters.append({"name": "@search", "value": search.lower()})
        
        if tags:
            tag_conditions = []
            for i, tag in enumerate(tags):
                tag_param = f"@tag{i}"
                tag_conditions.append(f"ARRAY_CONTAINS(c.tags, {tag_param})")
                parameters.append({"name": tag_param, "value": tag})
            where_clauses.append(f"({' OR '.join(tag_conditions)})")
        
        if where_clauses:
            query_parts.append("WHERE " + " AND ".join(where_clauses))
        
        query_parts.append("ORDER BY c.created_at DESC")
        query = " ".join(query_parts)
        
        items = await self.query(query=query, parameters=parameters if parameters else None)
        
        # Enrich with document counts
        vaults = []
        for item in items:
            vault = Vault(**item)
            
            # # Get document count for this vault
            # doc_count = await self._get_document_count(vault.id)
            # vault.stats.total_documents = doc_count
            
            vaults.append(vault)
        
        logger.debug(f"Found {len(vaults)} vaults")
        return vaults

    async def update_vault(self, vault_id: str, request: VaultUpdateRequest) -> Optional[Vault]:
        """Update a vault"""
        logger.info(f"Updating vault: {vault_id}")
        
        vault_data = await self.get_by_id(vault_id)
        if not vault_data:
            return None

        # Update fields
        update_data = request.model_dump(exclude_unset=True)
        
        for field, value in update_data.items():
            if value is not None:
                vault_data[field] = value
        
        # Update timestamp
        vault_data["updated_at"] = datetime.now(timezone.utc).isoformat()
        
        updated_vault = await self.update(vault_data)
        logger.info(f"Vault updated: {vault_id}")
        
        return Vault(**updated_vault)

    async def delete_vault(self, vault_id: str) -> bool:
        """Delete a vault and all its content"""
        logger.info(f"Deleting vault: {vault_id}")
        
        vault = await self.get_vault(vault_id)
        if not vault:
            raise ValueError(f"Vault {vault_id} not found")
        
        # Delete all content in the vault
        content_items = await self.list_vault_content(vault_id)
        for content in content_items:
            await self.delete_content(vault_id, content.id)
        
        # Delete the vault itself
        result = await self.delete(vault_id)
        logger.info(f"Vault deleted: {vault_id}")
        
        return result

    # # Content management methods
    
    # async def upload_content(
    #     self, 
    #     vault_id: str, 
    #     file_name: str,
    #     content_type: str,
    #     size_bytes: int,
    #     blob_path: Optional[str] = None,
    #     blob_url: Optional[str] = None,
    #     uploaded_by: Optional[str] = None
    # ) -> VaultContent:
    #     """Record uploaded content in the vault"""
    #     logger.info(f"Recording upload: {file_name} to vault {vault_id}")
        
    #     vault = await self.get_vault(vault_id)
    #     if not vault:
    #         raise ValueError(f"Vault {vault_id} not found")
        
    #     content = VaultContent(
    #         vault_id=vault_id,
    #         name=file_name,
    #         content_type=content_type,
    #         size_bytes=size_bytes,
    #         blob_path=blob_path,
    #         blob_url=blob_url,
    #         uploaded_by=uploaded_by,
    #         status="pending"
    #     )
        
    #     saved_content = await self.create(content.model_dump())
        
    #     # Update vault stats
    #     await self._update_vault_stats(vault_id)
        
    #     logger.info(f"Content recorded with ID: {saved_content['id']}")
    #     return VaultContent(**saved_content)

    # async def list_vault_content(
    #     self, 
    #     vault_id: str,
    #     status: Optional[str] = None,
    #     search: Optional[str] = None
    # ) -> List[VaultContent]:
    #     """List content in a vault"""
    #     logger.debug(f"Listing content for vault: {vault_id}")
        
    #     query_parts = ["SELECT * FROM c WHERE c.vault_id = @vault_id"]
    #     parameters = [{"name": "@vault_id", "value": vault_id}]
        
    #     if status:
    #         query_parts.append("AND c.status = @status")
    #         parameters.append({"name": "@status", "value": status})
        
    #     if search:
    #         query_parts.append("AND CONTAINS(LOWER(c.name), @search)")
    #         parameters.append({"name": "@search", "value": search.lower()})
        
    #     query_parts.append("ORDER BY c.created_at DESC")
    #     query = " ".join(query_parts)
        
    #     items = await self.query(query=query, parameters=parameters, target_container=self.content_container_name)
        
    #     return [VaultContent(**item) for item in items]

    # async def get_content(self, vault_id: str, content_id: str) -> Optional[VaultContent]:
    #     """Get specific content item"""
    #     content_data = await self.get_by_id(content_id)
        
    #     if not content_data or content_data.get("vault_id") != vault_id:
    #         return None
        
    #     return VaultContent(**content_data)

    # async def update_content_status(
    #     self,
    #     vault_id: str,
    #     content_id: str,
    #     status: str,
    #     error_message: Optional[str] = None,
    #     pipeline_execution_id: Optional[str] = None,
    #     entities_extracted: Optional[int] = None,
    #     chunks_created: Optional[int] = None
    # ) -> Optional[VaultContent]:
    #     """Update content processing status"""
    #     logger.info(f"Updating content status: {content_id} to {status}")
        
    #     content_data = await self.get_by_id(content_id)
    #     if not content_data or content_data.get("vault_id") != vault_id:
    #         return None
        
    #     content_data["status"] = status
    #     content_data["updated_at"] = datetime.now(timezone.utc).isoformat()
        
    #     if status == "ready":
    #         content_data["processed_at"] = datetime.now(timezone.utc).isoformat()
        
    #     if error_message is not None:
    #         content_data["error_message"] = error_message
        
    #     if pipeline_execution_id is not None:
    #         content_data["pipeline_execution_id"] = pipeline_execution_id
        
    #     if entities_extracted is not None:
    #         content_data["entities_extracted"] = entities_extracted
        
    #     if chunks_created is not None:
    #         content_data["chunks_created"] = chunks_created
        
    #     updated_content = await self.update(content_data)
        
    #     # Update vault stats
    #     await self._update_vault_stats(vault_id)
        
    #     logger.info(f"Content status updated: {content_id}")
    #     return VaultContent(**updated_content)

    # async def delete_content(self, vault_id: str, content_id: str) -> bool:
    #     """Delete content from vault"""
    #     logger.info(f"Deleting content: {content_id} from vault {vault_id}")
        
    #     content = await self.get_content(vault_id, content_id)
    #     if not content:
    #         return False
        
    #     result = await self.delete(content_id, target_container=self.content_container_name)
        
    #     # Update vault stats
    #     await self._update_vault_stats(vault_id)
        
    #     logger.info(f"Content deleted: {content_id}")
    #     return result

    # # Helper methods
    
    # async def _get_document_count(self, vault_id: str) -> int:
    #     """Get the total number of documents in a vault"""
    #     try:
    #         query = "SELECT VALUE COUNT(1) FROM c WHERE c.vault_id = @vault_id"
    #         parameters = [{"name": "@vault_id", "value": vault_id}]
            
    #         result = await self.query(
    #             query=query, 
    #             parameters=parameters,
    #             target_container=self.content_container_name
    #         )
            
    #         return result[0] if result else 0
    #     except Exception as e:
    #         logger.warning(f"Failed to get document count for vault {vault_id}: {e}")
    #         return 0

    # async def _update_vault_stats(self, vault_id: str) -> None:
    #     """Update vault statistics"""
    #     try:
    #         # Get all content for the vault
    #         content_items = await self.list_vault_content(vault_id)
            
    #         stats = VaultStats(
    #             total_documents=len(content_items),
    #             total_size_bytes=sum(c.size_bytes for c in content_items),
    #             processing_count=len([c for c in content_items if c.status == "processing"]),
    #             ready_count=len([c for c in content_items if c.status == "ready"]),
    #             error_count=len([c for c in content_items if c.status == "error"]),
    #             total_entities_extracted=sum(c.entities_extracted or 0 for c in content_items)
    #         )
            
    #         vault_data = await self.get_by_id(vault_id)
    #         if vault_data:
    #             vault_data["stats"] = stats.model_dump()
    #             vault_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    #             await self.update(vault_data)
                
    #     except Exception as e:
    #         logger.error(f"Failed to update vault stats for {vault_id}: {e}")

    async def check_pipeline_in_use_by_vault(self, pipeline_id: str) -> List[str]:
        """Check if a pipeline is used by any vault"""
        logger.debug(f"Checking if pipeline {pipeline_id} is in use")
        
        query = "SELECT * FROM c WHERE c.pipeline_id = @pipeline_id"
        parameters = [{"name": "@pipeline_id", "value": pipeline_id}]
        
        vaults_using_pipeline = await self.query(query=query, parameters=parameters)
        
        return [vault["name"] for vault in vaults_using_pipeline] if vaults_using_pipeline else []
