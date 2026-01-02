"""
Article Summarization Pipeline

Automatically summarize long-form articles, research papers, and blog posts using
advanced AI models with:
- Multi-level summarization (configurable length and style)
- Key entity extraction (people, organizations, locations, etc.)
- Sentiment analysis
- Topic detection

This sample demonstrates automated content analysis and summarization
suitable for news aggregation, content curation, and research workflows.
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
    """Execute document analysis pipeline"""
    
    print("=" * 80)
    print("Document Analysis Pipeline")
    print("=" * 80)
    
    # Validate required environment variables
    required_vars = [
        "AZURE_STORAGE_ACCOUNT_NAME",
        "AZURE_CONTENT_UNDERSTANDING_ENDPOINT",
        "AZURE_OPENAI_ENDPOINT"
    ]
    
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        print(f"\n❌ Missing required environment variables: {', '.join(missing_vars)}")
        print("Please set them in your .env file")
        return
    
    # Load config
    config_path = Path(__file__).parent / "pipeline-config.yaml"
    executor_catalog_path = samples_dir.parent / "executor_catalog.yaml"
    
    async with PipelineExecutor.from_config_file(
        config_path=config_path,
        pipeline_name="document_analysis_pipeline",
        executor_catalog_path=executor_catalog_path,
    ) as pipeline:
        
        print(f"\n✓ Initialized document analysis pipeline")
        print(f"  - AI Model: {os.getenv('AZURE_OPENAI_DEPLOYMENT')}")
        print(f"  - Summary Style: Paragraph format (medium length)")
        print(f"  - Entity Types: Person, Organization, Location, Date, Product, Event")
        print(f"  - PII Detection: Enabled")
        
        # Execute pipeline (no input needed for blob discovery)
        result = await pipeline.execute([])
        
        # Write results to output folder
        output_folder = Path(__file__).parent / "output"
        output_folder.mkdir(exist_ok=True)
        output_file = output_folder / "summarization_result.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(result.model_dump_json(indent=2))
        print(f"\n✓ Wrote detailed results to {output_file}")
        
        # Analyze results
        total_docs = len(result.content) if isinstance(result.content, list) else 1
        successful = sum(1 for d in result.content if d.get_status() == "completed") if isinstance(result.content, list) else (1 if result.content.get_status() == "completed" else 0)
        failed = sum(1 for d in result.content if d.get_status() == "failed") if isinstance(result.content, list) else (1 if result.content.get_status() == "failed" else 0)
        total_duration = result.duration_seconds
        
        print(f"\n" + "=" * 80)
        print(f"✓ Document Analysis Completed")
        print(f"=" * 80)
        print(f"  Total documents processed: {total_docs}")
        print(f"  Successfully analyzed: {successful}")
        print(f"  Failed: {failed}")
        print(f"  Total duration: {total_duration:.2f}s")
        if total_docs > 0:
            print(f"  Avg per document: {total_duration/total_docs:.2f}s")
        
        # Display summaries and extracted information
        if isinstance(result.content, list) and len(result.content) > 0:
            print(f"\n" + "=" * 80)
            print(f"📄 Document Analysis Results")
            print(f"=" * 80)
            
            for idx, doc in enumerate(result.content, 1):
                print(f"\n{'─' * 80}")
                print(f"Document {idx}: {doc.id.canonical_id}")
                print(f"{'─' * 80}")
                
                # Summary
                if 'summary' in doc.data:
                    summary = doc.data['summary']
                    print(f"\n✨ AI-Generated Summary:")
                    print(f"  {summary}")
                
                # Entities
                if 'entities' in doc.data:
                    entities = doc.data['entities']
                    print(f"\n🏷️  Extracted Entities:")
                    
                    if isinstance(entities, dict):
                        for entity_type, entity_list in entities.items():
                            if entity_list:
                                print(f"  {entity_type.upper()}: {[entity.get('text', entity) if isinstance(entity, dict) else entity for entity in entity_list][:10]}")  # Show first 10
                    elif isinstance(entities, list):
                        for entity in entities[:10]:  # Show first 10
                            if isinstance(entity, dict):
                                print(f"  - {entity.get('text', 'N/A')} ({entity.get('type', 'unknown')})")
                
                if 'pii_detected' in doc.data:
                    pii_info = doc.data['pii_detected']
                    print(f"\n🔒 PII Detection Results:")
                    for pii_found in pii_info["pii_found"]:
                        print(f"  Type: {pii_found["type"]}") 
                        print(f"  Value: {pii_found["value"]}")
                        print(f"  Confidence: {pii_found["confidence"]}\n")
                
        print(f"\n" + "=" * 80)
        print(f"🎉 Document analysis complete!")
        print(f"=" * 80)


if __name__ == "__main__":
    asyncio.run(run_pipeline())
