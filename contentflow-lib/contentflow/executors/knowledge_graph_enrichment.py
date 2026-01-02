"""
Knowledge Graph Enrichment Executor.

This executor enriches existing knowledge graph entities with additional
properties, inferred relationships, and AI-generated insights.
"""

import json
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

from agent_framework import WorkflowContext

from .parallel_executor import ParallelExecutor
from ..connectors.cosmos_gremlin_connector import CosmosGremlinConnector
from ..connectors.ai_inference_connector import AIInferenceConnector
from ..models import Content

logger = logging.getLogger("contentflow.executors.knowledge_graph_enrichment")


class KnowledgeGraphEnrichmentExecutor(ParallelExecutor):
    """
    Enrich knowledge graph entities with additional information and relationships.
    
    This executor enhances the knowledge graph by:
    - Adding inferred properties to entities
    - Discovering implicit relationships
    - Enriching entities with external data
    - Computing derived attributes
    - Identifying entity clusters and communities
    
    Configuration:
        gremlin_endpoint: Cosmos DB Gremlin endpoint
        gremlin_database: Database name
        gremlin_collection: Graph collection name
        gremlin_username: Username
        gremlin_password: Primary/secondary key
        enrichment_type: Type of enrichment ('ai_properties', 'infer_relationships', 'compute_metrics')
        ai_endpoint: Azure AI endpoint (for AI-based enrichment)
        ai_api_key: API key for AI service
        model_name: AI model for enrichment
        entity_selector: How to select entities ('all', 'by_label', 'by_property')
        selector_criteria: Criteria for entity selection
        output_field: Field to store enrichment stats
    """
    
    def __init__(
        self,
        id: str,
        settings: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        """Initialize the knowledge graph enrichment executor."""
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
        
        # Enrichment settings
        self.enrichment_type = self.get_setting("enrichment_type", required=True)
        self.entity_selector = self.get_setting("entity_selector", default="all")
        self.selector_criteria = self.get_setting("selector_criteria", default={})
        
        # AI settings (for AI-based enrichment)
        self.ai_endpoint = self.get_setting("ai_endpoint", required=False)
        self.ai_credential_type = self.get_setting("ai_credential_type", default="default_azure_credential")
        self.ai_api_key = self.get_setting("ai_api_key", required=False)
        self.model_name = self.get_setting("model_name", required=False)
        
        # Output settings
        self.output_field = self.get_setting("output_field", default="graph_enrichment_stats")
        self.batch_size = self.get_setting("batch_size", default=10)
        
        # Validate enrichment type
        valid_types = ["ai_properties", "infer_relationships", "compute_metrics", "entity_classification"]
        if self.enrichment_type not in valid_types:
            raise ValueError(
                f"Invalid enrichment_type: {self.enrichment_type}. "
                f"Must be one of {valid_types}"
            )
        
        # Initialize connectors
        self._gremlin_connector: Optional[CosmosGremlinConnector] = None
        self._ai_connector: Optional[AIInferenceConnector] = None
        
        logger.debug(
            f"KnowledgeGraphEnrichmentExecutor initialized: "
            f"enrichment_type={self.enrichment_type}, selector={self.entity_selector}"
        )
    
    async def _get_gremlin_connector(self) -> CosmosGremlinConnector:
        """Get or initialize the Gremlin connector."""
        if self._gremlin_connector is None:
            connector_settings = {
                "endpoint": self.gremlin_endpoint,
                "database": self.gremlin_database,
                "collection": self.gremlin_collection,
                "username": self.gremlin_username,
                "password": self.gremlin_password
            }
            
            self._gremlin_connector = CosmosGremlinConnector(
                name=f"gremlin_connector_{self.id}",
                settings=connector_settings
            )
            await self._gremlin_connector.initialize()
        
        return self._gremlin_connector
    
    async def _get_ai_connector(self) -> AIInferenceConnector:
        """Get or initialize the AI connector."""
        if self._ai_connector is None:
            if not self.ai_endpoint:
                raise ValueError("ai_endpoint required for AI-based enrichment")
            
            connector_settings = {
                "endpoint": self.ai_endpoint,
                "credential_type": self.ai_credential_type,
            }
            
            if self.ai_api_key:
                connector_settings["api_key"] = self.ai_api_key
            
            self._ai_connector = AIInferenceConnector(
                name=f"ai_connector_{self.id}",
                settings=connector_settings
            )
            await self._ai_connector.initialize()
        
        return self._ai_connector
    
    async def _select_entities(
        self,
        gremlin: CosmosGremlinConnector
    ) -> List[Dict[str, Any]]:
        """
        Select entities to enrich based on criteria.
        
        Returns:
            List of entity dictionaries
        """
        if self.entity_selector == "all":
            query = f"g.V().limit(100)"
        
        elif self.entity_selector == "by_label":
            label = self.selector_criteria.get("label")
            if not label:
                raise ValueError("label required in selector_criteria for by_label selector")
            query = f"g.V().hasLabel('{label}').limit(100)"
        
        elif self.entity_selector == "by_property":
            prop_name = self.selector_criteria.get("property_name")
            prop_value = self.selector_criteria.get("property_value")
            if not prop_name or not prop_value:
                raise ValueError(
                    "property_name and property_value required in selector_criteria "
                    "for by_property selector"
                )
            query = f"g.V().has('{prop_name}', '{prop_value}').limit(100)"
        
        else:
            raise ValueError(f"Unknown entity_selector: {self.entity_selector}")
        
        entities = await gremlin.execute_query(query)
        return entities
    
    async def _enrich_with_ai_properties(
        self,
        gremlin: CosmosGremlinConnector,
        ai: AIInferenceConnector,
        entity: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Use AI to generate additional properties for an entity.
        
        Args:
            gremlin: Gremlin connector
            ai: AI connector
            entity: Entity to enrich
            
        Returns:
            Enrichment results
        """
        try:
            # Extract entity information
            entity_id = entity.get("id")
            entity_label = entity.get("label", "Entity")
            entity_name = entity.get("properties", {}).get("name", ["Unknown"])[0]
            
            # Build enrichment prompt
            prompt = f"""You are a knowledge graph enrichment expert. Analyze this entity and generate additional properties.

Entity Type: {entity_label}
Entity Name: {entity_name}
Existing Properties: {json.dumps(entity.get("properties", {}), indent=2)}

Generate the following enrichments:
1. A concise description (2-3 sentences)
2. Category or classification
3. Key attributes relevant to this entity type
4. Potential tags or keywords

Return ONLY valid JSON in this format:
{{
    "description": "entity description",
    "category": "category name",
    "attributes": {{"key": "value"}},
    "tags": ["tag1", "tag2"]
}}
"""
            
            messages = [
                {"role": "system", "content": "You are a knowledge graph enrichment expert. Always respond with valid JSON only."},
                {"role": "user", "content": prompt}
            ]
            
            response = await ai.chat_completion(
                messages=messages,
                model=self.model_name,
                temperature=0.3,
                max_tokens=500
            )
            
            # Parse response
            response_text = response.choices[0].message.content.strip()
            
            # Remove markdown if present
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            
            response_text = response_text.strip()
            enrichment_data = json.loads(response_text)
            
            # Update entity with new properties
            update_props = {}
            
            if "description" in enrichment_data:
                update_props["ai_description"] = str(enrichment_data["description"])[:1000]
            
            if "category" in enrichment_data:
                update_props["ai_category"] = str(enrichment_data["category"])[:200]
            
            if "tags" in enrichment_data:
                update_props["ai_tags"] = ",".join(enrichment_data["tags"][:10])
            
            if "attributes" in enrichment_data and isinstance(enrichment_data["attributes"], dict):
                for k, v in list(enrichment_data["attributes"].items())[:5]:
                    update_props[f"ai_{k}"] = str(v)[:200]
            
            update_props["enriched_at"] = datetime.utcnow().isoformat()
            
            # Update in graph
            await gremlin.update_vertex(entity_id, update_props)
            
            return {
                "entity_id": entity_id,
                "properties_added": len(update_props),
                "success": True
            }
            
        except Exception as e:
            logger.error(f"Error enriching entity {entity.get('id', 'unknown')} with AI: {e}")
            return {
                "entity_id": entity.get("id", "unknown"),
                "properties_added": 0,
                "success": False,
                "error": str(e)
            }
    
    async def _infer_relationships(
        self,
        gremlin: CosmosGremlinConnector,
        entity: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Infer implicit relationships based on common properties or patterns.
        
        Args:
            gremlin: Gremlin connector
            entity: Entity to analyze
            
        Returns:
            Inferred relationships
        """
        try:
            entity_id = entity.get("id")
            
            # Example: Find entities with similar properties to create "similar_to" relationships
            # This is a simplified heuristic - can be enhanced
            
            # Get entity properties
            props = entity.get("properties", {})
            
            # Find entities with shared tags or categories
            relationships_created = 0
            
            if "ai_tags" in props:
                tags = props["ai_tags"][0].split(",") if isinstance(props["ai_tags"], list) else props["ai_tags"].split(",")
                
                for tag in tags[:3]:  # Limit to first 3 tags
                    # Find other entities with same tag
                    query = f"g.V().has('ai_tags', containing('{tag}')).hasId(neq('{entity_id}')).limit(5)"
                    similar = await gremlin.execute_query(query)
                    
                    for similar_entity in similar:
                        similar_id = similar_entity.get("id")
                        
                        # Create "similar_to" relationship
                        await gremlin.add_edge(
                            edge_label="similar_to",
                            from_vertex_id=entity_id,
                            to_vertex_id=similar_id,
                            properties={"reason": f"shared_tag:{tag}", "inferred": "true"}
                        )
                        relationships_created += 1
            
            return {
                "entity_id": entity_id,
                "relationships_created": relationships_created,
                "success": True
            }
            
        except Exception as e:
            logger.error(f"Error inferring relationships for {entity.get('id', 'unknown')}: {e}")
            return {
                "entity_id": entity.get("id", "unknown"),
                "relationships_created": 0,
                "success": False,
                "error": str(e)
            }
    
    async def _compute_metrics(
        self,
        gremlin: CosmosGremlinConnector,
        entity: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Compute graph metrics for an entity.
        
        Args:
            gremlin: Gremlin connector
            entity: Entity to analyze
            
        Returns:
            Computed metrics
        """
        try:
            entity_id = entity.get("id")
            
            # Compute various graph metrics
            
            # 1. Degree (number of connections)
            out_degree_query = f"g.V('{entity_id}').outE().count()"
            in_degree_query = f"g.V('{entity_id}').inE().count()"
            
            out_degree = await gremlin.execute_query(out_degree_query)
            in_degree = await gremlin.execute_query(in_degree_query)
            
            out_deg = int(out_degree[0]) if out_degree else 0
            in_deg = int(in_degree[0]) if in_degree else 0
            total_deg = out_deg + in_deg
            
            # Update entity with metrics
            metrics = {
                "graph_out_degree": str(out_deg),
                "graph_in_degree": str(in_deg),
                "graph_total_degree": str(total_deg),
                "metrics_computed_at": datetime.utcnow().isoformat()
            }
            
            await gremlin.update_vertex(entity_id, metrics)
            
            return {
                "entity_id": entity_id,
                "metrics_computed": len(metrics),
                "success": True
            }
            
        except Exception as e:
            logger.error(f"Error computing metrics for {entity.get('id', 'unknown')}: {e}")
            return {
                "entity_id": entity.get("id", "unknown"),
                "metrics_computed": 0,
                "success": False,
                "error": str(e)
            }
    
    async def process_content_item(
        self,
        content: Content,
        ctx: WorkflowContext
    ) -> Content:
        """
        Enrich knowledge graph entities.
        
        Args:
            content: Content item (used for context)
            ctx: Workflow context
            
        Returns:
            Content with enrichment statistics
        """
        try:
            logger.info(f"Enriching knowledge graph: type={self.enrichment_type}")
            
            # Get connectors
            gremlin = await self._get_gremlin_connector()
            
            # Select entities to enrich
            entities = await self._select_entities(gremlin)
            
            if not entities:
                logger.info("No entities found to enrich")
                content.summary_data[self.output_field] = {
                    "entities_enriched": 0,
                    "total_entities": 0
                }
                return content
            
            logger.info(f"Found {len(entities)} entities to enrich")
            
            # Perform enrichment based on type
            enrichment_results = []
            
            if self.enrichment_type == "ai_properties":
                ai = await self._get_ai_connector()
                for entity in entities:
                    result = await self._enrich_with_ai_properties(gremlin, ai, entity)
                    enrichment_results.append(result)
            
            elif self.enrichment_type == "infer_relationships":
                for entity in entities:
                    result = await self._infer_relationships(gremlin, entity)
                    enrichment_results.append(result)
            
            elif self.enrichment_type == "compute_metrics":
                for entity in entities:
                    result = await self._compute_metrics(gremlin, entity)
                    enrichment_results.append(result)
            
            else:
                raise ValueError(f"Unsupported enrichment_type: {self.enrichment_type}")
            
            # Compute statistics
            successful = sum(1 for r in enrichment_results if r.get("success", False))
            
            content.summary_data[self.output_field] = {
                "enrichment_type": self.enrichment_type,
                "entities_processed": len(entities),
                "entities_enriched": successful,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            logger.info(
                f"Knowledge graph enrichment completed: "
                f"{successful}/{len(entities)} entities enriched"
            )
            
            return content
            
        except Exception as e:
            logger.error(f"Error enriching knowledge graph: {e}")
            if self.fail_on_error:
                raise
            
            content.summary_data[self.output_field] = {
                "enrichment_type": self.enrichment_type,
                "entities_enriched": 0,
                "error": str(e)
            }
            return content
