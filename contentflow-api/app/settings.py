"""
Application settings for ContentFlow API.
"""
import os
from typing import Optional
from functools import lru_cache
from pydantic import BaseModel, Field
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv('.env'))

class AppSettings(BaseModel):
    """
    Application settings model.
    """

    # Application settings with defaults
    TITLE: str = "ContentFlow API"
    VERSION: str = "0.1.0"
    DESCRIPTION: str | None = "ContentFlow API for managing content processing pipelines."
    DOCS_URL: str = "/docs"
    OPENAPI_URL: str = "/openapi.json"
    REDOC_URL: str = "/redoc"

    API_SERVER_HOST: str = "0.0.0.0"
    API_SERVER_PORT: int = 8090
    API_SERVER_WORKERS: int = 4

    DEBUG: bool = True
    LOG_LEVEL: str = "DEBUG"

    ALLOW_CREDENTIALS: bool = True
    ALLOW_ORIGINS: list[str] = ["*"]
    ALLOW_METHODS: list[str] = ["*"]
    ALLOW_HEADERS: list[str] = ["*"]
    
    # Required settings (will be loaded from App Configuration)
    COSMOS_DB_ENDPOINT: str = ""
    COSMOS_DB_NAME: str = "contentflow"
    
    # Container names in Cosmos DB
    COSMOS_DB_CONTAINER_EXECUTOR_CATALOG: str = "executor_catalog"
    COSMOS_DB_CONTAINER_EXECUTOR_CATALOG_PARTITION_KEY : str = "/id"
    
    COSMOS_DB_CONTAINER_PIPELINES: str = "pipelines"
    COSMOS_DB_CONTAINER_PIPELINES_PARTITION_KEY: str = "/id"
    
    COSMOS_DB_CONTAINER_VAULTS: str = "vaults"
    COSMOS_DB_CONTAINER_VAULTS_PARTITION_KEY: str = "/id"
    
    COSMOS_DB_CONTAINER_BATCH_EXECUTIONS: str = "batch_executions"
    COSMOS_DB_CONTAINER_BATCH_EXECUTIONS_PARTITION_KEY: str = "/id"
    
    COSMOS_DB_CONTAINER_PIPELINE_EXECUTIONS: str = "pipeline_executions"
    COSMOS_DB_CONTAINER_PIPELINE_EXECUTIONS_PARTITION_KEY: str = "/id"
        
    # Azure Storage Blob settings
    BLOB_STORAGE_ACCOUNT_NAME: str = ""
    BLOB_STORAGE_CONTAINER_NAME: str = "content"
    
    # Azure Storage Queue settings
    STORAGE_ACCOUNT_WORKER_QUEUE_URL: str = ""
    STORAGE_WORKER_QUEUE_NAME: str = "contentflow-execution-requests"

    WORKER_ENGINE_API_ENDPOINT: str = "http://localhost:8099"

    def __init__(self, **kwargs):
        """Initialize AppSettings and load configuration from Azure App Configuration"""
        super().__init__(**kwargs)
        self._load_from_app_config()

    def _load_from_app_config(self):
        """Load configuration values from Azure App Configuration"""
        
        print(f"contentflow.api: Loading configuration from contentflow configuration provider...")
        
        try:
            from app.dependencies import get_config_provider
            config_provider = get_config_provider(refresh=True)
            
            # Define the configuration keys to load
            config_keys = [
                "COSMOS_DB_ENDPOINT",
                "COSMOS_DB_NAME",
                "BLOB_STORAGE_ACCOUNT_NAME",
                "BLOB_STORAGE_CONTAINER_NAME",
                "STORAGE_ACCOUNT_WORKER_QUEUE_URL",
                "STORAGE_WORKER_QUEUE_NAME",
                "WORKER_ENGINE_API_ENDPOINT",
                "API_SERVER_HOST",
                "API_SERVER_PORT",
                "API_SERVER_WORKERS",
                "LOG_LEVEL",
                "DEBUG",
                "ALLOW_CREDENTIALS",
                "ALLOW_ORIGINS",
                "ALLOW_METHODS",
                "ALLOW_HEADERS"
            ]
            
            # Load configuration values
            for key in config_keys:
                try:
                    value = None
                    
                    try:
                        value = config_provider.get_config_value(key)
                    except KeyError as e:
                        print(f"contentflow.api: Warning: Could not get config key '{key}' from config provider: {e}")
                        if value is None:
                            # Fallback to environment variable
                            value = os.environ.get(key, None)
                    
                    if (value is None or value == ""):
                        if getattr(self, key, None) in [None, ""]:
                            raise KeyError(f"Configuration key '{key}' not found in Azure App Configuration nor from environment variables.")
                        else:
                            print(f"\033[34mcontentflow.api: Config key not found. Using existing default value for key '{key}': {getattr(self, key)}\033[0m")
                            continue  # Keep existing default value
                        
                    if value is not None:
                        value = value.strip()
                        
                        # Handle type conversion
                        if key in ["API_SERVER_PORT", "API_SERVER_WORKERS"]:
                            value = int(value)
                        elif key == "DEBUG":
                            value = value.lower() in ("true", "1", "yes", "on")
                        elif key in ["ALLOW_ORIGINS", "ALLOW_METHODS", "ALLOW_HEADERS"]:
                            value = [item.strip() for item in value.split(",")]
                        elif key == "ALLOW_CREDENTIALS":
                            value = value.lower() in ("true", "1", "yes", "on")
                        
                        setattr(self, key, value)
                    
                except KeyError as e:
                    print(f"\033[91mcontentflow.api: {e}.\033[0m")
                except Exception as e:
                    print(f"\033[91mAn error occurred while loading configuration key '{key}': {e}\033[0m")
                    continue
                    
        except Exception as e:
            print("\033[91m🚨 contentflow.api: Critical Error. Failed to load configuration from Azure App Configuration. Application cannot start without required settings.\033[0m")
            print("\033[91m contentflow.api: Please ensure that either the AZURE_APP_CONFIG_CONNECTION_STRING or AZURE_APP_CONFIG_ENDPOINT environment variables is set correctly and that the application has access/permissions to Azure App Configuration resource.\033[0m")
            print(f"\033[91m contentflow.api: Error details: {e}\033[0m")
            raise e
    
    def get_cosmos_db_containers(self) -> dict[str, str]:
        """Get a dict of all Cosmos DB container names used by the application"""
        return {
            self.COSMOS_DB_CONTAINER_EXECUTOR_CATALOG: self.COSMOS_DB_CONTAINER_EXECUTOR_CATALOG_PARTITION_KEY,
            self.COSMOS_DB_CONTAINER_PIPELINES : self.COSMOS_DB_CONTAINER_PIPELINES_PARTITION_KEY,
            self.COSMOS_DB_CONTAINER_VAULTS: self.COSMOS_DB_CONTAINER_VAULTS_PARTITION_KEY,
            self.COSMOS_DB_CONTAINER_BATCH_EXECUTIONS: self.COSMOS_DB_CONTAINER_BATCH_EXECUTIONS_PARTITION_KEY,
            self.COSMOS_DB_CONTAINER_PIPELINE_EXECUTIONS: self.COSMOS_DB_CONTAINER_PIPELINE_EXECUTIONS_PARTITION_KEY
        }
    
    def get_blob_storage_account_details(self) -> dict[str, str]:
        """Get Azure Blob Storage account details"""
        return {
            "account_name": self.BLOB_STORAGE_ACCOUNT_NAME,
            "account_url": f"https://{self.BLOB_STORAGE_ACCOUNT_NAME}.blob.core.windows.net",
            "container_name": self.BLOB_STORAGE_CONTAINER_NAME
        }
    
    def get_fastapi_attributes(self) -> dict[str, str | bool | None]:
        """
        Set all `FastAPI` class' attributes with the custom values.
        """
        return {
            "title": self.TITLE,
            "version": self.VERSION,
            "debug": self.DEBUG,
            "description": self.DESCRIPTION,
            "docs_url": self.DOCS_URL,
            "openapi_url": self.OPENAPI_URL,
            "redoc_url": self.REDOC_URL
        }

from contentflow.utils import ttl_cache

@ttl_cache(ttl=60 * 10)  # Cache for 10 minutes
def get_settings() -> AppSettings:
    """Get cached AppSettings instance"""
    
    print("contentflow.api: Loading application settings...")
    return AppSettings()
