"""
Entity Extraction Pipeline Example

Demonstrates using EntityExtractionExecutor for extracting named entities:
- Organizations, People, Locations, Dates, Monetary values
- Customizable entity types
- Context extraction for each entity
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
    """Execute Entity Extraction pipeline"""
    
    print("=" * 70)
    print("ENTITY EXTRACTION EXECUTOR RUN")
    print("=" * 70)
    
    # Load config
    config_path = Path(__file__).parent / "entity_extraction_config.yaml"
    executor_catalog_path = samples_dir.parent / "executor_catalog.yaml"
    
    async with PipelineExecutor.from_config_file(
        config_path=config_path,
        pipeline_name="entity_extraction_pipeline",
        executor_catalog_path=executor_catalog_path,
    ) as pipeline_executor:
        
        print(f"\n✓ Initialized entity extraction pipeline")
        
        # Create sample documents with rich entity content
        documents = [
            Content(
                id=ContentIdentifier(
                    canonical_id="news1",
                    unique_id="news1",
                    source_name="sample",
                    source_type="text",
                ),
                data={
                    "text": """
                    Apple Inc. CEO Tim Cook announced a new partnership with Microsoft Corporation 
                    during a press conference in Cupertino, California on December 15, 2024. The 
                    collaboration will focus on integrating Apple's hardware innovations with 
                    Microsoft's cloud services, particularly Azure. The deal, valued at $2.5 billion, 
                    is expected to be finalized by January 2025. Industry analysts from Goldman Sachs 
                    and Morgan Stanley predict this partnership could generate over $10 billion in 
                    revenue over the next five years. Dr. Sarah Chen, Chief Technology Officer at 
                    Apple, will lead the integration team. Contact information can be found at 
                    partnerships@apple.com or call +1-408-996-1010.
                    """
                }
            ),
            Content(
                id=ContentIdentifier(
                    canonical_id="news2",
                    unique_id="news2",
                    source_name="sample",
                    source_type="text",
                ),
                data={
                    "text": """
                    The European Union announced new climate regulations at the COP29 summit in 
                    Dubai, United Arab Emirates. European Commission President Ursula von der Leyen 
                    stated that member states must reduce carbon emissions by 55% by 2030. Germany, 
                    France, and Italy have committed €500 million collectively to renewable energy 
                    projects. The agreement was signed on November 30, 2024, with implementation 
                    beginning on March 1, 2025. Environmental activist Greta Thunberg praised the 
                    initiative but called for more aggressive targets. The World Wildlife Fund and 
                    Greenpeace International endorsed the plan. For more details, visit 
                    www.ec.europa.eu/climate or email climate-action@ec.europa.eu.
                    """
                }
            ),
            Content(
                id=ContentIdentifier(
                    canonical_id="news3",
                    unique_id="news3",
                    source_name="sample",
                    source_type="text",
                ),
                data={
                    "text": """
                    Amazon.com announced the acquisition of Whole Foods Market competitor Fresh & Co. 
                    for $3.8 billion. The transaction, approved by the Federal Trade Commission, was 
                    completed on October 12, 2024. Amazon CEO Andy Jassy stated the acquisition will 
                    expand Amazon's presence in New York, Los Angeles, and Chicago. JPMorgan Chase 
                    served as financial advisor. The deal includes 127 stores across 15 states. 
                    Elizabeth Warren, U.S. Senator from Massachusetts, raised antitrust concerns. 
                    Trading on NASDAQ under ticker AMZN reached an all-time high of $185.50 per share. 
                    Shareholders can reach investor relations at ir@amazon.com or 1-800-123-4567.
                    """
                }
            ),
        ]
        
        print(f"\n✓ Created {len(documents)} documents for entity extraction")
        
        # Process all documents
        result = await pipeline_executor.execute(documents)
        
        # Write results to output folder
        output_folder = Path(__file__).parent / "output"
        output_folder.mkdir(exist_ok=True)
        output_file = output_folder / "entity_extraction_result.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(result.model_dump_json(indent=2))
        print(f"  Wrote output to {output_file}")
        
        # Analyze results
        successful = sum(1 for d in result.documents if d.get_status() == "completed") if isinstance(result.documents, list) else result.documents.get_status() == "completed"
        failed = sum(1 for d in result.documents if d.get_status() == "failed") if isinstance(result.documents, list) else result.documents.get_status() == "failed"
        total_duration = result.duration_seconds
        
        print(f"\n✓ Entity extraction processing completed")
        print(f"  Total documents: {len(result.documents) if isinstance(result.documents, list) else 1}")
        print(f"  Successful: {successful}")
        print(f"  Failed: {failed}")
        print(f"  Total duration: {total_duration:.2f}s")
        print(f"  Avg per document: {total_duration/(len(result.documents) if isinstance(result.documents, list) else 1):.2f}s")
        
        # Show extracted entities
        if isinstance(result.documents, list) and len(result.documents) > 0:
            print(f"\n{'=' * 70}")
            print("EXTRACTED ENTITIES")
            print(f"{'=' * 70}")
            
            for i, doc in enumerate(result.documents):
                if 'entities' in doc.data:
                    print(f"\n📄 Document {i+1}: {doc.id.canonical_id}")
                    print(f"\n{'─' * 70}")
                    print(f"Original Text ({len(doc.data['text'])} chars):")
                    print(f"{'─' * 70}")
                    print(doc.data['text'].strip()[:150] + "...")
                    print(f"\n{'─' * 70}")
                    print(f"Extracted Entities:")
                    print(f"{'─' * 70}")
                    
                    entities = doc.data['entities']
                    if isinstance(entities, dict):
                        for entity_type, entity_list in entities.items():
                            if entity_list:
                                print(f"\n  {entity_type.upper()}:")
                                if isinstance(entity_list, list):
                                    for entity in entity_list:
                                        if isinstance(entity, dict):
                                            print(f"    • {entity.get('text', entity)}")
                                            if 'context' in entity:
                                                print(f"      Context: \"{entity['context']}\"")
                                        else:
                                            print(f"    • {entity}")
                    else:
                        print(f"  {entities}")
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
    print("Entity Extraction Run Complete!")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(run_pipeline())
