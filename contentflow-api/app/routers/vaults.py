import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.models import (
    Vault,
    VaultCreateRequest,
    VaultUpdateRequest,
)
from app.services.vault_service import VaultService
from app.services.pipeline_service import PipelineService
from app.dependencies import get_vault_service, get_pipeline_service

router = APIRouter(prefix="/vaults", tags=["vaults"])

# Vault management endpoints

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
        # If pipeline_id is being updated, verify it exists
        if request.pipeline_id:
            pipeline = await pipeline_service.get_by_id(request.pipeline_id)
            if not pipeline:
                raise HTTPException(status_code=404, detail=f"Pipeline {request.pipeline_id} not found")
        
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


@router.delete("/{vault_id}", status_code=204)
async def delete_vault(
    vault_id: str,
    vault_service: VaultService = Depends(get_vault_service)
):
    """Delete a vault and all its content"""
    
    try:
        result = await vault_service.delete_vault(vault_id)
        
        if not result:
            raise HTTPException(status_code=404, detail=f"Vault {vault_id} not found")
        
        return None
    
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# # Content management endpoints

# @router.get("/{vault_id}/content", response_model=List[VaultContentResponse])
# async def list_vault_content(
#     vault_id: str,
#     status: Optional[str] = Query(None, description="Filter by status (pending, processing, ready, error)"),
#     search: Optional[str] = Query(None, description="Search by file name"),
#     vault_service: VaultService = Depends(get_vault_service)
# ):
#     """List content in a vault"""
#     logger.info(f"Listing content for vault: {vault_id}")
    
#     try:
#         # Verify vault exists
#         vault = await vault_service.get_vault(vault_id)
#         if not vault:
#             raise HTTPException(status_code=404, detail=f"Vault {vault_id} not found")
        
#         content_items = await vault_service.list_vault_content(vault_id, status=status, search=search)
        
#         return [_content_to_response(content) for content in content_items]
    
#     except HTTPException:
#         raise
    
#     except Exception as e:
#         logger.error(f"Error listing vault content: {e}")
#         raise HTTPException(status_code=500, detail=str(e))


# @router.post("/{vault_id}/content/upload", response_model=VaultContentResponse, status_code=201)
# async def upload_content(
#     vault_id: str,
#     file: UploadFile = File(...),
#     vault_service: VaultService = Depends(get_vault_service)
# ):
#     """Upload content to a vault"""
#     logger.info(f"Uploading content to vault: {vault_id}")
    
#     try:
#         # Verify vault exists
#         vault = await vault_service.get_vault(vault_id)
#         if not vault:
#             raise HTTPException(status_code=404, detail=f"Vault {vault_id} not found")
        
#         # Read file
#         file_content = await file.read()
#         file_size = len(file_content)
        
#         # TODO: Upload to blob storage and get URL
#         # For now, we'll just record the metadata
#         blob_path = f"vaults/{vault_id}/{file.filename}"
#         blob_url = None  # Would be set after blob upload
        
#         content = await vault_service.upload_content(
#             vault_id=vault_id,
#             file_name=file.filename,
#             content_type=file.content_type or "application/octet-stream",
#             size_bytes=file_size,
#             blob_path=blob_path,
#             blob_url=blob_url
#         )
        
#         return _content_to_response(content)
    
#     except HTTPException:
#         raise
    
#     except Exception as e:
#         logger.error(f"Error uploading content: {e}")
#         raise HTTPException(status_code=500, detail=str(e))


# @router.get("/{vault_id}/content/{content_id}", response_model=VaultContentResponse)
# async def get_content(
#     vault_id: str,
#     content_id: str,
#     vault_service: VaultService = Depends(get_vault_service)
# ):
#     """Get specific content details"""
#     logger.info(f"Getting content {content_id} from vault {vault_id}")
    
#     try:
#         content = await vault_service.get_content(vault_id, content_id)
        
#         if not content:
#             raise HTTPException(status_code=404, detail=f"Content {content_id} not found in vault {vault_id}")
        
#         return _content_to_response(content)
    
#     except HTTPException:
#         raise
    
#     except Exception as e:
#         logger.error(f"Error getting content: {e}")
#         raise HTTPException(status_code=500, detail=str(e))


# @router.delete("/{vault_id}/content/{content_id}", status_code=204)
# async def delete_content(
#     vault_id: str,
#     content_id: str,
#     vault_service: VaultService = Depends(get_vault_service)
# ):
#     """Delete content from a vault"""
#     logger.info(f"Deleting content {content_id} from vault {vault_id}")
    
#     try:
#         result = await vault_service.delete_content(vault_id, content_id)
        
#         if not result:
#             raise HTTPException(status_code=404, detail=f"Content {content_id} not found in vault {vault_id}")
        
#         return None
    
#     except HTTPException:
#         raise
    
#     except Exception as e:
#         logger.error(f"Error deleting content: {e}")
#         raise HTTPException(status_code=500, detail=str(e))


# @router.patch("/{vault_id}/content/{content_id}/status")
# async def update_content_status(
#     vault_id: str,
#     content_id: str,
#     status: str = Query(..., description="New status (pending, processing, ready, error)"),
#     error_message: Optional[str] = Query(None, description="Error message if status is error"),
#     pipeline_execution_id: Optional[str] = Query(None, description="Pipeline execution ID"),
#     entities_extracted: Optional[int] = Query(None, description="Number of entities extracted"),
#     chunks_created: Optional[int] = Query(None, description="Number of chunks created"),
#     vault_service: VaultService = Depends(get_vault_service)
# ):
#     """Update content processing status (for internal use)"""
#     logger.info(f"Updating status for content {content_id} in vault {vault_id}")
    
#     try:
#         content = await vault_service.update_content_status(
#             vault_id=vault_id,
#             content_id=content_id,
#             status=status,
#             error_message=error_message,
#             pipeline_execution_id=pipeline_execution_id,
#             entities_extracted=entities_extracted,
#             chunks_created=chunks_created
#         )
        
#         if not content:
#             raise HTTPException(status_code=404, detail=f"Content {content_id} not found in vault {vault_id}")
        
#         return _content_to_response(content)
    
#     except HTTPException:
#         raise
    
#     except Exception as e:
#         logger.error(f"Error updating content status: {e}")
#         raise HTTPException(status_code=500, detail=str(e))
