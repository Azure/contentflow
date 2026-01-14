from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import uuid
import logging

from .base_service import BaseService
from app.models import Pipeline
from app.database.cosmos import CosmosDBClient

logger = logging.getLogger("contentflow.api.services.pipeline_service")

class PipelineService(BaseService):
    """Service for managing pipeline operations"""
    
    def __init__(self, cosmos: CosmosDBClient, container_name: str = "pipelines"):
        super().__init__(cosmos, container_name)
    
    async def get_pipelines(self) -> List[Pipeline]:
        """List all pipelines from configuration"""
        result = await self.list_all()
        
        pipelines = [Pipeline(**item) for item in result]
        return pipelines
    
    async def get_pipeline_by_id(self, pipeline_id: str) -> Optional[Pipeline]:
        """Get pipeline definition from config by id"""
        result = await self.get_by_id(pipeline_id)
        if result:
            return Pipeline(**result)
        return None
    
    async def get_pipeline_by_name(self, pipeline_name: str) -> Optional[Pipeline]:
        """Get pipeline definition from config by name"""
        
        query = "SELECT TOP 1 * FROM c WHERE c.name=@name"
        params = [{"name": "@name", "value": pipeline_name}]
        pipelines = await self.query(query, params)
        if pipelines:
            result = pipelines[0]
            return Pipeline(**result)
        
        return None
    
    async def create_pipeline(self, pipeline_data: Dict[str, Any]) -> Pipeline:
        """Create a pipeline instance based on configuration"""
        
        # check is a pipeline with the same name already exists
        existing = await self.get_pipeline_by_name(pipeline_data.get("name"))
        if existing:
            raise ValueError(f"A pipeline with the name '{pipeline_data.get('name')}' already exists.")
        
        # Generate unique ID if not provided
        pipeline_id = f"{pipeline_data.get('name')}_{uuid.uuid4().hex[:8]}"
        pipeline_id = pipeline_id.replace(" ", "_").lower()
        
        pipeline = Pipeline(
            id=pipeline_id,
            name=pipeline_data.get("name"),
            description=pipeline_data.get("description", ""),
            yaml=pipeline_data.get("yaml"),
            nodes=pipeline_data.get("nodes", []),
            edges=pipeline_data.get("edges", []),
            created_by=pipeline_data.get("created_by", ""),
            tags=pipeline_data.get("tags", []),
            enabled=pipeline_data.get("enabled", True),
            retry_delay=pipeline_data.get("retry_delay", 5),
            timeout=pipeline_data.get("timeout", 600),
            retries=pipeline_data.get("retries", 3),
            version=pipeline_data.get("version", "1.0"),
        )
        
        result = await self.create(pipeline.model_dump())
        return Pipeline(**result)
    
    async def create_or_save_pipeline(self, pipeline_data: Dict[str, Any]) -> Pipeline:
        """Create a pipeline instance based on configuration"""
        
        logger.debug(f"Creating or saving pipeline {pipeline_data.get('name', '')}...")
        
        try:
            # check is a pipeline with the same name already exists
            pipeline_id = pipeline_data.get("id")
            if pipeline_id:
                
                logger.debug(f"Updating existing pipeline with ID: {pipeline_id}")
                
                # update existing
                await self.update_by_id(pipeline_id=pipeline_id, 
                                        update_data=pipeline_data)
                existing = await self.get_by_id(pipeline_id)
                return Pipeline(**existing)
            else:
                logger.debug(f"Creating new pipeline with name: {pipeline_data.get('name', '')}")
                return await self.create_pipeline(pipeline_data)
        except Exception as e:
            logger.error(f"Error in create_or_save_pipeline: {str(e)}")
            logger.exception(e)
            raise e
    
    async def update_by_id(self, pipeline_id: str, update_data: Dict[str, Any]) -> Pipeline:
        """Update a pipeline instance by ID"""
        existing = await self.get_by_id(pipeline_id)
        if not existing:
            raise ValueError("Pipeline not found")
        
        # Update allowed fields
        allowed_updates = ["name", "description", "yaml", "nodes", "edges", 
                           "created_by", "tags", "version", 
                           "enabled", "retry_delay", "timeout", "retries"]
    
        for key, value in update_data.items():
            if key in allowed_updates:
                existing[key] = value
        
        existing["updated_at"] = datetime.now(timezone.utc).isoformat()
                
        updated = await self.update(existing)
        return Pipeline(**updated)

    # TODO: when pipeline deleted, delete also pipeline executions
    async def delete_pipeline_by_id(self, pipeline_id: str) -> bool:
        """Delete a pipeline instance by ID"""
        existing = await self.get_by_id(pipeline_id)
        if not existing:
            return False
        
        # check if pipeline is in use by any vault
        from app.dependencies import get_vault_service
        vault_service = await get_vault_service()
        
        in_use_vaults = await vault_service.check_pipeline_in_use_by_vault(pipeline_id=pipeline_id)
        if in_use_vaults:
            raise ValueError(f"Pipeline is in use by vaults: {in_use_vaults}")

        return await self.delete(pipeline_id)
        
    
    async def check_step_instance_in_use(self, step_instance_id: str) -> List[str]:
        """Check if a step instance is used in any pipeline"""
        # query = "SELECT * FROM c WHERE c.name=@name"
        # params = [{"name": "@name", "value": name}]
        # items = await self.query(query, params)
        
        pipelines = await self.list_pipelines()
        in_use_pipelines = []
        for pipeline in pipelines:
            steps = pipeline.get("steps", [])
            if step_instance_id in steps:
                in_use_pipelines.append(pipeline.get("name"))
        
        return in_use_pipelines