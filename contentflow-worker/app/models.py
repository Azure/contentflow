"""
Task models for the ContentFlow worker engine.

This module defines the data structures for processing tasks that are
queued and processed by worker processes.
"""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from enum import Enum
from pydantic import BaseModel, Field

from contentflow.models import Content


class TaskType(str, Enum):
    """Type of task to be processed"""
    CONTENT_PROCESSING = "content_processing"
    INPUT_SOURCE_LOADING = "input_source_loading"


class TaskPriority(str, Enum):
    """Priority levels for task processing"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class TaskStatus(str, Enum):
    """Status of task processing"""
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"


class ContentProcessingTask(BaseModel):
    """
    Task for processing a content item through a pipeline.
    
    This task is created by input source workers and consumed by
    content processing workers.
    """
    task_id: str = Field(description="Unique identifier for this task")
    task_type: TaskType = TaskType.CONTENT_PROCESSING
    priority: TaskPriority = TaskPriority.NORMAL
    
    # Pipeline execution details
    pipeline_id: str = Field(description="ID of the pipeline to execute")
    pipeline_name: str = Field(description="Name of the pipeline")
    execution_id: str = Field(description="ID of the pipeline execution")
    vault_id: Optional[str] = Field(default=None, description="ID of the vault associated with this content")
    
    # Input content details
    content: List[Content] = Field(description="List of content items to process")

    # Executor tracking
    executed_input_executor: Optional[str] = Field(default=None, description="ID of input executor already executed")
    
    # Metadata
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    retry_count: int = Field(default=0, description="Number of retry attempts")
    max_retries: int = Field(default=3, description="Maximum number of retries")
    
    class Config:
        use_enum_values = True


class InputSourceTask(BaseModel):
    """
    Task for loading content from an input source.
    
    This task instructs an input source worker to scan a source
    (e.g., Azure Blob Storage) and create content processing tasks.
    """
    task_id: str = Field(description="Unique identifier for this task")
    task_type: TaskType = TaskType.INPUT_SOURCE_LOADING
    priority: TaskPriority = TaskPriority.NORMAL
    
    # Source configuration
    source_type: str = Field(description="Type of input source (e.g., azure_blob, azure_files)")
    source_name: str = Field(description="Name/identifier of the source")
    source_config: Dict[str, Any] = Field(description="Configuration for the source")
    
    # Pipeline to execute on discovered content
    pipeline_id: str = Field(description="ID of the pipeline to execute for each content item")
    pipeline_name: str = Field(description="Name of the pipeline")
    
    # Filtering options
    filters: Optional[Dict[str, Any]] = Field(default=None, description="Filters for content discovery")
    
    # Metadata
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    
    class Config:
        use_enum_values = True


class TaskMessage(BaseModel):
    """
    Generic task message envelope for queue messages.
    
    This wrapper allows us to handle different task types
    with a single queue structure.
    """
    task_type: TaskType
    payload: Dict[str, Any] = Field(description="Task payload (serialized task)")
    
    class Config:
        use_enum_values = True
