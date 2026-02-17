"""ForEachContent executor for inline per-item processing with chained executor steps."""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from agent_framework import WorkflowContext

from .base import BaseExecutor
from .executor_config import ExecutorInstanceConfig
from ..models import Content, ExecutorLogEntry

logger = logging.getLogger("contentflow.executors.for_each_content")


class ForEachContentExecutor(BaseExecutor):
    """
    Iterate over a List[Content] and apply an inline chain of executor
    steps to each item, with parallel execution and concurrency control.
    
    This executor acts as an inline loop boundary within a single pipeline,
    eliminating the need for sub-pipelines when per-document processing is
    a simple sequential chain of steps.
    
    Each content item flows through the declared steps sequentially:
        item → step1.process_input() → step2.process_input() → ... → result
    
    Items are processed in parallel up to max_concurrent. The original
    List[Content] ordering is preserved in the output.
    
    Configuration (settings dict):
        - steps (list[dict]): Ordered list of executor step definitions.
          Each dict has the same schema as a top-level executor definition:
          {id: str, type: str, settings: dict}
          Required: True
        - max_concurrent (int): Maximum number of items processed in parallel.
          Default: 5
        - timeout_per_item_secs (int): Timeout for processing a single item
          through all steps, in seconds.
          Default: 300
        - continue_on_error (bool): Continue processing remaining items if
          one fails. Failed items pass through with their original data.
          Default: True
        - preserve_order (bool): Return results in the same order as input.
          Default: True
        
        Also settings from BaseExecutor apply.
    
    Example:
        ```yaml
        - id: process_each_doc
          type: for_each_content
          settings:
            max_concurrent: 4
            timeout_per_item_secs: 600
            continue_on_error: false
            steps:
              - id: retrieve
                type: content_retriever
                settings:
                  blob_storage_account: "${STORAGE_ACCOUNT}"
                  blob_container_name: "reports"
              - id: extract
                type: pdf_extractor
                settings:
                  extract_tables: true
              - id: analyze
                type: ai_analysis
                settings:
                  endpoint: "${AZURE_OPENAI_ENDPOINT}"
                  deployment_name: "gpt-4.1"
        ```
    
    Input:
        Union[Content, List[Content]] — content items to iterate over.
        A single Content is wrapped in a list automatically.
        
    Output:
        List[Content] — processed content items in the same order as input.
        Each item has been passed through all declared steps sequentially.
        ExecutorLogEntry records are appended for each step and for the
        overall for_each_content execution.
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
        
        self.steps: List[Dict[str, Any]] = self.get_setting("steps", required=True)
        self.max_concurrent: int = self.get_setting("max_concurrent", default=5)
        self.timeout_per_item_secs: int = self.get_setting("timeout_per_item_secs", default=300)
        self.continue_on_error: bool = self.get_setting("continue_on_error", default=True)
        self.preserve_order: bool = self.get_setting("preserve_order", default=True)
        
        if not self.steps or not isinstance(self.steps, list):
            raise ValueError(
                f"{self.id}: 'steps' must be a non-empty list of executor definitions. "
                f"Each step must have 'id' and 'type' keys."
            )
        
        # Validate step definitions
        for i, step_def in enumerate(self.steps):
            if not isinstance(step_def, dict):
                raise ValueError(
                    f"{self.id}: Step {i} must be a dict with 'id' and 'type' keys, "
                    f"got {type(step_def).__name__}"
                )
            if "id" not in step_def or "type" not in step_def:
                raise ValueError(
                    f"{self.id}: Step {i} must have 'id' and 'type' keys. "
                    f"Got keys: {list(step_def.keys())}"
                )
        
        # Inner executor instances — built lazily on first use via _ensure_inner_executors()
        self._inner_executors: Optional[List[BaseExecutor]] = None
        
        if self.debug_mode:
            step_ids = [s["id"] for s in self.steps]
            logger.debug(
                f"Initialized ForEachContentExecutor {self.id} with "
                f"{len(self.steps)} steps: {step_ids}, "
                f"max_concurrent={self.max_concurrent}, "
                f"timeout_per_item_secs={self.timeout_per_item_secs}, "
                f"continue_on_error={self.continue_on_error}"
            )
    
    def _ensure_inner_executors(self) -> List[BaseExecutor]:
        """
        Lazily build inner executor instances from step definitions.
        
        Uses the ExecutorRegistry to dynamically instantiate each step's
        executor class. The registry is loaded from the default catalog.
        
        Returns:
            List of instantiated executor instances in step order.
            
        Raises:
            ValueError: If a step's executor type is not found in the registry.
        """
        if self._inner_executors is not None:
            return self._inner_executors
        
        from .executor_registry import ExecutorRegistry
        
        registry = ExecutorRegistry.load_default_catalog()
        
        executors = []
        for step_def in self.steps:
            step_id = step_def["id"]
            step_type = step_def["type"]
            step_settings = step_def.get("settings", {})
            
            if step_type not in registry:
                raise ValueError(
                    f"{self.id}: Step '{step_id}' references executor type "
                    f"'{step_type}' which is not found in the executor catalog. "
                    f"Available types: {registry.list_executor_ids()[:20]}..."
                )
            
            instance_config = ExecutorInstanceConfig(
                id=f"{self.id}.{step_id}",
                type=step_type,
                settings=step_settings
            )
            
            executor = registry.create_executor_instance(
                executor_id=step_type,
                instance_config=instance_config
            )
            executors.append(executor)
            
            if self.debug_mode:
                logger.debug(
                    f"{self.id}: Built inner executor '{step_id}' "
                    f"(type={step_type}, class={executor.__class__.__name__})"
                )
        
        self._inner_executors = executors
        logger.info(
            f"{self.id}: Initialized {len(executors)} inner executors: "
            f"{[s['id'] for s in self.steps]}"
        )
        return executors
    
    async def process_input(
        self,
        input: Union[Content, List[Content]],
        ctx: WorkflowContext[Union[Content, List[Content]], Union[Content, List[Content]]]
    ) -> Union[Content, List[Content]]:
        """
        Process each content item through the inline executor chain.
        
        Args:
            input: Content item or list of content items to process.
            ctx: Workflow context.
            
        Returns:
            List[Content] with each item processed through all steps.
        """
        overall_start = datetime.now()
        
        # Normalize to list
        if isinstance(input, Content):
            items = [input]
        else:
            items = list(input)
        
        if not items:
            logger.warning(f"{self.id}: Received empty input list, returning empty.")
            return []
        
        # Build inner executors on first use
        logger.debug(f"{self.id}: Starting ForEachContent processing for {len(items)} item(s)")
        logger.debug(f"{self.id}: Loading inner executors...")
        inner_executors = self._ensure_inner_executors()
        
        total_items = len(items)
        logger.info(
            f"{self.id}: Processing {total_items} item(s) through "
            f"{len(inner_executors)} step(s) with max_concurrent={self.max_concurrent}"
        )
        
        # Process items in parallel with concurrency control
        semaphore = asyncio.Semaphore(self.max_concurrent)
        
        async def process_one_item(index: int, content: Content) -> Union[Content, List[Content]]:
            """Process a single content item through all inner executor steps."""
            async with semaphore:
                return await self._process_item_through_steps(
                    index, content, inner_executors, ctx
                )
        
        tasks = [
            process_one_item(i, item) 
            for i, item in enumerate(items)
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Collect results, handling errors
        processed: List[Content] = []
        errors: List[Dict[str, Any]] = []
        
        for i, result in enumerate(results):
            if isinstance(result, BaseException):
                error_detail = {
                    "item_index": i,
                    "canonical_id": items[i].id.canonical_id if items[i].id else "unknown",
                    "error": str(result),
                    "error_type": type(result).__name__,
                }
                errors.append(error_detail)
                
                logger.error(
                    f"{self.id}: Item {i} "
                    f"({items[i].id.canonical_id if items[i].id else 'unknown'}) "
                    f"failed: {result}"
                )
                
                if not self.continue_on_error:
                    raise result
                
                # Pass through original item on error
                items[i].executor_logs.append(ExecutorLogEntry(
                    executor_id=self.id,
                    start_time=overall_start,
                    end_time=datetime.now(),
                    status="failed",
                    details={"item_index": i, "step_count": len(inner_executors)},
                    errors=[str(result)]
                ))
                processed.append(items[i])
            else:
                if isinstance(result, list):
                    processed.extend([r for r in result if isinstance(r, Content)])
                elif isinstance(result, Content):
                    processed.append(result)
        
        overall_elapsed = (datetime.now() - overall_start).total_seconds()
        
        succeeded = total_items - len(errors)
        logger.info(
            f"{self.id}: Completed processing {total_items} item(s) in "
            f"{overall_elapsed:.2f}s — {succeeded} succeeded, {len(errors)} failed"
        )
        
        if errors and self.debug_mode:
            for err in errors:
                logger.debug(
                    f"{self.id}: Failed item {err['item_index']} "
                    f"({err['canonical_id']}): [{err['error_type']}] {err['error']}"
                )
        
        return processed
    
    async def _process_item_through_steps(
        self,
        index: int,
        content: Content,
        executors: List[BaseExecutor],
        ctx: WorkflowContext
    ) -> Union[Content, List[Content]]:
        """
        Run a single content item through all inner executor steps sequentially.
        
        Applies a per-item timeout across all steps. Each step's process_input()
        is called directly, bypassing the Agent Framework's handle_content routing.
        
        Args:
            index: Item index in the original list (for logging).
            content: The content item to process.
            executors: Ordered list of inner executor instances.
            ctx: Workflow context.
            
        Returns:
            The content item or list of content items after all steps have been applied.
            
        Raises:
            asyncio.TimeoutError: If per-item processing exceeds timeout.
            Exception: Any unhandled error from a step executor.
        """
        item_start = datetime.now()
        item_id = content.id.canonical_id if content.id else f"item_{index}"
        
        if self.debug_mode:
            logger.debug(
                f"{self.id}: Starting item {index} ({item_id}) "
                f"through {len(executors)} step(s)"
            )
        
        async def _run_steps() -> Union[Content, List[Content]]:
            
            result = content
            for step_idx, executor in enumerate(executors):
                step_id = self.steps[step_idx]["id"]
                step_start = datetime.now()
                
                if self.debug_mode:
                    logger.debug(
                        f"{self.id}: Item {index} ({item_id}) → "
                        f"step {step_idx + 1}/{len(executors)}: {step_id}"
                    )
                
                try:
                    step_result = await executor.process_input(result, ctx)
                    
                    # # Normalize: per-item executors should return Content.
                    # # If a step returns a list (e.g. a ParallelExecutor-based
                    # # executor given a single Content), take the first item.
                    # if isinstance(step_result, list):
                    #     if len(step_result) == 1:
                    #         step_result = step_result[0]
                    #     elif len(step_result) > 1:
                    #         # Multiple outputs from a single input — take first,
                    #         # log a warning for visibility
                    #         logger.warning(
                    #             f"{self.id}: Step '{step_id}' returned "
                    #             f"{len(step_result)} items for a single input. "
                    #             f"Using first item only."
                    #         )
                    #         step_result = step_result[0]
                    #     else:
                    #         raise ValueError(
                    #             f"Step '{step_id}' returned an empty list "
                    #             f"for item {index} ({item_id})"
                    #         )
                    
                    step_elapsed = (datetime.now() - step_start).total_seconds()
                    
                    if isinstance(step_result, list):
                        for i, r in enumerate(step_result):
                            if isinstance(r, Content):
                                r.executor_logs.append(ExecutorLogEntry(
                                    executor_id=f"{self.id}.{step_id}",
                                    start_time=step_start,
                                    end_time=datetime.now(),
                                    status="completed",
                                    details={
                                        "for_each_parent": self.id,
                                        "item_index": index,
                                        "step_index": step_idx,
                                        "step_type": self.steps[step_idx]["type"],
                                        "list_index": i,
                                    },
                                    errors=[]
                                ))
                    else:
                        # Append step log entry to the content item
                        step_result.executor_logs.append(ExecutorLogEntry(
                            executor_id=f"{self.id}.{step_id}",
                            start_time=step_start,
                            end_time=datetime.now(),
                            status="completed",
                            details={
                                "for_each_parent": self.id,
                                "item_index": index,
                                "step_index": step_idx,
                                "step_type": self.steps[step_idx]["type"],
                            },
                            errors=[]
                        ))
                    
                    if self.debug_mode:
                        logger.debug(
                            f"{self.id}: Item {index} ({item_id}) ← "
                            f"step {step_id} completed in {step_elapsed:.2f}s"
                        )
                    
                    result = step_result
                    
                except Exception as e:
                    step_elapsed = (datetime.now() - step_start).total_seconds()
                    logger.error(
                        f"{self.id}: Item {index} ({item_id}) failed at "
                        f"step '{step_id}' after {step_elapsed:.2f}s: {e}",
                        exc_info=True
                    )
                    
                    # Log the failure on the content item
                    if isinstance(result, list):
                        for i, r in enumerate(result):
                            if isinstance(r, Content):
                                r.executor_logs.append(ExecutorLogEntry(
                                    executor_id=f"{self.id}.{step_id}",
                                    start_time=step_start,
                                    end_time=datetime.now(),
                                    status="failed",
                                    details={
                                        "for_each_parent": self.id,
                                        "item_index": index,
                                        "step_index": step_idx,
                                        "step_type": self.steps[step_idx]["type"],
                                        "list_index": i,
                                    },
                                    errors=[str(e)]
                                ))
                    else:
                        result.executor_logs.append(ExecutorLogEntry(
                            executor_id=f"{self.id}.{step_id}",
                            start_time=step_start,
                            end_time=datetime.now(),
                            status="failed",
                            details={
                                "for_each_parent": self.id,
                                "item_index": index,
                                "step_index": step_idx,
                                "step_type": self.steps[step_idx]["type"],
                            },
                            errors=[str(e)]
                        ))
 
                    raise
            
            return result
        
        # Apply per-item timeout
        try:
            result = await asyncio.wait_for(
                _run_steps(),
                timeout=self.timeout_per_item_secs
            )
        except asyncio.TimeoutError:
            item_elapsed = (datetime.now() - item_start).total_seconds()
            raise asyncio.TimeoutError(
                f"{self.id}: Item {index} ({item_id}) timed out after "
                f"{item_elapsed:.2f}s (limit: {self.timeout_per_item_secs}s)"
            )
        
        # Append overall for_each log entry for this item
        item_elapsed = (datetime.now() - item_start).total_seconds()
        
        if isinstance(result, list):
            for i, r in enumerate(result):
                if isinstance(r, Content):
                    r.executor_logs.append(ExecutorLogEntry(
                        executor_id=self.id,
                        start_time=item_start,
                        end_time=datetime.now(),
                        status="completed",
                        details={
                            "item_index": index,
                            "steps_completed": len(executors),
                            "duration_seconds": item_elapsed,
                            "list_index": i,
                        },
                        errors=[]
                    ))
        else:
            result.executor_logs.append(ExecutorLogEntry(
                executor_id=self.id,
                start_time=item_start,
                end_time=datetime.now(),
                status="completed",
                details={
                    "item_index": index,
                    "steps_completed": len(executors),
                    "duration_seconds": item_elapsed,
                },
                errors=[]
            ))
        
        if self.debug_mode:
            logger.debug(
                f"{self.id}: Item {index} ({item_id}) completed "
                f"all {len(executors)} step(s) in {item_elapsed:.2f}s"
            )
        
        return result
