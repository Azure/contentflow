"""
Advanced parallel processing executors for complex document workflows.

DEPRECATED: This module is deprecated. Please use the following modules instead:
- batch_splitter.py: DocumentSplitter, BatchDocumentSplitter, TableRowSplitter
- batch_aggregator.py: ResultAggregator, ChunkAggregator, BatchResultCollector
- batch_processor.py: BatchProcessor, ParallelDocumentProcessor, FilterProcessor

The executors in this file are kept for backward compatibility but will be
removed in a future version.

This module provides specialized executors for handling complex parallel processing
scenarios such as:
- Processing Excel rows in parallel sub-workflows
- Splitting large documents and processing chunks in parallel
- Fan-out/fan-in patterns with dynamic parallelism
"""

import logging
from typing import Any, Dict, List, Optional, Callable
from datetime import datetime

from agent_framework import Executor, handler, WorkflowContext, WorkflowExecutor, Workflow
from typing_extensions import Never

try:
    import sys
    import os
    doc_proc_lib_path = os.path.join(os.path.dirname(__file__), "../../../doc-proc-lib")
    if os.path.exists(doc_proc_lib_path):
        sys.path.insert(0, doc_proc_lib_path)
    
    from doc.proc.models import Document
except ImportError as e:
    raise ImportError(
        f"Failed to import doc-proc-lib models. Ensure doc-proc-lib is installed: {e}"
    )

from doc_proc_workflow.executors.base import DocumentExecutor

logger = logging.getLogger("doc_proc_workflow.executors.parallel")


class ExcelRowProcessor(Executor):
    """
    Process Excel rows in parallel using sub-workflows.
    
    This executor reads an Excel file from a document, spawns a sub-workflow
    for each row, and aggregates the results. Perfect for scenarios where
    each Excel row represents a task that needs independent processing.
    
    Example:
        ```python
        # Create a sub-workflow for processing one row
        row_workflow = build_row_processing_workflow()
        
        # Create Excel processor
        excel_processor = ExcelRowProcessor(
            sub_workflow=row_workflow,
            excel_key="excel_data",  # Key in document.data
            max_parallel=10  # Process up to 10 rows concurrently
        )
        
        # Use in main workflow
        workflow = WorkflowBuilder().add_edge(excel_processor, aggregator).build()
        ```
    """
    
    def __init__(
        self,
        sub_workflow: Workflow,
        excel_key: str = "excel_data",
        max_parallel: int = 10,
        row_key: str = "row_data",
        executor_id: str = "excel_row_processor"
    ):
        """
        Initialize the Excel row processor.
        
        Args:
            sub_workflow: Workflow to execute for each row
            excel_key: Key in document.data containing Excel data (list of dicts)
            max_parallel: Maximum number of rows to process in parallel
            row_key: Key to store row data in spawned documents
            executor_id: Unique executor identifier
        """
        super().__init__(id=executor_id)
        self.sub_workflow = sub_workflow
        self.excel_key = excel_key
        self.max_parallel = max_parallel
        self.row_key = row_key
        self.workflow_executor = WorkflowExecutor(sub_workflow, id=f"{executor_id}_workflow")
        
        logger.info(
            f"Initialized ExcelRowProcessor with max_parallel={max_parallel}"
        )
    
    @handler
    async def process_excel(
        self,
        document: Document,
        ctx: WorkflowContext[Never, List[Document]]
    ) -> None:
        """
        Process Excel document by spawning sub-workflows for each row.
        
        Args:
            document: Document containing Excel data
            ctx: Workflow context
        """
        start_time = datetime.now()
        
        # Extract Excel data
        excel_data = document.data.get(self.excel_key, [])
        if not excel_data:
            logger.warning(f"No Excel data found in document {document.id}")
            await ctx.yield_output([])
            return
        
        logger.info(
            f"Processing {len(excel_data)} Excel rows from document {document.id}"
        )
        
        # Create a document for each row
        row_documents = []
        for idx, row_data in enumerate(excel_data):
            row_doc = Document(
                id=f"{document.id}_row_{idx}",
                data={
                    self.row_key: row_data,
                    "source_document_id": document.id,
                    "row_index": idx,
                    "total_rows": len(excel_data)
                },
                summary_data={
                    "row_number": idx + 1,
                    "parent_document": document.id
                }
            )
            row_documents.append(row_doc)
        
        # Process rows in batches for controlled parallelism
        results = []
        batch_size = self.max_parallel
        
        for batch_start in range(0, len(row_documents), batch_size):
            batch_end = min(batch_start + batch_size, len(row_documents))
            batch = row_documents[batch_start:batch_end]
            
            logger.info(
                f"Processing batch {batch_start//batch_size + 1}: "
                f"rows {batch_start + 1}-{batch_end}"
            )
            
            # Send each row to the sub-workflow
            for row_doc in batch:
                await ctx.send_message(row_doc, target_id=self.workflow_executor.id)
        
        # Note: Results will be collected by the aggregator
        # This is a fan-out pattern - aggregation happens downstream
        elapsed = (datetime.now() - start_time).total_seconds()
        logger.info(
            f"Dispatched {len(row_documents)} rows for processing in {elapsed:.2f}s"
        )
        
        # Yield metadata about the processing
        summary_doc = Document(
            id=f"{document.id}_summary",
            data={
                "total_rows": len(row_documents),
                "source_document_id": document.id
            },
            summary_data={
                "processing_time_secs": elapsed,
                "rows_processed": len(row_documents)
            }
        )
        await ctx.yield_output(summary_doc)


