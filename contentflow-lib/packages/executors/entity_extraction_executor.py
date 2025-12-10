"""Entity extraction executor using Azure OpenAI Agent."""

import logging
import json
from typing import Dict, Any, Optional

from .azure_openai_agent_executor import AzureOpenAIAgentExecutor
from ..models import Content

logger = logging.getLogger(__name__)


class EntityExtractionExecutor(AzureOpenAIAgentExecutor):
    """
    Specialized executor for extracting named entities from text.
    
    This executor identifies and extracts entities such as people, organizations,
    locations, dates, monetary values, and other named entities.
    
    Configuration (settings dict):
        - entity_types (list[str]): Types of entities to extract
          Options: "person", "organization", "location", "date", "time",
                   "money", "percentage", "product", "event", "email", 
                   "phone", "url", "custom"
          Default: ["person", "organization", "location", "date"]
        - output_format (str): Format for extracted entities
          Options: "structured" (JSON), "list", "text"
          Default: "structured"
        - include_context (bool): Include surrounding text context
          Default: False
        - custom_entities (list[str]): Custom entity types to look for
          Default: None
        - input_field (str): Field containing text to analyze
          Default: "text"
        - output_field (str): Field name for extracted entities
          Default: "entities"
        
        All AzureOpenAIAgentExecutor settings are also supported.
    
    Example:
        ```python
        executor = EntityExtractionExecutor(
            id="entity_extractor",
            settings={
                "endpoint": "https://your-endpoint/",
                "deployment_name": "gpt-4.1",
                "entity_types": ["person", "organization", "location"],
                "output_format": "structured",
                "input_field": "text",
                "output_field": "entities"
            }
        )
        ```
    
    Input:
        Document with:
        - data[input_field]: Text to analyze
        
    Output:
        Document with added fields:
        - data[output_field]: Extracted entities (format depends on output_format)
    """
    
    def __init__(
        self,
        id: str,
        settings: Optional[Dict[str, Any]] = None,
        enabled: bool = True,
        fail_on_error: bool = False,
        debug_mode: bool = False,
        **kwargs
    ):
        # Extract entity-specific settings
        settings = settings or {}
        entity_types = settings.get("entity_types", ["person", "organization", "location", "date"])
        output_format = settings.get("output_format", "structured")
        include_context = settings.get("include_context", False)
        custom_entities = settings.get("custom_entities", None)
        
        # Build specialized instructions
        instructions = "You are an expert named entity recognition system. "
        instructions += f"Extract the following types of entities from the text: {', '.join(entity_types)}. "
        
        if custom_entities:
            instructions += f"Also extract these custom entities: {', '.join(custom_entities)}. "
        
        if output_format == "structured":
            instructions += "Return the results as a JSON object with entity types as keys and lists of found entities as values. "
            if include_context:
                instructions += "For each entity, include a brief context snippet (5-10 words surrounding the entity). "
                instructions += "Format: {\"entity_type\": [{\"text\": \"entity_name\", \"context\": \"...surrounding text...\"}]}. "
            else:
                instructions += "Format: {\"entity_type\": [\"entity1\", \"entity2\", ...]}. "
        elif output_format == "list":
            instructions += "Return a simple list of all extracted entities, one per line. "
        else:  # text
            instructions += "Return the extracted entities in a natural text format, grouped by type. "
        
        instructions += "Be thorough and accurate. Only extract entities that are clearly present in the text."
        
        # Set default fields
        if "input_field" not in settings:
            settings["input_field"] = "text"
        if "output_field" not in settings:
            settings["output_field"] = "entities"
        
        # Override instructions
        settings["instructions"] = instructions
        
        # Store format for post-processing
        self.output_format = output_format
        
        # Call parent constructor
        super().__init__(
            id=id,
            settings=settings,
            enabled=enabled,
            fail_on_error=fail_on_error,
            debug_mode=debug_mode,
            **kwargs
        )
        
        if self.debug_mode:
            logger.debug(
                f"EntityExtractionExecutor initialized with entity_types={entity_types}, "
                f"output_format={output_format}"
            )
    
    async def process_content_item(self, content: Content) -> Content:
        """Process content and parse structured output if needed."""
        content = await super().process_content_item(content)
        
        # If output format is structured, try to parse JSON
        if self.output_format == "structured" and self.output_field in content.data:
            try:
                response_text = content.data[self.output_field]
                # Try to extract JSON from response
                if isinstance(response_text, str):
                    # Look for JSON block in the response
                    start = response_text.find('{')
                    end = response_text.rfind('}')
                    if start != -1 and end != -1:
                        json_str = response_text[start:end+1]
                        parsed = json.loads(json_str)
                        content.data[self.output_field] = parsed
            except json.JSONDecodeError:
                logger.warning(f"Could not parse entities as JSON for {content.id}")
        
        return content
