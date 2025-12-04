#!/usr/bin/env python3
"""
PDF Extraction and Chunking Example

Demonstrates extracting text from PDF documents and creating intelligent chunks using:
- ContentRetrieverExecutor: Retrieve PDF documents from storage
- PDFExtractorExecutor: Extract content using PyMuPDF
- PDFContentChunkerExecutor: Create structure-aware chunks for RAG
- Efficient processing of PDF document sets
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
    config_path = Path(__file__).parent / "pdf_chunker_config.yaml"
    executor_catalog_path = Path(__file__).parent.parent.parent / "executor_catalog.yaml"
    
    async with PipelineExecutor.from_config_file(
        config_path=config_path,
        pipeline_name="pdf_extraction_and_chunking_pipeline",
        executor_catalog_path=executor_catalog_path,
    ) as pipeline:
        
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
        result = await pipeline.execute(documents[0:5])  # limit to first 5 for testing
    
        # write results to output folder
        output_folder = Path(__file__).parent / "output"
        output_folder.mkdir(exist_ok=True)
        output_file = output_folder / "chunker_result.json"
        with open(output_file, 'w', encoding='utf-8') as f:
                f.write(result.model_dump_json(indent=2))
        print(f"  Wrote output to {output_file}")
        
        # Analyze results
        successful = sum(1 for d in result.documents if d.get_status() == "completed") if isinstance(result.documents, list) else result.documents.get_status() == "completed"
        failed = sum(1 for d in result.documents if d.get_status() == "failed") if isinstance(result.documents, list) else result.documents.get_status() == "failed"
        total_duration = result.duration_seconds
        
        print(f"\n✓ PDF extraction and chunking completed")
        print(f"  Total documents: {len(result.documents) if isinstance(result.documents, list) else 1}")
        print(f"  Successful: {successful}")
        print(f"  Failed: {failed}")
        print(f"  Total duration (seconds): {total_duration:.2f}s")
        print(f"  Avg per document: {total_duration/(len(result.documents) if isinstance(result.documents, list) else 1):.2f}s")
    
        # Show chunking statistics
        print(f"\n📊 Chunking Statistics:")
        total_chunks = 0
        total_pages = 0
        
        if isinstance(result.documents, list):
            for doc in result.documents:
                doc_name = doc.id.canonical_id
                chunks_created = doc.summary_data.get('chunks_created', 0)
                avg_chunk_size = doc.summary_data.get('avg_chunk_size', 0)
                pages_processed = doc.summary_data.get('pages_processed', 0)
                chunking_strategy = doc.summary_data.get('chunking_strategy', 'N/A')
                
                total_chunks += chunks_created
                total_pages += pages_processed
                
                print(f"\n  📄 {doc_name}")
                print(f"     Pages: {pages_processed}")
                print(f"     Chunks: {chunks_created}")
                print(f"     Avg Chunk Size: {avg_chunk_size} chars")
                print(f"     Strategy: {chunking_strategy}")
    
            print(f"\n  Total Pages Processed: {total_pages}")
            print(f"  Total Chunks Created: {total_chunks}")
            if total_chunks > 0 and len(result.documents) > 0:
                print(f"  Average Chunks per Document: {total_chunks / len(result.documents):.1f}")
    
        # Show sample chunk data for first document
        if isinstance(result.documents, list) and len(result.documents) > 0:
            first_doc = result.documents[0]
            if 'chunks' in first_doc.data:
                chunks = first_doc.data['chunks']
                print(f"\n📄 Sample Chunks (First Document - {first_doc.id.canonical_id}):")
                
                # Show first 3 chunks
                for i, chunk in enumerate(chunks[:3], 1):
                    chunk_text = chunk['text'][:100] + "..." if len(chunk['text']) > 100 else chunk['text']
                    metadata = chunk['metadata']
                    
                    print(f"\n  Chunk {i}:")
                    print(f"    Text: {chunk_text}")
                    print(f"    Char Count: {metadata.get('char_count', 0)}")
                    print(f"    Word Count: {metadata.get('word_count', 0)}")
                    
                    if 'section_title' in metadata and metadata['section_title']:
                        print(f"    Section: {metadata['section_title']}")
                    
                    if 'page_numbers' in metadata:
                        print(f"    Pages: {metadata['page_numbers']}")
                    
                    if 'context' in chunk:
                        print(f"    Context: {chunk['context']}")
                
                # Chunk size distribution
                chunk_sizes = [chunk['metadata']['char_count'] for chunk in chunks]
                print(f"\n  Chunk Size Distribution:")
                print(f"    Total Chunks: {len(chunks)}")
                print(f"    Size Range: {min(chunk_sizes)} - {max(chunk_sizes)} chars")
                print(f"    Average Size: {sum(chunk_sizes) / len(chunk_sizes):.0f} chars")
        
        # Show processing events
        print(f"\n📊 Processing Events:")
        for i, event in enumerate(result.events):
            print(f"\n  Event {i+1}: {event.event_type}")
            print(f"    Executor: {event.executor_id}")
            
        print("\n" + "=" * 70)
        print(f'\nWrote pipeline result to {output_file}\n')
    
    print("\n" + "=" * 70)
    print("Done!")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(run_pipeline())
