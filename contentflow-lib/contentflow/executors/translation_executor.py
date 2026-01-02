"""Translation executor using Azure OpenAI Agent."""

import logging
from typing import Dict, Any, Optional, List

from .azure_openai_agent_executor import AzureOpenAIAgentExecutor

logger = logging.getLogger("contentflow.executors.translation_executor")


class TranslationExecutor(AzureOpenAIAgentExecutor):
    """
    Specialized executor for translating text between languages.
    
    This executor translates text from a source language to one or more
    target languages with configurable translation style.
    
    Configuration (settings dict):
        - target_language (str): Target language for translation
          Required: Must be provided (e.g., "Spanish", "French", "Japanese")
        - source_language (str): Source language (auto-detect if not specified)
          Default: None (auto-detect)
        - translation_style (str): Style of translation
          Options: "formal", "informal", "technical", "literal", "natural"
          Default: "natural"
        - preserve_formatting (bool): Preserve original text formatting
          Default: True
        - preserve_terminology (list[str]): Terms to not translate
          Default: None
        - glossary (dict): Custom translation glossary {source_term: target_term}
          Default: None
        - include_source (bool): Include original text in output
          Default: False
        - input_field (str): Field containing text to translate
          Default: "text"
        - output_field (str): Field name for translated text
          Default: "translated_text"
        
        All AzureOpenAIAgentExecutor settings are also supported.
    
    Example:
        ```python
        executor = TranslationExecutor(
            id="translator",
            settings={
                "endpoint": "https://your-endpoint/",
                "deployment_name": "gpt-4",
                "target_language": "Spanish",
                "source_language": "English",
                "translation_style": "formal",
                "preserve_formatting": True,
                "input_field": "text",
                "output_field": "translated_text"
            }
        )
        ```
    
    Input:
        Document with:
        - data[input_field]: Text to translate
        
    Output:
        Document with added fields:
        - data[output_field]: Translated text
        - data[output_field + '_source']: Original text (if include_source=True)
    """
    
    def __init__(
        self,
        id: str,
        settings: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        # Extract translation-specific settings
        settings = settings or {}
        target_language = settings.get("target_language", None)
        
        if not target_language:
            raise ValueError("TranslationExecutor requires 'target_language' setting")
        
        source_language = settings.get("source_language", None)
        translation_style = settings.get("translation_style", "natural")
        preserve_formatting = settings.get("preserve_formatting", True)
        preserve_terminology = settings.get("preserve_terminology", None)
        glossary = settings.get("glossary", None)
        include_source = settings.get("include_source", False)
        
        # Build specialized instructions
        instructions = "You are an expert translation system. "
        
        if source_language:
            instructions += f"Translate the following text from {source_language} to {target_language}. "
        else:
            instructions += f"Translate the following text to {target_language}. "
        
        # Translation style
        style_instructions = {
            "formal": "Use formal language and professional tone.",
            "informal": "Use casual, conversational language.",
            "technical": "Use precise technical terminology appropriate for the domain.",
            "literal": "Provide a literal, word-for-word translation where possible.",
            "natural": "Provide a natural, fluent translation that reads well in the target language."
        }
        instructions += style_instructions.get(translation_style, style_instructions["natural"])
        instructions += " "
        
        if preserve_formatting:
            instructions += "Preserve the original text formatting, including line breaks, paragraphs, and structure. "
        
        if preserve_terminology:
            instructions += f"Do NOT translate the following terms (keep them in the original language): {', '.join(preserve_terminology)}. "
        
        if glossary:
            instructions += "\n\nUse this translation glossary:\n"
            for source_term, target_term in glossary.items():
                instructions += f"- '{source_term}' → '{target_term}'\n"
        
        instructions += "\nProvide only the translated text without explanations or notes. "
        instructions += "Ensure accuracy and cultural appropriateness in the translation."
        
        # Set default fields
        if "input_field" not in settings:
            settings["input_field"] = "text"
        if "output_field" not in settings:
            settings["output_field"] = "translated_text"
        
        # Store include_source for post-processing
        self.include_source = include_source
        self.source_field = f"{settings['output_field']}_source"
        
        # Override instructions
        settings["instructions"] = instructions
        
        # Call parent constructor
        super().__init__(
            id=id,
            settings=settings,
            **kwargs
        )
        
        self.target_language = target_language
        
        if self.debug_mode:
            logger.debug(
                f"TranslationExecutor initialized with target={target_language}, "
                f"style={translation_style}"
            )
