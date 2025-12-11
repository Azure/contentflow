from typing import List, Optional
from pydantic import BaseModel, Field

from fastapi import APIRouter, Depends, HTTPException

from app.models import Pipeline
from app.services.pipeline_service import PipelineService
from app.dependencies import get_pipeline_service

router = APIRouter(prefix="/api/pipelines", tags=["pipelines"])

# region API models

class SavePipelineRequest(BaseModel):
    """Request to create a new pipeline"""
    id: Optional[str] = None # Must be provided for update operations
    name: str
    description: Optional[str] = None
    yaml: str
    tags: Optional[List[str]] = []
    # settings
    enabled: Optional[bool] = True
    retry_delay: Optional[int] = 5 # in seconds
    timeout: Optional[int] = 600  # in seconds
    retries: Optional[int] = 3


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
        raise HTTPException(status_code=400, detail=f"Failed to delete pipeline: {str(e)}")
    
    return {"message": "Pipeline deleted successfully"}