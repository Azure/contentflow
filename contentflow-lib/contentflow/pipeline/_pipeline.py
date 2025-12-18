from enum import Enum
from datetime import datetime, timezone
from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional, Union

from ..models import Content

class PipelineStatus(str, Enum):
    """Pipeline execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class PipelineEvent(BaseModel):
    """Captured pipeline event."""
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    event_type: str
    executor_id: Optional[str] = None
    data: Optional[Any] = None
    additional_info: Optional[Any] = None
    error: Optional[Any] = None

class PipelineResult(BaseModel):
    """Pipeline execution result."""
    pipeline_name: str
    status: PipelineStatus
    documents: Optional[Union[Content, List[Content]]] = None
    events: List[PipelineEvent] = Field(default_factory=list)
    start_time: datetime = None
    end_time: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        arbitrary_types_allowed = True
