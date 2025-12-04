# Doc-Proc-Lib-Workflows: Workflow-Based Document Processing

A modern, connector-based implementation of document processing workflows using the [Microsoft Agent Framework](https://github.com/microsoft/agent-framework). Build powerful document processing pipelines with minimal configuration.

> 📚 **New to this project?** See [DOCUMENTATION_INDEX.md](DOCUMENTATION_INDEX.md) for a complete guide to all documentation.  
> 🚀 **Want to get started quickly?** Jump to [GETTING_STARTED.md](GETTING_STARTED.md) for a 5-minute tutorial.

## Quick Start

**3 steps to process documents:**

```bash
# 1. Set environment variables
export STORAGE_ACCOUNT=mystorageaccount
export DOCUMENT_INTELLIGENCE_ENDPOINT=https://mydocint.cognitiveservices.azure.com
export SEARCH_ENDPOINT=https://mysearch.search.windows.net

# 2. Run example
python examples/simple_example.py
```

That's it! See `examples/SIMPLE_GUIDE.md` for details.

## Overview

This package provides a connector-based architecture for document processing workflows with:

✅ **Minimal Configuration** - Auto-detection of credentials, sensible defaults  
✅ **Environment Variables** - Easy config management with `${VAR_NAME}` syntax  
✅ **Production Ready** - Works with Azure managed identity out of the box  
✅ **Powerful Workflows** - Orchestrate complex pipelines with Microsoft Agent Framework  

## Key Features

- **🚀 Simple Setup**: Just 4 environment variables to get started
- **🔌 Smart Connectors**: Auto-detect credentials, work with managed identity
- **⚙️ Flexible Configuration**: YAML-based with environment variable support
- **🔄 Powerful Workflows**: Sequential, parallel, conditional execution patterns
- **📊 Built-in Executors**: Content retrieval, AI extraction, enrichment, indexing
- **📚 Executor Catalog**: Dynamic loading with schema validation (like step_catalog.yaml)
- **🎯 Type-Safe**: Full Pydantic model integration
- **🔍 Observable**: Built-in workflow events and monitoring

## What's New

### ✨ Executor Catalog System

Similar to `step_catalog.yaml` in doc-proc-lib, we now support dynamic executor loading:

- **Schema-based validation** - Define settings schemas in YAML
- **Dynamic loading** - Add executors without code changes
- **Rich metadata** - UI generation, documentation, searchability
- **Backward compatible** - Works alongside legacy executor types

```python
# Enable dynamic loading with executor catalog
factory = PipelineFactory.from_config_file(
    config_path="workflow_config.yaml",
    executor_catalog_path="executor_catalog.yaml"  # NEW!
)
```

See [EXECUTOR_CATALOG.md](EXECUTOR_CATALOG.md) for details.

### ✨ PipelineExecutor

High-level workflow execution with automatic output capture:

- **Simple API** - Load and execute workflows easily
- **Event capture** - Automatic event and output tracking
- **Batch processing** - Process multiple documents
- **Event streaming** - Real-time event monitoring
- **Context manager** - Auto lifecycle management

```python
# Simple workflow execution
async with PipelineExecutor.from_config_file(
    "workflow_config.yaml",
    "my_workflow"
) as executor:
    result = await executor.execute(document)
    print(f"Status: {result.status}, Duration: {result.duration_seconds}s")
```

See [PIPELINE_EXECUTOR.md](PIPELINE_EXECUTOR.md) for details.

### ✨ Edge-Based Workflows

Build complex workflow graphs with parallel processing:

- **Parallel execution** - Fan-out to multiple executors
- **Join patterns** - Fan-in from multiple paths
- **Conditional routing** - Dynamic path selection
- **Subworkflows** - Nested parallel processing

See [examples/PARALLEL_WORKFLOWS_GUIDE.md](examples/PARALLEL_WORKFLOWS_GUIDE.md) for examples.

## Architecture

### Connector-Based Design

```
PipelineFactory
    ├── ConnectorRegistry
    │   ├── BlobConnector (Azure Blob Storage)
    │   ├── AISearchConnector (Azure AI Search)
    │   ├── AIInferenceConnector (Azure AI)
    │   └── DocumentIntelligenceConnector (Document Intelligence)
    │
    └── Workflows
        ├── ContentRetrieverExecutor
        ├── DocumentIntelligenceExtractorExecutor
        ├── CustomAIPromptExecutor
        └── AISearchIndexWriterExecutor
```

### From Services to Connectors

**Old Approach (Complex):**
- Multiple catalog files (service_catalog.yaml, step_catalog.yaml)
- Complex service instance configuration
- Class-based settings

**New Approach (Simple):**
- Single configuration file
- Auto-detection of credentials
- Dict-based settings with environment variables

See `SERVICES_TO_CONNECTORS.md` for migration guide.

## Installation

```bash
# Install Microsoft Agent Framework
pip install agent-framework-azure-ai --pre

# Install this package
cd doc-proc-lib-workflows
pip install -e .
```

## Simple Example

**1. Create `config.yaml`:**

```yaml
connectors:
  - name: storage
    type: blob_storage
    settings:
      account_name: ${STORAGE_ACCOUNT}
  
  - name: doc_intelligence
    type: document_intelligence
    settings:
      endpoint: ${DOCUMENT_INTELLIGENCE_ENDPOINT}
  
  - name: search
    type: ai_search
    settings:
      endpoint: ${SEARCH_ENDPOINT}
      index_name: documents

workflows:
  - name: basic
    executors:
      - id: retrieve
        type: content_retriever
        connectors: [storage]
      
      - id: extract
        type: document_intelligence_extractor
        connectors: [doc_intelligence]
      
      - id: index
        type: ai_search_index_writer
        connectors: [search]
    
    execution_sequence: [retrieve, extract, index]
```

**2. Run the workflow:**

```python
from doc_proc_workflow.factory import PipelineFactory
from doc_proc_lib.models.document import Document, ContentIdentifier

async def process():
    # Load and initialize
    factory = PipelineFactory.from_config_file("config.yaml")
    await factory.initialize_connectors()
    
    # Create workflow
    workflow = await factory.create_workflow("basic")
    
    # Process document
    document = Document(
        id="doc1",
        content_identifier=ContentIdentifier(
            uri="https://storage.blob.core.windows.net/docs/sample.pdf",
            source_type="azure_blob"
        )
    )
    
    connectors = factory.get_connectors_dict()
    async for event in workflow.run_stream(document, context={"connectors": connectors}):
        print(f"Event: {type(event).__name__}")
    
    await factory.cleanup_connectors()

import asyncio
asyncio.run(process())
```

See `examples/SIMPLE_GUIDE.md` for complete guide.

## Available Connectors

### BlobConnector (`blob_storage`)
Azure Blob Storage operations.

**Required:** `account_name`  
**Auto-detects:** Connection string, account key, or managed identity

### DocumentIntelligenceConnector (`document_intelligence`)
Azure Document Intelligence for content extraction.

**Required:** `endpoint`  
**Auto-detects:** API key or managed identity

### AIInferenceConnector (`ai_inference`)
Azure AI for chat completions and enrichment.

**Required:** `endpoint`  
**Auto-detects:** API key or managed identity

### AISearchConnector (`ai_search`)
Azure AI Search for indexing and search.

**Required:** `endpoint`, `index_name`  
**Auto-detects:** API key or managed identity

## Available Executors

### ContentRetrieverExecutor
Downloads content from blob storage or local files.

**Connectors:** `storage` (BlobConnector)  
**Settings:** Optional container_name, temp file options

### DocumentIntelligenceExtractorExecutor
Extracts text, tables, and key-value pairs from documents.

**Connectors:** `doc_intelligence` (DocumentIntelligenceConnector)  
**Settings:** Optional model_id, extraction options

### CustomAIPromptExecutor
Processes chunks through AI with custom prompts.

**Connectors:** `ai_model` (AIInferenceConnector)  
**Settings:** Required system_prompt, user_prompt

### AISearchIndexWriterExecutor
Indexes documents or chunks to Azure AI Search.

**Connectors:** `search` (AISearchConnector)  
**Settings:** Optional index_mode (document/chunks), metadata fields

## Documentation

- **`examples/SIMPLE_GUIDE.md`** - Quick start guide with minimal configuration
- **`CONNECTOR_ARCHITECTURE.md`** - Full architecture and advanced usage
- **`SERVICES_TO_CONNECTORS.md`** - Migration guide from old service-based approach
- **`examples/workflow_config_guide.md`** - Detailed configuration reference
- **`MIGRATION.md`** - Pipeline to workflow migration guide

## Examples

- **`simple_example.py`** - Minimal working example
- **`workflow_example.py`** - Complete example with all features
- **`simple_config.yaml`** - Minimal configuration
- **`workflow_config.yaml`** - Full configuration with comments
                condition=lambda doc: doc.data.get("type") == "pdf",
                target=pdf_processor
            ),
            Case(
                condition=lambda doc: doc.data.get("type") == "image",
                target=image_processor
            ),
            Default(target=text_processor)
        ]
    )
    .build()
)
```

### 4. Parallel Excel Processing

```python
from doc_proc_workflow.executors import ExcelRowProcessor, ResultAggregator

