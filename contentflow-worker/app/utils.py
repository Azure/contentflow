"""
Utility functions for the ContentFlow worker.
"""
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


def create_execution_id() -> str:
    """Generate a unique execution ID"""
    import uuid
    return f"exec_{uuid.uuid4().hex[:12]}"


def create_task_id() -> str:
    """Generate a unique task ID"""
    import uuid
    return f"task_{uuid.uuid4().hex[:12]}"


def get_timestamp() -> str:
    """Get current timestamp in ISO format"""
    return datetime.now(timezone.utc).isoformat()


def format_duration(seconds: float) -> str:
    """
    Format duration in seconds to human-readable string.
    
    Args:
        seconds: Duration in seconds
        
    Returns:
        Formatted string (e.g., "2m 30s", "1h 15m 30s")
    """
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}m {secs}s"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        return f"{hours}h {minutes}m {secs}s"


def sanitize_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sanitize configuration by removing sensitive values.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        Sanitized configuration with sensitive values masked
    """
    sensitive_keys = [
        'password', 'secret', 'key', 'token', 'credential',
        'account_key', 'connection_string', 'api_key'
    ]
    
    sanitized = {}
    for k, v in config.items():
        key_lower = k.lower()
        if any(sensitive in key_lower for sensitive in sensitive_keys):
            sanitized[k] = "***REDACTED***"
        elif isinstance(v, dict):
            sanitized[k] = sanitize_config(v)
        else:
            sanitized[k] = v
    
    return sanitized


def validate_queue_config(
    queue_url: str,
    queue_name: str
) -> bool:
    """
    Validate queue configuration.
    
    Args:
        queue_url: Azure Storage Queue URL
        queue_name: Queue name
        
    Returns:
        True if valid, False otherwise
    """
    if not queue_url:
        logger.error("Queue URL is required")
        return False
    
    if not queue_name:
        logger.error("Queue name is required")
        return False
    
    if not queue_url.startswith("https://"):
        logger.error("Queue URL must start with https://")
        return False
    
    if ".queue.core.windows.net" not in queue_url:
        logger.warning("Queue URL does not appear to be an Azure Storage Queue URL")
    
    return True


def validate_cosmos_config(
    endpoint: str,
    database_name: str
) -> bool:
    """
    Validate Cosmos DB configuration.
    
    Args:
        endpoint: Cosmos DB endpoint URL
        database_name: Database name
        
    Returns:
        True if valid, False otherwise
    """
    if not endpoint:
        logger.error("Cosmos DB endpoint is required")
        return False
    
    if not database_name:
        logger.error("Database name is required")
        return False
    
    if not endpoint.startswith("https://"):
        logger.error("Cosmos DB endpoint must start with https://")
        return False
    
    if ".documents.azure.com" not in endpoint:
        logger.warning("Endpoint does not appear to be a Cosmos DB URL")
    
    return True


def retry_with_backoff(
    func,
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0
):
    """
    Retry a function with exponential backoff.
    
    Args:
        func: Function to retry
        max_retries: Maximum number of retries
        base_delay: Base delay in seconds
        max_delay: Maximum delay in seconds
        
    Returns:
        Function result if successful
        
    Raises:
        Exception: Last exception if all retries fail
    """
    import time
    
    last_exception = None
    delay = base_delay
    
    for attempt in range(max_retries + 1):
        try:
            return func()
        except Exception as e:
            last_exception = e
            
            if attempt < max_retries:
                logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {delay}s...")
                time.sleep(delay)
                delay = min(delay * 2, max_delay)
            else:
                logger.error(f"All {max_retries} retries failed")
    
    raise last_exception
