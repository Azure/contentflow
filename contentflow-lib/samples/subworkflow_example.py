"""
Sub-workflow execution examples.

Demonstrates how to use sub-workflow executors to process items in parallel
by running a complete workflow for each item.

Use cases:
- Process Excel rows through multi-step validation and enrichment
- Process document chunks through extraction and analysis
- Process batches through complex transformation pipelines
"""

import asyncio
import os
from pathlib import Path

from doc_proc_workflow import (
    PipelineExecutor,
    DocumentSplitter,
    RowSubPipelineExecutor,
    ChunkSubPipelineExecutor,
    BatchSubPipelineExecutor,
    ResultAggregator,
)

try:
    from doc_proc_lib.models.document import Document
except ImportError:
    # Fallback for testing
    from dataclasses import dataclass, field
    from typing import Dict, Any
    
    @dataclass
    class Document:
        id: str
        data: Dict[str, Any] = field(default_factory=dict)
        summary_data: Dict[str, Any] = field(default_factory=dict)

from agent_framework import Executor, WorkflowContext, handler
from agent_framework.workflow import WorkflowBuilder


# Simple enricher executor for demo purposes
class SimpleEnricherExecutor(Executor):
    """Simple executor that enriches documents with additional data."""
    
    def __init__(self, enrichments: dict, **kwargs):
        super().__init__(**kwargs)
        self.enrichments = enrichments
    
    @handler
    async def process_document(self, document: Document, ctx: WorkflowContext) -> Document:
        """Add enrichment data to document."""
        for key, value in self.enrichments.items():
            document.data[key] = value
        return document


async def example_row_subworkflow():
    """
    Example: Process Excel rows through a sub-workflow.
    
    Each row goes through: validation → enrichment → transformation
    """
    print("\n" + "=" * 80)
    print("Example 1: Row Sub-Workflow Processing")
    print("=" * 80)
    
    # Create a sub-workflow for processing each row
    # Row workflow: validate → enrich → transform
    row_validator = SimpleEnricherExecutor(
        enrichments={
            "is_valid": "True",  # Simple validation
            "validation_timestamp": "2024-01-01T00:00:00Z"
        }
    )
    
    row_enricher = SimpleEnricherExecutor(
        enrichments={
            "processed": "True",
            "row_status": "enriched"
        }
    )
    
    # Build row sub-workflow
    row_workflow = (
        WorkflowBuilder()
        .add_edge(row_validator, row_enricher)
        .build()
    )
    
    # Create row sub-workflow executor
    row_executor = RowSubPipelineExecutor(
        sub_workflow=row_workflow,
        settings={
            "max_parallel": 5,  # Process 5 rows in parallel
            "timeout_secs": 30,
            "table_key": "rows",
            "row_key": "row_data",
            "row_id_field": "id"
        }
    )
    
    # Create aggregator to collect results
    aggregator = ResultAggregator(
        settings={
            "strategy": "merge_list",
            "results_key": "processed_rows"
        }
    )
    
    # Build main workflow: row processor → aggregator
    main_workflow = (
        WorkflowBuilder()
        .add_edge(row_executor, aggregator)
        .build()
    )
    
    # Create executor
    async with PipelineExecutor(main_workflow) as executor:
        # Sample Excel data (would normally come from ExcelReaderExecutor)
        input_doc = Document(
            id="excel-1",
            data={
                "rows": [
                    {"id": "row1", "name": "Alice", "value": 100},
                    {"id": "row2", "name": "Bob", "value": 200},
                    {"id": "row3", "name": "Charlie", "value": 300},
                    {"id": "row4", "name": "David", "value": 400},
                    {"id": "row5", "name": "Eve", "value": 500},
                ]
            }
        )
        
        result = await executor.execute(input_doc)
        
        print(f"\nStatus: {result.status}")
        print(f"Duration: {result.duration_seconds:.2f}s")
        
        # Get final document
        final_doc = None
        for event in result.events:
            if hasattr(event, 'data'):
                final_doc = event.data
        
        if final_doc:
            print(f"\nProcessed {len(final_doc.data.get('processed_rows', []))} rows")
            print("\nSample processed row:")
            if final_doc.data.get('processed_rows'):
                import json
                print(json.dumps(final_doc.data['processed_rows'][0], indent=2))
            
            stats = final_doc.data.get('statistics', {})
            print(f"\nStatistics:")
            print(f"  Total items: {stats.get('total_items', 0)}")
            print(f"  Successful: {stats.get('successful_count', 0)}")
            print(f"  Failed: {stats.get('failed_count', 0)}")
            print(f"  Success rate: {stats.get('success_rate', 0):.1%}")


