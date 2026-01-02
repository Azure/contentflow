from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from app.database.cosmos import CosmosDBClient

class BaseService:
    """Base service class for common CRUD operations"""
    
    def __init__(self, cosmos: CosmosDBClient, container_name: str):
        self.cosmos = cosmos
        self.container_name = container_name
        
        self.cosmos_container_client = self.cosmos.get_container(container_name)
    
    async def create(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new item"""
        return await self.cosmos.create(self.container_name, item)
    
    async def get_by_id(self, item_id: str) -> Optional[Dict[str, Any]]:
        """Get item by ID"""
        return await self.cosmos.get_by_id(self.container_name, item_id)
    
    async def list_all(self, query: Optional[str] = None, parameters: Optional[List[Dict[str, Any]]] = None) -> List[Dict[str, Any]]:
        """List all items"""
        return await self.cosmos.list_all(self.container_name, query, parameters)
    
    async def query(self, query: str, parameters: Optional[List[Dict[str, Any]]] = None, target_container: Optional[str] = None) -> List[Dict[str, Any]]:
        """Execute a query"""
        target_container = target_container or self.container_name
        return await self.cosmos.query(target_container, query, parameters)
    
    async def update(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing item"""
        return await self.cosmos.update(self.container_name, item)
    
    async def delete(self, item_id: str, target_container: Optional[str] = None) -> bool:
        """Delete an item by ID"""
        try:
            target_container = target_container or self.container_name
            return await self.cosmos.delete(target_container, item_id)
        except Exception:
            return False
    
    async def batch_upsert(self, items: List[Dict[str, Any]], target_container: Optional[str] = None) -> List[Dict[str, Any]]:
        """Batch upsert items"""
        
        target_container = target_container or self.container_name
        return await self.cosmos.batch_upsert(target_container, items)
