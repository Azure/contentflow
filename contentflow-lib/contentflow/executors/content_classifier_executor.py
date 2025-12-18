"""Content classification executor using Azure OpenAI Agent."""

import logging
import json
from typing import Dict, Any, Optional, List

from .azure_openai_agent_executor import AzureOpenAIAgentExecutor
from ..models import Content

logger = logging.getLogger(__name__)


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
        
        if not categories or not isinstance(categories, list) or len(categories) == 0:
            raise ValueError("ContentClassifierExecutor requires 'categories' setting with at least one category")
        
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
        
        # Store categories for validation
        self.categories = categories
        
        # Call parent constructor
        super().__init__(
            id=id,
            settings=settings,
            **kwargs
        )
        
        if self.debug_mode:
            logger.debug(
                f"ContentClassifierExecutor initialized with {len(categories)} categories, "
                f"multi_label={multi_label}"
            )
    
    async def process_content_item(self, content: Content) -> Content:
        """Process content and parse JSON classification output."""
        content = await super().process_content_item(content)
        
        # Try to parse JSON response
        if self.output_field in content.data:
            try:
                response_text = content.data[self.output_field]
                if isinstance(response_text, str):
                    # Look for JSON block in the response
                    start = response_text.find('{')
                    end = response_text.rfind('}')
                    if start != -1 and end != -1:
                        json_str = response_text[start:end+1]
                        parsed = json.loads(json_str)
                        content.data[self.output_field] = parsed
            except json.JSONDecodeError:
                if self.debug_mode:
                    logger.debug(f"Could not parse classification as JSON for {content.id}")
        
        return content
