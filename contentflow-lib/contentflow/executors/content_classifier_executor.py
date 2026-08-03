"""Content classification executor using Azure OpenAI Agent."""

import logging
import json
from typing import Dict, Any, Optional, List

from .azure_openai_agent_executor import AzureOpenAIAgentExecutor
from ..models import Content

logger = logging.getLogger("contentflow.executors.content_classifier_executor")


class ContentClassifierExecutor(AzureOpenAIAgentExecutor):
    """
    Specialized executor for content classification.
    
    This executor classifies text into predefined or custom categories
    with optional multi-label support and confidence scores.
    
    Configuration (settings dict):
        - categories (list[str]): Categories to classify into
          Required: Must be provided
        - multi_label (bool): Allow multiple categories per document
          Default: False
        - include_confidence (bool): Include confidence scores
          Default: True
        - category_descriptions (dict): Descriptions for each category
          Default: None
        - min_confidence (float): Minimum confidence threshold (0-1)
          Default: 0.0
        - include_explanation (bool): Include explanation for classification
          Default: True
        - input_field (str): Field containing text to classify
          Default: "text"
        - output_field (str): Field name for classification results
          Default: "classification"
        
        All AzureOpenAIAgentExecutor settings are also supported.
    
    Example:
        ```python
        executor = ContentClassifierExecutor(
            id="classifier",
            settings={
                "endpoint": "https://your-endpoint/",
                "deployment_name": "gpt-4",
                "categories": ["Technology", "Business", "Sports", "Entertainment"],
                "multi_label": False,
                "include_confidence": True,
                "input_field": "text",
                "output_field": "classification"
            }
        )
        ```
    
    Input:
        Document with:
        - data[input_field]: Text to classify
        
    Output:
        Document with added fields:
        - data[output_field]: Classification results (JSON format)
    """
    
    def __init__(
        self,
        id: str,
        settings: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        # Extract classifier-specific settings
        settings = settings or {}
        categories = settings.get("categories", None)
        
        # Handle categories passed as JSON string from UI
        if isinstance(categories, str):
            import json as _json
            try:
                parsed = _json.loads(categories)
                if isinstance(parsed, dict):
                    # Dict format: {"category": "description", ...}
                    # Use keys as categories, store descriptions separately
                    settings["category_descriptions"] = parsed
                    categories = list(parsed.keys())
                elif isinstance(parsed, list):
                    categories = parsed
                else:
                    categories = [str(parsed)]
            except (_json.JSONDecodeError, ValueError):
                # Fallback: comma-separated list
                categories = [c.strip() for c in categories.strip("[]").split(",") if c.strip()]
                categories = [c.strip("'\"") for c in categories]
            settings["categories"] = categories
        
        if not categories or not isinstance(categories, list) or len(categories) == 0:
            raise ValueError(f"{id}: ContentClassifierExecutor requires 'categories' setting with at least one category")
        
        multi_label = settings.get("multi_label", False)
        include_confidence = settings.get("include_confidence", True)
        category_descriptions = settings.get("category_descriptions", {})
        min_confidence = settings.get("min_confidence", 0.0)
        include_explanation = settings.get("include_explanation", True)
        
        # Build specialized instructions
        instructions = "You are an expert text classification system. "
        
        if multi_label:
            instructions += f"Classify the text into one or more of these categories: {', '.join(categories)}. "
        else:
            instructions += f"Classify the text into exactly one of these categories: {', '.join(categories)}. "
        
        # Add category descriptions if provided
        if category_descriptions:
            instructions += "\n\nCategory descriptions:\n"
            for cat, desc in category_descriptions.items():
                instructions += f"- {cat}: {desc}\n"
        
        if include_confidence:
            instructions += f"Provide a confidence score (0.0 to 1.0) for each classification. "
            if min_confidence > 0:
                instructions += f"Only include categories with confidence >= {min_confidence}. "
        
        if include_explanation:
            instructions += "Provide a brief explanation for your classification decision. "
        
        # Define output format
        instructions += "\n\nReturn results as a JSON object. "
        
        if multi_label:
            if include_confidence and include_explanation:
                instructions += 'Format: {"categories": [{"name": "category", "confidence": 0.0-1.0}], "explanation": "reason"}. '
            elif include_confidence:
                instructions += 'Format: {"categories": [{"name": "category", "confidence": 0.0-1.0}]}. '
            else:
                instructions += 'Format: {"categories": ["category1", "category2"]}. '
        else:
            if include_confidence and include_explanation:
                instructions += 'Format: {"category": "category_name", "confidence": 0.0-1.0, "explanation": "reason"}. '
            elif include_confidence:
                instructions += 'Format: {"category": "category_name", "confidence": 0.0-1.0}. '
            else:
                instructions += 'Format: {"category": "category_name"}. '
        
        instructions += "Be accurate and consistent in your classifications."
        
        # Set default fields
        if "input_field" not in settings:
            settings["input_field"] = "text"
        if "output_field" not in settings:
            settings["output_field"] = "classification"
        
        # Override instructions
        settings["instructions"] = instructions
        settings["parse_response_as_json"] = True # Ensure JSON parsing
        
        # Store categories for validation
        self.categories = categories
        
        # Call parent constructor
        super().__init__(
            id=id,
            settings=settings,
            **kwargs
        )
        
        # Max characters to send to classifier (prevents context window overflow)
        self.max_input_chars = int(settings.get("max_input_chars", 4000))
        
        if self.debug_mode:
            logger.debug(
                f"ContentClassifierExecutor {self.id} initialized with {len(categories)} categories, "
                f"multi_label={multi_label}"
            )
    
    async def process_content_item(self, content: Content) -> Content:
        """Process content and parse JSON classification output.
        Truncates input to max_input_chars to prevent context window overflow."""
        # Truncate the input field to prevent context_length_exceeded errors
        input_field = self.get_setting("input_field", default="text")
        if input_field and input_field in content.data:
            value = content.data[input_field]
            if isinstance(value, str) and len(value) > self.max_input_chars:
                content.data[input_field] = value[:self.max_input_chars]
            elif isinstance(value, dict):
                # Convert dict to string representation and truncate
                value_str = json.dumps(value, ensure_ascii=False, default=str)
                if len(value_str) > self.max_input_chars:
                    content.data[input_field] = value_str[:self.max_input_chars]
            elif isinstance(value, list):
                # Convert list to string and truncate
                value_str = json.dumps(value, ensure_ascii=False, default=str)
                if len(value_str) > self.max_input_chars:
                    content.data[input_field] = value_str[:self.max_input_chars]
        content = await super().process_content_item(content)
        return content

