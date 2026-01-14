"""
Startup validation and health checks for ContentFlow Worker.

This module performs pre-flight checks before starting the worker engine:
- Validates required settings
- Verifies Cosmos DB connectivity and containers
- Verifies Azure Storage Queue connectivity
"""
import logging
from typing import List, Tuple

from azure.cosmos import CosmosClient
from azure.core.exceptions import ResourceNotFoundError, AzureError
from azure.storage.queue import QueueClient

from contentflow.utils import get_azure_credential
from app.settings import WorkerSettings

logger = logging.getLogger("contentflow.worker.startup")


class StartupValidator:
    """Validates system readiness before starting the worker engine"""
    
    def __init__(self, settings: WorkerSettings):
        """
        Initialize the startup validator.
        
        Args:
            settings: Worker configuration settings
        """
        self.settings = settings
        self.errors: List[str] = []
        self.warnings: List[str] = []
    
    def validate_all(self) -> bool:
        """
        Run all startup validations.
        
        Returns:
            True if all checks pass, False if any critical errors occur
        """
        logger.info("=" * 60)
        logger.info("Running Startup Validation Checks")
        logger.info("=" * 60)
        
        # Run all validation checks
        checks = [
            ("Settings Validation", self._validate_settings),
            ("Cosmos DB Connectivity", self._validate_cosmos_connectivity),
            ("Cosmos DB Containers", self._validate_cosmos_containers),
            ("Storage Queue Connectivity", self._validate_queue_connectivity),
        ]
        
        for check_name, check_func in checks:
            logger.info(f"Checking: {check_name}...")
            try:
                success, message = check_func()
                if success:
                    logger.info(f"✅ {check_name}: {message}")
                else:
                    logger.error(f"❌ {check_name}: {message}")
                    self.errors.append(f"{check_name}: {message}")
            except Exception as e:
                logger.error(f"❌ {check_name}: Unexpected error - {e}", exc_info=True)
                self.errors.append(f"{check_name}: {str(e)}")
        
        # Display summary
        logger.info("=" * 60)
        if self.warnings:
            logger.warning(f"⚠️  {len(self.warnings)} warning(s):")
            for warning in self.warnings:
                logger.warning(f"  - {warning}")
        
        if self.errors:
            logger.error(f"❌ {len(self.errors)} critical error(s) found:")
            for error in self.errors:
                logger.error(f"  - {error}")
            logger.error("=" * 60)
            logger.error("Startup validation FAILED. Fix errors before starting.")
            return False
        else:
            logger.info("✅ All startup validation checks passed!")
            logger.info("=" * 60)
            return True
    
    def _validate_settings(self) -> Tuple[bool, str]:
        """Validate that all required settings are present"""
        required_settings = {
            "COSMOS_DB_ENDPOINT": self.settings.COSMOS_DB_ENDPOINT,
            "COSMOS_DB_NAME": self.settings.COSMOS_DB_NAME,
            "STORAGE_ACCOUNT_WORKER_QUEUE_URL": self.settings.STORAGE_ACCOUNT_WORKER_QUEUE_URL,
            "STORAGE_WORKER_QUEUE_NAME": self.settings.STORAGE_WORKER_QUEUE_NAME,
            "BLOB_STORAGE_ACCOUNT_NAME": self.settings.BLOB_STORAGE_ACCOUNT_NAME,
        }
        
        missing = []
        for key, value in required_settings.items():
            if not value or value == "":
                missing.append(key)
        
        if missing:
            return False, f"Missing required settings: {', '.join(missing)}"
        
        # Validate worker counts
        if self.settings.NUM_PROCESSING_WORKERS < 0:
            return False, "NUM_PROCESSING_WORKERS must be >= 0"
        
        if self.settings.NUM_SOURCE_WORKERS < 0:
            return False, "NUM_SOURCE_WORKERS must be >= 0"
        
        if self.settings.NUM_PROCESSING_WORKERS == 0 and self.settings.NUM_SOURCE_WORKERS == 0:
            return False, "At least one of NUM_PROCESSING_WORKERS or NUM_SOURCE_WORKERS must be > 0"
        
        # Warnings for configuration
        if self.settings.NUM_PROCESSING_WORKERS == 0:
            self.warnings.append("NUM_PROCESSING_WORKERS is 0 - no content processing will occur")
        
        if self.settings.NUM_SOURCE_WORKERS == 0:
            self.warnings.append("NUM_SOURCE_WORKERS is 0 - no source scanning will occur")
        
        return True, f"All required settings present (Processing Workers: {self.settings.NUM_PROCESSING_WORKERS}, Source Workers: {self.settings.NUM_SOURCE_WORKERS})"
    
    def _validate_cosmos_connectivity(self) -> Tuple[bool, str]:
        """Validate connectivity to Cosmos DB"""
        try:
            credential = get_azure_credential()
            cosmos_client = CosmosClient(
                url=self.settings.COSMOS_DB_ENDPOINT,
                credential=credential
            )
            
            # Try to list databases to verify connectivity
            databases = list(cosmos_client.list_databases())
            
            # Check if our database exists
            db_exists = any(db["id"] == self.settings.COSMOS_DB_NAME for db in databases)
            
            if not db_exists:
                return False, f"Database '{self.settings.COSMOS_DB_NAME}' not found in Cosmos DB"
            
            return True, f"Connected to Cosmos DB at {self.settings.COSMOS_DB_ENDPOINT}"
            
        except AzureError as e:
            return False, f"Failed to connect to Cosmos DB: {str(e)}"
        except Exception as e:
            return False, f"Unexpected error connecting to Cosmos DB: {str(e)}"
    
    def _validate_cosmos_containers(self) -> Tuple[bool, str]:
        """Validate that required Cosmos DB containers exist"""
        required_containers = [
            self.settings.COSMOS_DB_CONTAINER_PIPELINES,
            self.settings.COSMOS_DB_CONTAINER_VAULT_EXECUTIONS,
            self.settings.COSMOS_DB_CONTAINER_VAULTS,
            self.settings.COSMOS_DB_CONTAINER_VAULT_EXECUTION_LOCKS,
            self.settings.COSMOS_DB_CONTAINER_CRAWL_CHECKPOINTS,
        ]
        
        try:
            credential = get_azure_credential()
            cosmos_client = CosmosClient(
                url=self.settings.COSMOS_DB_ENDPOINT,
                credential=credential
            )
            
            database = cosmos_client.get_database_client(self.settings.COSMOS_DB_NAME)
            
            # Check each container
            existing_containers = list(database.list_containers())
            existing_names = [c["id"] for c in existing_containers]
            
            missing_containers = []
            for container_name in required_containers:
                if container_name not in existing_names:
                    missing_containers.append(container_name)
            
            if missing_containers:
                return False, f"Missing required containers: {', '.join(missing_containers)}"
            
            return True, f"All {len(required_containers)} required containers exist"
            
        except ResourceNotFoundError:
            return False, f"Database '{self.settings.COSMOS_DB_NAME}' not found"
        except AzureError as e:
            return False, f"Failed to access Cosmos DB containers: {str(e)}"
        except Exception as e:
            return False, f"Unexpected error checking containers: {str(e)}"
    
    def _validate_queue_connectivity(self) -> Tuple[bool, str]:
        """Validate connectivity to Azure Storage Queue"""
        try:
            credential = get_azure_credential()
            full_queue_url = f"{self.settings.STORAGE_ACCOUNT_WORKER_QUEUE_URL}/{self.settings.STORAGE_WORKER_QUEUE_NAME}"
            
            queue_client = QueueClient.from_queue_url(
                queue_url=full_queue_url,
                credential=credential
            )
            
            # Try to get queue properties to verify connectivity and existence
            properties = queue_client.get_queue_properties()
            message_count = properties.approximate_message_count
            
            return True, f"Connected to queue '{self.settings.STORAGE_WORKER_QUEUE_NAME}' ({message_count} messages)"
            
        except ResourceNotFoundError:
            return False, f"Queue '{self.settings.STORAGE_WORKER_QUEUE_NAME}' not found"
        except AzureError as e:
            return False, f"Failed to connect to Storage Queue: {str(e)}"
        except Exception as e:
            return False, f"Unexpected error connecting to queue: {str(e)}"


def run_startup_checks(settings: WorkerSettings) -> bool:
    """
    Run startup validation checks.
    
    Args:
        settings: Worker configuration settings
        
    Returns:
        True if all checks pass, False otherwise
    """
    validator = StartupValidator(settings)
    return validator.validate_all()
