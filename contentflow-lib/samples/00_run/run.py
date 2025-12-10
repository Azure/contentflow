"""
Batch Processing Example

Demonstrates processing multiple documents efficiently using:
- BatchSplitterExecutor: Split documents into batches
- BatchAggregatorExecutor: Merge results from batches
- Efficient processing of large document sets
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
    
    # Check environment variables
    required_vars = {
        'AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT': os.getenv('AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT'),
    }
    
    missing = [k for k, v in required_vars.items() if not v]
    if missing:
        print(f"\n❌ Missing environment variables: {', '.join(missing)}")
        return
    
    # Load config
    config_path = Path(__file__).parent / "pipeline_config.yaml"
    executor_catalog_path = samples_dir.parent / "executor_catalog.yaml"
    
    async with PipelineExecutor.from_config_file(
        config_path=config_path,
        pipeline_name="pipeline1",
        executor_catalog_path=executor_catalog_path,
    ) as pipeline:
        
        print(f"\n✓ Initialized pipeline")
        
        documents = []
        
        # load documents from  local path
        local_path = Path('/Users/nadeemis/temp/test_files')
        for file in local_path.glob('*.pdf'):
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
        
        print(f"\n✓ Created {len(documents)} documents for batch processing")
        
        # Process all documents using batch executor
        result = await pipeline.execute(documents[0:4])  # limit to first 2 for testing
        
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
        
        print(f"\n✓ Batch processing completed")
        print(f"  Total documents: {len(result.documents) if isinstance(result.documents, list) else 1}")
        print(f"  Successful: {successful}")
        print(f"  Failed: {failed}")
        print(f"  Total duration (seconds): {total_duration:.2f}s")
        print(f"  Avg per document: {total_duration/(len(result.documents) if isinstance(result.documents, list) else 1):.2f}s")
        
        # Show batch event details
        print(f"\n📊 Processing Events:")
        for i, event in enumerate(result.events):  # Show first 3
            print(f"\n  Event {i}: {event.event_type}")
            print(f"    Executor: {event.executor_id}")
    
    print("\n" + "=" * 70)
    print("Done!")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(run_pipeline())
