"""
Excel Workbook Extraction Example

Demonstrates extracting text, sheets, tables, properties, and images from Excel workbooks using:
- ContentRetrieverExecutor: Retrieve Excel files from storage
- ExcelExtractorExecutor: Extract content using openpyxl
- Efficient processing of Excel workbook sets
"""

import asyncio
import logging
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from samples.setup_logger import setup_logging
from packages.pipeline import PipelineExecutor, PipelineResult
from packages.models import Content, ContentIdentifier

# Get the current directory
samples_dir = Path(__file__).parent.parent

# Load environment variables
load_dotenv(f'{samples_dir}/.env')

logger = logging.getLogger(__name__)

setup_logging()

async def run_pipeline():
    """Execute pipeline"""
    
    print("=" * 70)
    
    # Load config
    config_path = Path(__file__).parent / "pipeline_config.yaml"
    executor_catalog_path = samples_dir.parent / "executor_catalog.yaml"
    
    async with PipelineExecutor.from_config_file(
        config_path=config_path,
        pipeline_name="excel_extraction_pipeline",
        executor_catalog_path=executor_catalog_path,
    ) as pipeline_executor:
        
        print(f"\n✓ Initialized pipeline")
        
        documents = []
        
        # load documents from local path
        local_path = Path(f"{samples_dir}/99-assets")
        for file in local_path.glob('*.xlsx'):
            print(f"  Found file: {file}")
            
            documents.append(
                Content(
                    id=ContentIdentifier(
                        canonical_id=file.name,
                        unique_id=file.name,
                        source_name="local_file",
                        source_type="local_file",
                        path=str(file),
                    )
                )
            )
        
        # Also check for .xlsm files
        for file in local_path.glob('*.xlsm'):
            print(f"  Found file: {file}")
            
            documents.append(
                Content(
                    id=ContentIdentifier(
                        canonical_id=file.name,
                        unique_id=file.name,
                        source_name="local_file",
                        source_type="local_file",
                        path=str(file),
                    )
                )
            )
        
        print(f"\n✓ Created {len(documents)} documents for Excel extraction")
        
        if len(documents) == 0:
            print(f"\n⚠️  No Excel files found in {local_path}")
            print(f"   Please add .xlsx or .xlsm files to the directory")
            return
        
        # Process all documents
        result = await pipeline_executor.execute(documents[0:2])  # limit to first 2 for testing
        
        # write results to output folder
        output_folder = Path(__file__).parent / "output"
        output_folder.mkdir(exist_ok=True)
        output_file = output_folder / "pipeline_result.json"
        with open(output_file, 'w', encoding='utf-8') as f:
                f.write(result.model_dump_json(indent=2))
        print(f"  Wrote output to {output_file}")
        
        # Analyze results
        successful = sum(1 for d in result.documents if d.get_status() == "completed") if isinstance(result.documents, list) else result.documents.get_status() == "completed"
        failed = sum(1 for d in result.documents if d.get_status() == "failed") if isinstance(result.documents, list) else result.documents.get_status() == "failed"
        total_duration = result.duration_seconds
        
        print(f"\n✓ Excel extraction completed")
        print(f"  Total documents: {len(result.documents) if isinstance(result.documents, list) else 1}")
        print(f"  Successful: {successful}")
        print(f"  Failed: {failed}")
        print(f"  Total duration (seconds): {total_duration:.2f}s")
        print(f"  Avg per document: {total_duration/(len(result.documents) if isinstance(result.documents, list) else 1):.2f}s")
        
        # Show sample extracted data
        if isinstance(result.documents, list) and len(result.documents) > 0:
            first_doc = result.documents[0]
            if 'excel_output' in first_doc.data:
                excel_output = first_doc.data['excel_output']
                print(f"\n📄 Sample Extraction (First Document):")
                print(f"  Document ID: {first_doc.id}")
                if 'text' in excel_output:
                    print(f"  Text length: {len(excel_output['text'])} characters")
                    print(f"  Text preview: {excel_output['text'][:200]}...")
                if 'sheets' in excel_output:
                    print(f"  Sheets extracted: {len(excel_output['sheets'])}")
                    if excel_output['sheets']:
                        first_sheet = excel_output['sheets'][0]
                        print(f"    First sheet: {first_sheet.get('sheet_name', 'Unknown')}")
                        print(f"    Rows: {first_sheet.get('max_row', 0)}, Columns: {first_sheet.get('max_column', 0)}")
                        print(f"    Cells: {first_sheet.get('cell_count', 0)}")
                if 'tables' in excel_output:
                    print(f"  Tables extracted: {len(excel_output['tables'])}")
                    if excel_output['tables']:
                        first_table = excel_output['tables'][0]
                        print(f"    First table: {first_table.get('table_name', 'Unknown')}")
                        print(f"    Range: {first_table.get('range', 'N/A')}")
                        print(f"    Rows: {first_table.get('rows', 0)}, Columns: {first_table.get('columns', 0)}")
                if 'properties' in excel_output:
                    props = excel_output['properties']
                    print(f"  Workbook properties:")
                    if props.get('title'):
                        print(f"    Title: {props['title']}")
                    if props.get('creator'):
                        print(f"    Creator: {props['creator']}")
                    if props.get('sheet_count'):
                        print(f"    Total sheets: {props['sheet_count']}")
                    if props.get('sheet_names'):
                        print(f"    Sheet names: {', '.join(props['sheet_names'])}")
                if 'formulas' in excel_output:
                    print(f"  Formulas extracted: {len(excel_output['formulas'])}")
                if 'comments' in excel_output:
                    print(f"  Comments extracted: {len(excel_output['comments'])}")
                if 'images' in excel_output:
                    print(f"  Images extracted: {len(excel_output['images'])}")
        
        # Show processing events
        print(f"\n📊 Processing Events:")
        for i, event in enumerate(result.events[:5]):  # Show first 5
            print(f"\n  Event {i+1}: {event.event_type}")
            print(f"    Executor: {event.executor_id}")
            
        print("\n\n" + "=" * 70)
        print(f"Output written to: {output_file}\n")
    
    print("\n" + "=" * 70)
    print("Done!")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(run_pipeline())
