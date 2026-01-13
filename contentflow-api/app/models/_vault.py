from typing import Dict, List, Any, Optional, Literal
import uuid
from pydantic import BaseModel, Field

from ._base import CosmosBaseModel


class Vault(CosmosBaseModel):
    """Model representing a document vault/knowledge base"""
    
    name: str = Field(..., description="Vault name")
    description: Optional[str] = Field(default="", description="Vault description")
    pipeline_id: str = Field(..., description="Pipeline ID to use for processing documents")
    pipeline_name: Optional[str] = Field(default=None, description="Pipeline name (denormalized)")
    tags: List[str] = Field(default_factory=list, description="Tags for categorization")
    save_execution_output: Optional[bool] = Field(default=False, description="Whether to save execution output in cosmos db")
    # Metadata
    created_by: Optional[str] = Field(default=None, description="User who created the vault")
    enabled: bool = Field(default=True, description="Whether the vault is enabled")
    

class VaultCreateRequest(BaseModel):
    """Request model for creating a vault"""
    name: str = Field(..., min_length=1, max_length=100, description="Vault name")
    description: Optional[str] = Field(default="", max_length=500, description="Vault description")
    pipeline_id: str = Field(..., description="Pipeline ID to use for processing")
    save_execution_output: Optional[bool] = Field(default=False, description="Whether to save execution output in cosmos db")
    tags: List[str] = Field(default_factory=list, description="Tags for categorization")
    enabled: Optional[bool] = Field(default=True, description="Whether the vault is enabled")


class VaultUpdateRequest(BaseModel):
    """Request model for updating a vault"""
    name: Optional[str] = Field(default=None, min_length=1, max_length=100, description="Vault name")
    description: Optional[str] = Field(default=None, max_length=500, description="Vault description")
    tags: Optional[List[str]] = Field(default=None, description="Tags for categorization")
    save_execution_output: Optional[bool] = Field(default=None, description="Whether to save execution output in cosmos db")
    enabled: Optional[bool] = Field(default=None, description="Whether the vault is enabled")


class VaultExecution(CosmosBaseModel):
    """Model representing a vault execution"""
    pipeline_id: str = Field(..., description="ID of the pipeline used for execution")
    pipeline_name: str = Field(..., description="Name of the pipeline used for execution")
    vault_id: str = Field(..., description="ID of the vault being executed")
    status: Literal["pending", "running", "completed", "failed"] = Field(..., description="Execution status")
    status_message: Optional[str] = Field(default=None, description="Detailed status message")
    task_id: Optional[str] = Field(default=None, description="ID of the associated processing task")
    source_worker_id: Optional[str] = Field(default=None, description="ID of the source worker that handled the execution")
    processing_worker_id: Optional[str] = Field(default=None, description="ID of the processing worker that handled the execution")
    created_by: Optional[str] = Field(default=None, description="User who initiated the execution")
    error: Optional[str] = Field(default=None, description="Error message if execution failed")
    executor_outputs: Dict[str, Any] = Field(default_factory=dict, description="Outputs from executors")
    events: List[Dict[str, Any]] = Field(default_factory=list, description="Event log for the execution")
    started_at: Optional[str] = Field(default=None, description="Timestamp when execution started")
    completed_at: Optional[str] = Field(default=None, description="Timestamp when execution completed")
    content: Optional[List[Dict[str, Any]]] = Field(default=None, description="Detailed content of the execution")
    number_of_items: Optional[int] = Field(default=None, description="Number of content items processed in the execution")

class VaultCrawlCheckpoint(BaseModel):
    """Model representing a vault crawl checkpoint"""
    id: str = Field(..., description="Unique identifier for the checkpoint")
    pipeline_id: str = Field(..., description="ID of the pipeline used for crawling")
    vault_id: str = Field(..., description="ID of the vault being crawled")
    executor_id: str = Field(..., description="ID of the executor performing the crawl")
    checkpoint_timestamp: str = Field(..., description="Timestamp of the checkpoint")
    worker_id: str = Field(..., description="ID of the worker that created the checkpoint")
    