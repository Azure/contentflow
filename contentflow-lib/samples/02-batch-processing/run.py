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
from contentflow.pipeline import PipelineExecutor, PipelineResult
from contentflow.models import Content, ContentIdentifier

# Get the current directory
samples_dir = Path(__file__).parent.parent

# Load environment variables
load_dotenv(f'{samples_dir}/.env')

setup_logging()

logger = logging.getLogger(__name__)


async def batch_processing_example():
    """Process multiple documents in batches."""
    
    print("=" * 70)
    print("Batch Processing Example")
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
    config_path = Path(__file__).parent / "batch_config.yaml"
    executor_catalog_path = samples_dir.parent / "executor_catalog.yaml"
    
    async with PipelineExecutor.from_config_file(
        config_path=config_path,
        pipeline_name="batch_processing",
        executor_catalog_path=executor_catalog_path,
    ) as pipeline_executor:
        
        print(f"\n✓ Initialized batch processing pipeline")
        
        # Create multiple documents to process
        documents = [
            Content(
                id=ContentIdentifier(
                    canonical_id=f"doc_{i:03d}",
                    unique_id=f"doc_{i:03d}",
                    source_name="local_file",
                    source_type="local_file",
                    path=f"{samples_dir}/99-assets/sample.pdf",
                )
            )
            for i in range(1, 11)  # 10 documents
        ]
        
        print(f"\n✓ Created {len(documents)} documents for batch processing")
        
        # Process all documents using batch executor
        result = await pipeline_executor.execute(documents)
        
        # write results to output folder
        output_folder = Path(__file__).parent / "output"
        output_folder.mkdir(exist_ok=True)
        output_file = output_folder / "batch_processing_result.json"
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

        print("\n\n" + "=" * 70)
        print(f'\nWrote pipeline result to {output_file}\n')
        
        
    print("\n" + "=" * 70)
    print("Done!")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(batch_processing_example())
