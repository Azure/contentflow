from azure.cosmos import exceptions, ContainerProxy, DatabaseProxy, PartitionKey
from azure.cosmos.aio import CosmosClient
from azure.identity.aio import ChainedTokenCredential

import logging
from typing import Any, Dict, Optional, List

# Configure logging

logger = logging.getLogger("contentflow.api.database.cosmos")

class CosmosDBClient:
    """Azure Cosmos DB client wrapper"""

    def __init__(self, database: str, endpoint: str, credential: str | ChainedTokenCredential, initial_containers: Dict[str, str] = None):
        self.database = database
        self.endpoint = endpoint
        self.credential = credential
        self.initial_containers = initial_containers or {}
        
        self.client: CosmosClient = None
        self.database_proxy: DatabaseProxy = None
        self.containers: Dict[str, ContainerProxy] = {}
        
    async def connect(self):
        """Initialize Cosmos DB connection"""
        
        logger.info("Connecting to Cosmos DB...")
        
        try:
            self.client = CosmosClient(
                url=self.endpoint,
                credential=self.credential
            )
            
            logger.info(f"Attempting to create or get database '{self.database}...")
            # Create database if it doesn't exist
            self.database_proxy = await self._ensure_database(self.database)
            logger.info(f"Database '{self.database}' is ready.")
                        
            logger.info("Initializing containers...")
            if self.initial_containers:
                self.containers = {
                        container_name: self._ensure_container(container_name, partition_key) for container_name, partition_key in self.initial_containers.items()
                    }
            logger.info(f"Initialized {len(self.containers)} containers.")

            logger.info("Successfully connected to Cosmos DB")
        
        except exceptions.CosmosHttpResponseError as e:
            logger.error(f"Cosmos DB HTTP error: {str(e)}")
            # logger.exception(e)
            raise
        except Exception as e:
            logger.error(f"Failed to connect to or initialize Cosmos DB: {str(e)}")
            # logger.exception(e)
            raise
    
    async def close(self):
        """Close Cosmos DB connection"""
        if self.client:
            await self.client.close()
            self.client = None
            self.database_proxy = None
            self.containers = {}
            logger.info("Cosmos DB connection closed")

    async def _ensure_database(self, db_name: str):
        try:
            return await self.client.create_database_if_not_exists(id=db_name)
        except exceptions.CosmosResourceExistsError:
            return self.client.get_database_client(db_name)
        
    def _ensure_container(self, container_name: str, partition_key: str = "/id"):
        try:
            # return self.database_proxy.create_container_if_not_exists(id=container_name, partition_key=PartitionKey(path=partition_key))
            return self.database_proxy.get_container_client(container_name)
        except exceptions.CosmosResourceExistsError:
            raise Exception(f"Container '{container_name}' could not be accessed. Ensure container exists in the database '{self.database}'.")
            
    def get_container(self, container_name: str) -> ContainerProxy:
        """Get container by name"""
        container_proxy = self.containers.get(container_name)
        if not container_proxy:
            self.containers[container_name] = self._ensure_container(container_name)
        
        return self.containers[container_name]
    
    async def create(self, container_name: str, item: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new item"""
        _container = self.get_container(container_name)
        return await _container.create_item(body=item)
    
    async def get_by_id(self, container_name: str, item_id: str) -> Optional[Dict[str, Any]]:
        """Get item by ID"""
        try:
            _container = self.get_container(container_name)
            return await _container.read_item(item=item_id, partition_key=item_id)
        except exceptions.CosmosResourceNotFoundError:
            return None
    
    async def list_all(self, container_name: str, query: Optional[str] = None, parameters: Optional[List[Dict[str, Any]]] = None) -> List[Dict[str, Any]]:
        """List all items"""
        _container = self.get_container(container_name)
        
        result  = []
        if query:
            async for item in _container.query_items(query=query, parameters=parameters, enable_cross_partition_query=True):
                result.append(item)
        else:
            async for item in _container.read_all_items():
                result.append(item)
        
        return result
    
    async def query(self, container_name: str, query: str, parameters: Optional[List[Dict[str, Any]]] = None) -> List[Dict[str, Any]]:
        """Execute a query"""
        _container = self.get_container(container_name)
        result = []
        
        async for item in _container.query_items(query=query, parameters=parameters):
            result.append(item)
        
        return result
    
    async def update(self, container_name: str, item: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing item"""
        _container = self.get_container(container_name)
        return await _container.upsert_item(body=item)
    
    async def delete(self, container_name: str, item_id: str) -> bool:
        """Delete an item by ID"""
        try:
            _container = self.get_container(container_name)
            await _container.delete_item(item=item_id, partition_key=item_id)
            return True
        except Exception:
            return False
    
    async def batch_upsert(self, container_name: str, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Batch upsert items"""
        
        results = [ result for item in items for result in await self.update(container_name, item) ]
        
        return results
