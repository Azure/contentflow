from datetime import datetime, timezone
from pydantic import BaseModel, Field
from typing import Any, List, Optional

class ContentIdentifier(BaseModel):

    canonical_id : str = Field(default=..., description='Canonical identifier for the content')
    unique_id : str = Field(default=..., description='Unique identifier for the content')
    source_name : Optional[str] = Field(default=None, description='Name of the source instance of the content')
    source_type : Optional[str] = Field(default=None, description='Type of the data source (e.g., azure_blob, azure_files, sharepoint)')
    container : Optional[str] = Field(default=None, description='Container or bucket name where the content is stored')
    path : Optional[str] = Field(default=None, description='Path or location of the content within the source')
    filename: Optional[str] = Field(default=None, description='Filename of the content item')
    metadata : dict[str, object] | None = Field(default=None, description='Metadata associated with the content')

class ExecutorLogEntry(BaseModel):
    """Metadata for tracking document processing details."""
    executor_id: str = Field(default=..., description="Identifier of the executor that processed the document")
    start_time: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Start time of the processing step")
    end_time: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="End time of the processing step")
    status: str = Field(default="pending", description="Status of the processing step (e.g., pending, skipped, completed, failed)")
    details: dict[str, Any] = Field(default_factory=dict, description="Additional details about the processing step")
    errors: List[str] = Field(default_factory=list, description="List of errors encountered during processing")

class Content(BaseModel):
    """Input/Output data structure for pipeline executor steps that holds content data."""
    id: ContentIdentifier = Field(default=None, description="Content identifier for the content item")
    summary_data: dict[str, Any] = Field(default_factory=dict, description="Summary data for the content item")
    data: dict[str, Any] = Field(default_factory=dict, description="Main data dictionary for the content item")
    executor_logs: List[ExecutorLogEntry] = Field(default_factory=list, description="Execution metadata for tracking processing details")
    
    def get_status(self) -> str:
        """
        Get the overall status of the content item based on executor logs.
        If all executors completed successfully, return 'completed'.
        If no executors have run, return 'pending'.
        If any executor failed, return 'failed'.
        If all executors are either completed or skipped, return 'completed'.
        Otherwise, return 'pending'.
        """
        if not self.executor_logs:
            return "pending"
        
        # if any executor failed, document status is failed
        for log in self.executor_logs:
            if log.status == "failed":
                return "failed"
            
        # if all executors completed or skipped, content item status is completed
        for log in self.executor_logs:
            if log.status not in ("completed", "skipped"):
                return "pending"
        
        return "completed"