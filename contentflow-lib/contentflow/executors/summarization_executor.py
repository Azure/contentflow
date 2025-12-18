"""Summarization executor using Azure OpenAI Agent."""

import logging
from typing import Dict, Any, Optional

from .azure_openai_agent_executor import AzureOpenAIAgentExecutor

logger = logging.getLogger(__name__)


class SummarizationExecutor(AzureOpenAIAgentExecutor):
    """
    Specialized executor for text summarization.
    
    This executor inherits from AzureOpenAIAgentExecutor and provides
    optimized instructions for generating text summaries with configurable
    length and style.
    
    Configuration (settings dict):
        - summary_length (str): Desired summary length
          Options: "brief" (1-2 sentences), "short" (3-5 sentences), 
                   "medium" (1 paragraph), "detailed" (multiple paragraphs)
          Default: "short"
        - summary_style (str): Style of summary
          Options: "bullet_points", "paragraph", "abstract"
          Default: "paragraph"
        - focus_areas (str): Specific aspects to focus on
          Default: None (summarize all content)
        - preserve_key_facts (bool): Ensure key facts are preserved
          Default: True
        - input_field (str): Field containing text to summarize
          Default: "text"
        - output_field (str): Field name for summary
          Default: "summary"
        
        All AzureOpenAIAgentExecutor settings are also supported.
    
    Example:
        ```python
        executor = SummarizationExecutor(
            id="summarizer",
            settings={
                "endpoint": "https://your-endpoint/",
                "deployment_name": "gpt-4",
                "summary_length": "short",
                "summary_style": "paragraph",
                "input_field": "text",
                "output_field": "summary"
            }
        )
        ```
    
    Input:
        Document with:
        - data[input_field]: Text to summarize
        
    Output:
        Document with added fields:
        - data[output_field]: Generated summary
    """
    
    def __init__(
        self,
        id: str,
        settings: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        # Extract summarization-specific settings before calling parent
        settings = settings or {}
        summary_length = settings.get("summary_length", "short")
        summary_style = settings.get("summary_style", "paragraph")
        focus_areas = settings.get("focus_areas", None)
        preserve_key_facts = settings.get("preserve_key_facts", True)
        
        # Build specialized instructions
        length_instructions = {
            "brief": "Provide a very brief summary in 1-2 sentences.",
            "short": "Provide a concise summary in 3-5 sentences.",
            "medium": "Provide a summary in one paragraph (5-8 sentences).",
            "detailed": "Provide a detailed summary in multiple paragraphs."
        }
        
        style_instructions = {
            "bullet_points": "Format the summary as bullet points highlighting the main points.",
            "paragraph": "Write the summary as a cohesive paragraph.",
            "abstract": "Write the summary in an academic abstract style."
        }
        
        instructions = "You are an expert text summarizer. "
        instructions += length_instructions.get(summary_length, length_instructions["short"])
        instructions += " " + style_instructions.get(summary_style, style_instructions["paragraph"])
        
        if preserve_key_facts:
            instructions += " Ensure all key facts, figures, and important details are preserved."
        
        if focus_areas:
            instructions += f" Focus particularly on: {focus_areas}."
        
        instructions += " Maintain objectivity and accuracy in your summaries."
        
        # Set default fields if not provided
        if "input_field" not in settings:
            settings["input_field"] = "text"
        if "output_field" not in settings:
            settings["output_field"] = "summary"
        
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
                f"SummarizationExecutor initialized with length={summary_length}, "
                f"style={summary_style}"
            )
