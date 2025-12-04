"""
Concurrent Processing Example

Demonstrates parallel processing of document sections using:
- ParallelExecutor: Process multiple sections concurrently
- Configurable worker pools
- Timeout management
"""

import asyncio
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
samples_dir = Path(__file__).parent

# Load environment variables
load_dotenv(f'{samples_dir.parent.parent}/.env')

setup_logging()

logger = logging.getLogger(__name__)


async def concurrent_processing_example():
    """Process document sections concurrently."""
    
    print("=" * 70)
    print("Concurrent Processing Example")
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
    config_path = Path(__file__).parent / "concurrent_config.yaml"
    
    async with PipelineExecutor.from_config_file(
        config_path=config_path,
        pipeline_name="concurrent_processing"
    ) as executor:
        
        print(f"\n✓ Initialized concurrent processing pipeline")
        print(f"  Max workers: 4")
        print(f"  Timeout: 30s per task")
        
        # Create document
        document = Content(
            id=ContentIdentifier(
                canonical_id="doc_concurrent_001",
                unique_id="doc_concurrent_001",
                source_id="local_file_source",
                source_name="local_file",
                source_type="local_file",
                path=f"{samples_dir.parent.parent}/99-assets/sample.pdf",
            )
        )
        
        print(f"\n✓ Processing document: {document.id}")
        print(f"  Document will be split into sections for concurrent processing")
        
        # Execute with streaming to see concurrent events
        print(f"\n📊 Processing Events (real-time):")
        
        event_count = 0
        executor_events = {}
        
        async for event in executor.execute_stream(document):
            event_count += 1
            
            # Track events by executor
            executor_id = event.executor_id or "unknown"
            if executor_id not in executor_events:
                executor_events[executor_id] = []
            executor_events[executor_id].append(event)
            
            # Show parallel execution events
            if event.event_type in ["parallel_start", "parallel_complete", "parallel_error"]:
                print(f"\n  [{event.event_type}]")
                print(f"    Executor: {event.executor_id}")
                print(f"    Timestamp: {event.timestamp.strftime('%H:%M:%S.%f')[:-3]}")
                if event.data:
                    print(f"    Data: {event.data}")
        
        print(f"\n✓ Concurrent processing completed")
        print(f"  Total events: {event_count}")
        print(f"\n  Events by executor:")
        for executor_id, events in executor_events.items():
            print(f"    {executor_id}: {len(events)} events")
    
    print("\n" + "=" * 70)
    print("Done!")
    print("=" * 70)


async def concurrent_multiple_documents():
    """Process multiple documents with concurrent sections."""
    
    print("=" * 70)
    print("Concurrent Processing - Multiple Documents")
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
    config_path = Path(__file__).parent / "concurrent_config.yaml"
    
    async with PipelineExecutor.from_config_file(
        config_path=config_path,
        pipeline_name="concurrent_processing"
    ) as executor:
        
        print(f"\n✓ Initialized concurrent processing pipeline")
        
        # Create multiple documents
        documents = [
            Content(
                id=ContentIdentifier(
                    canonical_id=f"doc_concurrent_{i:03d}",
                    unique_id=f"doc_concurrent_{i:03d}",
                    source_id="local_batch",
                    source_name="batch_docs",
                    source_type="local_file",
                    path=f"{samples_dir.parent.parent}/99-assets/sample.pdf",
                )
            )
            for i in range(1, 6)  # 5 documents
        ]
        
        print(f"\n✓ Processing {len(documents)} documents concurrently")
        
        # Process all documents
        results = await executor.execute_batch(documents)
        
        # Analyze results
        successful = sum(1 for r in results if r.status.value == "completed")
        failed = sum(1 for r in results if r.status.value == "failed")
        total_duration = sum(r.duration_seconds for r in results)
        
        print(f"\n✓ Concurrent batch processing completed")
        print(f"  Total documents: {len(results)}")
        print(f"  Successful: {successful}")
        print(f"  Failed: {failed}")
        print(f"  Total duration: {total_duration:.2f}s")
        print(f"  Avg per document: {total_duration/len(results):.2f}s")
    
    print("\n" + "=" * 70)
    print("Done!")
    print("=" * 70)


if __name__ == "__main__":
    # Run single document with concurrent section processing
    asyncio.run(concurrent_processing_example())
    
    print("\n\n")
    
    # Run multiple documents with concurrent processing
    asyncio.run(concurrent_multiple_documents())
