"""
AI Agent Processing Example

Demonstrates using AI agent for content processing with:
- AIAgentExecutor: Process content using Azure OpenAI agent from agent-framework
- Configurable instructions and settings
- Support for both simple queries and conversation history
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
    """Execute AI Agent pipeline"""
    
    print("=" * 70)
    print("AI AGENT EXECUTOR RUN")
    print("=" * 70)
    
    # Load config
    config_path = Path(__file__).parent / "pipeline_config.yaml"
    executor_catalog_path = samples_dir.parent / "executor_catalog.yaml"
    
    async with PipelineExecutor.from_config_file(
        config_path=config_path,
        pipeline_name="ai_agent_pipeline",
        executor_catalog_path=executor_catalog_path,
    ) as pipeline_executor:
        
        print(f"\n✓ Initialized pipeline")
        
        # Create sample documents with text to process
        documents = [
            Content(
                id=ContentIdentifier(
                    canonical_id="doc1",
                    unique_id="doc1",
                    source_name="sample",
                    source_type="text",
                ),
                data={
                    "text": """
                    Artificial Intelligence (AI) is transforming how we work and live. 
                    From healthcare to transportation, AI systems are being deployed to 
                    solve complex problems. Machine learning, a subset of AI, enables 
                    computers to learn from data without explicit programming. Deep 
                    learning, using neural networks, has achieved remarkable results in 
                    image recognition, natural language processing, and game playing.
                    """
                }
            ),
            Content(
                id=ContentIdentifier(
                    canonical_id="doc2",
                    unique_id="doc2",
                    source_name="sample",
                    source_type="text",
                ),
                data={
                    "text": """
                    Cloud computing has revolutionized IT infrastructure. Organizations 
                    can now scale resources on-demand, reducing capital expenses and 
                    improving flexibility. Major cloud providers offer services ranging 
                    from basic storage to advanced AI and machine learning capabilities. 
                    Hybrid and multi-cloud strategies are becoming increasingly popular 
                    as businesses seek to avoid vendor lock-in and optimize costs.
                    """
                }
            ),
        ]
        
        print(f"\n✓ Created {len(documents)} documents for AI agent processing")
        
        # Process all documents
        result = await pipeline_executor.execute(documents)
        
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
        
        print(f"\n✓ AI agent processing completed")
        print(f"  Total documents: {len(result.documents) if isinstance(result.documents, list) else 1}")
        print(f"  Successful: {successful}")
        print(f"  Failed: {failed}")
        print(f"  Total duration (seconds): {total_duration:.2f}s")
        print(f"  Avg per document: {total_duration/(len(result.documents) if isinstance(result.documents, list) else 1):.2f}s")
        
        # Show sample agent responses
        if isinstance(result.documents, list) and len(result.documents) > 0:
            for i, doc in enumerate(result.documents[:2]):  # Show first 2
                if 'summary' in doc.data:
                    print(f"\n📄 Document {i+1} ({doc.id}):")
                    print(f"  Original text: {doc.data['text'][:100]}...")
                    print(f"  AI Summary: {doc.data['summary']}")
        
        # Show processing events
        print(f"\n📊 Processing Events:")
        for i, event in enumerate(result.events):
            print(f"\n  Event {i+1}: {event.event_type}")
            print(f"    Executor: {event.executor_id}")

        print(f"\n{'=' * 70}")
        print(f"\n📁 Outputs written to: {output_file}\n")
        
    print("\n" + "=" * 70)
    print("AI Agent Run Complete!")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(run_pipeline())
