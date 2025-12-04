"""
Example demonstrating the TableRowSplitterExecutor.

This example shows how to use the TableRowSplitterExecutor to process
tabular data and create individual content items for each row.
"""

import asyncio
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from packages.executors import TableRowSplitterExecutor
from packages.models import Content, ContentIdentifier
from samples.setup_logger import setup_logging

# Get the current directory
samples_dir = Path(__file__).parent.parent

setup_logging()

logger = logging.getLogger(__name__)


async def example_list_of_dicts():
    """Example: Split a list of dictionaries (e.g., from JSON or database)."""
    logger.info("\n=== Example 1: List of Dictionaries ===")
    
    # Create executor
    executor = TableRowSplitterExecutor(
        id="row_splitter",
        settings={
            "table_field": "customer_data",
            "table_format": "list_of_dicts",
            "row_id_field": "customer_id",
            "include_headers": True,
            "output_format": "dict"
        },
        debug_mode=True
    )
    
    # Create sample content with customer data
    content = Content(
        id=ContentIdentifier(canonical_id="customer_table_1"),
        data={
            "customer_data": [
                {"customer_id": "C001", "name": "John Doe", "email": "john@example.com", "age": 30},
                {"customer_id": "C002", "name": "Jane Smith", "email": "jane@example.com", "age": 28},
                {"customer_id": "C003", "name": "Bob Johnson", "email": "bob@example.com", "age": 35},
            ]
        }
    )
    
    # Process the content to split into rows
    row_contents = await executor.process_input(input=content, ctx=None)
    
    logger.info(f"\nCreated {len(row_contents)} row content items:")
    for row_content in row_contents:
        logger.info(f"  - ID: {row_content.id.canonical_id}")
        logger.info(f"    Data: {row_content.data['row_data']}")
        logger.info(f"    Summary: {row_content.summary_data}")


async def example_list_of_lists():
    """Example: Split a list of lists with headers (e.g., from CSV or Excel)."""
    logger.info("\n=== Example 2: List of Lists with Header ===")
    
    executor = TableRowSplitterExecutor(
        id="csv_splitter",
        settings={
            "table_field": "table_data",
            "table_format": "list_of_lists",
            "has_header": True,
            "header_row_index": 0,
            "skip_empty_rows": True,
            "output_format": "both"  # Include both dict and list formats
        },
        debug_mode=True
    )
    
    content = Content(
        id=ContentIdentifier(canonical_id="sales_table_1"),
        data={
            "table_data": [
                ["Product", "Quantity", "Price", "Total"],  # Header row
                ["Widget A", "10", "25.50", "255.00"],
                ["Widget B", "5", "30.00", "150.00"],
                ["", "", "", ""],  # Empty row (will be skipped)
                ["Widget C", "15", "20.00", "300.00"],
            ]
        }
    )
    
    row_contents = await executor.process_input(input=content, ctx=None)
    
    logger.info(f"\nCreated {len(row_contents)} row content items:")
    for row_content in row_contents:
        logger.info(f"  - ID: {row_content.id.canonical_id}")
        logger.info(f"    Dict: {row_content.data['row_data']}")
        logger.info(f"    List: {row_content.data['row_values']}")


async def example_csv_string():
    """Example: Split CSV string data."""
    logger.info("\n=== Example 3: CSV String ===")
    
    executor = TableRowSplitterExecutor(
        id="csv_parser",
        settings={
            "table_field": "csv_content",
            "table_format": "csv",
            "has_header": True,
            "csv_delimiter": ",",
            "max_rows": 2  # Only process first 2 rows
        },
        debug_mode=True
    )
    
    csv_data = """Name,Department,Salary
Alice Johnson,Engineering,95000
Bob Williams,Marketing,75000
Charlie Brown,Sales,82000
Diana Prince,HR,68000"""
    
    content = Content(
        id=ContentIdentifier(canonical_id="employee_csv_1"),
        data={
            "csv_content": csv_data
        }
    )
    
    row_contents = await executor.process_input(input=content, ctx=None)
    
    logger.info(f"\nCreated {len(row_contents)} row content items (max_rows=2):")
    for row_content in row_contents:
        logger.info(f"  - ID: {row_content.id.canonical_id}")
        logger.info(f"    Data: {row_content.data['row_data']}")


async def example_word_tables():
    """Example: Split tables extracted from Word documents."""
    logger.info("\n=== Example 4: Word Document Tables ===")
    
    executor = TableRowSplitterExecutor(
        id="word_table_splitter",
        settings={
            "table_field": "word_output.tables",
            "table_format": "word_tables",
            "has_header": True,
            "preserve_parent_data": True,
            "parent_data_fields": ["filename", "document_type"]
        },
        debug_mode=True
    )
    
    # Simulate Word extractor output
    content = Content(
        id=ContentIdentifier(canonical_id="report_doc_1"),
        data={
            "filename": "quarterly_report.docx",
            "document_type": "financial_report",
            "word_output": {
                "tables": [
                    {
                        "table_number": 1,
                        "rows": 4,
                        "columns": 3,
                        "data": [
                            ["Quarter", "Revenue", "Profit"],  # Header
                            ["Q1", "$100K", "$25K"],
                            ["Q2", "$120K", "$30K"],
                            ["Q3", "$115K", "$28K"],
                        ]
                    }
                ]
            }
        }
    )
    
    row_contents = await executor.process_input(input=content, ctx=None)
    
    logger.info(f"\nCreated {len(row_contents)} row content items:")
    for row_content in row_contents:
        logger.info(f"  - ID: {row_content.id.canonical_id}")
        logger.info(f"    Data: {row_content.data['row_data']}")
        logger.info(f"    Parent filename: {row_content.data.get('filename')}")


async def example_with_row_filtering():
    """Example: Advanced row filtering and indexing."""
    logger.info("\n=== Example 5: Row Filtering ===")
    
    executor = TableRowSplitterExecutor(
        id="filtered_splitter",
        settings={
            "table_field": "products",
            "table_format": "list_of_dicts",
            "row_id_field": "sku",
            "start_row": 1,  # Skip first row
            "max_rows": 3,   # Process only 3 rows
            "include_row_index": True,
            "row_id_prefix": "product"
        },
        debug_mode=True
    )
    
    content = Content(
        id=ContentIdentifier(canonical_id="inventory_1"),
        data={
            "products": [
                {"sku": "SKU001", "name": "Item 1", "stock": 100},
                {"sku": "SKU002", "name": "Item 2", "stock": 50},
                {"sku": "SKU003", "name": "Item 3", "stock": 75},
                {"sku": "SKU004", "name": "Item 4", "stock": 200},
                {"sku": "SKU005", "name": "Item 5", "stock": 150},
            ]
        }
    )
    
    row_contents = await executor.process_input(input=content, ctx=None)
    
    logger.info(f"\nCreated {len(row_contents)} row content items (start_row=1, max_rows=3):")
    for row_content in row_contents:
        logger.info(f"  - ID: {row_content.id.canonical_id}")
        logger.info(f"    Row Index: {row_content.data['row_index']}")
        logger.info(f"    Data: {row_content.data['row_data']}")


async def main():
    """Run all examples."""
    await example_list_of_dicts()
    await example_list_of_lists()
    await example_csv_string()
    await example_word_tables()
    await example_with_row_filtering()


if __name__ == "__main__":
    asyncio.run(main())
