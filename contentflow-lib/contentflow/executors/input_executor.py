"""
Base executor for document processing workflows.

This module provides the base class for all document processing executors,
integrating with the Microsoft Agent Framework's Executor pattern while
maintaining compatibility with doc-proc-lib's Document model and providing
dict-based configuration support.
"""
import functools
import hashlib
import logging
import os
from abc import ABC, abstractmethod
from typing import Any, AsyncGenerator, Dict, Optional, List, Union, Tuple
from typing_extensions import Never
from datetime import datetime

from agent_framework import WorkflowContext

from .base import BaseExecutor
from ..models import Content, ContentIdentifier

logger = logging.getLogger("contentflow.executors.input_executor")

class InputExecutor(BaseExecutor, ABC):
    """
    Base executor for input executors.
    
    This class serves as the base for all input executors in document
    processing workflows. It extends the BaseExecutor
    while providing additional functionality for crawling content sources
    and managing input content.
    
    Any input executor must inherit from this class and implement the
    abstract methods defined herein.
    
    Configuration (settings dict):
        - enabled (bool): Whether this executor is enabled
          Default: True
        - fail_pipeline_on_error (bool): Whether to fail the pipeline on error
          Default: False
        - debug_mode (bool): Enable debug logging
          Default: False
        - polling_interval_seconds (int): Polling interval in seconds
          Default: 300 (5 minutes)
        - max_results (int): Total to fetch per crawl
          Default: 1000
        - batch_size (int): Maximum results to fetch per poll/crawl
          Default: 100
        
    Checkpoint Management:
        The InputExecutor supports incremental crawling using checkpoint timestamps.
        - First crawl: checkpoint_timestamp is None, fetches initial content
        - Subsequent crawls: Uses the last successful checkpoint to fetch only new items
        - Checkpoint is saved automatically when crawl completes (continuation_token is None)
        
    Pagination:
        The crawl method returns a continuation_token for pagination support:
        - If more results exist: Returns a continuation_token for the next page
        - If all results fetched: Returns None as continuation_token
        - Use crawl_all() for automatic pagination across all pages
        
        Other Crawler-specific settings can be defined in subclasses
    """
    
    def __init__(
        self,
        id: str,
        settings: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        """
        Initialize the base executor.
        
        Args:
            id: Unique identifier for this executor
            settings: Configuration dict for the executor
            **kwargs: Additional executor configuration
        """
        super().__init__(id=id, settings=settings, **kwargs)
        
        self.polling_interval_seconds = self.settings.get("polling_interval_seconds", 300)
        self.max_results = self.settings.get("max_results", 1000)
        self.batch_size = self.settings.get("batch_size", 100)
        self.params = kwargs
        
        if self.debug_mode:
            logger.debug(
                f"Initialized InputExecutor: {id} "
                f"(enabled: {self.enabled})"
            )
    
    def _compute_content_hash(self, content: Content) -> str:
        """
        Compute a hash of the content to detect changes.
        
        This method generates a hash based on content attributes that
        should trigger an update when changed. Override this method if
        you need custom change detection logic.
        
        Args:
            content: The content item to hash
        
        Returns:
            A hash string representing the content's state
        """
        hash_input = f"{content.id.canonical_id}"
        
        return hashlib.md5(hash_input.encode()).hexdigest()
    
    @abstractmethod
    async def crawl(
        self, 
        checkpoint_timestamp: Optional[datetime] = None,
    ) -> AsyncGenerator[tuple[List[Content] | None, Optional[bool] | None], None]:
        """
        Crawl the content source and return an async generator of Content items.
        
        This method must be implemented by subclasses to define the
        specific crawling logic for the content source. It supports
        incremental crawling via checkpoints.
        
        Implementation Guidelines:
        - Use checkpoint_timestamp to filter content (e.g., modified_after=checkpoint)
        - Respect batch_size setting to limit items per crawl call
        - Return true in the second element if more results are available
        - Return None as false in the second element when all results are fetched
        
        Example implementation:
        ```python
        async def crawl(self, checkpoint_timestamp=None):
            self.current_checkpoint = checkpoint_timestamp
            
            # Query with checkpoint
            items = await self.source.query(
                modified_after=self.current_checkpoint,
                limit=self.batch_size
            )
            
            # Convert to Content objects
            content_items = [self._to_content(item) for item in items]
            
            # Determine if more results exist
            next_token = items.get_next_token()  # Hypothetical method            
            
            return content_items, next_token is not None
        ```
        
        Args:
            checkpoint_timestamp: Optional timestamp to fetch only content modified
                after this time. If None, uses last successful checkpoint or fetches all.
        
        Returns:
            A tuple containing:
            - List of Content items retrieved from the source (up to batch_size)
            - Optional bool indicating if more results are available, or None if complete
        """
        raise NotImplementedError("Subclasses must implement crawl method")
    
    # async def crawl_all(
    #     self,
    #     checkpoint_timestamp: Optional[datetime] = None
    # ) -> AsyncGenerator[List[Content], None]:
    #     """
    #     Crawl content from the source, handling pagination automatically and yielding batches.
        
    #     This async generator calls crawl() repeatedly and yields batches of content items
    #     up to batch_size. It continues until all content is fetched or max_items is reached.
        
    #     Example usage:
    #     ```python
    #     async for batch in executor.crawl_all():
    #         # Process batch of items
    #         await process_batch(batch)
    #     ```
        
    #     Args:
    #         checkpoint_timestamp: Optional timestamp to fetch only content modified
    #             after this time. If None, fetches all content.
                        
    #     Yields:
    #         Batches of Content items (up to batch_size per batch)
    #     """
    #     total_fetched = 0
    #     continuation_token: Optional[str] = None
        
    #     while True:
    #         # Check if we've reached max_results limit
    #         if self.max_results is not None and self.max_results > 0 and total_fetched >= self.max_results:
    #             if self.debug_mode:
    #                 logger.debug(f"Reached max results limit: {self.max_results}")
    #             break
            
    #         # Fetch next batch
    #         content_batch, continuation_token = await self.crawl(
    #             checkpoint_timestamp=checkpoint_timestamp,
    #             continuation_token=continuation_token
    #         )
            
    #         # Apply max_results limit to current batch if needed
    #         if self.max_results is not None and self.max_results > 0:
    #             remaining = self.max_results - total_fetched
    #             if len(content_batch) > remaining:
    #                 content_batch = content_batch[:remaining]
            
    #         if content_batch:
    #             total_fetched += len(content_batch)
                
    #             if self.debug_mode:
    #                 logger.debug(
    #                     f"Yielding batch of {len(content_batch)} items, "
    #                     f"total: {total_fetched}, "
    #                     f"has_more: {continuation_token is not None}"
    #                 )
                
    #             yield content_batch
            
    #         # Break if no more pages or we've applied max_items limit
    #         if continuation_token is None:
    #             break
            
    #     yield None # Indicate completion
    
    @abstractmethod
    async def process_input(
        self,
        input: Union[Content, List[Content]],
        ctx: WorkflowContext[Union[Content, List[Content]], Union[Content, List[Content]]]
    ) -> Union[Content, List[Content]]:
        """
        Process a single content item or a list of content items.
        
        This method must be implemented by subclasses to define the
        specific content processing logic.
        
        Args:
            input: The content item or list of content items to process
            ctx: The workflow execution context providing access to:
                - Shared state
                - Message passing capabilities
        
        Returns:
            The processed content item or a list of processed content items
            
        Raises:
            Exception: If processing fails and fail_on_error is True
        """
        raise NotImplementedError("Subclasses must implement process_input method")
