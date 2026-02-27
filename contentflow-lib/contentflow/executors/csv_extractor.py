"""CSV extraction executor using Python's built-in csv module."""

import csv
import io
import logging
from typing import Dict, Any, Optional, List

from . import ParallelExecutor
from ..models import Content

logger = logging.getLogger("contentflow.executors.csv_extractor")


class CSVExtractorExecutor(ParallelExecutor):
    """
    Extract structured content from CSV files.

    This executor parses CSV (and TSV/delimited) files to extract rows as
    structured records, with optional header handling, row limiting, type
    inference, and summary statistics.

    Configuration (settings dict):
        - content_field (str): Field containing CSV bytes/string content.
          Default: "content"
        - temp_file_path_field (str): Field containing a temp file path to a CSV file.
          Default: "temp_file_path"
        - output_field (str): Field name for extracted data.
          Default: "csv_output"
        - delimiter (str): Column delimiter character.
          Default: "," (comma)
        - quotechar (str): Character used to quote fields.
          Default: '"'
        - has_header (bool): Whether the first row is a header row.
          Default: True
        - encoding (str): File encoding when reading bytes.
          Default: "utf-8"
        - max_rows (int): Maximum number of data rows to extract (0 = unlimited).
          Default: 0
        - skip_empty_rows (bool): Skip rows where all fields are empty.
          Default: True
        - strip_whitespace (bool): Strip leading/trailing whitespace from cell values.
          Default: True
        - infer_types (bool): Attempt to infer numeric types for cell values.
          Default: False
        - extract_text (bool): Produce a plain-text representation of the CSV.
          Default: False

        Also settings from ParallelExecutor and BaseExecutor apply.

    Example:
        ```python
        executor = CSVExtractorExecutor(
            id="csv_extractor",
            settings={
                "has_header": True,
                "delimiter": ",",
                "max_rows": 1000,
                "infer_types": True,
            }
        )
        ```

    Input:
        Content or List[Content] where each item contains:
        - data['content']: CSV file bytes or string, OR
        - data['temp_file_path']: Path to a CSV file on disk

    Output:
        Content with added fields:
        - data['csv_output']['headers']: List of column header names (or generated names)
        - data['csv_output']['rows']: List of dicts (header-keyed) for each data row
        - data['csv_output']['row_count']: Number of data rows extracted
        - data['csv_output']['column_count']: Number of columns
        - data['csv_output']['text']: Plain-text representation (if extract_text enabled)
        - summary_data['rows_extracted']: Number of rows extracted
        - summary_data['columns_detected']: Number of columns detected
        - summary_data['csv_extraction_status']: "success" or error description
    """

    def __init__(
        self,
        id: str,
        settings: Optional[Dict[str, Any]] = None,
        **kwargs,
    ):
        super().__init__(id=id, settings=settings, **kwargs)

        self.content_field = self.get_setting("content_field", default="content")
        self.temp_file_field = self.get_setting("temp_file_path_field", default="temp_file_path")
        self.output_field = self.get_setting("output_field", default="csv_output")
        self.delimiter = self.get_setting("delimiter", default=",")
        self.quotechar = self.get_setting("quotechar", default='"')
        self.has_header = self.get_setting("has_header", default=True)
        self.encoding = self.get_setting("encoding", default="utf-8")
        self.max_rows = self.get_setting("max_rows", default=0)
        self.skip_empty_rows = self.get_setting("skip_empty_rows", default=True)
        self.strip_whitespace = self.get_setting("strip_whitespace", default=True)
        self.infer_types = self.get_setting("infer_types", default=False)
        self.extract_text = self.get_setting("extract_text", default=False)

        if self.debug_mode:
            logger.debug(
                f"CSVExtractorExecutor {self.id} initialized: "
                f"delimiter={self.delimiter!r}, has_header={self.has_header}, "
                f"max_rows={self.max_rows}, infer_types={self.infer_types}"
            )

    # ------------------------------------------------------------------
    # ParallelExecutor abstract method
    # ------------------------------------------------------------------

    async def process_content_item(self, content: Content) -> Content:
        """Process a single CSV file.

        Implements the abstract method from ParallelExecutor.
        """
        try:
            if not content or not content.data:
                raise ValueError("Content must have data")

            csv_text = self._get_csv_text(content)
            reader = csv.reader(
                io.StringIO(csv_text),
                delimiter=self.delimiter,
                quotechar=self.quotechar,
            )

            rows_iter = iter(reader)

            # Determine headers
            if self.has_header:
                try:
                    headers = next(rows_iter)
                except StopIteration:
                    headers = []
            else:
                headers = None  # will be auto-generated after peeking at first row

            extracted_rows: List[Dict[str, Any]] = []
            first_row_width: int = 0
            row_count = 0

            for raw_row in rows_iter:
                # Auto-generate headers from first data row width if needed
                if headers is None:
                    first_row_width = len(raw_row)
                    headers = [f"col_{i}" for i in range(first_row_width)]

                # Optionally skip empty rows
                if self.skip_empty_rows and all(
                    cell.strip() == "" for cell in raw_row
                ):
                    continue

                # Apply max_rows limit
                if self.max_rows > 0 and row_count >= self.max_rows:
                    break

                processed_row = self._process_row(raw_row, headers)
                extracted_rows.append(processed_row)
                row_count += 1

            # Handle edge case: no data rows and no header → empty result
            if headers is None:
                headers = []

            column_count = len(headers)

            # Strip whitespace from headers too
            if self.strip_whitespace:
                headers = [h.strip() for h in headers]

            extracted_data: Dict[str, Any] = {
                "headers": headers,
                "rows": extracted_rows,
                "row_count": row_count,
                "column_count": column_count,
            }

            if self.extract_text:
                extracted_data["text"] = self._rows_to_text(headers, extracted_rows)

            content.data[self.output_field] = extracted_data

            content.summary_data["rows_extracted"] = row_count
            content.summary_data["columns_detected"] = column_count
            content.summary_data["csv_extraction_status"] = "success"

            if self.debug_mode:
                logger.debug(
                    f"Extracted {row_count} rows x {column_count} columns "
                    f"from {content.id.canonical_id}"
                )

        except Exception as e:
            logger.error(
                f"CSVExtractorExecutor {self.id} failed processing "
                f"{content.id}: {e}",
                exc_info=True,
            )
            raise

        return content

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _get_csv_text(self, content: Content) -> str:
        """Resolve CSV content to a text string."""
        raw = content.data.get(self.content_field)
        if raw is not None:
            if isinstance(raw, bytes):
                return raw.decode(self.encoding)
            if isinstance(raw, str):
                return raw

        temp_path = content.data.get(self.temp_file_field)
        if temp_path is not None:
            with open(temp_path, "r", encoding=self.encoding) as fh:
                return fh.read()

        raise ValueError(
            f"CSV content missing. Needs either '{self.content_field}' "
            f"or '{self.temp_file_field}' in data."
        )

    def _process_row(
        self, raw_row: List[str], headers: List[str]
    ) -> Dict[str, Any]:
        """Convert a raw CSV row into a header-keyed dict."""
        row_dict: Dict[str, Any] = {}
        for idx, header in enumerate(headers):
            value = raw_row[idx] if idx < len(raw_row) else ""
            if self.strip_whitespace and isinstance(value, str):
                value = value.strip()
            if self.strip_whitespace:
                header = header.strip()
            if self.infer_types:
                value = self._infer_type(value)
            row_dict[header] = value
        return row_dict

    @staticmethod
    def _infer_type(value: str) -> Any:
        """Attempt to cast a string value to int or float."""
        if not isinstance(value, str):
            return value
        # Try int
        try:
            return int(value)
        except (ValueError, TypeError):
            pass
        # Try float
        try:
            return float(value)
        except (ValueError, TypeError):
            pass
        return value

    @staticmethod
    def _rows_to_text(
        headers: List[str], rows: List[Dict[str, Any]]
    ) -> str:
        """Produce a simple plain-text table representation."""
        lines: List[str] = []
        if headers:
            lines.append(" | ".join(headers))
            lines.append("-" * len(lines[0]))
        for row in rows:
            lines.append(
                " | ".join(str(row.get(h, "")) for h in headers)
            )
        return "\n".join(lines)
