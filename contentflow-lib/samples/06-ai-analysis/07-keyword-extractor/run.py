"""
Keyword Extractor Processing Example

Demonstrates using keyword extractor for identifying important terms and phrases with:
- KeywordExtractorExecutor: Extract keywords and key phrases using Azure OpenAI agent
- Configurable keyword types (single words, phrases, or both)
- Relevance scoring and ranking methods
- Topic extraction
- Context-aware phrase detection
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
    """Execute Keyword Extractor pipeline"""
    
    print("=" * 70)
    print("KEYWORD EXTRACTOR EXECUTOR RUN")
    print("=" * 70)
    
    # Load config
    config_path = Path(__file__).parent / "keyword_extractor_config.yaml"
    executor_catalog_path = samples_dir.parent / "executor_catalog.yaml"
    
    async with PipelineExecutor.from_config_file(
        config_path=config_path,
        pipeline_name="keyword_extractor_pipeline",
        executor_catalog_path=executor_catalog_path,
    ) as pipeline_executor:
        
        print(f"\n✓ Initialized pipeline")
        
        # Create sample documents with diverse content
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
                    Artificial Intelligence and Machine Learning in Healthcare
                    
                    The integration of artificial intelligence (AI) and machine learning (ML) 
                    technologies in healthcare is revolutionizing patient care and medical research. 
                    Deep learning algorithms can now detect diseases from medical imaging with 
                    accuracy rivaling human experts. Natural language processing helps analyze 
                    electronic health records to identify patterns and predict patient outcomes.
                    
                    Predictive analytics powered by AI enable early detection of conditions like 
                    sepsis and heart failure. Robotic surgery systems enhance precision and reduce 
                    recovery times. Drug discovery processes are accelerated through computational 
                    models that can screen millions of compounds. The future of personalized 
                    medicine relies heavily on AI-driven genomic analysis and treatment optimization.
                    
                    However, challenges remain around data privacy, algorithmic bias, regulatory 
                    approval, and integration with existing healthcare infrastructure. Ensuring 
                    ethical AI deployment while maintaining patient trust is paramount.
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
                    Sustainable Energy Solutions for Urban Development
                    
                    Cities worldwide are embracing renewable energy and green building practices 
                    to combat climate change and reduce carbon emissions. Solar panels and wind 
                    turbines are becoming common sights in urban landscapes. Smart grid technology 
                    optimizes energy distribution and reduces waste through real-time monitoring 
                    and automated load balancing.
                    
                    Electric vehicle infrastructure, including charging stations and battery swap 
                    facilities, is expanding rapidly. Green roofs and vertical gardens improve 
                    air quality while reducing urban heat islands. Energy-efficient buildings 
                    incorporate advanced insulation, LED lighting, and intelligent HVAC systems 
                    that adapt to occupancy patterns.
                    
                    District heating and cooling systems powered by geothermal energy provide 
                    sustainable temperature regulation. Waste-to-energy plants convert municipal 
                    solid waste into electricity. The circular economy approach minimizes resource 
                    consumption through recycling and upcycling initiatives. Investment in these 
                    sustainable technologies creates jobs while protecting the environment.
                    """
                }
            ),
            Content(
                id=ContentIdentifier(
                    canonical_id="doc3",
                    unique_id="doc3",
                    source_name="sample",
                    source_type="text",
                ),
                data={
                    "text": """
                    The Evolution of Remote Work and Digital Collaboration
                    
                    The COVID-19 pandemic accelerated the shift toward remote work, transforming 
                    how organizations operate globally. Video conferencing platforms like Zoom 
                    and Microsoft Teams became essential tools for maintaining business continuity. 
                    Cloud-based collaboration software enables teams to work together seamlessly 
                    across time zones and geographic boundaries.
                    
                    Companies are adopting hybrid work models that balance flexibility with 
                    in-person collaboration. Virtual reality meetings and augmented reality 
                    workspaces are emerging as next-generation communication tools. Project 
                    management platforms help track progress and maintain accountability in 
                    distributed teams.
                    
                    Cybersecurity concerns have increased with remote access to corporate networks. 
                    Employee wellbeing programs address isolation and work-life balance challenges. 
                    Digital nomad visas allow professionals to work from anywhere. The future 
                    workplace will likely be more flexible, technology-enabled, and focused on 
                    outcomes rather than physical presence.
                    """
                }
            ),
        ]
        
        print(f"\n✓ Created {len(documents)} documents for keyword extraction")
        
        # Process all documents
        result = await pipeline_executor.execute(documents)
        
        # write results to output folder
        output_folder = Path(__file__).parent / "output"
        output_folder.mkdir(exist_ok=True)
        output_file = output_folder / "keyword_extractor_result.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(result.model_dump_json(indent=2))
        print(f"  Wrote output to {output_file}")
        
        # Analyze results
        successful = sum(1 for d in result.documents if d.get_status() == "completed") if isinstance(result.documents, list) else result.documents.get_status() == "completed"
        failed = sum(1 for d in result.documents if d.get_status() == "failed") if isinstance(result.documents, list) else result.documents.get_status() == "failed"
        total_duration = result.duration_seconds
        
        print(f"\n✓ Keyword extraction completed")
        print(f"  Total documents: {len(result.documents) if isinstance(result.documents, list) else 1}")
        print(f"  Successful: {successful}")
        print(f"  Failed: {failed}")
        print(f"  Total duration (seconds): {total_duration:.2f}s")
        print(f"  Avg per document: {total_duration/(len(result.documents) if isinstance(result.documents, list) else 1):.2f}s")
        
        # Show sample keyword extraction results
        if isinstance(result.documents, list) and len(result.documents) > 0:
            for i, doc in enumerate(result.documents):
                print(f"\n📄 Document {i+1} ({doc.id}):")
                
                # Show original text snippet
                original_text = doc.data.get('text', '')
                # Get first line as title
                first_line = original_text.strip().split('\n')[0].strip()
                print(f"  Title: {first_line}")
                
                # Show keyword extraction results
                if 'keywords' in doc.data:
                    keywords_data = doc.data['keywords']
                    if isinstance(keywords_data, dict):
                        # Show keywords
                        if 'keywords' in keywords_data:
                            keywords_list = keywords_data['keywords']
                            keyword_count = len(keywords_list) if isinstance(keywords_list, list) else 0
                            print(f"  Keywords Extracted: {keyword_count}")
                            
                            if isinstance(keywords_list, list):
                                print(f"  Top Keywords:")
                                for idx, kw in enumerate(keywords_list[:10], 1):  # Show top 10
                                    if isinstance(kw, dict):
                                        term = kw.get('term', '')
                                        score = kw.get('score', 0)
                                        print(f"    {idx}. {term} (score: {score:.2f})")
                                    elif isinstance(kw, str):
                                        print(f"    {idx}. {kw}")
                        
                        # Show topics if available
                        if 'topics' in keywords_data:
                            topics = keywords_data['topics']
                            if isinstance(topics, list) and topics:
                                print(f"  Main Topics: {', '.join(topics)}")
                    else:
                        print(f"  Keywords: {keywords_data}")
                
                # Show keyword count from summary
                if 'keyword_count' in doc.summary_data:
                    print(f"  Summary Keyword Count: {doc.summary_data['keyword_count']}")
        
        # Show processing events
        print(f"\n📊 Processing Events:")
        for i, event in enumerate(result.events[:10]):  # Show first 10
            print(f"\n  Event {i+1}: {event.event_type}")
            print(f"    Executor: {event.executor_id}")

        print(f"\n{'=' * 70}")
        print(f"\n📁 Outputs written to: {output_file}\n")
        
    print("\n" + "=" * 70)
    print("Keyword Extractor Run Complete!")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(run_pipeline())