# Define row processing workflow
row_workflow = WorkflowBuilder()...build()

# Process Excel rows in parallel
excel_processor = ExcelRowProcessor(
    sub_workflow=row_workflow,
    excel_key="excel_data",
    max_parallel=5  # Process 5 rows concurrently
)

aggregator = ResultAggregator(aggregation_strategy="summarize")

workflow = (
    WorkflowBuilder()
    .add_edge(excel_processor, aggregator)
    .build()
)
```

### 5. Document Split and Merge

```python
from doc_proc_workflow.executors import (
    DocumentSplitter,
    ChunkProcessor,
    ResultAggregator
)

# Build chunk processing workflow
chunk_workflow = WorkflowBuilder()...build()

# Split document into chunks
splitter = DocumentSplitter(
    split_by="pages",  # or "characters", "words", "lines"
    chunk_size=2,      # 2 pages per chunk
    pages_key="pages"
)

# Process chunks in parallel
processor = ChunkProcessor(
    sub_workflow=chunk_workflow,
    max_parallel=3
)

# Merge results
aggregator = ResultAggregator(
    aggregation_strategy=custom_merge_function
)

workflow = (
    WorkflowBuilder()
    .add_edge(splitter, processor)
    .add_edge(processor, aggregator)
    .build()
)
```

## Migration from Pipeline-Based to Workflow-Based

### Before (Pipeline-Based)

```python
from doc.proc.pipeline.pipeline_factory import PipelineFactory

