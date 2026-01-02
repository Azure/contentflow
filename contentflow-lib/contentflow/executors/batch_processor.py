"""
Batch processing executors.

This module provides executors that process batches of documents or data
with various processing strategies.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

from agent_framework import WorkflowContext

from .base import DocumentExecutor

try:
    from doc.proc.models import Document
except ImportError as e:
    raise ImportError(f"Failed to import doc-proc-lib models: {e}")

logger = logging.getLogger("doc_proc_workflow.executors.batch_processor")


class BatchProcessor(DocumentExecutor):
    """
    Process items in batches with controlled parallelism.
    
    Generic batch processor that can handle any list of items,
    applying a processing function to each batch.
    
    For sub-workflow execution per batch, use BatchSubWorkflowExecutor instead.
    
    Configuration:
        items_key (str): Key in document.data containing items list (default: "items")
        batch_size (int): Number of items per batch (default: 10)
        max_concurrent (int): Maximum concurrent batch processing (default: 1)
        preserve_order (bool): Whether to preserve item order (default: True)
        retry_failures (bool): Whether to retry failed items (default: False)
        max_retries (int): Maximum retry attempts (default: 3)
    
    Example:
        ```yaml
        - id: batch_proc
          type: batch_processor
          settings:
            items_key: documents
            batch_size: 50
            max_concurrent: 3
        ```
    """
    
    def __init__(self, settings: Dict[str, Any] = None, **kwargs):
        super().__init__(id=kwargs.get("id", "batch_processor"), settings=settings)
        
        self.items_key = self.get_setting("items_key", default="items")
        self.batch_size = self.get_setting("batch_size", default=10)
        self.max_concurrent = self.get_setting("max_concurrent", default=1)
        self.preserve_order = self.get_setting("preserve_order", default=True)
        self.retry_failures = self.get_setting("retry_failures", default=False)
        self.max_retries = self.get_setting("max_retries", default=3)
        
        logger.info(
            f"Initialized BatchProcessor: batch_size={self.batch_size}, "
            f"max_concurrent={self.max_concurrent}"
        )
    
    async def process_document(
        self,
        document: Document,
        ctx: WorkflowContext
    ) -> Document:
        """
        Process items in batches.
        
        Args:
            document: Document containing items to process
            ctx: Workflow context
            
        Returns:
            Document with processed items
        """
        items = document.data.get(self.items_key, [])
        
        if not items:
            logger.warning(f"No items found at key '{self.items_key}' in {document.id}")
            document.data["processed_items"] = []
            document.summary_data["items_processed"] = 0
            return document
        
        start_time = datetime.utcnow()
        
        # Split into batches
        batches = [items[i:i + self.batch_size] 
                  for i in range(0, len(items), self.batch_size)]
        
        logger.info(f"Processing {len(items)} items in {len(batches)} batches")
        
        # Process batches with controlled concurrency
        processed_items = []
        failed_items = []
        
        if self.max_concurrent > 1:
            # Process multiple batches concurrently
            semaphore = asyncio.Semaphore(self.max_concurrent)
            
            async def process_batch_with_semaphore(batch, batch_idx):
                async with semaphore:
                    return await self._process_batch(batch, batch_idx, ctx)
            
            tasks = [process_batch_with_semaphore(batch, idx) 
                    for idx, batch in enumerate(batches)]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in results:
                if isinstance(result, Exception):
                    logger.error(f"Batch processing error: {result}")
                    failed_items.append({"error": str(result)})
                else:
                    processed_items.extend(result.get("processed", []))
                    failed_items.extend(result.get("failed", []))
        else:
            # Process batches sequentially
            for idx, batch in enumerate(batches):
                result = await self._process_batch(batch, idx, ctx)
                processed_items.extend(result.get("processed", []))
                failed_items.extend(result.get("failed", []))
        
        # Handle retries if enabled
        if self.retry_failures and failed_items:
            retry_count = 0
            while failed_items and retry_count < self.max_retries:
                retry_count += 1
                logger.info(f"Retrying {len(failed_items)} failed items (attempt {retry_count})")
                
                retry_result = await self._process_batch(
                    [item.get("item") for item in failed_items], 
                    -1, 
                    ctx
                )
                
                processed_items.extend(retry_result.get("processed", []))
                failed_items = retry_result.get("failed", [])
        
        elapsed = (datetime.utcnow() - start_time).total_seconds()
        
        # Store results
        document.data["processed_items"] = processed_items
        if failed_items:
            document.data["failed_items"] = failed_items
        
        document.summary_data.update({
            "total_items": len(items),
            "processed_count": len(processed_items),
            "failed_count": len(failed_items),
            "success_rate": len(processed_items) / len(items) if items else 0,
            "processing_time_secs": elapsed,
            "batches_processed": len(batches)
        })
        
        logger.info(
            f"Batch processing complete: {len(processed_items)}/{len(items)} successful "
            f"in {elapsed:.2f}s"
        )
        
        return document
    
    async def _process_batch(
        self,
        batch: List[Any],
        batch_idx: int,
        ctx: WorkflowContext
    ) -> Dict[str, List]:
        """
        Process a single batch of items.
        
        Override this method to implement custom batch processing logic.
        
        Args:
            batch: List of items to process
            batch_idx: Batch index
            ctx: Workflow context
            
        Returns:
            Dict with 'processed' and 'failed' lists
        """
        processed = []
        failed = []
        
        for item in batch:
            try:
                # Default: just pass through the item
                # Subclasses should override this method with actual processing
                processed.append(item)
            except Exception as e:
                logger.error(f"Error processing item: {e}")
                failed.append({"item": item, "error": str(e)})
        
        return {"processed": processed, "failed": failed}


class FilterProcessor(DocumentExecutor):
    """
    Filter items based on conditions.
    
    Filters a list of items based on configurable conditions,
    useful for pre-processing before batch operations.
    
    Configuration:
        items_key (str): Key in document.data containing items (default: "items")
        filter_field (str): Field to filter on (default: None = no filtering)
        filter_value (Any): Value to match (default: None)
        filter_operator (str): Operator for comparison (default: "equals")
            - "equals", "not_equals", "contains", "greater_than", "less_than"
        invert (bool): Invert the filter (default: False)
        remove_duplicates (bool): Remove duplicate items (default: False)
    
    Example:
        ```yaml
        - id: filter
          type: filter_processor
          settings:
            items_key: records
            filter_field: status
            filter_value: active
            filter_operator: equals
        ```
    """
    
    def __init__(self, settings: Dict[str, Any] = None, **kwargs):
        super().__init__(id=kwargs.get("id", "filter_processor"), settings=settings)
        
        self.items_key = self.get_setting("items_key", default="items")
        self.filter_field = self.get_setting("filter_field", default=None)
        self.filter_value = self.get_setting("filter_value", default=None)
        self.filter_operator = self.get_setting("filter_operator", default="equals")
        self.invert = self.get_setting("invert", default=False)
        self.remove_duplicates = self.get_setting("remove_duplicates", default=False)
        
        logger.info(f"Initialized FilterProcessor: field={self.filter_field}, operator={self.filter_operator}")
    
    async def process_document(
        self,
        document: Document,
        ctx: WorkflowContext
    ) -> Document:
        """
        Filter items based on conditions.
        
        Args:
            document: Document containing items to filter
            ctx: Workflow context
            
        Returns:
            Document with filtered items
        """
        items = document.data.get(self.items_key, [])
        
        if not items:
            logger.warning(f"No items found at key '{self.items_key}' in {document.id}")
            document.data["filtered_items"] = []
            return document
        
        original_count = len(items)
        
        # Apply filter if configured
        if self.filter_field and self.filter_value is not None:
            filtered = []
            for item in items:
                if self._matches_filter(item):
                    filtered.append(item)
            items = filtered
        
        # Remove duplicates if configured
        if self.remove_duplicates:
            seen = set()
            unique_items = []
            for item in items:
                # Create a hashable representation
                item_key = str(item)
                if item_key not in seen:
                    seen.add(item_key)
                    unique_items.append(item)
            items = unique_items
        
        document.data["filtered_items"] = items
        document.summary_data.update({
            "original_count": original_count,
            "filtered_count": len(items),
            "removed_count": original_count - len(items),
            "filter_applied": self.filter_field is not None
        })
        
        logger.info(f"Filtered {original_count} items to {len(items)} items")
        
        return document
    
    def _matches_filter(self, item: Any) -> bool:
        """Check if item matches filter conditions."""
        # Extract field value
        if isinstance(item, dict):
            value = item.get(self.filter_field)
        else:
            value = getattr(item, self.filter_field, None)
        
        # Apply operator
        match = False
        
        if self.filter_operator == "equals":
            match = value == self.filter_value
        elif self.filter_operator == "not_equals":
            match = value != self.filter_value
        elif self.filter_operator == "contains":
            match = self.filter_value in str(value)
        elif self.filter_operator == "greater_than":
            match = value > self.filter_value
        elif self.filter_operator == "less_than":
            match = value < self.filter_value
        
        # Invert if configured
        return not match if self.invert else match
