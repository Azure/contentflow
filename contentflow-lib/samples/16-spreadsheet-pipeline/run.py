"""
Spreadsheet Data Processing Pipeline

Process Excel/CSV files with schema detection, data validation, transformation,
and structured output generation. This pipeline demonstrates:
- Excel file extraction with schema detection
- Table row splitting for parallel processing
- Field mapping and normalization
- Data validation and cleaning
- Azure Blob Storage output

Suitable for ETL workflows, data migration, customer data imports,
financial report processing, and dataset normalization.
"""

import asyncio
import logging
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from samples.setup_logger import setup_logging
from contentflow.pipeline import PipelineExecutor, PipelineResult
from contentflow.models import Content, ContentIdentifier

# Get the current directory
samples_dir = Path(__file__).parent.parent

# Load environment variables
load_dotenv(f'{samples_dir}/.env')

logger = logging.getLogger(__name__)

setup_logging()

async def run_pipeline():
    """Execute spreadsheet data processing pipeline"""
    
    print("=" * 80)
    print("Spreadsheet Data Processing Pipeline")
    print("=" * 80)
    
    # Validate required environment variables
    required_vars = [
        "AZURE_STORAGE_ACCOUNT",
        "AZURE_OUTPUT_CONTAINER_NAME"
    ]
    
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        print(f"\n❌ Missing required environment variables: {', '.join(missing_vars)}")
        print("Please set them in your .env file")
        return
    
    # Load config
    config_path = Path(__file__).parent / "pipeline-config.yaml"
    executor_catalog_path = Path(__file__).parent.parent.parent / "executor_catalog.yaml"
    
    async with PipelineExecutor.from_config_file(
        config_path=config_path,
        pipeline_name="spreadsheet_data_pipeline",
        executor_catalog_path=executor_catalog_path,
    ) as pipeline:
        
        print(f"\n✓ Initialized spreadsheet processing pipeline")
        print(f"  - Output: Azure Blob Storage ({os.getenv('AZURE_OUTPUT_CONTAINER_NAME')})")
        print(f"  - Field Mapping: Enabled (normalize column names)")
        print(f"  - Data Validation: Enabled")
        
        # Create sample Excel data for processing
        # In production, you would load actual Excel files
        documents = []
        
        # Sample spreadsheet document
        # For this example, we'll use a sample Excel file path
        # You can replace this with your actual Excel file
        sample_excel_path = f"{samples_dir}/99-assets/sample-data.xlsx"
        
        document = Content(
            id=ContentIdentifier(
                canonical_id="excel_001",
                unique_id="excel_001",
                source_id="sample_spreadsheets",
                source_name="Customer Orders",
                source_type="file",
                path=sample_excel_path,
            )
        )
        documents.append(document)
        
        print(f"\n✓ Created {len(documents)} spreadsheet document for processing")
        
        print(f"\n🔄 Starting spreadsheet processing...")
        print(f"  Processing steps:")
        print(f"    1. Load Excel file")
        print(f"    2. Extract sheets and tables")
        print(f"    3. Split into individual rows")
        print(f"    4. Map and normalize field names")
        print(f"    5. Select relevant fields")
        print(f"    6. Write to Azure Blob Storage")
        
        # Execute pipeline
        result = await pipeline.execute(documents)
        
        # Write results to output folder
        output_folder = Path(__file__).parent / "output"
        output_folder.mkdir(exist_ok=True)
        output_file = output_folder / "spreadsheet_result.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(result.model_dump_json(indent=2))
        print(f"\n✓ Wrote detailed results to {output_file}")
        
        # Analyze results
        total_docs = len(result.content) if isinstance(result.content, list) else 1
        successful = sum(1 for d in result.content if d.get_status() == "completed") if isinstance(result.content, list) else (1 if result.content.get_status() == "completed" else 0)
        failed = sum(1 for d in result.content if d.get_status() == "failed") if isinstance(result.content, list) else (1 if result.content.get_status() == "failed" else 0)
        total_duration = result.duration_seconds
        
        print(f"\n" + "=" * 80)
        print(f"✓ Spreadsheet Processing Completed")
        print(f"=" * 80)
        print(f"  Total documents processed: {total_docs}")
        print(f"  Successfully processed: {successful}")
        print(f"  Failed: {failed}")
        print(f"  Total duration: {total_duration:.2f}s")
        if total_docs > 0:
            print(f"  Avg per document: {total_duration/total_docs:.2f}s")
        
        # Show sample results
        if isinstance(result.content, list) and len(result.content) > 0:
            print(f"\n" + "=" * 80)
            print(f"📊 Processing Results")
            print(f"=" * 80)
            
            # Count total rows processed
            total_rows = len([d for d in result.content if 'row_number' in d.data])
            print(f"\n✓ Total rows extracted and processed: {total_rows}")
            
            # Show first few records
            print(f"\n📄 Sample Records (First 5):")
            sample_count = min(5, len(result.content))
            
            for idx, doc in enumerate(result.content[:sample_count], 1):
                print(f"\n{'─' * 80}")
                print(f"Record {idx}:")
                
                # Show extracted fields
                displayed_fields = ['name', 'email', 'phone', 'date', 'amount', 'status', 'row_number']
                for field in displayed_fields:
                    if field in doc.data:
                        value = doc.data[field]
                        print(f"  {field:12s}: {value}")
                
                # Show metadata
                if 'excel_output' in doc.data:
                    excel_out = doc.data['excel_output']
                    if isinstance(excel_out, dict) and 'properties' in excel_out:
                        props = excel_out['properties']
                        if 'author' in props:
                            print(f"  {'author':12s}: {props['author']}")
            
            # Show statistics
            if total_rows > 0:
                print(f"\n" + "=" * 80)
                print(f"📈 Processing Statistics")
                print(f"=" * 80)
                
                # Count by status if available
                status_counts = {}
                amount_total = 0
                amount_count = 0
                
                for doc in result.content:
                    if 'status' in doc.data:
                        status = doc.data['status']
                        status_counts[status] = status_counts.get(status, 0) + 1
                    
                    if 'amount' in doc.data:
                        try:
                            amount = float(str(doc.data['amount']).replace('$', '').replace(',', ''))
                            amount_total += amount
                            amount_count += 1
                        except (ValueError, TypeError):
                            pass
                
                if status_counts:
                    print(f"\n📊 Status Distribution:")
                    for status, count in sorted(status_counts.items()):
                        percentage = (count / total_rows) * 100
                        print(f"  {status:15s}: {count:3d} ({percentage:5.1f}%)")
                
                if amount_count > 0:
                    print(f"\n💰 Financial Summary:")
                    print(f"  Total Amount: ${amount_total:,.2f}")
                    print(f"  Average Amount: ${amount_total/amount_count:,.2f}")
                    print(f"  Records with Amount: {amount_count}")
        
        print(f"\n" + "=" * 80)
        print(f"🎉 Spreadsheet data has been processed and exported to Azure Blob Storage!")
        print(f"=" * 80)
        print(f"\n📦 Output Location:")
        print(f"  Container: {os.getenv('AZURE_OUTPUT_CONTAINER_NAME')}")
        print(f"  Path Pattern: processed-data/{{year}}/{{month}}/{{day}}/")
        print(f"  File Pattern: record_{{row_number}}_{{timestamp}}.json")


if __name__ == "__main__":
    asyncio.run(run_pipeline())