factory = PipelineFactory(step_catalog, service_catalog)
pipeline = await factory.create_pipeline(pipeline_config)
result = await pipeline.run(input_data)
```

### After (Workflow-Based)

```python
from doc_proc_workflow import PipelineFactory

factory = PipelineFactory(step_catalog, service_catalog)
workflow = await factory.create_workflow(pipeline_config)
result = await workflow.run(input_data)
```

## Key Differences & Advantages

### 1. **Execution Model**
- **Pipeline**: Sequential with conditional skipping
- **Workflow**: Graph-based with native parallelism, branching, and loops

### 2. **Composability**
- **Pipeline**: Monolithic execution
- **Workflow**: Composable sub-workflows and executor reuse

### 3. **Event System**
- **Pipeline**: Basic logging
- **Workflow**: Rich event streaming (ExecutorInvokedEvent, ExecutorCompletedEvent, etc.)

### 4. **State Management**
- **Pipeline**: Context dictionary
- **Workflow**: SharedState with type-safe access

### 5. **Orchestration Patterns**
```python
# Fan-out/Fan-in
workflow = (
    WorkflowBuilder()
    .add_edge(source, [executor1, executor2, executor3])  # Fan-out
    .add_fan_in_edges([executor1, executor2, executor3], aggregator)  # Fan-in
    .build()
)

