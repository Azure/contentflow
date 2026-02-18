"""Document Set Collector executor for consolidating processed document sets."""

import logging
from collections import defaultdict
from datetime import datetime
from typing import Dict, Any, Optional, List, Union

from agent_framework import WorkflowContext

from .base import BaseExecutor
from ..models import Content, ContentIdentifier, ExecutorLogEntry

logger = logging.getLogger("contentflow.executors.document_set_collector")

_UNGROUPED_SET_PREFIX = "ungrouped_"


class DocumentSetCollectorExecutor(BaseExecutor):
    """
    Collect and consolidate processed documents from one or more document sets.
    
    Takes a Content or List[Content] with document_set metadata (stamped by
    DocumentSetInitializerExecutor), groups them by ``document_set_id``,
    validates completeness per group, orders each group by ``set_order``,
    and produces consolidated Content items for cross-document analysis.
    
    When the input contains items from a **single** document set the executor
    returns a single ``Content`` item.  When items belong to **multiple**
    document sets a ``List[Content]`` is returned – one consolidated
    ``Content`` per set.
    
    Items that carry no ``document_set_id`` are collected into an
    auto-generated "ungrouped" set so that no data is silently dropped.
    
    Configuration (settings dict):
        - require_complete_set (bool): Fail if not all documents are present.
          Default: True
        - fields_to_collect (list[str]): Data fields to collect from each
          Content item into the consolidated set. Empty/None = all data fields.
          Default: None (all fields)
        - summary_fields_to_collect (list[str]): Summary fields to collect.
          Empty/None = all summary_data fields.
          Default: None (all fields)
        - output_key (str): Key in output Content.data for consolidated set.
          Default: "document_set"
        - include_raw_content_list (bool): Also include the original List[Content]
          serialized under a separate key.
          Default: False
        
        Also settings from BaseExecutor apply.
    
    Example:
        ```yaml
        - id: collect_set
          type: document_set_collector
          settings:
            require_complete_set: true
            fields_to_collect:
              - "text"
              - "tables"
              - "financial_metrics"
            output_key: "document_set"
        ```
    
    Input:
        Content or List[Content] with document_set_* metadata in summary_data.
        Items may belong to one or more document sets.
        
    Output:
        - Single Content when all items belong to the same document set.
        - List[Content] when items span multiple document sets (one per set).
        
        Each Content item has data[output_key] containing consolidated set data:
        {
            "set_id": "fy2024-quarterly",
            "set_name": "FY2024 Quarterly Reports",
            "total_documents": 4,
            "documents": [
                {
                    "role": "Q1_2024",
                    "order": 0,
                    "canonical_id": "...",
                    "filename": "Q1_Report.pptx",
                    "data": { ... collected data fields ... },
                    "summary_data": { ... collected summary fields ... }
                },
                ...
            ]
        }
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
        
        self.require_complete_set = self.get_setting("require_complete_set", default=True)
        self.fields_to_collect = self.get_setting("fields_to_collect", default=None)
        self.summary_fields_to_collect = self.get_setting("summary_fields_to_collect", default=None)
        self.output_key = self.get_setting("output_key", default="document_set")
        self.include_raw_content_list = self.get_setting("include_raw_content_list", default=False)
        
        if self.debug_mode:
            logger.debug(
                f"DocumentSetCollectorExecutor {self.id} initialized: "
                f"require_complete={self.require_complete_set}, "
                f"output_key={self.output_key}"
            )
    
    async def process_input(
        self,
        input: Union[Content, List[Content]],
        ctx: WorkflowContext[Union[Content, List[Content]], Union[Content, List[Content]]]
    ) -> Union[Content, List[Content]]:
        """
        Collect and consolidate Content items, grouping by document set.
        
        Items are grouped by their ``document_set_id`` metadata.  Each group
        is independently validated for completeness, ordered by
        ``document_set_order``, and consolidated into a single ``Content``
        item.
        
        Args:
            input: Content or List of Content items with document_set metadata.
                   Items may belong to one or more document sets.
            ctx: Workflow context
            
        Returns:
            A single Content item when all items belong to one document set,
            or a List[Content] when items span multiple document sets (one
            consolidated Content per set).
        """
        start_time = datetime.now()
        
        # Normalize to list
        if isinstance(input, Content):
            content_items = [input]
        else:
            content_items = list(input)
        
        if not content_items:
            raise ValueError(f"{self.id}: Received empty input, cannot collect document set")
        
        # ------------------------------------------------------------------
        # Group items by document_set_id
        # ------------------------------------------------------------------
        groups: Dict[str, List[Content]] = defaultdict(list)
        
        for item in content_items:
            sid = item.summary_data.get("document_set_id")
            if not sid:
                # Assign an auto-generated group id so the item is not lost
                sid = f"{_UNGROUPED_SET_PREFIX}{self.generate_sha1_hash(str(datetime.now()))[:12]}"
                logger.warning(
                    f"{self.id}: Content item "
                    f"'{item.id.canonical_id if item.id else 'unknown'}' "
                    f"has no document_set_id. Assigned to auto-group '{sid}'."
                )
                # Stamp the generated id back so downstream logic is consistent
                item.summary_data["document_set_id"] = sid
            groups[sid].append(item)
        
        if self.debug_mode:
            logger.debug(
                f"{self.id}: Input has {len(content_items)} item(s) across "
                f"{len(groups)} document set(s): {list(groups.keys())}"
            )
        
        # ------------------------------------------------------------------
        # Consolidate each group
        # ------------------------------------------------------------------
        consolidated_outputs: List[Content] = []
        
        for set_id, set_items in groups.items():
            output = self._consolidate_set(set_id, set_items, start_time)
            consolidated_outputs.append(output)
        
        elapsed = (datetime.now() - start_time).total_seconds()
        logger.info(
            f"{self.id}: Consolidated {len(content_items)} item(s) into "
            f"{len(consolidated_outputs)} document set(s) in {elapsed:.2f}s"
        )
        
        # Return a single Content when there is exactly one set
        if len(consolidated_outputs) == 1:
            return consolidated_outputs[0]
        return consolidated_outputs
    
    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------
    
    def _consolidate_set(
        self,
        set_id: str,
        set_items: List[Content],
        start_time: datetime,
    ) -> Content:
        """
        Consolidate a single group of Content items into one Content.
        
        Args:
            set_id: The document set identifier for this group.
            set_items: Content items belonging to this set.
            start_time: Timestamp when overall processing began (for logs).
            
        Returns:
            A single consolidated Content item for the document set.
        """
        # Derive set-level metadata from the first item in the group
        first_item = set_items[0]
        set_name = first_item.summary_data.get("document_set_name", "")
        expected_total = first_item.summary_data.get(
            "document_set_total", len(set_items)
        )
        
        if set_id.startswith(_UNGROUPED_SET_PREFIX):
            set_name = set_name or "auto_collected_set"
        
        # Validate completeness
        if self.require_complete_set and len(set_items) != expected_total:
            raise ValueError(
                f"{self.id}: Incomplete document set '{set_name}' ({set_id}). "
                f"Expected {expected_total} documents but received {len(set_items)}"
            )
        
        # Warn about any items whose id does not match the group key
        mismatched = [
            c for c in set_items
            if c.summary_data.get("document_set_id")
            and c.summary_data.get("document_set_id") != set_id
        ]
        if mismatched:
            logger.warning(
                f"{self.id}: Found {len(mismatched)} item(s) with a "
                f"document_set_id that differs from the group key '{set_id}'."
            )
        
        # Order by set_order
        ordered_items = sorted(
            set_items,
            key=lambda c: c.summary_data.get("document_set_order", 0),
        )
        
        # Build consolidated documents list
        documents = [
            self._build_document_entry(content) for content in ordered_items
        ]
        
        # Build the consolidated set data structure
        consolidated_set = {
            "set_id": set_id,
            "set_name": set_name,
            "total_documents": len(documents),
            "collected_at": datetime.now().isoformat(),
            "documents": documents,
        }
        
        # Create output Content item
        output_content = Content(
            id=ContentIdentifier(
                canonical_id=f"document_set://{set_id}",
                unique_id=self.generate_sha1_hash(
                    f"set_{set_id}_{datetime.now().isoformat()}"
                ),
                source_name="document_set_collector",
                source_type="document_set",
                path=set_id,
                filename=set_name,
            ),
            data={
                self.output_key: consolidated_set,
            },
            summary_data={
                "document_set_id": set_id,
                "document_set_name": set_name,
                "document_set_total": len(documents),
                "collection_status": (
                    "complete" if len(documents) == expected_total else "partial"
                ),
            },
        )
        
        # Optionally include raw content list
        if self.include_raw_content_list:
            output_content.data["raw_content_list"] = [
                c.model_dump() for c in ordered_items
            ]
        
        # Add executor log entry
        output_content.executor_logs.append(
            ExecutorLogEntry(
                executor_id=self.id,
                start_time=start_time,
                end_time=datetime.now(),
                status="completed",
                details={
                    "set_id": set_id,
                    "documents_collected": len(documents),
                    "expected_total": expected_total,
                },
                errors=[],
            )
        )
        
        logger.info(
            f"{self.id}: Collected {len(documents)} document(s) for set "
            f"'{set_name}' ({set_id})"
        )
        
        return output_content
    
    def _build_document_entry(self, content: Content) -> Dict[str, Any]:
        """
        Build a consolidated document entry from a Content item.
        
        Args:
            content: Content item to extract data from
            
        Returns:
            Dict with document entry for the consolidated set
        """
        # Collect data fields
        if self.fields_to_collect:
            collected_data = {}
            for field in self.fields_to_collect:
                if field in content.data:
                    collected_data[field] = content.data[field]
                else:
                    # Try nested extraction
                    value = self.try_extract_nested_field_from_content(content, field)
                    if value is not None:
                        collected_data[field] = value
        else:
            collected_data = dict(content.data)
        
        # Collect summary fields
        if self.summary_fields_to_collect:
            collected_summary = {}
            for field in self.summary_fields_to_collect:
                if field in content.summary_data:
                    collected_summary[field] = content.summary_data[field]
        else:
            # Collect all summary_data except document_set_* keys
            collected_summary = {
                k: v for k, v in content.summary_data.items()
                if not k.startswith("document_set_")
            }
        
        return {
            "role": content.summary_data.get("document_set_role", ""),
            "order": content.summary_data.get("document_set_order", 0),
            "canonical_id": content.id.canonical_id if content.id else "",
            "unique_id": content.id.unique_id if content.id else "",
            "filename": content.id.filename if content.id else "",
            "path": content.id.path if content.id else "",
            "data": collected_data,
            "summary_data": collected_summary,
        }
