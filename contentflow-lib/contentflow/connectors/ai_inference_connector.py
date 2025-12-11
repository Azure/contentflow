"""
Azure AI Inference connector for AI model inference operations.

This connector provides access to Azure AI Inference API for chat completions
and other AI model operations during workflow execution.
"""

import logging
from typing import List, Dict, Any, Optional

from azure.identity import DefaultAzureCredential
from azure.core.credentials import AzureKeyCredential
from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import (
    SystemMessage,
    UserMessage,
    AssistantMessage,
    ChatRequestMessage,
    ChatCompletions
)

from .base import ConnectorBase

logger = logging.getLogger(__name__)


class AIInferenceConnector(ConnectorBase):
    """
    Azure AI Inference connector.
    
    Provides access to Azure AI models for chat completions and inference.
    Supports both Azure Key Credential and Default Azure Credential authentication.
    
    Configuration:
        - endpoint: AI model endpoint URL (supports ${ENV_VAR})
        - credential_type: 'azure_key_credential' or 'default_azure_credential'
        - api_key: API key (required for azure_key_credential)
    
    Example:
        ```python
        connector = AIInferenceConnector(
            name="ai_model",
            settings={
                "endpoint": "${AI_ENDPOINT}",
                "credential_type": "default_azure_credential"
            }
        )
        
        await connector.initialize()
        
        # Chat completion
        response = await connector.complete(
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "What is Azure?"}
            ],
            max_tokens=500,
            temperature=0.7
        )
        ```
    """
    
    def __init__(self, name: str, settings: Dict[str, Any], **kwargs):
        super().__init__(name=name, connector_type="ai_inference", settings=settings, **kwargs)
        
        # Validate and resolve settings
        self.endpoint = self._resolve_setting("endpoint", required=True)
        self.credential_type = self._resolve_setting("credential_type", required=True)
        
        # Validate credential type
        if self.credential_type not in ['azure_key_credential', 'default_azure_credential']:
            raise ValueError(
                f"Unsupported credential type: {self.credential_type}. "
                f"Supported types are 'azure_key_credential' and 'default_azure_credential'."
            )
        
        # Get API key if using key-based auth
        self.api_key = None
        if self.credential_type == 'azure_key_credential':
            self.api_key = self._resolve_setting("api_key", required=True)
        
        # Initialize client reference
        self.chat_client: Optional[ChatCompletionsClient] = None
    
    async def initialize(self) -> None:
        """Initialize the AI inference client."""
        if self.chat_client:
            return
        
        logger.debug(
            f"Creating ChatCompletionsClient with endpoint: {self.endpoint} "
            f"and credential type: {self.credential_type}"
        )
        
        if self.credential_type == 'azure_key_credential':
            self.chat_client = ChatCompletionsClient(
                endpoint=self.endpoint,
                credential=AzureKeyCredential(self.api_key)
            )
        else:  # default_azure_credential
            credential = DefaultAzureCredential()
            self.chat_client = ChatCompletionsClient(
                endpoint=self.endpoint,
                credential=credential,
                credential_scopes=["https://cognitiveservices.azure.com/.default"]
            )
        
        logger.info(f"Initialized AIInferenceConnector '{self.name}'")
    
    async def test_connection(self) -> bool:
        """Test the AI inference connection."""
        try:
            if not self.chat_client:
                await self.initialize()
            
            # Simple test with minimal prompt
            response = self.chat_client.complete(
                messages=[SystemMessage("Reply with YES")]
            )
            
            logger.info(f"AIInferenceConnector '{self.name}' connection test successful")
            return True
            
        except Exception as e:
            logger.error(f"AIInferenceConnector '{self.name}' connection test failed: {e}")
            raise
    
    def _convert_messages(
        self,
        messages: List[Dict[str, str]]
    ) -> List[ChatRequestMessage]:
        """
        Convert message dicts to ChatRequestMessage objects.
        
        Args:
            messages: List of message dicts with 'role' and 'content' keys
            
        Returns:
            List of ChatRequestMessage objects
        """
        converted = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            
            if role == "system":
                converted.append(SystemMessage(content=content))
            elif role == "assistant":
                converted.append(AssistantMessage(content=content))
            else:  # user or default
                converted.append(UserMessage(content=content))
        
        return converted
    
    async def complete(
        self,
        messages: List[Dict[str, str]],
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        frequency_penalty: Optional[float] = None,
        presence_penalty: Optional[float] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate chat completion.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            max_tokens: Maximum completion tokens
            temperature: Sampling temperature (0-2)
            top_p: Nucleus sampling parameter
            frequency_penalty: Frequency penalty (-2 to 2)
            presence_penalty: Presence penalty (-2 to 2)
            **kwargs: Additional parameters
            
        Returns:
            Dict with completion result including 'content' and 'usage'
        """
        if not self.chat_client:
            await self.initialize()
        
        # Convert messages to SDK format
        chat_messages = self._convert_messages(messages)
        
        # Build request parameters
        params = {}
        if max_tokens is not None:
            params["max_tokens"] = max_tokens
        if temperature is not None:
            params["temperature"] = temperature
        if top_p is not None:
            params["top_p"] = top_p
        if frequency_penalty is not None:
            params["frequency_penalty"] = frequency_penalty
        if presence_penalty is not None:
            params["presence_penalty"] = presence_penalty
        
        params.update(kwargs)
        
        # Make API call
        response: ChatCompletions = self.chat_client.complete(
            messages=chat_messages,
            **params
        )
        
        # Extract result
        choice = response.choices[0]
        content = choice.message.content
        
        result = {
            "content": content,
            "role": choice.message.role,
            "finish_reason": choice.finish_reason,
            "usage": {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            }
        }
        
        logger.debug(
            f"Completed inference: {result['usage']['total_tokens']} tokens, "
            f"finish_reason: {result['finish_reason']}"
        )
        
        return result
    
    async def complete_stream(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ):
        """
        Generate streaming chat completion.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            **kwargs: Additional parameters
            
        Yields:
            Streaming completion chunks
        """
        if not self.chat_client:
            await self.initialize()
        
        chat_messages = self._convert_messages(messages)
        
        response = self.chat_client.complete(
            messages=chat_messages,
            stream=True,
            **kwargs
        )
        
        for chunk in response:
            if chunk.choices:
                yield {
                    "content": chunk.choices[0].delta.content or "",
                    "finish_reason": chunk.choices[0].finish_reason
                }
    
    async def cleanup(self) -> None:
        """Cleanup connector resources."""
        # ChatCompletionsClient doesn't require explicit cleanup
        self.chat_client = None
        logger.info(f"Cleaned up AIInferenceConnector '{self.name}'")