class DocumentSplitter(DocumentExecutor):
    """
    Split large documents into chunks for parallel processing.
    
    This executor takes a large document (PDF, Word, text file) and splits it
    into smaller chunks that can be processed in parallel. Common use cases:
    - Splitting a 100-page PDF into 10-page chunks
    - Dividing a large text file by character/word count
    - Breaking up a Word document by sections
    
    Example:
        ```python
        splitter = DocumentSplitter(
            chunk_size=10,  # 10 pages/sections per chunk
            split_strategy="pages"  # or "characters", "words"
        )
        
        # Process chunks in parallel
        workflow = (
            WorkflowBuilder()
            .add_edge(splitter, [processor1, processor2, processor3])
            .add_fan_in_edges([processor1, processor2, processor3], merger)
            .build()
        )
        ```
    """
    
    def __init__(
        self,
        chunk_size: int = 10,
        split_strategy: str = "pages",
        content_key: str = "content",
        executor_id: str = "document_splitter"
    ):
        """
        Initialize the document splitter.
        
        Args:
            chunk_size: Size of each chunk (meaning depends on strategy)
            split_strategy: Strategy for splitting ("pages", "characters", "words", "lines")
            content_key: Key in document.data containing content to split
            executor_id: Unique executor identifier
        """
        super().__init__(id=executor_id)
        self.chunk_size = chunk_size
        self.split_strategy = split_strategy
        self.content_key = content_key
        
        logger.info(
            f"Initialized DocumentSplitter with strategy={split_strategy}, "
            f"chunk_size={chunk_size}"
        )
    
    async def process_document(
        self,
        document: Document,
        ctx: WorkflowContext
    ) -> Document:
        """
        Split document into chunks.
        
        This method modifies the document to include chunk information
        and stores chunks in document.data for downstream processing.
        
        Args:
            document: Document to split
            ctx: Workflow context
            
        Returns:
            Document with chunks stored in data
        """
        content = document.data.get(self.content_key, "")
        
        if not content:
            logger.warning(f"No content found in document {document.id}")
            return document
        
        # Split content based on strategy
        chunks = self._split_content(content, document)
        
        # Store chunks in document
        document.data["chunks"] = chunks
        document.data["total_chunks"] = len(chunks)
        document.summary_data["split_strategy"] = self.split_strategy
        document.summary_data["chunk_size"] = self.chunk_size
        document.summary_data["total_chunks"] = len(chunks)
        
        logger.info(
            f"Split document {document.id} into {len(chunks)} chunks "
            f"using {self.split_strategy} strategy"
        )
        
        return document
    
    def _split_content(
        self,
        content: str,
        document: Document
    ) -> List[Dict[str, Any]]:
        """
        Split content based on the configured strategy.
        
        Args:
            content: Content to split
            document: Source document
            
        Returns:
            List of chunk dictionaries
        """
        chunks = []
        
        if self.split_strategy == "pages":
            # Split by page markers or fixed character count as proxy
            chunks = self._split_by_pages(content, document)
        
        elif self.split_strategy == "characters":
            # Split by character count
            chunks = self._split_by_characters(content, document)
        
        elif self.split_strategy == "words":
            # Split by word count
            chunks = self._split_by_words(content, document)
        
        elif self.split_strategy == "lines":
            # Split by line count
            chunks = self._split_by_lines(content, document)
        
        else:
            raise ValueError(f"Unknown split strategy: {self.split_strategy}")
        
        return chunks
    
    def _split_by_pages(
        self,
        content: str,
        document: Document
    ) -> List[Dict[str, Any]]:
        """Split content by pages (page breaks or character count proxy)."""
        chunks = []
        
        # Check for explicit page markers
        if "\f" in content or "\\page" in content:
            # Split by form feed or page markers
            pages = content.split("\f") if "\f" in content else content.split("\\page")
        else:
            # Use character count as proxy (e.g., 3000 chars ≈ 1 page)
            chars_per_page = 3000
            total_chars = len(content)
            pages = []
            for i in range(0, total_chars, chars_per_page):
                pages.append(content[i:i + chars_per_page])
        
        # Group pages into chunks
        for i in range(0, len(pages), self.chunk_size):
            chunk_pages = pages[i:i + self.chunk_size]
            chunks.append({
                "chunk_id": f"{document.id}_chunk_{i//self.chunk_size}",
                "content": "\f".join(chunk_pages),
                "start_page": i + 1,
                "end_page": min(i + self.chunk_size, len(pages)),
                "total_pages": len(chunk_pages),
                "chunk_index": i // self.chunk_size
            })
        
        return chunks
    
    def _split_by_characters(
        self,
        content: str,
        document: Document
    ) -> List[Dict[str, Any]]:
        """Split content by character count."""
        chunks = []
        total_chars = len(content)
        
        for i in range(0, total_chars, self.chunk_size):
            chunk_content = content[i:i + self.chunk_size]
            chunks.append({
                "chunk_id": f"{document.id}_chunk_{i//self.chunk_size}",
                "content": chunk_content,
                "start_char": i,
                "end_char": min(i + self.chunk_size, total_chars),
                "char_count": len(chunk_content),
                "chunk_index": i // self.chunk_size
            })
        
        return chunks
    
    def _split_by_words(
        self,
        content: str,
        document: Document
    ) -> List[Dict[str, Any]]:
        """Split content by word count."""
        words = content.split()
        chunks = []
        
        for i in range(0, len(words), self.chunk_size):
            chunk_words = words[i:i + self.chunk_size]
            chunks.append({
                "chunk_id": f"{document.id}_chunk_{i//self.chunk_size}",
                "content": " ".join(chunk_words),
                "start_word": i,
                "end_word": min(i + self.chunk_size, len(words)),
                "word_count": len(chunk_words),
                "chunk_index": i // self.chunk_size
            })
        
        return chunks
    
    def _split_by_lines(
        self,
        content: str,
        document: Document
    ) -> List[Dict[str, Any]]:
        """Split content by line count."""
        lines = content.split("\n")
        chunks = []
        
        for i in range(0, len(lines), self.chunk_size):
            chunk_lines = lines[i:i + self.chunk_size]
            chunks.append({
                "chunk_id": f"{document.id}_chunk_{i//self.chunk_size}",
                "content": "\n".join(chunk_lines),
                "start_line": i + 1,
                "end_line": min(i + self.chunk_size, len(lines)),
                "line_count": len(chunk_lines),
                "chunk_index": i // self.chunk_size
            })
        
        return chunks


