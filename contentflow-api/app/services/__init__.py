import importlib.metadata

from .base_service import BaseService
from .health_service import HealthService
from .pipeline_service import PipelineService
from .vault_service import VaultService

try:
    __version__ = importlib.metadata.version(__name__)
except importlib.metadata.PackageNotFoundError:
    __version__ = "0.0.0"  # Fallback for development mode

__all__ = [
            "BaseService",
            "HealthService",
            "PipelineService",
            "VaultService"
          ]