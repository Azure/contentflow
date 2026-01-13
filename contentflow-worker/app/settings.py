"""
Worker settings and configuration for the ContentFlow worker engine.

This module handles configuration loading from environment variables
and Azure App Configuration.
"""
import os
from typing import Optional
from pydantic import BaseModel, Field
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv('.env'))


class WorkerSettings(BaseModel):
    """Configuration settings for the worker engine"""
    
    AZURE_APP_CONFIG_ENDPOINT: Optional[str] = Field(default=None, description="Azure App Configuration endpoint URL")
    APP_CONFIG_KEY_FILTERS: list = Field(default=["contentflow.worker.*"], description="Key filters for App Configuration")
    
    # Worker settings
    WORKER_NAME: str = Field(default="contentflow-worker", description="Worker instance name")
    NUM_PROCESSING_WORKERS: int = Field(default=0, description="Number of content processing worker processes")
    NUM_SOURCE_WORKERS: int = Field(default=1, description="Number of input source loading worker processes")
    
    # Queue settings
    STORAGE_ACCOUNT_WORKER_QUEUE_URL: str = Field(description="Azure Storage Queue URL")
    STORAGE_WORKER_QUEUE_NAME: str = Field(default="contentflow-execution-requests", description="Queue name for processing tasks")
    
    # Polling settings
    QUEUE_POLL_INTERVAL_SECONDS: int = Field(default=5, description="Interval between queue polls")
    QUEUE_VISIBILITY_TIMEOUT_SECONDS: int = Field(default=300, description="Message visibility timeout (5 minutes)")
    QUEUE_MAX_MESSAGES: int = Field(default=32, description="Maximum messages to retrieve per poll per worker")
    DEFAULT_POLLING_INTERVAL_SECONDS: int = Field(default=300, description="Default polling interval if not specified in input executor (5 minutes)")
    SCHEDULER_SLEEP_INTERVAL_SECONDS: int = Field(default=5, description="How often scheduler checks for ready pipelines")
    LOCK_TTL_SECONDS: int = Field(default=300, description="Lock time-to-live (5 minutes)")
    
    # Processing settings
    MAX_TASK_RETRIES: int = Field(default=3, description="Maximum retries for failed tasks")
    TASK_TIMEOUT_SECONDS: int = Field(default=600, description="Timeout for task processing (10 minutes)")
    
    # Cosmos DB settings (for pipeline and execution tracking)
    COSMOS_DB_ENDPOINT: str = Field(description="Cosmos DB endpoint")
    COSMOS_DB_NAME: str = Field(default="contentflow", description="Cosmos DB database name")
    COSMOS_DB_CONTAINER_PIPELINES: str = Field(default="pipelines", description="Container for pipelines")
    COSMOS_DB_CONTAINER_VAULT_EXECUTIONS: str = Field(default="vault_executions", description="Container for executions")
    COSMOS_DB_CONTAINER_VAULTS: str = Field(default="vaults", description="Container for vaults")
    COSMOS_DB_CONTAINER_VAULT_EXECUTION_LOCKS: str = Field(default="vault_exec_locks", description="Container for distributed locks")
    COSMOS_DB_CONTAINER_CRAWL_CHECKPOINTS: str = Field(default="vault_crawl_checkpoints", description="Container for vault input executor crawling checkpoints")
    
    # Blob Storage settings (for content retrieval)
    BLOB_STORAGE_ACCOUNT_NAME: str = Field(description="Azure Blob Storage account name")
    BLOB_STORAGE_CONTAINER_NAME: str = Field(default="content", description="Container for content")
    
    # API settings
    API_ENABLED: bool = Field(default=True, description="Enable health/status API")
    API_HOST: str = Field(default="0.0.0.0", description="API host to bind to")
    API_PORT: int = Field(default=8099, description="API port to bind to")
    
    # Logging
    LOG_LEVEL: str = Field(default="DEBUG", description="Logging level")
    DEBUG: bool = Field(default=False, description="Debug mode")
    
    def __init__(self, **kwargs):
        """Initialize WorkerSettings and load from environment/App Config"""
        # Load from environment variables first
        env_config = self._load_from_env()
        merged_config = {**env_config, **kwargs}
        super().__init__(**merged_config)
        
        # Try to load from Azure App Configuration
        self._load_from_app_config()
    
    def _load_from_env(self) -> dict:
        """Load configuration from environment variables"""
        return {
            "AZURE_APP_CONFIG_ENDPOINT": os.getenv("AZURE_APP_CONFIG_ENDPOINT", ""),
            "APP_CONFIG_KEY_FILTERS": os.getenv("APP_CONFIG_KEY_FILTERS", "contentflow.worker.*").split(","),
            "WORKER_NAME": os.getenv("WORKER_NAME", "contentflow-worker"),
            "NUM_PROCESSING_WORKERS": int(os.getenv("NUM_PROCESSING_WORKERS", "0")),
            "NUM_SOURCE_WORKERS": int(os.getenv("NUM_SOURCE_WORKERS", "1")),
            "STORAGE_ACCOUNT_WORKER_QUEUE_URL": os.getenv("STORAGE_ACCOUNT_WORKER_QUEUE_URL", ""),
            "STORAGE_WORKER_QUEUE_NAME": os.getenv("STORAGE_WORKER_QUEUE_NAME", "contentflow-execution-requests"),
            "QUEUE_POLL_INTERVAL_SECONDS": int(os.getenv("QUEUE_POLL_INTERVAL_SECONDS", "5")),
            "QUEUE_VISIBILITY_TIMEOUT_SECONDS": int(os.getenv("QUEUE_VISIBILITY_TIMEOUT_SECONDS", "300")),
            "QUEUE_MAX_MESSAGES": int(os.getenv("QUEUE_MAX_MESSAGES", "32")),
            "MAX_TASK_RETRIES": int(os.getenv("MAX_TASK_RETRIES", "3")),
            "TASK_TIMEOUT_SECONDS": int(os.getenv("TASK_TIMEOUT_SECONDS", "600")),
            "COSMOS_DB_ENDPOINT": os.getenv("COSMOS_DB_ENDPOINT", ""),
            "COSMOS_DB_NAME": os.getenv("COSMOS_DB_NAME", "contentflow"),
            "COSMOS_DB_CONTAINER_PIPELINES": os.getenv("COSMOS_DB_CONTAINER_PIPELINES", "pipelines"),
            "COSMOS_DB_CONTAINER_VAULTS": os.getenv("COSMOS_DB_CONTAINER_VAULTS", "vaults"),
            "COSMOS_DB_CONTAINER_VAULT_EXECUTIONS": os.getenv("COSMOS_DB_CONTAINER_VAULT_EXECUTIONS", "vault_executions"),
            "COSMOS_DB_CONTAINER_VAULT_EXECUTION_LOCKS": os.getenv("COSMOS_DB_CONTAINER_VAULT_EXECUTION_LOCKS", "vault_exec_locks"),
            "COSMOS_DB_CONTAINER_CRAWL_CHECKPOINTS": os.getenv("COSMOS_DB_CONTAINER_CRAWL_CHECKPOINTS", "vault_crawl_checkpoints"),
            "DEFAULT_POLLING_INTERVAL_SECONDS": int(os.getenv("DEFAULT_POLLING_INTERVAL_SECONDS", "300")),
            "SCHEDULER_SLEEP_INTERVAL_SECONDS": int(os.getenv("SCHEDULER_SLEEP_INTERVAL_SECONDS", "5")),
            "LOCK_TTL_SECONDS": int(os.getenv("LOCK_TTL_SECONDS", "300")),
            "BLOB_STORAGE_ACCOUNT_NAME": os.getenv("BLOB_STORAGE_ACCOUNT_NAME", ""),
            "BLOB_STORAGE_CONTAINER_NAME": os.getenv("BLOB_STORAGE_CONTAINER_NAME", "content"),
            "API_ENABLED": os.getenv("API_ENABLED", "True").lower() in ("true", "1", "yes"),
            "API_HOST": os.getenv("API_HOST", "0.0.0.0"),
            "API_PORT": int(os.getenv("API_PORT", "8099")),
            "LOG_LEVEL": os.getenv("LOG_LEVEL", "DBEUG"),
            "DEBUG": os.getenv("DEBUG", "False").lower() in ("true", "1", "yes"),
        }
    
    def _load_from_app_config(self):
        """Load configuration from Azure App Configuration (if available)"""
        try:
            if self.AZURE_APP_CONFIG_ENDPOINT in [None, ""]:
                print("Azure App Configuration endpoint not set in env variable AZURE_APP_CONFIG_ENDPOINT, skipping App Config load.")
                return
            
            from contentflow.utils import ConfigurationProvider
            config_provider = ConfigurationProvider(app_config_endpoint=self.AZURE_APP_CONFIG_ENDPOINT, config_key_filters=self.APP_CONFIG_KEY_FILTERS)
            
            # List of settings to load from App Config
            config_keys = [
                "STORAGE_ACCOUNT_WORKER_QUEUE_URL",
                "STORAGE_WORKER_QUEUE_NAME",
                "COSMOS_DB_ENDPOINT",
                "COSMOS_DB_NAME",
                "BLOB_STORAGE_ACCOUNT_NAME",
                "BLOB_STORAGE_CONTAINER_NAME",
                "NUM_PROCESSING_WORKERS",
                "NUM_SOURCE_WORKERS",
                "LOG_LEVEL",
                "DEBUG",
                "API_ENABLED",
                "API_HOST",
                "API_PORT",
                "QUEUE_POLL_INTERVAL_SECONDS",
                "QUEUE_VISIBILITY_TIMEOUT_SECONDS",
                "QUEUE_MAX_MESSAGES",
                "MAX_TASK_RETRIES",
                "TASK_TIMEOUT_SECONDS",
                "DEFAULT_POLLING_INTERVAL_SECONDS",
                "SCHEDULER_SLEEP_INTERVAL_SECONDS",
                "LOCK_TTL_SECONDS"
            ]
            
            for key in config_keys:
                value = config_provider.get_config_value(key)
                if value is not None:
                    # Convert to appropriate type
                    if key in ["NUM_PROCESSING_WORKERS", "NUM_SOURCE_WORKERS", "API_PORT", "QUEUE_POLL_INTERVAL_SECONDS", 
                               "QUEUE_VISIBILITY_TIMEOUT_SECONDS", "QUEUE_MAX_MESSAGES", "MAX_TASK_RETRIES", "TASK_TIMEOUT_SECONDS", 
                               "SOURCE_WORKER_POLL_INTERVAL_SECONDS", "DEFAULT_POLLING_INTERVAL_SECONDS", "SCHEDULER_SLEEP_INTERVAL_SECONDS", 
                               "LOCK_TTL_SECONDS"]:
                        value = int(value)
                    elif key in ["API_ENABLED", "DEBUG"]:
                        value = value.lower() in ("true", "1", "yes")
                    
                    setattr(self, key, value)
                    
        except ImportError:
            # Config provider not available, use environment variables only
            pass
        except Exception as e:
            print(f"Warning: Failed to load from App Configuration: {e}")
    
    class Config:
        validate_assignment = True


def get_settings() -> WorkerSettings:
    """Get worker settings (singleton pattern)"""
    global _settings
    if _settings is None:
        _settings = WorkerSettings()
    return _settings


# Global settings instance
_settings: Optional[WorkerSettings] = None
