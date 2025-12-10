"""
Simple example showing minimal configuration for document processing workflows.

This demonstrates the simplified connector-based architecture with:
- Auto-detection of credentials
- Sensible defaults
- Minimal required configuration
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
samples_dir = Path(__file__).parent.parent

# Load environment variables
load_dotenv(f'{samples_dir}/.env')

setup_logging()

logger = logging.getLogger(__name__)

async def simple_workflow_sample():
    """Run a simple document processing workflow with minimal configuration."""
    
    print("=" * 60)
    print("Simple Document Processing Workflow")
    print("=" * 60)
    
    # Just set 1 environment variable - that's it!
    required_vars = {
        'AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT': os.getenv('AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT'),
    }
    
    missing = [k for k, v in required_vars.items() if not v]
    if missing:
        print(f"\n❌ Missing environment variables: {', '.join(missing)}")
        print("\nQuick setup:")
        print("export AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT=https://mydocint.cognitiveservices.azure.com")
        return
    
    # Load simple config and create executor
    config_path = Path(__file__).parent / "simple_config.yaml"
    executor_catalog_path = samples_dir.parent / "executor_catalog.yaml"
    
    async with PipelineExecutor.from_config_file(
        config_path=config_path,
        pipeline_name="basic",
        executor_catalog_path=executor_catalog_path
    ) as pipeline_executor:
        
        print(f"\n✓ Loaded config and initialized executor")
        info = pipeline_executor.get_pipeline_info()
        print(f"  Pipelines: {', '.join(info['factory_info']['pipelines'])}")
        
        # Process a document
        document = Content(
                id=ContentIdentifier(
                        canonical_id="doc_pdf_001",
                        unique_id="doc_pdf_001",
                        source_name="local_file",
                        source_type="local_file",
                        path=f"{samples_dir}/99-assets/sample.pdf",
                    )
            )
        
        print(f"\n✓ Processing document: {document.id}")
        
        # Execute with PipelineExecutor
        result = await pipeline_executor.execute(document)
        
        print(f"\n✓ Workflow completed")
        print(f"  Status: {result.status}")
        print(f"  Duration: {result.duration_seconds:.2f}s")
        print(f"  Events captured: {len(result.events)}")
        
        # write results to output folder
        output_folder = Path(__file__).parent / "output"
        output_folder.mkdir(exist_ok=True)
        output_file = output_folder / "simple_workflow_result.json"
        with open(output_file, 'w', encoding='utf-8') as f:
                f.write(result.model_dump_json(indent=2))
        print(f"  Wrote output to {output_file}")
        
        if result.error:
            print(f"  Error: {result.error}")
    
    print("\n" + "=" * 60)
    print("Done!")
    print("=" * 60)


async def simple_workflow_sample_with_streaming():
    """Run workflow with streaming."""
    
    print("=" * 60)
    print("Document Processing with Streaming")
    print("=" * 60)
    
    # Just set 1 environment variable - that's it!
    required_vars = {
        'AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT': os.getenv('AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT'),
    }
    
    missing = [k for k, v in required_vars.items() if not v]
    if missing:
        print(f"\n❌ Missing environment variables: {', '.join(missing)}")
        print("\nQuick setup:")
        print("export AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT=https://mydocint.cognitiveservices.azure.com")
        return
    
    # Load simple config and create executor
    config_path = Path(__file__).parent / "simple_config.yaml"
    executor_catalog_path = samples_dir.parent / "executor_catalog.yaml"
    
    async with PipelineExecutor.from_config_file(
        config_path=config_path,
        pipeline_name="basic",
        executor_catalog_path=executor_catalog_path
    ) as pipeline_executor:
        
        print(f"\n✓ Loaded config and initialized executor")
        info = pipeline_executor.get_pipeline_info()
        print(f"  Pipelines: {', '.join(info['factory_info']['pipelines'])}")
        
       # Process a document
        document = Content(
                id=ContentIdentifier(
                        canonical_id="doc_pdf_001",
                        unique_id="doc_pdf_001",
                        source_name="local_file",
                        source_type="local_file",
                        path=f"{samples_dir}/99-assets/sample.pdf",
                    )
            )
        
        print(f"\n✓ Processing document: {document.id}")
        
        # Execute with PipelineExecutor
        async for event in pipeline_executor.execute_stream(document):
            print(f"\n--- Event received ---")
            print(f"  Type: {event.event_type}")
            print(f"  Executor: {event.executor_id}")
            print(f"  Data: {event.data}")
            print(f"  Error: {event.error}")

            
    print("\n" + "=" * 60)
    print("Done!")

if __name__ == "__main__":
    # Run simple example
    asyncio.run(simple_workflow_sample())
    
    asyncio.run(simple_workflow_sample_with_streaming())
