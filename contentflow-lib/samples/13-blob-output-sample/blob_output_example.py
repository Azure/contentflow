"""
Azure Blob Output Executor - Python Sample

This example demonstrates how to use the AzureBlobOutputExecutor
to write processed content to Azure Blob Storage.
"""

import asyncio
import logging
from datetime import datetime, timezone
import sys
from pathlib import Path
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from samples.setup_logger import setup_logging
from packages.pipeline import PipelineExecutor
from packages.models import Content, ContentIdentifier
from packages.executors import AzureBlobOutputExecutor

# Get the current directory
samples_dir = Path(__file__).parent.parent

# Load environment variables
load_dotenv(f'{samples_dir}/.env')

logger = logging.getLogger(__name__)

setup_logging()

async def example_basic_blob_output():
    """
    Example 1: Basic blob output with default settings.
    """
    print("=== Example 1: Basic Blob Output ===")
    
    # Create sample content
    content = Content(
        id=ContentIdentifier(
            unique_id="doc_001",
            canonical_id="sample_document_001",
            filename="sample.pdf"
        ),
        data={
            "title": "Sample Document",
            "author": "John Doe",
            "category": "reports",
            "content": "This is the document content...",
            "pages": 10,
            "created_at": "2024-01-15T10:00:00Z"
        },
        summary_data={
            "processed_at": datetime.now(timezone.utc).isoformat(),
            "word_count": 1500
        }
    )
    
    # Create executor
    executor = AzureBlobOutputExecutor(
        id="basic_blob_output_executor",
        settings={
            "storage_account_name": "${AZURE_STORAGE_ACCOUNT_NAME}",
            "credential_type": "default_azure_credential",
            "container_name": "processed-output",
            "path_template": "{executor_id}/{year}/{month}/{day}",
            "filename_template": "{id.unique_id}_{timestamp}.json",
            "content_field": "title",  # Write the 'title' field from Content.data
            "overwrite_existing": False,
            "pretty_print": True
        }
    )
    
    # Process content (this would normally be called by the workflow engine)
    try:
        result = await executor.process_content_item(content)
        
        print(f"Write Status: {result.summary_data.get('write_status')}")
        print(f"Blob Path: {result.summary_data.get('blob_path')}")
        print(f"Blob Size: {result.summary_data.get('blob_size')} bytes")
        print(f"Blob ETag: {result.summary_data.get('blob_etag')}")
        
    except Exception as e:
        logger.error(f"Error writing blob: {e}")


async def example_pipeline_blob_output():
    """
    Example 2: Blob output with gzip compression in a pipeline.
    """
    print("\n=== Example 2: Blob Output with Compression ===")
        
    try:
        # Load config
        config_path = Path(__file__).parent / "blob_output_example.yaml"
        executor_catalog_path = samples_dir.parent / "executor_catalog.yaml"
        
        async with PipelineExecutor.from_config_file(
            config_path=config_path,
            pipeline_name="basic_blob_output_pipeline",
            executor_catalog_path=executor_catalog_path,
        ) as pipeline:
            
            print(f"\n✓ Initialized pipeline")
            
            documents = []
            
            # load documents from local path
            local_path = Path(f"{samples_dir}/99-assets")
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
                        ),
                        data={
                            "title": "Large Document with Lots of Data",
                            "author": "Jane Smith",
                            "category": "research",
                            "content": "This is a very large document..." * 1000,  # Larger content
                            "metadata": {
                                "source": "research_database",
                                "tags": ["ml", "ai", "data"],
                                "department": "engineering"
                            },
                            "pages": 150,
                            "created_at": "2024-02-20T14:30:00Z"
                        },
                        summary_data={
                            "extracted_entities": ["Microsoft", "Azure", "AI"],
                            "sentiment": "neutral",
                            "language": "en"
                        }
                    )
                )
            
            print(f"\n✓ Created {len(documents)} documents for PDF extraction")
            
            if len(documents) == 0:
                print(f"\n⚠️  No PDF files found in {local_path}")
                print(f"   Please add .pdf files to the directory")
                return
            
            # Process all documents
            result = await pipeline.execute(documents[0:2])  # limit to first 2 for testing
            
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
        
            print(f"\n✓ PDF extraction completed")
            print(f"  Total documents: {len(result.documents) if isinstance(result.documents, list) else 1}")
            print(f"  Successful: {successful}")
            print(f"  Failed: {failed}")
            print(f"  Total duration (seconds): {total_duration:.2f}s")
            print(f"  Avg per document: {total_duration/(len(result.documents) if isinstance(result.documents, list) else 1):.2f}s")
        
    except Exception as e:
        print(f"Error writing compressed blob: {e}")



async def main():
    """Run all examples."""
    print("Azure Blob Output Executor - Sample Demonstrations\n")
    
    # Run examples
    await example_basic_blob_output()
    await example_pipeline_blob_output()
    
    print("\n=== All Examples Completed ===")


if __name__ == "__main__":
    # Note: These examples assume Azure credentials are configured
    # via environment variables or Azure CLI login
    asyncio.run(main())
