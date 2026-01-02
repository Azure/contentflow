"""
FastAPI application for worker health and status monitoring.

This module provides HTTP endpoints for monitoring the health and status
of the ContentFlow worker engine.
"""
import logging
from datetime import datetime, timezone
from typing import Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.settings import WorkerSettings
from app.engine import WorkerEngine

logger = logging.getLogger("contentflow.worker.api")

class HealthResponse(BaseModel):
    """Health check response model"""
    status: str
    timestamp: str
    worker_name: str


class WorkerStatusResponse(BaseModel):
    """Worker status response model"""
    worker_name: str
    running: bool
    timestamp: str
    processing_workers: dict
    source_workers: dict

def create_app(settings: WorkerSettings, engine: Optional[WorkerEngine] = None) -> FastAPI:
    """
    Create and configure the FastAPI application.
    
    Args:
        settings: Worker configuration
        engine: Reference to the WorkerEngine instance
        
    Returns:
        Configured FastAPI application
    """
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        # Load the ML model into app.state during startup
        app.state.engine = engine
        app.state.settings = settings
        app.state.start_time = datetime.now(timezone.utc)
        yield
        # Clean up (optional) during shutdown
        app.state.engine = None
        app.state.settings = None
        app.state.start_time = None
    
    app = FastAPI(
        title="ContentFlow Worker API",
        description="Health and status monitoring API for ContentFlow worker service",
        version="1.0.0",
        lifespan=lifespan
    )
    
    @app.get("/", tags=["root"])
    async def root():
        """Root endpoint"""
        return {
            "service": "ContentFlow Worker API",
            "version": "1.0.0",
            "worker_name": app.state.settings.WORKER_NAME
        }
    
    @app.get("/health", response_model=HealthResponse, tags=["monitoring"])
    async def health():
        """
        Health check endpoint.
        
        Returns basic health status indicating the API is responsive.
        """
        return HealthResponse(
            status="healthy",
            timestamp=datetime.now(timezone.utc).isoformat(),
            worker_name=app.state.settings.WORKER_NAME
        )
    
    @app.get("/status", response_model=WorkerStatusResponse, tags=["monitoring"])
    async def get_status():
        """
        Get detailed worker status.
        
        Returns comprehensive status information about the worker engine
        and all worker processes.
        """
        
        engine = app.state.engine
        engine_status = None
        
        if engine is None:
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={
                    "error": "Worker engine not initialized",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            )
        
        if isinstance(engine, WorkerEngine):
            engine_status = engine.get_status()
        
        if not engine_status:
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "error": "Unable to retrieve worker status",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            )
        
        return WorkerStatusResponse(
            worker_name=app.state.settings.WORKER_NAME,
            running=engine_status["running"],
            timestamp=datetime.now(timezone.utc).isoformat(),
            processing_workers=engine_status["processing_workers"],
            source_workers=engine_status["source_workers"]
        )
        
    return app
    