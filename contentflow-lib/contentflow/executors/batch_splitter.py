"""
Document batch splitting executors.

This module provides executors that split documents or data into batches
for parallel processing.
"""

import logging
from typing import Any, Dict, List, Optional

from agent_framework import WorkflowContext

from .base import DocumentExecutor

try:
    from doc.proc.models import Document
except ImportError as e:
    raise ImportError(f"Failed to import doc-proc-lib models: {e}")

logger = logging.getLogger("doc_proc_workflow.executors.batch_splitter")


class DocumentSplitter(DocumentExecutor):
    """
    Split large documents into chunks for parallel processing.
    
    Splits documents by pages, characters, words, or lines to enable
    parallel processing of large documents.
    
    Configuration:
        chunk_size (int): Size of each chunk (default: 10)
        split_strategy (str): "pages", "characters", "words", "lines" (default: "pages")
        content_key (str): Key in document.data containing content (default: "content")
        overlap (int): Number of units to overlap between chunks (default: 0)
    
    Example:
        ```yaml
        - id: splitter
          type: document_splitter
          settings:
            chunk_size: 10
            split_strategy: pages
            overlap: 1
        ```
    """
    
    def __init__(self, settings: Dict[str, Any] = None, **kwargs):
        super().__init__(id=kwargs.get("id", "document_splitter"), settings=settings)
        
        self.chunk_size = self.get_setting("chunk_size", default=10)
        self.split_strategy = self.get_setting("split_strategy", default="pages")
        self.content_key = self.get_setting("content_key", default="content")
        self.overlap = self.get_setting("overlap", default=0)
        
        logger.info(
            f"Initialized DocumentSplitter: strategy={self.split_strategy}, "
            f"chunk_size={self.chunk_size}, overlap={self.overlap}"
        )
    
    async def process_document(
        self,
        document: Document,
        ctx: WorkflowContext
    ) -> Document:
        """
        Split document into chunks.
        
        Args:
            document: Document to split
            ctx: Workflow context
            
        Returns:
            Document with chunks stored in data['chunks']
        """
        content = document.data.get(self.content_key)
        
        if content is None:
            logger.warning(f"No content found at key '{self.content_key}' in document {document.id}")
            document.data["chunks"] = []
            document.data["total_chunks"] = 0
            return document
        
        # Split content based on strategy
        chunks = self._split_content(content, document)
        
        # Store chunks in document
        document.data["chunks"] = chunks
        document.data["total_chunks"] = len(chunks)
        document.summary_data["split_strategy"] = self.split_strategy
        document.summary_data["chunk_size"] = self.chunk_size
        document.summary_data["total_chunks"] = len(chunks)
        document.summary_data["overlap"] = self.overlap
        
        logger.info(
            f"Split document {document.id} into {len(chunks)} chunks "
            f"using {self.split_strategy} strategy"
        )
        
        return document
    
    def _split_content(
        self,
        content: Any,
        document: Document
    ) -> List[Dict[str, Any]]:
        """Split content based on the configured strategy."""
        if self.split_strategy == "pages":
            return self._split_by_pages(content, document)
        elif self.split_strategy == "characters":
            return self._split_by_characters(str(content), document)
        elif self.split_strategy == "words":
            return self._split_by_words(str(content), document)
        elif self.split_strategy == "lines":
            return self._split_by_lines(str(content), document)
        else:
            raise ValueError(f"Unknown split strategy: {self.split_strategy}")
    
    def _split_by_pages(
        self,
        content: Any,
        document: Document
    ) -> List[Dict[str, Any]]:
        """Split content by pages."""
        chunks = []
        
        # If content is a list (e.g., list of pages), split that
        if isinstance(content, list):
            pages = content
        # If content is string, split by page markers
        elif isinstance(content, str):
            if "\f" in content:
                pages = content.split("\f")
            elif "\\page" in content:
                pages = content.split("\\page")
            else:
                # Use character count as proxy (3000 chars ≈ 1 page)
                chars_per_page = 3000
                pages = [content[i:i + chars_per_page] 
                        for i in range(0, len(content), chars_per_page)]
        else:
            pages = [str(content)]
        
        # Group pages into chunks with overlap
        chunk_idx = 0
        i = 0
        while i < len(pages):
            end_idx = min(i + self.chunk_size, len(pages))
            chunk_pages = pages[i:end_idx]
            
            chunks.append({
                "chunk_id": f"{document.id}_chunk_{chunk_idx}",
                "content": chunk_pages if isinstance(content, list) else "\f".join(chunk_pages),
                "start_page": i + 1,
                "end_page": end_idx,
                "total_pages": len(chunk_pages),
                "chunk_index": chunk_idx
            })
            
            # Move to next chunk, accounting for overlap
            i += self.chunk_size - self.overlap
            chunk_idx += 1
        
        return chunks
    
    def _split_by_characters(
        self,
        content: str,
        document: Document
    ) -> List[Dict[str, Any]]:
        """Split content by character count."""
        chunks = []
        chunk_idx = 0
        i = 0
        
        while i < len(content):
            end_idx = min(i + self.chunk_size, len(content))
            chunk_content = content[i:end_idx]
            
            chunks.append({
                "chunk_id": f"{document.id}_chunk_{chunk_idx}",
                "content": chunk_content,
                "start_char": i,
                "end_char": end_idx,
                "char_count": len(chunk_content),
                "chunk_index": chunk_idx
            })
            
            i += self.chunk_size - self.overlap
            chunk_idx += 1
        
        return chunks
    
    def _split_by_words(
        self,
        content: str,
        document: Document
    ) -> List[Dict[str, Any]]:
        """Split content by word count."""
        words = content.split()
        chunks = []
        chunk_idx = 0
        i = 0
        
        while i < len(words):
            end_idx = min(i + self.chunk_size, len(words))
            chunk_words = words[i:end_idx]
            
            chunks.append({
                "chunk_id": f"{document.id}_chunk_{chunk_idx}",
                "content": " ".join(chunk_words),
                "start_word": i,
                "end_word": end_idx,
                "word_count": len(chunk_words),
                "chunk_index": chunk_idx
            })
            
            i += self.chunk_size - self.overlap
            chunk_idx += 1
        
        return chunks
    
    def _split_by_lines(
        self,
        content: str,
        document: Document
    ) -> List[Dict[str, Any]]:
        """Split content by line count."""
        lines = content.split("\n")
        chunks = []
        chunk_idx = 0
        i = 0
        
        while i < len(lines):
            end_idx = min(i + self.chunk_size, len(lines))
            chunk_lines = lines[i:end_idx]
            
            chunks.append({
                "chunk_id": f"{document.id}_chunk_{chunk_idx}",
                "content": "\n".join(chunk_lines),
                "start_line": i + 1,
                "end_line": end_idx,
                "line_count": len(chunk_lines),
                "chunk_index": chunk_idx
            })
            
            i += self.chunk_size - self.overlap
            chunk_idx += 1
        
        return chunks


