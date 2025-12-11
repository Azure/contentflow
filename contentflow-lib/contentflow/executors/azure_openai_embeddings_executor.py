"""Azure OpenAI Embeddings executor for generating vector embeddings."""

import logging
from typing import Dict, Any, Optional, List

try:
    from openai import AsyncAzureOpenAI
except ImportError:
    raise ImportError(
        "openai is required for Azure OpenAI Embeddings execution. "
        "Install it with: pip install openai"
    )

from ..utils.credential_provider import get_azure_credential
from . import ParallelExecutor
from ..models import Content

logger = logging.getLogger(__name__)


class AzureOpenAIEmbeddingsExecutor(ParallelExecutor):
    """
    Generate embeddings using Azure OpenAI embeddings models.
    
    This executor uses Azure OpenAI's embeddings API to convert text into
    vector embeddings, useful for semantic search, similarity matching,
    and other vector-based operations.
    
    Configuration (settings dict):
        - endpoint (str): Azure OpenAI endpoint URL
          Default: None (uses environment variable AZURE_OPENAI_ENDPOINT)
        - deployment_name (str): Azure OpenAI embeddings model deployment name
          Default: None (required - e.g., "text-embedding-ada-002")
        - api_version (str): Azure OpenAI API version
          Default: "2024-02-01"
        - credential_type (str): Azure credential type to use
          Default: "default_azure_credential"
          Options: "default_azure_credential", "azure_key_credential"
        - api_key (str): API key for credential if needed
          Default: None
        - input_field (str): Field containing the text to embed
          Default: "text"
        - output_field (str): Field name for embedding vector
          Default: "embedding"
        - dimensions (int): Number of dimensions for the embedding
          Default: None (uses model default)
          Note: Only supported by newer models like text-embedding-3-small/large
        - max_concurrent (int): Max concurrent embedding operations
          Default: 5
        - continue_on_error (bool): Continue if a content item fails
          Default: True
    
    Example:
        ```python
        executor = AzureOpenAIEmbeddingsExecutor(
            id="text_embedder",
            settings={
                "endpoint": "https://your-azure-openai-endpoint/",
                "deployment_name": "text-embedding-ada-002",
                "credential_type": "default_azure_credential",
                "input_field": "text",
                "output_field": "text_embedding",
                "dimensions": 1536
            }
        )
        ```
    
    Input:
        Document or List[Document] each with (ContentIdentifier) id containing:
        - data[input_field]: Text to generate embeddings for
        
    Output:
        Document or List[Document] with added fields:
        - data[output_field]: List of float values representing the embedding vector
        - summary_data['embedding_dimensions']: Number of dimensions in the embedding
        - summary_data['embedding_model']: Model used for embedding
        - summary_data['embedding_status']: Execution status
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
        super().__init__(
            id=id,
            settings=settings,
            enabled=enabled,
            fail_on_error=fail_on_error,
            debug_mode=debug_mode,
            **kwargs
        )
        
        # Extract configuration
        self.endpoint = self.get_setting("endpoint", default=None)
        self.deployment_name = self.get_setting("deployment_name", default=None)
        self.api_version = self.get_setting("api_version", default="2024-02-01")
        self.credential_type = self.get_setting("credential_type", default="default_azure_credential")
        self.api_key = self.get_setting("api_key", default=None)
        self.input_field = self.get_setting("input_field", default="text")
        self.output_field = self.get_setting("output_field", default="embedding")
        self.dimensions = self.get_setting("dimensions", default=None)
        
        if not self.deployment_name:
            raise ValueError("deployment_name is required for Azure OpenAI Embeddings")
        
        # Initialize Azure OpenAI client
        client_kwargs = {
            "azure_endpoint": self.endpoint,
            "api_version": self.api_version
        }
        
        if self.credential_type == "default_azure_credential":
            credential = get_azure_credential()
            # For Azure credential, we need to get a token
            token_provider = credential.get_token("https://cognitiveservices.azure.com/.default")
            client_kwargs["azure_ad_token"] = token_provider.token
        elif self.credential_type == "azure_key_credential":
            if not self.api_key:
                raise ValueError("api_key must be provided for azure_key_credential")
            client_kwargs["api_key"] = self.api_key
        else:
            raise ValueError(f"Unsupported credential_type: {self.credential_type}")
        
        self.client = AsyncAzureOpenAI(**client_kwargs)
        
        if self.debug_mode:
            logger.debug(
                f"AzureOpenAIEmbeddingsExecutor with id {self.id} initialized: "
                f"deployment_name={self.deployment_name}, dimensions={self.dimensions}"
            )
    
    async def process_content_item(
        self,
        content: Content
    ) -> Content:
        """Process a single content item to generate embeddings.
           Implements the abstract method from ParallelExecutor.
        """
        
        try:
            if not content or not content.data:
                raise ValueError("Content must have data")
            
            # Get input text
            text = self.try_extract_nested_field_from_content(
                content,
                self.input_field
            )
            if text is None:
                raise ValueError(
                    f"Content missing, required input field '{self.input_field}'"
                )
            
            if not isinstance(text, str):
                text = str(text)
            
            if not text or not text.strip():
                raise ValueError("Input text is empty")
            
            if self.debug_mode:
                logger.debug(f"Generating embedding for content {content.id}: {text[:100]}...")
            
            # Generate embedding
            embedding = await self._generate_embedding(text)
            
            # Store embedding
            content.data[self.output_field] = embedding
            
            # Update summary
            content.summary_data['embedding_dimensions'] = len(embedding)
            content.summary_data['embedding_model'] = self.deployment_name
            content.summary_data['embedding_status'] = "success"
            
            if self.debug_mode:
                logger.debug(
                    f"Generated embedding for {content.id}: "
                    f"{len(embedding)} dimensions"
                )

        except Exception as e:
            logger.error(
                f"AzureOpenAIEmbeddingsExecutor {self.id} failed processing content {content.id}",
                exc_info=True
            )
            
            # Update summary with error status
            content.summary_data['embedding_status'] = "failed"
            content.summary_data['embedding_error'] = str(e)
            
            # Raise the exception to be handled upstream if needed
            raise
        
        return content
    
    async def _generate_embedding(
        self,
        text: str
    ) -> List[float]:
        """Generate embedding for a single text.
        
        Args:
            text: Text to embed
            
        Returns:
            List of float values representing the embedding vector
        """
        try:
            # Prepare API call parameters
            embedding_kwargs = {
                "model": self.deployment_name,
                "input": text
            }
            
            # Add dimensions if specified (only supported by newer models)
            if self.dimensions is not None:
                embedding_kwargs["dimensions"] = self.dimensions
            
            # Call Azure OpenAI embeddings API
            response = await self.client.embeddings.create(**embedding_kwargs)
            
            # Extract embedding from response
            embedding = response.data[0].embedding
            
            return embedding
            
        except Exception as e:
            logger.error(f"Failed to generate embedding: {str(e)}", exc_info=True)
            raise
    
    