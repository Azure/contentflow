"""
Base executor for document processing workflows.

This module provides the base class for all document processing executors,
integrating with the Microsoft Agent Framework's Executor pattern while
maintaining compatibility with doc-proc-lib's Document model and providing
dict-based configuration support.
"""

import hashlib
import logging
import os
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, List, Union
from typing_extensions import Never
from datetime import datetime

from agent_framework import Executor, handler, WorkflowContext

from ..models import Content

logger = logging.getLogger("doc_proc_workflow.executors.base")


class BaseExecutor(Executor, ABC):
    """
    Base executor for document processing workflows.
    
    This executor adapts the Agent Framework's Executor pattern, providing a 
    consistent interface for content processing operations within workflows 
    with dict-based configuration.
    
    Key Features:
    - Dict-based configuration with environment variable resolution
    - Error handling and logging
    - Execution statistics tracking
    - Integration with workflow context
    
    Configuration:
        Executors can be configured via a settings dict that supports:
        - Environment variable substitution: "${ENV_VAR_NAME}"
        - Nested configuration
        - Type-safe parameter access
    
    Example:
        ```python
        class MyContentProcessor(BaseExecutor):
            def __init__(self, settings: Dict[str, Any] = None):
                super().__init__(
                    id="my_processor",
                    settings=settings,
                )
                
                # Access settings with defaults
                self.output_field = self.get_setting("output_field", default="result")
                self.max_retries = self.get_setting("max_retries", default=3)
            
            async def process_contents(
                self, 
                contents: List[Document], 
                ctx: WorkflowContext
            ) -> Union[Document, List[Document]]:
                # Your processing logic
                document.summary_data["processed"] = True
                return document
        ```
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
        """
        Initialize the base executor.
        
        Args:
            id: Unique identifier for this executor
            settings: Configuration dict for the executor
            enabled: Whether this executor is enabled
            fail_on_error: Whether to fail the workflow on error
            debug_mode: Enable debug logging
            **kwargs: Additional executor configuration
        """
        super().__init__(id=id)
        
        self.settings = settings or {}
        self.enabled = enabled
        self.fail_on_error = fail_on_error
        self.debug_mode = debug_mode
        self.params = kwargs
        
        if self.debug_mode:
            logger.debug(
                f"Initialized BaseExecutor: {id} "
                f"(enabled: {self.enabled})"
            )
    
    def _resolve_setting_value(self, value: Any) -> Any:
        """
        Resolve a setting value, supporting environment variable substitution.
        
        Settings can use ${ENV_VAR_NAME} syntax to reference environment
        variables, which will be automatically resolved.
        
        Args:
            value: The setting value to resolve
            
        Returns:
            Resolved setting value
        """
        if isinstance(value, str) and value.startswith('${') and value.endswith('}'):
            env_var_name = value[2:-1]
            resolved_value = os.getenv(env_var_name)
            
            if resolved_value is None:
                logger.warning(
                    f"Environment variable '{env_var_name}' not set for executor '{self.id}'"
                )
                return value
            
            return resolved_value
        
        return value
    
    def get_setting(
        self,
        setting_key: str,
        default: Any = None,
        required: bool = False
    ) -> Any:
        """
        Get a setting value with optional default and environment variable resolution.
        
        Args:
            setting_key: Setting key to retrieve
            default: Default value if not found
            required: Whether this setting is required
            
        Returns:
            Setting value or default
            
        Raises:
            ValueError: If required setting is missing
        """
        value = self.settings.get(setting_key, default)
        
        if value is None and required:
            raise ValueError(
                f"Required setting '{setting_key}' not found for executor '{self.id}'"
            )
        
        return self._resolve_setting_value(value)
    
    def try_extract_nested_field_from_content(
        self,
        content: Content,
        field_path: str
    ) -> Any:
        """
        Extract a nested field value from a Content item's data.
        
        Args:
            content: Content item to extract from
            field_path: Dot-separated path to the field
        Returns:
            Extracted field value or None if not found
        """
        fields = field_path.split('.')
        current_value = content.data
        
        for field in fields:
            if isinstance(current_value, dict) and field in current_value:
                current_value = current_value[field]
            else:
                return None
        
        return current_value
    
    
    def generate_sha1_hash(self, input_string: str) -> str:
        """
        Generate a SHA1 hash from a given string.
        
        Args:
            input_string: String to hash
            
        Returns:
            SHA1 hash as hexadecimal string
        """
        encoded_string = input_string.encode('utf-8')
        sha1_hash = hashlib.sha1()
        sha1_hash.update(encoded_string)
        return sha1_hash.hexdigest()
    
    @handler
    async def handle_content(
        self,
        input: Union[Content, List[Content]],
        ctx: WorkflowContext[Union[Content, List[Content]], Union[Content, List[Content]]]
    ) -> None:
        """
        Main handler for content processing.
        
        This is the entry point called by the Agent Framework workflow engine.
        It orchestrates the content processing lifecycle including error handling,
        logging, and statistics tracking.
        
        Args:
            input: The content or list of contents to process
            ctx: The workflow execution context
        """
        if not self.enabled:
            if self.debug_mode:
                logger.info(f"Executor {self.id} is disabled, skipping execution.")
            
            # Send the original input unmodified downstream
            await ctx.send_message(input)
            
            # Yield the original input as output of this executor
            await ctx.yield_output(input)
            return
        
        start_time = datetime.now()
        
        try:
            if self.debug_mode:
                logger.debug(f"Executor {self.id} processing input: {input.id if isinstance(input, Content) else f'{len(input)} document(s)'}")
            
            # Call the abstract process_input method
            processed_content = await self.process_input(input, ctx)
            
            # Validate output
            if not isinstance(processed_content, Content) and not (isinstance(processed_content, list) and all(isinstance(doc, Content) for doc in processed_content)):
                raise TypeError(
                    f"Executor {self.id} must return a Content instance or a list of Content instances, "
                    f"got {type(processed_content)}"
                )
            
            # Update statistics
            elapsed = (datetime.now() - start_time).total_seconds()
            
            # Send the processed content item(s) downstream
            await ctx.send_message(processed_content)
            
            logger.info(
                    f"Executor {self.id} completed {input.id if isinstance(input, Content) else f'{len(input)} content item(s)'} "
                    f"in {elapsed:.2f}s"
                )
            
            # Yield the processed content item(s) as output
            await ctx.yield_output(processed_content)
            
        except Exception as e:
            elapsed = (datetime.now() - start_time).total_seconds()
            
            logger.error(
                f"Executor {self.id} failed processing input {input.id if isinstance(input, Content) else f'{len(input)} content item(s)'} "
                f"after {elapsed:.2f}s: {str(e)}",
                exc_info=True
            )
            
            if self.fail_on_error:
                raise
            else:
                # Pass through the original document if error is not fatal
                await ctx.send_message(input)
                await ctx.yield_output(input)
    
    @abstractmethod
    async def process_input(
        self,
        input: Union[Content, List[Content]],
        ctx: WorkflowContext[Union[Content, List[Content]], Union[Content, List[Content]]]
    ) -> Union[Content, List[Content]]:
        """
        Process a single content item or a list of content items.
        
        This method must be implemented by subclasses to define the
        specific content processing logic.
        
        Args:
            input: The content item or list of content items to process
            ctx: The workflow execution context providing access to:
                - Shared state
                - Message passing capabilities
        
        Returns:
            The processed content item or a list of processed content items
            
        Raises:
            Exception: If processing fails and fail_on_error is True
        """
        raise NotImplementedError("Subclasses must implement process_input method")
    
    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}(id='{self.id}', "
            f"enabled={self.enabled}"
        )
