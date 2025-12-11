import importlib.metadata

from ._base import CosmosBaseModel
from ._pipeline import Pipeline

try:
    __version__ = importlib.metadata.version(__name__)
except importlib.metadata.PackageNotFoundError:
    __version__ = "0.0.0"  # Fallback for development mode

__all__ = [
            "CosmosBaseModel", 
            "Pipeline", 
          ]