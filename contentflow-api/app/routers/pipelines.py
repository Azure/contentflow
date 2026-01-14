import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.responses import StreamingResponse

from app.models import Pipeline, PipelineExecution, PipelineExecutionEvent
from app.services.pipeline_service import PipelineService
from app.services.pipeline_execution_service import PipelineExecutionService
from app.dependencies import get_pipeline_service, get_pipeline_execution_service

router = APIRouter(prefix="/pipelines", tags=["pipelines"])

# region API models

class SavePipelineRequest(BaseModel):
    """Request to create a new pipeline"""
    id: Optional[str] = None # Must be provided for update operations
    name: str
    description: Optional[str] = None
    yaml: str
    nodes: Optional[List[Any]] = None
    edges: Optional[List[Any]] = None
    tags: Optional[List[str]] = []
    # settings
    enabled: Optional[bool] = True
    retry_delay: Optional[int] = 5 # in seconds
    timeout: Optional[int] = 600  # in seconds
    retries: Optional[int] = 3


class ExecutePipelineRequest(BaseModel):
    """Request to execute a pipeline"""
    inputs: Optional[Dict[str, Any]] = None
    configuration: Optional[Dict[str, Any]] = None


class ExecutePipelineResponse(BaseModel):
    """Response for pipeline execution"""
    execution_id: str
    status: str
    message: str


# end region API models

# region API endpoints

@router.get("/", response_model=List[Pipeline])
async def get_pipelines(service: PipelineService = Depends(get_pipeline_service)):
    """List all pipelines"""
    return await service.get_pipelines()

@router.get("/{pipeline_id_or_name}", response_model=Pipeline)
async def get_pipeline(pipeline_id_or_name: str, service: PipelineService = Depends(get_pipeline_service)):
    """Get a specific pipeline by ID or by Name"""
    pipeline = await service.get_pipeline_by_id(pipeline_id_or_name)
    if not pipeline:
        pipeline = await service.get_pipeline_by_name(pipeline_id_or_name)
    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    
    return pipeline

@router.post("/", response_model=Pipeline)
async def save_pipeline(pipeline_data: SavePipelineRequest, service: PipelineService = Depends(get_pipeline_service)):
    """Create a new pipeline"""
    try:
        created_pipeline = await service.create_or_save_pipeline(pipeline_data.model_dump())
        return created_pipeline
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to create pipeline: {str(e)}")

@router.delete("/{pipeline_id}")
async def delete_pipeline(pipeline_id: str, service: PipelineService = Depends(get_pipeline_service)):
    """Delete a pipeline"""
    try:
        success = await service.delete_pipeline_by_id(pipeline_id)
        if not success:
            raise HTTPException(status_code=404, detail="Pipeline instance not found")
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Attemp to delete pipeline failed. {str(e)}")
    
    return {"message": "Pipeline deleted successfully"}


@router.post("/{pipeline_id}/execute", response_model=ExecutePipelineResponse)
async def execute_pipeline(
    pipeline_id: str,
    request: ExecutePipelineRequest,
    background_tasks: BackgroundTasks,
    pipeline_service: PipelineService = Depends(get_pipeline_service),
    execution_service: PipelineExecutionService = Depends(get_pipeline_execution_service)
):
    """Execute a pipeline"""
    
    # Get pipeline
    pipeline = await pipeline_service.get_pipeline_by_id(pipeline_id)
    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    
    if not pipeline.enabled:
        raise HTTPException(status_code=400, detail="Pipeline is disabled")
    
    try:
        
        # Start execution
        
        # Create execution record
        execution = await execution_service.create_execution(
            pipeline=pipeline,
            inputs=request.inputs,
            configuration=request.configuration,
            created_by=None  # TODO: get user from auth
        )
        
        # Execute pipeline in background
        _executor_function = execution_service.start_execution
        background_tasks.add_task(
            _executor_function,
            execution_id=execution.id,
            pipeline=pipeline,
            inputs=request.inputs,
            configuration=request.configuration
        )
        
        # execution_id = await execution_service.start_execution(
        #     pipeline=pipeline,
        #     inputs=request.inputs,
        #     configuration=request.configuration
        # )
        
        return ExecutePipelineResponse(
            execution_id=execution.id,
            status="started",
            message=f"Pipeline execution started with ID: {execution.id}"
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start pipeline execution: {str(e)}")


@router.get("/executions/{execution_id}", response_model=PipelineExecution)
async def get_execution_status(
    execution_id: str,
    execution_service: PipelineExecutionService = Depends(get_pipeline_execution_service)
):
    """Get pipeline execution status"""
    
    execution = await execution_service.get_execution(execution_id)
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")
    
    return execution


@router.get("/executions/{execution_id}/stream")
async def stream_execution_events(
    execution_id: str,
    execution_service: PipelineExecutionService = Depends(get_pipeline_execution_service)
):
    """Stream pipeline execution events using Server-Sent Events (SSE)"""
    
    # Verify execution exists
    execution = await execution_service.get_execution(execution_id)
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")
    
    def to_sse_format(event: PipelineExecutionEvent) -> str:
        """Format event for SSE transmission"""
        data_json = event.model_dump_json()
        return f"data: {data_json}\n\n"
    
    async def event_generator():
        """Generate SSE events"""
        try:
            async for event in execution_service.stream_execution_events(execution_id):
                # Convert event to sse format
                yield to_sse_format(event)
        except Exception as e:
            error_data = f'data: {{"type": "error", "message": "Stream error: {str(e)}", "data":  {{"error": "{str(e)}", "error_type": "{type(e).__name__}"}} , "timestamp": "{datetime.now(datetime.timezone.utc).isoformat()}"}}\n\n'
            yield error_data
    
    return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",  # Disable buffering in nginx
                "Access-Control-Allow-Origin": "*",  # Allow CORS for SSE
                "Access-Control-Allow-Credentials": "true"
            }
        )


@router.post("/executions/{execution_id}/cancel")
async def cancel_execution(
    execution_id: str,
    execution_service: PipelineExecutionService = Depends(get_pipeline_execution_service)
):
    """Cancel a running pipeline execution"""
    
    success = await execution_service.cancel_execution(execution_id)
    if not success:
        raise HTTPException(status_code=404, detail="Execution not found or already completed")
    
    return {"message": "Execution cancelled successfully"}


@router.get("/{pipeline_id}/executions", response_model=List[PipelineExecution])
async def get_pipeline_executions(
    pipeline_id: str,
    limit: Optional[int] = None,
    execution_service: PipelineExecutionService = Depends(get_pipeline_execution_service)
):
    """Get execution history for a pipeline"""
    
    return await execution_service.get_execution_history(pipeline_id=pipeline_id, limit=limit)