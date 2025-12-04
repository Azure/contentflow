"""Document Intelligence executor for document analysis and extraction."""

from datetime import datetime
import logging
from typing import Dict, Any, Optional, List, Union

from agent_framework import WorkflowContext

from . import ParallelExecutor
from ..models import Content, ExecutorLogEntry
from ..connectors import DocumentIntelligenceConnector

logger = logging.getLogger(__name__)


class AzureDocumentIntelligenceExtractorExecutor(ParallelExecutor):
    """
    Extract content from documents using Azure Document Intelligence.
    
    This executor analyzes documents to extract text, layout, tables,
    and key-value pairs using Azure Document Intelligence service.
    
    Configuration (settings dict):
        - model_id (str): Document Intelligence model to use
          Default: "prebuilt-layout"
          Options: "prebuilt-layout", "prebuilt-document", "prebuilt-read"
        - output_format (str): Format of extracted content
          Default: "markdown"
          Options: "markdown", "text"
        - doc_intel_features (list): Additional features to extract
          Default: []
        - extract_text (bool): Extract plain text
          Default: True
        - extract_tables (bool): Extract tables
          Default: True
        - extract_key_value_pairs (bool): Extract key-value pairs
          Default: False
        - extract_figures (bool): Extract figures
          Default: True
        - pages (str): Page range to analyze (e.g., "1-5")
          Default: None (all pages)
        - locale (str): Document locale (e.g., "en-US")
          Default: None (auto-detect)
        - content_field (str): Field containing document bytes
          Default: "content"
        - temp_file_path_field (str): Field containing temp file path
          Default: "temp_file_path"
        - output_field (str): Field name for extracted data
          Default: "doc_intell_output"
        - include_full_result (bool): Include full raw result from document 
          intelligence service. Useful for debugging.
          Default: False
        - max_concurrent (int): Max concurrent document processing
          Default: 3
        - continue_on_error (bool): Continue if a content item fails
          Default: True
        - doc_intelligence_endpoint (str): Document Intelligence service endpoint
          Default: None (must be provided)
        - doc_intelligence_credential_type (str): Credential type for service
          Default: "default_azure_credential"
        - doc_intelligence_credential_key (str): Credential key if needed
          Default: None
    
    Example:
        ```python
        executor = AzureDocumentIntelligenceExtractorExecutor(
            id="azure_document_intelligence_extractor",
            settings={
                "model_id": "prebuilt-layout",
                "extract_text": True,
                "extract_tables": True,
                "extract_key_value_pairs": True,
                "doc_intelligence_endpoint": "<your_endpoint>",
            }
        )
        ```
    
    Input:
        Document or List[Document] each with (ContentIdentifier) id containing:
        - data['content']: Document bytes, OR
        - data['temp_file_path']: Path to document file
        
    Output:
        Document or List[Document] with added fields:
        - data['doc_intell_output']['text']: Extracted text
        - data['doc_intell_output']['tables']: Extracted tables
        - data['doc_intell_output']['key_value_pairs']: Extracted KV pairs
        - data['doc_intell_output']['pages']: Page-level chunks with text
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
        self.model_id = self.get_setting("model_id", default="prebuilt-layout")
        self.output_format = self.get_setting("output_format", default="markdown")
        self.doc_intel_features = self.get_setting("doc_intel_features", default=[])
        self.extract_text = self.get_setting("extract_text", default=True)
        self.extract_tables = self.get_setting("extract_tables", default=True)
        self.extract_kv_pairs = self.get_setting("extract_key_value_pairs", default=False)
        self.extract_figures = self.get_setting("extract_figures", default=True)
        self.pages = self.get_setting("pages", default=None)
        self.locale = self.get_setting("locale", default=None)
        self.content_field = self.get_setting("content_field", default="content")
        self.temp_file_field = self.get_setting("temp_file_path_field", default="temp_file_path")
        self.output_field = self.get_setting("output_field", default="doc_intell_output")
        self.include_full_result = self.get_setting("include_full_result", default=False)
        
        # Document intelligence connector config
        self.doc_intelligence_endpoint = self.get_setting("doc_intelligence_endpoint", default=None)
        if not self.doc_intelligence_endpoint:
            raise ValueError("Document Intelligence endpoint must be provided in settings")
        
        self.doc_intelligence_credential_type = self.get_setting("doc_intelligence_credential_type", default="default_azure_credential")
        self.doc_intelligence_credential_key = self.get_setting("doc_intelligence_credential_key", default=None)
        
        self.doc_intelligence_connector: DocumentIntelligenceConnector = DocumentIntelligenceConnector(
            name="doc_intelligence_connector",
            settings={
                "endpoint": self.doc_intelligence_endpoint,
                "credential_type": self.doc_intelligence_credential_type,
                "credential_key": self.doc_intelligence_credential_key
            }
        )
                
        if self.debug_mode:
            logger.debug(
                f"DocumentIntelligenceExtractorExecutor with id {self.id} initialized: "
                f"model={self.model_id}, text={self.extract_text}, "
                f"tables={self.extract_tables}, kv={self.extract_kv_pairs}"
            )
        
    async def process_content_item(
        self,
        content: Content
    ) -> Content:
        """Process a single content item using Azure Document Intelligence.
           Implements the abstract method from ParallelExecutor.
        """

        # Initialize the connector
        await self.doc_intelligence_connector.initialize()
        
        try:
            if not content or not content.data:
                raise ValueError("Content must have data")
            
            # Get document content
            content_bytes = None
            
            # Try to get from content field
            if self.content_field in content.data:
                content_bytes = content.data[self.content_field]
            
            # Try to get from temp file
            elif self.temp_file_field in content.data:
                temp_file_path = content.data[self.temp_file_field]
                with open(temp_file_path, 'rb') as f:
                    content_bytes = f.read()
            
            if not content_bytes:
                raise ValueError(
                    f"Document missing required content. "
                    f"Needs either '{self.content_field}' or '{self.temp_file_field}'"
                )
            
            if self.debug_mode:
                logger.debug(
                    f"Analyzing document {content.id} with model '{self.model_id}' "
                    f"({len(content_bytes)} bytes)"
                )
            
            # Analyze document (sync operation in SDK)
            result = await self.doc_intelligence_connector.analyze_document(
                document_bytes=content_bytes,
                model_id=self.model_id,
                output_content_format=self.output_format,
                features=self.doc_intel_features,
                pages=self.pages,
                locale=self.locale
            )
            
            if self.include_full_result:
                # Store full raw result for debugging
                content.data[f"{self.output_field}_full_result"] = result.as_dict()
            
            # Extract requested data
            extracted_data = {}
            
            if self.extract_text:
                text = self.doc_intelligence_connector.extract_text(result)
                extracted_data['text'] = text
                
                if self.debug_mode:
                    logger.debug(f"Extracted {len(text)} characters of text")
            
            if self.extract_tables:
                tables = self.doc_intelligence_connector.extract_tables(result)
                extracted_data['tables'] = tables
                
                if self.debug_mode:
                    logger.debug(f"Extracted {len(tables)} tables")
            
            if self.extract_kv_pairs:
                kv_pairs = self.doc_intelligence_connector.extract_key_value_pairs(result)
                extracted_data['key_value_pairs'] = kv_pairs
                
                if self.debug_mode:
                    logger.debug(f"Extracted {len(kv_pairs)} key-value pairs")
            
            if self.extract_figures:
                figures = self.doc_intelligence_connector.extract_figures(result)
                extracted_data['figures'] = figures
                
                if self.debug_mode:
                    logger.debug(f"Extracted {len(figures)} figures")
            
            # Store in content
            content.data[self.output_field] = extracted_data
            
            # Create page-level chunks
            if result.pages:
                pages = []
                for page in result.pages:
                    page_info = {
                        "page_number": page.page_number,
                        "width": page.width,
                        "height": page.height,
                        "unit": page.unit,
                        "text": ""
                    }
                    
                    # Extract text for this page
                    if page.lines:
                        page_info["text"] = "\n".join(line.content for line in page.lines if line.content)
                    
                    pages.append(page_info)
                
                extracted_data['pages'] = pages
                
                if self.debug_mode:
                    logger.debug(f"Created {len(pages)} page chunks")
            
            # Store in content
            content.data[self.output_field] = extracted_data
            
            # Update summary
            content.summary_data['pages_analyzed'] = len(result.pages) if result.pages else 0
            content.summary_data['extraction_status'] = "success"
                            
        except Exception as e:
            logger.error(
                f"DocumentIntelligenceExtractorExecutor {self.id} failed processing document {content.id}",
                exc_info=True
            )
            logger.exception(e)
            
            # raise the exception to be handled upstream if needed
            raise
        
        return content
