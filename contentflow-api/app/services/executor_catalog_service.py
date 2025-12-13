from datetime import datetime, timezone
import logging
from typing import Any, Dict, List, Optional
from pydantic import ValidationError
import yaml

from .base_service import BaseService
from app.database.cosmos import CosmosDBClient

from app.models import ExecutorCatalogDefinition

logger = logging.getLogger("contentflow-api.services.executor_catalog")

class ExecutorCatalogService(BaseService):
    """Service for managing executor catalog operations"""
    
    def __init__(self, cosmos: CosmosDBClient, container_name: str = "executor_catalog"):
        super().__init__(cosmos, container_name)
    
        self._catalog_cache = None
    
    async def _load_catalog_from_yaml(self, executor_catalog_file_path: str) -> Dict[str, Any]:
        """Load step catalog from YAML file"""
        catalog_path = executor_catalog_file_path
        catalog = {"executor_catalog": []}
        
        try:
            with open(catalog_path, 'r') as file:
                catalog = yaml.safe_load(file)
        except FileNotFoundError as e:
            logger.error(f"Error loading executor catalog from path {catalog_path}: {e}")
            raise e
        
        return catalog
    
    async def _sync_catalog_executors_to_db(self, yaml_catalog_executors: List[Dict[str, Any]]):
        """Sync catalog executors to Cosmos DB catalog container"""
        
        created_count = 0
        
        to_update = []
        
        existing_executors = await self.list_all()
        
        for executor in yaml_catalog_executors:
            executor_id = executor.get("id")
            existing = next((ex for ex in existing_executors if ex.get("id") == executor_id), None)
                        
            # Only update if not exists or version changed
            if not existing or (existing and existing.get("version") != executor.get("version")):
                executor_doc = {
                    **executor,
                    "synced_at": datetime.now(timezone.utc).isoformat()
                }
                
                is_valid, error_msg = self._validate_executor_definition(executor_doc)
                if not is_valid:
                    logger.warning(f"Skipping invalid executor definition with ID {executor_id}: {error_msg}")
                    continue
                
                to_update.append(executor_doc)
                created_count += 1
        
        if to_update and len(to_update) > 0:
            await self.batch_upsert(to_update)

        return {"created_count": created_count}
    
    def _validate_executor_definition(self, executor_definition: Dict[str, Any]) -> tuple[bool, str]:
        """Validate executor definition structure"""
        try:
            ExecutorCatalogDefinition(**executor_definition)
            return (True, "")
        except ValidationError as e:
            logger.error(f"Executor definition validation failed: {str(e)}")
            return (False, str(e))
    
    async def initialize_executor_catalog(self, executor_catalog_file_path: str) -> Dict[str, Any]:
        """Initialize executor definitions from catalog if they don't exist"""
        logger.info("Initializing executor definitions from catalog...")
        
        _yaml_catalog = await self._load_catalog_from_yaml(executor_catalog_file_path)
        _yaml_executors = _yaml_catalog.get("executor_catalog", [])
            
        # Store catalog executors in Cosmos DB for persistence and updates
        result = await self._sync_catalog_executors_to_db(_yaml_executors)
        
        # run again to get updated count
        catalog_executors = await self.get_catalog_executors()
        
        return {
            "created_count": result.get("created_count", 0),
            "total_catalog_executors": len(catalog_executors)
        }
    
    async def get_catalog_executors(self) -> List[ExecutorCatalogDefinition]:
        """List all executors from catalog"""
        if self._catalog_cache is None:
            executors = await self.list_all()
            self._catalog_cache = [ExecutorCatalogDefinition(**ex) for ex in executors]
        return self._catalog_cache
    
    async def get_catalog_executor_by_id(self, executor_id: str) -> Optional[ExecutorCatalogDefinition]:
        """Get executor definition from catalog by ID"""
        catalog_executors = await self.get_catalog_executors()
        for executor in catalog_executors:
            if executor.id == executor_id:
                return executor
        return None