class BatchDocumentSplitter(DocumentExecutor):
    """
    Split a batch of documents into smaller batches.
    
    Takes a document containing a list of documents and splits them
    into batches for controlled parallel processing.
    
    Configuration:
        batch_size (int): Number of documents per batch (default: 10)
        documents_key (str): Key in document.data containing document list (default: "documents")
    
    Example:
        ```yaml
        - id: batch_splitter
          type: batch_document_splitter
          settings:
            batch_size: 50
        ```
    """
    
    def __init__(self, settings: Dict[str, Any] = None, **kwargs):
        super().__init__(id=kwargs.get("id", "batch_document_splitter"), settings=settings)
        
        self.batch_size = self.get_setting("batch_size", default=10)
        self.documents_key = self.get_setting("documents_key", default="documents")
        
        logger.info(f"Initialized BatchDocumentSplitter: batch_size={self.batch_size}")
    
    async def process_document(
        self,
        document: Document,
        ctx: WorkflowContext
    ) -> Document:
        """
        Split document list into batches.
        
        Args:
            document: Document containing list of documents
            ctx: Workflow context
            
        Returns:
            Document with batches stored in data['batches']
        """
        documents = document.data.get(self.documents_key, [])
        
        if not documents:
            logger.warning(f"No documents found at key '{self.documents_key}' in {document.id}")
            document.data["batches"] = []
            document.data["total_batches"] = 0
            return document
        
        # Split into batches
        batches = []
        for i in range(0, len(documents), self.batch_size):
            batch = documents[i:i + self.batch_size]
            batches.append({
                "batch_id": f"{document.id}_batch_{i // self.batch_size}",
                "documents": batch,
                "batch_index": i // self.batch_size,
                "start_index": i,
                "end_index": min(i + self.batch_size, len(documents)),
                "document_count": len(batch)
            })
        
        document.data["batches"] = batches
        document.data["total_batches"] = len(batches)
        document.summary_data["batch_size"] = self.batch_size
        document.summary_data["total_documents"] = len(documents)
        document.summary_data["total_batches"] = len(batches)
        
        logger.info(
            f"Split {len(documents)} documents into {len(batches)} batches "
            f"of size {self.batch_size}"
        )
        
        return document


