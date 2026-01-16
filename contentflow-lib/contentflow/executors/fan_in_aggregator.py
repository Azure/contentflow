"""
Result aggregation executors.

This module provides executors that aggregate results from parallel
or batch processing operations.
"""

from datetime import datetime
import logging
from typing import Any, Callable, Dict, List, Optional, Union

from agent_framework import WorkflowContext, handler

from ..models import Content
from .base import BaseExecutor

logger = logging.getLogger("contentflow.executors.fan_in_aggregator")


class FanInAggregator(BaseExecutor):
    """
    Aggregate results from fan-in (join) edges.
    
    Collects content items from multiple parallel branches
    and aggregates them into a single content item or list of 
    content items based on canonical id of content.
    
    This executor provides a specific handler for fan-in edges in a workflow
    that accepts a list of content items or list of list of content items.
    
    The results from all incoming branches are merged into a single list
    of content items, merging content fields based on content ID.
    
    Configuration:
        No special configuration is required for this executor.

    Example:
        ```yaml
        - id: aggregator
          type: fan_in_aggregator
          settings:
            duplicate_field_merge_strategy: keep-one
        ```
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
        
        if self.debug_mode:
            logger.debug(
                f"Initialized FanInAggregator {self.id}, (enabled: {self.enabled})"
            )
    
    @handler
    async def handle_multiple_edge_input(
        self,
        input: Union[List[Content], List[List[Content]]],
        ctx: WorkflowContext[Union[Content, List[Content]], Union[Content, List[Content]]]
    ) -> Union[Content, List[Content]]:
        """
        Process a list of content items or list of list of content items.
        
        This method aggregates content items from multiple branches,
        merging them based on their canonical IDs according to the
        specified duplicate field merge strategy.
        
        Args:
            input: The list of content items or list of list of content items to process
            ctx: The workflow execution context providing access to:
                - Shared state
                - Message passing capabilities
        Returns:
            The aggregated list of content items
        aggregated_contents: Dict[str, Content] = {} 
        """
        if not self.enabled:
            if self.debug_mode:
                logger.info(f"Executor {self.id} is disabled, skipping execution.")
            
            # Send the original input unmodified downstream
            await ctx.send_message(input)
            
            # Yield the original input as output of this executor
            await ctx.yield_output(input)
            return
        
        start_time = datetime.now()
        
        try:
            if self.debug_mode:
                logger.debug(f"Executor {self.id} processing input: {input.id if isinstance(input, Content) else f'{len(input)} document(s)'}")
            
            # Call the abstract process_input method
            merged_content = await self._merge_content_batches(input)
            
            # Validate output
            if not isinstance(merged_content, Content) and not (isinstance(merged_content, list) and all(isinstance(doc, Content) for doc in merged_content)):
                raise TypeError(
                    f"Executor {self.id} must return a Content instance or a list of Content instances, "
                    f"got {type(merged_content)}"
                )
            
            # Update statistics
            elapsed = (datetime.now() - start_time).total_seconds()
            
            # Send the processed content item(s) downstream
            await ctx.send_message(merged_content)
            
            logger.info(
                    f"Executor {self.id} completed {input.id if isinstance(input, Content) else f'{len(input)} content item(s)'} "
                    f"in {elapsed:.2f}s"
                )
            
            # Yield the processed content item(s) as output
            await ctx.yield_output(merged_content)
            
        except Exception as e:
            elapsed = (datetime.now() - start_time).total_seconds()
            
            logger.error(
                f"Executor {self.id} failed processing input {input.id if isinstance(input, Content) else f'{len(input)} content item(s)'} "
                f"after {elapsed:.2f}s: {str(e)}",
                exc_info=True
            )
            
            if self.fail_pipeline_on_error:
                raise
            else:
                # Pass through the original document if error is not fatal
                await ctx.send_message(input)
                await ctx.yield_output(input)
            
    async def _merge_content_batches(
        self,
        input: Union[List[Content], List[List[Content]]]
    ) -> Union[Content, List[Content]]:
        """
        Merge content batches.
        
        This method merges multiple content items based on their canonical IDs.
        Items are merged based on the field names, where the first occurrence
        of a field based on it's name is kept.
        
        Args:
            input: The list of content items or list of list of content items to merge
        
        Returns:
            The merged content item or list of content items
        """
        
        content_items: List[Content] = []
        # Process input if it's a list of lists
        if all(isinstance(item, list) for item in input):
            # the input is List[List[Content]]
            for content_list in input:
                content_items.extend(content_list)
        else:
            # the input is List[Content]
            content_items = input  # type: ignore
        
        # Aggregate contents by canonical ID
        aggregated_contents: Dict[str, Content] = {}
        
        for idx, content in enumerate(content_items):
            content_id = content.id.canonical_id
            if content_id not in aggregated_contents:
                aggregated_contents[content_id] = content
            else:
                # Merge content fields based on the specified strategy
                existing_content = aggregated_contents[content_id]
                
                # merge summary data fields
                for field, value in content.summary_data.items():
                    if field not in existing_content.summary_data:
                        existing_content.summary_data[field] = value
                    
                
                # merge data fields
                for field, value in content.data.items():
                    if field not in existing_content.data:
                        existing_content.data[field] = value
        
        # Return aggregated contents as a list
        return list(aggregated_contents.values())
    
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
        raise NotImplementedError("This method is not implemented, the other handler method should be used.")