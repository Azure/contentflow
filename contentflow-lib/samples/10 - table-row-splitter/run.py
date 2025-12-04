"""
Table Row Splitter Executor Example

This example demonstrates how to use the TableRowSplitterExecutor to split
tabular data into individual content items for parallel processing.

Features demonstrated:
1. Read CSV file and load as table data
2. Split table into individual row content items
3. Process each row independently
4. Monitor processing with event streaming
"""

import asyncio
import csv
import logging
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from samples.setup_logger import setup_logging
from packages.pipeline import PipelineExecutor
from packages.models import Content, ContentIdentifier

# Get the current directory
samples_dir = Path(__file__).parent.parent

# Load environment variables
load_dotenv(f'{samples_dir}/.env')

setup_logging()

logger = logging.getLogger(__name__)


async def csv_to_rows_basic():
    """Basic example: Read CSV file and split into rows."""
    
    print("=" * 80)
    print("Table Row Splitter - Basic CSV Processing")
    print("=" * 80)
    
    # Load config and create executor
    config_path = Path(__file__).parent / "csv_to_rows_config.yaml"
    executor_catalog_path = Path(__file__).parent.parent.parent / "executor_catalog.yaml"
    
    print(f"\n✓ Loading pipeline configuration")
    print(f"  Config: {config_path.name}")
    print(f"  Pipeline: csv_to_rows_basic")
    
    async with PipelineExecutor.from_config_file(
        config_path=config_path,
        pipeline_name="csv_to_rows_basic",
        executor_catalog_path=executor_catalog_path
    ) as pipeline_executor:
        
        print(f"\n✓ Pipeline loaded with 2 executors:")
        print(f"  1. PassThroughExecutor - Load CSV file")
        print(f"  2. TableRowSplitterExecutor - Split into rows")
        
        # Create input content with CSV file path
        csv_file = Path(__file__).parent / "sample_data.csv"
        
        if not csv_file.exists():
            print(f"\n❌ CSV file not found: {csv_file}")
            print(f"   Creating sample CSV file...")
            create_sample_csv(csv_file)
            print(f"   ✓ Sample CSV created")
        
        # Read CSV file content
        with open(csv_file, 'r', encoding='utf-8') as f:
            csv_content = f.read()
        
        print(f"\n📄 Input CSV file: {csv_file.name}")
        print(f"  Size: {len(csv_content)} characters")
        print(f"\n  Preview:")
        for i, line in enumerate(csv_content.split('\n')[:5], 1):
            print(f"    {i}. {line}")
        
        # Create input content
        input_content = Content(
            id=ContentIdentifier(canonical_id="sample_csv"),
            data={
                "csv_data": csv_content,
                "filename": csv_file.name
            }
        )
        
        # Execute pipeline
        print(f"\n🔄 Executing pipeline...")
        result = await pipeline_executor.execute([input_content])
        
        print(f"\n✓ Pipeline completed")
        print(f"  Status: {result.status}")
        print(f"  Duration: {result.duration_seconds:.2f}s")
        
        # Write results to output folder
        output_folder = Path(__file__).parent / "output"
        output_folder.mkdir(exist_ok=True)
        output_file = output_folder / "csv_to_rows_basic_result.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(result.model_dump_json(indent=2))
        print(f"  Output: {output_file}")
        
        # Display results
        if result.documents:
            rows = result.documents if isinstance(result.documents, list) else [result.documents]
            print(f"\n📊 Created {len(rows)} row content items:")
            
            for i, row in enumerate(rows[:10], 1):
                print(f"\n  Row {i}:")
                print(f"    ID: {row.id.canonical_id}")
                print(f"    Data: {row.data.get('row_data', {})}")
                print(f"    Row Index: {row.data.get('row_index', 'N/A')}")
            
            if len(rows) > 10:
                print(f"\n  ... and {len(rows) - 10} more rows")
        
        if result.error:
            print(f"\n❌ Error: {result.error}")
        
        # Show processing events
        print(f"\n📊 Processing Events:")
        for event in result.events:
            print(f"  • {event.event_type} - {event.executor_id}")
        
        print("\n" + "=" * 80)
    
    print()


