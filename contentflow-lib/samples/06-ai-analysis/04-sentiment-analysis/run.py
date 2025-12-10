"""
Sentiment Analysis Pipeline Example

Demonstrates using SentimentAnalysisExecutor for analyzing sentiment:
- Positive, Negative, Neutral classification
- Confidence scores
- Emotion detection
- Explanations for sentiment decisions
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
    """Execute Sentiment Analysis pipeline"""
    
    print("=" * 70)
    print("SENTIMENT ANALYSIS EXECUTOR RUN")
    print("=" * 70)
    
    # Load config
    config_path = Path(__file__).parent / "sentiment_analysis_config.yaml"
    executor_catalog_path = samples_dir.parent / "executor_catalog.yaml"
    
    async with PipelineExecutor.from_config_file(
        config_path=config_path,
        pipeline_name="sentiment_analysis_pipeline",
        executor_catalog_path=executor_catalog_path,
    ) as pipeline_executor:
        
        print(f"\n✓ Initialized sentiment analysis pipeline")
        
        # Create sample documents with different sentiments
        documents = [
            Content(
                id=ContentIdentifier(
                    canonical_id="review1",
                    unique_id="review1",
                    source_name="sample",
                    source_type="text",
                ),
                data={
                    "text": """
                    I absolutely love this product! The quality is outstanding and exceeded all my 
                    expectations. The customer service team was incredibly helpful and responsive. 
                    This is hands down the best purchase I've made this year. I'm thrilled with 
                    the results and would highly recommend it to anyone. Five stars all the way!
                    """
                }
            ),
            Content(
                id=ContentIdentifier(
                    canonical_id="review2",
                    unique_id="review2",
                    source_name="sample",
                    source_type="text",
                ),
                data={
                    "text": """
                    This was a complete waste of money. The product arrived damaged and customer 
                    service was unhelpful and rude. I'm extremely disappointed and frustrated with 
                    this entire experience. The quality is terrible and nothing like what was 
                    advertised. I would strongly advise against purchasing this. Very dissatisfied.
                    """
                }
            ),
            Content(
                id=ContentIdentifier(
                    canonical_id="review3",
                    unique_id="review3",
                    source_name="sample",
                    source_type="text",
                ),
                data={
                    "text": """
                    The product is decent and works as described. It meets basic requirements 
                    but nothing special. The price is reasonable for what you get. Delivery 
                    was on time. Overall, it's an acceptable purchase - not great, not terrible. 
                    It does the job adequately.
                    """
                }
            ),
            Content(
                id=ContentIdentifier(
                    canonical_id="review4",
                    unique_id="review4",
                    source_name="sample",
                    source_type="text",
                ),
                data={
                    "text": """
                    I had high hopes but ended up with mixed feelings. Some aspects are really 
                    good - the design is beautiful and it's easy to use. However, the performance 
                    is inconsistent and it crashes occasionally. The price seems a bit high for 
                    what you get. I'm somewhat satisfied but also somewhat disappointed.
                    """
                }
            ),
            Content(
                id=ContentIdentifier(
                    canonical_id="review5",
                    unique_id="review5",
                    source_name="sample",
                    source_type="text",
                ),
                data={
                    "text": """
                    Wow! This exceeded every expectation! I'm absolutely amazed by the innovation 
                    and attention to detail. The joy I feel using this product is indescribable. 
                    It brings a smile to my face every day. The team behind this deserves all 
                    the praise. This is pure excellence!
                    """
                }
            ),
        ]
        
        print(f"\n✓ Created {len(documents)} documents for sentiment analysis")
        
        # Process all documents
        result = await pipeline_executor.execute(documents)
        
        # Write results to output folder
        output_folder = Path(__file__).parent / "output"
        output_folder.mkdir(exist_ok=True)
        output_file = output_folder / "sentiment_analysis_result.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(result.model_dump_json(indent=2))
        print(f"  Wrote output to {output_file}")
        
        # Analyze results
        successful = sum(1 for d in result.documents if d.get_status() == "completed") if isinstance(result.documents, list) else result.documents.get_status() == "completed"
        failed = sum(1 for d in result.documents if d.get_status() == "failed") if isinstance(result.documents, list) else result.documents.get_status() == "failed"
        total_duration = result.duration_seconds
        
        print(f"\n✓ Sentiment analysis processing completed")
        print(f"  Total documents: {len(result.documents) if isinstance(result.documents, list) else 1}")
        print(f"  Successful: {successful}")
        print(f"  Failed: {failed}")
        print(f"  Total duration: {total_duration:.2f}s")
        print(f"  Avg per document: {total_duration/(len(result.documents) if isinstance(result.documents, list) else 1):.2f}s")
        
        # Show sentiment analysis results
        if isinstance(result.documents, list) and len(result.documents) > 0:
            print(f"\n{'=' * 70}")
            print("SENTIMENT ANALYSIS RESULTS")
            print(f"{'=' * 70}")
            
            for i, doc in enumerate(result.documents):
                if 'sentiment' in doc.data:
                    print(f"\n📄 Document {i+1}: {doc.id.canonical_id}")
                    print(f"\n{'─' * 70}")
                    print(f"Text ({len(doc.data['text'])} chars):")
                    print(f"{'─' * 70}")
                    print(doc.data['text'].strip()[:120] + "...")
                    print(f"\n{'─' * 70}")
                    print(f"Sentiment Analysis:")
                    print(f"{'─' * 70}")
                    
                    sentiment = doc.data['sentiment']
                    if isinstance(sentiment, dict):
                        # Display main sentiment
                        if 'sentiment' in sentiment:
                            sentiment_value = sentiment['sentiment']
                            # Add emoji based on sentiment
                            emoji = {
                                'positive': '😊',
                                'very positive': '🤩',
                                'negative': '😞',
                                'very negative': '😡',
                                'neutral': '😐'
                            }.get(sentiment_value.lower(), '📊')
                            print(f"\n  Sentiment: {emoji} {sentiment_value.upper()}")
                        
                        # Display confidence
                        if 'confidence' in sentiment:
                            confidence = sentiment['confidence']
                            bar_length = int(confidence * 20)
                            bar = '█' * bar_length + '░' * (20 - bar_length)
                            print(f"  Confidence: {bar} {confidence:.2%}")
                        
                        # Display emotions
                        if 'emotions' in sentiment and sentiment['emotions']:
                            emotions = sentiment['emotions']
                            if isinstance(emotions, list):
                                print(f"  Emotions: {', '.join(emotions)}")
                            else:
                                print(f"  Emotions: {emotions}")
                        
                        # Display explanation
                        if 'explanation' in sentiment:
                            print(f"  Explanation: {sentiment['explanation']}")
                    else:
                        print(f"  {sentiment}")
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
    print("Sentiment Analysis Run Complete!")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(run_pipeline())
