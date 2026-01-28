"""Search indexer executor for transforming content into Azure AI Search document format."""

import logging
import json
import hashlib
import re
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
        
        - chunk_field (str): Field path to chunks array in content.data
          Default: "chunks"
          Used to locate chunks when use_chunks is True
        
        - content_field (str): Field path to content text in content.data
          Default: "markdown"
          Used to get full content text when use_chunks is False
          
        - max_chunk_size (int): Maximum size in bytes for chunk content
          Default: 32766
          Truncates chunk content exceeding this size to fit Azure AI Search limits
        
        - extract_title (bool): Extract title from markdown/content
          Default: True
          Extracts first heading (# Title) as document title
        
        - title_field (str): Field path to pre-extracted title in content.data
          Default: None
          If provided, uses this field instead of extracting from markdown
          
        - max_title_length (int): Maximum length for extracted title
          Default: 50
        
        - category_field (str): Field path to category in content.data
          Default: None
          If provided, extracts category from this field
        
        - default_category (str): Default category for documents without category
          Default: None
        
        - summary_field (str): Field path to summary in content.data
          Default: "summary"
          If provided, uses this field to populate document summary
        
        - id_prefix (str): Prefix for generated document IDs
          Default: None
          Example: "doc-" results in "doc-sha256hash"
        
        - parent_id_field (str): Field path for parent document ID
          Default: None
          If provided and use_chunks is True, creates parent_id linking chunks
        
        - url_field (str): Field path for source URL in content.data
          Default: None
          If provided, uses this field to populate document URL
          
        - source_value (str): Static source value for all documents
          Default: None
          If provided, uses this value for the source field in documents
        
        - related_images_field (str): Field path for related images in content.data
          Default: None
          If provided, extracts related images metadata for documents
        
        - related_files_field (str): Field path for related files in content.data
          Default: None
          If provided, extracts related files metadata for documents

        - output_field (str): Field in content.data to store generated documents
          Default: "search_documents"
          The generated Azure AI Search documents will be stored here
        
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
                "summary_field": "summary",
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
                "summary_field": "summary",
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
        self.chunk_field = self.get_setting("chunk_field", default="chunks")
        self.content_field = self.get_setting("content_field", default="text")
        self.max_chunk_size = self.get_setting("max_chunk_size", default=32766)
        
        # Title and metadata extraction
        self.extract_title = self.get_setting("extract_title", default=True)
        self.title_field = self.get_setting("title_field", default=None)
        self.max_title_length = self.get_setting("max_title_length", default=50)
        self.category_field = self.get_setting("category_field", default=None)
        self.default_category = self.get_setting("default_category", default=None)
                        
        # Summary and content configuration
        self.summary_field = self.get_setting("summary_field", default="summary")
        self.source_value = self.get_setting("source_value", default=None)
        self.related_images_field = self.get_setting("related_images_field", default=None)
        self.related_files_field = self.get_setting("related_files_field", default=None)
        
        # ID generation
        self.id_prefix = self.get_setting("id_prefix", default=None)
        self.parent_id_field = self.get_setting("parent_id_field", default=None)
        self.url_field = self.get_setting("url_field", default=None)
        
        # Output configuration
        self.output_field = self.get_setting("output_field", default="search_documents")
        self.add_output_metadata = self.get_setting("add_output_metadata", default=False)
        
        if self.debug_mode:
            logger.debug(
                f"GPTRAGSearchIndexDocumentGeneratorExecutor '{self.id}' initialized with settings: "
                f"chunk_field={self.chunk_field}, "
                f"content_field={self.content_field}, "
                f"output_field={self.output_field}, ..."
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
            f"chunk_field={self.chunk_field}"
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
        
        # Get chunks from content
        if self.chunk_field not in [None, ""] and self.chunk_field in content.data:
            chunks = self._get_nested_value(content.data, self.chunk_field)
            if not chunks or not isinstance(chunks, list):
                logger.warning(f"No chunks found at '{self.chunk_field}', creating from full content")
                return self._generate_from_full_content(content)
        else:
            return self._generate_from_full_content(content)
        
        # Get parent ID if configured
        parent_id = None
        if self.parent_id_field:
            parent_id = self._get_nested_value(content.data, self.parent_id_field)
            if parent_id is None and content.id:
                parent_id = f"/{content.id.container}/{content.id.path}"
        
        
        # Create document for each chunk
        for chunk_index, chunk in enumerate(chunks):
            try:
                # Extract content from chunk
                chunk_content = chunk.get(self.content_field, "") if isinstance(chunk, dict) else ""
                if len(chunk_content.encode('utf-8')) > self.max_chunk_size:
                    logger.warning(
                        f"Chunk content size exceeds max_chunk_size ({self.max_chunk_size} bytes), truncating"
                    )
                encoded = chunk_content.encode('utf-8')[:self.max_chunk_size]
                chunk_content = encoded.decode('utf-8', errors='ignore')
                
                chunk[self.content_field] = chunk_content
                
                doc = self._create_search_document(
                    content=content,
                    chunk=chunk,
                    chunk_index=chunk_index,
                    parent_id=parent_id
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
    
    def _generate_from_full_content(self, content: Content) -> List[Dict[str, Any]]:
        """
        Generate single search document from full content.
        
        Args:
            content: Content item
            
        Returns:
            List with single search document
        """
        
        # Get full content text
        content_text = self._get_nested_value(content.data, self.content_field)
        if not content_text:
            logger.warning(f"No content found at '{self.content_field}'")
            content_text = ""
            
        # Truncate content if exceeds max chunk size
        if len(content_text.encode('utf-8')) > self.max_chunk_size:
            logger.warning(
                f"Content size exceeds max_chunk_size ({self.max_chunk_size} bytes), truncating"
            )
            encoded = content_text.encode('utf-8')[:self.max_chunk_size]
            content_text = encoded.decode('utf-8', errors='ignore')
        
        # Create single document
        doc = self._create_search_document(
            content=content,
            chunk={
                self.content_field: content_text,
                "chunk_index": 0,
            },
            chunk_index=0,
            parent_id=None
        )
        
        return [doc]
    
    def _create_search_document(
        self,
        content: Content,
        chunk: Dict[str, Any],
        chunk_index: int,
        parent_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a single Azure AI Search document.
        
        Args:
            content: Source content item
            chunk: Chunk data
            chunk_index: Index of chunk
            
        Returns:
            Search document object
        """
        
        # Get parent ID if configured
        parent_id = None
        if self.parent_id_field:
            parent_id = self._get_nested_value(content.data, self.parent_id_field)
        parent_id = parent_id or (f"/{content.id.container}/{content.id.path}" if content.id else None)

        # Extract URL if configured
        url = None
        if self.url_field:
            url = self._get_nested_value(content.data, self.url_field)
        url = url or (content.id.canonical_id if content.id else None)

        related_images = []
        if self.related_images_field:
            if chunk and isinstance(chunk, dict):
                related_images = chunk.get("related_images", [])
            if not related_images:
                related_images = self._get_nested_value(content.data, self.related_images_field) or []
        
        related_files = []
        if self.related_files_field:
            if chunk and isinstance(chunk, dict):
                related_files = chunk.get("related_files", [])
            if not related_files:
                related_files = self._get_nested_value(content.data, self.related_files_field) or []
        
        # Extract title once for all chunks
        title = self._extract_title(content)
        category = self._extract_category(content)
        summary = self._extract_summary(content)
        # Generate document ID
        doc_id = self._generate_document_id(content, chunk_index)
        
        chunk_content = chunk.get(self.content_field, "") if isinstance(chunk, dict) else ""
        
        # Build base document
        doc = {
            "id": doc_id,
            "parent_id": parent_id or "",
            "metadata_storage_path": (f"/{content.id.container}/{content.id.path}" if content.id else ""),
            "metadata_storage_name": content.id.filename if (content.id and content.id.filename) else "",
            "metadata_storage_last_modified": content.id.metadata["last_modified"] if (content.id and hasattr(content.id, "metadata") and content.id.metadata and "last_modified" in content.id.metadata) else "",
            "metadata_security_group_ids": [],
            "metadata_security_user_ids": [],
            "metadata_security_rbac_scope": [],
            "chunk_id": chunk_index,
            "content": chunk_content or "",
            "imageCaptions": "",
            "page": chunk.get("page_number", 0) if isinstance(chunk, dict) else 0,
            "offset": chunk.get("offset", 0) if isinstance(chunk, dict) else 0,
            "length": len(chunk_content),
            "title": title or "",
            "category": category or self.default_category or "",
            "filepath": (f"/{content.id.container}/{content.id.path}" if content.id else ""),
            "url": url or "",
            "summary": summary or "",
            "relatedImages": related_images,
            "relatedFiles": related_files,
            "source": self.source_value or (content.id.source_type if content.id else ""),
        }
        
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
            base = "doc"
        
        base = self._sanitize_key_part(base)
        
        if len(base) > 128:
            digest = hashlib.sha256(base.encode()).hexdigest()
            base = f"{base[:64]}-{digest}"
        
        doc_id = f"{base}-c{chunk_index:05d}"
        
        if self.id_prefix:
            doc_id = f"{self.id_prefix}{doc_id}"
        
        return doc_id
    
    def _sanitize_key_part(self, s: str) -> str:
        """
        Sanitize a string for use in an Azure AI Search key:
        keep only [A-Za-z0-9_-]; replace others (including '.') with '-'; collapse repeats; trim.
        """
        # Replace disallowed chars (including '.') with '-'
        s = re.sub(r"[^A-Za-z0-9_-]+", "-", s)
        # Collapse multiple '-'
        s = re.sub(r"-+", "-", s)
        # Trim leading/trailing '-'
        return s.strip('-')
    
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
            return content.id.filename.split('.')[0][:self.max_title_length]
        
        return None
    
    def _extract_category(self, content: Content) -> Optional[str]:
        """
        Extract document category from content.
        
        Args:
            content: Content item
            
        Returns:
            Category string or None
        """
        if self.category_field:
            category = self._get_nested_value(content.data, self.category_field)
            if category:
                return str(category)
        
        return None
    
    def _extract_summary(self, content: Content) -> Optional[str]:
        """
        Extract document summary from content analysis results.
        
        Args:
            content: Content item
            
        Returns:
            Summary string or None
        """
        if self.summary_field:
            summary = self._get_nested_value(content.data, self.summary_field)
            if summary:
                return str(summary)
        
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
