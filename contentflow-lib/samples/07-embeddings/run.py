"""
PDF to Embeddings Example

Demonstrates extracting text from PDFs and generating embeddings using:
- ContentRetrieverExecutor: Retrieve PDF documents from storage
- PDFExtractorExecutor: Extract text content from PDFs
- AzureOpenAIEmbeddingsExecutor: Generate vector embeddings from extracted text
- Efficient processing of PDF document sets with semantic embeddings
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
        pipeline_name="pdf_extraction_pipeline",
        executor_catalog_path=executor_catalog_path,
    ) as pipeline:
        
        print(f"\n✓ Initialized pipeline")
        
        documents = []
        
        # Process a document
        document = Content(
                id=ContentIdentifier(
                        canonical_id="doc_pdf_001",
                        unique_id="doc_pdf_001",
                        source_id="local_file_source",
                        source_name="local_file",
                        source_type="local_file",
                        path=f"{samples_dir}/99-assets/sample.pdf",
                    )
            )
        documents.append(document)
        
        print(f"\n✓ Created {len(documents)} documents for PDF extraction and embedding generation")
        
        # Process all documents
        result = await pipeline.execute(documents)
        
        # write results to output folder
        output_folder = Path(__file__).parent / "output"
        output_folder.mkdir(exist_ok=True)
        output_file = output_folder / "embeddings_result.json"
        with open(output_file, 'w', encoding='utf-8') as f:
                f.write(result.model_dump_json(indent=2))
        print(f"  Wrote output to {output_file}")
        
        # Analyze results
        successful = sum(1 for d in result.documents if d.get_status() == "completed") if isinstance(result.documents, list) else result.documents.get_status() == "completed"
        failed = sum(1 for d in result.documents if d.get_status() == "failed") if isinstance(result.documents, list) else result.documents.get_status() == "failed"
        total_duration = result.duration_seconds
        
        print(f"\n✓ PDF extraction and embeddings generation completed")
        print(f"  Total documents: {len(result.documents) if isinstance(result.documents, list) else 1}")
        print(f"  Successful: {successful}")
        print(f"  Failed: {failed}")
        print(f"  Total duration (seconds): {total_duration:.2f}s")
        print(f"  Avg per document: {total_duration/(len(result.documents) if isinstance(result.documents, list) else 1):.2f}s")
        
        # Show sample extracted data and embeddings
        if isinstance(result.documents, list) and len(result.documents) > 0:
            first_doc = result.documents[0]
            print(f"\n📄 Sample Results (First Document):")
            print(f"  Document ID: {first_doc.id}")
            
            if 'pdf_output' in first_doc.data:
                pdf_output = first_doc.data['pdf_output']
                if 'text' in pdf_output:
                    print(f"  Text length: {len(pdf_output['text'])} characters")
                    print(f"  Text preview: {pdf_output['text'][:200]}...")
                if 'pages' in pdf_output:
                    print(f"  Pages extracted: {len(pdf_output['pages'])}")
                if 'images' in pdf_output:
                    print(f"  Images extracted: {len(pdf_output['images'])}")
            
            if 'embedding' in first_doc.data:
                embedding = first_doc.data['embedding']
                print(f"\n  🔢 Embedding Generated:")
                print(f"    Dimensions: {len(embedding)}")
                print(f"    First 5 values: {embedding[:5]}")
                print(f"    Model: {first_doc.summary_data.get('embedding_model', 'N/A')}")
                print(f"    Status: {first_doc.summary_data.get('embedding_status', 'N/A')}")
        
        # Show processing events
        print(f"\n📊 Processing Events:")
        for i, event in enumerate(result.events):
            print(f"\n  Event {i+1}: {event.event_type}")
            print(f"    Executor: {event.executor_id}")
    
        print("\n" + "=" * 70)
        print(f"\nOutput written to: {output_file}\n")
    
    print("\n" + "=" * 70)
    print("Done!")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(run_pipeline())
