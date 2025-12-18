from typing import Dict, List, Any, Optional, Literal
from pydantic import BaseModel, Field

from ._base import CosmosBaseModel


class VaultStorageConfig(BaseModel):
    """Configuration for vault storage"""
    account_name: str = Field(..., description="Storage account name")
    container_name: str = Field(..., description="Storage container name")
    credential_type: str = Field(default="default_azure_credential", description="Credential type (default_azure_credential, azure_key_credential)")
    credential_key: Optional[str] = Field(default=None, description="Storage account key (if using key credential)")

# class VaultProcessingConfig(BaseModel):
#     """Configuration for vault processing"""
#     auto_process: bool = Field(default=True, description="Automatically process uploaded documents")
#     extract_entities: bool = Field(default=True, description="Extract entities from documents")
#     generate_embeddings: bool = Field(default=True, description="Generate embeddings for documents")
#     chunk_size: int = Field(default=1000, description="Chunk size for document splitting")
#     chunk_overlap: int = Field(default=200, description="Overlap between chunks")


# class VaultStats(BaseModel):
#     """Statistics for a vault"""
#     total_documents: int = Field(default=0, description="Total number of documents")
#     total_size_bytes: int = Field(default=0, description="Total size of all documents in bytes")
#     processing_count: int = Field(default=0, description="Number of documents currently processing")
#     ready_count: int = Field(default=0, description="Number of documents ready")
#     error_count: int = Field(default=0, description="Number of documents with errors")


class Vault(CosmosBaseModel):
    """Model representing a document vault/knowledge base"""
    
    name: str = Field(..., description="Vault name")
    description: Optional[str] = Field(default="", description="Vault description")
    pipeline_id: str = Field(..., description="Pipeline ID to use for processing documents")
    pipeline_name: Optional[str] = Field(default=None, description="Pipeline name (denormalized)")
    tags: List[str] = Field(default_factory=list, description="Tags for categorization")
    
    # Storage configuration
    storage_config: Optional[VaultStorageConfig] = Field(default=None, description="Storage configuration")
    
    # # Processing configuration
    # processing_config: VaultProcessingConfig = Field(
    #     default_factory=VaultProcessingConfig, 
    #     description="Processing configuration"
    # )
    
    # Statistics
    # stats: VaultStats = Field(default_factory=VaultStats, description="Vault statistics")
    
    # Metadata
    created_by: Optional[str] = Field(default=None, description="User who created the vault")
    enabled: bool = Field(default=True, description="Whether the vault is enabled")
    

class VaultCreateRequest(BaseModel):
    """Request model for creating a vault"""
    name: str = Field(..., min_length=1, max_length=100, description="Vault name")
    description: Optional[str] = Field(default="", max_length=500, description="Vault description")
    pipeline_id: str = Field(..., description="Pipeline ID to use for processing")
    tags: List[str] = Field(default_factory=list, description="Tags for categorization")
    storage_config: Optional[dict[str, str]] = Field(default=None, description="Storage configuration")


class VaultUpdateRequest(BaseModel):
    """Request model for updating a vault"""
    name: Optional[str] = Field(default=None, min_length=1, max_length=100, description="Vault name")
    description: Optional[str] = Field(default=None, max_length=500, description="Vault description")
    tags: Optional[List[str]] = Field(default=None, description="Tags for categorization")
    enabled: Optional[bool] = Field(default=None, description="Whether the vault is enabled")

# class VaultContent(CosmosBaseModel):
#     """Model representing content/document stored in a vault"""
    
#     vault_id: str = Field(..., description="Parent vault ID")
#     name: str = Field(..., description="Content file name")
#     content_type: str = Field(..., description="Content MIME type (e.g., application/pdf)")
#     size_bytes: int = Field(..., description="File size in bytes")
    
#     # Storage location
#     blob_path: Optional[str] = Field(default=None, description="Path to blob storage")
#     blob_url: Optional[str] = Field(default=None, description="URL to access the blob")
    
#     # Processing status
#     status: Literal["pending", "processing", "ready", "error"] = Field(
#         default="pending", 
#         description="Processing status"
#     )
#     error_message: Optional[str] = Field(default=None, description="Error message if status is error")
    
#     # Processing results
#     pipeline_execution_id: Optional[str] = Field(default=None, description="Pipeline execution ID")
#     entities_extracted: Optional[int] = Field(default=None, description="Number of entities extracted")
#     chunks_created: Optional[int] = Field(default=None, description="Number of chunks created")
    
#     # Metadata
#     uploaded_by: Optional[str] = Field(default=None, description="User who uploaded the content")
#     processed_at: Optional[str] = Field(default=None, description="When processing completed")
#     metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


# class VaultCreateRequest(BaseModel):
#     """Request model for creating a vault"""
#     name: str = Field(..., min_length=1, max_length=100, description="Vault name")
#     description: Optional[str] = Field(default="", max_length=500, description="Vault description")
#     pipeline_id: str = Field(..., description="Pipeline ID to use for processing")
#     tags: List[str] = Field(default_factory=list, description="Tags for categorization")
#     storage_config: Optional[VaultStorageConfig] = Field(default=None, description="Storage configuration")
#     processing_config: Optional[VaultProcessingConfig] = Field(default=None, description="Processing configuration")


# class VaultUpdateRequest(BaseModel):
#     """Request model for updating a vault"""
#     name: Optional[str] = Field(default=None, min_length=1, max_length=100, description="Vault name")
#     description: Optional[str] = Field(default=None, max_length=500, description="Vault description")
#     pipeline_id: Optional[str] = Field(default=None, description="Pipeline ID to use for processing")
#     tags: Optional[List[str]] = Field(default=None, description="Tags for categorization")
#     processing_config: Optional[VaultProcessingConfig] = Field(default=None, description="Processing configuration")
#     enabled: Optional[bool] = Field(default=None, description="Whether the vault is enabled")


# class VaultResponse(BaseModel):
#     """Response model for vault operations"""
#     id: str
#     name: str
#     description: Optional[str]
#     pipeline_id: str
#     pipeline_name: Optional[str]
#     tags: List[str]
#     document_count: int = Field(alias="documentCount")
#     created_at: str = Field(alias="createdAt")
#     updated_at: str = Field(alias="updatedAt")
#     enabled: bool
#     stats: VaultStats
    
#     class Config:
#         populate_by_name = True


# class VaultContentResponse(BaseModel):
#     """Response model for vault content"""
#     id: str
#     name: str
#     type: str
#     size: int
#     uploaded_at: str = Field(alias="uploadedAt")
#     status: Literal["pending", "processing", "ready", "error"]
#     extracted_entities: Optional[int] = Field(default=None, alias="extractedEntities")
#     error_message: Optional[str] = Field(default=None, alias="errorMessage")
#     blob_url: Optional[str] = Field(default=None, alias="blobUrl")
    
#     class Config:
#         populate_by_name = True
