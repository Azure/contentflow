"""
Test script for subworkflow functionality in PipelineFactory.

This script demonstrates:
1. Loading a configuration with subworkflows
2. Creating a pipeline that uses subworkflows
3. Verifying that subworkflows are properly wrapped in WorkflowExecutor
"""

import asyncio
import logging
import sys
from pathlib import Path

from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from samples.setup_logger import setup_logging
from contentflow.pipeline import PipelineExecutor
from contentflow.models import Content, ContentIdentifier

# Get the current directory
samples_dir = Path(__file__).parent.parent

# Load environment variables
load_dotenv(f'{samples_dir}/.env')

logger = logging.getLogger(__name__)

setup_logging()

async def test_nested_subpipeline():
    """Test simple subpipeline example."""
    print("=" * 70)
    print("TEST 1: Simple Subpipeline Example")
    print("=" * 70)
    
    config_path = Path(__file__).parent / "nested_subpipelines.yaml"
    executor_catalog_path = samples_dir.parent / "executor_catalog.yaml"
    
    async with PipelineExecutor.from_config_file(
        config_path=config_path,
        pipeline_name="batch_nested_processing",
        executor_catalog_path=executor_catalog_path,
    ) as pipeline_executor:
        
        print(f"\n✓ Initialized pipeline")
        
        documents = []
        
        # load documents from local path
        local_path = Path(f'{samples_dir}/99-assets')
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
        
        print(f"\n✓ Created {len(documents)} documents for PDF extraction and chunking")
        
        # Process all documents
        result = await pipeline_executor.execute(documents) # process all documents
    
        # write results to output folder
        output_folder = Path(__file__).parent / "output"
        output_folder.mkdir(exist_ok=True)
        output_file = output_folder / "nested_subpipeline_result.json"
        with open(output_file, 'w', encoding='utf-8') as f:
                f.write(result.model_dump_json(indent=2))
        print(f"  Wrote output to {output_file}")
    
        # Analyze results
        successful = sum(1 for d in result.content if d.get_status() == "completed") if isinstance(result.content, list) else result.content.get_status() == "completed"
        failed = sum(1 for d in result.content if d.get_status() == "failed") if isinstance(result.content, list) else result.content.get_status() == "failed"
        total_duration = result.duration_seconds
        
        print(f"\n✓ Processed {len(documents)} documents:")
        print(f"  Successful: {successful}")
        print(f"  Failed: {failed}")
        print(f"  Total Duration: {total_duration:.2f} seconds")
        
        # Show processing events
        print(f"\n📊 Processing Events:")
        for i, event in enumerate(result.events):
            print(f"\n  Event {i+1}: {event.event_type}")
            print(f"    Executor: {event.executor_id}")
    
        print(f"\n✓ Pipeline execution completed with status: {result.status}")
        
async def main():
    """Run all tests."""
    print("\n" + "=" * 70)
    print("SUB PIPELINE FUNCTIONALITY TEST SUITE")
    print("=" * 70 + "\n")
       
    # Run tests
    await test_nested_subpipeline()
    
    print("=" * 70 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
    
