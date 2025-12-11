"""Content retriever executor for downloading content from sources."""

from datetime import datetime
import logging
import os
import tempfile
from pathlib import Path
from typing import Dict, Any, List, Optional, Union

from agent_framework import WorkflowContext

from .base import BaseExecutor
from ..models import Content, ExecutorLogEntry
    
logger = logging.getLogger(__name__)


class PassThroughExecutor(BaseExecutor):
    """
    Dummy executor that passes through the document unchanged.
    
    Configuration (settings dict):
        - No specific settings for this executor.
    
    Example:
        ```python
        executor = PassThroughExecutor(
            settings={
                # No specific settings
            },
        )
        
    Input:
        Document or List[Document] each with (ContentIdentifier) id containing:
        - canonical_id: Unique document ID
    
    Output:
        Document or List[Document] with unchanged fields.
    """
    
    def __init__(
        self,
        id: str,
        settings: Optional[Dict[str, Any]] = None,
        enabled: bool = True,
        fail_on_error: bool = False,
        debug_mode: bool = False,
        **kwargs
    ):
        super().__init__(
            id=id,
            settings=settings,
            enabled=enabled,
            fail_on_error=fail_on_error,
            debug_mode=debug_mode,
            **kwargs
        )
        
        if self.debug_mode:
            logger.debug(
                f"PassThroughExecutor with id {self.id} initialized."
            )
    
    async def process_input(
        self,
        input: Union[Content, List[Content]],
        ctx: WorkflowContext[Union[Content, List[Content]], Union[Content, List[Content]]]
    ) -> Union[Content, List[Content]]:
        """Pass through the document(s) unchanged."""
        
        if self.debug_mode:
            logger.debug(
                f"Passing through document(s) unchanged."
            )
        
        start_time = datetime.now()
            
        if isinstance(input, list):
            results = []
            for item in input:
                item.executor_logs.append(ExecutorLogEntry(
                    executor_id=self.id,
                    start_time=start_time,
                    end_time=datetime.now(),
                    status="completed",
                    details={},
                    errors=[]
                ))
                results.append(item)
            return results
        else:
            # Single document processing
            result = input
            result.executor_logs.append(ExecutorLogEntry(
                executor_id=self.id,
                start_time=start_time,
                end_time=datetime.now(),
                status="completed",
                details={},
                errors=[]
            ))
            return result
        