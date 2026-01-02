"""
Pipeline execution service for running and managing pipeline executions.
"""
import asyncio
import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, AsyncIterator
from pathlib import Path
import tempfile
import yaml

from azure.cosmos import exceptions as cosmos_exceptions

from app.models import (
    PipelineExecution,
    PipelineExecutionEvent,
    ExecutorOutput,
    ExecutionStatus,
    ExecutorStatus,
    Pipeline
)
from app.database.cosmos import CosmosDBClient
from .base_service import BaseService

# Import contentflow library components
from contentflow.pipeline import PipelineExecutor as ContentFlowPipelineExecutor
from contentflow.models import Content
from contentflow.utils import make_safe_json

logger = logging.getLogger("contentflow.api.services.pipeline_execution_service")


class PipelineExecutionService(BaseService):
    """Service for managing pipeline executions"""
    
    def __init__(self, cosmos: CosmosDBClient, container_name: str = "pipeline_executions"):
        super().__init__(cosmos, container_name)
        self._active_executions: Dict[str, asyncio.Task] = {}
        
    async def create_execution(
        self,
        pipeline: Pipeline,
        inputs: Optional[Dict[str, Any]] = None,
        configuration: Optional[Dict[str, Any]] = None,
        created_by: Optional[str] = None
    ) -> PipelineExecution:
        """Create a new pipeline execution record"""
        
        execution_id = f"exec_{uuid.uuid4().hex[:16]}"
        
        execution = PipelineExecution(
            id=execution_id,
            pipeline_id=pipeline.id,
            pipeline_name=pipeline.name,
            status=ExecutionStatus.PENDING,
            inputs=inputs or {},
            configuration=configuration or {},
            created_by=created_by,
            started_at=datetime.now(timezone.utc).isoformat()
        )
        
        # Save to database
        await self.create(execution.model_dump(exclude_none=False))
        
        logger.info(f"Created pipeline execution: {execution_id} for pipeline: {pipeline.name}")
        return execution
    
    async def get_execution(self, execution_id: str) -> Optional[PipelineExecution]:
        """Get execution by ID"""
        result = await self.get_by_id(execution_id)
        if result:
            return PipelineExecution(**result)
        return None
    
    async def update_execution_status(
        self,
        execution_id: str,
        status: ExecutionStatus,
        error: Optional[str] = None,
        outputs: Optional[Dict[str, Any]] = None
    ) -> None:
        """Update execution status"""
        
        execution = await self.get_execution(execution_id)
        if not execution:
            logger.warning(f"Execution {execution_id} not found for status update")
            return
        
        execution.status = status.value
        
        if status in [ExecutionStatus.COMPLETED, ExecutionStatus.FAILED, ExecutionStatus.CANCELLED]:
            execution.completed_at = datetime.now(timezone.utc).isoformat()
            
        if error:
            execution.error = error
            
        if outputs:
            execution.outputs = outputs
            
        await self.update(execution.model_dump(by_alias=True, exclude_none=False))
        logger.debug(f"Updated execution {execution_id} status to {status}")
    
    async def add_executor_output(
        self,
        execution_id: str,
        executor_output: ExecutorOutput
    ) -> None:
        """Add executor output to execution record"""
        execution = await self.get_execution(execution_id)
        if execution:
            execution.executor_outputs[executor_output.executor_id] = executor_output
            await self.update(execution.model_dump(by_alias=True, exclude_none=False))
    
    async def add_event(
        self,
        execution_id: str,
        event: PipelineExecutionEvent
    ) -> None:
        """Add event to execution record"""
        execution = await self.get_execution(execution_id)
        if execution:
            execution.events.append(event)
            # Keep only last 1000 events to avoid bloat
            if len(execution.events) > 1000:
                execution.events = execution.events[-1000:]
            await self.update(execution.model_dump(exclude_none=False))
    
    async def execute_pipeline_async(
        self,
        execution_id: str,
        pipeline: Pipeline,
    ) -> None:
        """Execute pipeline asynchronously (runs in background)"""
        
        try:
            logger.info(f"Starting async pipeline execution: {execution_id}")
            
            # Update status to running
            await self.update_execution_status(execution_id, ExecutionStatus.RUNNING)
            
            # Create temporary YAML file from pipeline definition
            with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
                yaml.dump(yaml.safe_load(pipeline.yaml), f)
                temp_yaml_path = f.name
            
            try:
                # Create pipeline executor from YAML
                async with ContentFlowPipelineExecutor.from_config_file(
                    config_path=temp_yaml_path,
                    pipeline_name=pipeline.name
                ) as executor:
                    
                    has_pipeline_failed = False
                    
                    # Execute and collect events
                    async for event in executor.execute_stream([]):
                        # Convert to our event model
                        exec_event = PipelineExecutionEvent(
                            event_type=event.event_type,
                            executor_id=event.executor_id,
                            timestamp=event.timestamp.isoformat(),
                            data=make_safe_json(event.data) if event.data is not None else None,
                            additional_info=make_safe_json(event.additional_info) if event.additional_info is not None else None,
                            error=make_safe_json(event.error) if event.error is not None else None
                        )
                        
                        logger.debug("-" * 80)
                        logger.debug(f"Execution {execution_id} event: \033[1;34m{event.event_type}\033[0m from executor: \033[1;34m{event.executor_id}\033[0m")
                        logger.debug("-" * 80)
                        
                        # Save event
                        if event.event_type != "Error":
                            
                            try:
                                await self.add_event(execution_id, exec_event)
                            except cosmos_exceptions.CosmosHttpResponseError as ce:
                                # check if it's due to request entity too large
                                if ce.status_code == 413:
                                    logger.warning(f"Event too large to store for execution {execution_id}, skipping event data storage.")
                                    exec_event.data = {"error": "Output data too large to store in Cosmos DB. View output saved by output executor(s)."}
                                    await self.add_event(execution_id, exec_event)
                                else:
                                    logger.error(f"Failed to add event to execution {execution_id}: {ce}", exc_info=False)
                                    
                        # Track executor status
                        if event.executor_id:
                            status = ExecutorStatus.RUNNING
                            
                            if event.event_type == "ExecutorCompletedEvent":
                                status = ExecutorStatus.COMPLETED
                            elif event.event_type == "ExecutorFailedEvent":
                                status = ExecutorStatus.FAILED
                            elif event.event_type == "ExecutorInvokedEvent":
                                status = ExecutorStatus.RUNNING
                                
                            executor_output = ExecutorOutput(
                                executor_id=event.executor_id,
                                timestamp=event.timestamp.isoformat(),
                                status=status,
                                data=make_safe_json(event.data) if event.data is not None else None,
                                error=make_safe_json(event.error) if event.error is not None else None
                            )
                            
                            try:
                                await self.add_executor_output(execution_id, executor_output)
                            except cosmos_exceptions.CosmosHttpResponseError as ce:
                                # check if it's due to request entity too large
                                if ce.status_code == 413:
                                    logger.warning(f"Output too large to store for execution {execution_id}, skipping event data storage.")
                                    executor_output.data = {"error": "Output data too large to store in Cosmos DB. View output saved by output executor(s)."}
                                    await self.add_executor_output(execution_id, executor_output)
                                else:
                                    logger.error(f"Failed to add event to execution {execution_id}: {ce}", exc_info=False)

                        if event.event_type == "WorkflowFailedEvent":
                            # Update execution status to failed
                            await self.update_execution_status(
                                execution_id,
                                ExecutionStatus.FAILED,
                                error=str(event.error.message) if event.error and hasattr(event.error, "message") else "Workflow failed"
                            )
                            has_pipeline_failed = True
                    
                    if not has_pipeline_failed:
                        # Mark as completed
                        await self.update_execution_status(
                            execution_id,
                            ExecutionStatus.COMPLETED
                        )
                    logger.info(f"Pipeline execution completed: {execution_id}")
                    
            finally:
                # Clean up temp file
                Path(temp_yaml_path).unlink(missing_ok=True)
                
        except Exception as e:
            logger.error(f"Pipeline execution failed: {execution_id}", exc_info=True)
            await self.update_execution_status(
                execution_id,
                ExecutionStatus.FAILED,
                error=str(e)
            )
        finally:
            # Remove from active executions
            if execution_id in self._active_executions:
                del self._active_executions[execution_id]
    
    async def stream_execution_events(
        self,
        execution_id: str
    ) -> AsyncIterator[PipelineExecutionEvent]:
        """Stream execution events in real-time"""
        
        # Get initial state
        execution = await self.get_execution(execution_id)
        if not execution:
            raise ValueError(f"Execution {execution_id} not found")
        
        # Send all existing events first
        for event in execution.events:
            yield event
        
        # If execution is completed/failed/cancelled, stop here
        if execution.status in [ExecutionStatus.COMPLETED, ExecutionStatus.FAILED, ExecutionStatus.CANCELLED]:
            return
        
        # Poll for new events
        last_event_count = len(execution.events)
        
        while True:
            await asyncio.sleep(0.5)  # Poll every 500ms
            
            execution = await self.get_execution(execution_id)
            if not execution:
                break
            
            # Yield new events
            new_events = execution.events[last_event_count:]
            for event in new_events:
                yield event
            
            last_event_count = len(execution.events)
            
            # Stop if execution completed
            if execution.status in [ExecutionStatus.COMPLETED, ExecutionStatus.FAILED, ExecutionStatus.CANCELLED]:
                break
    
    async def start_execution(
        self,
        execution_id: str,
        pipeline: Pipeline,
        inputs: Optional[Dict[str, Any]] = None,
        configuration: Optional[Dict[str, Any]] = None,
        created_by: Optional[str] = None
    ) -> str:
        """Start a pipeline execution and return execution ID"""
        
        # Start execution task in background
        task = asyncio.create_task(
            self.execute_pipeline_async(
                execution_id=execution_id,
                pipeline=pipeline
            )
        )
        
        self._active_executions[execution_id] = task
        
        return execution_id
    
    async def cancel_execution(self, execution_id: str) -> bool:
        """Cancel a running execution"""
        
        if execution_id in self._active_executions:
            task = self._active_executions[execution_id]
            task.cancel()
            
            await self.update_execution_status(
                execution_id,
                ExecutionStatus.CANCELLED
            )
            
            del self._active_executions[execution_id]
            logger.info(f"Cancelled execution: {execution_id}")
            return True
        
        return False
    
    async def get_execution_history(
        self,
        pipeline_id: Optional[str] = None,
        limit: Optional[int] = 10
    ) -> List[PipelineExecution]:
        """Get execution history"""
        
        if pipeline_id:
            query = "SELECT TOP @limit * FROM c WHERE c.pipeline_id = @pipeline_id ORDER BY c.started_at DESC"
            params = [{"name": "@pipeline_id", "value": pipeline_id}, {"name": "@limit", "value": limit}]
            results = await self.query(query=query, parameters=params)
        else:
            query = "SELECT TOP @limit * FROM c ORDER BY c.started_at DESC"
            params = [{"name": "@limit", "value": limit}]
            results = await self.query(query=query, parameters=params)
        
        return [PipelineExecution(**r) for r in results]
