"""
Sub-workflow executors for parallel processing.

This module provides executors that spawn sub-workflows for processing
items in parallel, such as rows, chunks, or batches.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

from agent_framework import Workflow, WorkflowContext

from .base import DocumentExecutor

try:
    from doc.proc.models import Document
except ImportError as e:
    raise ImportError(f"Failed to import doc-proc-lib models: {e}")

logger = logging.getLogger("doc_proc_workflow.executors.subworkflow")


class SubWorkflowExecutor(DocumentExecutor):
    """
    Base executor for running sub-workflows on document items.
    
    This executor processes items by running each through a sub-workflow,
    enabling complex multi-step processing in parallel.
    
    Configuration:
        sub_workflow (Workflow): Workflow to execute for each item (required, passed in __init__)
        items_key (str): Key in document.data containing items (default: "items")
        max_parallel (int): Maximum concurrent sub-workflow executions (default: 5)
        timeout_secs (int): Timeout per sub-workflow in seconds (default: 300)
        collect_results (bool): Whether to collect sub-workflow results (default: True)
    """
    
    def __init__(
        self, 
        sub_workflow: Workflow,
        settings: Dict[str, Any] = None,
        **kwargs
    ):
        """
        Initialize sub-workflow executor.
        
        Args:
            sub_workflow: Workflow to execute for each item
            settings: Configuration settings
            **kwargs: Additional arguments (id, etc.)
        """
        super().__init__(id=kwargs.get("id", "subworkflow_executor"), settings=settings)
        
        if not sub_workflow:
            raise ValueError("sub_workflow is required")
        
        self.sub_workflow = sub_workflow
        self.items_key = self.get_setting("items_key", default="items")
        self.max_parallel = self.get_setting("max_parallel", default=5)
        self.timeout_secs = self.get_setting("timeout_secs", default=300)
        self.collect_results = self.get_setting("collect_results", default=True)
        
        logger.info(
            f"Initialized SubWorkflowExecutor: max_parallel={self.max_parallel}, "
            f"timeout={self.timeout_secs}s"
        )
    
    async def process_document(
        self,
        document: Document,
        ctx: WorkflowContext
    ) -> Document:
        """
        Process document items through sub-workflow.
        
        Args:
            document: Document containing items to process
            ctx: Workflow context
            
        Returns:
            Document with sub-workflow results
        """
        items = document.data.get(self.items_key, [])
        
        if not items:
            logger.warning(f"No items found at key '{self.items_key}' in {document.id}")
            document.data["subworkflow_results"] = []
            return document
        
        logger.info(f"Processing {len(items)} items through sub-workflow")
        
        start_time = datetime.utcnow()
        
        # Process items with controlled concurrency
        semaphore = asyncio.Semaphore(self.max_parallel)
        
        async def process_item_with_semaphore(item, idx):
            async with semaphore:
                try:
                    return await asyncio.wait_for(
                        self._execute_subworkflow(item, idx, ctx),
                        timeout=self.timeout_secs
                    )
                except asyncio.TimeoutError:
                    logger.error(f"Item {idx} timed out after {self.timeout_secs}s")
                    return {"error": "timeout", "item_index": idx}
                except Exception as e:
                    logger.error(f"Error processing item {idx}: {e}")
                    return {"error": str(e), "item_index": idx}
        
        # Execute sub-workflows in parallel
        tasks = [process_item_with_semaphore(item, idx) for idx, item in enumerate(items)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Separate successful and failed results
        successful_results = []
        errors = []
        
        for result in results:
            if isinstance(result, Exception):
                errors.append({"error": str(result)})
            elif isinstance(result, dict) and "error" in result:
                errors.append(result)
            else:
                successful_results.append(result)
        
        elapsed = (datetime.utcnow() - start_time).total_seconds()
        
        # Store results
        if self.collect_results:
            document.data["subworkflow_results"] = successful_results
        if errors:
            document.data["subworkflow_errors"] = errors
        
        document.summary_data.update({
            "total_items": len(items),
            "successful_count": len(successful_results),
            "failed_count": len(errors),
            "success_rate": len(successful_results) / len(items) if items else 0,
            "processing_time_secs": elapsed
        })
        
        logger.info(
            f"Sub-workflow processing complete: {len(successful_results)}/{len(items)} "
            f"successful in {elapsed:.2f}s"
        )
        
        return document
    
    async def _execute_subworkflow(
        self,
        item: Any,
        index: int,
        ctx: WorkflowContext
    ) -> Any:
        """
        Execute sub-workflow for a single item.
        
        Args:
            item: Item to process
            index: Item index
            ctx: Workflow context
            
        Returns:
            Sub-workflow result
        """
        # Create a document for the item
        item_doc = self._create_item_document(item, index)
        
        # Get connectors from context if available
        connectors = {}
        if hasattr(ctx, "data") and isinstance(ctx.data, dict):
            connectors = ctx.data.get("connectors", {})
        
        # Execute sub-workflow
        result_doc = None
        async for event in self.sub_workflow.run_stream(
            item_doc, 
            context={"connectors": connectors}
        ):
            # Capture final document from workflow output
            if hasattr(event, "data"):
                result_doc = event.data
        
        return result_doc or item_doc
    
    def _create_item_document(self, item: Any, index: int) -> Document:
        """
        Create a document for an item.
        
        Override this method to customize item document creation.
        
        Args:
            item: Item data
            index: Item index
            
        Returns:
            Document for the item
        """
        return Document(
            id=f"item_{index}",
            data={"item": item, "item_index": index},
            summary_data={"item_number": index + 1}
        )


class RowSubWorkflowExecutor(SubWorkflowExecutor):
    """
    Execute sub-workflow for each row in table/Excel data.
    
    Processes rows from Excel, CSV, or tabular data by running
    each row through a sub-workflow.
    
    Configuration:
        sub_workflow (Workflow): Workflow to execute for each row (required, passed in __init__)
        table_key (str): Key in document.data containing table data (default: "table_data")
        row_key (str): Key to store row data in item documents (default: "row_data")
        max_parallel (int): Maximum concurrent row processing (default: 10)
        row_id_field (str): Field to use as row ID (default: None = use index)
    
    Example:
        ```python
        from agent_framework import WorkflowBuilder
        
        # Create row processing workflow
        row_workflow = (
            WorkflowBuilder()
            .add_edge(validator, enricher)
            .build()
        )
        
        # Create row executor
        row_executor = RowSubWorkflowExecutor(
            sub_workflow=row_workflow,
            settings={
                "table_key": "excel_data",
                "max_parallel": 10
            }
        )
        ```
    """
    
    def __init__(
        self,
        sub_workflow: Workflow,
        settings: Dict[str, Any] = None,
        **kwargs
    ):
        # Override items_key default
        if settings is None:
            settings = {}
        settings.setdefault("items_key", "table_data")
        
        super().__init__(sub_workflow=sub_workflow, settings=settings, **kwargs)
        
        self.table_key = self.get_setting("table_key", default="table_data")
        self.row_key = self.get_setting("row_key", default="row_data")
        self.row_id_field = self.get_setting("row_id_field", default=None)
        
        # Update items_key to match table_key
        self.items_key = self.table_key
    
    def _create_item_document(self, item: Any, index: int) -> Document:
        """Create a document for a table row."""
        # Determine row ID
        if self.row_id_field and isinstance(item, dict):
            row_id = item.get(self.row_id_field, f"row_{index}")
        else:
            row_id = f"row_{index}"
        
        return Document(
            id=f"row_{row_id}",
            data={
                self.row_key: item,
                "row_index": index
            },
            summary_data={
                "row_number": index + 1
            }
        )


class ChunkSubWorkflowExecutor(SubWorkflowExecutor):
    """
    Execute sub-workflow for each document chunk.
    
    Processes chunks created by DocumentSplitter by running each
    chunk through a sub-workflow.
    
    Configuration:
        sub_workflow (Workflow): Workflow to execute for each chunk (required, passed in __init__)
        chunks_key (str): Key in document.data containing chunks (default: "chunks")
        max_parallel (int): Maximum concurrent chunk processing (default: 5)
    
    Example:
        ```python
        # Create chunk processing workflow
        chunk_workflow = (
            WorkflowBuilder()
            .add_edge(text_extractor, entity_recognizer)
            .add_edge(entity_recognizer, sentiment_analyzer)
            .build()
        )
        
        # Create chunk executor
        chunk_executor = ChunkSubWorkflowExecutor(
            sub_workflow=chunk_workflow,
            settings={"max_parallel": 5}
        )
        ```
    """
    
    def __init__(
        self,
        sub_workflow: Workflow,
        settings: Dict[str, Any] = None,
        **kwargs
    ):
        # Override items_key default
        if settings is None:
            settings = {}
        settings.setdefault("items_key", "chunks")
        
        super().__init__(sub_workflow=sub_workflow, settings=settings, **kwargs)
        
        self.chunks_key = self.get_setting("chunks_key", default="chunks")
        self.items_key = self.chunks_key
    
    def _create_item_document(self, item: Any, index: int) -> Document:
        """Create a document for a chunk."""
        chunk_id = item.get("chunk_id", f"chunk_{index}") if isinstance(item, dict) else f"chunk_{index}"
        
        return Document(
            id=chunk_id,
            data={
                "chunk_data": item,
                "chunk_content": item.get("content") if isinstance(item, dict) else str(item),
                "chunk_index": index
            },
            summary_data={
                "chunk_number": index + 1,
                "chunk_metadata": item if isinstance(item, dict) else {}
            }
        )


class BatchSubWorkflowExecutor(SubWorkflowExecutor):
    """
    Execute sub-workflow for each batch of documents.
    
    Processes batches created by BatchDocumentSplitter by running
    each batch through a sub-workflow.
    
    Configuration:
        sub_workflow (Workflow): Workflow to execute for each batch (required, passed in __init__)
        batches_key (str): Key in document.data containing batches (default: "batches")
        max_parallel (int): Maximum concurrent batch processing (default: 3)
    
    Example:
        ```python
        # Create batch processing workflow
        batch_workflow = build_batch_processor()
        
        # Create batch executor
        batch_executor = BatchSubWorkflowExecutor(
            sub_workflow=batch_workflow,
            settings={"max_parallel": 3}
        )
        ```
    """
    
    def __init__(
        self,
        sub_workflow: Workflow,
        settings: Dict[str, Any] = None,
        **kwargs
    ):
        # Override items_key default
        if settings is None:
            settings = {}
        settings.setdefault("items_key", "batches")
        
        super().__init__(sub_workflow=sub_workflow, settings=settings, **kwargs)
        
        self.batches_key = self.get_setting("batches_key", default="batches")
        self.items_key = self.batches_key
    
    def _create_item_document(self, item: Any, index: int) -> Document:
        """Create a document for a batch."""
        batch_id = item.get("batch_id", f"batch_{index}") if isinstance(item, dict) else f"batch_{index}"
        
        return Document(
            id=batch_id,
            data={
                "batch_data": item,
                "documents": item.get("documents", []) if isinstance(item, dict) else [],
                "batch_index": index
            },
            summary_data={
                "batch_number": index + 1,
                "batch_size": len(item.get("documents", [])) if isinstance(item, dict) else 0
            }
        )
