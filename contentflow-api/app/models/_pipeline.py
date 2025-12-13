from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field

from ._base import CosmosBaseModel

class Pipeline(CosmosBaseModel):
    """Model representing a content processing pipeline"""
    
    name: str = Field(..., description="Pipeline name")
    description: Optional[str] = Field(default="", description="Pipeline description")
    yaml: str = Field(default=..., description="Pipeline YAML definition")
    # Visual representation (for UI)
    nodes: Optional[List[Any]] = Field(default=None, description="Pipeline nodes for visual representation")
    edges: Optional[List[Any]] = Field(default=None, description="Pipeline edges for visual representation")
    # Additional fields for pipeline metadata
    created_by: Optional[str] = Field(default=None, description="Creator of the pipeline")
    tags: Optional[List[str]] = Field(default_factory=list, description="Tags associated with the pipeline")
    version: Optional[str] = Field(default="1.0", description="Pipeline version")
    # Settings
    enabled: Optional[bool] = Field(default=True, description="Whether the pipeline is enabled")
    retry_delay: Optional[int] = Field(default=5, description="Retry delay in seconds")
    timeout: Optional[int] = Field(default=600, description="Timeout in seconds")
    retries: Optional[int] = Field(default=3, description="Number of retries")
    
    