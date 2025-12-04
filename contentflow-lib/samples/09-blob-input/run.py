"""
Azure Blob Input Executor Example

This example demonstrates how to use the AzureBlobInputExecutor to discover
and list content files from Azure Blob Storage containers.

Features demonstrated:
1. Basic blob discovery - listing all files in a container
2. Advanced filtering - by prefix, extensions, size, dates
3. Full pipeline - discover → retrieve → extract
4. Streaming execution with event monitoring
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
from packages.models import Content

# Get the current directory
samples_dir = Path(__file__).parent.parent

# Load environment variables
load_dotenv(f'{samples_dir}/.env')

setup_logging()

logger = logging.getLogger(__name__)


async def basic_blob_discovery():
    """Basic example: Discover all files in a blob container."""
    
    print("=" * 80)
    print("Azure Blob Input - Basic Discovery")
    print("=" * 80)
    
    # Check required environment variables
    required_vars = {
        'AZURE_STORAGE_ACCOUNT_NAME': os.getenv('AZURE_STORAGE_ACCOUNT_NAME'),
    }
    
    missing = [k for k, v in required_vars.items() if not v]
    if missing:
        print(f"\n❌ Missing environment variables: {', '.join(missing)}")
        print("\nQuick setup:")
        print("export AZURE_STORAGE_ACCOUNT_NAME=mystorageaccount")
        return
    
    print(f"\n✓ Environment configured")
    print(f"  Storage Account: {required_vars['AZURE_STORAGE_ACCOUNT_NAME']}")
    
    # Load config and create executor
    config_path = Path(__file__).parent / "blob_input_config.yaml"
    executor_catalog_path = Path(__file__).parent.parent.parent / "executor_catalog.yaml"
    
    async with PipelineExecutor.from_config_file(
        config_path=config_path,
        pipeline_name="blob_discovery_basic",
        executor_catalog_path=executor_catalog_path
    ) as pipeline_executor:
        
        print(f"\n✓ Pipeline loaded")
        
        # Execute pipeline (no input needed for blob discovery)
        result = await pipeline_executor.execute([])
        
        print(f"\n✓ Discovery completed")
        print(f"  Status: {result.status}")
        print(f"  Duration: {result.duration_seconds:.2f}s")
        
        # Write results to output folder
        output_folder = Path(__file__).parent / "output"
        output_folder.mkdir(exist_ok=True)
        output_file = output_folder / "blob_discovery_basic_result.json"
        with open(output_file, 'w', encoding='utf-8') as f:
                f.write(result.model_dump_json(indent=2))
        print(f"  Wrote output to {output_file}")
        
        if result.documents:
            blobs = result.documents if isinstance(result.documents, list) else [result.documents]
            print(f"\n📁 Discovered {len(blobs)} files:")
            
            for i, blob in enumerate(blobs[:10], 1):  # Show first 10
                print(f"\n  {i}. {blob.data.get('blob_name', 'N/A')}")
                print(f"     Size: {blob.data.get('size', 0):,} bytes")
                print(f"     Modified: {blob.data.get('last_modified', 'N/A')}")
                print(f"     Type: {blob.data.get('content_type', 'N/A')}")
            
            if len(blobs) > 10:
                print(f"\n  ... and {len(blobs) - 10} more files")
        
        if result.error:
            print(f"\n❌ Error: {result.error}")

        # Show processing events
        print(f"\n📊 Processing Events:")
        for i, event in enumerate(result.events):
            print(f"\n  Event {i+1}: {event.event_type}")
            print(f"    Executor: {event.executor_id}")
    
        print("\n" + "=" * 70)
        print(f"\nOutput written to: {output_file}\n")
        
    print("\n" + "=" * 80)


async def filtered_blob_discovery():
    """Advanced example: Discover files with filters."""
    
    print("=" * 80)
    print("Azure Blob Input - Filtered Discovery")
    print("=" * 80)
    
    # Check required environment variables
    required_vars = {
        'AZURE_STORAGE_ACCOUNT_NAME': os.getenv('AZURE_STORAGE_ACCOUNT_NAME'),
    }
    
    missing = [k for k, v in required_vars.items() if not v]
    if missing:
        print(f"\n❌ Missing environment variables: {', '.join(missing)}")
        return
    
    print(f"\n✓ Environment configured")
    print(f"  Storage Account: {required_vars['AZURE_STORAGE_ACCOUNT_NAME']}")
    print(f"  Filters: prefix='documents/', extensions=[.pdf, .docx]")
    
    # Load config and create executor
    config_path = Path(__file__).parent / "blob_input_config.yaml"
    executor_catalog_path = Path(__file__).parent.parent.parent / "executor_catalog.yaml"
    
    async with PipelineExecutor.from_config_file(
        config_path=config_path,
        pipeline_name="blob_discovery_filtered",
        executor_catalog_path=executor_catalog_path
    ) as executor:
        
        print(f"\n✓ Pipeline loaded with filters")
        
        # Execute pipeline
        result = await executor.execute([])
        
        print(f"\n✓ Discovery completed")
        print(f"  Status: {result.status}")
        print(f"  Duration: {result.duration_seconds:.2f}s")
        
        # Write results to output folder
        output_folder = Path(__file__).parent / "output"
        output_folder.mkdir(exist_ok=True)
        output_file = output_folder / "blob_discovery_filtered_result.json"
        with open(output_file, 'w', encoding='utf-8') as f:
                f.write(result.model_dump_json(indent=2))
        print(f"  Wrote output to {output_file}")
        
        if result.documents:
            blobs = result.documents if isinstance(result.documents, list) else [result.documents]
            print(f"\n📁 Discovered {len(blobs)} matching files:")
            
            # Show statistics
            total_size = sum(blob.data.get('size', 0) for blob in blobs)
            pdf_count = sum(1 for blob in blobs if blob.data.get('blob_name', '').endswith('.pdf'))
            docx_count = sum(1 for blob in blobs if blob.data.get('blob_name', '').endswith('.docx'))
            
            print(f"\n  Statistics:")
            print(f"    PDF files: {pdf_count}")
            print(f"    DOCX files: {docx_count}")
            print(f"    Total size: {total_size:,} bytes ({total_size / 1024 / 1024:.2f} MB)")
            
            print(f"\n  Recent files (sorted by last modified):")
            for i, blob in enumerate(blobs[:5], 1):
                print(f"    {i}. {blob.data.get('blob_name', 'N/A')}")
                print(f"       {blob.data.get('size', 0):,} bytes | {blob.data.get('last_modified', 'N/A')}")
        else:
            print(f"\n📁 No files matched the filters.")
        
        if result.error:
            print(f"\n❌ Error: {result.error}")
            
        # Show processing events
        print(f"\n📊 Processing Events:")
        for i, event in enumerate(result.events):
            print(f"\n  Event {i+1}: {event.event_type}")
            print(f"    Executor: {event.executor_id}")
    
        print("\n" + "=" * 70)
        print(f"\nOutput written to: {output_file}\n")
    
    print("\n" + "=" * 80)


async def blob_discovery_with_streaming():
    """Example with streaming to monitor progress."""
    
    print("=" * 80)
    print("Azure Blob Input - Discovery with Event Streaming")
    print("=" * 80)
    
    # Check required environment variables
    required_vars = {
        'AZURE_STORAGE_ACCOUNT_NAME': os.getenv('AZURE_STORAGE_ACCOUNT_NAME'),
    }
    
    missing = [k for k, v in required_vars.items() if not v]
    if missing:
        print(f"\n❌ Missing environment variables: {', '.join(missing)}")
        return
    
    print(f"\n✓ Environment configured")
    
    # Load config and create executor
    config_path = Path(__file__).parent / "blob_input_config.yaml"
    executor_catalog_path = Path(__file__).parent.parent.parent / "executor_catalog.yaml"
    
    async with PipelineExecutor.from_config_file(
        config_path=config_path,
        pipeline_name="blob_discovery_filtered",
        executor_catalog_path=executor_catalog_path
    ) as executor:
        
        print(f"\n✓ Pipeline loaded")
        print(f"\n📡 Streaming events...\n")
        
        # Execute with streaming
        discovered_blobs = []
        async for event in executor.execute_stream([]):
            if event.event_type == "ExecutorInvokedEvent":
                print(f"  ▶ Executor '{event.executor_id}' started")
            elif event.event_type == "ExecutorCompletedEvent":
                print(f"  ✓ Executor '{event.executor_id}' completed")
            elif event.event_type == "WorkflowOutputEvent":
                print(f"  📤 Output received")
                output_folder = Path(__file__).parent / "output"
                output_folder.mkdir(exist_ok=True)
                output_file = output_folder / "blob_discovery_streaming_result.json"
                with open(output_file, 'w', encoding='utf-8') as f:
                        f.write(event.model_dump_json(indent=2))
                print(f"  Wrote output to {output_file}")
                
                if event.data:
                    discovered_blobs = event.data if isinstance(event.data, list) else [event.data]
        
        print(f"\n✓ Discovery completed")
        print(f"  Discovered {len(discovered_blobs)} files")
    
    print("\n" + "=" * 80)


async def full_pipeline_example():
    """Full pipeline: Discover → Retrieve → Extract."""
    
    print("=" * 80)
    print("Azure Blob Input - Full Pipeline (Discover → Retrieve → Extract)")
    print("=" * 80)
    
    # Check required environment variables
    required_vars = {
        'AZURE_STORAGE_ACCOUNT_NAME': os.getenv('AZURE_STORAGE_ACCOUNT_NAME'),
        'AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT': os.getenv('AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT'),
    }
    
    missing = [k for k, v in required_vars.items() if not v]
    if missing:
        print(f"\n❌ Missing environment variables: {', '.join(missing)}")
        print("\nQuick setup:")
        print("export AZURE_STORAGE_ACCOUNT_NAME=mystorageaccount")
        print("export AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT=https://mydocint.cognitiveservices.azure.com")
        return
    
    print(f"\n✓ Environment configured")
    
    # Load config and create executor
    config_path = Path(__file__).parent / "blob_input_config.yaml"
    executor_catalog_path = Path(__file__).parent.parent.parent / "executor_catalog.yaml"
    
    async with PipelineExecutor.from_config_file(
        config_path=config_path,
        pipeline_name="blob_to_extraction",
        executor_catalog_path=executor_catalog_path
    ) as pipeline_executor:
        
        print(f"\n✓ Pipeline loaded (3 executors)")
        print(f"  1. Discover blobs")
        print(f"  2. Retrieve content")
        print(f"  3. Extract with Document Intelligence")
        
        print(f"\n📡 Processing...\n")
        
        # Execute
        result = await pipeline_executor.execute([])
        
        # Write results to output folder
        output_folder = Path(__file__).parent / "output"
        output_folder.mkdir(exist_ok=True)
        output_file = output_folder / "full_pipeline_result.json"
        with open(output_file, 'w', encoding='utf-8') as f:
                f.write(result.model_dump_json(indent=2))
        print(f"  Wrote output to {output_file}")
        
        print(f"\n✓ Pipeline execution completed")
        print(f"  Status: {result.status}")
        print(f"  Duration: {result.duration_seconds:.2f}s")
                
        print(f"\n✓ Full pipeline completed")
    
    print("\n" + "=" * 80)


async def main():
    """Run all examples."""
    
    # Choose which example to run
    examples = {
        "1": ("Basic Discovery", basic_blob_discovery),
        "2": ("Filtered Discovery", filtered_blob_discovery),
        "3": ("Discovery with Streaming", blob_discovery_with_streaming),
        "4": ("Full Pipeline", full_pipeline_example),
    }
    
    print("\nAzure Blob Input Executor Examples")
    print("=" * 80)
    print("\nSelect an example to run:")
    for key, (name, _) in examples.items():
        print(f"  {key}. {name}")
    print(f"  5. Run all examples")
    print(f"  0. Exit")
    
    # For automated testing, default to basic discovery
    choice = input("\nEnter choice (0-5): ").strip()
    
    if choice == '0':
        return
    elif choice == '5':
        for name, func in examples.values():
            await func()
            print("\n")
    elif choice in examples:
        _, func = examples[choice]
        await func()
    else:
        print("\n❌ Invalid choice")


if __name__ == "__main__":
    asyncio.run(main())
