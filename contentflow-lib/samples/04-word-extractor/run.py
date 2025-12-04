"""
Word Document Extraction Example

Demonstrates extracting text, paragraphs, tables, and properties from Word documents using:
- ContentRetrieverExecutor: Retrieve Word documents from storage
- WordExtractorExecutor: Extract content using python-docx
- Efficient processing of Word document sets
"""

import asyncio
import logging
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from samples.setup_logger import setup_logging
from packages.pipeline import PipelineExecutor, PipelineResult
from packages.models import Content, ContentIdentifier

# Get the current directory
samples_dir = Path(__file__).parent.parent

# Load environment variables
load_dotenv(f'{samples_dir}/.env')

logger = logging.getLogger(__name__)

setup_logging()

async def run_pipeline():
    """Execute pipeline"""
    
    print("=" * 70)
    
    # Load config
    config_path = Path(__file__).parent / "pipeline_config.yaml"
    executor_catalog_path = Path(__file__).parent.parent.parent / "executor_catalog.yaml"
    
    async with PipelineExecutor.from_config_file(
        config_path=config_path,
        pipeline_name="word_extraction_pipeline",
        executor_catalog_path=executor_catalog_path,
    ) as pipeline:
        
        print(f"\n✓ Initialized pipeline")
        
        documents = []
        
        # load documents from local path
        local_path = Path('/Users/nadeemis/temp/test_files')
        for file in local_path.glob('*.docx'):
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
        
        print(f"\n✓ Created {len(documents)} documents for Word extraction")
        
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
        
        print(f"\n✓ Word extraction completed")
        print(f"  Total documents: {len(result.documents) if isinstance(result.documents, list) else 1}")
        print(f"  Successful: {successful}")
        print(f"  Failed: {failed}")
        print(f"  Total duration (seconds): {total_duration:.2f}s")
        print(f"  Avg per document: {total_duration/(len(result.documents) if isinstance(result.documents, list) else 1):.2f}s")
        
        # Show sample extracted data
        if isinstance(result.documents, list) and len(result.documents) > 0:
            first_doc = result.documents[0]
            if 'word_output' in first_doc.data:
                word_output = first_doc.data['word_output']
                print(f"\n📄 Sample Extraction (First Document):")
                print(f"  Document ID: {first_doc.id}")
                if 'text' in word_output:
                    print(f"  Text length: {len(word_output['text'])} characters")
                    print(f"  Text preview: {word_output['text'][:200]}...")
                if 'paragraphs' in word_output:
                    print(f"  Paragraphs extracted: {len(word_output['paragraphs'])}")
                if 'tables' in word_output:
                    print(f"  Tables extracted: {len(word_output['tables'])}")
                if 'properties' in word_output:
                    props = word_output['properties']
                    print(f"  Document properties:")
                    if props.get('title'):
                        print(f"    Title: {props['title']}")
                    if props.get('author'):
                        print(f"    Author: {props['author']}")
                if 'images' in word_output:
                    print(f"  Images extracted: {len(word_output['images'])}")
        
        # Show processing events
        print(f"\n📊 Processing Events:")
        for i, event in enumerate(result.events):
            print(f"\n  Event {i+1}: {event.event_type}")
            print(f"    Executor: {event.executor_id}")
    
    print("\n" + "=" * 70)
    print("Done!")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(run_pipeline())
