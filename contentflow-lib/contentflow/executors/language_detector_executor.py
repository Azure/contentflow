"""Language detection executor using Azure OpenAI Agent."""

import logging
import json
from typing import Dict, Any, Optional

from .azure_openai_agent_executor import AzureOpenAIAgentExecutor
from ..models import Content

logger = logging.getLogger("contentflow.executors.language_detector")


class LanguageDetectorExecutor(AzureOpenAIAgentExecutor):
    """
    Specialized executor for detecting the language of text.
    
    This executor identifies the language(s) present in text with confidence
    scores and optional script/dialect detection.
    
    Configuration (settings dict):
        - detect_multiple (bool): Detect multiple languages if present
          Default: False
        - include_confidence (bool): Include confidence scores (0-1)
          Default: True
        - detect_script (bool): Also identify writing script (Latin, Cyrillic, etc.)
          Default: False
        - detect_dialect (bool): Detect language dialects/variants
          Default: False
        - min_confidence (float): Minimum confidence threshold (0-1)
          Default: 0.5
        - iso_format (str): Language code format
          Options: "iso-639-1" (2-letter), "iso-639-3" (3-letter), "name"
          Default: "name"
        - input_field (str): Field containing text to analyze
          Default: "text"
        - output_field (str): Field name for language detection results
          Default: "language"
        
        All AzureOpenAIAgentExecutor settings are also supported.
    
    Example:
        ```python
        executor = LanguageDetectorExecutor(
            id="lang_detector",
            settings={
                "endpoint": "https://your-endpoint/",
                "deployment_name": "gpt-4",
                "detect_multiple": True,
                "include_confidence": True,
                "detect_script": True,
                "input_field": "text",
                "output_field": "language"
            }
        )
        ```
    
    Input:
        Document with:
        - data[input_field]: Text to analyze
        
    Output:
        Document with added fields:
        - data[output_field]: Language detection results (JSON format)
    """
    
    def __init__(
        self,
        id: str,
        settings: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        # Extract language detection settings
        settings = settings or {}
        detect_multiple = settings.get("detect_multiple", False)
        include_confidence = settings.get("include_confidence", True)
        detect_script = settings.get("detect_script", False)
        detect_dialect = settings.get("detect_dialect", False)
        min_confidence = settings.get("min_confidence", 0.5)
        iso_format = settings.get("iso_format", "name")
        
        # Build specialized instructions
        instructions = "You are an expert language detection system. "
        
        if detect_multiple:
            instructions += "Identify all languages present in the text. "
        else:
            instructions += "Identify the primary language of the text. "
        
        # Language code format
        if iso_format == "iso-639-1":
            instructions += "Use ISO 639-1 two-letter language codes (e.g., 'en', 'es', 'fr'). "
        elif iso_format == "iso-639-3":
            instructions += "Use ISO 639-3 three-letter language codes (e.g., 'eng', 'spa', 'fra'). "
        else:  # name
            instructions += "Use full language names (e.g., 'English', 'Spanish', 'French'). "
        
        if include_confidence:
            instructions += f"Provide a confidence score (0.0 to 1.0) for each detected language. "
            instructions += f"Only report languages with confidence >= {min_confidence}. "
        
        if detect_script:
            instructions += "Also identify the writing script (e.g., Latin, Cyrillic, Arabic, Chinese, etc.). "
        
        if detect_dialect:
            instructions += "If applicable, identify specific dialects or variants (e.g., 'American English', 'British English'). "
        
        # Define output format
        instructions += "\n\nReturn results as a JSON object. "
        
        if detect_multiple:
            base_format = '{"languages": [{"language": "...", "confidence": 0.0-1.0'
            if detect_script:
                base_format += ', "script": "..."'
            if detect_dialect:
                base_format += ', "dialect": "..."'
            base_format += '}]'
            
            if detect_script or detect_dialect:
                base_format += ', "primary_language": "..."'
            
            base_format += '}'
            instructions += f"Format: {base_format}. "
        else:
            base_format = '{"language": "...", "confidence": 0.0-1.0'
            if detect_script:
                base_format += ', "script": "..."'
            if detect_dialect:
                base_format += ', "dialect": "..."'
            base_format += '}'
            instructions += f"Format: {base_format}. "
        
        instructions += "Be accurate and only report languages you are confident about."
        
        # Set default fields
        if "input_field" not in settings:
            settings["input_field"] = "text"
        if "output_field" not in settings:
            settings["output_field"] = "language"
        
        # Override instructions
        settings["instructions"] = instructions
        settings["response_as_json"] = True # Ensure JSON response
        
        # Call parent constructor
        super().__init__(
            id=id,
            settings=settings,
            **kwargs
        )
        
        if self.debug_mode:
            logger.debug(
                f"LanguageDetectorExecutor initialized with detect_multiple={detect_multiple}, "
                f"iso_format={iso_format}"
            )
    
    async def process_content_item(self, content: Content) -> Content:
        """Process content and parse JSON language output."""
        content = await super().process_content_item(content)
        
        return content
