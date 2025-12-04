"""Custom AI prompt executor for AI-powered document enrichment."""

import logging
from typing import Dict, Any, Optional, List

from agent_framework import WorkflowContext

from .base import DocumentExecutor

try:
    import sys
    import os
    doc_proc_lib_path = os.path.join(os.path.dirname(__file__), "../../../doc-proc-lib")
    if os.path.exists(doc_proc_lib_path):
        sys.path.insert(0, doc_proc_lib_path)
    
    from doc.proc.models import Document
except ImportError as e:
    raise ImportError(f"Failed to import doc-proc-lib modules: {e}")

logger = logging.getLogger(__name__)


class CustomAIPromptExecutor(DocumentExecutor):
    """
    Apply custom AI prompts to document content for enrichment.
    
    This executor processes document chunks through an AI model using
    configurable system and user prompts to extract, transform, or
    enrich document data.
    
    Configuration (settings dict):
        - content_iterator_field (str): Field containing chunks to process
          Default: "chunks"
        - chunk_fields_to_apply_prompt_on (str): Comma-separated field names
          Default: "markdown,text"
        - output_field_name (str): Field name for AI output
          Default: "custom_ai_prompt_output"
        - system_prompt (str): System prompt for AI
          Required
        - user_prompt (str): User prompt template (can use {field} placeholders)
          Required
        - max_completion_tokens (int): Max tokens in response
          Default: 4000
        - temperature (float): Sampling temperature (0-2)
          Default: 1.0
        - top_p (float): Nucleus sampling parameter
          Default: 1.0
        - frequency_penalty (float): Frequency penalty (-2 to 2)
          Default: 0.0
        - presence_penalty (float): Presence penalty (-2 to 2)
          Default: 0.0
    
    Connectors:
        - ai_model: AIInferenceConnector instance (required)
    
    Example:
        ```python
        executor = CustomAIPromptExecutor(
            settings={
                "content_iterator_field": "chunks",
                "chunk_fields_to_apply_prompt_on": "text",
                "output_field_name": "summary",
                "system_prompt": "You are a document summarizer.",
                "user_prompt": "Summarize this text:\\n\\n{text}",
                "max_completion_tokens": 500,
                "temperature": 0.7
            },
            connectors=["ai_model"]
        )
        ```
    
    Input:
        Document with data containing:
        - chunks: List of chunk dicts with text fields
        
    Output:
        Document with each chunk enriched with:
        - chunk[output_field_name]: AI model response
    """
    
    def __init__(
        self,
        settings: Optional[Dict[str, Any]] = None,
        connectors: Optional[list] = None,
        **kwargs
    ):
        super().__init__(
            id="custom_ai_prompt",
            settings=settings,
            connectors=connectors or ["ai_model"],
            **kwargs
        )
        
        # Extract configuration
        self.content_iterator_field = self.get_setting(
            "content_iterator_field",
            default="chunks"
        )
        
        chunk_fields_str = self.get_setting(
            "chunk_fields_to_apply_prompt_on",
            default="markdown,text"
        )
        self.chunk_fields = [f.strip() for f in chunk_fields_str.split(",")]
        
        self.output_field_name = self.get_setting(
            "output_field_name",
            default="custom_ai_prompt_output"
        )
        
        # Required prompts
        self.system_prompt = self.get_setting("system_prompt", required=True)
        self.user_prompt = self.get_setting("user_prompt", required=True)
        
        # AI parameters
        self.max_completion_tokens = self.get_setting("max_completion_tokens", default=4000)
        self.temperature = self.get_setting("temperature", default=1.0)
        self.top_p = self.get_setting("top_p", default=1.0)
        self.frequency_penalty = self.get_setting("frequency_penalty", default=0.0)
        self.presence_penalty = self.get_setting("presence_penalty", default=0.0)
        
        if self.debug_mode:
            logger.debug(
                f"CustomAIPromptExecutor initialized: "
                f"iterator={self.content_iterator_field}, "
                f"output={self.output_field_name}"
            )
    
    async def process_document(
        self,
        document: Document,
        ctx: WorkflowContext
    ) -> Document:
        """Apply AI prompts to document chunks."""
        
        # Validate document structure
        if not document or not document.data:
            raise ValueError("Document must have data")
        
        doc_id = document.id
        data = document.data
        
        # Get AI connector
        ai_model = self.get_connector(ctx, "ai_model")
        if not ai_model:
            raise RuntimeError(
                "AIInferenceConnector 'ai_model' not found in context. "
                "Ensure it's initialized in workflow."
            )
        
        # Ensure connector is initialized
        if not hasattr(ai_model, 'chat_client') or not ai_model.chat_client:
            await ai_model.initialize()
        
        # Validate chunks exist
        if self.content_iterator_field not in data:
            raise ValueError(
                f"Document missing required field '{self.content_iterator_field}'"
            )
        
        chunks = data.get(self.content_iterator_field, [])
        if not chunks:
            logger.warning(f"No chunks found in document {doc_id}")
            return document
        
        if self.debug_mode:
            logger.debug(
                f"Processing {len(chunks)} chunks for document {doc_id}"
            )
        
        # Process each chunk
        for i, chunk in enumerate(chunks):
            if not isinstance(chunk, dict):
                logger.warning(f"Chunk {i} is not a dict, skipping")
                continue
            
            # Build user prompt from chunk fields
            user_content = self._build_user_prompt(chunk)
            
            if not user_content:
                logger.warning(f"Chunk {i} has no content in fields {self.chunk_fields}")
                continue
            
            # Call AI model
            try:
                result = await ai_model.complete(
                    messages=[
                        {"role": "system", "content": self.system_prompt},
                        {"role": "user", "content": user_content}
                    ],
                    max_tokens=self.max_completion_tokens,
                    temperature=self.temperature,
                    top_p=self.top_p,
                    frequency_penalty=self.frequency_penalty,
                    presence_penalty=self.presence_penalty
                )
                
                # Store result in chunk
                chunk[self.output_field_name] = result.get("content", "")
                
                if self.debug_mode:
                    logger.debug(
                        f"Chunk {i} processed: {result.get('usage', {}).get('total_tokens', 0)} tokens"
                    )
                
            except Exception as e:
                logger.error(f"Error processing chunk {i}: {e}")
                if self.fail_on_error:
                    raise
                # Store error info
                chunk[self.output_field_name] = f"[ERROR: {str(e)}]"
        
        if self.debug_mode:
            logger.debug(f"Completed AI processing for document {doc_id}")
        
        return document
    
    def _build_user_prompt(self, chunk: Dict[str, Any]) -> str:
        """Build user prompt from chunk data."""
        
        # First, try to use the user_prompt as a template
        prompt = self.user_prompt
        
        # Replace {field} placeholders with chunk values
        for field in self.chunk_fields:
            if field in chunk:
                placeholder = f"{{{field}}}"
                if placeholder in prompt:
                    prompt = prompt.replace(placeholder, str(chunk[field]))
        
        # If no placeholders were used, concatenate chunk fields
        if prompt == self.user_prompt and "{" not in self.user_prompt:
            content_parts = []
            for field in self.chunk_fields:
                if field in chunk and chunk[field]:
                    content_parts.append(str(chunk[field]))
            
            if content_parts:
                # Append content to prompt
                prompt = f"{self.user_prompt}\n\n{' '.join(content_parts)}"
        
        return prompt
