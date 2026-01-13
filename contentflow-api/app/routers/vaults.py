import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.models import (
    Vault,
    VaultCreateRequest,
    VaultUpdateRequest,
    VaultExecution,
    VaultCrawlCheckpoint,
)
from app.services import VaultService, PipelineService, VaultExecutionService
from app.dependencies import get_vault_service, get_pipeline_service, get_vault_execution_service

router = APIRouter(prefix="/vaults", tags=["vaults"])

#region Vault management endpoints

@router.get("/", response_model=List[Vault])
async def list_vaults(
    search: Optional[str] = Query(None, description="Search by name or description"),
    tags: Optional[str] = Query(None, description="Comma-separated tags to filter by"),
    vault_service: VaultService = Depends(get_vault_service)
):
    """List all vaults with optional filtering"""
      
    try:
        tag_list = tags.split(",") if tags else None
        vaults = await vault_service.list_vaults(search=search, tags=tag_list)
        
        return vaults
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list vaults: {str(e)}")


@router.post("/", response_model=Vault, status_code=201)
async def create_vault(
    request: VaultCreateRequest,
    vault_service: VaultService = Depends(get_vault_service),
    pipeline_service: PipelineService = Depends(get_pipeline_service)
):
    """Create a new vault"""    
    try:
        # Verify pipeline exists
        pipeline = await pipeline_service.get_by_id(request.pipeline_id)
        if not pipeline:
            raise HTTPException(status_code=404, detail=f"Pipeline {request.pipeline_id} not found")
        
        vault = await vault_service.create_vault(request, pipeline_name=pipeline.get("name"))
        
        return vault
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Validation error creating vault: {e}")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{vault_id}", response_model=Vault)
async def get_vault(
    vault_id: str,
    vault_service: VaultService = Depends(get_vault_service)
):
    """Get a specific vault by ID"""
    try:
        vault = await vault_service.get_vault(vault_id)
        
        if not vault:
            raise HTTPException(status_code=404, detail=f"Vault {vault_id} not found")
        
        return vault
    
    except HTTPException:
        raise
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{vault_id}", response_model=Vault)
async def update_vault(
    vault_id: str,
    request: VaultUpdateRequest,
    vault_service: VaultService = Depends(get_vault_service),
    pipeline_service: PipelineService = Depends(get_pipeline_service)
):
    """Update a vault"""
    
    try:
        vault = await vault_service.update_vault(vault_id, request)
        
        if not vault:
            raise HTTPException(status_code=404, detail=f"Vault {vault_id} not found")
        
        return vault
    
    except HTTPException:
        raise
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{vault_id}")
async def delete_vault(
    vault_id: str,
    vault_service: VaultService = Depends(get_vault_service)
):
    """Delete a vault and all its content"""
    
    try:
        result = await vault_service.delete_vault(vault_id)
        
        if not result:
            raise HTTPException(status_code=404, detail=f"Vault {vault_id} not found")
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {"message": "Vault deleted successfully"}

#endregion Vault management endpoints

#region Vault execution endpoints

# Get Vault Executions
@router.get("/executions/{vault_id}", response_model=List[VaultExecution])
async def get_vault_executions(
    vault_id: str,
    start_date: Optional[str] = Query(None, description="Filter executions starting from this date (ISO format)"),
    end_date: Optional[str] = Query(None, description="Filter executions up to this date (ISO format)"),
    vault_exec_service: VaultExecutionService = Depends(get_vault_execution_service)
):
    """Get a specific vault by ID"""
    try:
        vault_executions = await vault_exec_service.get_vault_executions(vault_id, start_date=start_date, end_date=end_date)
        
        return vault_executions
    
    except HTTPException:
        raise
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Get Vault Crawl Checkpoints
@router.get("/crawl-checkpoints/{vault_id}", response_model=List[VaultCrawlCheckpoint])
async def get_vault_crawl_checkpoints(
    vault_id: str,
    vault_exec_service: VaultExecutionService = Depends(get_vault_execution_service)
):
    """Get crawl checkpoints for a specific vault by ID"""
    try:
        vault_checkpoints = await vault_exec_service.get_vault_crawl_checkpoints(vault_id)
        
        return vault_checkpoints
    
    except HTTPException:
        raise
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

#endregion Vault execution endpoints