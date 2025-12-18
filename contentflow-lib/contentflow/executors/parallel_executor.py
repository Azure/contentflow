"""
Batch processing executors.

This module provides executors that process batches of documents or data
with various processing strategies.
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union
from datetime import datetime

from agent_framework import WorkflowContext

from .base import BaseExecutor
from ..models import Content, ContentIdentifier, ExecutorLogEntry
    
logger = logging.getLogger(__name__)


class ParallelExecutor(BaseExecutor, ABC):
    """
    Process multiple content items in parallel.
    
    Takes a content item or list of content items and processes
    them in parallel with controlled concurrency.
    
    For sub-workflow execution per content item, use SubWorkflowExecutor instead.
    
    Configuration (settings dict):
        - max_concurrent (int): Maximum concurrent document processing
          Default: 5
        - timeout_secs (int): Timeout per document in seconds
          Default: 300
        - continue_on_error (bool): Continue if a document fails
          Default: True
    
    Example:
        ```yaml
        - id: parallel_proc
          type: parallel_processor
          settings:
            max_concurrent: 10
            timeout_secs: 60
            continue_on_error: true
        ```
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
        
        self.max_concurrent = self.get_setting("max_concurrent", default=5)
        self.timeout_secs = self.get_setting("timeout_secs", default=300)
        self.continue_on_error = self.get_setting("continue_on_error", default=True)
        
        if self.debug_mode:
            logger.debug(
                f"Initialized ParallelExecutor {self.id} with settings: "
                f"max_concurrent={self.max_concurrent}, "
                f"timeout_secs={self.timeout_secs}, "
                f"continue_on_error={self.continue_on_error}"
            )
    
    async def process_input(
        self,
        input: Union[Content, List[Content]],
        ctx: WorkflowContext[Union[Content, List[Content]], Union[Content, List[Content]]]
    ) -> Union[Content, List[Content]]:
        """
        Process content items in parallel.
        
        Args:
            input: Content item or list of content items to process
            ctx: Workflow context
            
        Returns:
            Content item or list of content items with processed content
        """
        # Handle list of content items with parallel processing
        if isinstance(input, list):
            if self.max_concurrent <= 1:
                # Sequential processing
                results = []
                for doc in input:
                    result = await self._process_content_item_internal(doc)
                    results.append(result)
                return results
            else:
                # Parallel processing with concurrency control
                import asyncio
                
                semaphore = asyncio.Semaphore(self.max_concurrent)
                
                async def process_with_semaphore(doc: Content) -> Content:
                    async with semaphore:
                        return await self._process_content_item_internal(doc)
                
                tasks = [process_with_semaphore(doc) for doc in input]
                results = await asyncio.gather(*tasks)
                return results
        
        # Single content item processing
        return await self._process_content_item_internal(input)
    
    async def _process_content_item_internal(
        self,
        content: Content
    ) -> Content:
        """
        Wraps the method process_content_item and adds timeout and error handling.
        """
        start_time = datetime.now()
        
        try:
            result = await asyncio.wait_for(
                self.process_content_item(content),
                timeout=self.timeout_secs
            )
            
            result.executor_logs.append(ExecutorLogEntry(
                executor_id=self.id,
                start_time=start_time,
                end_time=datetime.now(),
                status="completed",
                details={},
                errors=[]
            ))
            
            return result
            
        except Exception as e:
            logger.error(
                f"Content item failed in executor {self.id}: "
                f"{content.id.canonical_id if content.id else 'unknown'}: {str(e)}",
                exc_info=True
            )
            logger.exception(e)
            
            content.executor_logs.append(ExecutorLogEntry(
                executor_id=self.id,
                start_time=start_time,
                end_time=datetime.now(),
                status="failed",
                details={},
                errors=[str(e)]
            ))
            
            if self.fail_pipeline_on_error:
                raise
            else:
                return content  # Return original content on error"
        
    @abstractmethod
    async def process_content_item(
        self,
        content: Content
    ) -> Content:
        """
        Process a single content item.
        
        Override this method to implement custom content processing logic.
        
        Args:
            content: Content item to process
            
        Returns:
            Processed content item
        """
        # Subclasses should override with actual processing
        raise NotImplementedError("Subclasses must implement process_content_item method.")