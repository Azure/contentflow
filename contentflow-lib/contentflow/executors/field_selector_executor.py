"""Field selector executor for selecting or excluding specific fields from Content items."""

import logging
import fnmatch
from typing import Dict, Any, Optional, List, Set

from agent_framework import WorkflowContext

from .parallel_executor import ParallelExecutor
from ..models import Content

logger = logging.getLogger("contentflow.executors.field_selector_executor")


class FieldSelectorExecutor(ParallelExecutor):
    """
    Select, keep, or remove specific fields from Content items for data privacy, 
    size optimization, or pipeline simplification.
    
    This executor filters Content item data by selecting only specified fields or 
    excluding specified fields. It supports wildcard patterns, nested field selection,
    conditional field selection based on values, and preserves or flattens nested structures.
    
    Configuration (settings dict):
        - mode (str): Selection mode
          Default: "include"
          Options:
            - "include": Keep only the specified fields
            - "exclude": Remove the specified fields
        
        - fields (str): A Json list of field names or patterns to select/exclude
          Supports wildcard patterns (e.g., temp_*, internal_*)
          Supports nested paths with dot notation (e.g., metadata.author.name)
          Example: ["field1", "field2", "temp_*", "metadata.author"]
        
        - nested_delimiter (str): Delimiter for nested field paths
          Default: "."
        
        - preserve_structure (bool): Preserve nested dictionary structures
          Default: True
          Options:
            - True: Keep nested structures intact
            - False: Flatten selected fields to top level
        
        - conditional_selection (bool): Enable conditional field selection
          Default: False
          When enabled, fields can be selected/excluded based on their values
        
        - condition_field (str): Field to evaluate for conditional selection
          Only used when conditional_selection is True
        
        - condition_operator (str): Comparison operator for conditional selection
          Default: "equals"
          Options: "equals", "not_equals", "contains", "not_contains", "exists", "not_exists"
        
        - condition_value (str): Value to compare against for conditional selection
        
        - keep_id_fields (bool): Always preserve Content ID and core fields
          Default: True
          When True, always keeps essential fields regardless of selection
        
        - bulk_operations (bool): Enable bulk field operations
          Default: False
          When True, optimizes processing for large field sets
        
        - fail_on_missing_field (bool): Raise error if specified field doesn't exist
          Default: False (skip missing fields)
        
        - add_selection_metadata (bool): Add metadata about field selection
          Default: False
          When True, adds selection info to content.summary_data
          
        Also setting from ParallelExecutor and BaseExecutor apply.
    
    Example:
        ```python
        # Basic field inclusion - keep only specific fields
        executor = FieldSelectorExecutor(
            id="field_selector",
            settings={
                "mode": "include",
                "fields": ["content", "title", "metadata.author"]
            }
        )
        
        # Field exclusion with wildcards - remove temporary fields
        executor = FieldSelectorExecutor(
            id="remove_temp",
            settings={
                "mode": "exclude",
                "fields": ["temp_*", "internal_*", "processing_stats"],
                "preserve_structure": True
            }
        )
        
        # Conditional field selection
        executor = FieldSelectorExecutor(
            id="conditional_select",
            settings={
                "mode": "include",
                "fields": ["*"],
                "conditional_selection": True,
                "condition_field": "status",
                "condition_operator": "equals",
                "condition_value": "approved"
            }
        )
        
        # Privacy-focused exclusion
        executor = FieldSelectorExecutor(
            id="privacy_filter",
            settings={
                "mode": "exclude",
                "fields": ["ssn", "credit_card", "password", "personal.*"],
                "keep_id_fields": True
            }
        )
        ```
    
    Input:
        Content items with arbitrary data fields
        
    Output:
        Content items with selected/excluded fields according to configuration
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
        
        # Field selection configuration
        self.mode = self.get_setting("mode", default="include")
        if self.mode not in ["include", "exclude"]:
            raise ValueError("'mode' must be 'include' or 'exclude'")
        
        self.fields = self.get_setting("fields", default="", required=True)
        if not isinstance(self.fields, str):
            raise ValueError("'fields' must be a JSON string list of field names or patterns")
        try:
            import json
            self.fields = json.loads(self.fields)
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse 'fields' JSON string: {e}")
        
        if not isinstance(self.fields, list):
            raise ValueError("'fields' must be a list of field names or patterns")
        
        self.nested_delimiter = self.get_setting("nested_delimiter", default=".")
        self.preserve_structure = self.get_setting("preserve_structure", default=True)
        self.conditional_selection = self.get_setting("conditional_selection", default=False)
        self.condition_field = self.get_setting("condition_field", default=None)
        self.condition_operator = self.get_setting("condition_operator", default="equals")
        self.condition_value = self.get_setting("condition_value", default=None)
        self.keep_id_fields = self.get_setting("keep_id_fields", default=True)
        self.bulk_operations = self.get_setting("bulk_operations", default=False)
        self.fail_on_missing_field = self.get_setting("fail_on_missing_field", default=False)
        self.add_selection_metadata = self.get_setting("add_selection_metadata", default=False)
        
        # Validate conditional selection settings
        if self.conditional_selection:
            if not self.condition_field:
                raise ValueError("'condition_field' is required when conditional_selection is True")
            if self.condition_operator not in [
                "equals", "not_equals", "contains", "not_contains", "exists", "not_exists"
            ]:
                raise ValueError(
                    "'condition_operator' must be one of: equals, not_equals, contains, "
                    "not_contains, exists, not_exists"
                )
        
        # Core fields that should always be preserved
        self.core_fields = {"id", "canonical_id", "source_id"} if self.keep_id_fields else set()
        
        if self.debug_mode:
            logger.debug(
                f"FieldSelectorExecutor '{self.id}' initialized with "
                f"mode={self.mode}, {len(self.fields)} field patterns"
            )
    
    async def process_content_item(
        self,
        content: Content
    ) -> Content:
        """
        Process content item and apply field selection/exclusion.
        Implements ParallelExecutor abstract method.
        
        Args:
            content: Content item to process
            ctx: Workflow execution context
            
        Returns:
            Content item with selected/excluded fields
        """
        if not content:
            logger.warning(f"No content provided to {self.id}")
            return content
        
        # Check conditional selection
        if self.conditional_selection and not self._evaluate_condition(content):
            if self.debug_mode:
                logger.debug(f"Content item does not meet condition, skipping field selection")
            return content
        
        logger.info(
            f"Applying field selection for content item "
            f"with mode={self.mode}, {len(self.fields)} patterns"
        )
        
        try:
            # Get all field paths in the content
            all_fields = self._get_all_field_paths(content.data)
            
            if self.debug_mode:
                logger.debug(f"Found {len(all_fields)} total fields in content")
            
            # Determine which fields to keep
            if self.mode == "include":
                fields_to_keep = self._select_matching_fields(all_fields)
            else:  # exclude mode
                matching_fields = self._select_matching_fields(all_fields)
                fields_to_keep = all_fields - matching_fields
            
            # Always keep core fields
            fields_to_keep.update(self.core_fields)
            
            if self.debug_mode:
                logger.debug(f"Keeping {len(fields_to_keep)} fields after selection")
            
            # Create new data with selected fields
            if self.preserve_structure:
                new_data = self._build_structured_data(content.data, fields_to_keep)
            else:
                new_data = self._build_flat_data(content.data, fields_to_keep)
            
            # Update content data
            content.data = new_data
            
            # Add metadata if requested
            if self.add_selection_metadata:
                if not hasattr(content, 'summary_data'):
                    content.summary_data = {}
                content.summary_data['field_selection'] = {
                    'mode': self.mode,
                    'fields_selected': len(fields_to_keep),
                    'fields_removed': len(all_fields) - len(fields_to_keep),
                    'patterns': self.fields
                }
            
            logger.info(
                f"Successfully applied field selection: "
                f"{len(fields_to_keep)} fields kept, "
                f"{len(all_fields) - len(fields_to_keep)} fields removed"
            )
            
        except Exception as e:
            logger.error(f"Failed to apply field selection: {e}")
            raise
        
        return content
    
    def _evaluate_condition(self, content: Content) -> bool:
        """
        Evaluate conditional selection criteria.
        
        Args:
            content: Content item to evaluate
            
        Returns:
            True if condition is met, False otherwise
        """
        if not self.conditional_selection:
            return True
        
        # Get field value
        value = self._get_nested_value(content.data, self.condition_field)
        
        # Evaluate based on operator
        if self.condition_operator == "exists":
            return value is not None
        elif self.condition_operator == "not_exists":
            return value is None
        elif value is None:
            return False
        elif self.condition_operator == "equals":
            return str(value) == str(self.condition_value)
        elif self.condition_operator == "not_equals":
            return str(value) != str(self.condition_value)
        elif self.condition_operator == "contains":
            return str(self.condition_value) in str(value)
        elif self.condition_operator == "not_contains":
            return str(self.condition_value) not in str(value)
        
        return False
    
    def _get_all_field_paths(
        self,
        data: Dict[str, Any],
        prefix: str = ""
    ) -> Set[str]:
        """
        Get all field paths in a nested dictionary.
        
        Args:
            data: Dictionary to traverse
            prefix: Current path prefix
            
        Returns:
            Set of all field paths
        """
        paths = set()
        
        if not isinstance(data, dict):
            return paths
        
        for key, value in data.items():
            if prefix:
                path = f"{prefix}{self.nested_delimiter}{key}"
            else:
                path = key
            
            paths.add(path)
            
            # Recursively get nested paths
            if isinstance(value, dict):
                nested_paths = self._get_all_field_paths(value, path)
                paths.update(nested_paths)
        
        return paths
    
    def _select_matching_fields(self, all_fields: Set[str]) -> Set[str]:
        """
        Select fields that match the configured patterns.
        
        Args:
            all_fields: Set of all available field paths
            
        Returns:
            Set of matching field paths
        """
        matching = set()
        
        for pattern in self.fields:
            # Check for wildcard pattern
            if '*' in pattern or '?' in pattern:
                # Use fnmatch for wildcard matching
                for field in all_fields:
                    if fnmatch.fnmatch(field, pattern):
                        matching.add(field)
                        if self.debug_mode:
                            logger.debug(f"Pattern '{pattern}' matched field '{field}'")
            else:
                # Exact match or nested path
                if pattern in all_fields:
                    matching.add(pattern)
                    if self.debug_mode:
                        logger.debug(f"Exact match for field '{pattern}'")
                else:
                    # Check if it's a parent path (include all nested fields)
                    for field in all_fields:
                        if field.startswith(pattern + self.nested_delimiter):
                            matching.add(field)
                            if self.debug_mode:
                                logger.debug(f"Parent path '{pattern}' matched field '{field}'")
                    
                    if pattern not in all_fields and self.fail_on_missing_field:
                        raise ValueError(f"Field '{pattern}' not found in content")
        
        return matching
    
    def _build_structured_data(
        self,
        original_data: Dict[str, Any],
        fields_to_keep: Set[str]
    ) -> Dict[str, Any]:
        """
        Build new data dictionary preserving nested structure.
        
        Args:
            original_data: Original data dictionary
            fields_to_keep: Set of field paths to keep
            
        Returns:
            New data dictionary with selected fields
        """
        new_data = {}
        
        for field_path in fields_to_keep:
            value = self._get_nested_value(original_data, field_path)
            if value is not None:
                self._set_nested_value(new_data, field_path, value)
        
        return new_data
    
    def _build_flat_data(
        self,
        original_data: Dict[str, Any],
        fields_to_keep: Set[str]
    ) -> Dict[str, Any]:
        """
        Build new data dictionary with flattened structure.
        
        Args:
            original_data: Original data dictionary
            fields_to_keep: Set of field paths to keep
            
        Returns:
            Flattened data dictionary with selected fields
        """
        new_data = {}
        
        for field_path in fields_to_keep:
            value = self._get_nested_value(original_data, field_path)
            if value is not None:
                # Use the full path as the key (flattened)
                new_data[field_path] = value
        
        return new_data
    
    def _get_nested_value(self, data: Dict[str, Any], path: str) -> Any:
        """
        Get value from nested dictionary using dot notation path.
        
        Args:
            data: Dictionary to search
            path: Dot-notation path (e.g., "user.profile.name")
            
        Returns:
            Value at path, or None if not found
        """
        keys = path.split(self.nested_delimiter)
        current = data
        
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return None
        
        return current
    
    def _set_nested_value(
        self,
        data: Dict[str, Any],
        path: str,
        value: Any
    ) -> None:
        """
        Set value in nested dictionary using dot notation path.
        Creates nested structure as needed.
        
        Args:
            data: Dictionary to modify
            path: Dot-notation path (e.g., "user.profile.name")
            value: Value to set
        """
        keys = path.split(self.nested_delimiter)
        current = data
        
        # Navigate to parent, creating nested dicts as needed
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            elif not isinstance(current[key], dict):
                # If the intermediate value is not a dict, we can't create nested structure
                logger.warning(
                    f"Cannot create nested path '{path}' - "
                    f"'{key}' exists but is not a dictionary"
                )
                return
            current = current[key]
        
        # Set the final value
        final_key = keys[-1]
        current[final_key] = value
