"""
Azure Document Intelligence connector for document analysis.

This connector provides access to Azure Document Intelligence (formerly Form Recognizer)
for document layout analysis, OCR, and structured data extraction.
"""

import logging
from typing import Dict, Any, Optional, List

from azure.core.credentials import AzureKeyCredential
from azure.ai.documentintelligence.aio import DocumentIntelligenceClient, DocumentIntelligenceAdministrationClient
from azure.ai.documentintelligence.models import AnalyzeDocumentRequest, DocumentContentFormat, AnalyzeResult

from ..utils import get_azure_credential_async

from .base import ConnectorBase

logger = logging.getLogger(__name__)


class DocumentIntelligenceConnector(ConnectorBase):
    """
    Azure Document Intelligence connector.
    
    Provides access to Azure Document Intelligence for document analysis,
    OCR, layout analysis, and structured data extraction.
    
    Configuration:
        - endpoint: Document Intelligence endpoint URL (supports ${ENV_VAR})
        - credential_type: 'azure_key_credential' or 'default_azure_credential'
        - api_key: API key (required for azure_key_credential)
        - api_version: API version (default: '2024-07-31-preview')
    
    Example:
        ```python
        connector = DocumentIntelligenceConnector(
            name="doc_intelligence",
            settings={
                "endpoint": "${DOC_INTELLIGENCE_ENDPOINT}",
                "credential_type": "default_azure_credential",
                "api_version": "2024-07-31-preview"
            }
        )
        
        await connector.initialize()
        
        # Analyze document
        result = await connector.analyze_document(
            document_bytes=pdf_content,
            model_id="prebuilt-layout"
        )
        ```
    """
    
    def __init__(self, name: str, settings: Dict[str, Any], **kwargs):
        super().__init__(
            name=name,
            connector_type="document_intelligence",
            settings=settings,
            **kwargs
        )
        
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
        self.client: Optional[DocumentIntelligenceClient] = None
    
    async def initialize(self) -> None:
        """Initialize the Document Intelligence client."""
        if self.client:
            return
        
        logger.debug(
            f"Creating DocumentIntelligenceClient with endpoint: {self.endpoint} "
            f"and credential type: {self.credential_type}"
        )
        
        if self.credential_type == 'azure_key_credential':
            self.client = DocumentIntelligenceClient(
                endpoint=self.endpoint,
                credential=AzureKeyCredential(self.api_key)
            )
        else:  # default_azure_credential
            credential = await get_azure_credential_async()
            self.client = DocumentIntelligenceClient(
                endpoint=self.endpoint,
                credential=credential
            )
        
        logger.info(
            f"Initialized DocumentIntelligenceConnector '{self.name}' "
        )
   
    async def analyze_document(
        self,
        document_bytes: bytes,
        model_id: str = "prebuilt-layout",
        output_content_format: str = "markdown",
        features: Optional[List[str]] = None,
        pages: Optional[str] = None,
        locale: Optional[str] = None
    ) -> AnalyzeResult:
        """
        Analyze a document using Document Intelligence.
        
        Args:
            document_bytes: Document content as bytes
            model_id: Model to use for analysis (e.g., 'prebuilt-layout', 'prebuilt-document'). Default is 'prebuilt-layout'.
            output_content_format: Output content format, either "text" or "markdown". Default is "markdown".
            features: Additional features to extract (e.g., ['ocrHighResolution', 'keyValuePairs']). Valid values are the enumeration azure.ai.documentintelligence.models.DocumentAnalysisFeature defined in the SDK. Default is None.
            pages: 1-based page numbers to analyze.  Ex. "1-3,5,7-9". Default value is None.
            locale: Locale hint for text recognition and document analysis.  Value may contain only the language code (ex. "en", "fr") or BCP 47 language tag (ex. "en-US"). Default value is None.
            
        Returns:
            AnalyzeResult with document analysis
        """
        if not self.client:
            raise RuntimeError("Connector not initialized. Call initialize() first.")
        
        try:
            poller = await self.client.begin_analyze_document(
                    model_id=model_id,
                    body=AnalyzeDocumentRequest(
                        bytes_source=document_bytes,
                    ),
                    pages=pages,
                    locale=locale,
                    features=features,
                    output_content_format= DocumentContentFormat.TEXT if output_content_format == "text" else DocumentContentFormat.MARKDOWN,
                )
                
            result: AnalyzeResult = await poller.result()

            return result

        except Exception as e:
            logger.error(f"Error analyzing document from bytes: {str(e)}")
            raise
        
    async def analyze_document_from_url(
        self,
        document_url: str,
        model_id: str = "prebuilt-layout",
        output_content_format: str = "markdown",
        features: Optional[List[str]] = None,
        pages: Optional[str] = None,
        locale: Optional[str] = None
    ) -> AnalyzeResult:
        """
        Analyze a document from URL using Document Intelligence.
        
        Args:
            document_url: URL to document
            model_id: Model to use for analysis (e.g., 'prebuilt-layout', 'prebuilt-document'). Default is 'prebuilt-layout'.
            output_content_format: Output content format, either "text" or "markdown". Default is "markdown".
            features: Additional features to extract (e.g., ['ocrHighResolution', 'keyValuePairs']). Valid values are the enumeration azure.ai.documentintelligence.models.DocumentAnalysisFeature defined in the SDK. Default is None.
            pages: 1-based page numbers to analyze.  Ex. "1-3,5,7-9". Default value is None.
            locale: Locale hint for text recognition and document analysis.  Value may contain only the language code (ex. "en", "fr") or BCP 47 language tag (ex. "en-US"). Default value is None.
                        
        Returns:
            AnalyzeResult with document analysis
        """
        if not self.client:
            raise RuntimeError("Connector not initialized. Call initialize() first.")
               
        try:
            poller = await self.client.begin_analyze_document(
                    model_id=model_id,
                    body=AnalyzeDocumentRequest(
                        url_source=document_url,
                    ),
                    pages=pages,
                    locale=locale,
                    features=features,
                    output_content_format= DocumentContentFormat.TEXT if output_content_format == "text" else DocumentContentFormat.MARKDOWN,
                )
                
            result: AnalyzeResult = await poller.result()
                
            return result

        except Exception as e:
            logger.error(f"Error analyzing document from URL: {str(e)}")
            raise
    
    def extract_text(self, analyze_result: AnalyzeResult) -> str:
        """
        Extract plain text from analysis result.
        
        Args:
            analyze_result: Result from analyze_document
            
        Returns:
            Extracted text content
        """
        if analyze_result.content:
            return analyze_result.content
        
        # Fallback: concatenate paragraphs
        if analyze_result.paragraphs:
            return "\n\n".join(
                p.content for p in analyze_result.paragraphs if p.content
            )
        
        return ""
    
    def extract_tables(
        self,
        analyze_result: AnalyzeResult
    ) -> List[Dict[str, Any]]:
        """
        Extract tables from analysis result.
        
        Args:
            analyze_result: Result from analyze_document
            
        Returns:
            List of table dicts with row/column structure
        """
        if not analyze_result.tables:
            return []
        
        tables = []
        for table in analyze_result.tables:
            table_data = {
                "row_count": table.row_count,
                "column_count": table.column_count,
                "cells": []
            }
            
            for cell in table.cells:
                table_data["cells"].append({
                    "row_index": cell.row_index,
                    "column_index": cell.column_index,
                    "content": cell.content,
                    "kind": cell.kind
                })
            
            tables.append(table_data)
        
        return tables
    
    def extract_key_value_pairs(
        self,
        analyze_result: AnalyzeResult
    ) -> Dict[str, str]:
        """
        Extract key-value pairs from analysis result.
        
        Args:
            analyze_result: Result from analyze_document
            
        Returns:
            Dict of key-value pairs
        """
        if not analyze_result.key_value_pairs:
            return {}
        
        kv_pairs = {}
        for kv in analyze_result.key_value_pairs:
            if kv.key and kv.key.content and kv.value and kv.value.content:
                kv_pairs[kv.key.content] = kv.value.content
        
        return kv_pairs
    
    def extract_figures(
        self,
        analyze_result: AnalyzeResult
    ) -> List[Dict[str, Any]]:
        """
        Extract figures (images, graphics) from analysis result.
        
        Args:
            analyze_result: Result from analyze_document
        Returns:
            List of figure dicts
        """
        
        figures = []
        if analyze_result.figures:
            
            md_content = analyze_result.content if analyze_result.content else ""
            
            for idx, figure in enumerate(analyze_result.figures):
                figure_id = idx
                figure_content = ""
                figure_caption = ""
                figure_page_number = -1
                
                if figure.id:
                    figure_id = figure.id
                
                if figure.bounding_regions and len(figure.bounding_regions) > 0:
                    figure_page_number = figure.bounding_regions[0].page_number
                
                if figure.spans:
                    for span in figure.spans:
                        figure_content += md_content[span.offset:span.offset + span.length]
                if figure.caption and figure.caption.content:
                    figure_caption = figure.caption.content
                
                figures.append({
                    "id": figure_id,
                    "page_number": figure_page_number,
                    "content": figure_content,
                    "caption": figure_caption
                })
        
        return figures
    
    async def cleanup(self) -> None:
        """Cleanup connector resources."""
        if self.client:
            self.client.close()
        
        self.client = None
        logger.info(f"Cleaned up DocumentIntelligenceConnector '{self.name}'")
