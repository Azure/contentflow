"""
Knowledge Graph Query Executor.

This executor queries the knowledge graph to retrieve entities, traverse
relationships, and enrich content with graph-based insights.
"""

import json
import logging
from typing import Any, Dict, List, Optional

from agent_framework import WorkflowContext

from .base import BaseExecutor
from ..connectors.cosmos_gremlin_connector import CosmosGremlinConnector
from ..models import Content

logger = logging.getLogger("contentflow.executors.knowledge_graph_query")


class KnowledgeGraphQueryExecutor(BaseExecutor):
    """
    Query knowledge graph for entity retrieval and relationship traversal.
    
    This executor provides various query capabilities:
    - Find entities by ID, name, or properties
    - Traverse relationships (find connected entities)
    - Pattern matching (find paths between entities)
    - Aggregate queries (count, group by)
    - Enrich content with related entities
    
    Configuration:
        gremlin_endpoint: Cosmos DB Gremlin endpoint
        gremlin_database: Database name
        gremlin_collection: Graph collection name
        gremlin_username: Username
        gremlin_password: Primary/secondary key
        query_type: Type of query ('find_entity', 'traverse', 'pattern_match', 'custom')
        query_parameters: Parameters for the query
        output_field: Field to store query results
        max_results: Maximum number of results to return
    """
    
    def __init__(
        self,
        id: str,
        settings: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        """Initialize the knowledge graph query executor."""
        super().__init__(id=id, settings=settings, **kwargs)
        
        # Gremlin connection settings
        self.gremlin_endpoint = self.get_setting("gremlin_endpoint", required=True)
        self.gremlin_database = self.get_setting("gremlin_database", required=True)
        self.gremlin_collection = self.get_setting("gremlin_collection", required=True)
        self.gremlin_username = self.get_setting(
            "gremlin_username",
            default=f"/dbs/{self.gremlin_database}/colls/{self.gremlin_collection}"
        )
        self.gremlin_password = self.get_setting("gremlin_password", required=True)
        
        # Query settings
        self.query_type = self.get_setting("query_type", default="find_entity")
        self.query_parameters = self.get_setting("query_parameters", default={})
        self.output_field = self.get_setting("output_field", default="graph_query_results")
        self.max_results = self.get_setting("max_results", default=100)
        
        # Validate query type
        valid_types = ["find_entity", "traverse", "pattern_match", "aggregate", "custom"]
        if self.query_type not in valid_types:
            raise ValueError(
                f"Invalid query_type: {self.query_type}. "
                f"Must be one of {valid_types}"
            )
        
        # Initialize connector
        self._connector: Optional[CosmosGremlinConnector] = None
        
        logger.debug(
            f"KnowledgeGraphQueryExecutor initialized: "
            f"query_type={self.query_type}, max_results={self.max_results}"
        )
    
    async def _get_connector(self) -> CosmosGremlinConnector:
        """Get or initialize the Gremlin connector."""
        if self._connector is None:
            connector_settings = {
                "endpoint": self.gremlin_endpoint,
                "database": self.gremlin_database,
                "collection": self.gremlin_collection,
                "username": self.gremlin_username,
                "password": self.gremlin_password
            }
            
            self._connector = CosmosGremlinConnector(
                name=f"gremlin_connector_{self.id}",
                settings=connector_settings
            )
            await self._connector.initialize()
        
        return self._connector
    
    async def _find_entity_query(
        self,
        connector: CosmosGremlinConnector,
        params: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Find entities by criteria.
        
        Params:
            entity_id: Specific entity ID (optional)
            label: Entity label/type (optional)
            property_name: Property to filter on (optional)
            property_value: Value to match (optional)
        """
        entity_id = params.get("entity_id")
        label = params.get("label")
        property_name = params.get("property_name")
        property_value = params.get("property_value")
        
        if entity_id:
            # Find specific entity
            query = f"g.V('{entity_id}')"
        elif label and property_name and property_value:
            # Find by label and property
            query = f"g.V().hasLabel('{label}').has('{property_name}', '{property_value}').limit({self.max_results})"
        elif label:
            # Find by label only
            query = f"g.V().hasLabel('{label}').limit({self.max_results})"
        elif property_name and property_value:
            # Find by property only
            query = f"g.V().has('{property_name}', '{property_value}').limit({self.max_results})"
        else:
            # Get all vertices (limited)
            query = f"g.V().limit({self.max_results})"
        
        results = await connector.execute_query(query)
        return results
    
    async def _traverse_query(
        self,
        connector: CosmosGremlinConnector,
        params: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Traverse relationships from a starting entity.
        
        Params:
            start_entity_id: Starting entity ID (required)
            edge_label: Relationship type to follow (optional)
            direction: 'out', 'in', or 'both' (default: 'out')
            max_depth: Maximum traversal depth (default: 2)
        """
        start_id = params.get("start_entity_id")
        if not start_id:
            raise ValueError("start_entity_id is required for traverse query")
        
        edge_label = params.get("edge_label")
        direction = params.get("direction", "out")
        max_depth = params.get("max_depth", 2)
        
        results = await connector.traverse(
            start_vertex_id=start_id,
            edge_label=edge_label,
            direction=direction,
            max_depth=max_depth
        )
        
        return results[:self.max_results]
    
    async def _pattern_match_query(
        self,
        connector: CosmosGremlinConnector,
        params: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Find patterns in the graph.
        
        Params:
            pattern_type: Type of pattern ('shortest_path', 'common_neighbors', 'similar_entities')
            entity_a_id: First entity ID
            entity_b_id: Second entity ID (for path/neighbor queries)
        """
        pattern_type = params.get("pattern_type", "shortest_path")
        entity_a = params.get("entity_a_id")
        
        if not entity_a:
            raise ValueError("entity_a_id is required for pattern matching")
        
        if pattern_type == "shortest_path":
            entity_b = params.get("entity_b_id")
            if not entity_b:
                raise ValueError("entity_b_id is required for shortest_path")
            
            # Find shortest path between entities
            query = f"g.V('{entity_a}').repeat(out().simplePath()).until(hasId('{entity_b}')).path().limit(1)"
        
        elif pattern_type == "common_neighbors":
            entity_b = params.get("entity_b_id")
            if not entity_b:
                raise ValueError("entity_b_id is required for common_neighbors")
            
            # Find entities connected to both
            query = f"g.V('{entity_a}').out().where(__.in().hasId('{entity_b}')).limit({self.max_results})"
        
        elif pattern_type == "similar_entities":
            # Find entities with similar connections
            query = f"g.V('{entity_a}').both().groupCount().order(local).by(values, desc).limit({self.max_results})"
        
        else:
            raise ValueError(f"Unknown pattern_type: {pattern_type}")
        
        results = await connector.execute_query(query)
        return results
    
    async def _aggregate_query(
        self,
        connector: CosmosGremlinConnector,
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Aggregate queries for statistics.
        
        Params:
            aggregation_type: 'count', 'group_by', 'distribution'
            label: Entity label to aggregate (optional)
            property_name: Property for grouping (for group_by)
        """
        agg_type = params.get("aggregation_type", "count")
        label = params.get("label")
        
        if agg_type == "count":
            # Count vertices by label
            if label:
                vertex_count = await connector.count_vertices(label)
                edge_count = await connector.count_edges(label)
            else:
                vertex_count = await connector.count_vertices()
                edge_count = await connector.count_edges()
            
            return {
                "vertex_count": vertex_count,
                "edge_count": edge_count,
                "label": label
            }
        
        elif agg_type == "group_by":
            property_name = params.get("property_name")
            if not property_name:
                raise ValueError("property_name required for group_by aggregation")
            
            query_base = f"g.V()"
            if label:
                query_base += f".hasLabel('{label}')"
            
            query = f"{query_base}.groupCount().by('{property_name}')"
            results = await connector.execute_query(query)
            
            return {
                "aggregation_type": "group_by",
                "property": property_name,
                "results": results[0] if results else {}
            }
        
        elif agg_type == "distribution":
            # Get label distribution
            query = "g.V().groupCount().by(label)"
            results = await connector.execute_query(query)
            
            return {
                "aggregation_type": "distribution",
                "label_distribution": results[0] if results else {}
            }
        
        else:
            raise ValueError(f"Unknown aggregation_type: {agg_type}")
    
    async def _custom_query(
        self,
        connector: CosmosGremlinConnector,
        params: Dict[str, Any]
    ) -> List[Any]:
        """
        Execute a custom Gremlin query.
        
        Params:
            query: Gremlin query string (required)
        """
        query = params.get("query")
        if not query:
            raise ValueError("query parameter required for custom query type")
        
        results = await connector.execute_query(query)
        return results[:self.max_results]
    
    async def process_contents(
        self,
        contents: List[Content],
        ctx: WorkflowContext
    ) -> List[Content]:
        """
        Execute knowledge graph queries.
        
        Args:
            contents: Input contents (query can use content data)
            ctx: Workflow context
            
        Returns:
            Contents with query results
        """
        try:
            logger.info(f"Executing knowledge graph query: type={self.query_type}")
            
            # Get connector
            connector = await self._get_connector()
            
            # Execute query based on type
            if self.query_type == "find_entity":
                results = await self._find_entity_query(connector, self.query_parameters)
            elif self.query_type == "traverse":
                results = await self._traverse_query(connector, self.query_parameters)
            elif self.query_type == "pattern_match":
                results = await self._pattern_match_query(connector, self.query_parameters)
            elif self.query_type == "aggregate":
                results = await self._aggregate_query(connector, self.query_parameters)
            elif self.query_type == "custom":
                results = await self._custom_query(connector, self.query_parameters)
            else:
                raise ValueError(f"Unsupported query type: {self.query_type}")
            
            # Store results in all content items
            for content in contents:
                content.summary_data[self.output_field] = {
                    "query_type": self.query_type,
                    "results": results,
                    "result_count": len(results) if isinstance(results, list) else 1
                }
            
            logger.info(
                f"Knowledge graph query completed: "
                f"{len(results) if isinstance(results, list) else 1} results"
            )
            
            return contents
            
        except Exception as e:
            logger.error(f"Error executing knowledge graph query: {e}")
            if self.fail_on_error:
                raise
            
            for content in contents:
                content.summary_data[self.output_field] = {
                    "query_type": self.query_type,
                    "error": str(e),
                    "results": []
                }
            
            return contents
