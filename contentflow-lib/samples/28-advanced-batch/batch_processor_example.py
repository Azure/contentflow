"""
Advanced Batch Processor Example

Demonstrates comprehensive batch processing capabilities:
- BatchProcessor: Generic batch processing with retries
- FilterProcessor: Pre/post-processing filtering
- ParallelDocumentProcessor: Concurrent document processing
- Real-world scenarios and performance optimization
"""

import asyncio
import logging
import os
import sys
import random
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from samples.setup_logger import setup_logging
from contentflow.pipeline import PipelineExecutor
from contentflow.models import Content, ContentIdentifier

# Get the current directory
samples_dir = Path(__file__).parent

# Load environment variables
load_dotenv(f'{samples_dir.parent.parent}/.env')

setup_logging()

logger = logging.getLogger(__name__)


def generate_sample_records(count: int = 100):
    """Generate sample records for batch processing."""
    statuses = ["active", "pending", "inactive", "processing"]
    priorities = ["high", "medium", "low"]
    
    records = []
    for i in range(count):
        records.append({
            "id": f"record_{i:04d}",
            "status": random.choice(statuses),
            "priority": random.choice(priorities),
            "value": random.randint(1, 1000),
            "timestamp": datetime.now().isoformat(),
            "data": f"Sample data for record {i}"
        })
    
    return records


async def basic_batch_processing():
    """Demonstrate basic batch processing."""
    
    print("=" * 70)
    print("Basic Batch Processing")
    print("=" * 70)
    
    config_path = Path(__file__).parent / "batch_processor_config.yaml"
    
    async with PipelineExecutor.from_config_file(
        config_path=config_path,
        pipeline_name="basic_batch"
    ) as executor:
        
        print(f"\n✓ Initialized basic batch processing pipeline")
        print(f"  Settings:")
        print(f"    - Batch size: 10 items")
        print(f"    - Concurrency: 1 (sequential)")
        print(f"    - Retries: Disabled")
        
        # Create document with sample records
        records = generate_sample_records(50)
        
        document = Content(
            id=ContentIdentifier(
                canonical_id="batch_001",
                unique_id="batch_001",
                source_id="sample_data",
                source_name="records",
                source_type="generated",
                path="memory://records",
            ),
            data={"records": records}
        )
        
        print(f"\n✓ Created document with {len(records)} records")
        print(f"  Record sample:")
        print(f"    {records[0]}")
        
        # Execute pipeline
        start_time = datetime.now()
        result = await executor.execute(document)
        duration = (datetime.now() - start_time).total_seconds()
        
        print(f"\n✓ Batch processing completed")
        print(f"  Status: {result.status}")
        print(f"  Duration: {duration:.2f}s")
        
        if result.document:
            summary = result.document.summary_data
            print(f"\n📊 Processing Summary:")
            print(f"  Total items: {summary.get('items_processed', 0)}")
            print(f"  Batches processed: {summary.get('batches_processed', 0)}")
            print(f"  Processing time: {summary.get('processing_time_secs', 0):.2f}s")
            
            # Show batch breakdown
            batch_size = 10
            num_batches = (len(records) + batch_size - 1) // batch_size
            print(f"  Batch breakdown:")
            for i in range(num_batches):
                batch_items = min(batch_size, len(records) - i * batch_size)
                print(f"    Batch {i+1}: {batch_items} items")
    
    print("\n" + "=" * 70)


async def parallel_batch_processing():
    """Demonstrate parallel batch processing with filtering."""
    
    print("=" * 70)
    print("Parallel Batch Processing with Filtering")
    print("=" * 70)
    
    config_path = Path(__file__).parent / "batch_processor_config.yaml"
    
    async with PipelineExecutor.from_config_file(
        config_path=config_path,
        pipeline_name="parallel_batch"
    ) as executor:
        
        print(f"\n✓ Initialized parallel batch processing pipeline")
        print(f"  Pipeline stages:")
        print(f"    1. Load data")
        print(f"    2. Filter (status=active, remove duplicates)")
        print(f"    3. Batch process (25 items, 4 concurrent, retry enabled)")
        
        # Create document with sample records
        records = generate_sample_records(200)
        
        # Add some duplicates
        records.extend(records[:20])
        random.shuffle(records)
        
        document = Content(
            id=ContentIdentifier(
                canonical_id="parallel_batch_001",
                unique_id="parallel_batch_001",
                source_id="sample_data",
                source_name="records",
                source_type="generated",
                path="memory://records",
            ),
            data={"records": records}
        )
        
        print(f"\n✓ Created document with {len(records)} records (including duplicates)")
        
        # Count by status
        status_counts = {}
        for r in records:
            status = r['status']
            status_counts[status] = status_counts.get(status, 0) + 1
        
        print(f"  Status distribution:")
        for status, count in sorted(status_counts.items()):
            print(f"    {status}: {count}")
        
        # Execute with streaming to see filtering and batching
        print(f"\n🔄 Processing events:")
        
        events_by_executor = {}
        async for event in executor.execute_stream(document):
            executor_id = event.executor_id or "unknown"
            if executor_id not in events_by_executor:
                events_by_executor[executor_id] = []
            events_by_executor[executor_id].append(event)
            
            # Show key events
            if "filter" in executor_id.lower():
                if "complete" in event.event_type.lower():
                    print(f"  ✓ Filtering completed")
                    if event.data:
                        filtered = event.data.get('filtered_count', 0)
                        print(f"    Filtered to: {filtered} items")
            
            elif "batch" in executor_id.lower():
                if "batch" in event.event_type.lower():
                    batch_num = event.data.get('batch_number', '?')
                    print(f"  → Processing batch {batch_num}")
        
        print(f"\n📊 Event Summary:")
        for executor_id, events in events_by_executor.items():
            print(f"  {executor_id}: {len(events)} events")
    
    print("\n" + "=" * 70)