async def csv_to_rows_with_streaming():
    """Example with streaming to monitor progress."""
    
    print("=" * 80)
    print("Table Row Splitter - CSV Processing with Event Streaming")
    print("=" * 80)
    
    # Load config and create executor
    config_path = Path(__file__).parent / "csv_to_rows_config.yaml"
    executor_catalog_path = Path(__file__).parent.parent.parent / "executor_catalog.yaml"
    
    print(f"\n✓ Loading pipeline configuration")
    
    async with PipelineExecutor.from_config_file(
        config_path=config_path,
        pipeline_name="csv_to_rows_basic",
        executor_catalog_path=executor_catalog_path
    ) as pipeline_executor:
        
        print(f"\n✓ Pipeline loaded")
        
        # Create input content with CSV file path
        csv_file = Path(__file__).parent / "sample_data.csv"
        
        if not csv_file.exists():
            create_sample_csv(csv_file)
        
        # Read CSV file content
        with open(csv_file, 'r', encoding='utf-8') as f:
            csv_content = f.read()
        
        print(f"\n📄 Processing: {csv_file.name}")
        
        # Create input content
        input_content = Content(
            id=ContentIdentifier(canonical_id="sample_csv_streaming"),
            data={
                "csv_data": csv_content,
                "filename": csv_file.name
            }
        )
        
        print(f"\n📡 Streaming events...\n")
        
        # Execute with streaming
        row_count = 0
        async for event in pipeline_executor.execute_stream([input_content]):
            if event.event_type == "ExecutorInvokedEvent":
                print(f"  ▶ Executor '{event.executor_id}' started")
            elif event.event_type == "ExecutorCompletedEvent":
                print(f"  ✓ Executor '{event.executor_id}' completed")
                if event.data:
                    items = event.data if isinstance(event.data, list) else [event.data]
                    print(f"    Output: {len(items)} items")
            elif event.event_type == "WorkflowOutputEvent":
                print(f"  📤 Final output received")
                if event.data:
                    rows = event.data if isinstance(event.data, list) else [event.data]
                    row_count = len(rows)
                    
                    # Write output
                    output_folder = Path(__file__).parent / "output"
                    output_folder.mkdir(exist_ok=True)
                    output_file = output_folder / "csv_to_rows_streaming_result.json"
                    with open(output_file, 'w', encoding='utf-8') as f:
                        f.write(event.model_dump_json(indent=2))
                    print(f"    Saved to: {output_file}")
        
        print(f"\n✓ Processing completed")
        print(f"  Total rows created: {row_count}")
    
    print("\n" + "=" * 80)
    print()


async def csv_to_rows_with_filters():
    """Example with row filtering and advanced options."""
    
    print("=" * 80)
    print("Table Row Splitter - CSV Processing with Filters")
    print("=" * 80)
    
    # Load config and create executor
    config_path = Path(__file__).parent / "csv_to_rows_config.yaml"
    executor_catalog_path = Path(__file__).parent.parent.parent / "executor_catalog.yaml"
    
    print(f"\n✓ Loading pipeline configuration")
    print(f"  Pipeline: csv_to_rows_filtered")
    print(f"  Filters: skip first 2 rows, max 5 rows")
    
    async with PipelineExecutor.from_config_file(
        config_path=config_path,
        pipeline_name="csv_to_rows_filtered",
        executor_catalog_path=executor_catalog_path
    ) as pipeline_executor:
        
        print(f"\n✓ Pipeline loaded")
        
        # Create input content with CSV file path
        csv_file = Path(__file__).parent / "sample_data.csv"
        
        if not csv_file.exists():
            create_sample_csv(csv_file)
        
        # Read CSV file content
        with open(csv_file, 'r', encoding='utf-8') as f:
            csv_content = f.read()
        
        print(f"\n📄 Processing: {csv_file.name}")
        
        # Create input content
        input_content = Content(
            id=ContentIdentifier(canonical_id="sample_csv_filtered"),
            data={
                "csv_data": csv_content,
                "filename": csv_file.name,
                "source": "local_file"
            }
        )
        
        # Execute pipeline
        print(f"\n🔄 Executing pipeline...")
        result = await pipeline_executor.execute([input_content])
        
        print(f"\n✓ Pipeline completed")
        print(f"  Status: {result.status}")
        
        # Write results
        output_folder = Path(__file__).parent / "output"
        output_folder.mkdir(exist_ok=True)
        output_file = output_folder / "csv_to_rows_filtered_result.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(result.model_dump_json(indent=2))
        
        # Display results
        if result.documents:
            rows = result.documents if isinstance(result.documents, list) else [result.documents]
            print(f"\n📊 Created {len(rows)} row content items (with filters):")
            
            for i, row in enumerate(rows, 1):
                row_data = row.data.get('row_data', {})
                print(f"\n  Row {i}:")
                print(f"    ID: {row.id.canonical_id}")
                print(f"    Original Index: {row.data.get('row_index', 'N/A')}")
                print(f"    Data: {row_data}")
                # Show preserved parent fields
                if 'filename' in row.data:
                    print(f"    Parent Filename: {row.data['filename']}")
                if 'source' in row.data:
                    print(f"    Parent Source: {row.data['source']}")
        
        print(f"\n  Output saved to: {output_file}")
    
    print("\n" + "=" * 80)
    print()