# Concurrent processing
from agent_framework import ConcurrentBuilder
workflow = ConcurrentBuilder().participants([exec1, exec2, exec3]).build()

# Conditional loops
workflow = (
    WorkflowBuilder()
    .add_edge(processor, judge)
    .add_edge(judge, processor, condition=lambda x: x.needs_retry)
    .build()
)

# Parallel Excel processing
excel_processor = ExcelRowProcessor(
    sub_workflow=row_workflow,
    excel_key="excel_data",
    max_parallel=5
)

# Document split and parallel processing
workflow = (
    WorkflowBuilder()
    .add_edge(
        DocumentSplitter(split_by="pages", chunk_size=2),
        ChunkProcessor(sub_workflow=chunk_workflow, max_parallel=3)
    )
    .add_edge(ChunkProcessor(...), ResultAggregator(...))
    .build()
)
```

## Parallel Processing Patterns

### Excel Row Processing

Process each row in an Excel file through a dedicated sub-workflow:

```python
from doc_proc_workflow.executors import ExcelRowProcessor, ResultAggregator

# Define how to process each row
row_workflow = (
    WorkflowBuilder()
    .add_edge(validator, enricher)
    .add_edge(enricher, transformer)
    .build()
)

# Process rows in parallel
excel_processor = ExcelRowProcessor(
    sub_workflow=row_workflow,
    excel_key="excel_data",  # Key in document.data containing row list
    max_parallel=10          # Process 10 rows concurrently
)

# Aggregate results
aggregator = ResultAggregator(aggregation_strategy="summarize")

# Complete workflow
workflow = (
    WorkflowBuilder()
    .add_edge(excel_processor, aggregator)
    .build()
)
```

**Use Cases:**
- Invoice processing (one workflow per invoice)
- Customer data enrichment (parallel API calls)
- Batch data validation and transformation

See `examples/excel_parallel_processing.py` for a complete example.

### Document Splitting and Merging

Split large documents into chunks, process in parallel, and merge results:

```python
from doc_proc_workflow.executors import (
    DocumentSplitter,
    ChunkProcessor,
    ResultAggregator
)

# Define chunk processing workflow
chunk_workflow = (
    WorkflowBuilder()
    .add_edge(text_extractor, entity_recognizer)
    .add_edge(entity_recognizer, sentiment_analyzer)
    .build()
)

# Split large document
splitter = DocumentSplitter(
    split_by="pages",      # Split strategy: pages, characters, words, lines
    chunk_size=5,          # 5 pages per chunk
    pages_key="pages"      # Key containing page content
)

# Process chunks in parallel
processor = ChunkProcessor(
    sub_workflow=chunk_workflow,
    max_parallel=4         # Process 4 chunks concurrently
)

# Merge results with custom function
def merge_analysis(results: list) -> dict:
    return {
        "total_entities": sum(r.get("entity_count", 0) for r in results),
        "avg_sentiment": sum(r.get("sentiment", 0) for r in results) / len(results)
    }

aggregator = ResultAggregator(aggregation_strategy=merge_analysis)

# Complete workflow
workflow = (
    WorkflowBuilder()
    .add_edge(splitter, processor)
    .add_edge(processor, aggregator)
    .build()
)
```

**Splitting Strategies:**
- `pages`: Split by page count (for PDFs, Word docs)
- `characters`: Split by character count (for text files)
- `words`: Split by word count (for NLP processing)
- `lines`: Split by line count (for log files, CSV)

**Aggregation Strategies:**
- `merge_list`: Combine all results into a flat list
- `concatenate`: Concatenate text results
- `summarize`: Extract summary data from all results
- Custom function: Provide your own merge logic

**Use Cases:**
- Large PDF analysis (split by pages, extract entities, merge)
- Long document summarization (split, summarize chunks, merge summaries)
- Parallel OCR processing (split images, OCR each, merge text)

See `examples/document_split_merge.py` for a complete example.

## Advanced Features

### Sub-Workflows

```python
from doc_proc_workflow.executors import PipelineExecutor

