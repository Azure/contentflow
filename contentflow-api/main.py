"""
Main application entry point for the ContentFlow API.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import uvicorn

from app.settings import get_settings
from app.utils.logging import setup_logger
from app.startup import startup, shutdown
from app.routers import health_router, pipelines_router, executors_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await startup()
    yield
    # Shutdown
    await shutdown()

def initialize_api_application() -> FastAPI:
    
    app = FastAPI(
        title=app_settings.TITLE,
        version=app_settings.VERSION,
        debug=app_settings.DEBUG,
        lifespan=lifespan
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=app_settings.ALLOW_ORIGINS,
        allow_credentials=app_settings.ALLOW_CREDENTIALS,
        allow_methods=app_settings.ALLOW_METHODS,
        allow_headers=app_settings.ALLOW_HEADERS,
    )

    # # Include routers
    app.include_router(health_router, prefix="/api")
    app.include_router(pipelines_router, prefix="/api")
    app.include_router(executors_router, prefix="/api")

    # # Global exception handler
    # @app.exception_handler(Exception)
    # async def global_exception_handler(request, exc):
    #     return JSONResponse(
    #         status_code=500,
    #         content={
    #             "success": False,
    #             "error": "Internal server error",
    #             "details": str(exc) if app_settings.DEBUG else "An unexpected error occurred"
    #         }
    #     )

    @app.get("/")
    async def root():
        """Root endpoint"""
        return {"message": "ContentFlow API", "version": app_settings.VERSION}

    return app

app_settings = get_settings()

setup_logger(app_settings.LOG_LEVEL)

app: FastAPI = initialize_api_application()

if __name__ == "__main__":
    uvicorn.run("main:app", 
                reload=app_settings.DEBUG,
                host=app_settings.API_SERVER_HOST,
                port=app_settings.API_SERVER_PORT,
                workers=app_settings.API_SERVER_WORKERS,
                use_colors=True,
                log_config=None)  # Disable uvicorn's default logging config