"""Cross-document comparison executor using Azure OpenAI for AI-powered analysis."""

import asyncio
import json
import logging
from datetime import datetime
from typing import Any, Dict, Optional, List, Union

try:
    from agent_framework.azure import AzureOpenAIResponsesClient
    from agent_framework import ChatAgent, AgentRunResponse
except ImportError:
    raise ImportError(
        "agent-framework and azure-identity are required for AI Agent execution. "
        "Install them with: pip install agent-framework azure-identity"
    )

from agent_framework import WorkflowContext

from .cross_document_executor import CrossDocumentExecutor
from ..models import Content
from ..utils.credential_provider import get_azure_credential

logger = logging.getLogger("contentflow.executors.cross_document_comparison")


class CrossDocumentComparisonExecutor(CrossDocumentExecutor):
    """
    Compare data across documents in a set using Azure OpenAI.
    
    Sends the consolidated document set data to an LLM with instructions
    to perform comparative analysis, trend detection, and variance identification.
    
    Configuration (settings dict):
        - endpoint (str): Azure OpenAI endpoint URL.
          Default: None (uses environment variable AZURE_OPENAI_ENDPOINT)
        - deployment_name (str): Azure OpenAI model deployment name.
          Required: True
        - credential_type (str): Azure credential type.
          Default: "default_azure_credential"
          Options: "default_azure_credential", "azure_key_credential"
        - api_key (str): API key (if using azure_key_credential).
          Default: None
        - comparison_instructions (str): Custom prompt/instructions for comparison.
          Default: Built-in comparative analysis prompt
        - comparison_fields (list[str]): Specific field paths to include in
          the comparison. If None, sends all document data.
          Default: None
        - output_format (str): Desired output format from the LLM.
          Options: "json", "markdown", "structured"
          Default: "structured"
        - include_trend_analysis (bool): Request period-over-period trends.
          Default: True
        - include_variance_detection (bool): Flag significant variances.
          Default: True
        - variance_threshold_pct (float): Percentage change to flag as significant.
          Default: 10.0
        - temperature (float): Sampling temperature (0.0 to 2.0).
          Default: None (uses model default)
        - max_tokens (int): Maximum tokens in response.
          Default: None (uses model default)
        - max_retries (int): Max retries on transient errors.
          Default: 3
        - retry_backoff_seconds (int): Initial backoff seconds for retries.
          Default: 1
        - retry_backoff_factor (int): Backoff multiplier for retries.
          Default: 2
        
        Also settings from CrossDocumentExecutor and BaseExecutor apply.
    
    Example:
        ```yaml
        - id: cross_doc_comparison
          type: cross_document_comparison
          settings:
            endpoint: "${AZURE_OPENAI_ENDPOINT}"
            deployment_name: "gpt-4.1"
            comparison_instructions: |
              Compare the financial metrics across quarterly reports.
              Identify trends, variances, and risk indicators.
            comparison_fields:
              - "data.financial_metrics"
              - "data.tables"
            include_trend_analysis: true
            variance_threshold_pct: 10.0
        ```
    
    Input:
        Content with consolidated document set data (from DocumentSetCollectorExecutor)
        
    Output:
        Content with data[output_key] containing AI-generated comparison analysis
    """
    
    def __init__(
        self,
        id: str,
        settings: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        super().__init__(
            id=id,
            settings=settings,
            **kwargs
        )
        
        self.endpoint = self.get_setting("endpoint", default=None)
        self.deployment_name = self.get_setting("deployment_name", required=True)
        self.credential_type = self.get_setting("credential_type", default="default_azure_credential")
        self.api_key = self.get_setting("api_key", default=None)
        self.comparison_instructions = self.get_setting("comparison_instructions", default=None)
        self.comparison_fields = self.get_setting("comparison_fields", default=None)
        self.output_format = self.get_setting("output_format", default="structured")
        self.include_trend_analysis = self.get_setting("include_trend_analysis", default=True)
        self.include_variance_detection = self.get_setting("include_variance_detection", default=True)
        self.variance_threshold_pct = self.get_setting("variance_threshold_pct", default=10.0)
        self.temperature = self.get_setting("temperature", default=None)
        self.max_tokens = self.get_setting("max_tokens", default=None)
        self.max_retries = self.get_setting("max_retries", default=3)
        self.retry_backoff_seconds = self.get_setting("retry_backoff_seconds", default=1)
        self.retry_backoff_factor = self.get_setting("retry_backoff_factor", default=2)
        
        # Validate credential
        if self.credential_type not in ["default_azure_credential", "azure_key_credential"]:
            raise ValueError(f"{self.id}: Invalid credential_type '{self.credential_type}'")
        
        if self.credential_type == "azure_key_credential" and not self.api_key:
            raise ValueError(f"{self.id}: api_key must be provided for azure_key_credential")
        
        self.agent: Optional[ChatAgent] = None
        
        if self.debug_mode:
            logger.debug(
                f"CrossDocumentComparisonExecutor {self.id} initialized: "
                f"deployment={self.deployment_name}, format={self.output_format}"
            )
    
    def _init_agent(self) -> None:
        """Initialize the AI agent for cross-document comparison."""
        client_kwargs = {
            'deployment_name': self.deployment_name,
            'endpoint': self.endpoint,
            'credential': get_azure_credential() if self.credential_type == "default_azure_credential" else None,
            'api_key': self.api_key if self.credential_type == "azure_key_credential" else None,
        }
        
        client = AzureOpenAIResponsesClient(**client_kwargs)
        
        # Build system instructions
        instructions = self._build_system_instructions()
        
        agent_kwargs = {
            'id': f"{self.id}_agent",
            'name': f"{self.id}_agent",
            'temperature': self.temperature,
            'max_tokens': self.max_tokens,
            'instructions': instructions,
        }
        
        self.agent = client.create_agent(**agent_kwargs)
    
    def _build_system_instructions(self) -> str:
        """Build the system instructions for the comparison agent."""
        if self.comparison_instructions:
            instructions = self.comparison_instructions
        else:
            instructions = (
                "You are an expert document analyst specializing in cross-document comparison. "
                "You will receive data from multiple documents in a set. Your task is to analyze "
                "the data across all documents and provide a comprehensive comparison."
            )
        
        # Add format-specific instructions
        if self.output_format == "json":
            instructions += (
                "\n\nProvide your analysis as valid JSON with the following structure: "
                '{"summary": "...", "comparisons": [...], "trends": [...], "variances": [...], '
                '"recommendations": [...]}'
            )
        elif self.output_format == "structured":
            instructions += (
                "\n\nProvide your analysis as valid JSON with clearly labeled sections: "
                "summary, key_findings, comparisons, trends (if applicable), "
                "variances (if applicable), and recommendations."
            )
        elif self.output_format == "markdown":
            instructions += (
                "\n\nProvide your analysis in markdown format with clear headings for each section: "
                "Summary, Key Findings, Comparisons, Trends (if applicable), Variances (if applicable), "
                "and Recommendations."
            )
        
        if self.include_trend_analysis:
            instructions += (
                "\n\nInclude period-over-period trend analysis. Identify upward/downward trends, "
                "growth rates, and any inflection points."
            )
        
        if self.include_variance_detection:
            instructions += (
                f"\n\nFlag significant variances where changes exceed "
                f"{self.variance_threshold_pct}% between consecutive periods. "
                f"Explain potential causes for each variance."
            )
        
        return instructions
    
    async def process_document_set(
        self,
        set_data: Dict[str, Any],
        content: Content,
        ctx: WorkflowContext
    ) -> Content:
        """
        Run AI-powered cross-document comparison.
        
        Args:
            set_data: Consolidated document set data
            content: Parent Content item
            ctx: Workflow context
            
        Returns:
            Content with comparison analysis in data[output_key]
        """
        # Build the comparison payload
        comparison_payload = self._build_comparison_payload(set_data)
        
        # Format as query for the agent
        query = (
            f"Document Set: {set_data.get('set_name', 'Unknown')}\n"
            f"Total Documents: {set_data.get('total_documents', 0)}\n\n"
            f"Document Data:\n{json.dumps(comparison_payload, indent=2, default=str)}"
        )
        
        if self.debug_mode:
            logger.debug(
                f"{self.id}: Sending comparison query ({len(query)} chars) "
                f"for set '{set_data.get('set_name')}'"
            )
        
        # Run the agent
        response_text = await self._run_comparison(query)
        
        # Parse response
        analysis_result = self._parse_response(response_text)
        
        # Store results
        content.data[self.output_key] = {
            "type": "cross_document_comparison",
            "set_id": set_data.get("set_id", ""),
            "set_name": set_data.get("set_name", ""),
            "documents_compared": set_data.get("total_documents", 0),
            "analysis": analysis_result,
            "output_format": self.output_format,
            "generated_at": datetime.now().isoformat(),
        }
        
        return content
    
    def _build_comparison_payload(self, set_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Build the comparison payload from set data.
        
        If comparison_fields is set, only include those fields.
        Otherwise, include all document data.
        """
        documents = self.get_documents_ordered(set_data)
        payload = []
        
        for doc in documents:
            entry = {
                "role": doc.get("role", ""),
                "order": doc.get("order", 0),
                "filename": doc.get("filename", ""),
            }
            
            if self.comparison_fields:
                # Only include specified fields
                for field_path in self.comparison_fields:
                    value = self._extract_nested_value(doc, field_path)
                    if value is not None:
                        field_name = field_path.split(".")[-1]
                        entry[field_name] = value
            else:
                # Include all data
                entry["data"] = doc.get("data", {})
                entry["summary_data"] = doc.get("summary_data", {})
            
            payload.append(entry)
        
        return payload
    
    async def _run_comparison(self, query: str) -> str:
        """
        Run the comparison agent with retry logic.
        
        Args:
            query: The comparison query text
            
        Returns:
            Agent response text
        """
        retries = 0
        backoff = self.retry_backoff_seconds
        
        # Initialize agent if not already done
        if self.agent is None:
            self._init_agent()
        
        while True:
            try:
                result = await self.agent.run(query, store=False)
                response_text = result.text if hasattr(result, 'text') else str(result)
                return response_text
            except Exception as e:
                if retries >= self.max_retries:
                    raise
                logger.warning(
                    f"{self.id}: Retry {retries + 1}/{self.max_retries} after error: {e}"
                )
                
                # Handle unauthorized errors
                if (hasattr(e, "statusCode") and e.statusCode == 401) or \
                   (hasattr(e, "message") and "Unauthorized" in str(e.message)):
                    logger.info(f"{self.id}: Re-initializing agent due to unauthorized error.")
                    self._init_agent()
                
                await asyncio.sleep(backoff)
                backoff *= self.retry_backoff_factor
                retries += 1
    
    def _parse_response(self, response_text: str) -> Any:
        """
        Parse the agent response, attempting JSON extraction if applicable.
        
        Args:
            response_text: Raw response text from the agent
            
        Returns:
            Parsed response (dict if JSON, string otherwise)
        """
        if self.output_format in ("json", "structured"):
            try:
                # Try to extract JSON from the response
                start = response_text.find('{')
                end = response_text.rfind('}')
                if start != -1 and end != -1:
                    json_str = response_text[start:end + 1]
                    return json.loads(json_str)
            except json.JSONDecodeError:
                logger.warning(
                    f"{self.id}: Failed to parse response as JSON, "
                    f"returning raw text"
                )
        
        return response_text
