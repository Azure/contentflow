"""
Summarization Pipeline Example

Demonstrates using SummarizationExecutor for content summarization with:
- Configurable summary styles (brief, detailed, bullet points)
- Support for various content types
- Customizable length and format
"""

import asyncio
import logging
import sys
from pathlib import Path
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from samples.setup_logger import setup_logging
from packages.pipeline import PipelineExecutor
from packages.models import Content, ContentIdentifier

# Get the samples directory
samples_dir = Path(__file__).parent.parent.parent

# Load environment variables
load_dotenv(f'{samples_dir}/.env')

logger = logging.getLogger(__name__)

setup_logging()

async def run_pipeline():
    """Execute Summarization pipeline"""
    
    print("=" * 70)
    print("SUMMARIZATION EXECUTOR TEST")
    print("=" * 70)
    
    # Load config
    config_path = Path(__file__).parent / "summarization_config.yaml"
    executor_catalog_path = samples_dir.parent / "executor_catalog.yaml"
    
    async with PipelineExecutor.from_config_file(
        config_path=config_path,
        pipeline_name="summarization_pipeline",
        executor_catalog_path=executor_catalog_path,
    ) as pipeline_executor:
        
        print(f"\n✓ Initialized summarization pipeline")
        
        # Create sample documents with different types of content
        documents = [
            Content(
                id=ContentIdentifier(
                    canonical_id="article1",
                    unique_id="article1",
                    source_name="sample",
                    source_type="text",
                ),
                data={
                    "text": """
                    The global climate crisis continues to accelerate, with 2024 marking the warmest year 
                    on record according to international meteorological organizations. Average temperatures 
                    have risen by 1.5 degrees Celsius above pre-industrial levels, surpassing the critical 
                    threshold set by the Paris Agreement. Scientists warn that without immediate and 
                    substantial reductions in greenhouse gas emissions, the world faces catastrophic 
                    consequences including rising sea levels, extreme weather events, and widespread 
                    ecosystem collapse. Renewable energy adoption has increased significantly, with solar 
                    and wind power now accounting for 30% of global electricity generation. However, experts 
                    emphasize that the pace of transition must accelerate dramatically to meet climate goals. 
                    Governments and corporations are being urged to implement more aggressive policies and 
                    investments in clean energy infrastructure, carbon capture technologies, and sustainable 
                    practices across all sectors of the economy.
                    """
                }
            ),
            Content(
                id=ContentIdentifier(
                    canonical_id="article2",
                    unique_id="article2",
                    source_name="sample",
                    source_type="text",
                ),
                data={
                    "text": """
                    Quantum computing represents a paradigm shift in computational power and problem-solving 
                    capabilities. Unlike classical computers that use bits representing 0 or 1, quantum 
                    computers utilize qubits that can exist in multiple states simultaneously through 
                    superposition. This property, combined with quantum entanglement, enables quantum systems 
                    to process vast amounts of information in parallel. Recent breakthroughs have demonstrated 
                    quantum advantage in specific applications, including cryptography, drug discovery, and 
                    optimization problems. Major technology companies and research institutions have invested 
                    billions in developing stable quantum systems, though challenges remain in maintaining 
                    qubit coherence and reducing error rates. Experts predict that within the next decade, 
                    quantum computers will revolutionize fields such as materials science, financial modeling, 
                    and artificial intelligence, potentially solving problems that are intractable for even 
                    the most powerful classical supercomputers.
                    """
                }
            ),
            Content(
                id=ContentIdentifier(
                    canonical_id="article3",
                    unique_id="article3",
                    source_name="sample",
                    source_type="text",
                ),
                data={
                    "text": """
                    The Mediterranean diet has long been celebrated as one of the healthiest eating patterns 
                    in the world. Originating from countries bordering the Mediterranean Sea, this dietary 
                    approach emphasizes whole grains, fresh fruits and vegetables, legumes, nuts, olive oil, 
                    and moderate amounts of fish and poultry. Red meat and processed foods are consumed 
                    sparingly. Numerous scientific studies have linked the Mediterranean diet to reduced 
                    risks of heart disease, stroke, type 2 diabetes, and certain cancers. The diet is rich 
                    in antioxidants, healthy fats, and fiber while being low in saturated fats and refined 
                    sugars. Beyond physical health benefits, research suggests that adherence to this eating 
                    pattern may also support cognitive function and reduce the risk of neurodegenerative 
                    diseases like Alzheimer's. The social aspect of Mediterranean eating culture, which 
                    emphasizes shared meals and mindful eating, contributes to overall well-being and longevity.
                    """
                }
            ),
        ]
        
        print(f"\n✓ Created {len(documents)} documents for summarization")
        
        # Process all documents
        result = await pipeline_executor.execute(documents)
        
        # Write results to output folder
        output_folder = Path(__file__).parent / "output"
        output_folder.mkdir(exist_ok=True)
        output_file = output_folder / "summarization_result.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(result.model_dump_json(indent=2))
        print(f"  Wrote output to {output_file}")
        
        # Analyze results
        successful = sum(1 for d in result.documents if d.get_status() == "completed") if isinstance(result.documents, list) else result.documents.get_status() == "completed"
        failed = sum(1 for d in result.documents if d.get_status() == "failed") if isinstance(result.documents, list) else result.documents.get_status() == "failed"
        total_duration = result.duration_seconds
        
        print(f"\n✓ Summarization processing completed")
        print(f"  Total documents: {len(result.documents) if isinstance(result.documents, list) else 1}")
        print(f"  Successful: {successful}")
        print(f"  Failed: {failed}")
        print(f"  Total duration: {total_duration:.2f}s")
        print(f"  Avg per document: {total_duration/(len(result.documents) if isinstance(result.documents, list) else 1):.2f}s")
        
        # Show summaries with different styles
        if isinstance(result.documents, list) and len(result.documents) > 0:
            print(f"\n{'=' * 70}")
            print("GENERATED SUMMARIES")
            print(f"{'=' * 70}")
            
            for i, doc in enumerate(result.documents):
                if 'summary' in doc.data:
                    print(f"\n📄 Document {i+1}: {doc.id.canonical_id}")
                    print(f"\n{'─' * 70}")
                    print(f"Original Text ({len(doc.data['text'])} chars):")
                    print(f"{'─' * 70}")
                    print(doc.data['text'].strip()[:200] + "...")
                    print(f"\n{'─' * 70}")
                    print(f"Summary:")
                    print(f"{'─' * 70}")
                    print(doc.data['summary'])
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
    print("Summarization Run Complete!")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(run_pipeline())