class ChunkProcessor(Executor):
    """
    Process individual document chunks in parallel.
    
    This executor works with DocumentSplitter to process chunks created
    from a split document. It spawns a document for each chunk and sends
    them through a sub-workflow.
    
    Example:
        ```python
        # Create chunk processing workflow
        chunk_workflow = build_chunk_workflow()
        
        # Create chunk processor
        chunk_processor = ChunkProcessor(
            sub_workflow=chunk_workflow,
            max_parallel=5
        )
        
        # Chain with splitter and merger
        workflow = (
            WorkflowBuilder()
            .add_edge(splitter, chunk_processor)
            .add_edge(chunk_processor, merger)
            .build()
        )
        ```
    """
    
    def __init__(
        self,
        sub_workflow: Workflow,
        max_parallel: int = 5,
        executor_id: str = "chunk_processor"
    ):
        """
        Initialize the chunk processor.
        
        Args:
            sub_workflow: Workflow to execute for each chunk
            max_parallel: Maximum number of chunks to process in parallel
            executor_id: Unique executor identifier
        """
        super().__init__(id=executor_id)
        self.sub_workflow = sub_workflow
        self.max_parallel = max_parallel
        self.workflow_executor = WorkflowExecutor(sub_workflow, id=f"{executor_id}_workflow")
        
        logger.info(
            f"Initialized ChunkProcessor with max_parallel={max_parallel}"
        )
    
    @handler
    async def process_chunks(
        self,
        document: Document,
        ctx: WorkflowContext[Never, List[Document]]
    ) -> None:
        """
        Process document chunks in parallel.
        
        Args:
            document: Document containing chunks
            ctx: Workflow context
        """
        chunks = document.data.get("chunks", [])
        
        if not chunks:
            logger.warning(f"No chunks found in document {document.id}")
            await ctx.yield_output([])
            return
        
        logger.info(
            f"Processing {len(chunks)} chunks from document {document.id}"
        )
        
        # Create a document for each chunk
        chunk_documents = []
        for chunk in chunks:
            chunk_doc = Document(
                id=chunk.get("chunk_id", f"{document.id}_chunk_{chunk.get('chunk_index')}"),
                data={
                    "chunk_content": chunk.get("content"),
                    "chunk_metadata": chunk,
                    "source_document_id": document.id
                },
                summary_data={
                    "chunk_index": chunk.get("chunk_index"),
                    "parent_document": document.id
                }
            )
            chunk_documents.append(chunk_doc)
        
        # Process chunks in batches
        batch_size = self.max_parallel
        for batch_start in range(0, len(chunk_documents), batch_size):
            batch_end = min(batch_start + batch_size, len(chunk_documents))
            batch = chunk_documents[batch_start:batch_end]
            
            logger.info(
                f"Processing batch {batch_start//batch_size + 1}: "
                f"chunks {batch_start + 1}-{batch_end}"
            )
            
            for chunk_doc in batch:
                await ctx.send_message(chunk_doc, target_id=self.workflow_executor.id)
        
        logger.info(f"Dispatched {len(chunk_documents)} chunks for processing")