async def parallel_document_processing():
    """Demonstrate parallel document processing."""
    
    print("=" * 70)
    print("Parallel Document Processing")
    print("=" * 70)
    
    config_path = Path(__file__).parent / "batch_processor_config.yaml"
    
    async with PipelineExecutor.from_config_file(
        config_path=config_path,
        pipeline_name="parallel_documents"
    ) as executor:
        
        print(f"\n✓ Initialized parallel document processor")
        print(f"  Settings:")
        print(f"    - Max concurrent: 10 documents")
        print(f"    - Timeout: 60s per document")
        print(f"    - Continue on error: Yes")
        
        # Create multiple documents
        documents = []
        for i in range(50):
            doc_data = {
                "id": f"doc_{i:03d}",
                "content": f"Content for document {i}",
                "metadata": {
                    "index": i,
                    "type": random.choice(["pdf", "docx", "txt"]),
                    "size": random.randint(100, 10000)
                }
            }
            documents.append(doc_data)
        
        # Create container document
        document = Content(
            id=ContentIdentifier(
                canonical_id="parallel_docs_001",
                unique_id="parallel_docs_001",
                source_id="sample_data",
                source_name="document_batch",
                source_type="generated",
                path="memory://documents",
            ),
            data={"documents": documents}
        )
        
        print(f"\n✓ Created batch of {len(documents)} documents")
        
        # Execute pipeline
        start_time = datetime.now()
        result = await executor.execute(document)
        duration = (datetime.now() - start_time).total_seconds()
        
        print(f"\n✓ Parallel processing completed")
        print(f"  Status: {result.status}")
        print(f"  Duration: {duration:.2f}s")
        
        if result.document:
            summary = result.document.summary_data
            total = summary.get('total_documents', 0)
            successful = summary.get('successful_count', 0)
            failed = summary.get('failed_count', 0)
            success_rate = summary.get('success_rate', 0)
            
            print(f"\n📊 Processing Summary:")
            print(f"  Total documents: {total}")
            print(f"  Successful: {successful}")
            print(f"  Failed: {failed}")
            print(f"  Success rate: {success_rate*100:.1f}%")
            print(f"  Avg time per doc: {duration/total:.2f}s")
            
            # Calculate speedup
            sequential_estimate = total * 0.1  # Assume 0.1s per doc
            speedup = sequential_estimate / duration if duration > 0 else 0
            print(f"\n  Parallel speedup: ~{speedup:.1f}x")
            print(f"  (Estimated sequential: {sequential_estimate:.2f}s)")
    
    print("\n" + "=" * 70)