# Create a sub-workflow
pdf_processing_workflow = WorkflowBuilder()...build()

# Use as executor in parent workflow
pdf_executor = PipelineExecutor(pdf_processing_workflow, id="pdf_processing")

parent_workflow = (
    WorkflowBuilder()
    .add_edge(classifier, pdf_executor)
    .build()
)
```

### Checkpointing

```python
from agent_framework import FileCheckpointStorage

checkpoint_storage = FileCheckpointStorage("./checkpoints")

workflow = (
    WorkflowBuilder()
    .with_checkpoint_storage(checkpoint_storage)
    .add_edge(step1, step2)
    .build()
)

# Resume from checkpoint
result = await workflow.resume_from_checkpoint("checkpoint_id")
```

### Human-in-the-Loop

```python
from agent_framework import response_handler

class ReviewExecutor(DocumentExecutor):
    @response_handler
    async def request_review(self, doc: Document) -> ApprovalResponse:
        """Request human review before proceeding."""
        pass
    
    async def process_document(self, doc: Document, ctx: WorkflowContext):
        # Request approval
        approval = await self.request_review(doc)
        if approval.approved:
            return doc
        else:
            raise Exception("Document rejected")
```

## Observability

```python
from agent_framework import (
    ExecutorCompletedEvent,
    ExecutorFailedEvent,
    WorkflowOutputEvent
)

async for event in workflow.run_stream(input_data):
    if isinstance(event, ExecutorCompletedEvent):
        print(f"✓ {event.executor_id} completed")
    elif isinstance(event, ExecutorFailedEvent):
        print(f"✗ {event.executor_id} failed: {event.error}")
    elif isinstance(event, WorkflowOutputEvent):
        print(f"Final result: {event.data}")
```

## API Reference

### PipelineFactory

Primary entry point for creating workflows from configurations.

```python
factory = PipelineFactory.from_config_files(
    step_catalog_path="step_catalog.yaml",
    service_catalog_path="service_catalog.yaml",
    pipeline_config_path="pipeline_config.yaml"
)

# Create workflow from pipeline name
workflow = await factory.create_workflow("my_pipeline")

# Create custom workflow
workflow = factory.create_custom_workflow(
    executors=[executor1, executor2],
    edges=[(executor1, executor2)]
)
```

### DocumentExecutor

Base class for document processing executors.

```python
class DocumentExecutor(Executor):
    async def process_document(
        self, 
        document: Document, 
        ctx: WorkflowContext
    ) -> Document:
        """Override to implement document processing logic."""
        pass
```

### StepExecutorAdapter

Wraps existing `StepBase` instances as Agent Framework executors.

```python
from doc_proc_workflow.executors import StepExecutorAdapter

adapter = StepExecutorAdapter(
    step_instance=existing_step,
    executor_id="my_step_executor"
)
```

## Contributing

This is a refactored implementation demonstrating workflow-based orchestration. Future enhancements:

1. **Enhanced Orchestration Patterns**: More sophisticated routing and coordination
2. **Distributed Execution**: Support for distributed workflow execution
3. **Advanced State Management**: Persistent state across workflow runs
4. **Metrics & Monitoring**: Integration with OpenTelemetry
5. **Visual Workflow Designer**: UI for building workflows

## License

Same as the parent project.

## Resources

- [Microsoft Agent Framework](https://github.com/microsoft/agent-framework)
- [Agent Framework Documentation](https://microsoft.github.io/agent-framework/)
- [Workflow Samples](https://github.com/microsoft/agent-framework/tree/main/python/samples/getting_started/workflows)
