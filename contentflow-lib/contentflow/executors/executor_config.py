"""
Executor configuration models.

Provides Pydantic models for executor catalog configuration.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, ValidationError
import yaml
import logging

logger = logging.getLogger("contentflow.lib.executors.executor_config")


class SettingSchema(BaseModel):
    """Schema definition for an executor setting."""
    type: str
    title: str
    description: str
    required: bool = False
    default: Optional[Any] = None
    options: Optional[List[str]] = None
    min: Optional[float] = None
    max: Optional[float] = None
    items: Optional[Dict[str, Any]] = None
    ui_component: str = "input"


class UIMetadata(BaseModel):
    """UI metadata for executor."""
    icon: str
    description_short: str
    description_long: str


class ExecutorConfig(BaseModel):
    """
    Configuration for an executor type in the catalog.
    
    Defines the executor's properties, settings schema, and metadata
    for dynamic loading and UI generation.
    """
    id: str
    name: str
    description: str
    module_path: str
    class_name: str
    tags: List[str] = Field(default_factory=list)
    category: str
    version: str
    settings_schema: Dict[str, SettingSchema] = Field(default_factory=dict)
    ui_metadata: Optional[UIMetadata] = None
    
    @classmethod
    def from_file(cls, file_path: str) -> List["ExecutorConfig"]:
        """
        Load executor configurations from YAML file.
        
        Args:
            file_path: Path to executor catalog YAML file
            
        Returns:
            List of ExecutorConfig objects
        """
        try:
            with open(file_path, 'r') as f:
                data = yaml.safe_load(f)
            
            if not data or 'executor_catalog' not in data:
                logger.warning(f"No executor_catalog found in {file_path}")
                return []
            
            executor_configs = []
            for executor_data in data['executor_catalog']:
                # Convert settings_schema dict to SettingSchema objects
                if 'settings_schema' in executor_data:
                    settings_schema = {}
                    for key, value in executor_data['settings_schema'].items():
                        settings_schema[key] = SettingSchema(**value)
                    executor_data['settings_schema'] = settings_schema
                
                # Convert ui_metadata to UIMetadata object
                if 'ui_metadata' in executor_data:
                    executor_data['ui_metadata'] = UIMetadata(**executor_data['ui_metadata'])
                
                executor_config = cls(**executor_data)
                executor_configs.append(executor_config)
            
            logger.info(f"Loaded {len(executor_configs)} executor configurations from {file_path}")
            return executor_configs
        
        except ValidationError as ve:
            logger.error(f"Validation error loading executor configurations from {file_path}: {ve}")
            logger.error(ve.json())
            logger.exception(ve)
            raise
        
        except Exception as e:
            logger.error(f"Failed to load executor configurations from {file_path}: {e}")
            logger.exception(e)
            raise
    
    def validate_settings(self, settings: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate settings against schema and apply defaults.
        
        Args:
            settings: Settings dict to validate
            
        Returns:
            Validated settings with defaults applied
        """
        validated = {}
        
        for key, schema in self.settings_schema.items():
            value = settings.get(key)
            
            # Check required
            if schema.required and value is None:
                raise ValueError(
                    f"Required setting '{key}' missing for executor '{self.id}'"
                )
            
            # Apply default
            if value is None:
                value = schema.default
            
            # Type validation
            if value is not None:
                if schema.type == 'integer' and not isinstance(value, int):
                    try:
                        value = int(value)
                    except (ValueError, TypeError):
                        raise ValueError(
                            f"Setting '{key}' must be integer, got {type(value)}"
                        )
                
                elif schema.type == 'number' and not isinstance(value, (int, float)):
                    try:
                        value = float(value)
                    except (ValueError, TypeError):
                        raise ValueError(
                            f"Setting '{key}' must be number, got {type(value)}"
                        )
                
                elif schema.type == 'boolean' and not isinstance(value, bool):
                    if isinstance(value, str):
                        value = value.lower() in ('true', '1', 'yes')
                    else:
                        raise ValueError(
                            f"Setting '{key}' must be boolean, got {type(value)}"
                        )
                
                elif schema.type == 'string' and not isinstance(value, str):
                    value = str(value)
                
                # Range validation
                if schema.min is not None and value < schema.min:
                    raise ValueError(
                        f"Setting '{key}' must be >= {schema.min}, got {value}"
                    )
                
                if schema.max is not None and value > schema.max:
                    raise ValueError(
                        f"Setting '{key}' must be <= {schema.max}, got {value}"
                    )
                
                # Options validation
                if schema.options and (schema.required and value not in schema.options):
                    raise ValueError(
                        f"Setting '{key}' must be one of {schema.options}, got {value}"
                    )
            
            validated[key] = value
        
        # Include any additional settings not in schema
        for key, value in settings.items():
            if key not in validated:
                validated[key] = value
        
        return validated
    
    def get_setting_info(self, setting_name: str) -> Optional[SettingSchema]:
        """Get schema info for a specific setting."""
        return self.settings_schema.get(setting_name)
    
    def list_required_settings(self) -> List[str]:
        """Get list of required setting names."""
        return [
            key for key, schema in self.settings_schema.items()
            if schema.required
        ]
    
    def get_default_settings(self) -> Dict[str, Any]:
        """Get dict of all default settings."""
        return {
            key: schema.default
            for key, schema in self.settings_schema.items()
            if schema.default is not None
        }


class ExecutorInstanceConfig(BaseModel):
    """
    Configuration for a specific executor instance in a workflow.
    
    References an ExecutorConfig by ID and provides instance-specific settings.
    """
    id: str  # Instance ID (unique within workflow)
    type: str  # Executor type (references ExecutorConfig.id)
    settings: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        extra = "allow"  # Allow additional fields