class TableRowSplitter(DocumentExecutor):
    """
    Split tabular data (Excel, CSV, DataFrame) into rows for parallel processing.
    
    Extracts rows from tabular data and creates individual row records
    that can be processed in parallel.
    
    Configuration:
        table_key (str): Key in document.data containing table data (default: "table_data")
        row_id_field (str): Field to use as row ID (default: uses index)
        max_rows (int): Maximum rows to process (default: None = all)
    
    Example:
        ```yaml
        - id: row_splitter
          type: table_row_splitter
          settings:
            table_key: excel_data
            row_id_field: customer_id
        ```
    """
    
    def __init__(self, settings: Dict[str, Any] = None, **kwargs):
        super().__init__(id=kwargs.get("id", "table_row_splitter"), settings=settings)
        
        self.table_key = self.get_setting("table_key", default="table_data")
        self.row_id_field = self.get_setting("row_id_field", default=None)
        self.max_rows = self.get_setting("max_rows", default=None)
        
        logger.info(f"Initialized TableRowSplitter: table_key={self.table_key}")
    
    async def process_document(
        self,
        document: Document,
        ctx: WorkflowContext
    ) -> Document:
        """
        Split table into rows.
        
        Args:
            document: Document containing table data
            ctx: Workflow context
            
        Returns:
            Document with rows stored in data['rows']
        """
        table_data = document.data.get(self.table_key, [])
        
        if not table_data:
            logger.warning(f"No table data found at key '{self.table_key}' in {document.id}")
            document.data["rows"] = []
            document.data["total_rows"] = 0
            return document
        
        # Apply max_rows limit if specified
        if self.max_rows:
            table_data = table_data[:self.max_rows]
        
        # Create row records
        rows = []
        for idx, row_data in enumerate(table_data):
            # Determine row ID
            if self.row_id_field and isinstance(row_data, dict):
                row_id = row_data.get(self.row_id_field, f"row_{idx}")
            else:
                row_id = f"row_{idx}"
            
            rows.append({
                "row_id": f"{document.id}_{row_id}",
                "row_data": row_data,
                "row_index": idx,
                "source_document_id": document.id,
                "total_rows": len(table_data)
            })
        
        document.data["rows"] = rows
        document.data["total_rows"] = len(rows)
        document.summary_data["rows_extracted"] = len(rows)
        document.summary_data["source_table_key"] = self.table_key
        
        logger.info(f"Extracted {len(rows)} rows from table in document {document.id}")
        
        return document