async def example_chunk_subworkflow():
    """
    Example: Process document chunks through a sub-workflow.
    
    Each chunk goes through: extraction → analysis → summarization
    """
    print("\n" + "=" * 80)
    print("Example 2: Chunk Sub-Workflow Processing")
    print("=" * 80)
    
    # Create document splitter
    splitter = DocumentSplitter(
        settings={
            "split_by": "characters",
            "chunk_size": 100,
            "overlap": 20,
            "chunks_key": "text_chunks"
        }
    )
    
    # Create chunk processing sub-workflow
    chunk_analyzer = SimpleEnricherExecutor(
        enrichments={
            "analyzed": "True",
            "word_count": 100,
            "chunk_type": "text"
        }
    )
    
    chunk_enricher = SimpleEnricherExecutor(
        enrichments={
            "processed": "True",
            "chunk_status": "complete"
        }
    )
    
    # Build chunk sub-workflow
    chunk_workflow = (
        WorkflowBuilder()
        .add_edge(chunk_analyzer, chunk_enricher)
        .build()
    )
    
    # Create chunk sub-workflow executor
    chunk_executor = ChunkSubPipelineExecutor(
        sub_workflow=chunk_workflow,
        settings={
            "max_parallel": 3,
            "timeout_secs": 20,
            "items_key": "text_chunks"
        }
    )
    
    # Create aggregator
    aggregator = ResultAggregator(
        settings={
            "strategy": "merge_list",
            "results_key": "processed_chunks"
        }
    )
    
    # Build main workflow: split → process chunks → aggregate
    main_workflow = (
        WorkflowBuilder()
        .add_edge(splitter, chunk_executor)
        .add_edge(chunk_executor, aggregator)
        .build()
    )
    
    # Create executor
    async with PipelineExecutor(main_workflow) as executor:
        # Sample document with text content
        input_doc = Document(
            id="doc-1",
            data={
                "content": "This is a sample document with enough text content to be split into multiple chunks. " * 10
            }
        )
        
        result = await executor.execute(input_doc)
        
        print(f"\nStatus: {result.status}")
        print(f"Duration: {result.duration_seconds:.2f}s")
        
        # Get final document
        final_doc = None
        for event in result.events:
            if hasattr(event, 'data'):
                final_doc = event.data
        
        if final_doc:
            print(f"\nProcessed {len(final_doc.data.get('processed_chunks', []))} chunks")
            
            stats = final_doc.data.get('statistics', {})
            print(f"\nStatistics:")
            print(f"  Total chunks: {stats.get('total_items', 0)}")
            print(f"  Successful: {stats.get('successful_count', 0)}")
            print(f"  Failed: {stats.get('failed_count', 0)}")
            print(f"  Processing time: {stats.get('processing_time_secs', 0):.2f}s")


async def example_batch_subworkflow():
    """
    Example: Process document batches through a sub-workflow.
    
    Each batch goes through: validation → transformation → quality check
    """
    print("\n" + "=" * 80)
    print("Example 3: Batch Sub-Workflow Processing")
    print("=" * 80)
    
    # Create batch processing sub-workflow
    batch_validator = SimpleEnricherExecutor(
        enrichments={
            "validated": "True",
            "batch_size": 2
        }
    )
    
    batch_enricher = SimpleEnricherExecutor(
        enrichments={
            "processed": "True",
            "batch_status": "complete"
        }
    )
    
    # Build batch sub-workflow
    batch_workflow = (
        WorkflowBuilder()
        .add_edge(batch_validator, batch_enricher)
        .build()
    )
    
    # Create batch sub-workflow executor
    batch_executor = BatchSubPipelineExecutor(
        sub_workflow=batch_workflow,
        settings={
            "max_parallel": 2,
            "timeout_secs": 30,
            "items_key": "batches"
        }
    )
    
    # Create aggregator
    aggregator = ResultAggregator(
        settings={
            "strategy": "merge_list",
            "results_key": "processed_batches"
        }
    )
    
    # Build main workflow
    main_workflow = (
        WorkflowBuilder()
        .add_edge(batch_executor, aggregator)
        .build()
    )
    
    # Create executor
    async with PipelineExecutor(main_workflow) as executor:
        # Sample batches (would normally come from BatchDocumentSplitter)
        input_doc = Document(
            id="batches-1",
            data={
                "batches": [
                    {
                        "batch_id": "batch1",
                        "documents": [
                            {"id": "doc1", "type": "invoice"},
                            {"id": "doc2", "type": "receipt"}
                        ]
                    },
                    {
                        "batch_id": "batch2",
                        "documents": [
                            {"id": "doc3", "type": "contract"},
                            {"id": "doc4", "type": "agreement"}
                        ]
                    }
                ]
            }
        )
        
        result = await executor.execute(input_doc)
        
        print(f"\nStatus: {result.status}")
        print(f"Duration: {result.duration_seconds:.2f}s")
        
        # Get final document
        final_doc = None
        for event in result.events:
            if hasattr(event, 'data'):
                final_doc = event.data
        
        if final_doc:
            print(f"\nProcessed {len(final_doc.data.get('processed_batches', []))} batches")
            
            stats = final_doc.data.get('statistics', {})
            print(f"\nStatistics:")
            print(f"  Total batches: {stats.get('total_items', 0)}")
            print(f"  Successful: {stats.get('successful_count', 0)}")
            print(f"  Failed: {stats.get('failed_count', 0)}")


