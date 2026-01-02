"""
GPT-RAG Document Ingestion Pipeline

Enterprise-grade RAG ingestion pipeline for processing diverse documents with:
- Azure Blob Storage scanning for multi-format documents
- Azure Document Intelligence extraction (PDF, DOCX, PPTX, etc.)
- Intelligent recursive chunking optimized for RAG retrieval
- Vector embeddings generation with Azure OpenAI
- Azure AI Search indexing for semantic search

This sample demonstrates a complete end-to-end RAG ingestion workflow
suitable for production knowledge base and AI-powered chat applications.
"""

import asyncio
import logging
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from samples.setup_logger import setup_logging
from contentflow.pipeline import PipelineExecutor, PipelineResult
from contentflow.models import Content, ContentIdentifier

# Get the current directory
samples_dir = Path(__file__).parent.parent

# Load environment variables
load_dotenv(f'{samples_dir}/.env')

logger = logging.getLogger(__name__)

setup_logging()

async def run_pipeline():
    """Execute GPT-RAG ingestion pipeline"""
    
    print("=" * 80)
    print("GPT-RAG Document Ingestion Pipeline")
    print("=" * 80)
    
    # Validate required environment variables
    required_vars = [
        "AZURE_STORAGE_ACCOUNT",
        "AZURE_BLOB_CONTAINER_NAME",
        "AZURE_DOC_INTELLIGENCE_ENDPOINT",
        "AZURE_OPENAI_ENDPOINT",
        "AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT",
        "AZURE_AI_SEARCH_ACCOUNT",
        "AZURE_AI_SEARCH_INDEX"
    ]
    
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        print(f"\n❌ Missing required environment variables: {', '.join(missing_vars)}")
        print("Please set them in your .env file")
        return
    
    # Load config
    config_path = Path(__file__).parent / "pipeline-config.yaml"
    executor_catalog_path = Path(__file__).parent.parent.parent / "executor_catalog.yaml"
    
    async with PipelineExecutor.from_config_file(
        config_path=config_path,
        pipeline_name="gpt_rag_ingestion_pipeline",
        executor_catalog_path=executor_catalog_path,
    ) as pipeline:
        
        print(f"\n✓ Initialized GPT-RAG ingestion pipeline")
        print(f"  - Source: Azure Blob Storage ({os.getenv('AZURE_BLOB_CONTAINER_NAME')})")
        print(f"  - Document Intelligence: {os.getenv('AZURE_DOC_INTELLIGENCE_ENDPOINT')}")
        print(f"  - Embeddings Model: {os.getenv('AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT')}")
        print(f"  - Search Index: {os.getenv('AZURE_AI_SEARCH_INDEX')}")
        
        # The pipeline starts with azure_blob_input which discovers documents
        # We pass an empty list as the blob scanner will populate documents
        documents = []
        
        print(f"\n🔄 Starting document ingestion...")
        print(f"  Pipeline will:")
        print(f"    1. Scan Azure Blob Storage for documents")
        print(f"    2. Retrieve document content")
        print(f"    3. Extract text with Document Intelligence")
        print(f"    4. Create intelligent chunks")
        print(f"    5. Generate vector embeddings")
        print(f"    6. Index to Azure AI Search")
        
        # Execute pipeline
        result = await pipeline.execute(documents)
        
        # Write results to output folder
        output_folder = Path(__file__).parent / "output"
        output_folder.mkdir(exist_ok=True)
        output_file = output_folder / "rag_ingestion_result.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(result.model_dump_json(indent=2))
        print(f"\n✓ Wrote detailed results to {output_file}")
        
        # Analyze results
        total_docs = len(result.content) if isinstance(result.content, list) else 1
        successful = sum(1 for d in result.content if d.get_status() == "completed") if isinstance(result.content, list) else (1 if result.content.get_status() == "completed" else 0)
        failed = sum(1 for d in result.content if d.get_status() == "failed") if isinstance(result.content, list) else (1 if result.content.get_status() == "failed" else 0)
        total_duration = result.duration_seconds
        
        print(f"\n" + "=" * 80)
        print(f"✓ RAG Ingestion Pipeline Completed")
        print(f"=" * 80)
        print(f"  Total documents processed: {total_docs}")
        print(f"  Successfully indexed: {successful}")
        print(f"  Failed: {failed}")
        print(f"  Total duration: {total_duration:.2f}s")
        if total_docs > 0:
            print(f"  Avg per document: {total_duration/total_docs:.2f}s")
        
        # Show sample results
        if isinstance(result.content, list) and len(result.content) > 0:
            first_doc = result.content[0]
            print(f"\n📄 Sample Results (First Document):")
            print(f"  Document ID: {first_doc.id}")
            
            # Show extraction stats
            if 'doc_intell_output' in first_doc.data:
                doc_output = first_doc.data['doc_intell_output']
                if 'text' in doc_output:
                    print(f"  Extracted text: {len(doc_output['text'])} characters")
                if 'pages' in doc_output:
                    print(f"  Pages processed: {len(doc_output['pages'])}")
            
            # Show chunking stats
            if 'chunks' in first_doc.data:
                chunks = first_doc.data['chunks']
                if isinstance(chunks, list):
                    print(f"  Chunks created: {len(chunks)}")
                    total_chunk_chars = sum(len(chunk.get('text', '')) for chunk in chunks)
                    avg_chunk_size = total_chunk_chars / len(chunks) if chunks else 0
                    print(f"  Avg chunk size: {avg_chunk_size:.0f} characters")
            
            # Show embedding stats
            if 'embedding' in first_doc.data:
                embedding = first_doc.data['embedding']
                if isinstance(embedding, list):
                    print(f"  Embedding dimensions: {len(embedding)}")
        
        print(f"\n🎉 Documents are now indexed and ready for semantic search!")
        print(f"=" * 80)


if __name__ == "__main__":
    asyncio.run(run_pipeline())