async def inline_csv_example():
    """Example with inline CSV data (no file)."""
    
    print("=" * 80)
    print("Table Row Splitter - Inline CSV Data")
    print("=" * 80)
    
    # Load config and create executor
    config_path = Path(__file__).parent / "csv_to_rows_config.yaml"
    executor_catalog_path = Path(__file__).parent.parent.parent / "executor_catalog.yaml"
    
    print(f"\n✓ Loading pipeline configuration")
    
    async with PipelineExecutor.from_config_file(
        config_path=config_path,
        pipeline_name="csv_to_rows_basic",
        executor_catalog_path=executor_catalog_path
    ) as pipeline_executor:
        
        print(f"\n✓ Pipeline loaded")
        
        # Create inline CSV data
        inline_csv = """Product,Category,Price,Stock
Laptop,Electronics,999.99,45
Mouse,Electronics,29.99,150
Keyboard,Electronics,79.99,89
Monitor,Electronics,299.99,34
Desk Chair,Furniture,199.99,23
Desk Lamp,Furniture,39.99,67"""
        
        print(f"\n📄 Using inline CSV data:")
        for i, line in enumerate(inline_csv.split('\n')[:4], 1):
            print(f"  {i}. {line}")
        print(f"  ...")
        
        # Create input content
        input_content = Content(
            id=ContentIdentifier(canonical_id="inline_products_csv"),
            data={
                "csv_data": inline_csv,
                "filename": "products.csv",
                "source": "inline"
            }
        )
        
        # Execute pipeline
        print(f"\n🔄 Executing pipeline...")
        result = await pipeline_executor.execute([input_content])
        
        print(f"\n✓ Pipeline completed")
        
        # Display results
        if result.documents:
            rows = result.documents if isinstance(result.documents, list) else [result.documents]
            print(f"\n📊 Created {len(rows)} product row items:")
            
            # Calculate statistics
            total_stock = sum(int(row.data.get('row_data', {}).get('Stock', 0)) for row in rows)
            electronics = sum(1 for row in rows if row.data.get('row_data', {}).get('Category') == 'Electronics')
            furniture = sum(1 for row in rows if row.data.get('row_data', {}).get('Category') == 'Furniture')
            
            print(f"\n  Statistics:")
            print(f"    Electronics items: {electronics}")
            print(f"    Furniture items: {furniture}")
            print(f"    Total stock units: {total_stock}")
            
            print(f"\n  Sample rows:")
            for i, row in enumerate(rows[:3], 1):
                row_data = row.data.get('row_data', {})
                print(f"    {i}. {row_data.get('Product', 'N/A')}: ${row_data.get('Price', 'N/A')} ({row_data.get('Stock', 'N/A')} in stock)")
        
        # Write output
        output_folder = Path(__file__).parent / "output"
        output_folder.mkdir(exist_ok=True)
        output_file = output_folder / "csv_to_rows_inline_result.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(result.model_dump_json(indent=2))
        print(f"\n  Output saved to: {output_file}")
    
    print("\n" + "=" * 80)
    print()


def create_sample_csv(file_path: Path):
    """Create a sample CSV file for demonstration."""
    
    sample_data = [
        ["EmployeeID", "Name", "Department", "Salary", "HireDate"],
        ["E001", "Alice Johnson", "Engineering", "95000", "2020-03-15"],
        ["E002", "Bob Williams", "Marketing", "75000", "2019-07-22"],
        ["E003", "Charlie Brown", "Sales", "82000", "2021-01-10"],
        ["E004", "Diana Prince", "HR", "68000", "2018-11-05"],
        ["E005", "Eve Davis", "Engineering", "98000", "2020-09-18"],
        ["E006", "Frank Miller", "Finance", "85000", "2019-04-30"],
        ["E007", "Grace Lee", "Marketing", "72000", "2021-06-12"],
        ["E008", "Henry Wilson", "Engineering", "102000", "2017-12-01"],
        ["E009", "Iris Martinez", "Sales", "78000", "2020-02-28"],
        ["E010", "Jack Thompson", "IT", "91000", "2019-08-14"],
    ]
    
    with open(file_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerows(sample_data)


async def main():
    """Run all examples."""
    
    # Choose which example to run
    examples = {
        "1": ("Basic CSV to Rows", csv_to_rows_basic),
        "2": ("CSV with Event Streaming", csv_to_rows_with_streaming),
        "3": ("CSV with Row Filters", csv_to_rows_with_filters),
        "4": ("Inline CSV Data", inline_csv_example),
    }
    
    print("\nTable Row Splitter Executor Examples")
    print("=" * 80)
    print("\nSelect an example to run:")
    for key, (name, _) in examples.items():
        print(f"  {key}. {name}")
    print(f"  5. Run all examples")
    print(f"  0. Exit")
    
    # For automated testing, check if argument provided
    if len(sys.argv) > 1:
        choice = sys.argv[1]
    else:
        choice = input("\nEnter choice (0-5) [default: 1]: ").strip() or "1"
    
    if choice == '0':
        return
    elif choice == '5':
        for name, func in examples.values():
            await func()
            print("\n")
    elif choice in examples:
        _, func = examples[choice]
        await func()
    else:
        print("\n❌ Invalid choice")


if __name__ == "__main__":
    asyncio.run(main())
