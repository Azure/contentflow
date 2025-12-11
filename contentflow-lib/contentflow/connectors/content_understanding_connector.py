"""
Azure Content Understanding connector for document analysis.

This connector provides access to Azure AI Content Understanding 
for document analysis, content extraction, and field extraction.
"""

import logging
import time
from typing import Dict, Any, Optional, List
from pathlib import Path

import requests

from .base import ConnectorBase
from ..utils.credential_provider import get_azure_credential

logger = logging.getLogger(__name__)


class ContentUnderstandingConnector(ConnectorBase):
    """
    Azure Content Understanding connector.
    
    Provides access to Azure AI Content Understanding for document analysis,
    content extraction, field extraction, and structured data extraction.
    
    Configuration:
        - endpoint: Content Understanding endpoint URL (supports ${ENV_VAR})
        - credential_type: 'subscription_key', 'token_provider', or 'default_azure_credential'
        - subscription_key: API subscription key (required for subscription_key)
        - api_version: API version (default: '2025-11-01')
        - timeout: Timeout in seconds for service calls (default: 180)
        - polling_interval: Seconds between polling for long-running operations (default: 2)
        - default_model_deployments: Default model deployment mappings
    
    Example:
        ```python
        connector = ContentUnderstandingConnector(
            name="content_understanding",
            settings={
                "endpoint": "${AZURE_CONTENT_UNDERSTANDING_ENDPOINT}",
                "credential_type": "default_azure_credential",
                "api_version": "2025-11-01",
                "timeout": 60,
                "default_model_deployments": {
                    "gpt-4.1": "myGpt41Deployment",
                    "gpt-4o": "myGpt4oDeployment",
                    "text-embedding-3-large": "myTextEmbedding3LargeDeployment"
                }
            }
        )
        
        await connector.initialize()
        
        # Analyze document from file
        result = await connector.analyze_document_binary(
            analyzer_id="prebuilt-documentSearch",
            file_path="document.pdf"
        )
        
        # Analyze document from URL
        result = await connector.analyze_document_url(
            analyzer_id="prebuilt-documentSearch",
            url="https://example.com/document.pdf"
        )
        ```
    """
   
    def __init__(self, name: str, settings: Dict[str, Any], **kwargs):
        super().__init__(
            name=name,
            connector_type="content_understanding",
            settings=settings,
            **kwargs
        )
        
        # Validate and resolve settings
        self.endpoint = self._resolve_setting("endpoint", required=True).rstrip("/")
        self.credential_type = self._resolve_setting("credential_type", required=True)
        self.api_version = self._resolve_setting("api_version", default="2025-11-01")
        
        # Validate credential type
        if self.credential_type not in ['azure_key_credential', 'default_azure_credential']:
            raise ValueError(
                f"Unsupported credential type: {self.credential_type}. "
                f"Supported types are 'azure_key_credential' and 'default_azure_credential'."
            )
        
        # Get subscription key if using key-based auth
        self.subscription_key = None
        if self.credential_type == 'azure_key_credential':
            self.subscription_key = self._resolve_setting("subscription_key", required=True)
        
        self.timeout = self._resolve_setting("timeout", default=180)
        if isinstance(self.timeout, str):
            self.timeout = int(self.timeout)
            
        self.polling_interval = self._resolve_setting("polling_interval", default=2)
        if isinstance(self.polling_interval, str):
            self.polling_interval = int(self.polling_interval)
        
        self.default_model_deployments = self._resolve_setting("default_model_deployments", default=None)
        
        # Initialize headers reference
        self.headers: Optional[Dict[str, str]] = None
    
    async def initialize(self) -> None:
        """Initialize the Content Understanding connector."""
        if self.headers:
            return
        
        logger.debug(
            f"Initializing ContentUnderstandingConnector with endpoint: {self.endpoint} "
            f"and credential type: {self.credential_type}"
        )
        
        self.headers = {}
        
        if self.credential_type == 'azure_key_credential':
            self.headers["Ocp-Apim-Subscription-Key"] = self.subscription_key
        elif self.credential_type == 'default_azure_credential':
            credential = get_azure_credential()
            token = credential.get_token("https://cognitiveservices.azure.com/.default")
            self.headers["Authorization"] = f"Bearer {token.token}"
        
        if self.default_model_deployments:
            # Update defaults on the service
            
            # parse model deployments
            if isinstance(self.default_model_deployments, str):
                # split by comma
                deployments_list = self.default_model_deployments.split(",")
                deployments_dict = {}
                for item in deployments_list:
                    if ":" in item:
                        model, deployment = item.split(":", 1)
                        deployments_dict[model.strip()] = deployment.strip()
                self.default_model_deployments = deployments_dict
            
                self.update_defaults(self.default_model_deployments)
                logger.info(
                    f"Set default model deployments: {self.default_model_deployments}"
                )
            else:
                self.update_defaults(self.default_model_deployments)
                logger.info(
                    f"Set default model deployments: {self.default_model_deployments}"
                )
            
        logger.info(f"Initialized ContentUnderstandingConnector '{self.name}'")
   
    def _get_analyze_binary_url(self, analyzer_id: str) -> str:
        """Get URL for binary analyze endpoint."""
        return f"{self.endpoint}/contentunderstanding/analyzers/{analyzer_id}:analyzeBinary?api-version={self.api_version}"
    
    def _get_analyze_url(self, analyzer_id: str) -> str:
        """Get URL for analyze endpoint (for URLs)."""
        return f"{self.endpoint}/contentunderstanding/analyzers/{analyzer_id}:analyze?api-version={self.api_version}"
    
    def _get_defaults_url(self) -> str:
        return f"{self.endpoint}/contentunderstanding/defaults?api-version={self.api_version}"
    
    def _raise_for_status_with_detail(self, response: requests.Response) -> None:
        """Raise HTTPError with detailed error message if request failed."""
        if not response.ok:
            try:
                error_detail = response.json()
                error_msg = f"HTTP {response.status_code}: {error_detail}"
            except Exception:
                error_msg = f"HTTP {response.status_code}: {response.text}"
            
            logger.error(f"Content Understanding API error: {error_msg}")
            response.raise_for_status()
    
    def get_defaults(self) -> Dict[str, Any]:
        """
        Retrieves the current default settings for the Content Understanding resource.

        This method sends a GET request to the service endpoint to fetch the default
        model deployment mappings.

        Returns:
            dict: A dictionary containing the default settings, including modelDeployments.
                  Example: {"modelDeployments": {"gpt-4.1": "myGpt41Deployment", ...}}

        Raises:
            requests.exceptions.HTTPError: If the HTTP request returned an unsuccessful status code.
        """
        response = requests.get(
            url=self._get_defaults_url(),
            headers=self.headers,
        )
        self._raise_for_status_with_detail(response)
        return response.json()

    def update_defaults(self, model_deployments: Dict[str, Optional[str]]) -> Dict[str, Any]:
        """
        Updates the default model deployment mappings for the Content Understanding resource.

        This is a PATCH operation using application/merge-patch+json. You can update individual
        model deployments without sending the entire object. Any keys you include will be
        added/updated. You can remove keys by setting them to None.

        Args:
            model_deployments (Dict[str, Optional[str]]): A dictionary mapping model names to
                deployment names. Set a value to None to remove that mapping.
                Example: {"gpt-4.1": "myGpt41Deployment", "gpt-4o": "myGpt4oDeployment", "text-embedding-3-large": "myTextEmbedding3LargeDeployment"}

        Returns:
            dict: A dictionary containing the updated default settings.

        Raises:
            requests.exceptions.HTTPError: If the HTTP request returned an unsuccessful status code.

        Example:
            # Update specific deployments
            client.update_defaults({
                "gpt-4o": "new-deployment-name",
                "text-embedding-3-large": "myTextEmbedding3LargeDeployment"
            })

            # Remove a deployment mapping
            client.update_defaults({"gpt-4.1": None})
        """
        headers = self.headers.copy()
        headers["Content-Type"] = "application/merge-patch+json"

        body = {"modelDeployments": model_deployments}

        response = requests.patch(
            url=self._get_defaults_url(),
            headers=headers,
            json=body,
        )
        self._raise_for_status_with_detail(response)
        return response.json()
    
    async def analyze_document_binary(
        self,
        file_path: str,
        analyzer_id: str = "prebuilt-documentSearch"
    ) -> Dict[str, Any]:
        """
        Analyze a document from a local file using Content Understanding.
        
        Args:
            file_path: Path to the document file
            analyzer_id: Analyzer to use (e.g., 'prebuilt-documentSearch', 'prebuilt-layout'). 
                        Default is 'prebuilt-documentSearch'.
            
        Returns:
            Analysis result dictionary
        """
        if not self.headers:
            raise RuntimeError("Connector not initialized. Call initialize() first.")
        
        file_path_obj = Path(file_path)
        if not file_path_obj.exists() or not file_path_obj.is_file():
            raise ValueError(f"File not found or not a valid file: {file_path}")
        
        try:
            with open(file_path, "rb") as file:
                file_bytes = file.read()
            
            headers = {"Content-Type": "application/octet-stream"}
            headers.update(self.headers)
            
            logger.debug(
                f"Analyzing binary file {file_path} ({len(file_bytes)} bytes) "
                f"with analyzer '{analyzer_id}'"
            )
            
            response = requests.post(
                url=self._get_analyze_binary_url(analyzer_id),
                headers=headers,
                data=file_bytes
            )
            
            self._raise_for_status_with_detail(response)
            
            logger.info(f"Started analysis for file {file_path} with analyzer {analyzer_id}")
            
            # Poll for results
            return await self.poll_result(response)
            
        except Exception as e:
            logger.error(f"Error analyzing document from file {file_path}: {str(e)}")
            raise
    
    async def analyze_document_url(
        self,
        url: str,
        analyzer_id: str = "prebuilt-documentSearch"
    ) -> Dict[str, Any]:
        """
        Analyze a document from a URL using Content Understanding.
        
        Args:
            url: URL to the document
            analyzer_id: Analyzer to use (e.g., 'prebuilt-documentSearch', 'prebuilt-layout'). 
                        Default is 'prebuilt-documentSearch'.
                        
        Returns:
            Analysis result dictionary
        """
        if not self.headers:
            raise RuntimeError("Connector not initialized. Call initialize() first.")
        
        if not (url.startswith("https://") or url.startswith("http://")):
            raise ValueError("URL must start with http:// or https://")
        
        try:
            # URL must be wrapped in inputs array
            data = {"inputs": [{"url": url}]}
            headers = {"Content-Type": "application/json"}
            headers.update(self.headers)
            
            logger.debug(f"Analyzing document from URL {url} with analyzer '{analyzer_id}'")
            
            response = requests.post(
                url=self._get_analyze_url(analyzer_id),
                headers=headers,
                json=data
            )
            
            self._raise_for_status_with_detail(response)
            
            logger.info(f"Started analysis for URL {url} with analyzer {analyzer_id}")
            
            # Poll for results
            return await self.poll_result(response)
            
        except Exception as e:
            logger.error(f"Error analyzing document from URL {url}: {str(e)}")
            raise
    
    async def poll_result(
        self,
        response: requests.Response,
        timeout_seconds: int = None,
        polling_interval_seconds: int = None
    ) -> Dict[str, Any]:
        """
        Poll for analysis results until completion.
        
        Args:
            response: Initial response from analyze operation
            timeout_seconds: Maximum time to wait for results
            polling_interval_seconds: Time between polling attempts
            
        Returns:
            Final analysis result
        """
        timeout = timeout_seconds or self.timeout
        interval = polling_interval_seconds or self.polling_interval
        
        operation_location = response.headers.get("operation-location", "")
        if not operation_location:
            raise ValueError("Operation location not found in response headers")
        
        start_time = time.time()
        
        while True:
            if time.time() - start_time > timeout:
                raise TimeoutError(
                    f"Analysis operation timed out after {timeout} seconds"
                )
            
            # Poll the operation location
            poll_response = requests.get(
                url=operation_location,
                headers=self.headers
            )
            
            self._raise_for_status_with_detail(poll_response)
            
            result = poll_response.json()
            status = result.get("status", "").lower()
            
            logger.debug(f"Polling status: {status}")
            
            if status == "succeeded":
                logger.info("Analysis completed successfully")
                return result
            elif status in ["failed", "canceled"]:
                error_msg = result.get("error", {})
                raise RuntimeError(
                    f"Analysis operation {status}: {error_msg}"
                )
            
            # Wait before next poll
            time.sleep(interval)
    
    def extract_content(
        self,
        analysis_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Extract content from analysis result.
        
        Args:
            analysis_result: Result from analyze operation
            
        Returns:
            Dictionary with extracted content including text, markdown, tables, etc.
        """
        extracted = {
            "text": "",
            "markdown": "",
            "tables": [],
            "pages": [],
            "fields": {}
        }
        
        result = analysis_result.get("result", {})
        contents = result.get("contents", [])
        
        if not contents:
            return extracted
        
        # Get first content item (usually the document)
        content = contents[0]
        
        # Extract text and markdown
        extracted["text"] = content.get("text", "")
        extracted["markdown"] = content.get("markdown", "")
        
        # Extract fields if present
        extracted["fields"] = content.get("fields", {})
        
        # Extract pages
        pages = content.get("pages", [])
        for page in pages:
            page_info = {
                "page_number": page.get("pageNumber"),
                "text": page.get("text", ""),
                "markdown": page.get("markdown", "")
            }
            extracted["pages"].append(page_info)
        
        # Extract tables
        tables = content.get("tables", [])
        for table in tables:
            table_data = {
                "row_count": table.get("rowCount"),
                "column_count": table.get("columnCount"),
                "cells": table.get("cells", [])
            }
            extracted["tables"].append(table_data)
        
        return extracted
    
    async def cleanup(self) -> None:
        """Cleanup connector resources."""
        self.headers = None
        logger.info(f"Cleaned up ContentUnderstandingConnector '{self.name}'")
