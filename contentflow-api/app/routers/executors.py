from typing import List

from fastapi import APIRouter, HTTPException, Depends

from app.models import ExecutorCatalogDefinition
from app.services import ExecutorCatalogService
from app.dependencies import get_executor_catalog_service

router = APIRouter(prefix="/executors", tags=["executors"])

#######################################################
# Executor Catalog endpoints

@router.get("/", response_model=List[ExecutorCatalogDefinition])
async def get_executor_catalog(service: ExecutorCatalogService = Depends(get_executor_catalog_service)):
    """List all executors from the executor catalog"""
    try:
        catalog = await service.get_catalog_executors()
        return catalog
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Failed to retrieve catalog: {str(e)}')

@router.get("/{executor_definition_id}", response_model=ExecutorCatalogDefinition)
async def get_executor_definition(executor_definition_id: str, service: ExecutorCatalogService = Depends(get_executor_catalog_service)):
    """Get a specific executor from the catalog by ID"""
    catalog_executor = await service.get_catalog_executor_by_id(executor_definition_id)
    if not catalog_executor:
        raise HTTPException(status_code=404, detail="Executor definition not found in catalog")
    
    return catalog_executor

# @router.post("/initialize")
# async def initialize_catalog(service: ExecutorCatalogService = Depends(get_executor_catalog_service)):
#     """Initialize default executors from catalog"""
#     return await service.initialize_executor_catalog()