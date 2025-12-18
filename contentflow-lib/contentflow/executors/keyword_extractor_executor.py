"""Keyword extraction executor using Azure OpenAI Agent."""

import logging
import json
from typing import Dict, Any, Optional

from .azure_openai_agent_executor import AzureOpenAIAgentExecutor
from ..models import Content

logger = logging.getLogger(__name__)


class KeywordExtractorExecutor(AzureOpenAIAgentExecutor):
    """
    Specialized executor for extracting keywords and key phrases from text.
    
    This executor identifies important terms, phrases, and topics from text
    with optional ranking and categorization.
    
    Configuration (settings dict):
        - max_keywords (int): Maximum number of keywords to extract
          Default: 10
        - keyword_type (str): Type of keywords to extract
          Options: "single_words", "phrases", "both"
          Default: "both"
        - include_score (bool): Include relevance scores (0-1)
          Default: True
        - extract_topics (bool): Also extract main topics/themes
          Default: False
        - min_word_length (int): Minimum word length for single words
          Default: 3
        - context_aware (bool): Consider context for multi-word phrases
          Default: True
        - ranking_method (str): How to rank keywords
          Options: "relevance", "frequency", "importance"
          Default: "relevance"
        - input_field (str): Field containing text to analyze
          Default: "text"
        - output_field (str): Field name for extracted keywords
          Default: "keywords"
        
        All AzureOpenAIAgentExecutor settings are also supported.
    
    Example:
        ```python
        executor = KeywordExtractorExecutor(
            id="keyword_extractor",
            settings={
                "endpoint": "https://your-endpoint/",
                "deployment_name": "gpt-4",
                "max_keywords": 15,
                "keyword_type": "both",
                "include_score": True,
                "extract_topics": True,
                "input_field": "text",
                "output_field": "keywords"
            }
        )
        ```
    
    Input:
        Document with:
        - data[input_field]: Text to extract keywords from
        
    Output:
        Document with added fields:
        - data[output_field]: Extracted keywords (JSON format)
    """
    
    def __init__(
        self,
        id: str,
        settings: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        # Extract keyword-specific settings
        settings = settings or {}
        max_keywords = settings.get("max_keywords", 10)
        keyword_type = settings.get("keyword_type", "both")
        include_score = settings.get("include_score", True)
        extract_topics = settings.get("extract_topics", False)
        min_word_length = settings.get("min_word_length", 3)
        context_aware = settings.get("context_aware", True)
        ranking_method = settings.get("ranking_method", "relevance")
        
        # Build specialized instructions
        instructions = "You are an expert keyword extraction system. "
        instructions += f"Extract up to {max_keywords} "
        
        if keyword_type == "single_words":
            instructions += "single-word keywords "
            instructions += f"(minimum {min_word_length} characters) "
        elif keyword_type == "phrases":
            instructions += "key phrases (2-5 words) "
        else:  # both
            instructions += "keywords and key phrases "
            instructions += f"(single words must be at least {min_word_length} characters) "
        
        instructions += "that best represent the main concepts and topics in the text. "
        
        if context_aware and keyword_type in ["phrases", "both"]:
            instructions += "Consider the context to identify meaningful multi-word phrases. "
        
        # Ranking method
        ranking_descriptions = {
            "relevance": "based on their relevance to the main topics",
            "frequency": "based on their frequency of occurrence",
            "importance": "based on their semantic importance"
        }
        instructions += f"Rank keywords {ranking_descriptions.get(ranking_method, ranking_descriptions['relevance'])}. "
        
        if include_score:
            instructions += "Provide a relevance score (0.0 to 1.0) for each keyword. "
        
        if extract_topics:
            instructions += "Also identify 2-3 main topics or themes. "
        
        # Define output format
        instructions += "\n\nReturn results as a JSON object. "
        
        if extract_topics:
            if include_score:
                instructions += 'Format: {"keywords": [{"term": "keyword", "score": 0.0-1.0}], "topics": ["topic1", "topic2"]}. '
            else:
                instructions += 'Format: {"keywords": ["keyword1", "keyword2", ...], "topics": ["topic1", "topic2"]}. '
        else:
            if include_score:
                instructions += 'Format: {"keywords": [{"term": "keyword", "score": 0.0-1.0}]}. '
            else:
                instructions += 'Format: {"keywords": ["keyword1", "keyword2", ...]}. '
        
        instructions += "Focus on extracting keywords that would be useful for search, indexing, or understanding the content. "
        instructions += "Avoid generic stopwords and overly common terms."
        
        # Set default fields
        if "input_field" not in settings:
            settings["input_field"] = "text"
        if "output_field" not in settings:
            settings["output_field"] = "keywords"
        
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
                f"KeywordExtractorExecutor initialized with max_keywords={max_keywords}, "
                f"type={keyword_type}, ranking={ranking_method}"
            )
    
    async def process_content_item(self, content: Content) -> Content:
        """Process content and parse JSON keyword output."""
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
                        
                        # Add keyword count to summary
                        if "keywords" in parsed:
                            if isinstance(parsed["keywords"], list):
                                content.summary_data['keyword_count'] = len(parsed["keywords"])
                                
            except json.JSONDecodeError:
                if self.debug_mode:
                    logger.debug(f"Could not parse keywords as JSON for {content.id}")
        
        return content
