"""Field mapper executor for renaming and remapping fields in Content items."""

import logging
import re
from typing import Dict, Any, Optional, List

from agent_framework import WorkflowContext

from .parallel_executor import ParallelExecutor
from ..models import Content

logger = logging.getLogger("contentflow.executors.field_mapper_executor")


class FieldMapperExecutor(ParallelExecutor):
    """
    Rename, move, and remap fields within Content items for standardization and compatibility.
    
    This executor transforms the structure of Content item data by mapping fields from
    source paths to target paths. It supports field renaming, moving nested fields,
    copying vs. moving fields, creating nested structures, and template-based dynamic
    field naming.
    
    Configuration (settings dict):
        - mappings (str): A Json dictionary of source → target field mappings
          Source and target can use dot notation for nested fields
          Example: {"old_name": "new_name", "user.full_name": "author.name"}
        
        - object_mappings (str): A JSON dictionary for multi-source mappings that combine
          multiple fields into structured objects. Maps target field to an object with
          key-value pairs where keys are field names and values are source paths.
          Example: {"pages_with_content": {"page_num": "pages.page_number", "text": "pages.lines"}}
          This creates: [{"page_num": 1, "text": [...]}, {"page_num": 2, "text": [...]}]
          Default: None (disabled)
          
        - source_id_mappings (str): A JSON dictionary to map content.id fields to data fields.
          Supports field extraction, whole ID copying, and f-string templates.
          Example formats:
            - {"doc_id": "id.unique_id"} - Extract unique_id field from content.id
            - {"url": "id.canonical_id"} - Extract canonical_id field
            - {"path": "{id.container}/{id.path}"} - F-string template (when template_fields=True)
            - {"id": "content.id"} - Copy entire content.id object
          Supports dot notation for nested field access within content.id
          Default: None (disabled)
        
        - copy_mode (str): How to handle source fields after mapping
          Default: "move"
          Options:
            - "move": Delete source field after copying to target
            - "copy": Keep source field, create copy at target
        
        - create_nested (bool): Automatically create nested dictionary structures
          when target path includes dots
          Default: True
        
        - overwrite_existing (bool): Overwrite target field if it already exists
          Default: True
        
        - template_fields (bool): Enable template-based dynamic field naming and f-string evaluation
          Source and target paths support Python f-string style formatting with {variable} placeholders.
          Variables are resolved from content.data at runtime.
          Examples:
            - Source: "data.{source_type}_content" evaluates based on content.data['source_type']
            - Target: "extracted_{format}" evaluates based on content.data['format']
            - Can reference nested fields: "result.{doc.type}_output"
          Default: False
        
        - nested_delimiter (str): Delimiter for nested field paths
          Default: "."
        
        - case_transform (str): Transform field name case during mapping
          Default: None
          Options: None, "lower", "upper", "title", "camel", "snake"
        
        - fail_on_missing_source (bool): Raise error if source field doesn't exist
          Default: False (skip missing sources)
        
        - remove_empty_objects (bool): Remove empty nested objects after moving fields
          Default: False
        
        - list_handling (str): How to handle values when traversing lists in source path
          Default: "first"
          Options:
            - "first": Take only the first item from each list encountered
            - "merge": Flatten and merge all values from nested lists into a single list
            - "all": Keep all values as nested lists (no flattening)
        
        - join_separator (str): Separator to use when joining list values into a string
          (list_handling="concatenate")
          Default: "\n"
          
        - merge_deduplicate (bool): Remove duplicates when merging lists (list_handling="merge")
          Default: False
        
        - merge_filter_empty (bool): Filter out None/empty values when merging lists
          Default: True
          
        Also setting from ParallelExecutor and BaseExecutor apply.
    
    Example:
        ```python
        # Basic field renaming
        executor = FieldMapperExecutor(
            id="field_mapper",
            settings={
                "mappings": {
                    "old_field_name": "new_field_name",
                    "document_text": "content",
                    "metadata.author": "creator"
                },
                "copy_mode": "move"
            }
        )
        
        # Merge nested lists into flat list
        executor = FieldMapperExecutor(
            id="merge_lines",
            settings={
                "mappings": {
                    "result.contents.pages.lines.content": "all_lines"
                },
                "list_handling": "merge",
                "merge_filter_empty": True
            }
        )
        
        # Combine multiple fields into structured objects
        executor = FieldMapperExecutor(
            id="pages_mapper",
            settings={
                "object_mappings": {
                    "pages_with_content": {
                        "page_number": "pages.page_number",
                        "lines": "pages.lines"
                    }
                },
                "list_handling": "merge"
            }
        )
        
        # Restructure nested fields
        executor = FieldMapperExecutor(
            id="restructure",
            settings={
                "mappings": {
                    "user.first_name": "author.name.first",
                    "user.last_name": "author.name.last",
                    "user.email": "author.contact.email"
                },
                "create_nested": True
            }
        )
        
        # Template-based field naming with f-string evaluation
        executor = FieldMapperExecutor(
            id="dynamic_mapper",
            settings={
                "mappings": {
                    "data.{source_type}_content": "extracted_data",
                    "metadata": "{source_type}_metadata"
                },
                "template_fields": True
            }
        )
        # If content.data has source_type="pdf":
        # - "data.{source_type}_content" -> "data.pdf_content"
        # - "{source_type}_metadata" -> "pdf_metadata"
        
        # Map content.id fields to data fields
        executor = FieldMapperExecutor(
            id="add_id_fields",
            settings={
                "source_id_mappings": {
                    "doc_id": "id.unique_id",
                    "url": "id.canonical_id",
                    "reference": "id"
                }
            }
        )
        
        # Map with f-string templates (requires template_fields=True)
        executor = FieldMapperExecutor(
            id="id_templates",
            settings={
                "source_id_mappings": {
                    "path": "{id.container}/{id.path}",
                    "full_reference": "{id.unique_id}_v{id.version}"
                },
                "template_fields": True
            }
        )
        
        # Combine content.id mapping with regular field mappings
        executor = FieldMapperExecutor(
            id="combined_mapper",
            settings={
                "mappings": {
                    "title": "document_title"
                },
                "source_id_mappings": {
                    "doc_id": "content.id"
                }
            }
        )
        ```
    
    Input:
        Content items with arbitrary data fields
        
    Output:
        Content items with remapped fields according to configuration
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
        
        # Field mapping configuration
        import json
        
        self.mappings = self.get_setting("mappings", default="")
        if self.mappings and not isinstance(self.mappings, str):
            raise ValueError(f"{self.id}: 'mappings' must be a JSON string of source -> target field paths")
        try:
            self.mappings = json.loads(self.mappings) if self.mappings else {}
        except json.JSONDecodeError as e:
            raise ValueError(f"{self.id}: Invalid JSON for 'mappings': {e}")
        
        # Source ID mappings for mapping content.id to data fields
        self.source_id_mappings = self.get_setting("source_id_mappings", default="")
        if self.source_id_mappings and not isinstance(self.source_id_mappings, str):
            raise ValueError(f"{self.id}: 'source_id_mappings' must be a JSON string")
        try:
            self.source_id_mappings = json.loads(self.source_id_mappings) if self.source_id_mappings else {}
        except json.JSONDecodeError as e:
            raise ValueError(f"{self.id}: Invalid JSON for 'source_id_mappings': {e}")
        
        # Object mappings for multi-source combinations
        self.object_mappings = self.get_setting("object_mappings", default="")
        if self.object_mappings and not isinstance(self.object_mappings, str):
            raise ValueError(f"{self.id}: 'object_mappings' must be a JSON string")
        try:
            self.object_mappings = json.loads(self.object_mappings) if self.object_mappings else {}
        except json.JSONDecodeError as e:
            raise ValueError(f"{self.id}: Invalid JSON for 'object_mappings': {e}")
        
        # Validate that at least one mapping type is provided
        if not self.mappings and not self.object_mappings and not self.source_id_mappings:
            raise ValueError(f"{self.id}: At least one of 'mappings', 'object_mappings', or 'source_id_mappings' must be provided")
        
        self.case_transform = self.get_setting("case_transform", default=None)
        self.fail_on_missing_source = self.get_setting("fail_on_missing_source", default=False)
        self.remove_empty_objects = self.get_setting("remove_empty_objects", default=False)
        
        # List handling configuration
        self.list_handling = self.get_setting("list_handling", default="merge")
        if self.list_handling not in ["first", "merge", "concatenate", "all"]:
            raise ValueError(f"{self.id}: 'list_handling' must be 'first', 'merge', 'concatenate', or 'all'")
        
        self.join_separator = self.get_setting("join_separator", default="\n")
        self.merge_deduplicate = self.get_setting("merge_deduplicate", default=False)
        self.merge_filter_empty = self.get_setting("merge_filter_empty", default=True)
        
        if self.case_transform and self.case_transform not in [
            "lower", "upper", "title", "camel", "snake"
        ]:
            raise ValueError(
                f"{self.id}: 'case_transform' must be one of: lower, upper, title, camel, snake"
            )
        
        # Additional configuration
        self.copy_mode = self.get_setting("copy_mode", default="move")
        if self.copy_mode not in ["move", "copy"]:
            raise ValueError(f"{self.id}: 'copy_mode' must be 'move' or 'copy'")
        
        self.create_nested = self.get_setting("create_nested", default=True)
        self.overwrite_existing = self.get_setting("overwrite_existing", default=True)
        self.template_fields = self.get_setting("template_fields", default=True)
        self.nested_delimiter = self.get_setting("nested_delimiter", default=".")
        
        if self.debug_mode:
            logger.debug(
                f"FieldMapperExecutor '{self.id}' initialized with "
                f"{len(self.mappings)} mappings, copy_mode={self.copy_mode}"
            )
        
    async def process_content_item(
        self,
        content: Content
    ) -> Content:
        """
        Process content item and apply field mappings.
        Implements ParallelExecutor abstract method.
        
        Args:
            contents: List of Content items to process
            
        Returns:
            List of Content items with remapped fields
        """
        if not content:
            logger.warning(f"No contents provided to {self.id}")
            return content
        
        logger.debug(
            f"Mapping fields for content item "
            f"with {len(self.mappings)} field mappings"
        )
        
        try:
            # Apply field mappings to this content item
            self._apply_mappings(content)
            
            if self.debug_mode:
                logger.debug(
                    f"Applied {len(self.mappings)} field mappings"
                )
                
        except Exception as e:
            logger.error(f"Failed to map fields for content: {e}")
            
            # Raise error to be handled by ParallelExecutor
            raise
        
        logger.debug(
            f"Successfully mapped fields for content item"
        )
        
        return content
    
    def _apply_mappings(self, content: Content) -> None:
        """
        Apply all field mappings to a single content item.
        
        Args:
            content: Content item to modify
        """
        
        # Step 1: Apply source ID mappings to extract fields from content.id
        # Apply source ID mappings (content.id fields to data fields)
        self._apply_source_id_mappings(content)
        
        # Apply object mappings first (multi-source to single target)
        for target_path, field_mappings in self.object_mappings.items():
            try:
                combined_objects = self._combine_fields_to_objects(content.data, field_mappings)
                if combined_objects is not None:
                    self._set_nested_value(content.data, target_path, combined_objects)
                    
                    if self.debug_mode:
                        logger.debug(f"{self.id}: Created {len(combined_objects)} objects at '{target_path}'")
            except Exception as e:
                logger.error(f"{self.id}: Failed to apply object mapping to '{target_path}': {e}")
                raise
        
        
        # Resolve templates if enabled and apply regular mappings
        mappings = self._resolve_template_mappings(content) if self.template_fields else self.mappings
        
        # Process each mapping
        for source_path, target_path in mappings.items():
            
            logger.debug(f"Mapping '{source_path}' to '{target_path}'")
            
            try:
                # Apply case transformation to target if specified
                if self.case_transform:
                    target_path = self._transform_case(target_path)
                
                # Get value from source path
                value = self._get_nested_value(content.data, source_path)
                                
                if value is None:
                    if self.fail_on_missing_source:
                        raise ValueError(f"Source field '{source_path}' not found")
                    else:
                        if self.debug_mode:
                            logger.debug(f"Source field '{source_path}' not found, skipping")
                        continue
                
                # Set value at target path
                self._set_nested_value(content.data, target_path, value)
                
                # Handle source field based on copy_mode
                if self.copy_mode == "move":
                    self._delete_nested_value(content.data, source_path)
                
                if self.debug_mode:
                    logger.debug(f"Mapped '{source_path}' -> '{target_path}'")
                    
            except Exception as e:
                logger.error(f"Failed to map '{source_path}' -> '{target_path}': {e}")
                raise
        
        # Clean up empty objects if moving fields
        if self.copy_mode == "move" and self.remove_empty_objects:
            self._remove_empty_objects(content.data)
    
    # region Source ID Mappings
    
    def _apply_source_id_mappings(self, content: Content) -> None:
        """
        Apply source ID mappings to extract fields from content.id to data fields.
        
        Supports:
        - Direct field access: "id.field_name" extracts content.id.field_name
        - F-string templates: "{id.field1}/{id.field2}" evaluates with id fields
        - Whole ID: "content.id" or "id" copies the entire ID
        
        Args:
            content: Content item to process
        """
        for target_path, source_spec  in self.source_id_mappings.items():
            try:
                value = None
                
                # Check for f-string template format if enabled
                if self.template_fields and "{" in source_spec:
                    # Create context from content.id for template evaluation
                    id_context = self._flatten_id_for_templates(content.id.to_dict())
                    try:
                        value = source_spec.format(**id_context)
                    except (KeyError, ValueError, AttributeError) as e:
                        logger.warning(
                            f"{self.id}: Failed to resolve source ID template '{source_spec}, using {id_context}': {e}"
                        )
                        value = None
                # Handle dot notation to extract specific fields from content.id
                elif source_spec.startswith("id."):
                    # Extract field from content.id using dot notation
                    field_path = source_spec[3:]  # Remove "id." prefix
                    value = self._get_id_field(content.id, field_path)
                # Handle whole ID reference
                elif source_spec in ["content.id", "id"]:
                    value = content.id
                else:
                    # Literal value
                    value = source_spec
                
                if value is not None:
                    self._set_nested_value(content.data, target_path, value)
                    if self.debug_mode:
                        logger.debug(f"Mapped '{source_spec}' to '{target_path}'")
                else:
                    logger.debug(f"Source ID mapping '{source_spec}' resolved to None")
            except Exception as e:
                logger.error(f"Failed to apply source ID mapping to '{target_path}': {e}", exc_info=True)
                if self.fail_on_missing_source:
                    raise
    
    def _get_id_field(self, id_obj: Any, field_path: str) -> Any:
        """
        Extract a field from content.id using dot notation.
        
        Args:
            id_obj: The content.id object
            field_path: Dot-notation path (e.g., "unique_id", "container.name")
            
        Returns:
            Field value, or None if not found
        """
        if not field_path:
            return id_obj
        
        keys = field_path.split(self.nested_delimiter)
        current = id_obj
        
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            elif hasattr(current, key):
                current = getattr(current, key)
            else:
                return None
        
        return current
    
    def _flatten_id_for_templates(self, id_obj: dict, prefix: str = "id") -> Dict[str, Any]:
        """
        Flatten content.id object for use as f-string template context.
        
        Provides an attribute-accessible object for format() templates like
        "{id.container}/{id.path}" by converting nested dicts into namespaces.
        
        Args:
            id_obj: The content.id object (dict or object)
            prefix: Context key (default: "id")
            
        Returns:
            Dictionary with a single key (default: "id") mapped to an
            attribute-accessible namespace
        """
        from types import SimpleNamespace

        def _to_namespace(value: Any) -> Any:
            if isinstance(value, dict):
                return SimpleNamespace(**{k: _to_namespace(v) for k, v in value.items()})
            if isinstance(value, list):
                return [_to_namespace(v) for v in value]
            return value

        return {prefix: _to_namespace(id_obj)}
    
    # endregion Source ID Mappings
    
    def _resolve_template_mappings(self, content: Content) -> Dict[str, str]:
        """
        Resolve f-string style template placeholders in mapping source and target paths.
        
        Evaluates {variable} placeholders using content.data as the variable context.
        Templates can appear in both source and target paths and support nested field access.
        
        Args:
            content: Content item for template context
            
        Returns:
            Resolved mappings dictionary with template placeholders evaluated
            
        Example:
            If content.data = {"source_type": "pdf", "format": "text"}
            mappings = {"data.{source_type}_content": "output.{format}_file"}
            Result = {"data.pdf_content": "output.text_file"}
        """
        resolved = {}
        
        for source_path, target_path in self.mappings.items():
            # Create a flat dictionary for template evaluation
            # This allows both top-level and nested field access
            template_context = self._flatten_dict_for_templates(content.data)
            
            try:
                # Resolve source path using f-string style formatting
                resolved_source = source_path.format(**template_context)
            except (KeyError, ValueError) as e:
                logger.warning(
                    f"Failed to resolve source path template '{source_path}': {e}"
                )
                resolved_source = source_path
            
            try:
                # Resolve target path using f-string style formatting
                resolved_target = target_path.format(**template_context)
            except (KeyError, ValueError) as e:
                logger.warning(
                    f"Failed to resolve target path template '{target_path}': {e}"
                )
                resolved_target = target_path
            
            if self.debug_mode:
                logger.debug(
                    f"Resolved templates: '{source_path}' -> '{resolved_source}' "
                    f"and '{target_path}' -> '{resolved_target}'"
                )
            
            resolved[resolved_source] = resolved_target
        
        return resolved
    
    def _flatten_dict_for_templates(self, data: Dict[str, Any], prefix: str = "") -> Dict[str, Any]:
        """
        Flatten a nested dictionary for use as f-string template context.
        
        Creates both flat keys and dot-notation keys for accessing nested values.
        
        Args:
            data: Dictionary to flatten
            prefix: Current prefix for recursive calls
            
        Returns:
            Flattened dictionary with both direct and nested-path keys
            
        Example:
            Input: {"user": {"name": "John", "age": 30}, "status": "active"}
            Output: {
                "user.name": "John",
                "user.age": 30,
                "status": "active",
                "user": {"name": "John", "age": 30}
            }
        """
        result = {}
        
        for key, value in data.items():
            full_key = f"{prefix}{key}" if prefix else key
            
            # Always include the value itself
            result[key] = value
            
            # For nested dicts, add both the dict itself and flattened keys
            if isinstance(value, dict):
                # Add the nested dict
                result[full_key] = value
                # Recursively flatten nested dictionaries
                nested_flat = self._flatten_dict_for_templates(value, f"{full_key}.")
                result.update(nested_flat)
            else:
                # For non-dict values, add with full prefix key too
                if prefix:
                    result[full_key] = value
        
        return result
    
    def _combine_fields_to_objects(
        self,
        data: Dict[str, Any],
        field_mappings: Dict[str, str]
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Combine multiple source fields into a list of objects.
        
        This method traverses parallel arrays and combines corresponding values
        into structured objects.
        
        Args:
            data: Source data dictionary
            field_mappings: Dictionary mapping object keys to source paths
                Example: {"page_num": "pages.page_number", "text": "pages.lines"}
        
        Returns:
            List of objects with combined fields, or None if no data found
            
        Example:
            Input data:
                {
                    "data": {
                        "full_content": {
                            "result": {
                                "contents": [
                                    {
                                        "pages": [
                                         {
                                           "pageNumber": 1,
                                            "lines": 
                                            [
                                                {
                                                    "content": "Line 1"
                                                },
                                                {
                                                    "content": "Line 2"
                                                }
                                            ]
                                         },
                                         {
                                            "pageNumber": 2,
                                            "lines": 
                                            [
                                                {
                                                    "content": "Line 1"
                                                },
                                                {
                                                    "content": "Line 2"
                                                },
                                                {
                                                    "content": "Line 3"
                                                }
                                            ]
                                         }
                                    }
                                }
                            }
                        }
                    }
                }               
            
            Field mappings:
                {
                    "pages": {
                        "page_number": "full_content.result.contents.pages.pageNumber",
                        "content": "full_content.result.contents.pages.lines.content"
                    }
                }
            
            Output:
                {
                    "pages": [
                        {"page_number": 1, "content": ["Line 1", "Line 2"]},
                        {"page_number": 2, "content": ["Line 1", "Line 2", "Line 3"]}
                    ]
                }
        """
        # Find the common list ancestor path for all field mappings
        # This determines the array we'll iterate over to create objects
        common_ancestor = self._find_common_list_ancestor(data, list(field_mappings.values()))
        
        if not common_ancestor:
            # No common list ancestor, collect values normally
            field_values = {}
            max_length = 0
            
            for target_key, source_path in field_mappings.items():
                value = self._get_nested_value(data, source_path)
                
                if value is not None:
                    # Ensure value is a list for iteration
                    if not isinstance(value, list):
                        value = [value]
                    
                    field_values[target_key] = value
                    max_length = max(max_length, len(value))
                else:
                    if self.fail_on_missing_source:
                        raise ValueError(f"Source field '{source_path}' not found for object mapping")
                    else:
                        if self.debug_mode:
                            logger.debug(f"Source field '{source_path}' not found, will use None")
                        field_values[target_key] = []
            
            if not field_values or max_length == 0:
                return None
            
            # Combine into objects
            result = []
            for i in range(max_length):
                obj = {}
                for target_key, values in field_values.items():
                    # Get value at index i, or None if list is shorter
                    obj[target_key] = values[i] if i < len(values) else None
                
                # Filter empty objects if configured
                if self.merge_filter_empty:
                    # Only include if object has at least one non-None value
                    if any(v is not None for v in obj.values()):
                        result.append(obj)
                else:
                    result.append(obj)
            
            return result if result else None
        
        # Get the list at the common ancestor
        ancestor_list = self._get_nested_value_no_merge(data, common_ancestor)
        if not isinstance(ancestor_list, list):
            return None
        
        # For each item in the ancestor list, extract the relative paths
        result = []
        for item in ancestor_list:
            obj = {}
            for target_key, source_path in field_mappings.items():
                # Calculate the relative path from the common ancestor
                relative_path = self._get_relative_path(common_ancestor, source_path)
                
                # Extract value from the current item using relative path
                # Use merge mode for nested lists within each item
                value = self._get_nested_value(item, relative_path)
                obj[target_key] = value
            
            # Filter empty objects if configured
            if self.merge_filter_empty:
                # Only include if object has at least one non-None value
                if any(v is not None for v in obj.values()):
                    result.append(obj)
            else:
                result.append(obj)
        
        return result if result else None
    
    def _find_common_list_ancestor(self, data: Dict[str, Any], paths: List[str]) -> Optional[str]:
        """
        Find the deepest common ancestor path that points to a list.
        
        This identifies which array we should iterate over to create objects.
        
        Args:
            data: Source data
            paths: List of source paths
            
        Returns:
            Common ancestor path, or None if no common list ancestor
        """
        if not paths:
            return None
        
        # Split all paths into components
        path_components = [p.split(self.nested_delimiter) for p in paths]
        
        # Find common prefix
        common_prefix = []
        for components in zip(*path_components):
            if len(set(components)) == 1:  # All paths have same component at this level
                common_prefix.append(components[0])
            else:
                break
        
        # Walk from deepest to shallowest, find first list
        for i in range(len(common_prefix), 0, -1):
            candidate_path = self.nested_delimiter.join(common_prefix[:i])
            value = self._get_nested_value_no_merge(data, candidate_path)
            if isinstance(value, list):
                return candidate_path
        
        return None
    
    def _get_relative_path(self, ancestor_path: str, full_path: str) -> str:
        """
        Get the relative path from ancestor to the target.
        
        Args:
            ancestor_path: The common ancestor path
            full_path: The full path to the target field
            
        Returns:
            Relative path from ancestor to target
        """
        if not ancestor_path:
            return full_path
        
        ancestor_parts = ancestor_path.split(self.nested_delimiter)
        full_parts = full_path.split(self.nested_delimiter)
        
        # Remove the ancestor prefix
        relative_parts = full_parts[len(ancestor_parts):]
        
        return self.nested_delimiter.join(relative_parts) if relative_parts else ""
    
    def _get_nested_value_no_merge(self, data: Dict[str, Any], path: str) -> Any:
        """
        Get value from nested dictionary WITHOUT applying list_handling merge.
        Used internally to navigate structure without flattening.
        
        Args:
            data: Dictionary to search
            path: Dot-notation path
            
        Returns:
            Value at path, or None if not found
        """
        if not path:
            return data
            
        keys = path.split(self.nested_delimiter)
        current = data
        
        for key in keys:
            if isinstance(current, list):
                # For lists, take first item to continue navigation
                if len(current) > 0:
                    current = current[0]
                else:
                    return None
                # Continue with this key on the first item
                if isinstance(current, dict) and key in current:
                    current = current[key]
                else:
                    return None
            elif isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return None
        
        return current
    
    def _get_nested_value(self, data: Dict[str, Any], path: str) -> Any:
        """
        Get value from nested dictionary using dot notation path.
        Handles list traversal based on list_handling configuration.
        
        Args:
            data: Dictionary to search
            path: Dot-notation path (e.g., "user.profile.name")
            
        Returns:
            Value at path, or None if not found
        """
        keys = path.split(self.nested_delimiter)
        current = data
        
        for i, key in enumerate(keys):
            if isinstance(current, list):
                # Handle list traversal
                if self.list_handling == "first":
                    # Take first item
                    if len(current) > 0:
                        current = current[0]
                    else:
                        return None
                    
                    # Continue with remaining path on first item
                    if isinstance(current, dict) and key in current:
                        current = current[key]
                    else:
                        return None
                        
                elif self.list_handling == "merge":
                    # Recursively collect values from all list items
                    remaining_path = self.nested_delimiter.join(keys[i:])
                    values = []
                    for item in current:
                        value = self._get_nested_value(item, remaining_path)
                        if value is not None:
                            if isinstance(value, list):
                                values.extend(value)
                            else:
                                values.append(value)
                    
                    # Filter and deduplicate if configured
                    if self.merge_filter_empty:
                        values = [v for v in values if v is not None and v != ""]
                    if self.merge_deduplicate:
                        # Preserve order while removing duplicates
                        seen = set()
                        unique_values = []
                        for v in values:
                            # Use str representation for hashability
                            key_val = str(v) if not isinstance(v, (str, int, float, bool)) else v
                            if key_val not in seen:
                                seen.add(key_val)
                                unique_values.append(v)
                        values = unique_values
                    
                    return values if values else None
                
                elif self.list_handling == "concatenate":
                    # Recursively collect values from all list items
                    remaining_path = self.nested_delimiter.join(keys[i:])
                    values = []
                    for item in current:
                        value = self._get_nested_value(item, remaining_path)
                        if value is not None:
                            if isinstance(value, list):
                                values.extend(value)
                            else:
                                values.append(value)
                    
                    # Filter and deduplicate if configured
                    if self.merge_filter_empty:
                        values = [v for v in values if v is not None and v != ""]
                    if self.merge_deduplicate:
                        # Preserve order while removing duplicates
                        seen = set()
                        unique_values = []
                        for v in values:
                            # Use str representation for hashability
                            key_val = str(v) if not isinstance(v, (str, int, float, bool)) else v
                            if key_val not in seen:
                                seen.add(key_val)
                                unique_values.append(v)
                        values = unique_values
                    
                    # return the first value if only one, else join
                    if values and len(values) == 1:
                        return values[0]
                    
                    return self.join_separator.join(str(v) for v in values) if values else None
                    
                else:  # "all"
                    # Keep nested structure, navigate into each item
                    remaining_path = self.nested_delimiter.join(keys[i:])
                    return [self._get_nested_value(item, remaining_path) for item in current]
            
            elif isinstance(current, dict) and key in current:
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
                if self.create_nested:
                    current[key] = {}
                else:
                    raise ValueError(
                        f"Cannot create nested path '{path}' - "
                        f"parent '{key}' does not exist and create_nested=False"
                    )
            elif not isinstance(current[key], dict):
                raise ValueError(
                    f"Cannot create nested path '{path}' - "
                    f"'{key}' exists but is not a dictionary"
                )
            current = current[key]
        
        # Set the final value
        final_key = keys[-1]
        if final_key in current and not self.overwrite_existing:
            logger.warning(
                f"Target field '{path}' already exists and overwrite_existing=False, skipping"
            )
            return
        
        current[final_key] = value
    
    def _delete_nested_value(self, data: Dict[str, Any], path: str) -> None:
        """
        Delete value from nested dictionary using dot notation path.
        
        Args:
            data: Dictionary to modify
            path: Dot-notation path (e.g., "user.profile.name")
        """
        keys = path.split(self.nested_delimiter)
        current = data
        parents = []
        
        # Navigate to parent
        for key in keys[:-1]:
            if isinstance(current, dict) and key in current:
                parents.append((current, key))
                current = current[key]
            else:
                return  # Path doesn't exist, nothing to delete
        
        # Delete the final key
        final_key = keys[-1]
        if isinstance(current, dict) and final_key in current:
            del current[final_key]
    
    def _remove_empty_objects(self, data: Dict[str, Any]) -> None:
        """
        Recursively remove empty nested dictionaries.
        
        Args:
            data: Dictionary to clean
        """
        keys_to_delete = []
        
        for key, value in data.items():
            if isinstance(value, dict):
                # Recursively clean nested dicts
                self._remove_empty_objects(value)
                
                # Mark for deletion if empty
                if not value:
                    keys_to_delete.append(key)
        
        # Delete empty dictionaries
        for key in keys_to_delete:
            del data[key]
    
    def _transform_case(self, text: str) -> str:
        """
        Transform text case according to configuration.
        
        Args:
            text: Text to transform
            
        Returns:
            Transformed text
        """
        if self.case_transform == "lower":
            return text.lower()
        elif self.case_transform == "upper":
            return text.upper()
        elif self.case_transform == "title":
            return text.title()
        elif self.case_transform == "camel":
            # Convert to camelCase
            parts = text.split("_")
            return parts[0].lower() + "".join(p.title() for p in parts[1:])
        elif self.case_transform == "snake":
            # Convert to snake_case
            text = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', text)
            return re.sub('([a-z0-9])([A-Z])', r'\1_\2', text).lower()
        else:
            return text