class ResultAggregator(Executor):
    """
    Aggregate results from parallel processing operations.
    
    This executor collects results from multiple parallel executors (rows, chunks)
    and combines them into a single output. Supports various aggregation strategies:
    - Merge all results into a list
    - Concatenate text content
    - Combine summary statistics
    - Custom aggregation logic
    
    Example:
        ```python
        aggregator = ResultAggregator(
            aggregation_strategy="merge_list",
            expected_count=10  # Wait for 10 results
        )
        
        workflow = (
            WorkflowBuilder()
            .add_fan_in_edges([proc1, proc2, proc3], aggregator)
            .build()
        )
        ```
    """
    
    def __init__(
        self,
        aggregation_strategy: str = "merge_list",
        expected_count: Optional[int] = None,
        custom_aggregator: Optional[Callable] = None,
        executor_id: str = "result_aggregator"
    ):
        """
        Initialize the result aggregator.
        
        Args:
            aggregation_strategy: Strategy for aggregating results
                - "merge_list": Combine into list
                - "concatenate": Concatenate text content
                - "summarize": Combine summary statistics
                - "custom": Use custom aggregator function
            expected_count: Expected number of results (optional)
            custom_aggregator: Custom aggregation function
            executor_id: Unique executor identifier
        """
        super().__init__(id=executor_id)
        self.aggregation_strategy = aggregation_strategy
        self.expected_count = expected_count
        self.custom_aggregator = custom_aggregator
        self.collected_results: List[Any] = []
        
        logger.info(
            f"Initialized ResultAggregator with strategy={aggregation_strategy}"
        )
    
    @handler
    async def aggregate_results(
        self,
        results: List[Document],
        ctx: WorkflowContext[Never, Document]
    ) -> None:
        """
        Aggregate results from parallel processing.
        
        Args:
            results: List of result documents
            ctx: Workflow context
        """
        if not results:
            logger.warning("No results to aggregate")
            empty_doc = Document(
                id="aggregated_empty",
                data={"results": []},
                summary_data={"result_count": 0}
            )
            await ctx.yield_output(empty_doc)
            return
        
        logger.info(f"Aggregating {len(results)} results")
        
        # Apply aggregation strategy
        if self.aggregation_strategy == "merge_list":
            aggregated = self._merge_list(results)
        elif self.aggregation_strategy == "concatenate":
            aggregated = self._concatenate(results)
        elif self.aggregation_strategy == "summarize":
            aggregated = self._summarize(results)
        elif self.aggregation_strategy == "custom" and self.custom_aggregator:
            aggregated = await self.custom_aggregator(results)
        else:
            # Default: merge list
            aggregated = self._merge_list(results)
        
        await ctx.yield_output(aggregated)
    
    def _merge_list(self, results: List[Document]) -> Document:
        """Merge results into a list."""
        return Document(
            id="aggregated_results",
            data={
                "results": [r.data for r in results],
                "result_count": len(results)
            },
            summary_data={
                "aggregation_strategy": "merge_list",
                "total_results": len(results),
                "result_ids": [r.id for r in results]
            }
        )
    
    def _concatenate(self, results: List[Document]) -> Document:
        """Concatenate text content from results."""
        concatenated_content = "\n\n".join([
            r.data.get("content", "") or r.data.get("chunk_content", "")
            for r in results
        ])
        
        return Document(
            id="aggregated_results",
            data={
                "content": concatenated_content,
                "result_count": len(results)
            },
            summary_data={
                "aggregation_strategy": "concatenate",
                "total_results": len(results),
                "total_length": len(concatenated_content)
            }
        )
    
    def _summarize(self, results: List[Document]) -> Document:
        """Summarize statistics from results."""
        summary_stats = {
            "total_results": len(results),
            "result_ids": [r.id for r in results]
        }
        
        # Collect summary data from all results
        for result in results:
            for key, value in result.summary_data.items():
                if isinstance(value, (int, float)):
                    if key not in summary_stats:
                        summary_stats[key] = 0
                    summary_stats[key] += value
        
        return Document(
            id="aggregated_results",
            data={"results": [r.data for r in results]},
            summary_data=summary_stats
        )
