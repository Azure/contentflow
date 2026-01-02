"""
Executor registry for managing executor configurations and instances.

Similar to StepRegistry in doc-proc-lib, provides dynamic executor loading
from catalog and instance creation.
"""

import logging
import importlib
from typing import Dict, List, Optional, Type, Any
from pathlib import Path

from .executor_config import ExecutorConfig, ExecutorInstanceConfig
from .base import BaseExecutor

logger = logging.getLogger("contentflow.executors.executor_registry")

DEFAULT_CATALOG_PATH = f'{Path(__file__).parent.parent.parent}/executor_catalog.yaml'

class ExecutorRegistry:
    """
    Registry for managing executor configurations and instances.
    
    Provides:
    - Loading executor definitions from catalog YAML
    - Dynamic executor class loading
    - Executor instance creation with validation
    - Caching of executor instances
    """
    
    def __init__(self):
        """Initialize the executor registry."""
        self._executors: Dict[str, ExecutorConfig] = {}
        self._instances: Dict[str, BaseExecutor] = {}
        self._loaded_classes: Dict[str, Type[BaseExecutor]] = {}

    @classmethod
    def load_default_catalog(cls) -> 'ExecutorRegistry':
        """Load the default executor catalog."""
        return cls.load_from_yaml(DEFAULT_CATALOG_PATH)
    
    @classmethod
    def load(cls, executor_configs: List[ExecutorConfig]) -> 'ExecutorRegistry':
        """
        Load multiple executor configurations into the registry.
        
        Args:
            executor_configs: List of ExecutorConfig objects
            
        Returns:
            ExecutorRegistry instance with loaded configurations
        """
        registry = cls()
        for config in executor_configs:
            registry._executors[config.id] = config
            logger.debug(f"Loaded executor config: {config.id}")
        return registry
    
    @classmethod
    def load_from_yaml(cls, file_path: str) -> 'ExecutorRegistry':
        """
        Load executor configurations from YAML catalog file.
        
        Args:
            file_path: Path to executor_catalog.yaml
            
        Returns:
            ExecutorRegistry instance with loaded configurations
        """
        registry = cls()
        try:
            executor_configs = ExecutorConfig.from_file(file_path)
            registry._executors = {
                config.id: config for config in executor_configs
            }
            
            logger.info(
                f"Loaded {len(registry._executors)} executor configurations from {file_path}"
            )
            
        except Exception as e:
            logger.error(f"Failed to load executor catalog from {file_path}: {e}")
            raise
        
        return registry
    
    def register_executor(self, executor_config: ExecutorConfig) -> None:
        """
        Register a single executor configuration.
        
        Args:
            executor_config: ExecutorConfig to register
        """
        self._executors[executor_config.id] = executor_config
        logger.info(f"Registered executor: {executor_config.id}")
    
    def get_executor_config(self, executor_id: str) -> Optional[ExecutorConfig]:
        """
        Get executor configuration by ID.
        
        Args:
            executor_id: Executor type ID
            
        Returns:
            ExecutorConfig or None if not found
        """
        return self._executors.get(executor_id)
    
    def list_executors(self) -> List[ExecutorConfig]:
        """Get list of all registered executor configurations."""
        return list(self._executors.values())
    
    def list_executor_ids(self) -> List[str]:
        """Get list of all registered executor IDs."""
        return list(self._executors.keys())
    
    def _load_executor_class(
        self,
        executor_config: ExecutorConfig
    ) -> Type[BaseExecutor]:
        """
        Dynamically load executor class from module path.
        
        Args:
            executor_config: Executor configuration
            
        Returns:
            Executor class
        """
        # Check cache first
        if executor_config.id in self._loaded_classes:
            return self._loaded_classes[executor_config.id]
        
        try:
            # Import module
            module = importlib.import_module(executor_config.module_path)
            
            # Get class
            executor_class = getattr(module, executor_config.class_name)
            
            # Validate it's a BaseExecutor subclass
            if not issubclass(executor_class, BaseExecutor):
                raise TypeError(
                    f"Class {executor_config.class_name} is not a BaseExecutor subclass"
                )
            
            # Cache the class
            self._loaded_classes[executor_config.id] = executor_class
            
            logger.debug(
                f"Loaded executor class: {executor_config.class_name} "
                f"from {executor_config.module_path}"
            )
            
            return executor_class
            
        except Exception as e:
            logger.error(
                f"Failed to load executor class for '{executor_config.id}': {e}"
            )
            raise
    
    def create_executor_instance(
        self,
        executor_id: str,
        instance_config: ExecutorInstanceConfig
    ) -> BaseExecutor:
        """
        Create an executor instance from registered configuration.
        
        Args:
            executor_id: Executor type ID from catalog
            instance_config: Instance-specific configuration
            
        Returns:
            DocumentExecutor instance
            
        Raises:
            ValueError: If executor not found or configuration invalid
        """
        # Get executor config
        executor_config = self.get_executor_config(executor_id)
        if not executor_config:
            raise ValueError(
                f"Executor configuration not found: {executor_id}. "
                f"Available: {list(self._executors.keys())}"
            )
        
        # Validate settings
        try:
            validated_settings = executor_config.validate_settings(
                instance_config.settings
            )
        except Exception as e:
            logger.error(
                f"Settings validation failed for executor '{executor_id}': {e}"
            )
            raise
        
        # Load executor class
        executor_class = self._load_executor_class(executor_config)
        
        # Create instance
        try:
            instance = executor_class(
                id=instance_config.id,
                settings=validated_settings
            )
            
            # Cache the instance
            cache_key = f"{executor_id}_{instance_config.id}"
            self._instances[cache_key] = instance
            
            logger.info(
                f"Created executor instance: {instance_config.id} "
                f"(type: {executor_config.class_name})"
            )
            
            return instance
            
        except Exception as e:
            logger.error(
                f"Failed to create executor instance '{instance_config.id}': {e}"
            )
            raise
    
    def get_cached_instance(
        self,
        executor_id: str,
        instance_id: str
    ) -> Optional[BaseExecutor]:
        """
        Get a cached executor instance.
        
        Args:
            executor_id: Executor type ID
            instance_id: Instance ID
            
        Returns:
            Cached executor instance or None
        """
        cache_key = f"{executor_id}_{instance_id}"
        return self._instances.get(cache_key)
    
    def remove_cached_instance(
        self,
        executor_id: str,
        instance_id: str
    ) -> None:
        """
        Remove a cached executor instance.
        
        Args:
            executor_id: Executor type ID
            instance_id: Instance ID
        """
        cache_key = f"{executor_id}_{instance_id}"
        if cache_key in self._instances:
            del self._instances[cache_key]
            logger.debug(f"Removed cached instance: {cache_key}")
    
    def clear_cache(self) -> None:
        """Clear all cached executor instances."""
        count = len(self._instances)
        self._instances.clear()
        logger.debug(f"Cleared {count} cached executor instances")
    
    def get_executors_by_category(self, category: str) -> List[ExecutorConfig]:
        """
        Get all executors of a specific category.
        
        Args:
            category: Category name (e.g., "Input", "Processor", "Output")
            
        Returns:
            List of matching ExecutorConfig objects
        """
        return [
            config for config in self._executors.values()
            if config.category == category
        ]
    
    def get_executors_by_tag(self, tag: str) -> List[ExecutorConfig]:
        """
        Get all executors with a specific tag.
        
        Args:
            tag: Tag name
            
        Returns:
            List of matching ExecutorConfig objects
        """
        return [
            config for config in self._executors.values()
            if tag in config.tags
        ]
        
    def get_executor_info(self, executor_id: str) -> Optional[ExecutorConfig]:
        """
        Get detailed executor configuration by ID.
        
        Args:
            executor_id: Executor type ID
            
        Returns:
            ExecutorConfig or None if not found
        """
        return self._executors.get(executor_id)
        
    def __len__(self) -> int:
        """Get number of registered executors."""
        return len(self._executors)
    
    def __contains__(self, executor_id: str) -> bool:
        """Check if executor ID is registered."""
        return executor_id in self._executors


# # Global registry instance
# _executor_registry = ExecutorRegistry()

# def get_executor_registry() -> ExecutorRegistry:
#     """Get the global executor registry instance."""
#     return _executor_registry

# def load_executor_catalog(file_path: str = "executor_catalog.yaml") -> None:
#     """
#     Load executors from catalog file into global registry.
    
#     Args:
#         file_path: Path to executor catalog YAML file
#     """
#     _executor_registry.load_from_yaml(file_path)
