"""
Pipeline execution models for tracking and managing pipeline runs.
"""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from enum import Enum
from pydantic import BaseModel, Field

from ._base import CosmosBaseModel


class ExecutionStatus(str, Enum):
    """Status of pipeline execution"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class ExecutorStatus(str, Enum):
    """Status of individual executor execution"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"

class ExecutorOutput(BaseModel):
    """Output from an executor"""
    executor_id: str
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    status: ExecutorStatus
    data: Optional[Any] = None
    error: Optional[Any] = None
    duration_ms: Optional[float] = None

class PipelineExecutionEvent(BaseModel):
    """Event emitted during pipeline execution"""
    event_type: str
    executor_id: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    data: Optional[Any] = None
    error: Optional[Any] = None
    additional_info: Optional[Any] = None
    status: Optional[str] = None

class PipelineExecution(CosmosBaseModel):
    """Model for tracking pipeline execution state"""
    pipeline_id: str
    pipeline_name: str
    status: ExecutionStatus = ExecutionStatus.PENDING
    inputs: Optional[Dict[str, Any]] = None
    configuration: Optional[Dict[str, Any]] = None
    outputs: Optional[Dict[str, Any]] = None
    
    # Execution tracking
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    duration_seconds: Optional[float] = None
    error: Optional[str] = None
    
    # Executor outputs and events
    executor_outputs: Dict[str, ExecutorOutput] = Field(default_factory=dict)
    events: List[PipelineExecutionEvent] = Field(default_factory=list)
    
    # Metadata
    created_by: Optional[str] = None
    
    class Config:
        populate_by_name = True
        
