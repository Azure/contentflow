"""
Azure Content Understanding Extraction Example

Demonstrates extracting content from documents using Azure Content Understanding:
- ContentRetrieverExecutor: Retrieve documents from storage
- AzureContentUnderstandingExtractorExecutor: Extract content, tables, fields using AI
- RAG-optimized content extraction with 70+ prebuilt analyzers
- Efficient processing of document sets with semantic understanding
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
        pipeline_name="content_understanding_pipeline",
        executor_catalog_path=executor_catalog_path,
    ) as pipeline_executor:
        
        print(f"\n✓ Initialized pipeline")
        
        documents = []
        
        # load documents from  local path
        local_path = Path(f'{samples_dir}/99-assets/')
        for file in local_path.glob('*.pdf'):
            print(f"  Found file: {file}")
            
            documents.append(
                Content(
                    id=ContentIdentifier(
                        canonical_id=file.name,
                        unique_id=file.name,
                        source_id="local_file_source",
                        source_name="local_file",
                        source_type="local_file",
                        path=str(file),
                    )
                )
            )
        
        print(f"\n✓ Created {len(documents)} documents for batch processing")
        
        # Process all documents using batch executor
        result = await pipeline_executor.execute(documents[0:2])  # limit to first 2 for testing
        
        # Write results to output folder
        output_folder = Path(__file__).parent / "output"
        output_folder.mkdir(exist_ok=True)
        output_file = output_folder / "content_understanding_result.json"
        with open(output_file, 'w', encoding='utf-8') as f:
                f.write(result.model_dump_json(indent=2))
        print(f"  Wrote output to {output_file}")
        
        # Analyze results
        successful = sum(1 for d in result.documents if d.get_status() == "completed") if isinstance(result.documents, list) else result.documents.get_status() == "completed"
        failed = sum(1 for d in result.documents if d.get_status() == "failed") if isinstance(result.documents, list) else result.documents.get_status() == "failed"
        total_duration = result.duration_seconds
        
        print(f"\n✓ Content Understanding extraction completed")
        print(f"  Total documents: {len(result.documents) if isinstance(result.documents, list) else 1}")
        print(f"  Successful: {successful}")
        print(f"  Failed: {failed}")
        print(f"  Total duration (seconds): {total_duration:.2f}s")
        print(f"  Avg per document: {total_duration/(len(result.documents) if isinstance(result.documents, list) else 1):.2f}s")
        
        # Show sample extracted data
        if isinstance(result.documents, list) and len(result.documents) > 0:
            first_doc = result.documents[0]
            print(f"\n📄 Sample Results (First Document):")
            print(f"  Document ID: {first_doc.id}")
            
            if 'content_understanding_output' in first_doc.data:
                cu_output = first_doc.data['content_understanding_output']
                
                if 'text' in cu_output and cu_output['text']:
                    print(f"\n  📝 Text Extraction:")
                    print(f"    Length: {len(cu_output['text'])} characters")
                    print(f"    Preview: {cu_output['text'][:200]}...")
                
                if 'markdown' in cu_output and cu_output['markdown']:
                    print(f"\n  📋 Markdown Extraction:")
                    print(f"    Length: {len(cu_output['markdown'])} characters")
                    print(f"    Preview: {cu_output['markdown'][:200]}...")
                
                if 'tables' in cu_output and cu_output['tables']:
                    print(f"\n  📊 Tables Extracted: {len(cu_output['tables'])}")
                    for i, table in enumerate(cu_output['tables'][:2]):
                        print(f"    Table {i+1}: {table.get('row_count', 0)} rows x {table.get('column_count', 0)} columns")
                
                if 'fields' in cu_output and cu_output['fields']:
                    print(f"\n  🏷️  Fields Extracted: {len(cu_output['fields'])}")
                    for field_name, field_value in list(cu_output['fields'].items())[:5]:
                        print(f"    {field_name}: {field_value}")
                
                if 'pages' in cu_output and cu_output['pages']:
                    print(f"\n  📄 Pages Extracted: {len(cu_output['pages'])}")
            
            print(f"\n  ℹ️  Summary Data:")
            print(f"    Analyzer: {first_doc.summary_data.get('analyzer_id', 'N/A')}")
            print(f"    Status: {first_doc.summary_data.get('extraction_status', 'N/A')}")
            print(f"    Pages analyzed: {first_doc.summary_data.get('pages_analyzed', 0)}")
        
        # Show processing events
        print(f"\n📊 Processing Events:")
        for i, event in enumerate(result.events):
            print(f"\n  Event {i+1}: {event.event_type}")
            print(f"    Executor: {event.executor_id}")
    
        print("\n" + "=" * 70)
        print(f"\nOutput written to: {output_file}\n")
    
    print("\n" + "=" * 70)
    print("Done!")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(run_pipeline())

