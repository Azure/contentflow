"""
Document Split and Merge Example

This example demonstrates splitting large documents into chunks, processing
each chunk in parallel, and merging the results.

Use Case: Process large PDFs or Word documents by splitting them into
smaller segments (by pages, characters, etc.), processing each segment
independently, and combining the results.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add doc-proc-lib to path
doc_proc_lib_path = Path(__file__).parent.parent / "doc-proc-lib"
if doc_proc_lib_path.exists():
    sys.path.insert(0, str(doc_proc_lib_path))

from agent_framework import WorkflowBuilder
from doc_proc_workflow.executors import (
    DocumentExecutor,
    DocumentSplitter,
    ChunkProcessor,
    ResultAggregator,
)
from doc.proc.models import Document
from agent_framework import WorkflowContext

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Step 1: Define chunk processing logic
class TextExtractor(DocumentExecutor):
    """Extract and clean text from document chunk."""
    
    def __init__(self):
        super().__init__(id="text_extractor")
    
    async def process_document(
        self,
        document: Document,
        ctx: WorkflowContext
    ) -> Document:
        chunk_data = document.data.get("chunk_data", {})
        chunk_id = document.id
        
        logger.info(f"  Extracting text from {chunk_id}")
        
        # Simulate text extraction
        content = chunk_data.get("content", "")
        
        # Clean and process text
        cleaned_text = content.strip()
        word_count = len(cleaned_text.split())
        
        document.data["extracted_text"] = cleaned_text
        document.summary_data["word_count"] = word_count
        document.summary_data["extracted"] = True
        
        logger.info(f"  {chunk_id}: Extracted {word_count} words")
        
        return document


class EntityRecognizer(DocumentExecutor):
    """Recognize named entities in text."""
    
    def __init__(self):
        super().__init__(id="entity_recognizer")
    
    async def process_document(
        self,
        document: Document,
        ctx: WorkflowContext
    ) -> Document:
        text = document.data.get("extracted_text", "")
        chunk_id = document.id
        
        logger.info(f"  Recognizing entities in {chunk_id}")
        
        # Simulate entity recognition (normally would use NLP model)
        await asyncio.sleep(0.2)  # Simulate processing time
        
        # Mock entity detection
        entities = {
            "PERSON": [word for word in text.split() if word[0].isupper() and len(word) > 3],
            "DATE": [],
            "MONEY": []
        }
        
        document.data["entities"] = entities
        document.summary_data["entity_count"] = sum(len(v) for v in entities.values())
        
        logger.info(
            f"  {chunk_id}: Found {document.summary_data['entity_count']} entities"
        )
        
        return document


class SentimentAnalyzer(DocumentExecutor):
    """Analyze sentiment of text."""
    
    def __init__(self):
        super().__init__(id="sentiment_analyzer")
    
    async def process_document(
        self,
        document: Document,
        ctx: WorkflowContext
    ) -> Document:
        text = document.data.get("extracted_text", "")
        chunk_id = document.id
        
        logger.info(f"  Analyzing sentiment for {chunk_id}")
        
        # Simulate sentiment analysis
        await asyncio.sleep(0.1)
        
        # Mock sentiment scoring
        sentiment_score = 0.75  # Positive
        
        document.data["sentiment"] = {
            "score": sentiment_score,
            "label": "positive" if sentiment_score > 0.5 else "negative"
        }
        document.summary_data["sentiment_score"] = sentiment_score
        
        logger.info(f"  {chunk_id}: Sentiment = {sentiment_score:.2f}")
        
        return document


async def main():
    """
    Demonstrate document split, parallel processing, and merge.
    
    This example:
    1. Creates a large document
    2. Splits it into chunks by page
    3. Processes each chunk through a sub-workflow in parallel
    4. Merges results from all chunks
    """
    
    logger.info("=" * 80)
    logger.info("Document Split and Merge Example")
    logger.info("=" * 80)
    
    # Step 1: Create large document
    logger.info("\nStep 1: Creating large document")
    
    # Simulate a 10-page document
    pages = [
        f"Page {i+1} content. This is sample text for page {i+1}. "
        f"Lorem ipsum dolor sit amet for page {i+1}. "
        f"Important information on page {i+1}. "
        f"More details here on page {i+1}."
        for i in range(10)
    ]
    
    large_document = Document(
        id="large_doc_001",
        data={
            "pages": pages,
            "source": "large_report.pdf",
            "total_pages": len(pages)
        },
        summary_data={
            "document_type": "report",
            "page_count": len(pages)
        }
    )
    
    logger.info(f"  Created document with {len(pages)} pages")
    
    # Step 2: Build chunk processing workflow
    logger.info("\nStep 2: Building chunk processing workflow")
    
    extractor = TextExtractor()
    entity_recognizer = EntityRecognizer()
    sentiment_analyzer = SentimentAnalyzer()
    
    # Each chunk: extract -> recognize entities -> analyze sentiment
    chunk_workflow = (
        WorkflowBuilder()
        .add_edge(extractor, entity_recognizer)
        .add_edge(entity_recognizer, sentiment_analyzer)
        .set_start_executor(extractor)
        .build()
    )
    
    logger.info("  ✓ Chunk processing workflow created")
    
    # Step 3: Build main split-process-merge workflow
    logger.info("\nStep 3: Building split-process-merge workflow")
    
    # Split document by pages (2 pages per chunk)
    splitter = DocumentSplitter(
        split_by="pages",
        chunk_size=2,
        pages_key="pages"
    )
    
    # Process chunks in parallel (max 3 at a time)
    processor = ChunkProcessor(
        sub_workflow=chunk_workflow,
        max_parallel=3
    )
    
    # Merge results using custom function
    def merge_analysis_results(results: list) -> dict:
        """Custom merge function for analysis results."""
        total_words = sum(r.get("word_count", 0) for r in results)
        total_entities = sum(r.get("entity_count", 0) for r in results)
        avg_sentiment = sum(r.get("sentiment_score", 0) for r in results) / len(results) if results else 0
        
        return {
            "total_words": total_words,
            "total_entities": total_entities,
            "average_sentiment": avg_sentiment,
            "chunks_processed": len(results)
        }
    
    aggregator = ResultAggregator(
        aggregation_strategy=merge_analysis_results
    )
    
    # Main workflow: Split -> Process -> Merge
    main_workflow = (
        WorkflowBuilder()
        .add_edge(splitter, processor)
        .add_edge(processor, aggregator)
        .set_start_executor(splitter)
        .build()
    )
    
    logger.info("  ✓ Split-process-merge workflow created")
    
    # Step 4: Execute workflow
    logger.info("\nStep 4: Executing split-process-merge pipeline")
    logger.info("=" * 80)
    
    from agent_framework import (
        ExecutorCompletedEvent,
        ExecutorInvokedEvent,
        WorkflowOutputEvent
    )
    
    results = []
    async for event in main_workflow.run_stream(large_document):
        if isinstance(event, ExecutorInvokedEvent):
            logger.info(f"  ▶ {event.executor_id} started")
        elif isinstance(event, ExecutorCompletedEvent):
            logger.info(f"  ✓ {event.executor_id} completed")
        elif isinstance(event, WorkflowOutputEvent):
            results.append(event.data)
    
    logger.info("=" * 80)
    
    # Step 5: Display results
    logger.info("\nStep 5: Merged Results")
    
    if results:
        final_result = results[-1]
        
        logger.info(f"\n📊 Document Analysis Summary:")
        logger.info(f"  Original pages: {large_document.summary_data['page_count']}")
        
        merged_data = final_result.data.get("aggregated_data", {})
        
        logger.info(f"  Chunks processed: {merged_data.get('chunks_processed', 0)}")
        logger.info(f"  Total words: {merged_data.get('total_words', 0)}")
        logger.info(f"  Total entities found: {merged_data.get('total_entities', 0)}")
        logger.info(f"  Average sentiment: {merged_data.get('average_sentiment', 0):.2f}")
        
        # Show individual chunk details
        all_chunks = final_result.summary_data.get("all_results", [])
        
        if all_chunks:
            logger.info(f"\n📄 Chunk Details:")
            for i, chunk in enumerate(all_chunks, 1):
                logger.info(f"  Chunk {i}:")
                logger.info(f"    Words: {chunk.get('word_count', 0)}")
                logger.info(f"    Entities: {chunk.get('entity_count', 0)}")
                logger.info(f"    Sentiment: {chunk.get('sentiment_score', 0):.2f}")
    
    logger.info("\n" + "=" * 80)
    logger.info("Example completed!")
    logger.info("=" * 80)
    logger.info("\nKey Takeaways:")
    logger.info("  1. DocumentSplitter divides large documents into manageable chunks")
    logger.info("  2. Each chunk is processed independently through a sub-workflow")
    logger.info("  3. ChunkProcessor handles parallel execution (controlled by max_parallel)")
    logger.info("  4. ResultAggregator combines results using custom merge logic")
    logger.info("  5. This pattern scales to very large documents efficiently")
    
    logger.info("\nSplitting Strategies:")
    logger.info("  - 'pages': Split by page count (chunk_size = pages per chunk)")
    logger.info("  - 'characters': Split by character count (chunk_size = chars per chunk)")
    logger.info("  - 'words': Split by word count (chunk_size = words per chunk)")
    logger.info("  - 'lines': Split by line count (chunk_size = lines per chunk)")


if __name__ == "__main__":
    asyncio.run(main())
