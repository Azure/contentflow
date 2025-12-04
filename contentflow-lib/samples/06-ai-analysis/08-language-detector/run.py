"""
Language Detection Pipeline Example

Demonstrates using LanguageDetectorExecutor for detecting languages in text with:
- Single or multiple language detection
- Confidence scores
- Optional script and dialect detection
- Configurable ISO format (ISO 639-1, ISO 639-3, or full names)
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
    """Execute Language Detection pipeline"""
    
    print("=" * 70)
    print("LANGUAGE DETECTION EXECUTOR RUN")
    print("=" * 70)
    
    # Load config
    config_path = Path(__file__).parent / "language_detector_config.yaml"
    executor_catalog_path = Path(__file__).parent.parent.parent.parent / "executor_catalog.yaml"
    
    async with PipelineExecutor.from_config_file(
        config_path=config_path,
        pipeline_name="language_detector_pipeline",
        executor_catalog_path=executor_catalog_path,
    ) as pipeline:
        
        print(f"\n✓ Initialized language detection pipeline")
        
        # Create sample documents with different languages
        documents = [
            Content(
                id=ContentIdentifier(
                    canonical_id="english_text",
                    unique_id="english_text",
                    source_name="sample",
                    source_type="text",
                ),
                data={
                    "text": """
                    Artificial intelligence is transforming the way we live and work. Machine learning 
                    algorithms can now process vast amounts of data to identify patterns and make 
                    predictions that would be impossible for humans to detect manually.
                    """
                }
            ),
            Content(
                id=ContentIdentifier(
                    canonical_id="spanish_text",
                    unique_id="spanish_text",
                    source_name="sample",
                    source_type="text",
                ),
                data={
                    "text": """
                    La inteligencia artificial está transformando la forma en que vivimos y trabajamos. 
                    Los algoritmos de aprendizaje automático ahora pueden procesar grandes cantidades 
                    de datos para identificar patrones y hacer predicciones que serían imposibles de 
                    detectar manualmente para los humanos.
                    """
                }
            ),
            Content(
                id=ContentIdentifier(
                    canonical_id="french_text",
                    unique_id="french_text",
                    source_name="sample",
                    source_type="text",
                ),
                data={
                    "text": """
                    L'intelligence artificielle transforme notre façon de vivre et de travailler. Les 
                    algorithmes d'apprentissage automatique peuvent désormais traiter de grandes 
                    quantités de données pour identifier des modèles et faire des prédictions qu'il 
                    serait impossible pour les humains de détecter manuellement.
                    """
                }
            ),
            Content(
                id=ContentIdentifier(
                    canonical_id="mixed_language",
                    unique_id="mixed_language",
                    source_name="sample",
                    source_type="text",
                ),
                data={
                    "text": """
                    This is an English sentence. Esta es una oración en español. Ceci est une phrase 
                    en français. Multilingual text can be challenging to process.
                    """
                }
            ),
            Content(
                id=ContentIdentifier(
                    canonical_id="japanese_text",
                    unique_id="japanese_text",
                    source_name="sample",
                    source_type="text",
                ),
                data={
                    "text": """
                    人工知能は私たちの生活と仕事の方法を変えています。機械学習アルゴリズムは、
                    人間が手動で検出することが不可能なパターンを識別し、予測を行うために、
                    膨大な量のデータを処理できるようになりました。
                    """
                }
            ),
            Content(
                id=ContentIdentifier(
                    canonical_id="arabic_text",
                    unique_id="arabic_text",
                    source_name="sample",
                    source_type="text",
                ),
                data={
                    "text": """
                    الذكاء الاصطناعي يغير الطريقة التي نعيش ونعمل بها. يمكن لخوارزميات التعلم 
                    الآلي الآن معالجة كميات هائلة من البيانات لتحديد الأنماط وإجراء تنبؤات 
                    يستحيل على البشر اكتشافها يدويًا.
                    """
                }
            ),
        ]
        
        print(f"\n✓ Created {len(documents)} documents for language detection")
        
        # Process all documents
        result = await pipeline.execute(documents)
        
        # Write results to output folder
        output_folder = Path(__file__).parent / "output"
        output_folder.mkdir(exist_ok=True)
        output_file = output_folder / "language_detection_result.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(result.model_dump_json(indent=2))
        print(f"  Wrote output to {output_file}")
        
        # Analyze results
        successful = sum(1 for d in result.documents if d.get_status() == "completed") if isinstance(result.documents, list) else result.documents.get_status() == "completed"
        failed = sum(1 for d in result.documents if d.get_status() == "failed") if isinstance(result.documents, list) else result.documents.get_status() == "failed"
        total_duration = result.duration_seconds
        
        print(f"\n✓ Language detection processing completed")
        print(f"  Total documents: {len(result.documents) if isinstance(result.documents, list) else 1}")
        print(f"  Successful: {successful}")
        print(f"  Failed: {failed}")
        print(f"  Total duration: {total_duration:.2f}s")
        print(f"  Avg per document: {total_duration/(len(result.documents) if isinstance(result.documents, list) else 1):.2f}s")
        
        # Show detected languages
        if isinstance(result.documents, list) and len(result.documents) > 0:
            print(f"\n{'=' * 70}")
            print("DETECTED LANGUAGES")
            print(f"{'=' * 70}")
            
            for i, doc in enumerate(result.documents):
                if 'language' in doc.data:
                    print(f"\n📄 Document {i+1}: {doc.id.canonical_id}")
                    print(f"\n{'─' * 70}")
                    print(f"Text Sample:")
                    print(f"{'─' * 70}")
                    print(doc.data['text'].strip()[:150] + "...")
                    print(f"\n{'─' * 70}")
                    print(f"Detection Result:")
                    print(f"{'─' * 70}")
                    
                    # Parse and display language info
                    lang_info = doc.data['language']
                    if isinstance(lang_info, dict):
                        if 'languages' in lang_info:
                            # Multiple languages detected
                            print(f"Multiple languages detected:")
                            for lang in lang_info['languages']:
                                lang_name = lang.get('language', 'Unknown')
                                confidence = lang.get('confidence', 0)
                                script = lang.get('script', '')
                                dialect = lang.get('dialect', '')
                                
                                print(f"  • {lang_name} (confidence: {confidence:.2f})", end='')
                                if script:
                                    print(f" [Script: {script}]", end='')
                                if dialect:
                                    print(f" [Dialect: {dialect}]", end='')
                                print()
                            
                            if 'primary_language' in lang_info:
                                print(f"Primary language: {lang_info['primary_language']}")
                        else:
                            # Single language detected
                            lang_name = lang_info.get('language', 'Unknown')
                            confidence = lang_info.get('confidence', 0)
                            script = lang_info.get('script', '')
                            dialect = lang_info.get('dialect', '')
                            
                            print(f"Language: {lang_name} (confidence: {confidence:.2f})")
                            if script:
                                print(f"Script: {script}")
                            if dialect:
                                print(f"Dialect: {dialect}")
                    else:
                        print(f"{lang_info}")
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
    print("Language Detection Run Complete!")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(run_pipeline())
