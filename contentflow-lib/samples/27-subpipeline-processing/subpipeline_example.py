"""
Sub-Pipeline Processing Example

Demonstrates nested pipeline execution using:
- SubworkflowExecutor: Execute pipelines within pipelines
- Page-level processing: Process each page independently
- Chunk-level processing: Process document chunks
- Result aggregation: Combine sub-pipeline results
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


async def page_subpipeline_example():
    """Process document pages using a sub-pipeline."""
    
    print("=" * 70)
    print("Page-Level Sub-Pipeline Processing")
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
    config_path = Path(__file__).parent / "subpipeline_config.yaml"
    
    async with PipelineExecutor.from_config_file(
        config_path=config_path,
        pipeline_name="main_pipeline"
    ) as executor:
        
        print(f"\n✓ Initialized main pipeline with page sub-pipeline")
        print(f"  Main: get_content → extract → process_pages → aggregate")
        print(f"  Sub:  analyze_page → extract_page_metadata")
        
        # Create document
        document = Content(
            id=ContentIdentifier(
                canonical_id="doc_pages_001",
                unique_id="doc_pages_001",
                source_id="local_file",
                source_name="multi_page_doc",
                source_type="local_file",
                path=f"{samples_dir.parent.parent}/99-assets/sample.pdf",
            )
        )
        
        print(f"\n✓ Processing document: {document.id}")
        print(f"  Each page will be processed by the sub-pipeline")
        
        # Track sub-pipeline executions
        subpipeline_count = 0
        main_pipeline_events = []
        sub_pipeline_events = []
        
        async for event in executor.execute_stream(document):
            # Categorize events
            if event.executor_id == "process_pages":
                main_pipeline_events.append(event)
                if "subworkflow" in event.event_type.lower():
                    subpipeline_count += 1
                    print(f"  → Sub-pipeline execution #{subpipeline_count}")
            elif event.executor_id in ["analyze_page", "extract_page_metadata"]:
                sub_pipeline_events.append(event)
                print(f"    ├─ {event.executor_id}: {event.event_type}")
        
        print(f"\n📊 Sub-Pipeline Statistics:")
        print(f"  Total sub-pipeline executions: {subpipeline_count}")
        print(f"  Main pipeline events: {len(main_pipeline_events)}")
        print(f"  Sub-pipeline events: {len(sub_pipeline_events)}")
        
        # Show event breakdown
        if sub_pipeline_events:
            event_types = {}
            for event in sub_pipeline_events:
                key = event.executor_id
                event_types[key] = event_types.get(key, 0) + 1
            
            print(f"\n  Sub-pipeline executor calls:")
            for executor_id, count in event_types.items():
                print(f"    {executor_id}: {count}")
    
    print("\n" + "=" * 70)
    print("Done!")
    print("=" * 70)


async def chunk_subpipeline_example():
    """Process document chunks using a sub-pipeline."""
    
    print("=" * 70)
    print("Chunk-Level Sub-Pipeline Processing")
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
    config_path = Path(__file__).parent / "subpipeline_config.yaml"
    
    async with PipelineExecutor.from_config_file(
        config_path=config_path,
        pipeline_name="chunk_pipeline"
    ) as executor:
        
        print(f"\n✓ Initialized chunk processing pipeline")
        print(f"  Main: get_content → extract → process_chunks → aggregate")
        print(f"  Sub:  analyze_chunk → extract_entities")
        print(f"  Chunk size: 1000 characters")
        
        # Create document
        document = Content(
            id=ContentIdentifier(
                canonical_id="doc_chunks_001",
                unique_id="doc_chunks_001",
                source_id="local_file",
                source_name="chunked_doc",
                source_type="local_file",
                path=f"{samples_dir.parent.parent}/99-assets/sample.pdf",
            )
        )
        
        print(f"\n✓ Processing document: {document.id}")
        print(f"  Document will be split into chunks")
        
        result = await executor.execute(document)
        
        print(f"\n✓ Chunk processing completed")
        print(f"  Status: {result.status}")
        print(f"  Duration: {result.duration_seconds:.2f}s")
        print(f"  Total events: {len(result.events)}")
        
        # Analyze chunk processing
        chunk_events = [e for e in result.events if "chunk" in e.executor_id.lower()]
        print(f"  Chunk-related events: {len(chunk_events)}")
    
    print("\n" + "=" * 70)
    print("Done!")
    print("=" * 70)


async def nested_hierarchy_example():
    """Demonstrate multi-level nested pipelines."""
    
    print("=" * 70)
    print("Nested Hierarchy Example")
    print("=" * 70)
    
    print(f"\n📊 Pipeline Hierarchy:")
    print(f"  Level 1 (Main): Document processing")
    print(f"  Level 2 (Sub):  Page/Chunk processing")
    print(f"  Level 3 (Deep): Individual element processing (if configured)")
    
    print(f"\n💡 Use Cases:")
    print(f"  • Complex document structures (books, reports)")
    print(f"  • Multi-stage processing with different granularities")
    print(f"  • Recursive processing patterns")
    print(f"  • Hierarchical result aggregation")
    
    print(f"\n✓ Benefits:")
    print(f"  • Modular, reusable sub-pipelines")
    print(f"  • Clear separation of concerns")
    print(f"  • Easier testing and maintenance")
    print(f"  • Flexible composition")
    
    print("\n" + "=" * 70)
    print("Done!")
    print("=" * 70)


if __name__ == "__main__":
    # Run page-level sub-pipeline example
    asyncio.run(page_subpipeline_example())
    
    print("\n\n")
    
    # Run chunk-level sub-pipeline example
    asyncio.run(chunk_subpipeline_example())
    
    print("\n\n")
    
    # Show nested hierarchy concepts
    asyncio.run(nested_hierarchy_example())
