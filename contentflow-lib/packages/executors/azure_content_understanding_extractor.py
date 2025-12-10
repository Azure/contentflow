"""Azure Content Understanding executor for document analysis and extraction."""

from datetime import datetime
import logging
from typing import Dict, Any, Optional, List, Union

from agent_framework import WorkflowContext

from . import ParallelExecutor
from ..models import Content, ExecutorLogEntry
from ..connectors import ContentUnderstandingConnector

logger = logging.getLogger(__name__)


class AzureContentUnderstandingExtractorExecutor(ParallelExecutor):
    """
    Extract content from documents using Azure Content Understanding.
    
    This executor analyzes documents to extract text, layout, tables,
    fields, and structured data using Azure Content Understanding service.
    
    Configuration (settings dict):
        - analyzer_id (str): Content Understanding analyzer to use
          Default: "prebuilt-documentSearch"
          Options: "prebuilt-documentSearch", "prebuilt-layout", "prebuilt-read",
                   "prebuilt-invoice", "prebuilt-receipt", etc.
        - content_field (str): Field containing document bytes
          Default: "content"
        - temp_file_path_field (str): Field containing temp file path
          Default: "temp_file_path"
        - url_field (str): Field containing document URL
          Default: "url"
        - output_field (str): Field name for extracted data
          Default: "content_understanding_output"
        - max_concurrent (int): Max concurrent document processing
          Default: 3
        - continue_on_error (bool): Continue if a content item fails
          Default: True
        - content_understanding_endpoint (str): Content Understanding service endpoint
          Default: None (must be provided)
        - content_understanding_credential_type (str): Credential type for service
          Default: "default_azure_credential"
          Options: "azure_key_credential", "default_azure_credential"
        - content_understanding_subscription_key (str): Subscription key if needed
          Default: None
        - content_understanding_api_version (str): API version to use
          Default: "2025-11-01"
        - content_understanding_timeout (int): Timeout in seconds for service calls
          Default: 60
        - content_understanding_model_mappings (str): Default model deployment mappings in Json format.
          Default: None
    
    Example:
        ```python
        executor = AzureContentUnderstandingExtractorExecutor(
            id="content_understanding_extractor",
            settings={
                "analyzer_id": "prebuilt-documentSearch",
                "content_understanding_endpoint": "<your_endpoint>",
            }
        )
        ```
    
    Input:
        Document or List[Document] each with (ContentIdentifier) id containing:
        - data['content']: Document bytes, OR
        - data['temp_file_path']: Path to document file, OR
    
    Output:
        Document or List[Document] with added fields:
        - data['content_understanding_output']: Dict with content from Azure Content Understanding
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
        self.analyzer_id = self.get_setting("analyzer_id", default="prebuilt-documentSearch")
        self.content_field = self.get_setting("content_field", default="content")
        self.temp_file_field = self.get_setting("temp_file_path_field", default="temp_file_path")
        self.output_field = self.get_setting("output_field", default="content_understanding_output")
        
        # Content Understanding connector config
        self.content_understanding_endpoint = self.get_setting("content_understanding_endpoint", default=None, required=True)
        if not self.content_understanding_endpoint:
            raise ValueError("Content Understanding endpoint must be provided in settings")
        
        self.content_understanding_credential_type = self.get_setting(
            "content_understanding_credential_type", 
            default="default_azure_credential"
        )
        self.content_understanding_subscription_key = self.get_setting(
            "content_understanding_subscription_key", 
            default=None
        )
        self.content_understanding_api_version = self.get_setting(
            "content_understanding_api_version", 
            default="2025-11-01"
        )
        self.content_understanding_timeout = self.get_setting(
            "content_understanding_timeout", 
            default=180
        )
        self.content_understanding_polling_interval = self.get_setting(
            "content_understanding_polling_interval", 
            default=2
        )
        self.content_understanding_model_mappings = self.get_setting(
            "content_understanding_model_mappings",
            default=None,
            required=True
        )
        if not isinstance(self.content_understanding_model_mappings, str):
            raise ValueError("'content_understanding_model_mappings' must be a JSON string of model to deployment ID mappings.")
        try:
            import json
            self.content_understanding_model_mappings = json.loads(self.content_understanding_model_mappings)
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse 'content_understanding_model_mappings' JSON string: {e}")
        
        # Create connector
        connector_settings = {
            "endpoint": self.content_understanding_endpoint,
            "credential_type": self.content_understanding_credential_type,
            "api_version": self.content_understanding_api_version,
            "timeout": self.content_understanding_timeout,
            "polling_interval": self.content_understanding_polling_interval,
            "default_model_deployments": self.content_understanding_model_mappings
        }
        
        if self.content_understanding_subscription_key:
            connector_settings["subscription_key"] = self.content_understanding_subscription_key
        
        self.content_understanding_connector: ContentUnderstandingConnector = ContentUnderstandingConnector(
            name="content_understanding_connector",
            settings=connector_settings
        )
        
        if self.debug_mode:
            logger.debug(
                f"AzureContentUnderstandingExtractorExecutor with id {self.id} initialized: "
                f"analyzer={self.analyzer_id}"
            )

    async def process_content_item(
        self,
        content: Content
    ) -> Content:
        """Process a single content item using Azure Content Understanding.
           Implements the abstract method from ParallelExecutor.
        """

        # Initialize the connector
        await self.content_understanding_connector.initialize()
        
        try:
            if not content or not content.data:
                raise ValueError("Content must have data")
            
            # Determine input type and analyze accordingly
            analysis_result = None
            
            # Priority: temp_file > content bytes
            if self.temp_file_field in content.data:
                temp_file_path = content.data[self.temp_file_field]
                
                if self.debug_mode:
                    logger.debug(
                        f"Analyzing document {content.id} from file '{temp_file_path}' "
                        f"with analyzer '{self.analyzer_id}'"
                    )
                
                analysis_result = await self.content_understanding_connector.analyze_document_binary(
                    file_path=temp_file_path,
                    analyzer_id=self.analyzer_id
                )
            
            elif self.content_field in content.data:
                # Need to write to temp file for binary analysis
                import tempfile
                
                content_bytes = content.data[self.content_field]
                
                # Create temp file
                with tempfile.NamedTemporaryFile(delete=False, suffix=".tmp") as tmp_file:
                    tmp_file.write(content_bytes)
                    tmp_file_path = tmp_file.name
                
                if self.debug_mode:
                    logger.debug(
                        f"Analyzing document {content.id} from bytes ({len(content_bytes)} bytes) "
                        f"with analyzer '{self.analyzer_id}'"
                    )
                
                try:
                    analysis_result = await self.content_understanding_connector.analyze_document_binary(
                        file_path=tmp_file_path,
                        analyzer_id=self.analyzer_id
                    )
                finally:
                    # Clean up temp file
                    import os
                    try:
                        os.unlink(tmp_file_path)
                    except Exception:
                        pass
            
            else:
                raise ValueError(
                    f"Document missing required content. "
                    f"Needs one of: '{self.url_field}', '{self.temp_file_field}', or '{self.content_field}'"
                )
            
            # Store response as output
            content.data[f"{self.output_field}"] = analysis_result
            
            # Update summary
            content.summary_data['extraction_status'] = "success"
            content.summary_data['analyzer_id'] = self.analyzer_id

        except Exception as e:
            logger.error(
                f"AzureContentUnderstandingExtractorExecutor {self.id} failed processing document {content.id}",
                exc_info=True
            )
            logger.exception(e)
            
            # raise the exception to be handled upstream if needed
            raise
        
        return content
