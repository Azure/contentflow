"""
Azure Cosmos DB Gremlin API connector for graph database operations.

This connector provides access to Azure Cosmos DB Graph API (Gremlin)
for creating, querying, and managing knowledge graphs.
"""

import logging
from typing import Dict, Any, Optional, List, Union
from gremlin_python.driver import client, serializer
from gremlin_python.driver.protocol import GremlinServerError
import asyncio

from .base import ConnectorBase

logger = logging.getLogger("contentflow.lib.connectors.cosmos_gremlin")


class CosmosGremlinConnector(ConnectorBase):
    """
    Azure Cosmos DB Gremlin API connector.
    
    Provides access to Azure Cosmos DB Graph API for knowledge graph
    construction, querying, and management using Gremlin queries.
    
    Configuration:
        - endpoint: Cosmos DB Gremlin endpoint (e.g., 'wss://account.gremlin.cosmos.azure.com:443/')
        - database: Database name
        - collection: Graph collection/container name
        - username: Username in format '/dbs/{database}/colls/{collection}'
        - password: Primary or secondary key
        - enable_ssl: Enable SSL (default: True)
        - max_retries: Maximum retry attempts (default: 3)
        - connection_pool_size: Connection pool size (default: 4)
    
    Example:
        ```python
        connector = CosmosGremlinConnector(
            name="knowledge_graph",
            settings={
                "endpoint": "${COSMOS_GREMLIN_ENDPOINT}",
                "database": "knowledge",
                "collection": "entities",
                "username": "/dbs/knowledge/colls/entities",
                "password": "${COSMOS_PRIMARY_KEY}"
            }
        )
        
        await connector.initialize()
        
        # Execute query
        results = await connector.execute_query("g.V().count()")
        ```
    """
    
    def __init__(
        self,
        name: str,
        settings: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        """Initialize the Cosmos DB Gremlin connector."""
        super().__init__(
            name=name,
            connector_type="cosmos_gremlin",
            settings=settings,
            **kwargs
        )
        
        self._client: Optional[client.Client] = None
        self._is_initialized = False
        
        # Resolve settings
        self.endpoint = self._resolve_setting("endpoint", required=True)
        self.database = self._resolve_setting("database", required=True)
        self.collection = self._resolve_setting("collection", required=True)
        
        # Username format: /dbs/{database}/colls/{collection}
        self.username = self._resolve_setting(
            "username",
            required=False,
            default=f"/dbs/{self.database}/colls/{self.collection}"
        )
        self.password = self._resolve_setting("password", required=True)
        
        # Connection options
        self.enable_ssl = self._resolve_setting("enable_ssl", required=False, default=True)
        self.max_retries = self._resolve_setting("max_retries", required=False, default=3)
        self.connection_pool_size = self._resolve_setting("connection_pool_size", required=False, default=4)
        
        logger.debug(
            f"CosmosGremlinConnector initialized: endpoint={self.endpoint}, "
            f"database={self.database}, collection={self.collection}"
        )
    
    async def initialize(self) -> None:
        """Initialize the Gremlin client connection."""
        if self._is_initialized:
            logger.debug(f"Connector '{self.name}' already initialized")
            return
        
        try:
            logger.info(f"Initializing Cosmos DB Gremlin connector: {self.name}")
            
            # Create Gremlin client
            self._client = client.Client(
                url=self.endpoint,
                traversal_source='g',
                username=self.username,
                password=self.password,
                message_serializer=serializer.GraphSONSerializersV2d0()
            )
            
            # Test connection
            test_result = await self._execute_sync_query("g.V().limit(1).count()")
            
            self._is_initialized = True
            logger.info(
                f"Cosmos DB Gremlin connector '{self.name}' initialized successfully. "
                f"Test query executed."
            )
            
        except Exception as e:
            logger.error(f"Failed to initialize Cosmos DB Gremlin connector '{self.name}': {e}")
            raise
    
    async def test_connection(self) -> bool:
        """
        Test the Gremlin connection.
        
        Returns:
            True if connection is successful
        """
        try:
            if not self._is_initialized:
                await self.initialize()
            
            # Execute simple count query
            result = await self._execute_sync_query("g.V().count()")
            logger.info(f"Gremlin connection test successful for '{self.name}'. Vertex count: {result}")
            return True
            
        except Exception as e:
            logger.error(f"Gremlin connection test failed for '{self.name}': {e}")
            return False
    
    async def cleanup(self) -> None:
        """Cleanup the Gremlin client connection."""
        if self._client:
            try:
                self._client.close()
                logger.info(f"Cosmos DB Gremlin connector '{self.name}' cleaned up")
            except Exception as e:
                logger.error(f"Error cleaning up connector '{self.name}': {e}")
            finally:
                self._client = None
                self._is_initialized = False
    
    async def _execute_sync_query(self, query: str) -> Any:
        """
        Execute a Gremlin query synchronously (wrapper for sync client).
        
        Args:
            query: Gremlin query string
            
        Returns:
            Query results
        """
        if not self._client:
            raise RuntimeError("Gremlin client not initialized. Call initialize() first.")
        
        loop = asyncio.get_event_loop()
        
        def _submit_query():
            callback = self._client.submitAsync(query)
            return callback.result()
        
        result = await loop.run_in_executor(None, _submit_query)
        return result.all().result()
    
    async def execute_query(
        self,
        query: str,
        bindings: Optional[Dict[str, Any]] = None
    ) -> List[Any]:
        """
        Execute a Gremlin query.
        
        Args:
            query: Gremlin query string
            bindings: Optional query parameter bindings
            
        Returns:
            List of query results
            
        Example:
            ```python
            # Simple query
            results = await connector.execute_query("g.V().has('type', 'person').values('name')")
            
            # Query with bindings
            results = await connector.execute_query(
                "g.V().has('id', id_val)",
                bindings={'id_val': 'person-123'}
            )
            ```
        """
        if not self._is_initialized:
            await self.initialize()
        
        try:
            logger.debug(f"Executing Gremlin query: {query[:100]}...")
            
            if bindings:
                # For parameterized queries, we need to format them
                # Gremlin Python client handles bindings differently
                for key, value in bindings.items():
                    if isinstance(value, str):
                        query = query.replace(f"{key}", f"'{value}'")
                    else:
                        query = query.replace(f"{key}", str(value))
            
            results = await self._execute_sync_query(query)
            
            logger.debug(f"Query returned {len(results) if results else 0} results")
            return results if results else []
            
        except GremlinServerError as e:
            logger.error(f"Gremlin server error executing query: {e}")
            raise
        except Exception as e:
            logger.error(f"Error executing Gremlin query: {e}")
            raise
    
    async def add_vertex(
        self,
        label: str,
        vertex_id: str,
        properties: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Add a vertex to the graph.
        
        Args:
            label: Vertex label (e.g., 'person', 'document', 'organization')
            vertex_id: Unique vertex identifier
            properties: Vertex properties as key-value pairs
            
        Returns:
            Created vertex data
            
        Example:
            ```python
            vertex = await connector.add_vertex(
                label='person',
                vertex_id='person-123',
                properties={'name': 'John Doe', 'role': 'Manager'}
            )
            ```
        """
        # Build property string for Gremlin query
        prop_strings = [f"property('{k}', '{v}')" for k, v in properties.items()]
        props = ".".join(prop_strings)
        
        query = f"g.addV('{label}').property('id', '{vertex_id}')"
        if props:
            query += f".{props}"
        
        results = await self.execute_query(query)
        return results[0] if results else {}
    
    async def add_edge(
        self,
        edge_label: str,
        from_vertex_id: str,
        to_vertex_id: str,
        properties: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Add an edge between two vertices.
        
        Args:
            edge_label: Edge label (e.g., 'knows', 'works_at', 'authored')
            from_vertex_id: Source vertex ID
            to_vertex_id: Target vertex ID
            properties: Optional edge properties
            
        Returns:
            Created edge data
            
        Example:
            ```python
            edge = await connector.add_edge(
                edge_label='authored',
                from_vertex_id='person-123',
                to_vertex_id='document-456',
                properties={'date': '2025-01-01'}
            )
            ```
        """
        query = (
            f"g.V('{from_vertex_id}').addE('{edge_label}').to(g.V('{to_vertex_id}'))"
        )
        
        if properties:
            prop_strings = [f"property('{k}', '{v}')" for k, v in properties.items()]
            query += "." + ".".join(prop_strings)
        
        results = await self.execute_query(query)
        return results[0] if results else {}
    
    async def update_vertex(
        self,
        vertex_id: str,
        properties: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update vertex properties.
        
        Args:
            vertex_id: Vertex ID to update
            properties: Properties to update/add
            
        Returns:
            Updated vertex data
        """
        prop_strings = [f"property('{k}', '{v}')" for k, v in properties.items()]
        props = ".".join(prop_strings)
        
        query = f"g.V('{vertex_id}').{props}"
        results = await self.execute_query(query)
        return results[0] if results else {}
    
    async def get_vertex(self, vertex_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a vertex by ID.
        
        Args:
            vertex_id: Vertex ID
            
        Returns:
            Vertex data or None if not found
        """
        query = f"g.V('{vertex_id}')"
        results = await self.execute_query(query)
        return results[0] if results else None
    
    async def delete_vertex(self, vertex_id: str) -> bool:
        """
        Delete a vertex and its edges.
        
        Args:
            vertex_id: Vertex ID to delete
            
        Returns:
            True if deleted successfully
        """
        try:
            query = f"g.V('{vertex_id}').drop()"
            await self.execute_query(query)
            return True
        except Exception as e:
            logger.error(f"Error deleting vertex '{vertex_id}': {e}")
            return False
    
    async def count_vertices(self, label: Optional[str] = None) -> int:
        """
        Count vertices in the graph.
        
        Args:
            label: Optional label to filter by
            
        Returns:
            Vertex count
        """
        if label:
            query = f"g.V().hasLabel('{label}').count()"
        else:
            query = "g.V().count()"
        
        results = await self.execute_query(query)
        return int(results[0]) if results else 0
    
    async def count_edges(self, label: Optional[str] = None) -> int:
        """
        Count edges in the graph.
        
        Args:
            label: Optional label to filter by
            
        Returns:
            Edge count
        """
        if label:
            query = f"g.E().hasLabel('{label}').count()"
        else:
            query = "g.E().count()"
        
        results = await self.execute_query(query)
        return int(results[0]) if results else 0
    
    async def traverse(
        self,
        start_vertex_id: str,
        edge_label: Optional[str] = None,
        direction: str = "out",
        max_depth: int = 1
    ) -> List[Dict[str, Any]]:
        """
        Traverse the graph from a starting vertex.
        
        Args:
            start_vertex_id: Starting vertex ID
            edge_label: Optional edge label to follow
            direction: Traversal direction ('out', 'in', 'both')
            max_depth: Maximum traversal depth
            
        Returns:
            List of connected vertices
        """
        if direction not in ["out", "in", "both"]:
            raise ValueError(f"Invalid direction: {direction}. Must be 'out', 'in', or 'both'")
        
        # Build traversal query
        if edge_label:
            if direction == "out":
                traversal = f"outE('{edge_label}').inV()"
            elif direction == "in":
                traversal = f"inE('{edge_label}').outV()"
            else:
                traversal = f"bothE('{edge_label}').otherV()"
        else:
            if direction == "out":
                traversal = "out()"
            elif direction == "in":
                traversal = "in()"
            else:
                traversal = "both()"
        
        # Repeat for depth
        repeat_clause = f"repeat({traversal}).times({max_depth})" if max_depth > 1 else traversal
        
        query = f"g.V('{start_vertex_id}').{repeat_clause}"
        results = await self.execute_query(query)
        return results if results else []
