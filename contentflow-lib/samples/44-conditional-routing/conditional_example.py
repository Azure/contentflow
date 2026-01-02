"""
Conditional Routing Example

Demonstrates routing documents based on their properties using:
- Conditional edges: Route based on document metadata
- Type-specific processing: Different executors for different doc types
- Dynamic pipeline paths
"""

import asyncio
import logging
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from samples.setup_logger import setup_logging
from contentflow.pipeline_executor import PipelineExecutor
from contentflow.models import Content, ContentIdentifier

# Get the current directory
samples_dir = Path(__file__).parent

# Load environment variables
load_dotenv(f'{samples_dir.parent.parent}/.env')

setup_logging()

logger = logging.getLogger(__name__)


async def conditional_routing_example():
    """Route documents based on their type."""
    
    print("=" * 70)
    print("Conditional Routing Example")
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
    config_path = Path(__file__).parent / "conditional_config.yaml"
    
    async with PipelineExecutor.from_config_file(
        config_path=config_path,
        pipeline_name="conditional_routing"
    ) as executor:
        
        print(f"\n✓ Initialized conditional routing pipeline")
        print(f"  Routes: PDF → process_pdf")
        print(f"          Image → process_image")
        print(f"          Text → process_text")
        
        # Create documents of different types
        documents = [
            Content(
                id=ContentIdentifier(
                    canonical_id="doc_pdf_001",
                    unique_id="doc_pdf_001",
                    source_id="local_file",
                    source_name="pdf_doc",
                    source_type="local_file",
                    path=f"{samples_dir.parent.parent}/99-assets/sample.pdf",
                ),
                metadata={"file_type": "pdf", "name": "sample.pdf"}
            ),
            Content(
                id=ContentIdentifier(
                    canonical_id="doc_img_001",
                    unique_id="doc_img_001",
                    source_id="local_file",
                    source_name="image_doc",
                    source_type="local_file",
                    path=f"{samples_dir.parent.parent}/99-assets/sample.jpg",
                ),
                metadata={"file_type": "jpg", "name": "sample.jpg"}
            ),
            Content(
                id=ContentIdentifier(
                    canonical_id="doc_txt_001",
                    unique_id="doc_txt_001",
                    source_id="local_file",
                    source_name="text_doc",
                    source_type="local_file",
                    path=f"{samples_dir.parent.parent}/99-assets/sample.txt",
                ),
                metadata={"file_type": "txt", "name": "sample.txt"}
            ),
        ]
        
        print(f"\n✓ Processing {len(documents)} documents with different types")
        
        # Process each document and track routing
        for doc in documents:
            print(f"\n📄 Processing: {doc.metadata.get('name', doc.id)}")
            print(f"  Type: {doc.metadata.get('file_type', 'unknown')}")
            
            # Execute with streaming to see routing
            route_taken = []
            
            async for event in executor.execute_stream(doc):
                if event.executor_id:
                    route_taken.append(event.executor_id)
                
                # Show routing decision
                if "routing" in event.event_type or "conditional" in event.event_type:
                    print(f"  → Routing event: {event.event_type}")
                    if event.data:
                        print(f"    Data: {event.data}")
            
            # Show the path taken
            unique_route = []
            for executor_id in route_taken:
                if not unique_route or unique_route[-1] != executor_id:
                    unique_route.append(executor_id)
            
            print(f"  ✓ Route taken: {' → '.join(unique_route)}")
    
    print("\n" + "=" * 70)
    print("Done!")
    print("=" * 70)


async def conditional_with_fallback():
    """Demonstrate conditional routing with fallback."""
    
    print("=" * 70)
    print("Conditional Routing with Fallback")
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
    config_path = Path(__file__).parent / "conditional_config.yaml"
    
    async with PipelineExecutor.from_config_file(
        config_path=config_path,
        pipeline_name="conditional_routing"
    ) as executor:
        
        print(f"\n✓ Initialized conditional routing pipeline")
        
        # Create document with unknown type (should use fallback if configured)
        document = Content(
            id=ContentIdentifier(
                canonical_id="doc_unknown_001",
                unique_id="doc_unknown_001",
                source_id="local_file",
                source_name="unknown_doc",
                source_type="local_file",
                path=f"{samples_dir.parent.parent}/99-assets/sample.pdf",
            ),
            metadata={"file_type": "unknown", "name": "unknown.dat"}
        )
        
        print(f"\n📄 Processing document with unknown type")
        print(f"  Type: {document.metadata.get('file_type')}")
        
        try:
            result = await executor.execute(document)
            
            print(f"\n✓ Processing result:")
            print(f"  Status: {result.status}")
            print(f"  Duration: {result.duration_seconds:.2f}s")
            
            if result.error:
                print(f"  Note: {result.error}")
                print(f"  (This is expected for unknown types without fallback)")
        
        except Exception as e:
            print(f"\n⚠️  Expected error for unknown type: {str(e)}")
            print(f"  Tip: Add a default route in your conditional edges")
    
    print("\n" + "=" * 70)
    print("Done!")
    print("=" * 70)


if __name__ == "__main__":
    # Run basic conditional routing
    asyncio.run(conditional_routing_example())
    
    print("\n\n")
    
    # Run with fallback demonstration
    asyncio.run(conditional_with_fallback())
