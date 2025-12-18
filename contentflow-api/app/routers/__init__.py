import importlib.metadata

from .health import router as health_router
from .pipelines import router as pipelines_router
from .executors import router as executors_router
from .vaults import router as vaults_router

try:
    __version__ = importlib.metadata.version(__name__)
except importlib.metadata.PackageNotFoundError:
    __version__ = "0.0.0"  # Fallback for development mode

__all__ = [
            "health_router",
            "pipelines_router",
            "executors_router",
            "vaults_router",
          ]