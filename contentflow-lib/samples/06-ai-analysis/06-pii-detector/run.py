"""
PII Detector Processing Example

Demonstrates using PII detector for identifying and redacting personally identifiable information with:
- PIIDetectorExecutor: Detect and redact PII using Azure OpenAI agent
- Configurable PII types (name, email, phone, SSN, credit card, address, etc.)
- Multiple actions (detect, redact, mask, label)
- Position tracking and confidence thresholds
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
    """Execute PII Detector pipeline"""
    
    print("=" * 70)
    print("PII DETECTOR EXECUTOR RUN")
    print("=" * 70)
    
    # Load config
    config_path = Path(__file__).parent / "pii_detector_config.yaml"
    executor_catalog_path = samples_dir.parent / "executor_catalog.yaml"
    
    async with PipelineExecutor.from_config_file(
        config_path=config_path,
        pipeline_name="pii_detector_pipeline",
        executor_catalog_path=executor_catalog_path,
    ) as pipeline_executor:
        
        print(f"\n✓ Initialized pipeline")
        
        # Create sample documents with text containing PII
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
                    Customer Support Ticket #12345
                    
                    Customer: John Smith
                    Email: john.smith@email.com
                    Phone: (555) 123-4567
                    SSN: 123-45-6789
                    
                    Issue: Need to update billing information for credit card ending in 4532.
                    Please send confirmation to the address on file: 123 Main Street, 
                    Springfield, IL 62701.
                    
                    Thank you for your assistance.
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
                    Employee Record Update
                    
                    Name: Sarah Johnson
                    Contact: sarah.j@company.com | Mobile: 555-987-6543
                    SSN: 987-65-4321
                    Address: 456 Oak Avenue, Apartment 2B, Boston, MA 02101
                    
                    Emergency Contact: Michael Johnson (spouse)
                    Phone: (555) 234-5678
                    
                    Please update payroll direct deposit to account ending in 7890.
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
                    This is a general business document discussing our company's 
                    expansion plans for 2024. We aim to open three new offices in 
                    major metropolitan areas and hire approximately 150 new employees. 
                    The project budget is estimated at $5 million over two years.
                    
                    No personal information is contained in this document.
                    """
                }
            ),
        ]
        
        print(f"\n✓ Created {len(documents)} documents for PII detection")
        
        # Process all documents
        result = await pipeline_executor.execute(documents)
        
        # write results to output folder
        output_folder = Path(__file__).parent / "output"
        output_folder.mkdir(exist_ok=True)
        output_file = output_folder / "pii_detection_result.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(result.model_dump_json(indent=2))
        print(f"  Wrote output to {output_file}")
        
        # Analyze results
        successful = sum(1 for d in result.documents if d.get_status() == "completed") if isinstance(result.documents, list) else result.documents.get_status() == "completed"
        failed = sum(1 for d in result.documents if d.get_status() == "failed") if isinstance(result.documents, list) else result.documents.get_status() == "failed"
        total_duration = result.duration_seconds
        
        print(f"\n✓ PII detection completed")
        print(f"  Total documents: {len(result.documents) if isinstance(result.documents, list) else 1}")
        print(f"  Successful: {successful}")
        print(f"  Failed: {failed}")
        print(f"  Total duration (seconds): {total_duration:.2f}s")
        print(f"  Avg per document: {total_duration/(len(result.documents) if isinstance(result.documents, list) else 1):.2f}s")
        
        # Show sample PII detection results
        if isinstance(result.documents, list) and len(result.documents) > 0:
            for i, doc in enumerate(result.documents):
                print(f"\n📄 Document {i+1} ({doc.id}):")
                
                # Show original text snippet
                original_text = doc.data.get('text', '')
                print(f"  Original text: {original_text[:150]}...")
                
                # Show PII detection results
                if 'pii_detected' in doc.data:
                    pii_data = doc.data['pii_detected']
                    if isinstance(pii_data, dict):
                        pii_count = pii_data.get('count', len(pii_data.get('pii_found', [])))
                        print(f"  PII Items Found: {pii_count}")
                        
                        if 'pii_found' in pii_data:
                            for pii_item in pii_data['pii_found'][:5]:  # Show first 5
                                pii_type = pii_item.get('type', 'unknown')
                                pii_value = pii_item.get('value', '')
                                confidence = pii_item.get('confidence', 0)
                                print(f"    - {pii_type}: {pii_value} (confidence: {confidence})")
                    else:
                        print(f"  PII Detection: {pii_data}")
                
                # Show redacted text if available
                if 'text_redacted' in doc.data:
                    redacted_text = doc.data['text_redacted']
                    print(f"  Redacted text: {redacted_text[:200]}...")
                
                # Show PII count from summary
                if 'pii_count' in doc.summary_data:
                    print(f"  Summary PII Count: {doc.summary_data['pii_count']}")
        
        # Show processing events
        print(f"\n📊 Processing Events:")
        for i, event in enumerate(result.events[:10]):  # Show first 10
            print(f"\n  Event {i+1}: {event.event_type}")
            print(f"    Executor: {event.executor_id}")

        print(f"\n{'=' * 70}")
        print(f"\n📁 Outputs written to: {output_file}\n")
        
    print("\n" + "=" * 70)
    print("PII Detector Run Complete!")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(run_pipeline())
