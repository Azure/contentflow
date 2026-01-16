"""Search indexer executor for transforming content into Azure AI Search document format."""

import logging
import json
import hashlib
from typing import Dict, Any, Optional, List
from datetime import datetime

from agent_framework import WorkflowContext

from .parallel_executor import ParallelExecutor
from ..models import Content

logger = logging.getLogger("contentflow.executors.gpt_rag_search_index_document_generator")


class GPTRAGSearchIndexDocumentGeneratorExecutor(ParallelExecutor):
    """
    Transform Content items into Azure AI Search indexable documents.
    
    This executor converts extracted content (with markdown, chunks, and metadata)
    into the format expected by Azure AI Search indexes, following the schema defined
    in GPT-RAG (https://github.com/Azure/GPT-RAG/blob/main/config/search/search.j2).
    
    The executor processes content items and creates search documents from chunks or
    full content, populating required fields like id, content, title, metadata, etc.
    
    Configuration (settings dict):
        - use_chunks (bool): Create separate search documents for each chunk
          Default: True
          If True, each chunk in content.data.chunks becomes a separate search document
          If False, creates a single document from content.data.markdown or combined content
          Also processes Azure Document Intelligence pages if available
        
        - chunk_field (str): Field path to chunks array in content.data
          Default: "chunks"
          Used to locate chunks when use_chunks is True
        
        - doc_intell_field (str): Field path to Document Intelligence output
          Default: "doc_intell_output"
          Used to detect and process Azure Document Intelligence results
        
        - content_field (str): Field path to content text in content.data
          Default: "markdown"
          Used to get full content text when use_chunks is False
        
        - extract_title (bool): Extract title from markdown/content
          Default: True
          Extracts first heading (# Title) as document title
        
        - title_field (str): Field path to pre-extracted title in content.data
          Default: None
          If provided, uses this field instead of extracting from markdown
        
        - category_field (str): Field path to category in content metadata
          Default: None
          If provided, extracts category from this field
        
        - default_category (str): Default category for documents without category
          Default: "document"
        
        - include_summary (bool): Include content summary in search document
          Default: True
          Extracts from content_understanding_result.contents[0].fields.Summary if available
        
        - generate_id (bool): Auto-generate document IDs
          Default: True
          If True, generates IDs from source path and chunk index
          If False, uses pre-existing IDs in content
        
        - id_prefix (str): Prefix for generated document IDs
          Default: None
          Example: "doc-" results in "doc-sha256hash"
        
        - parent_id_field (str): Field path for parent document ID
          Default: None
          If provided and use_chunks is True, creates parent_id linking chunks
        
        - include_page_metadata (bool): Include page number and offset in output
          Default: True
          Adds page, offset, and length fields for precise document location
        
        - include_storage_metadata (bool): Include Azure storage metadata
          Default: True
          Adds metadata_storage_path, metadata_storage_name, etc.
        
        - include_source_metadata (bool): Include original source information
          Default: True
          Adds source, filepath, and other source identification fields
        
        - extract_images (bool): Extract image captions (if available)
          Default: False
          Extracts imageCaptions field if present in content analysis
        
        - max_title_length (int): Maximum length for extracted title
          Default: 500
        
        - output_mode (str): Format of output documents
          Default: "list"
          Options:
            - "list": Returns list of search documents in output
            - "nested": Keeps documents nested in content.data.search_documents
        
        - add_output_metadata (bool): Add metadata about index preparation
          Default: False
          When True, adds summary_data about document preparation
        
        Also settings from ParallelExecutor and BaseExecutor apply.
    
    Example:
        ```python
        # Create search documents from chunks
        executor = GPTRAGSearchIndexDocumentGenerator(
            id="gpt_rag_search_index_document_generator",
            settings={
                "use_chunks": True,
                "extract_title": True,
                "default_category": "document",
                "include_summary": True,
                "include_storage_metadata": True,
                "id_prefix": "doc-"
            }
        )
        
        # Create single document from full content
        executor = GPTRAGSearchIndexDocumentGenerator(
            id="gpt_rag_search_index_document_generator_full",
            settings={
                "use_chunks": False,
                "content_field": "markdown",
                "extract_title": True,
                "title_field": None,
                "include_page_metadata": False
            }
        )
        
        # Advanced configuration with parent IDs
        executor = GPTRAGSearchIndexDocumentGenerator(
            id="gpt_rag_search_index_document_generator_advanced",
            settings={
                "use_chunks": True,
                "parent_id_field": "canonical_id",
                "include_summary": True,
                "extract_images": True,
                "add_output_metadata": True
            }
        )
        ```
    
    Input:
        Content items with extracted document data, markdown, and chunks
        
    Output:
        List of Azure AI Search document objects ready for indexing
        Each document contains fields: id, content, title, metadata, chunk_id, etc.
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
        
        # Chunk processing configuration
        self.use_chunks = self.get_setting("use_chunks", default=True)
        self.chunk_field = self.get_setting("chunk_field", default="chunks")
        self.doc_intell_field = self.get_setting("doc_intell_field", default="doc_intell_output")
        self.content_field = self.get_setting("content_field", default="markdown")
        
        # Title and metadata extraction
        self.extract_title = self.get_setting("extract_title", default=True)
        self.title_field = self.get_setting("title_field", default=None)
        self.category_field = self.get_setting("category_field", default=None)
        self.default_category = self.get_setting("default_category", default="document")
        self.max_title_length = self.get_setting("max_title_length", default=500)
        
        # Summary and content configuration
        self.include_summary = self.get_setting("include_summary", default=True)
        
        # ID generation
        self.generate_id = self.get_setting("generate_id", default=True)
        self.id_prefix = self.get_setting("id_prefix", default=None)
        self.parent_id_field = self.get_setting("parent_id_field", default=None)
        
        # Metadata inclusion
        self.include_page_metadata = self.get_setting("include_page_metadata", default=True)
        self.include_storage_metadata = self.get_setting("include_storage_metadata", default=True)
        self.include_source_metadata = self.get_setting("include_source_metadata", default=True)
        self.extract_images = self.get_setting("extract_images", default=False)
        
        # Output configuration
        self.output_field = self.get_setting("output_field", default="search_documents")
        self.output_mode = self.get_setting("output_mode", default="list")
        if self.output_mode not in ["list", "nested"]:
            raise ValueError("'output_mode' must be 'list' or 'nested'")
        
        self.add_output_metadata = self.get_setting("add_output_metadata", default=False)
        
        if self.debug_mode:
            logger.debug(
                f"GPTRAGSearchIndexDocumentGeneratorExecutor '{self.id}' initialized with settings: "
                f"use_chunks={self.use_chunks}, "
                f"extract_title={self.extract_title}, "
                f"include_summary={self.include_summary}, "
                f"output_mode={self.output_mode}"
            )
    
    async def process_content_item(
        self,
        content: Content
    ) -> Content:
        """
        Transform content item into Azure AI Search documents.
        Implements ParallelExecutor abstract method.
        
        Args:
            content: Content item to process
            
        Returns:
            Content item with search documents generated
        """
        if not content:
            logger.warning(f"No content provided to {self.id}")
            return content
        
        logger.debug(
            f"{self.id}: Preparing content for Azure AI Search indexing: "
            f"use_chunks={self.use_chunks}"
        )
        
        try:
            # Generate GPT RAG search index documents from content
            search_documents = self._generate_search_documents(content)
            
            if self.debug_mode:
                logger.debug(f"{self.id}: Generated {len(search_documents)} search documents")
            
            # Store documents in content item
            content.data[self.output_field] = search_documents
            
            # Add metadata if requested
            if self.add_output_metadata:
                if not hasattr(content, 'summary_data'):
                    content.summary_data = {}
                content.summary_data['gptrag_search_index_documents'] = {
                    'documents_generated': len(search_documents),
                    'use_chunks': self.use_chunks,
                    'timestamp': datetime.now().isoformat()
                }
            
            logger.debug(
                f"{self.id}: Successfully prepared {len(search_documents)} documents for indexing"
            )
            
        except Exception as e:
            logger.error(f"{self.id}: Failed to prepare content for search indexing: {e}", exc_info=True)
            raise
        
        return content
    
    def _generate_search_documents(self, content: Content) -> List[Dict[str, Any]]:
        """
        Generate Azure AI Search documents from content item.
        
        Args:
            content: Content item with extracted data
            
        Returns:
            List of search document objects
        """
        documents = []
        
        # Detect input type and process accordingly
        # Check for Document Intelligence output first
        if self.doc_intell_field not in [None, ""] and self.doc_intell_field in content.data:
            doc_intell_output = self._get_nested_value(content.data, self.doc_intell_field)
            if doc_intell_output and isinstance(doc_intell_output, dict):
                # Process Document Intelligence pages
                documents = self._generate_from_doc_intell_output(content)
        
        # Check for Content Understanding output if no Document Intelligence output
        elif self.cu_field not in [None, ""] and self.cu_field in content.data:
            cu_output = self._get_nested_value(content.data, self.cu_field)
            if cu_output and isinstance(cu_output, dict):
                # Process Content Understanding chunks
                documents = self._generate_from_chunks(content)
        
        # Check for python library output (specilized executors)
        
        
        else:
            # Create single document from full content
            documents = self._generate_from_full_content(content)
        
        return documents
    
    def _generate_from_doc_intell_output(self, content: Content) -> List[Dict[str, Any]]:
        """
        Generate search documents from Azure Document Intelligence output.
        
        Args:
            content: Content item with Document Intelligence results
            
        Returns:
            List of search documents
        """
        documents = []
        
        # Get Document Intelligence output
        doc_intell_output = self._get_nested_value(content.data, self.doc_intell_field)
        if not doc_intell_output or not isinstance(doc_intell_output, dict):
            logger.warning(f"No Document Intelligence output found at '{self.doc_intell_field}'")
            return []
        
        # Get parent ID if configured
        parent_id = None
        if self.parent_id_field:
            parent_id = self._get_nested_value(content.data, self.parent_id_field)
        if parent_id is None and content.id:
            parent_id = content.id.unique_id
        
         # Extract title once for all pages
        title = self._extract_title(content)
        category = self._extract_category(content)
        summary = self._extract_summary(content) if self.include_summary else None
        
        # Get pages from Document Intelligence output
        pages = doc_intell_output.get("pages", [])
        
        # Check if all pages are empty, this indicates file types like docx, pptx, xlsx where doc-intell may not extract page text
        all_pages_empty = all(not page.get("text", "").strip() for page in pages if isinstance(page, dict))
        if not all_pages_empty:
            logger.debug("Will use Document Intelligence pages for search document generation")
            # Create document for each page
            for page in pages:
                try:
                    if not isinstance(page, dict):
                        logger.warning(f"Skipping non-dict page: {page}")
                        continue
                    
                    page_number = page.get("page_number", 0)
                    page_text = page.get("text", "")
                    
                    # Skip empty pages
                    if not page_text or not page_text.strip():
                        if self.debug_mode:
                            logger.debug(f"Skipping empty page {page_number}")
                        continue
                    
                    doc = self._create_search_document(
                        content=content,
                        chunk={
                            "content": page_text,
                            "page_number": page_number,
                            "width": page.get("width"),
                            "height": page.get("height"),
                            "unit": page.get("unit"),
                        },
                        chunk_index=page_number,
                        parent_id=parent_id,
                        title=title,
                        category=category,
                        summary=summary
                    )
                    documents.append(doc)
                    
                except Exception as e:
                    logger.error(
                        f"{self.id}: Failed to create search document for page {page.get('page_number', '?')}: {e}",
                        exc_info=True
                    )
                    if self.fail_pipeline_on_error:
                        raise
                    continue
        
        # Fall back to full text if no valid pages
        if not pages or all_pages_empty:
            logger.debug(f"{self.id}: No pages found in Document Intelligence output")
            # Fall back to full text
            full_text = doc_intell_output.get("text")
            if full_text and full_text.strip():
                return self._generate_from_full_content(content, full_text)
            return []
        
        return documents
    
    def _generate_from_chunks(self, content: Content) -> List[Dict[str, Any]]:
        """
        Generate search documents from content chunks.
        
        Args:
            content: Content item
            
        Returns:
            List of search documents
        """
        documents = []
        
        # Get chunks from content
        chunks = self._get_nested_value(content.data, self.chunk_field)
        if not chunks or not isinstance(chunks, list):
            logger.warning(f"No chunks found at '{self.chunk_field}', creating from full content")
            return self._generate_from_full_content(content)
        
        # Get parent ID if configured
        parent_id = None
        if self.parent_id_field:
            parent_id = self._get_nested_value(content.data, self.parent_id_field)
            if parent_id is None and content.id:
                parent_id = content.id.canonical_id
        
        # Extract title once for all chunks
        title = self._extract_title(content)
        category = self._extract_category(content)
        summary = self._extract_summary(content) if self.include_summary else None
        
        # Create document for each chunk
        for chunk_index, chunk in enumerate(chunks):
            try:
                doc = self._create_search_document(
                    content=content,
                    chunk=chunk,
                    chunk_index=chunk_index,
                    parent_id=parent_id,
                    title=title, # get title per chunk
                    category=category,
                    summary="" # summary per chunk not supported
                )
                documents.append(doc)
                
            except Exception as e:
                logger.error(
                    f"{self.id}: Failed to create search document for chunk {chunk_index}: {e}",
                    exc_info=True
                )
                if self.fail_pipeline_on_error:
                    raise
                continue
        
        return documents
    
    def _generate_from_full_content(self, content: Content, text: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Generate single search document from full content.
        
        Args:
            content: Content item
            
        Returns:
            List with single search document
        """
        
        # Get full content text
        content_text = text or self._get_nested_value(content.data, self.content_field)
        if not content_text:
            logger.warning(f"No content found at '{self.content_field}'")
            return []
        
        # Extract metadata
        title = self._extract_title(content)
        category = self._extract_category(content)
        summary = self._extract_summary(content) if self.include_summary else None
        
        # Create single document
        doc = self._create_search_document(
            content=content,
            chunk={
                "content": content_text,
                "chunk_index": 0,
                "metadata": {}
            },
            chunk_index=0,
            parent_id=None,
            title=title,
            category=category,
            summary=summary
        )
        
        return [doc]
    
    def _create_search_document(
        self,
        content: Content,
        chunk: Dict[str, Any],
        chunk_index: int,
        parent_id: Optional[str] = None,
        title: Optional[str] = None,
        category: Optional[str] = None,
        summary: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a single Azure AI Search document.
        
        Args:
            content: Source content item
            chunk: Chunk data
            chunk_index: Index of chunk
            parent_id: Parent document ID
            title: Document title
            category: Document category
            summary: Document summary
            
        Returns:
            Search document object
        """
        # Generate document ID
        doc_id = self._generate_document_id(content, chunk_index)
        
        # Extract content from chunk
        chunk_content = chunk.get("content", "") if isinstance(chunk, dict) else str(chunk)
        
        # Build base document
        doc = {
            "id": doc_id,
            "content": chunk_content,
            "title": title or self.default_category,
            "category": category or self.default_category,
        }
        
        # Add parent ID if provided
        if parent_id:
            doc["parent_id"] = parent_id
        
        # Add summary
        if summary:
            doc["summary"] = summary
        
        # Add page and offset metadata
        if isinstance(chunk, dict):
            chunk_metadata = chunk.get("metadata", {})
            if "page_number" in chunk_metadata:
                doc["page"] = chunk_metadata["page_number"]
            
            # Calculate offset (character position of chunk content in full text)
            if "offset" in chunk_metadata:
                doc["offset"] = chunk_metadata["offset"]
            
            # Add content length
            doc["length"] = len(chunk_content)
        
        # Add storage metadata
        if content.id:
            doc["metadata_storage_path"] = content.id.canonical_id or ""
            doc["metadata_storage_name"] = content.id.filename or ""
            
            if hasattr(content.id, "metadata") and content.id.metadata:
                if "last_modified" in content.id.metadata:
                    doc["metadata_storage_last_modified"] = content.id.metadata["last_modified"]
        
            # Add source metadata
            doc["source"] = content.id.source_name or "unknown"
            doc["filepath"] = content.id.path or ""
            doc["url"] = content.id.canonical_id or ""
        
        # Add chunk ID
        doc["chunk_id"] = chunk_index
        
        return doc
    
    def _generate_document_id(self, content: Content, chunk_index: int) -> str:
        """
        Generate unique document ID.
        
        Args:
            content: Content item
            chunk_index: Chunk index
            
        Returns:
            Document ID string
        """
        
        # Generate ID from content path and chunk index
        base = ""
        if content.id:
            if content.id.canonical_id:
                base = content.id.canonical_id
            elif content.id.path:
                base = content.id.path
        
        if not base:
            base = "document"
        
        # Create hash-based ID
        id_source = f"{base}-{chunk_index}"
        doc_id = hashlib.sha256(id_source.encode()).hexdigest()
        
        if self.id_prefix:
            doc_id = f"{self.id_prefix}{doc_id}"
        
        return doc_id
    
    def _extract_title(self, content: Content) -> Optional[str]:
        """
        Extract document title from content.
        
        Args:
            content: Content item
            
        Returns:
            Title string or None
        """
        # Try to get from configured title field
        if self.title_field:
            title = self._get_nested_value(content.data, self.title_field)
            if title:
                return str(title)[:self.max_title_length]
        
        # Try to extract from markdown
        if self.extract_title:
            content_text = self._get_nested_value(content.data, self.content_field)
            if content_text:
                # Extract first heading
                lines = str(content_text).split('\n')
                for line in lines:
                    line = line.strip()
                    if line.startswith('# '):
                        title = line[2:].strip()
                        return title[:self.max_title_length]
        
        # Use filename if available
        if content.id and content.id.filename:
            return content.id.filename[:self.max_title_length]
        
        return None
    
    def _extract_category(self, content: Content) -> Optional[str]:
        """
        Extract document category from content.
        
        Args:
            content: Content item
            
        Returns:
            Category string
        """
        if self.category_field:
            category = self._get_nested_value(content.data, self.category_field)
            if category:
                return str(category)
        
        # Try to get from summary_data
        if hasattr(content, 'summary_data') and content.summary_data:
            if "chunking_method" in content.summary_data:
                return content.summary_data["chunking_method"]
        
        return self.default_category
    
    def _extract_summary(self, content: Content) -> Optional[str]:
        """
        Extract document summary from content analysis results.
        
        Args:
            content: Content item
            
        Returns:
            Summary string or None
        """
        # Try to get from content understanding results
        content_understanding = self._get_nested_value(
            content.data,
            "content_understanding_result"
        )
        
        if content_understanding and isinstance(content_understanding, dict):
            result = content_understanding.get("result", {})
            contents = result.get("contents", [])
            
            if contents and isinstance(contents, list):
                first_content = contents[0]
                if isinstance(first_content, dict):
                    fields = first_content.get("fields", {})
                    if "Summary" in fields:
                        summary_obj = fields["Summary"]
                        if isinstance(summary_obj, dict):
                            return summary_obj.get("valueString")
        
        # Try summary_data
        if hasattr(content, 'summary_data') and content.summary_data:
            if "extraction_status" in content.summary_data:
                # Could build summary from extraction metadata
                pass
        
        return None
    
    def _get_nested_value(self, data: Dict[str, Any], path: str) -> Any:
        """
        Get value from nested dictionary using dot notation path.
        
        Args:
            data: Dictionary to search
            path: Dot-notation path (e.g., "user.profile.name")
            
        Returns:
            Value at path, or None if not found
        """
        if not path or not data:
            return None
        
        keys = path.split('.')
        current = data
        
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return None
        
        return current
