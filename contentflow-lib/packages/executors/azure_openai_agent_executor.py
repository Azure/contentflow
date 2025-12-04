"""AI Agent executor using AzureOpenAIResponsesClient from agent-framework."""

import logging
from typing import Dict, Any, Optional

try:
    from agent_framework.azure import AzureOpenAIResponsesClient
    from agent_framework import ChatAgent, AgentRunResponse
except ImportError:
    raise ImportError(
        "agent-framework and azure-identity are required for AI Agent execution. "
        "Install them with: pip install agent-framework azure-identity"
    )

from ..utils.credential_provider import get_azure_credential
from . import ParallelExecutor
from ..models import Content

logger = logging.getLogger(__name__)


class AzureOpenAIAgentExecutor(ParallelExecutor):
    """
    Execute AI agent interactions using Azure OpenAI Responses Client.
    
    This executor wraps an agent created with AzureOpenAIResponsesClient from the
    agent-framework library to process content items with AI capabilities.
    
    Configuration (settings dict):
        - instructions (str): System instructions for the agent
          Default: "You are a helpful AI assistant."
        - endpoint (str): Azure OpenAI endpoint URL
          Default: None (uses environment variable AZURE_OPENAI_ENDPOINT)
        - deployment_name (str): Azure OpenAI model deployment name
          Default: None (uses agent-framework default)
        - credential_type (str): Azure credential type to use
          Default: "default_azure_credential"
          Options: "default_azure_credential", "azure_key_credential"
        - api_key (str): API key for credential if needed
          Default: None
        - input_field (str): Field containing the input text/query
          Default: "text"
        - output_field (str): Field name for agent response
          Default: "agent_response"
        - include_full_response (bool): Include full agent response object
          Default: False
        - temperature (float): Sampling temperature (0.0 to 2.0)
          Default: None (uses model default)
        - max_tokens (int): Maximum tokens in response
          Default: None (uses model default)
        - max_concurrent (int): Max concurrent agent executions
          Default: 3
        - continue_on_error (bool): Continue if a content item fails
          Default: True
    
    Example:
        ```python
        executor = AIAgentExecutor(
            id="ai_agent",
            settings={
                "instructions": "You are a document summarizer. Provide concise summaries.",
                "endpoint": "https://your-azure-openai-endpoint/",
                "deployment_name": "gpt-4.1-deployment",
                "credential_type": "default_azure_credential",
                "input_field": "text",
                "output_field": "summary"
            }
        )
        ```
    
    Input:
        Document or List[Document] each with (ContentIdentifier) id containing:
        - data[input_field]: Text query/input for the agent        
    Output:
        Document or List[Document] with added fields:
        - data[output_field]: Agent response text
        - data[output_field + '_full']: Full response object (if include_full_response=True)
        - summary_data['agent_execution_status']: Execution status
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
        self.instructions = self.get_setting("instructions", default="You are a helpful AI assistant.")
        self.endpoint = self.get_setting("endpoint", default=None)
        self.deployment_name = self.get_setting("deployment_name", default=None)
        self.credential_type = self.get_setting("credential_type", default="default_azure_credential")
        self.api_key = self.get_setting("api_key", default=None)
        self.input_field = self.get_setting("input_field", default="text")
        self.output_field = self.get_setting("output_field", default="agent_response")
        self.include_full_response = self.get_setting("include_full_response", default=False)
        self.temperature = self.get_setting("temperature", default=None)
        self.max_tokens = self.get_setting("max_tokens", default=None)
        
        # Initialize credential
        if self.credential_type == "default_azure_credential":
            credential = get_azure_credential()
        elif self.credential_type == "azure_key_credential":
            if not self.api_key:
                raise ValueError("api_key must be provided for azure_key_credential")
        
        # Initialize Azure OpenAI Responses Client
        client_kwargs = {}
        client_kwargs['deployment_name'] = self.deployment_name
        client_kwargs['endpoint'] = self.endpoint
        client_kwargs["credential"] = credential if self.credential_type == "default_azure_credential" else None
        client_kwargs["api_key"] = self.api_key if self.credential_type == "azure_key_credential" else None
        
        self.client = AzureOpenAIResponsesClient(**client_kwargs)
        
        # Create agent
        agent_kwargs = {
            'id': f"{self.id}_agent",
            'name': f"{self.id}_agent",
            'temperature': self.temperature,
            'max_tokens': self.max_tokens,
            'instructions': self.instructions
        }
        
        self.agent: ChatAgent = self.client.create_agent(**agent_kwargs)
        
        if self.debug_mode:
            logger.debug(
                f"AIAgentExecutor with id {self.id} initialized: "
                f"instructions='{self.instructions[:50]}...', deployment_name={self.deployment_name}"
            )
    
    async def process_content_item(
        self,
        content: Content
    ) -> Content:
        """Process a single content item using the AI agent.
           Implements the abstract method from ParallelExecutor.
        """
        
        try:
            if not content or not content.data:
                raise ValueError("Content must have data")
            
            # Get input for the agent
            query = None
            
            # Otherwise use simple text input
            if self.input_field in content.data:
                query = content.data[self.input_field]
                if not isinstance(query, str):
                    query = str(query)
            else:
                raise ValueError(
                    f"Content missing required input. "
                    f"Field '{self.input_field}' not found."
                )
            
            if self.debug_mode:
                if query:
                    logger.debug(f"Processing content {content.id} with query: {query[:100]}...")
            
            # Execute agent
            response_text, full_response = await self._run_agent(query)
            
            # Store response
            content.data[self.output_field] = response_text
            
            if self.include_full_response:
                content.data[f"{self.output_field}_agent_full_response"] = full_response.to_json()
            
            # Update summary
            content.summary_data['agent_execution_status'] = "success"
            content.summary_data['response_length'] = len(response_text) if response_text else 0
            
            if self.debug_mode:
                logger.debug(f"Agent response for {content.id}: {response_text[:100]}...")

        except Exception as e:
            logger.error(
                f"AIAgentExecutor {self.id} failed processing content {content.id}",
                exc_info=True
            )
            
            # Raise the exception to be handled upstream if needed
            raise
        
        return content
    
    async def _run_agent(
        self,
        query: Optional[str] = None,
    ) -> tuple[str, AgentRunResponse]:
        """Run agent in non-streaming mode.
        
        Args:
            query: Simple text query
            
        Returns:
            Tuple of (response_text, full_response)
        """
        result = await self.agent.run(query, store=False)
        
        response_text = result.text if hasattr(result, 'text') else str(result)
        
        return response_text, result
    