"""
Conditional Routing Workflow Example

This example demonstrates how to route documents through different
processing paths based on document properties using switch-case patterns.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add doc-proc-lib to path
doc_proc_lib_path = Path(__file__).parent.parent / "doc-proc-lib"
if doc_proc_lib_path.exists():
    sys.path.insert(0, str(doc_proc_lib_path))

from agent_framework import WorkflowBuilder, Case, Default, executor
from doc_proc_workflow.executors import DocumentExecutor
from doc.proc.models import Document
from agent_framework import WorkflowContext
from typing_extensions import Never

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Document classifier
@executor(id="classifier")
async def classify_document(
    document: Document,
    ctx: WorkflowContext[Never, Document]
) -> None:
    """Classify document by type."""
    content = document.data.get("content", "")
    
    # Simple classification logic
    if "pdf" in content.lower():
        doc_type = "pdf"
    elif "image" in content.lower() or "photo" in content.lower():
        doc_type = "image"
    elif "text" in content.lower() or "doc" in content.lower():
        doc_type = "text"
    else:
        doc_type = "unknown"
    
    document.data["document_type"] = doc_type
    logger.info(f"  Classified document {document.id} as: {doc_type}")
    
    await ctx.yield_output(document)


# Type-specific processors
class PDFDocumentProcessor(DocumentExecutor):
    """Process PDF documents."""
    
    def __init__(self):
        super().__init__(id="pdf_processor")
    
    async def process_document(
        self,
        document: Document,
        ctx: WorkflowContext
    ) -> Document:
        logger.info(f"  🔴 PDF Processor: Processing {document.id}")
        await asyncio.sleep(0.3)
        document.summary_data["processor"] = "PDF"
        document.summary_data["extracted_pages"] = 10
        return document


class ImageDocumentProcessor(DocumentExecutor):
    """Process image documents."""
    
    def __init__(self):
        super().__init__(id="image_processor")
    
    async def process_document(
        self,
        document: Document,
        ctx: WorkflowContext
    ) -> Document:
        logger.info(f"  🔵 Image Processor: Processing {document.id}")
        await asyncio.sleep(0.2)
        document.summary_data["processor"] = "Image"
        document.summary_data["ocr_applied"] = True
        return document


class TextDocumentProcessor(DocumentExecutor):
    """Process text documents."""
    
    def __init__(self):
        super().__init__(id="text_processor")
    
    async def process_document(
        self,
        document: Document,
        ctx: WorkflowContext
    ) -> Document:
        logger.info(f"  🟢 Text Processor: Processing {document.id}")
        await asyncio.sleep(0.1)
        document.summary_data["processor"] = "Text"
        document.summary_data["word_count"] = 500
        return document


class DefaultDocumentProcessor(DocumentExecutor):
    """Process unknown document types."""
    
    def __init__(self):
        super().__init__(id="default_processor")
    
    async def process_document(
        self,
        document: Document,
        ctx: WorkflowContext
    ) -> Document:
        logger.info(f"  ⚪ Default Processor: Processing {document.id}")
        document.summary_data["processor"] = "Default"
        document.summary_data["needs_review"] = True
        return document


async def main():
    """
    Run a conditional routing workflow.
    
    This example demonstrates:
    1. Document classification
    2. Conditional routing based on document type
    3. Type-specific processing
    """
    
    logger.info("=" * 80)
    logger.info("Conditional Routing Workflow Example")
    logger.info("=" * 80)
    
    logger.info("\nStep 1: Creating executors")
    
    # Create processors for each document type
    pdf_processor = PDFDocumentProcessor()
    image_processor = ImageDocumentProcessor()
    text_processor = TextDocumentProcessor()
    default_processor = DefaultDocumentProcessor()
    
    logger.info(f"  ✓ Created 4 type-specific processors")
    
    logger.info("\nStep 2: Building conditional workflow")
    
    # Build workflow with switch-case routing
    workflow = (
        WorkflowBuilder()
        .set_start_executor(classify_document)
        .add_switch_case_edge_group(
            classify_document,
            [
                Case(
                    condition=lambda doc: doc.data.get("document_type") == "pdf",
                    target=pdf_processor
                ),
                Case(
                    condition=lambda doc: doc.data.get("document_type") == "image",
                    target=image_processor
                ),
                Case(
                    condition=lambda doc: doc.data.get("document_type") == "text",
                    target=text_processor
                ),
                Default(target=default_processor)
            ]
        )
        .build()
    )
    
    logger.info("  ✓ Conditional workflow created with 3 cases + default")
    
    # Create test documents of different types
    logger.info("\nStep 3: Preparing test documents")
    
    test_documents = [
        Document(
            id="doc_001",
            data={
                "content": "This is a PDF document with multiple pages",
                "source": "test"
            },
            summary_data={}
        ),
        Document(
            id="doc_002",
            data={
                "content": "This is an image file that needs OCR processing",
                "source": "test"
            },
            summary_data={}
        ),
        Document(
            id="doc_003",
            data={
                "content": "This is a text document with plain content",
                "source": "test"
            },
            summary_data={}
        ),
        Document(
            id="doc_004",
            data={
                "content": "This is some unknown format",
                "source": "test"
            },
            summary_data={}
        )
    ]
    
    logger.info(f"  ✓ Created {len(test_documents)} test documents")
    
    # Process each document
    logger.info("\nStep 4: Processing documents through conditional workflow")
    logger.info("=" * 80)
    
    from agent_framework import (
        ExecutorCompletedEvent,
        WorkflowOutputEvent
    )
    
    all_results = []
    
    for doc in test_documents:
        logger.info(f"\nProcessing: {doc.id}")
        logger.info(f"  Content: {doc.data.get('content')[:50]}...")
        logger.info("-" * 40)
        
        outputs = []
        async for event in workflow.run_stream(doc):
            if isinstance(event, ExecutorCompletedEvent):
                logger.info(f"    ✓ {event.executor_id}")
            elif isinstance(event, WorkflowOutputEvent):
                outputs.append(event.data)
        
        if outputs:
            result = outputs[0]
            all_results.append(result)
            logger.info(f"  Result: {result.summary_data}")
    
    logger.info("\n" + "=" * 80)
    logger.info("Step 5: Summary")
    logger.info("=" * 80)
    
    # Summarize results by processor type
    processor_counts = {}
    for result in all_results:
        processor = result.summary_data.get("processor", "Unknown")
        processor_counts[processor] = processor_counts.get(processor, 0) + 1
    
    logger.info("\nDocuments processed by each processor:")
    for processor, count in processor_counts.items():
        logger.info(f"  {processor}: {count} documents")
    
    logger.info("\n" + "=" * 80)
    logger.info("Example completed!")
    logger.info("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
