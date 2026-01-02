"""
Base connector class for external service connections.

This module defines the abstract base class for all connectors used in
document processing workflows. Connectors replace the service concept,
providing a cleaner interface for connecting to external services like
storage, search, and AI services.
"""

import logging
import os
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

logger = logging.getLogger("contentflow.lib.connectors.base")


class ConnectorBase(ABC):
    """
    Abstract base class for service connectors.
    
    Connectors provide standardized access to external services used in
    document processing workflows. Each connector handles:
    - Configuration validation and environment variable resolution
    - Connection initialization and management
    
    Attributes:
        name: Unique identifier for this connector instance
        type: Type/category of the connector (e.g., 'blob_storage', 'ai_search')
        settings: Configuration dict for the connector
    
    Example:
        ```python
        connector = BlobConnector(
            name="storage",
            settings={
                "account_name": "${STORAGE_ACCOUNT}",
                "credential_type": "default_azure_credential"
            }
        )
        
        await connector.test_connection()
        ```
    """
    
    def __init__(
        self,
        name: str,
        connector_type: str,
        settings: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        """
        Initialize the connector.
        
        Args:
            name: Unique name for this connector instance
            connector_type: Type identifier for the connector
            settings: Configuration dictionary
            **kwargs: Additional connector-specific parameters
        """
        if not name:
            raise ValueError("Connector name cannot be empty")
        
        if not connector_type:
            raise ValueError("Connector type cannot be empty")
        
        self.name = name
        self.type = connector_type
        self.settings = settings or {}
        self.params = kwargs
        
        logger.debug(f"Initializing {self.type} connector: {self.name}")
        
    def _resolve_setting(
        self,
        setting_key: str,
        required: bool = True,
        default: Any = None
    ) -> Any:
        """
        Resolve a setting value, supporting environment variable substitution.
        
        Settings can use ${ENV_VAR_NAME} syntax to reference environment
        variables, which will be automatically resolved.
        
        Args:
            setting_key: Key to look up in settings
            required: Whether this setting is required
            default: Default value if not found (when not required)
            
        Returns:
            Resolved setting value
            
        Raises:
            ValueError: If required setting is missing or env var not found
        """
        value = self.settings.get(setting_key, default)
        
        if value is None and required:
            raise ValueError(
                f"Required setting '{setting_key}' not found for connector '{self.name}'"
            )
        
        # Resolve environment variable if present
        if isinstance(value, str) and value.startswith('${') and value.endswith('}'):
            env_var_name = value[2:-1]
            resolved_value = os.getenv(env_var_name)
            
            if resolved_value is None and required:
                raise ValueError(
                    f"Environment variable '{env_var_name}' for setting '{setting_key}' "
                    f"is not set or empty. Ensure it is defined in your environment or .env file."
                )
            
            return resolved_value
        
        return value
    
    def get_setting(
        self,
        setting_key: str,
        default: Any = None
    ) -> Any:
        """
        Get a setting value with optional default.
        
        Args:
            setting_key: Setting key to retrieve
            default: Default value if not found
            
        Returns:
            Setting value or default
        """
        return self._resolve_setting(setting_key, required=False, default=default)
    
    async def initialize(self) -> None:
        """
        Initialize the connector (optional hook for async initialization).
        
        Override this method if your connector needs async initialization
        logic, such as creating async clients or establishing connections.
        """
        pass
    
    async def cleanup(self) -> None:
        """
        Cleanup connector resources (optional hook for cleanup).
        
        Override this method if your connector needs to release resources,
        close connections, or perform cleanup on shutdown.
        """
        pass
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name='{self.name}', type='{self.type}')"
