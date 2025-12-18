"""
Dependency injection and initialization for ContentFlow API services.
"""
import os
import logging
from anyio import Path

from contentflow.utils import ttl_cache
from contentflow.utils import ConfigurationProvider

from contentflow import pipeline

from app.utils.credential import get_azure_credential, get_azure_credential_async
from app.database.cosmos import CosmosDBClient

logger = logging.getLogger("contentflow-api.dependencies")

# Global instances
__cosmos_client: CosmosDBClient = None
__config: ConfigurationProvider = None
__cache_ttl: int = 60 * 10  # cache for 10 minutes for all services


EXECUTOR_CATALOG_FILE_PATH = f'{Path(__file__).parent.parent.parent}/contentflow-lib/executor_catalog.yaml'

def get_config_provider(refresh: bool = False) -> ConfigurationProvider:
    """Get a singleton instance of ConfigurationProvider"""
    global __config
    if __config is None:
        _app_config_endpoint = os.environ.get("AZURE_APP_CONFIG_ENDPOINT", "")
        __config = ConfigurationProvider(app_config_endpoint=_app_config_endpoint.strip(), config_key_filters=["contentflow.api.*"])
    elif refresh:
        __config.request_refresh()
    return __config

# Dependency to get database connection
async def get_cosmos_client() -> CosmosDBClient:
    """Dependency to get Cosmos DB client"""
    global __cosmos_client
    
    if __cosmos_client is None:
        await initialize_cosmos()
        
    return __cosmos_client


@ttl_cache(ttl=__cache_ttl)  # Cache for 10 minutes
def get_health_service():
    """Get HealthService instance"""
    from app.settings import get_settings
    app_settings = get_settings()
    
    from app.services import HealthService
    
    return HealthService(cosmos_endpoint=app_settings.COSMOS_DB_ENDPOINT,
                         cosmos_db_name=app_settings.COSMOS_DB_NAME,
                         cosmos_db_containers=app_settings.get_cosmos_db_containers(),
                         blob_storage_account=app_settings.BLOB_STORAGE_ACCOUNT_NAME,
                         blob_storage_container=app_settings.BLOB_STORAGE_CONTAINER_NAME,
                         storage_account_worker_queue_url=app_settings.STORAGE_ACCOUNT_WORKER_QUEUE_URL,
                         storage_worker_queue_name=app_settings.STORAGE_WORKER_QUEUE_NAME,
                         worker_engine_api_endpoint=app_settings.WORKER_ENGINE_API_ENDPOINT)

@ttl_cache(ttl=__cache_ttl)  # Cache for 10 minutes
async def get_pipeline_service():
    """Dependency to get PipelineService"""
    from app.services import PipelineService
    return PipelineService(await get_cosmos_client())

@ttl_cache(ttl=__cache_ttl)  # Cache for 10 minutes
async def get_vault_service():
    """Dependency to get VaultService"""
    from app.services import VaultService
    return VaultService(await get_cosmos_client())

@ttl_cache(ttl=__cache_ttl)  # Cache for 10 minutes
async def get_executor_catalog_service():
    """Dependency to get ExecutorCatalogService"""
    from app.services import ExecutorCatalogService
    return ExecutorCatalogService(await get_cosmos_client())

@ttl_cache(ttl=__cache_ttl)  # Cache for 10 minutes
async def get_pipeline_execution_service():
    """Dependency to get PipelineExecutionService"""
    from app.services.pipeline_execution_service import PipelineExecutionService
    return PipelineExecutionService(await get_cosmos_client())

# async def get_analysis_service():
#     """Dependency to get AnalysisService"""
#     from app.services.analysis_service import AnalysisService
#     global cosmos_client
#     return AnalysisService(cosmos_client)

async def initialize_executor_catalog():
    """Initialize executor catalog"""
    logger.info(f"{'>'*70}")
    logger.info("contentflow.api: Initializing executor catalog...")
    logger.info(f"{'-'*70}")
    try:
        executor_catalog_service = await get_executor_catalog_service()
        result = await executor_catalog_service.initialize_executor_catalog(EXECUTOR_CATALOG_FILE_PATH)
        
        logger.info("contentflow.api: Executor catalog initialized successfully.")
        logger.info(f"Created {result.get('created_count', 0)} new executors from catalog.")
        logger.info(f"Total executors in catalog: {result.get('total_catalog_executors', 0)}")
        logger.info(f"{'<'*70}")
        
        return True
    except Exception as e:
        logger.error(f"Error during executor catalog initialization: {str(e)}")
        logger.exception(e)
        raise

async def initialize_cosmos():
    """Initialize Cosmos dependencies"""
    logger.info(f"{'>'*70}")
    logger.info("contentflow.api: Initializing cosmos db dependencies...")
    logger.info(f"{'-'*70}")
    try:
        from app.settings import get_settings
        app_settings = get_settings()
        
        global __cosmos_client
        if not __cosmos_client:
            __cosmos_client = CosmosDBClient(database=app_settings.COSMOS_DB_NAME, 
                                             endpoint=app_settings.COSMOS_DB_ENDPOINT, 
                                             credential=await get_azure_credential_async(),
                                             initial_containers=app_settings.get_cosmos_db_containers())
            await __cosmos_client.connect()
        
        logger.info("contentflow.api: Cosmos db dependencies initialized successfully.")
        logger.info(f"{'<'*70}")
        
        return True
    except Exception as e:
        logger.error(f"Error during cosmos db dependencies initialization: {str(e)}")
        logger.exception(e)
        raise
    
async def initialize_blob_storage():
    """Initialize blob storage dependencies"""
    logger.info(f"{'>'*70}")
    logger.info("contentflow.api: Initializing blob storage dependencies...")
    logger.info(f"{'-'*70}")
    try:
        from app.settings import get_settings
        app_settings = get_settings()
        
        # Initialize blob storage
        from app.utils.blob_storage import get_blob_storage_service
        await get_blob_storage_service(account_name=app_settings.BLOB_STORAGE_ACCOUNT_NAME, 
                                       container_name=app_settings.BLOB_STORAGE_CONTAINER_NAME)
        
        logger.info("contentflow.api: Blob storage dependencies initialized successfully.")
        logger.info(f"{'<'*70}")
        
        return True
    except Exception as e:
        logger.error(f"Error during blob storage dependencies initialization: {str(e)}")
        logger.exception(e)
        raise

async def close_all():
    """Close all dependencies"""
    global __cosmos_client
    if __cosmos_client:
        await __cosmos_client.close()
    
    # Close blob storage
    from app.utils.blob_storage import close_blob_storage_service
    await close_blob_storage_service()