async def complete_pipeline_example():
    """Demonstrate complete multi-stage batch processing pipeline."""
    
    print("=" * 70)
    print("Complete Multi-Stage Batch Processing Pipeline")
    print("=" * 70)
    
    config_path = Path(__file__).parent / "batch_processor_config.yaml"
    
    async with PipelineExecutor.from_config_file(
        config_path=config_path,
        pipeline_name="complete_pipeline"
    ) as executor:
        
        print(f"\n✓ Initialized complete processing pipeline")
        print(f"  Pipeline stages:")
        print(f"    1. Load data")
        print(f"    2. Filter pending records")
        print(f"    3. Batch process (20 items, 3 concurrent, retry)")
        print(f"    4. Filter successful results")
        
        # Create document with diverse records
        records = generate_sample_records(150)
        
        document = Content(
            id=ContentIdentifier(
                canonical_id="complete_001",
                unique_id="complete_001",
                source_id="sample_data",
                source_name="records",
                source_type="generated",
                path="memory://records",
            ),
            data={"records": records}
        )
        
        print(f"\n✓ Created document with {len(records)} records")
        
        # Show initial distribution
        status_counts = {}
        for r in records:
            status = r['status']
            status_counts[status] = status_counts.get(status, 0) + 1
        
        print(f"  Initial status distribution:")
        for status, count in sorted(status_counts.items()):
            print(f"    {status}: {count}")
        
        # Execute with detailed tracking
        print(f"\n🔄 Processing pipeline:")
        
        stage_results = {}
        async for event in executor.execute_stream(document):
            executor_id = event.executor_id or "unknown"
            
            # Track stage completions
            if "complete" in event.event_type.lower():
                stage_results[executor_id] = event.data
                
                if "filter" in executor_id.lower():
                    filtered = event.data.get('filtered_count', 0)
                    removed = event.data.get('removed_count', 0)
                    print(f"  ✓ {executor_id}: {filtered} items (removed {removed})")
                
                elif "batch" in executor_id.lower():
                    processed = event.data.get('processed_count', 0)
                    batches = event.data.get('batches_processed', 0)
                    print(f"  ✓ {executor_id}: {processed} items in {batches} batches")
        
        print(f"\n📊 Pipeline Summary:")
        print(f"  Stages completed: {len(stage_results)}")
        
        # Show data flow through pipeline
        if stage_results:
            print(f"\n  Data flow:")
            print(f"    Input: {len(records)} records")
            
            for executor_id, data in stage_results.items():
                if "filter_active" in executor_id:
                    print(f"    After filter 1: {data.get('filtered_count', 0)} records")
                elif "batch_process" in executor_id:
                    print(f"    After batch: {data.get('processed_count', 0)} records")
                elif "filter_successful" in executor_id:
                    print(f"    Final output: {data.get('filtered_count', 0)} records")
    
    print("\n" + "=" * 70)


async def performance_comparison():
    """Compare different batch processing strategies."""
    
    print("=" * 70)
    print("Performance Comparison: Sequential vs Parallel")
    print("=" * 70)
    
    records = generate_sample_records(100)
    
    document = Content(
        id=ContentIdentifier(
            canonical_id="perf_test_001",
            unique_id="perf_test_001",
            source_id="sample_data",
            source_name="records",
            source_type="generated",
            path="memory://records",
        ),
        data={"records": records}
    )
    
    config_path = Path(__file__).parent / "batch_processor_config.yaml"
    
    # Test sequential
    print(f"\n🔄 Testing sequential processing...")
    async with PipelineExecutor.from_config_file(
        config_path=config_path,
        pipeline_name="basic_batch"
    ) as executor:
        start = datetime.now()
        await executor.execute(document)
        sequential_time = (datetime.now() - start).total_seconds()
    
    print(f"  ✓ Sequential: {sequential_time:.2f}s")
    
    # Test parallel
    print(f"\n🔄 Testing parallel processing...")
    async with PipelineExecutor.from_config_file(
        config_path=config_path,
        pipeline_name="parallel_batch"
    ) as executor:
        start = datetime.now()
        await executor.execute(document)
        parallel_time = (datetime.now() - start).total_seconds()
    
    print(f"  ✓ Parallel: {parallel_time:.2f}s")
    
    # Compare
    speedup = sequential_time / parallel_time if parallel_time > 0 else 0
    improvement = ((sequential_time - parallel_time) / sequential_time * 100) if sequential_time > 0 else 0
    
    print(f"\n📊 Performance Analysis:")
    print(f"  Sequential time: {sequential_time:.2f}s")
    print(f"  Parallel time: {parallel_time:.2f}s")
    print(f"  Speedup: {speedup:.2f}x")
    print(f"  Improvement: {improvement:.1f}%")
    
    print(f"\n💡 Recommendations:")
    if speedup > 1.5:
        print(f"  ✓ Parallel processing provides significant benefit")
        print(f"  → Use parallel batch processing for this workload")
    elif speedup > 1.1:
        print(f"  ≈ Moderate benefit from parallel processing")
        print(f"  → Consider parallel for larger batches")
    else:
        print(f"  ⚠ Sequential may be sufficient")
        print(f"  → Overhead may outweigh benefits for small batches")
    
    print("\n" + "=" * 70)


if __name__ == "__main__":
    print("\n" + "🚀 Advanced Batch Processor Examples" + "\n")
    
    # Run all examples
    asyncio.run(basic_batch_processing())
    print("\n\n")
    
    asyncio.run(parallel_batch_processing())
    print("\n\n")
    
    asyncio.run(parallel_document_processing())
    print("\n\n")
    
    asyncio.run(complete_pipeline_example())
    print("\n\n")
    
    asyncio.run(performance_comparison())
    
    print("\n" + "✅ All examples completed!" + "\n")