async def example_nested_subworkflows():
    """
    Example: Nested sub-workflows - split document → process chunks in batches.
    
    Main workflow:
      1. Split document into chunks
      2. Process each chunk through a sub-workflow
      3. Aggregate results
    
    Chunk sub-workflow:
      1. Analyze chunk
      2. Enrich chunk
    """
    print("\n" + "=" * 80)
    print("Example 4: Nested Sub-Workflows (Complex Composition)")
    print("=" * 80)
    
    # Create document splitter
    splitter = DocumentSplitter(
        settings={
            "split_by": "words",
            "chunk_size": 50,
            "overlap": 10,
            "chunks_key": "word_chunks"
        }
    )
    
    # Create inner sub-workflow for each chunk
    chunk_analyzer = SimpleEnricherExecutor(
        enrichments={
            "analyzed": "True",
            "analysis_level": "detailed"
        }
    )
    
    chunk_summarizer = SimpleEnricherExecutor(
        enrichments={
            "summarized": "True",
            "summary": "Chunk processed successfully"
        }
    )
    
    # Build chunk processing sub-workflow
    chunk_workflow = (
        WorkflowBuilder()
        .add_edge(chunk_analyzer, chunk_summarizer)
        .build()
    )
    
    # Create chunk sub-workflow executor
    chunk_executor = ChunkSubPipelineExecutor(
        sub_workflow=chunk_workflow,
        settings={
            "max_parallel": 4,
            "timeout_secs": 15,
            "items_key": "word_chunks"
        }
    )
    
    # Create final aggregator
    aggregator = ResultAggregator(
        settings={
            "strategy": "concatenate",
            "results_key": "all_processed_chunks",
            "separator": "\n---\n"
        }
    )
    
    # Build main workflow: split → process → aggregate
    main_workflow = (
        WorkflowBuilder()
        .add_edge(splitter, chunk_executor)
        .add_edge(chunk_executor, aggregator)
        .build()
    )
    
    # Create executor
    async with PipelineExecutor(main_workflow) as executor:
        # Sample document
        input_doc = Document(
            id="doc-nested",
            data={
                "content": " ".join([f"Word{i}" for i in range(200)])  # 200 words
            }
        )
        
        result = await executor.execute(input_doc)
        
        print(f"\nStatus: {result.status}")
        print(f"Duration: {result.duration_seconds:.2f}s")
        
        # Get final document
        final_doc = None
        for event in result.events:
            if hasattr(event, 'data'):
                final_doc = event.data
        
        if final_doc:
            stats = final_doc.data.get('statistics', {})
            print(f"\nNested processing statistics:")
            print(f"  Original words: 200")
            print(f"  Chunks created: {stats.get('total_items', 0)}")
            print(f"  Chunks processed: {stats.get('successful_count', 0)}")
            print(f"  Success rate: {stats.get('success_rate', 0):.1%}")
            print(f"  Total processing time: {stats.get('processing_time_secs', 0):.2f}s")


async def main():
    """Run all sub-workflow examples."""
    print("\n" + "=" * 80)
    print("SUB-WORKFLOW EXECUTION EXAMPLES")
    print("=" * 80)
    print("\nDemonstrating how to compose workflows by running sub-workflows")
    print("for each item in parallel processing scenarios.")
    
    await example_row_subworkflow()
    await example_chunk_subworkflow()
    await example_batch_subworkflow()
    await example_nested_subworkflows()
    
    print("\n" + "=" * 80)
    print("All examples completed successfully!")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
