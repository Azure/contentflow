"""Sentiment analysis executor using Azure OpenAI Agent."""

import logging
import json
from typing import Dict, Any, Optional

from .azure_openai_agent_executor import AzureOpenAIAgentExecutor
from ..models import Content

logger = logging.getLogger(__name__)


class SentimentAnalysisExecutor(AzureOpenAIAgentExecutor):
    """
    Specialized executor for sentiment analysis.
    
    This executor analyzes text to determine sentiment (positive, negative, neutral)
    with optional confidence scores and aspect-based sentiment analysis.
    
    Configuration (settings dict):
        - granularity (str): Level of sentiment analysis
          Options: "document" (overall), "sentence", "aspect"
          Default: "document"
        - include_confidence (bool): Include confidence scores (0-1)
          Default: True
        - include_emotions (bool): Identify specific emotions
          Default: False
        - aspects (list[str]): Specific aspects to analyze (for aspect-based)
          Default: None
        - scale (str): Sentiment scale
          Options: "3-point" (positive/neutral/negative),
                   "5-point" (very positive to very negative)
          Default: "3-point"
        - input_field (str): Field containing text to analyze
          Default: "text"
        - output_field (str): Field name for sentiment results
          Default: "sentiment"
        
        All AzureOpenAIAgentExecutor settings are also supported.
    
    Example:
        ```python
        executor = SentimentAnalysisExecutor(
            id="sentiment_analyzer",
            settings={
                "endpoint": "https://your-endpoint/",
                "deployment_name": "gpt-4",
                "granularity": "document",
                "include_confidence": True,
                "include_emotions": True,
                "input_field": "text",
                "output_field": "sentiment"
            }
        )
        ```
    
    Input:
        Document with:
        - data[input_field]: Text to analyze
        
    Output:
        Document with added fields:
        - data[output_field]: Sentiment analysis results (JSON format)
    """
    
    def __init__(
        self,
        id: str,
        settings: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        # Extract sentiment-specific settings
        settings = settings or {}
        granularity = settings.get("granularity", "document")
        include_confidence = settings.get("include_confidence", True)
        include_emotions = settings.get("include_emotions", False)
        aspects = settings.get("aspects", None)
        scale = settings.get("scale", "3-point")
        
        # Build specialized instructions
        instructions = "You are an expert sentiment analysis system. "
        
        if scale == "5-point":
            instructions += "Classify sentiment on a 5-point scale: very positive, positive, neutral, negative, very negative. "
        else:
            instructions += "Classify sentiment as: positive, neutral, or negative. "
        
        if granularity == "sentence":
            instructions += "Analyze sentiment for each sentence separately. "
        elif granularity == "aspect" and aspects:
            instructions += f"Analyze sentiment for these specific aspects: {', '.join(aspects)}. "
        else:
            instructions += "Analyze the overall sentiment of the entire text. "
        
        if include_confidence:
            instructions += "Provide a confidence score (0.0 to 1.0) for your sentiment classification. "
        
        if include_emotions:
            instructions += "Also identify specific emotions present (e.g., joy, anger, sadness, fear, surprise, disgust). "
        
        # Define output format
        instructions += "Return results as a JSON object. "
        
        if granularity == "document":
            if include_emotions:
                instructions += 'Format: {"sentiment": "positive/neutral/negative", "confidence": 0.0-1.0, "emotions": ["emotion1", "emotion2"], "explanation": "brief reason"}. '
            else:
                instructions += 'Format: {"sentiment": "positive/neutral/negative", "confidence": 0.0-1.0, "explanation": "brief reason"}. '
        elif granularity == "sentence":
            instructions += 'Format: {"sentences": [{"text": "sentence", "sentiment": "...", "confidence": 0.0-1.0}], "overall": {...}}. '
        elif granularity == "aspect":
            instructions += 'Format: {"aspects": {"aspect_name": {"sentiment": "...", "confidence": 0.0-1.0}}, "overall": {...}}. '
        
        instructions += "Be objective and consistent in your analysis."
        
        # Set default fields
        if "input_field" not in settings:
            settings["input_field"] = "text"
        if "output_field" not in settings:
            settings["output_field"] = "sentiment"
        
        # Override instructions
        settings["instructions"] = instructions
        
        # Call parent constructor
        super().__init__(
            id=id,
            settings=settings,
            **kwargs
        )
        
        if self.debug_mode:
            logger.debug(
                f"SentimentAnalysisExecutor initialized with granularity={granularity}, "
                f"scale={scale}"
            )
    
    async def process_content_item(self, content: Content) -> Content:
        """Process content and parse JSON sentiment output."""
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
                    logger.debug(f"Could not parse sentiment as JSON for {content.id}")
        
        return content
