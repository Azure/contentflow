"""
Startup and initialization logic for the application.
"""
import asyncio
import logging
from opentelemetry import trace

from app.dependencies import initialize_cosmos, initialize_blob_storage, initialize_executor_catalog

logger = logging.getLogger("contentflow.api.startup")

async def startup_tasks():
    """Run all startup tasks"""
    logger.info("Starting application initialization tasks...")
    
    tasks = [
        initialize_cosmos(),
        initialize_blob_storage(),
        initialize_executor_catalog(),
        # Add other startup tasks here
    ]
    
    for i, task in enumerate(tasks):
        logger.info(f"Running startup task {i}: {task.__name__}")
        try:
            # run the task and wait for completion
            await task
            has_errors = False
        except Exception as e:
            has_errors = True
            logger.error(f"Error in startup task {i} ({task.__name__}): {str(e)}")
            logger.exception(e)
            
        logger.info(f"Completed startup task {i}: {task.__name__}")
        
    
    if has_errors:
        logger.warning("⚠️ Application initialization completed with errors")
    else:
        logger.info("✅ Application initialization completed")


async def startup():
    tracer = trace.get_tracer("contentflow-api.startup")
    with tracer.start_as_current_span("startup"):
        logger.info("Application is starting up...")
        await startup_tasks()
    
    
async def shutdown():
    logger.info("Application is shutting down...")
    # Add cleanup tasks here if needed