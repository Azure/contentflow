"""
Knowledge Graph Writer Executor.

This executor writes entities and relationships to Azure Cosmos DB Graph API,
building a comprehensive and evolving knowledge graph of business content.
"""

import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

from agent_framework import WorkflowContext

from .parallel_executor import ParallelExecutor
from ..connectors.cosmos_gremlin_connector import CosmosGremlinConnector
from ..models import Content

logger = logging.getLogger("contentflow.executors.knowledge_graph_writer")


class KnowledgeGraphWriterExecutor(ParallelExecutor):
    """
    Write entities and relationships to Cosmos DB Graph API.
    
    This executor takes extracted entities and relationships from content
    and persists them to a knowledge graph, supporting:
    - Entity deduplication and merging
    - Relationship creation with properties
    - Graph evolution (updating existing entities)
    - Metadata tracking (source documents, timestamps)
    
    Configuration:
        gremlin_endpoint: Cosmos DB Gremlin endpoint
        gremlin_database: Database name
        gremlin_collection: Graph collection name
        gremlin_username: Username (or auto-generated from db/collection)
        gremlin_password: Primary/secondary key
        input_field: Field containing extracted entities (default: 'knowledge_graph_entities')
        merge_strategy: How to handle existing entities ('merge', 'overwrite', 'skip')
        enable_deduplication: Whether to merge duplicate entities
        add_timestamps: Add creation/update timestamps to entities
        batch_size: Number of entities to write per batch
    """
    
    def __init__(
        self,
        id: str,
        settings: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        """Initialize the knowledge graph writer."""
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
        
        # Processing settings
        self.input_field = self.get_setting("input_field", default="knowledge_graph_entities")
        self.merge_strategy = self.get_setting("merge_strategy", default="merge")
        self.enable_deduplication = self.get_setting("enable_deduplication", default=True)
        self.add_timestamps = self.get_setting("add_timestamps", default=True)
        self.batch_size = self.get_setting("batch_size", default=20)
        
        # Output field for statistics
        self.output_field = self.get_setting("output_field", default="graph_write_stats")
        
        # Validate merge strategy
        if self.merge_strategy not in ["merge", "overwrite", "skip"]:
            raise ValueError(
                f"Invalid merge_strategy: {self.merge_strategy}. "
                "Must be 'merge', 'overwrite', or 'skip'"
            )
        
        # Initialize connector
        self._connector: Optional[CosmosGremlinConnector] = None
        
        logger.debug(
            f"KnowledgeGraphWriterExecutor initialized: "
            f"database={self.gremlin_database}, collection={self.gremlin_collection}, "
            f"merge_strategy={self.merge_strategy}"
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
    
    def _sanitize_property_value(self, value: Any) -> str:
        """
        Sanitize property values for Gremlin queries.
        
        Args:
            value: Property value
            
        Returns:
            Sanitized string value
        """
        if value is None:
            return ""
        
        # Convert to string and escape single quotes
        str_value = str(value).replace("'", "\\'")
        
        # Truncate if too long (Cosmos DB has property size limits)
        max_length = 1000
        if len(str_value) > max_length:
            str_value = str_value[:max_length] + "..."
        
        return str_value
    
    async def _write_entity(
        self,
        connector: CosmosGremlinConnector,
        entity: Dict[str, Any]
    ) -> bool:
        """
        Write a single entity to the graph.
        
        Args:
            connector: Gremlin connector
            entity: Entity data
            
        Returns:
            True if successful
        """
        try:
            entity_id = entity.get("id")
            label = entity.get("label", "Entity")
            name = entity.get("name", "Unknown")
            properties = entity.get("properties", {})
            
            if not entity_id:
                logger.warning("Entity missing ID, skipping")
                return False
            
            # Check if entity exists
            existing = await connector.get_vertex(entity_id)
            
            if existing:
                if self.merge_strategy == "skip":
                    logger.debug(f"Entity {entity_id} exists, skipping (merge_strategy=skip)")
                    return True
                elif self.merge_strategy == "merge":
                    # Update existing entity with new properties
                    update_props = {
                        k: self._sanitize_property_value(v)
                        for k, v in properties.items()
                    }
                    update_props["name"] = self._sanitize_property_value(name)
                    
                    if self.add_timestamps:
                        update_props["updated_at"] = datetime.utcnow().isoformat()
                    
                    await connector.update_vertex(entity_id, update_props)
                    logger.debug(f"Merged entity {entity_id}")
                    return True
                else:  # overwrite
                    # Delete and recreate
                    await connector.delete_vertex(entity_id)
            
            # Create new entity
            vertex_props = {
                "name": self._sanitize_property_value(name),
                **{k: self._sanitize_property_value(v) for k, v in properties.items()}
            }
            
            if self.add_timestamps:
                vertex_props["created_at"] = datetime.utcnow().isoformat()
                vertex_props["updated_at"] = datetime.utcnow().isoformat()
            
            await connector.add_vertex(
                label=label,
                vertex_id=entity_id,
                properties=vertex_props
            )
            
            logger.debug(f"Created entity {entity_id} with label {label}")
            return True
            
        except Exception as e:
            logger.error(f"Error writing entity {entity.get('id', 'unknown')}: {e}")
            return False
    
    async def _write_relationship(
        self,
        connector: CosmosGremlinConnector,
        relationship: Dict[str, Any]
    ) -> bool:
        """
        Write a single relationship to the graph.
        
        Args:
            connector: Gremlin connector
            relationship: Relationship data
            
        Returns:
            True if successful
        """
        try:
            from_id = relationship.get("from_entity_id")
            to_id = relationship.get("to_entity_id")
            rel_type = relationship.get("relationship_type", "related_to")
            properties = relationship.get("properties", {})
            
            if not from_id or not to_id:
                logger.warning("Relationship missing from/to entity IDs, skipping")
                return False
            
            # Check if both vertices exist
            from_vertex = await connector.get_vertex(from_id)
            to_vertex = await connector.get_vertex(to_id)
            
            if not from_vertex:
                logger.warning(f"Source vertex {from_id} not found, skipping relationship")
                return False
            
            if not to_vertex:
                logger.warning(f"Target vertex {to_id} not found, skipping relationship")
                return False
            
            # Add edge properties
            edge_props = {
                k: self._sanitize_property_value(v)
                for k, v in properties.items()
            }
            
            if self.add_timestamps:
                edge_props["created_at"] = datetime.utcnow().isoformat()
            
            await connector.add_edge(
                edge_label=rel_type,
                from_vertex_id=from_id,
                to_vertex_id=to_id,
                properties=edge_props
            )
            
            logger.debug(f"Created relationship {rel_type} from {from_id} to {to_id}")
            return True
            
        except Exception as e:
            logger.error(
                f"Error writing relationship {relationship.get('relationship_type', 'unknown')}: {e}"
            )
            return False
    
    async def process_content_item(
        self,
        content: Content,
        ctx: WorkflowContext
    ) -> Content:
        """
        Write knowledge graph entities and relationships from content.
        
        Args:
            content: Content with extracted entities
            ctx: Workflow context
            
        Returns:
            Content with write statistics
        """
        try:
            logger.info(f"Writing knowledge graph for content: {content.content_id}")
            
            # Get extracted entities
            kg_data = content.summary_data.get(self.input_field, {})
            
            if not kg_data or not isinstance(kg_data, dict):
                logger.warning(
                    f"No knowledge graph data found in field '{self.input_field}' "
                    f"for content {content.content_id}"
                )
                content.summary_data[self.output_field] = {
                    "entities_written": 0,
                    "relationships_written": 0,
                    "error": "No knowledge graph data found"
                }
                return content
            
            entities = kg_data.get("entities", [])
            relationships = kg_data.get("relationships", [])
            
            if not entities:
                logger.info(f"No entities to write for content {content.content_id}")
                content.summary_data[self.output_field] = {
                    "entities_written": 0,
                    "relationships_written": 0
                }
                return content
            
            # Get connector
            connector = await self._get_connector()
            
            # Write entities
            entities_written = 0
            for entity in entities:
                success = await self._write_entity(connector, entity)
                if success:
                    entities_written += 1
            
            # Write relationships
            relationships_written = 0
            for relationship in relationships:
                success = await self._write_relationship(connector, relationship)
                if success:
                    relationships_written += 1
            
            # Store statistics
            stats = {
                "entities_written": entities_written,
                "entities_total": len(entities),
                "relationships_written": relationships_written,
                "relationships_total": len(relationships),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            content.summary_data[self.output_field] = stats
            
            logger.info(
                f"Knowledge graph write completed for {content.content_id}: "
                f"{entities_written}/{len(entities)} entities, "
                f"{relationships_written}/{len(relationships)} relationships"
            )
            
            return content
            
        except Exception as e:
            logger.error(f"Error writing knowledge graph for content {content.content_id}: {e}")
            if self.fail_on_error:
                raise
            
            content.summary_data[self.output_field] = {
                "entities_written": 0,
                "relationships_written": 0,
                "error": str(e)
            }
            return content
