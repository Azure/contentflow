# 📚 ContentFlow Library

> **Flexible content processing engine** - Build intelligent pipelines with 40+ pre-built executors, YAML-based orchestration, and seamless Azure integration.

## 📑 Table of Contents

- [🎯 Overview](#overview)
- [Installation](#installation)
- [📚 Core Concepts](#core-concepts)
  - [Pipelines](#pipelines)
  - [Executors](#executors)
  - [Content Model](#content-model)
  - [Events & Results](#events--results)
- [🛠️ Executor Catalog](#executor-catalog)
  - [Built-In Executors](#built-in-executors)
- [🔗 Data Connectors](#data-connectors)
- [🏗️ Project Structure](#project-structure)
- [💡 Creating Custom Executors](#creating-custom-executors)

---

## Overview

ContentFlow is a Python library for building intelligent content processing pipelines:

- **40+ Pre-Built Executors** - PDF, Word, Excel, embeddings, AI analysis, web scraping, and more
- **YAML-Based Pipelines** - Declarative configuration with conditional routing and parallel execution
- **Azure Integration** - Seamless connectors for Blob Storage, Search, Document Intelligence, and OpenAI
- **Async Processing** - Built on asyncio for scalable, non-blocking operations
- **Extensible Architecture** - Create custom executors and register them in the catalog

---

## Installation

```bash
# Install from source
cd contentflow-lib
pip install -e .
```

---

## Core Concepts

### Pipelines

Pipelines are directed acyclic graphs (DAGs) of executors that process content. They are:

- **Declaratively defined** in YAML with optional Python composition
- **Type-safe** using Pydantic models
- **Event-driven** with comprehensive execution tracking
- **Composable** through sub-pipelines for complex workflows

**Pipeline Structure:**
```yaml
pipeline:
  name: pipeline_name
  description: "Human-readable description"
  
  executors:
    - id: executor_id
      type: executor_type
      settings:
        key1: value1
        key2: ${ENV_VAR}  # Environment variable substitution
  
  edges:
    - from: executor_id_1
      to: executor_id_2
```

### Executors

Executors are reusable, configurable processors that operate on `Content` objects. Each executor:

- Inherits from `BaseExecutor`
- Implements a `process_input()` method with async support
- Has a defined settings schema for validation
- Returns modified `Content` with results in the `data` dictionary

**Executor Types:**

| Category | Examples |
|----------|----------|
| **Input** | `azure_blob_input_discovery`, `local_file_reader`, `web_scraper` |
| **Extraction** | `pdf_extractor`, `azure_document_intelligence_extractor`, `word_extractor`, `excel_extractor` |
| **Processing** | `recursive_text_chunker`, `entity_extraction_executor`, `sentiment_analysis_executor`, `field_mapper_executor` |
| **AI/ML** | `azure_openai_embeddings_executor`, `azure_openai_agent_executor`, `content_classifier_executor` |
| **Output** | `azure_blob_writer`, `ai_search_index_uploader` |

### Content Model

The `Content` class is the universal data structure passed through pipelines:

```python
from contentflow.models import Content, ContentIdentifier

content = Content(
    id=ContentIdentifier(
        canonical_id="unique_canonical_id",
        unique_id="unique_id",
        source_name="azure_blob", 
        source_type="pdf",
        container="input",
        path="documents/file.pdf",
        filename="file.pdf",
        metadata={"author": "John Doe"}
    ),
    summary_data={},           # High-level summary information
    data={},                   # Main processing results
    executor_logs=[]           # Execution history
)
```

### Events & Results

Pipelines emit events during execution:

```python
result = await executor.execute(content)

# Check status
print(result.status)           # PipelineStatus.COMPLETED
print(result.duration_seconds) # Execution time

# Review events
for event in result.events:
    print(f"[{event.timestamp}] {event.executor_id}: {event.event_type}")
    print(f"  Data: {event.data}")
    if event.error:
        print(f"  Error: {event.error}")
```

---

## Executor Catalog

ContentFlow includes **40+ pre-built executors** organized in `executor_catalog.yaml`. This catalog defines:

- Executor metadata (name, description, version)
- Configuration schema with validation rules
- UI hints for form generation
- Input/output specifications

### Built-In Executors

**Document Extraction:**
- `pdf_extractor` - Extract text, images, tables from PDFs (PyMuPDF)
- `azure_document_intelligence_extractor` - Advanced extraction with Document Intelligence API
- `word_extractor` - Process Word documents
- `excel_extractor` - Extract spreadsheet data
- `powerpoint_extractor` - PowerPoint slide extraction
- `azure_blob_input_discovery` - List files from Blob Storage

**AI & Analysis:**
- `azure_openai_embeddings_executor` - Generate vector embeddings
- `azure_openai_agent_executor` - Run agentic workflows with OpenAI
- `azure_content_understanding_extractor` - Semantic analysis
- `summarization_executor` - Create summaries
- `entity_extraction_executor` - NER and entity identification
- `sentiment_analysis_executor` - Sentiment classification
- `content_classifier_executor` - Multi-class classification

**Text Processing:**
- `recursive_text_chunker` - Intelligent text segmentation
- `language_detector_executor` - Detect document language
- `translation_executor` - Translate content
- `keyword_extractor_executor` - Extract keywords
- `table_row_splitter_executor` - Convert table rows to documents
- `field_mapper_executor` - Transform field mappings

**Routing & Control:**
- `parallel_executor` - Execute multiple paths concurrently
- `web_scraping_executor` - Extract web content with Playwright
- `pass_through` - Identity operation (for debugging)

**Storage & Output:**
- `azure_blob_writer` - Write to Blob Storage
- `ai_search_index_writer` - Write to Azure AI Search

---

## Data Connectors

Connectors provide standardized access to external services. Available connectors:

- **AzureBlobConnector** - Azure Blob Storage access
- **AzureSearchConnector** - Azure AI Search integration
- **DocumentIntelligenceConnector** - Document Intelligence API

**Using Connectors:**

```python
from contentflow.connectors import AzureBlobConnector

connector = AzureBlobConnector(
    name="storage",
    settings={
        "account_name": os.getenv("STORAGE_ACCOUNT"),
        "credential_type": "default_azure_credential"
    }
)

# List blobs
async with connector:
    blobs = await connector.list_blobs("container", prefix="documents/")
```

---

## Project Structure

```
contentflow/
├── pipeline/
│   ├── _pipeline.py              # Pipeline models
│   ├── _pipeline_executor.py     # Executor wrapper
│   └── pipeline_factory.py       # Configuration parser
│
├── executors/
│   ├── base.py                   # BaseExecutor class
│   ├── executor_registry.py      # Dynamic loading
│   ├── executor_config.py        # Validation
│   └── [40+ implementations]
│
├── connectors/
│   ├── base.py                   # ConnectorBase class
│   └── [connector implementations]
│
├── models/
│   └── _content.py               # Content model
│
├── utils/
│   ├── credential_provider.py    # Credential management
│   ├── config_provider.py        # Configuration loading
│   └── [utilities]
│
└── executor_catalog.yaml         # All executor definitions
```

---

## Creating Custom Executors

**Follow the guide [Creating Custom Executors in ContentFlow](./CustomExecutor.md)**

---

## 🤝 Contributing

Contributions are welcome! To create a custom executor or connector:

1. Inherit from `BaseExecutor` or `ConnectorBase`
2. Implement required methods
3. Add to executor catalog or register dynamically
4. Write tests in `tests/`
5. Submit pull request

---

## 📖 Documentation

- [Full ContentFlow Project README](../README.md)
- [Sample Pipelines](samples/README.md)
- [API Service Guide](../contentflow-api/README.md)
- [Web Dashboard Guide](../contentflow-web/README.md)
- [Infrastructure Deployment](../infra/README.md)
- [Creating Custom Executors Guide](./CustomExecutor.md)
---