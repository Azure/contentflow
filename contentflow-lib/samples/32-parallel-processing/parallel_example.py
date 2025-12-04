"""
Parallel Processing Example

Demonstrates parallel execution paths using:
- Multiple parallel branches
- Concurrent execution of independent tasks
- Result merging from parallel paths
"""

import asyncio
import logging
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from samples.setup_logger import setup_logging
from packages.pipeline_executor import PipelineExecutor
from packages.models import Content, ContentIdentifier

# Get the current directory
samples_dir = Path(__file__).parent

# Load environment variables
load_dotenv(f'{samples_dir.parent.parent}/.env')

setup_logging()

logger = logging.getLogger(__name__)


async def parallel_processing_example():
    """Process document through parallel execution paths."""
    
    print("=" * 70)
    print("Parallel Processing Example")
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
    config_path = Path(__file__).parent / "parallel_config.yaml"
    
    async with PipelineExecutor.from_config_file(
        config_path=config_path,
        pipeline_name="parallel_processing"
    ) as executor:
        
        print(f"\n✓ Initialized parallel processing pipeline")
        print(f"  Parallel branches:")
        print(f"    1. extract_metadata")
        print(f"    2. extract_entities")
        print(f"    3. extract_summary")
        print(f"  Merge: All results combined")
        
        # Create document
        document = Content(
            id=ContentIdentifier(
                canonical_id="doc_parallel_001",
                unique_id="doc_parallel_001",
                source_id="local_file",
                source_name="parallel_doc",
                source_type="local_file",
                path=f"{samples_dir.parent.parent}/99-assets/sample.pdf",
            )
        )
        
        print(f"\n✓ Processing document: {document.id}")
        print(f"  Watching parallel execution...")
        
        # Track execution timeline
        timeline = []
        start_time = datetime.now()
        
        async for event in executor.execute_stream(document):
            elapsed = (datetime.now() - start_time).total_seconds()
            
            timeline.append({
                "time": elapsed,
                "executor": event.executor_id,
                "type": event.event_type
            })
            
            # Show parallel execution events
            if event.executor_id in ["extract_metadata", "extract_entities", "extract_summary"]:
                status = "START" if "start" in event.event_type.lower() else "COMPLETE"
                print(f"  [{elapsed:6.2f}s] {event.executor_id:20s} - {status}")
            
            if event.executor_id == "merge_results":
                print(f"  [{elapsed:6.2f}s] {'merge_results':20s} - MERGING")
        
        # Analyze parallel execution
        print(f"\n📊 Execution Analysis:")
        
        # Find parallel execution windows
        parallel_executors = ["extract_metadata", "extract_entities", "extract_summary"]
        parallel_events = [e for e in timeline if e["executor"] in parallel_executors]
        
        if parallel_events:
            first_start = min(e["time"] for e in parallel_events)
            last_complete = max(e["time"] for e in parallel_events)
            
            print(f"  Parallel execution window: {first_start:.2f}s - {last_complete:.2f}s")
            print(f"  Parallel duration: {last_complete - first_start:.2f}s")
            print(f"  Total events: {len(timeline)}")
        
        total_time = timeline[-1]["time"] if timeline else 0
        print(f"  Total pipeline duration: {total_time:.2f}s")
    
    print("\n" + "=" * 70)
    print("Done!")
    print("=" * 70)


async def parallel_vs_sequential_comparison():
    """Compare parallel vs sequential execution."""
    
    print("=" * 70)
    print("Parallel vs Sequential Comparison")
    print("=" * 70)
    
    # Check environment variables
    required_vars = {
        'AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT': os.getenv('AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT'),
    }
    
    missing = [k for k, v in required_vars.items() if not v]
    if missing:
        print(f"\n❌ Missing environment variables: {', '.join(missing)}")
        return
    
    # Create document
    document = Content(
        id=ContentIdentifier(
            canonical_id="doc_compare_001",
            unique_id="doc_compare_001",
            source_id="local_file",
            source_name="compare_doc",
            source_type="local_file",
            path=f"{samples_dir.parent.parent}/99-assets/sample.pdf",
        )
    )
    
    # Test parallel execution
    print(f"\n🔄 Running PARALLEL execution...")
    config_path = Path(__file__).parent / "parallel_config.yaml"
    
    async with PipelineExecutor.from_config_file(
        config_path=config_path,
        pipeline_name="parallel_processing"
    ) as executor:
        
        start = datetime.now()
        result = await executor.execute(document)
        parallel_duration = (datetime.now() - start).total_seconds()
        
        print(f"  ✓ Completed in {parallel_duration:.2f}s")
        print(f"  Status: {result.status}")
        print(f"  Events: {len(result.events)}")
    
    print(f"\n📊 Comparison:")
    print(f"  Parallel execution: {parallel_duration:.2f}s")
    print(f"  Speedup benefit: Processes multiple branches concurrently")
    print(f"  Use case: When branches are independent and can run in parallel")
    
    print("\n" + "=" * 70)
    print("Done!")
    print("=" * 70)


if __name__ == "__main__":
    # Run parallel processing example
    asyncio.run(parallel_processing_example())
    
    print("\n\n")
    
    # Run comparison
    asyncio.run(parallel_vs_sequential_comparison())
