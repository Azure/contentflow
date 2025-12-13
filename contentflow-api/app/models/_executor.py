from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field

from ._base import CosmosBaseModel


class ExecutorSettingsSchema(BaseModel):
    """Schema definition for executor settings"""
    type: str
    title: str
    description: Optional[str] = None
    placeholder: Optional[str] = None
    required: Optional[bool] = None
    default: Optional[str | int | float | bool | None] = None
    ui_component: Optional[str] = None
    options: Optional[List[str]] = None
    min: Optional[int | float] = None
    max: Optional[int | float] = None
    increment: Optional[int | float] = None

class ExecutorUIMetadata(BaseModel):
    """UI metadata for executor display"""
    icon: Optional[str] = None
    description_short: Optional[str] = None
    description_long: Optional[str] = None

class ExecutorCatalogDefinition(CosmosBaseModel):
    """Executor catalog definition from YAML"""
    name: str
    description: str
    module_path: str
    class_name: str
    category: str
    version: Optional[str] = None
    tags: Optional[List[str]] = None
    settings_schema: Optional[Dict[str, ExecutorSettingsSchema]] = None
    ui_metadata: Optional[ExecutorUIMetadata] = None
    synced_at: Optional[str] = None

