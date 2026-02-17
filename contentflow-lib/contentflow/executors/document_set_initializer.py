"""Document Set Initializer executor for stamping set metadata on Content items."""

import logging
import re
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List, Union

from agent_framework import WorkflowContext

from .base import BaseExecutor
from ..models import Content, ContentIdentifier, ExecutorLogEntry

logger = logging.getLogger("contentflow.executors.document_set_initializer")


class DocumentSetInitializerExecutor(BaseExecutor):
    """
    Initialize document set metadata on a list of Content items.
    
    Takes a List[Content] (from discovery/input) and stamps each item with
    document set metadata in summary_data. Optionally auto-detects ordering
    from filenames, blob metadata, or user-provided mappings.
    
    Configuration (settings dict):
        - set_id (str): Explicit set ID.
          Default: auto-generated UUID
        - set_name (str): Human-readable name for the document set.
          Default: None
        - ordering_strategy (str): How to determine document order.
          Options: "filename_alpha", "filename_numeric", "explicit_mapping",
                   "last_modified", "input_order"
          Default: "filename_alpha"
        - role_field (str): Metadata field or filename pattern to extract role.
          Default: None (uses filename stem)
        - role_mapping (dict): Explicit mapping of filename patterns to roles.
          Example: {"Q1": "Q1_2024", "Q2": "Q2_2024", ...}
          Default: None
        - validate_set_size (int): Expected number of documents. 0 = no validation.
          Default: 0
        
        Also settings from BaseExecutor apply.
    
    Example:
        ```yaml
        - id: init_set
          type: document_set_initializer
          settings:
            set_name: "FY2024 Quarterly Reports"
            ordering_strategy: filename_alpha
            role_mapping:
              "Q1": "Q1_2024"
              "Q2": "Q2_2024"
              "Q3": "Q3_2024"
              "Q4": "Q4_2024"
            validate_set_size: 4
        ```
    
    Input:
        List[Content] — a list of content items to be tagged as a document set
        
    Output:
        List[Content] — the same content items with document_set_* metadata
        added to each item's summary_data:
        - document_set_id (str): Unique identifier for the set
        - document_set_name (str): Human-readable name for the set
        - document_set_role (str): Role/label of this document in the set
        - document_set_order (int): Ordering index (0-based)
        - document_set_total (int): Total number of documents in the set
    """
    
    def __init__(
        self,
        id: str,
        settings: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        super().__init__(
            id=id,
            settings=settings,
            **kwargs
        )
        
        self.set_id = self.get_setting("set_id", default=None)
        self.set_name = self.get_setting("set_name", default=None)
        self.ordering_strategy = self.get_setting("ordering_strategy", default="filename_alpha")
        self.role_field = self.get_setting("role_field", default=None)
        self.role_mapping = self.get_setting("role_mapping", default=None)
        self.validate_set_size = self.get_setting("validate_set_size", default=0)
        
        # Validate ordering strategy
        valid_strategies = [
            "filename_alpha", "filename_numeric", "explicit_mapping",
            "last_modified", "input_order"
        ]
        if self.ordering_strategy not in valid_strategies:
            raise ValueError(
                f"{self.id}: Invalid ordering_strategy '{self.ordering_strategy}'. "
                f"Must be one of: {', '.join(valid_strategies)}"
            )
        
        if self.debug_mode:
            logger.debug(
                f"DocumentSetInitializerExecutor {self.id} initialized: "
                f"set_name={self.set_name}, ordering={self.ordering_strategy}"
            )
    
    async def process_input(
        self,
        input: Union[Content, List[Content]],
        ctx: WorkflowContext[Union[Content, List[Content]], Union[Content, List[Content]]]
    ) -> List[Content]:
        """
        Stamp document set metadata on each Content item.
        
        Args:
            input: Content item or list of content items to tag
            ctx: Workflow context
            
        Returns:
            List[Content] with document_set_* metadata in summary_data
        """
        start_time = datetime.now()
        
        # Normalize to list
        if isinstance(input, Content):
            content_items = [input]
        else:
            content_items = list(input)
        
        if not content_items:
            logger.warning(f"{self.id}: Received empty input, nothing to initialize")
            return content_items
        
        # Validate set size if configured
        if self.validate_set_size > 0 and len(content_items) != self.validate_set_size:
            raise ValueError(
                f"{self.id}: Expected {self.validate_set_size} documents in set, "
                f"but received {len(content_items)}"
            )
        
        # Generate or use provided set ID
        set_id = self.set_id or str(uuid.uuid4())
        set_name = self.set_name or f"document_set_{set_id[:8]}"
        total_documents = len(content_items)
        
        # Order the content items
        ordered_items = self._order_content_items(content_items)
        
        # Stamp metadata on each item
        for order_index, content in enumerate(ordered_items):
            role = self._determine_role(content, order_index)
            
            content.summary_data["document_set_id"] = set_id
            content.summary_data["document_set_name"] = set_name
            content.summary_data["document_set_role"] = role
            content.summary_data["document_set_order"] = order_index
            content.summary_data["document_set_total"] = total_documents
            
            # Add executor log entry
            content.executor_logs.append(ExecutorLogEntry(
                executor_id=self.id,
                start_time=start_time,
                end_time=datetime.now(),
                status="completed",
                details={
                    "set_id": set_id,
                    "role": role,
                    "order": order_index,
                    "total": total_documents
                },
                errors=[]
            ))
            
            if self.debug_mode:
                logger.debug(
                    f"{self.id}: Tagged content '{content.id.canonical_id}' "
                    f"as role='{role}', order={order_index}/{total_documents}"
                )
        
        elapsed = (datetime.now() - start_time).total_seconds()
        logger.info(
            f"{self.id}: Initialized document set '{set_name}' with "
            f"{total_documents} documents in {elapsed:.2f}s"
        )
        
        return ordered_items
    
    def _order_content_items(self, items: List[Content]) -> List[Content]:
        """
        Order content items according to the configured ordering strategy.
        
        Args:
            items: List of Content items to order
            
        Returns:
            Ordered list of Content items
        """
        if self.ordering_strategy == "input_order":
            return items
        
        elif self.ordering_strategy == "filename_alpha":
            return sorted(
                items,
                key=lambda c: (c.id.filename or c.id.path or c.id.canonical_id).lower()
            )
        
        elif self.ordering_strategy == "filename_numeric":
            return sorted(
                items,
                key=lambda c: self._extract_numeric_key(
                    c.id.filename or c.id.path or c.id.canonical_id
                )
            )
        
        elif self.ordering_strategy == "last_modified":
            return sorted(
                items,
                key=lambda c: (
                    c.id.metadata.get("last_modified", datetime.min)
                    if c.id.metadata else datetime.min
                )
            )
        
        elif self.ordering_strategy == "explicit_mapping":
            if not self.role_mapping:
                logger.warning(
                    f"{self.id}: explicit_mapping strategy requires role_mapping, "
                    f"falling back to input_order"
                )
                return items
            
            # Order by the position of matched role in the role_mapping keys
            mapping_keys = list(self.role_mapping.keys())
            
            def mapping_order(content: Content) -> int:
                filename = content.id.filename or content.id.path or ""
                for idx, pattern in enumerate(mapping_keys):
                    if pattern.lower() in filename.lower():
                        return idx
                return len(mapping_keys)  # unmapped items go last
            
            return sorted(items, key=mapping_order)
        
        return items
    
    def _extract_numeric_key(self, name: str) -> tuple:
        """
        Extract numeric components from a filename for numeric sorting.
        
        Args:
            name: Filename or path to extract numbers from
            
        Returns:
            Tuple for sorting (numbers extracted, original name as fallback)
        """
        numbers = re.findall(r'\d+', name)
        if numbers:
            return tuple(int(n) for n in numbers)
        return (0, name.lower())
    
    def _determine_role(self, content: Content, order_index: int) -> str:
        """
        Determine the role label for a content item within the set.
        
        Args:
            content: Content item
            order_index: Position in the ordered set
            
        Returns:
            Role string for this document
        """
        filename = content.id.filename or content.id.path or content.id.canonical_id
        filename_stem = filename.rsplit('.', 1)[0] if '.' in filename else filename
        
        # Try role_field from metadata or data
        if self.role_field:
            role_value = None
            # Check in content.data
            if self.role_field.startswith("data."):
                role_value = self.try_extract_nested_field_from_content(
                    content, self.role_field.replace("data.", "", 1)
                )
            # Check in metadata
            elif content.id.metadata:
                role_value = content.id.metadata.get(self.role_field)
            
            if role_value:
                return str(role_value)
        
        # Try role_mapping (match filename patterns to roles)
        if self.role_mapping:
            for pattern, role in self.role_mapping.items():
                if pattern.lower() in filename.lower():
                    return role
        
        # Default: use filename stem as role
        return filename_stem
