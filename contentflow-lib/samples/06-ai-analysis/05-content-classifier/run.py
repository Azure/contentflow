"""
Content Classifier Pipeline Example

Demonstrates using ContentClassifierExecutor for categorizing content:
- Multi-category classification (Technology, Business, Science, etc.)
- Confidence scores
- Explanations for classifications
- Category distribution analysis
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
    """Execute Content Classifier pipeline"""
    
    print("=" * 70)
    print("CONTENT CLASSIFIER EXECUTOR RUN")
    print("=" * 70)
    
    # Load config
    config_path = Path(__file__).parent / "content_classifier_config.yaml"
    executor_catalog_path = samples_dir.parent / "executor_catalog.yaml"
    
    async with PipelineExecutor.from_config_file(
        config_path=config_path,
        pipeline_name="content_classifier_pipeline",
        executor_catalog_path=executor_catalog_path,
    ) as pipeline_executor:
        
        print(f"\n✓ Initialized content classifier pipeline")
        
        # Create sample documents from different categories
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
                    Apple's new Vision Pro headset has revolutionized augmented reality computing. 
                    The device features advanced spatial computing capabilities with dual 4K displays, 
                    eye-tracking technology, and seamless integration with the Apple ecosystem. Developers 
                    are already building innovative applications using visionOS, Apple's new spatial 
                    operating system. The headset uses advanced machine learning algorithms to understand 
                    hand gestures and create immersive 3D experiences. Tech analysts predict this could 
                    be the beginning of a new era in human-computer interaction.
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
                    The Federal Reserve announced an interest rate cut of 0.25% in response to slowing 
                    economic growth. Wall Street responded positively with the Dow Jones rising 2.3% and 
                    the S&P 500 gaining 1.8%. Market analysts from Goldman Sachs and JPMorgan predict 
                    this could signal the end of the rate-hiking cycle. Corporate earnings reports from 
                    major companies show mixed results, with tech sector outperforming traditional 
                    industries. Investors are closely watching inflation data and unemployment figures 
                    for signs of economic stability.
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
                    NASA's James Webb Space Telescope has discovered seven Earth-sized exoplanets orbiting 
                    a distant star in the TRAPPIST-1 system. Three of these planets are located in the 
                    habitable zone where liquid water could exist. Spectroscopic analysis reveals 
                    atmospheric compositions similar to Earth's early atmosphere. Scientists are excited 
                    about the potential for finding biosignatures - chemical indicators of life. This 
                    discovery represents a major breakthrough in the search for extraterrestrial life and 
                    planetary science research.
                    """
                }
            ),
            Content(
                id=ContentIdentifier(
                    canonical_id="article4",
                    unique_id="article4",
                    source_name="sample",
                    source_type="text",
                ),
                data={
                    "text": """
                    Taylor Swift's Eras Tour has become the highest-grossing concert tour of all time, 
                    surpassing $2 billion in revenue. The tour, spanning 152 shows across five continents, 
                    has broken attendance records worldwide. The concert film released in theaters earned 
                    over $250 million globally. Music industry experts credit Swift's dedicated fanbase 
                    and innovative marketing strategies. The tour has also had significant economic impact 
                    on host cities, with local businesses reporting record sales during concert weekends.
                    """
                }
            ),
            Content(
                id=ContentIdentifier(
                    canonical_id="article5",
                    unique_id="article5",
                    source_name="sample",
                    source_type="text",
                ),
                data={
                    "text": """
                    The Los Angeles Lakers defeated the Boston Celtics 118-109 in a thrilling NBA playoff 
                    game. LeBron James led the Lakers with 35 points, 12 rebounds, and 8 assists in a 
                    dominant performance. The victory gives the Lakers a 3-2 series lead heading into 
                    Game 6. Anthony Davis contributed 28 points and 15 rebounds, while the Celtics struggled 
                    with three-point shooting, making only 28% of their attempts. Fans packed the Crypto.com 
                    Arena in what many are calling one of the most exciting playoff series in recent years.
                    """
                }
            ),
            Content(
                id=ContentIdentifier(
                    canonical_id="article6",
                    unique_id="article6",
                    source_name="sample",
                    source_type="text",
                ),
                data={
                    "text": """
                    The United Nations climate summit concluded with 196 nations agreeing to accelerate 
                    the transition away from fossil fuels. World leaders committed to tripling renewable 
                    energy capacity by 2030 and phasing out coal power plants. The agreement includes 
                    $100 billion in annual climate finance for developing countries. Environmental groups 
                    praised the historic accord while noting implementation challenges. Political tensions 
                    between major economies complicated negotiations, but diplomats eventually reached 
                    consensus on emission reduction targets.
                    """
                }
            ),
            Content(
                id=ContentIdentifier(
                    canonical_id="article7",
                    unique_id="article7",
                    source_name="sample",
                    source_type="text",
                ),
                data={
                    "text": """
                    Breakthrough mRNA cancer vaccine shows 89% success rate in clinical trials. The vaccine, 
                    developed by researchers at Johns Hopkins Medical Center, trains the immune system to 
                    recognize and attack melanoma cancer cells. Patients who received the treatment showed 
                    significantly improved survival rates compared to traditional chemotherapy. The FDA has 
                    fast-tracked approval for Phase III trials. Medical experts believe this technology 
                    could revolutionize cancer treatment and be adapted for other types of cancer.
                    """
                }
            ),
            Content(
                id=ContentIdentifier(
                    canonical_id="article8",
                    unique_id="article8",
                    source_name="sample",
                    source_type="text",
                ),
                data={
                    "text": """
                    Harvard University announces largest financial aid expansion in its history, making 
                    education free for families earning under $85,000 annually. The initiative, funded by 
                    a $15 billion endowment allocation, will benefit over 25% of the undergraduate student 
                    body. University officials aim to increase access to higher education and reduce student 
                    debt burden. Other Ivy League institutions are expected to follow with similar programs. 
                    Education policy experts view this as a potential model for addressing college affordability 
                    nationwide.
                    """
                }
            ),
        ]
        
        print(f"\n✓ Created {len(documents)} documents for classification")
        
        # Process all documents
        result = await pipeline_executor.execute(documents)
        
        # Write results to output folder
        output_folder = Path(__file__).parent / "output"
        output_folder.mkdir(exist_ok=True)
        output_file = output_folder / "content_classifier_result.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(result.model_dump_json(indent=2))
        print(f"  Wrote output to {output_file}")
        
        # Analyze results
        successful = sum(1 for d in result.content if d.get_status() == "completed") if isinstance(result.content, list) else result.content.get_status() == "completed"
        failed = sum(1 for d in result.content if d.get_status() == "failed") if isinstance(result.content, list) else result.content.get_status() == "failed"
        total_duration = result.duration_seconds
        
        print(f"\n✓ Content classification processing completed")
        print(f"  Total documents: {len(result.content) if isinstance(result.content, list) else 1}")
        print(f"  Successful: {successful}")
        print(f"  Failed: {failed}")
        print(f"  Total duration: {total_duration:.2f}s")
        print(f"  Avg per document: {total_duration/(len(result.content) if isinstance(result.content, list) else 1):.2f}s")
        
        # Show classification results with visual indicators
        if isinstance(result.content, list) and len(result.content) > 0:
            print(f"\n{'=' * 70}")
            print("CLASSIFICATION RESULTS")
            print(f"{'=' * 70}")
            
            # Category icons
            category_icons = {
                'Technology': '💻',
                'Business': '💼',
                'Science': '🔬',
                'Entertainment': '🎬',
                'Sports': '⚽',
                'Politics': '🏛️',
                'Health': '⚕️',
                'Education': '🎓'
            }
            
            # Count classifications by category
            category_counts = {}
            
            for i, doc in enumerate(result.content):
                if 'classification' in doc.data:
                    print(f"\n📄 Document {i+1}: {doc.id.canonical_id}")
                    print(f"\n{'─' * 70}")
                    print(f"Text ({len(doc.data['text'])} chars):")
                    print(f"{'─' * 70}")
                    print(doc.data['text'].strip()[:120] + "...")
                    print(f"\n{'─' * 70}")
                    print(f"Classification:")
                    print(f"{'─' * 70}")
                    
                    classification = doc.data['classification']
                    if isinstance(classification, dict):
                        # Single-label classification
                        if 'category' in classification:
                            category = classification['category']
                            icon = category_icons.get(category, '📊')
                            print(f"\n  Category: {icon} {category.upper()}")
                            
                            # Track counts
                            category_counts[category] = category_counts.get(category, 0) + 1
                        
                        # Display confidence
                        if 'confidence' in classification:
                            confidence = classification['confidence']
                            bar_length = int(confidence * 20)
                            bar = '█' * bar_length + '░' * (20 - bar_length)
                            print(f"  Confidence: {bar} {confidence:.2%}")
                        
                        # Display explanation
                        if 'explanation' in classification:
                            print(f"  Explanation: {classification['explanation']}")
                    else:
                        print(f"  {classification}")
                    print()
            
            # Show category distribution
            if category_counts:
                print(f"\n{'=' * 70}")
                print("CATEGORY DISTRIBUTION")
                print(f"{'=' * 70}\n")
                
                max_count = max(category_counts.values())
                for category, count in sorted(category_counts.items(), key=lambda x: x[1], reverse=True):
                    icon = category_icons.get(category, '📊')
                    bar_length = int((count / max_count) * 30)
                    bar = '█' * bar_length
                    print(f"  {icon} {category:15s} {bar} ({count})")
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
    print("Content Classification Run Complete!")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(run_pipeline())
