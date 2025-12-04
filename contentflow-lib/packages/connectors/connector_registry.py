"""
Connector registry for managing connector instances.

This module provides the ConnectorRegistry class for managing and accessing
connector instances in workflows.
"""

import logging
from typing import Dict, Any, Optional, Type

from doc_proc_workflow.connectors.base import ConnectorBase
from doc_proc_workflow.connectors.blob_connector import BlobConnector
from doc_proc_workflow.connectors.ai_search_connector import AISearchConnector
from doc_proc_workflow.connectors.ai_inference_connector import AIInferenceConnector
from doc_proc_workflow.connectors.document_intelligence_connector import DocumentIntelligenceConnector

logger = logging.getLogger(__name__)


# Connector type registry
CONNECTOR_TYPES: Dict[str, Type[ConnectorBase]] = {
    "blob_storage": BlobConnector,
    "ai_search": AISearchConnector,
    "ai_inference": AIInferenceConnector,
    "document_intelligence": DocumentIntelligenceConnector,
}


class ConnectorRegistry:
    """
    Registry for managing connector instances.
    
    The ConnectorRegistry provides a centralized way to:
    - Create connector instances from configuration
    - Store and retrieve connectors by name
    - Initialize and cleanup connectors
    - Test connector connections
    
    Example:
        ```python
        registry = ConnectorRegistry()
        
        # Register a connector
        registry.register(
            name="storage",
            connector_type="blob_storage",
            settings={
                "account_name": "${STORAGE_ACCOUNT}",
                "credential_type": "default_azure_credential"
            }
        )
        
        # Initialize all connectors
        await registry.initialize_all()
        
        # Get a connector
        storage = registry.get("storage")
        
        # Cleanup
        await registry.cleanup_all()
        ```
    """
    
    def __init__(self):
        """Initialize the connector registry."""
        self._connectors: Dict[str, ConnectorBase] = {}
        logger.debug("ConnectorRegistry initialized")
    
    def register(
        self,
        name: str,
        connector_type: str,
        settings: Dict[str, Any],
        **kwargs
    ) -> ConnectorBase:
        """
        Register a new connector instance.
        
        Args:
            name: Unique name for this connector
            connector_type: Type of connector (e.g., 'blob_storage', 'ai_search')
            settings: Configuration dict for the connector
            **kwargs: Additional connector parameters
            
        Returns:
            Created connector instance
            
        Raises:
            ValueError: If connector type is unknown or name already exists
        """
        if name in self._connectors:
            raise ValueError(f"Connector '{name}' already registered")
        
        if connector_type not in CONNECTOR_TYPES:
            raise ValueError(
                f"Unknown connector type: {connector_type}. "
                f"Available types: {list(CONNECTOR_TYPES.keys())}"
            )
        
        # Create connector instance
        connector_class = CONNECTOR_TYPES[connector_type]
        connector = connector_class(name=name, settings=settings, **kwargs)
        
        self._connectors[name] = connector
        
        logger.info(f"Registered connector '{name}' of type '{connector_type}'")
        
        return connector
    
    def register_connector(self, connector: ConnectorBase) -> None:
        """
        Register an existing connector instance.
        
        Args:
            connector: Connector instance to register
            
        Raises:
            ValueError: If connector name already exists
        """
        if connector.name in self._connectors:
            raise ValueError(f"Connector '{connector.name}' already registered")
        
        self._connectors[connector.name] = connector
        
        logger.info(f"Registered existing connector '{connector.name}'")
    
    def get(self, name: str) -> Optional[ConnectorBase]:
        """
        Get a connector by name.
        
        Args:
            name: Connector name
            
        Returns:
            Connector instance or None if not found
        """
        return self._connectors.get(name)
    
    def has(self, name: str) -> bool:
        """
        Check if a connector is registered.
        
        Args:
            name: Connector name
            
        Returns:
            True if connector exists
        """
        return name in self._connectors
    
    def list_connectors(self) -> Dict[str, str]:
        """
        List all registered connectors.
        
        Returns:
            Dict mapping connector names to their types
        """
        return {
            name: connector.type
            for name, connector in self._connectors.items()
        }
    
    async def initialize_all(self) -> None:
        """Initialize all registered connectors."""
        logger.info(f"Initializing {len(self._connectors)} connectors")
        
        for name, connector in self._connectors.items():
            try:
                await connector.initialize()
                logger.debug(f"Initialized connector '{name}'")
            except Exception as e:
                logger.error(f"Failed to initialize connector '{name}': {e}")
                raise
    
    async def test_all_connections(self) -> Dict[str, bool]:
        """
        Test all connector connections.
        
        Returns:
            Dict mapping connector names to test results (True/False)
        """
        results = {}
        
        for name, connector in self._connectors.items():
            try:
                result = await connector.test_connection()
                results[name] = result
                logger.debug(f"Connector '{name}' connection test: {'✓' if result else '✗'}")
            except Exception as e:
                logger.error(f"Connector '{name}' connection test failed: {e}")
                results[name] = False
        
        return results
    
    async def cleanup_all(self) -> None:
        """Cleanup all registered connectors."""
        logger.info(f"Cleaning up {len(self._connectors)} connectors")
        
        for name, connector in self._connectors.items():
            try:
                await connector.cleanup()
                logger.debug(f"Cleaned up connector '{name}'")
            except Exception as e:
                logger.error(f"Failed to cleanup connector '{name}': {e}")
    
    def get_all(self) -> Dict[str, ConnectorBase]:
        """
        Get all connectors as a dict.
        
        Returns:
            Dict mapping connector names to connector instances
        """
        return dict(self._connectors)
    
    def remove(self, name: str) -> bool:
        """
        Remove a connector from the registry.
        
        Args:
            name: Connector name
            
        Returns:
            True if connector was removed, False if not found
        """
        if name in self._connectors:
            del self._connectors[name]
            logger.info(f"Removed connector '{name}'")
            return True
        return False
    
    def __len__(self) -> int:
        """Get number of registered connectors."""
        return len(self._connectors)
    
    def __contains__(self, name: str) -> bool:
        """Check if connector is registered (supports 'in' operator)."""
        return name in self._connectors
    
    def __repr__(self) -> str:
        return f"ConnectorRegistry({len(self._connectors)} connectors)"
