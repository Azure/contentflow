"""
Knowledge Graph Entity Extraction Executor.

This executor uses AI to extract entities and relationships from content
to build a comprehensive knowledge graph of business models and concepts.
"""

import json
import logging
from typing import Any, Dict, List, Optional, Union

from agent_framework import WorkflowContext

from .parallel_executor import ParallelExecutor
from ..connectors.ai_inference_connector import AIInferenceConnector
from ..models import Content

logger = logging.getLogger("contentflow.executors.knowledge_graph_entity_extractor")


class KnowledgeGraphEntityExtractorExecutor(ParallelExecutor):
    """
    Extract entities and relationships from content for knowledge graph construction.
    
    This executor analyzes content using AI to identify:
    - Business entities (organizations, products, services, people, locations)
    - Concepts and topics
    - Relationships between entities
    - Entity attributes and properties
    
    The extracted information is structured for knowledge graph storage.
    
    Configuration:
        ai_endpoint: Azure AI endpoint URL
        ai_credential_type: Credential type ('azure_key_credential' or 'default_azure_credential')
        ai_api_key: API key (if using azure_key_credential)
        model_name: Model deployment name
        entity_types: List of entity types to extract (default: comprehensive list)
        relationship_types: List of relationship types to extract
        max_entities_per_content: Maximum entities to extract per content item
        include_attributes: Whether to extract entity attributes
        confidence_threshold: Minimum confidence score (0.0-1.0)
        output_field: Field to store extracted entities (default: 'knowledge_graph_entities')
    """
    
    def __init__(
        self,
        id: str,
        settings: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        """Initialize the knowledge graph entity extractor."""
        super().__init__(id=id, settings=settings, **kwargs)
        
        # AI settings
        self.ai_endpoint = self.get_setting("ai_endpoint", required=True)
        self.ai_credential_type = self.get_setting(
            "ai_credential_type",
            default="default_azure_credential"
        )
        self.ai_api_key = self.get_setting("ai_api_key", required=False)
        self.model_name = self.get_setting("model_name", required=True)
        
        # Entity extraction settings
        self.entity_types = self.get_setting(
            "entity_types",
            default=[
                "Organization", "Person", "Product", "Service",
                "Technology", "Location", "Event", "Concept",
                "Document", "Project", "Department", "Role"
            ]
        )
        
        self.relationship_types = self.get_setting(
            "relationship_types",
            default=[
                "works_at", "manages", "located_in", "part_of",
                "provides", "uses", "related_to", "depends_on",
                "collaborates_with", "authored_by", "mentions"
            ]
        )
        
        self.max_entities_per_content = self.get_setting("max_entities_per_content", default=50)
        self.include_attributes = self.get_setting("include_attributes", default=True)
        self.confidence_threshold = self.get_setting("confidence_threshold", default=0.6)
        self.output_field = self.get_setting("output_field", default="knowledge_graph_entities")
        
        # Temperature for extraction (lower for more deterministic results)
        self.temperature = self.get_setting("temperature", default=0.1)
        
        # Initialize connector
        self._connector: Optional[AIInferenceConnector] = None
        
        logger.debug(
            f"KnowledgeGraphEntityExtractorExecutor initialized: "
            f"model={self.model_name}, entity_types={len(self.entity_types)}, "
            f"relationship_types={len(self.relationship_types)}"
        )
    
    async def _get_connector(self) -> AIInferenceConnector:
        """Get or initialize the AI connector."""
        if self._connector is None:
            connector_settings = {
                "endpoint": self.ai_endpoint,
                "credential_type": self.ai_credential_type,
            }
            
            if self.ai_api_key:
                connector_settings["api_key"] = self.ai_api_key
            
            self._connector = AIInferenceConnector(
                name=f"ai_connector_{self.id}",
                settings=connector_settings
            )
            await self._connector.initialize()
        
        return self._connector
    
    def _build_extraction_prompt(self, content: Content) -> str:
        """
        Build the prompt for entity and relationship extraction.
        
        Args:
            content: Content item to analyze
            
        Returns:
            Formatted prompt
        """
        text = content.text_content or ""
        title = content.title or "Untitled"
        
        prompt = f"""You are an expert knowledge graph builder. Analyze the following content and extract business entities and their relationships.

**Document Title:** {title}

**Content:**
{text[:4000]}  # Limit content length

**Task:** Extract entities and relationships to build a comprehensive business knowledge graph.

**Entity Types to Extract:** {', '.join(self.entity_types)}

**Relationship Types to Consider:** {', '.join(self.relationship_types)}

**Instructions:**
1. Identify all significant entities in the content
2. Extract entity attributes (properties, descriptions)
3. Identify relationships between entities
4. Assign confidence scores (0.0-1.0) to each entity and relationship
5. Only include entities with confidence >= {self.confidence_threshold}

**Output Format (JSON):**
{{
    "entities": [
        {{
            "id": "unique-entity-id",
            "label": "entity-type",
            "name": "entity-name",
            "properties": {{
                "description": "brief description",
                "attribute1": "value1"
            }},
            "confidence": 0.95
        }}
    ],
    "relationships": [
        {{
            "from_entity_id": "entity-1-id",
            "to_entity_id": "entity-2-id",
            "relationship_type": "relationship-label",
            "properties": {{
                "context": "relationship context"
            }},
            "confidence": 0.90
        }}
    ]
}}

Return only valid JSON. Ensure all IDs are unique and use lowercase with hyphens.
"""
        return prompt
    
    async def process_content_item(
        self,
        content: Content,
        ctx: WorkflowContext
    ) -> Content:
        """
        Extract entities and relationships from a single content item.
        
        Args:
            content: Content to process
            ctx: Workflow context
            
        Returns:
            Content with extracted entities in knowledge_graph_entities field
        """
        try:
            logger.info(f"Extracting knowledge graph entities from content: {content.content_id}")
            
            # Get AI connector
            connector = await self._get_connector()
            
            # Build extraction prompt
            prompt = self._build_extraction_prompt(content)
            
            # Call AI model
            messages = [
                {
                    "role": "system",
                    "content": "You are an expert at extracting structured business entities and relationships for knowledge graphs. Always respond with valid JSON only."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
            
            response = await connector.chat_completion(
                messages=messages,
                model=self.model_name,
                temperature=self.temperature,
                max_tokens=2000
            )
            
            # Parse response
            response_text = response.choices[0].message.content.strip()
            
            # Remove markdown code blocks if present
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            
            response_text = response_text.strip()
            
            # Parse JSON
            extracted_data = json.loads(response_text)
            
            # Validate and filter by confidence
            entities = [
                e for e in extracted_data.get("entities", [])
                if e.get("confidence", 0) >= self.confidence_threshold
            ]
            
            relationships = [
                r for r in extracted_data.get("relationships", [])
                if r.get("confidence", 0) >= self.confidence_threshold
            ]
            
            # Limit number of entities
            if len(entities) > self.max_entities_per_content:
                # Sort by confidence and take top N
                entities = sorted(entities, key=lambda x: x.get("confidence", 0), reverse=True)
                entities = entities[:self.max_entities_per_content]
            
            # Add source document reference to all entities
            for entity in entities:
                if "properties" not in entity:
                    entity["properties"] = {}
                entity["properties"]["source_document_id"] = content.content_id
                entity["properties"]["source_document_title"] = content.title or "Untitled"
            
            # Store in content
            content.summary_data[self.output_field] = {
                "entities": entities,
                "relationships": relationships,
                "extraction_metadata": {
                    "total_entities": len(entities),
                    "total_relationships": len(relationships),
                    "entity_types": list(set(e.get("label") for e in entities)),
                    "model_used": self.model_name
                }
            }
            
            logger.info(
                f"Extracted {len(entities)} entities and {len(relationships)} relationships "
                f"from content {content.content_id}"
            )
            
            return content
            
        except json.JSONDecodeError as e:
            logger.error(
                f"Failed to parse AI response as JSON for content {content.content_id}: {e}\n"
                f"Response: {response_text[:500]}"
            )
            content.summary_data[self.output_field] = {
                "entities": [],
                "relationships": [],
                "error": "Failed to parse extraction results"
            }
            return content
            
        except Exception as e:
            logger.error(f"Error extracting entities from content {content.content_id}: {e}")
            if self.fail_on_error:
                raise
            
            content.summary_data[self.output_field] = {
                "entities": [],
                "relationships": [],
                "error": str(e)
            }
            return content
