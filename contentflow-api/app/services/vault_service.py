import logging
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone

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
            save_execution_output=request.save_execution_output,
            enabled=request.enabled if request.enabled is not None else True,
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
            return False
        
        # Delete the vault itself
        result = await self.delete(vault_id)
        logger.info(f"Vault deleted: {vault_id}")
        
        try:
            # Delete all vault executions
            from app.dependencies import get_vault_execution_service
            
            vault_execution_service = await get_vault_execution_service()
            await vault_execution_service.delete_vault_executions(vault_id)
            await vault_execution_service.delete_vault_crawl_checkpoints(vault_id)
        except Exception as e:
            logger.error(f"Error deleting vault executions or crawl checkpoints for vault {vault_id}: {e}")
        
        return result

    async def check_pipeline_in_use_by_vault(self, pipeline_id: str) -> List[str]:
        """Check if a pipeline is used by any vault"""
        logger.debug(f"Checking if pipeline {pipeline_id} is in use")
        
        query = "SELECT * FROM c WHERE c.pipeline_id = @pipeline_id"
        parameters = [{"name": "@pipeline_id", "value": pipeline_id}]
        
        vaults_using_pipeline = await self.query(query=query, parameters=parameters)
        
        return [vault["name"] for vault in vaults_using_pipeline] if vaults_using_pipeline else []
