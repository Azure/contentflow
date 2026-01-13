import importlib.metadata

from ._base import CosmosBaseModel
from ._pipeline import Pipeline
from ._executor import ExecutorCatalogDefinition, ExecutorSettingsSchema, ExecutorUIMetadata
from ._pipeline_execution import (
    PipelineExecution,
    PipelineExecutionEvent,
    ExecutorOutput,
    ExecutionStatus,
    ExecutorStatus
)
from ._vault import (
    Vault,
    VaultCreateRequest,
    VaultUpdateRequest,
    VaultExecution,
    VaultCrawlCheckpoint,
)

try:
    __version__ = importlib.metadata.version(__name__)
except importlib.metadata.PackageNotFoundError:
    __version__ = "0.0.0"  # Fallback for development mode

__all__ = [
            "CosmosBaseModel", 
            "Pipeline",
            "ExecutorCatalogDefinition",
            "ExecutorSettingsSchema",
            "ExecutorUIMetadata",
            "PipelineExecution",
            "PipelineExecutionEvent",
            "ExecutorOutput",
            "ExecutionStatus",
            "ExecutorStatus",
            "Vault",
            "VaultCreateRequest",
            "VaultUpdateRequest",
            "VaultExecution",
            "VaultCrawlCheckpoint",
          ]