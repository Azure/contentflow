"""
Translation Pipeline Example

Demonstrates using TranslationExecutor for translating text with:
- Configurable target and source languages
- Multiple translation styles (formal, informal, technical, natural, literal)
- Format preservation
- Custom terminology and glossary support
"""

import asyncio
import logging
import sys
from pathlib import Path
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from samples.setup_logger import setup_logging
from contentflow.pipeline import PipelineExecutor
from contentflow.models import Content, ContentIdentifier

# Get the samples directory
samples_dir = Path(__file__).parent.parent.parent

# Load environment variables
load_dotenv(f'{samples_dir}/.env')

logger = logging.getLogger(__name__)

setup_logging()

async def run_pipeline():
    """Execute Translation pipeline"""
    
    print("=" * 70)
    print("TRANSLATION EXECUTOR RUN")
    print("=" * 70)
    
    # Load config
    config_path = Path(__file__).parent / "translation_config.yaml"
    executor_catalog_path = samples_dir.parent / "executor_catalog.yaml"
    
    async with PipelineExecutor.from_config_file(
        config_path=config_path,
        pipeline_name="translation_pipeline",
        executor_catalog_path=executor_catalog_path,
    ) as pipeline_executor:
        
        print(f"\n✓ Initialized translation pipeline")
        
        # Create sample documents with different types of content for translation
        documents = [
            Content(
                id=ContentIdentifier(
                    canonical_id="tech_article",
                    unique_id="tech_article",
                    source_name="sample",
                    source_type="text",
                ),
                data={
                    "text": """
                    Artificial intelligence and machine learning are revolutionizing the technology industry. 
                    Neural networks can now process complex data patterns with unprecedented accuracy. Cloud 
                    computing infrastructure enables scalable deployment of AI models across global regions.
                    """
                }
            ),
            Content(
                id=ContentIdentifier(
                    canonical_id="business_doc",
                    unique_id="business_doc",
                    source_name="sample",
                    source_type="text",
                ),
                data={
                    "text": """
                    Dear valued customer,
                    
                    We are pleased to announce the launch of our new product line. Our team has worked 
                    diligently to ensure the highest quality standards. We appreciate your continued 
                    support and look forward to serving you.
                    
                    Best regards,
                    Customer Service Team
                    """
                }
            ),
            Content(
                id=ContentIdentifier(
                    canonical_id="casual_message",
                    unique_id="casual_message",
                    source_name="sample",
                    source_type="text",
                ),
                data={
                    "text": """
                    Hey! How's it going? I just wanted to check in and see how you're doing. We should 
                    grab coffee sometime soon and catch up. Let me know when you're free!
                    """
                }
            ),
            Content(
                id=ContentIdentifier(
                    canonical_id="medical_text",
                    unique_id="medical_text",
                    source_name="sample",
                    source_type="text",
                ),
                data={
                    "text": """
                    The patient presented with symptoms of acute respiratory infection. Blood pressure 
                    was measured at 120/80 mmHg. Laboratory tests indicated elevated white blood cell 
                    count. Treatment protocol includes antibiotic therapy and monitoring.
                    """
                }
            ),
            Content(
                id=ContentIdentifier(
                    canonical_id="marketing_copy",
                    unique_id="marketing_copy",
                    source_name="sample",
                    source_type="text",
                ),
                data={
                    "text": """
                    Transform your workflow with cutting-edge automation! Our innovative solution delivers 
                    exceptional results while reducing costs by up to 50%. Join thousands of satisfied 
                    customers who have already made the switch. Try it free for 30 days!
                    """
                }
            ),
        ]
        
        print(f"\n✓ Created {len(documents)} documents for translation")
        
        # Process all documents
        result = await pipeline_executor.execute(documents)
        
        # Write results to output folder
        output_folder = Path(__file__).parent / "output"
        output_folder.mkdir(exist_ok=True)
        output_file = output_folder / "translation_result.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(result.model_dump_json(indent=2))
        print(f"  Wrote output to {output_file}")
        
        # Analyze results
        successful = sum(1 for d in result.documents if d.get_status() == "completed") if isinstance(result.documents, list) else result.documents.get_status() == "completed"
        failed = sum(1 for d in result.documents if d.get_status() == "failed") if isinstance(result.documents, list) else result.documents.get_status() == "failed"
        total_duration = result.duration_seconds
        
        print(f"\n✓ Translation processing completed")
        print(f"  Total documents: {len(result.documents) if isinstance(result.documents, list) else 1}")
        print(f"  Successful: {successful}")
        print(f"  Failed: {failed}")
        print(f"  Total duration: {total_duration:.2f}s")
        print(f"  Avg per document: {total_duration/(len(result.documents) if isinstance(result.documents, list) else 1):.2f}s")
        
        # Show translations
        if isinstance(result.documents, list) and len(result.documents) > 0:
            print(f"\n{'=' * 70}")
            print("TRANSLATIONS")
            print(f"{'=' * 70}")
            
            for i, doc in enumerate(result.documents):
                if 'translated_text' in doc.data:
                    print(f"\n📄 Document {i+1}: {doc.id.canonical_id}")
                    print(f"\n{'─' * 70}")
                    print(f"Original (English):")
                    print(f"{'─' * 70}")
                    print(doc.data['text'].strip())
                    print(f"\n{'─' * 70}")
                    print(f"Translation (Spanish):")
                    print(f"{'─' * 70}")
                    print(doc.data['translated_text'].strip())
                    print()
        
        print(f"{'=' * 70}")
        # Show processing events
        print(f"\n📊 Processing Events:")
        for i, event in enumerate(result.events):
            print(f"\n  Event {i+1}: {event.event_type}")
            print(f"    Executor: {event.executor_id}")
    
        print(f"\n{'=' * 70}")
        print(f"\n📁 Outputs written to: {output_file}\n")
    
    print("\n" + "=" * 70)
    print("Translation Run Complete!")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(run_pipeline())
