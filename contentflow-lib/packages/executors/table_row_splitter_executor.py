"""Table row splitter executor that creates separate content items for each table row."""

import csv
import io
import logging
from typing import Dict, Any, Optional, List, Union

from agent_framework import WorkflowContext

from .base import BaseExecutor
from ..models import Content, ContentIdentifier

logger = logging.getLogger(__name__)


class TableRowSplitterExecutor(BaseExecutor):
    """
    Split tabular data into individual content items, one per row.
    
    This executor processes documents containing tabular data (list of lists,
    list of dicts, CSV string, or extracted tables from documents) and creates
    a separate Content item for each row. This enables parallel processing of
    individual rows through subsequent pipeline stages.
    
    Configuration (settings dict):
        - table_field (str): Field in data containing the table
          Default: "table"
        - table_format (str): Format of table data
          Default: "auto" (auto-detect)
          Options: "auto", "list_of_lists", "list_of_dicts", "csv", "word_tables", "excel_rows"
        - has_header (bool): Whether first row/element contains headers
          Default: True (for list_of_lists and CSV)
        - header_row_index (int): Index of header row (for list_of_lists)
          Default: 0
        - skip_empty_rows (bool): Skip rows with all empty/null values
          Default: True
        - row_id_field (str): Field name to use as unique row identifier (for list_of_dicts)
          Default: None (use row index)
        - row_id_prefix (str): Prefix for generated row IDs
          Default: "row"
        - include_row_index (bool): Include original row index in output
          Default: True
        - include_headers (bool): Include header information in each row content
          Default: True
        - preserve_parent_data (bool): Copy parent document's data fields to each row
          Default: False
        - parent_data_fields (List[str]): Specific parent fields to copy (if preserve_parent_data=True)
          Default: None (copy all)
        - output_format (str): How to structure row data in Content item
          Default: "dict"
          Options: "dict", "list", "both"
        - csv_delimiter (str): Delimiter for CSV parsing
          Default: ","
        - csv_quotechar (str): Quote character for CSV parsing
          Default: '"'
        - max_rows (int): Maximum number of rows to process
          Default: None (all rows)
        - start_row (int): Row index to start from (after header)
          Default: 0
    
    Example:
        ```python
        # Process list of dicts
        executor = TableRowSplitterExecutor(
            id="row_splitter",
            settings={
                "table_field": "customer_data",
                "table_format": "list_of_dicts",
                "row_id_field": "customer_id"
            }
        )
        
        # Process CSV string
        executor = TableRowSplitterExecutor(
            id="csv_splitter",
            settings={
                "table_field": "csv_content",
                "table_format": "csv",
                "has_header": True
            }
        )
        
        # Process Word document tables
        executor = TableRowSplitterExecutor(
            id="word_table_splitter",
            settings={
                "table_field": "word_output.tables",
                "table_format": "word_tables"
            }
        )
        ```
    
    Input:
        Content item with:
        - data[table_field]: Table data in specified format
        
    Output:
        List[Content] - One Content item per table row with:
        - id: New ContentIdentifier with row-specific canonical_id
        - data['row_data']: Row data as dict (if output_format includes "dict")
        - data['row_values']: Row data as list (if output_format includes "list")
        - data['row_index']: Original row index (if include_row_index=True)
        - data['headers']: Column headers (if include_headers=True)
        - data['parent_id']: Original document ID
        - summary_data['row_number']: Row number in original table
        - summary_data['total_rows']: Total rows in original table
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
        
        # Table configuration
        self.table_field = self.get_setting("table_field", default="table")
        self.table_format = self.get_setting("table_format", default="auto")
        self.has_header = self.get_setting("has_header", default=True)
        self.header_row_index = self.get_setting("header_row_index", default=0)
        self.skip_empty_rows = self.get_setting("skip_empty_rows", default=True)
        
        # Row identification
        self.row_id_field = self.get_setting("row_id_field", default=None)
        self.row_id_prefix = self.get_setting("row_id_prefix", default="row")
        
        # Output configuration
        self.include_row_index = self.get_setting("include_row_index", default=True)
        self.include_headers = self.get_setting("include_headers", default=True)
        self.preserve_parent_data = self.get_setting("preserve_parent_data", default=False)
        self.parent_data_fields = self.get_setting("parent_data_fields", default=None)
        self.output_format = self.get_setting("output_format", default="dict")
        
        # CSV configuration
        self.csv_delimiter = self.get_setting("csv_delimiter", default=",")
        self.csv_quotechar = self.get_setting("csv_quotechar", default='"')
        
        # Row filtering
        self.max_rows = self.get_setting("max_rows", default=None)
        self.start_row = self.get_setting("start_row", default=0)
        
        # Validate settings
        if self.table_format not in ["auto", "list_of_lists", "list_of_dicts", "csv", "word_tables", "excel_rows"]:
            raise ValueError(
                f"Invalid table_format: {self.table_format}. "
                f"Must be one of: auto, list_of_lists, list_of_dicts, csv, word_tables, excel_rows"
            )
        
        if self.output_format not in ["dict", "list", "both"]:
            raise ValueError(
                f"Invalid output_format: {self.output_format}. Must be one of: dict, list, both"
            )
        
        if self.debug_mode:
            logger.debug(
                f"TableRowSplitterExecutor with id {self.id} initialized: "
                f"table_field={self.table_field}, format={self.table_format}, "
                f"has_header={self.has_header}"
            )
    
    async def process_input(
        self,
        input: Union[Content, List[Content]],
        ctx: WorkflowContext[Union[Content, List[Content]], Union[Content, List[Content]]]
    ) -> Union[Content, List[Content]]:
        """
        Process content item(s) and split tables into individual row content items.
        
        Args:
            input: Content item or list of content items containing tables
            ctx: Workflow context
            
        Returns:
            List[Content] - Flattened list of row content items from all input tables
        """
        # Handle both single content and list of content items
        if isinstance(input, list):
            all_row_contents = []
            for content in input:
                row_contents = await self._process_single_content(content)
                all_row_contents.extend(row_contents)
            return all_row_contents
        else:
            return await self._process_single_content(input)
    
    async def _process_single_content(self, content: Content) -> List[Content]:
        """
        Process a single content item and split its table into row content items.
        
        Args:
            content: Content item containing table data
            
        Returns:
            List[Content] - One content item per table row
        """
        try:
            if not content or not content.data:
                raise ValueError("Content must have data")
            
            # Extract table data from nested field path
            table_data = self.try_extract_nested_field_from_content(content, self.table_field)
            
            if table_data is None:
                logger.warning(
                    f"Table field '{self.table_field}' not found in content {content.id.canonical_id}"
                )
                return []
            
            if self.debug_mode:
                logger.debug(
                    f"Processing table from content {content.id.canonical_id}, "
                    f"format: {self.table_format}"
                )
            
            # Parse table based on format
            headers, rows = self._parse_table(table_data)
            
            if self.debug_mode:
                logger.debug(f"Parsed {len(rows)} rows with headers: {headers}")
            
            # Apply row filtering
            if self.start_row > 0:
                rows = rows[self.start_row:]
            
            if self.max_rows is not None:
                rows = rows[:self.max_rows]
            
            # Create content items for each row
            row_contents = []
            total_rows = len(rows)
            
            for row_idx, row_data in enumerate(rows):
                # Skip empty rows if configured
                if self.skip_empty_rows and self._is_empty_row(row_data):
                    continue
                
                # Generate unique row ID
                row_id = self._generate_row_id(content, row_data, row_idx)
                
                # Create new content item for this row
                row_content = self._create_row_content(
                    parent_content=content,
                    row_data=row_data,
                    row_index=row_idx,
                    row_id=row_id,
                    headers=headers,
                    total_rows=total_rows
                )
                
                row_contents.append(row_content)
            
            if self.debug_mode:
                logger.debug(
                    f"Created {len(row_contents)} row content items from "
                    f"content {content.id.canonical_id}"
                )
            
            return row_contents
            
        except Exception as e:
            logger.error(
                f"TableRowSplitterExecutor {self.id} failed processing content "
                f"{content.id.canonical_id}: {str(e)}",
                exc_info=True
            )
            
            if self.fail_on_error:
                raise
            
            return []
    
    def _parse_table(self, table_data: Any) -> tuple[Optional[List[str]], List[Any]]:
        """
        Parse table data into headers and rows based on format.
        
        Args:
            table_data: Raw table data
            
        Returns:
            Tuple of (headers, rows) where headers is optional list of column names
        """
        # Auto-detect format if needed
        if self.table_format == "auto":
            detected_format = self._detect_table_format(table_data)
            if self.debug_mode:
                logger.debug(f"Auto-detected table format: {detected_format}")
        else:
            detected_format = self.table_format
        
        # Parse based on format
        if detected_format == "list_of_dicts":
            return self._parse_list_of_dicts(table_data)
        elif detected_format == "list_of_lists":
            return self._parse_list_of_lists(table_data)
        elif detected_format == "csv":
            return self._parse_csv(table_data)
        elif detected_format == "word_tables":
            return self._parse_word_tables(table_data)
        elif detected_format == "excel_rows":
            return self._parse_excel_rows(table_data)
        else:
            raise ValueError(f"Unsupported table format: {detected_format}")
    
    def _detect_table_format(self, table_data: Any) -> str:
        """Auto-detect table format from data structure."""
        if isinstance(table_data, str):
            return "csv"
        elif isinstance(table_data, list) and len(table_data) > 0:
            if isinstance(table_data[0], dict):
                # Check if it's a Word table structure
                if "table_number" in table_data[0] and "data" in table_data[0]:
                    return "word_tables"
                return "list_of_dicts"
            elif isinstance(table_data[0], (list, tuple)):
                return "list_of_lists"
        
        return "list_of_lists"  # Default fallback
    
    def _parse_list_of_dicts(self, table_data: List[Dict]) -> tuple[List[str], List[Dict]]:
        """Parse list of dictionaries format."""
        if not table_data:
            return None, []
        
        # Extract headers from first dict
        headers = list(table_data[0].keys())
        return headers, table_data
    
    def _parse_list_of_lists(self, table_data: List[List]) -> tuple[Optional[List[str]], List[List]]:
        """Parse list of lists format."""
        if not table_data:
            return None, []
        
        headers = None
        rows = table_data
        
        if self.has_header and len(table_data) > self.header_row_index:
            headers = table_data[self.header_row_index]
            # Remove header row from data
            rows = table_data[:self.header_row_index] + table_data[self.header_row_index + 1:]
        
        return headers, rows
    
    def _parse_csv(self, table_data: str) -> tuple[Optional[List[str]], List[List[str]]]:
        """Parse CSV string format."""
        csv_reader = csv.reader(
            io.StringIO(table_data),
            delimiter=self.csv_delimiter,
            quotechar=self.csv_quotechar
        )
        
        rows = list(csv_reader)
        
        if not rows:
            return None, []
        
        headers = None
        if self.has_header and len(rows) > 0:
            headers = rows[0]
            rows = rows[1:]
        
        return headers, rows
    
    def _parse_word_tables(self, table_data: List[Dict]) -> tuple[Optional[List[str]], List[List]]:
        """Parse Word document table format (from WordExtractorExecutor)."""
        if not table_data:
            return None, []
        
        # Word tables come as list of table objects with 'data' field
        all_rows = []
        headers = None
        
        for table in table_data:
            if "data" in table and table["data"]:
                table_rows = table["data"]
                
                # Use first row as header if configured
                if self.has_header and not headers and len(table_rows) > 0:
                    headers = table_rows[0]
                    all_rows.extend(table_rows[1:])
                else:
                    all_rows.extend(table_rows)
        
        return headers, all_rows
    
    def _parse_excel_rows(self, table_data: List[Dict]) -> tuple[Optional[List[str]], List[Dict]]:
        """Parse Excel row format (list of row dictionaries)."""
        # Similar to list_of_dicts but may have additional Excel-specific structure
        return self._parse_list_of_dicts(table_data)
    
    def _is_empty_row(self, row_data: Any) -> bool:
        """Check if a row is empty (all values are None, empty string, or whitespace)."""
        if isinstance(row_data, dict):
            return all(
                v is None or (isinstance(v, str) and not v.strip())
                for v in row_data.values()
            )
        elif isinstance(row_data, (list, tuple)):
            return all(
                v is None or (isinstance(v, str) and not v.strip())
                for v in row_data
            )
        return False
    
    def _generate_row_id(self, parent_content: Content, row_data: Any, row_idx: int) -> str:
        """Generate unique ID for a row."""
        # Try to use specified field as ID
        if self.row_id_field and isinstance(row_data, dict):
            field_value = row_data.get(self.row_id_field)
            if field_value is not None:
                return f"{parent_content.id.canonical_id}_{self.row_id_prefix}_{field_value}"
        
        # Fallback to index-based ID
        return f"{parent_content.id.canonical_id}_{self.row_id_prefix}_{row_idx}"
    
    def _create_row_content(
        self,
        parent_content: Content,
        row_data: Any,
        row_index: int,
        row_id: str,
        headers: Optional[List[str]],
        total_rows: int
    ) -> Content:
        """Create a new Content item for a single row."""
        # Create new content identifier
        row_content_id = ContentIdentifier(
            canonical_id=row_id,
            source_name=parent_content.id.source_name,
            source_type=parent_content.id.source_type,
            container=parent_content.id.container,
            path=parent_content.id.path,
            metadata={
                "parent_id": parent_content.id.canonical_id,
                "row_index": row_index,
                "is_table_row": True
            }
        )
        
        # Prepare row data in requested format(s)
        row_content_data = {}
        
        # Convert row to dict if needed
        if isinstance(row_data, dict):
            row_dict = row_data
            row_list = list(row_data.values()) if headers else None
        else:
            # row_data is a list/tuple
            row_list = list(row_data)
            if headers and len(headers) == len(row_list):
                row_dict = dict(zip(headers, row_list))
            else:
                row_dict = {f"column_{i}": val for i, val in enumerate(row_list)}
        
        # Add data based on output format
        if self.output_format in ["dict", "both"]:
            row_content_data["row_data"] = row_dict
        
        if self.output_format in ["list", "both"]:
            row_content_data["row_values"] = row_list
        
        # Add optional fields
        if self.include_row_index:
            row_content_data["row_index"] = row_index
        
        if self.include_headers and headers:
            row_content_data["headers"] = headers
        
        row_content_data["parent_id"] = parent_content.id.canonical_id
        
        # Preserve parent data if configured
        if self.preserve_parent_data:
            if self.parent_data_fields:
                # Copy only specified fields
                for field in self.parent_data_fields:
                    if field in parent_content.data and field not in row_content_data:
                        row_content_data[field] = parent_content.data[field]
            else:
                # Copy all parent data (excluding table field)
                for key, value in parent_content.data.items():
                    if key != self.table_field and key not in row_content_data:
                        row_content_data[key] = value
        
        # Create summary data
        summary_data = {
            "row_number": row_index + 1,
            "total_rows": total_rows,
            "parent_document": parent_content.id.canonical_id
        }
        
        # Create and return new content item
        return Content(
            id=row_content_id,
            data=row_content_data,
            summary_data=summary_data,
            executor_logs=[]
        )
