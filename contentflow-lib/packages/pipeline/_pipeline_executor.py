"""
Pipeline executor for managing pipeline execution and output capture.

This module provides the PipelineExecutor class that handles:
- Loading pipelines from configuration
- Executing pipelines with proper context
- Capturing pipeline outputs and events
- Managing pipeline lifecycle
"""

import logging
from typing import Any, Dict, List, Optional, AsyncIterator, Union, cast
from pathlib import Path
from datetime import datetime, timezone
from enum import Enum
from pydantic import BaseModel, Field

from agent_framework import Workflow, WorkflowRunResult, WorkflowOutputEvent

from ..models import Content
from .pipeline_factory import PipelineFactory
from ._pipeline import PipelineEvent, PipelineResult, PipelineStatus

logger = logging.getLogger("contentflow.lib.pipeline.executor")

class PipelineExecutor:
    """
    Executor for running pipelines and capturing outputs.
    
    This class provides:
    - Loading pipelines from configuration files
    - Executing pipelines with document inputs
    - Capturing events and outputs
    - Managing pipeline lifecycle (initialization, execution, cleanup)
    - Result aggregation and reporting
    
    Example:
        ```python
        # Create executor from config
        executor = PipelineExecutor.from_config_file(
            config_path="pipeline_config.yaml",
            pipeline_name="document_processing"
        )
        
        # Initialize
        await executor.initialize()
        
        # Execute pipeline
        result = await executor.execute(document)
        
        # Check results
        print(f"Status: {result.status}")
        print(f"Duration: {result.duration_seconds}s")
        print(f"Events: {len(result.events)}")
        
        # Cleanup
        await executor.cleanup()
        ```
    
    Example (with context manager):
        ```python
        async with PipelineExecutor.from_config_file(
            config_path="pipeline_config.yaml",
            pipeline_name="document_processing"
        ) as executor:
            result = await executor.execute(document)
        ```
    """
    
    def __init__(
        self,
        factory: PipelineFactory,
        pipeline_name: str,
        pipeline: Optional[Workflow] = None,
        auto_initialize: bool = True
    ):
        """
        Initialize the pipeline executor.
        
        Args:
            factory: PipelineFactory instance
            pipeline_name: Name of the pipeline to execute
            pipeline: Pre-created Workflow instance (optional, internal implementation detail)
            auto_initialize: Whether to auto-initialize on first execute
        """
        self.factory = factory
        self.pipeline_name = pipeline_name
        self._pipeline = pipeline
        self.auto_initialize = auto_initialize
        
        self._initialized = False
        self._events: List[PipelineEvent] = []
        
        logger.info(f"PipelineExecutor created for pipeline: {pipeline_name}")
    
    @classmethod
    def from_config_file(
        cls,
        config_path: Union[str, Path],
        pipeline_name: str,
        executor_catalog_path: Optional[Union[str, Path]] = None,
        auto_initialize: bool = True
    ) -> "PipelineExecutor":
        """
        Create a PipelineExecutor from configuration file.
        
        Args:
            config_path: Path to pipeline configuration YAML
            pipeline_name: Name of the pipeline to execute
            executor_catalog_path: Optional path to executor catalog
            auto_initialize: Whether to auto-initialize on first execute
            
        Returns:
            Configured PipelineExecutor instance
        """
        logger.info(f"Creating PipelineExecutor from config: {config_path}")
        
        # Create factory
        factory = PipelineFactory.from_config_file(
            pipeline_config_path=config_path,
            executor_catalog_path=executor_catalog_path
        )
        
        # Create executor
        return cls(
            factory=factory,
            pipeline_name=pipeline_name,
            auto_initialize=auto_initialize
        )
    
    @classmethod
    async def from_config_file_initialized(
        cls,
        config_path: Union[str, Path],
        pipeline_name: str,
        executor_catalog_path: Optional[Union[str, Path]] = None,
    ) -> "PipelineExecutor":
        """
        Create and initialize a PipelineExecutor from configuration file.
        
        Args:
            config_path: Path to pipeline configuration YAML
            pipeline_name: Name of the pipeline to execute
            executor_catalog_path: Optional path to executor catalog
            
        Returns:
            Initialized PipelineExecutor instance
        """
        executor = cls.from_config_file(
            config_path=config_path,
            pipeline_name=pipeline_name,
            executor_catalog_path=executor_catalog_path,
            auto_initialize=False
        )
        
        await executor.initialize()
        return executor
    
    async def initialize(self) -> None:
        """
        Initialize the pipeline executor.
        
        This includes:
        - Initializing all connectors
        - Creating the pipeline instance
        """
        if self._initialized:
            logger.debug("PipelineExecutor already initialized")
            return
        
        logger.info(f"Initializing PipelineExecutor for: {self.pipeline_name}")
        
        # Create pipeline if not provided
        if self._pipeline is None:
            self._pipeline = await self.factory.create_pipeline(self.pipeline_name)
            logger.debug(f"Pipeline created: {self.pipeline_name}")
        
        self._initialized = True
        logger.info("PipelineExecutor initialization complete")
    
    async def cleanup(self) -> None:
        """
        Cleanup the pipeline executor.
        
        This includes:
        - Cleaning up all connectors
        - Clearing cached data
        """
        logger.info("Cleaning up PipelineExecutor")
                
        self._initialized = False
        logger.info("PipelineExecutor cleanup complete")
    
    async def execute(
        self,
        input: Union[Content, List[Content]],
        metadata: Optional[Dict[str, Any]] = None
    ) -> PipelineResult:
        """
        Execute the pipeline with a document.
        
        Args:
            input: Document or list of Documents to process
            metadata: Additional metadata to include in result
            
        Returns:
            PipelineResult with execution results
        """
        
        # Auto-initialize if needed
        if not self._initialized and self.auto_initialize:
            await self.initialize()

        if not self._initialized:
            raise RuntimeError(
                "PipelineExecutor not initialized. Call initialize() first or "
                "set auto_initialize=True"
            )

        logger.info(
            f"Executing pipeline '{self.pipeline_name}' for input of {len(input) if isinstance(input, list) else 1} document(s)."
        )

        # Track execution
        start_time = datetime.now(timezone.utc)
        status = PipelineStatus.RUNNING
        error_msg = None
        events: List[PipelineEvent] = []
        result = None

        try:
            # Execute
            result = input
        
            workflow_run_result : WorkflowRunResult = await self._pipeline.run(input)
            logger.debug(f"Workflow Run Result obtained...")

            events = [PipelineEvent(
                event_type=type(event).__name__,
                executor_id=event.executor_id if hasattr(event, "executor_id") else (event.source_executor_id if hasattr(event, "source_executor_id") else None),
                data=event.data if hasattr(event, "data") else {},
                error=None
            ) for event in workflow_run_result]
            
            # get the data from the last output event
            workflow_output_events = [event for event in workflow_run_result if isinstance(event, WorkflowOutputEvent)]
            if len(workflow_output_events) > 0:
                last_output_event = workflow_output_events[-1]
                if last_output_event.data:
                    result = last_output_event.data
                    if isinstance(result, Content):
                        result = cast(Content, result)
                    elif isinstance(result, list):
                        result = cast(List[Content], result)
                    
                    logger.debug(f"Extracted result with {len(result) if isinstance(result, list) else 1} document(s) from last output event. ")
            
            status = PipelineStatus.COMPLETED
            logger.info(f"Pipeline execution completed: {self.pipeline_name}")
        except Exception as e:
            status = PipelineStatus.FAILED
            error_msg = str(e)
            logger.error(
                f"Pipeline execution failed: {self.pipeline_name}",
                exc_info=True
            )

        # Calculate duration
        end_time = datetime.now(timezone.utc)
        duration = (end_time - start_time).total_seconds()

        # Create result
        result = PipelineResult(
            pipeline_name=self.pipeline_name,
            status=status,
            documents=result,
            events=events,
            start_time=start_time,
            end_time=end_time,
            duration_seconds=duration,
            error=error_msg,
            metadata=metadata or {}
        )

        logger.info(
            f"Pipeline execution result: status={status}, "
            f"duration={duration:.2f}s, events={len(events)}"
        )

        return result
    
    async def execute_stream(
        self,
        input: Union[Content, List[Content]],
    ) -> AsyncIterator[PipelineEvent]:
        """
        Execute pipeline and stream events as they occur.
        
        Args:
            input: Document or list of Documents to process
            
        Yields:
            PipelineEvent objects as they occur
        """
        # Auto-initialize if needed
        if not self._initialized and self.auto_initialize:
            await self.initialize()
        
        if not self._initialized:
            raise RuntimeError("PipelineExecutor not initialized")
        
        logger.info(f"Streaming pipeline execution: {self.pipeline_name}")
        
        try:
            async for event in self._pipeline.run_stream(input):
                # Create pipeline event
                pipeline_event = PipelineEvent(
                    event_type=type(event).__name__,
                    executor_id=event.executor_id if hasattr(event, "executor_id") else (event.source_executor_id if hasattr(event, "source_executor_id") else None),
                    data=event.data if hasattr(event, "data") else {},
                    error=None
                )
                
                # Yield event
                yield pipeline_event

        except Exception as e:
            # Yield error event
            error_event = PipelineEvent(
                event_type="error",
                error=str(e),
                data={"exception": type(e).__name__}
            )
            
            yield error_event
    
    def get_pipeline_info(self) -> Dict[str, Any]:
        """
        Get information about the pipeline.
        
        Returns:
            Dict with pipeline information
        """
        return {
            "pipeline_name": self.pipeline_name,
            "initialized": self._initialized,
            "cached_events": len(self._events),
            "factory_info": {
                "pipelines": self.factory.get_pipeline_names(),
            }
        }
    
    async def __aenter__(self) -> "PipelineExecutor":
        """Async context manager entry."""
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self.cleanup()
