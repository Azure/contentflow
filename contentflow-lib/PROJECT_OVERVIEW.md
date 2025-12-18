# ContentFlow Project Overview

> **"From Documents to Intelligence in Minutes, Not Months"**

## What is ContentFlow?

**ContentFlow** is a modern, workflow-based document processing and content intelligence platform built on the [Microsoft Agent Framework](https://github.com/microsoft/agent-framework). It enables organizations to build powerful, scalable content processing pipelines through a simple, declarative YAML configuration with minimal code.

ContentFlow transforms the complexity of enterprise content processing into an elegant, connector-based architecture that auto-detects credentials, works seamlessly with Azure managed identity, and provides production-ready document processing workflows out of the box.

## Core Value Proposition

### Traditional Approach: Complex & Fragile
- Manual integration of multiple Azure services
- Complex authentication and credential management  
- Custom code for each processing step
- Difficult to maintain and scale
- Long development cycles

### ContentFlow Approach: Simple & Powerful
- **4 environment variables** to get started
- **YAML-based configuration** - no code required for common workflows
- **Auto-detected credentials** with managed identity support
- **40+ pre-built executors** for common processing tasks
- **Production-ready** workflows in minutes

## Key Capabilities

### 🔌 Smart Connector Architecture
- **Auto-detection**: Automatically discovers Azure credentials and configuration
- **Managed Identity**: First-class support for Azure managed identity
- **Multi-cloud Ready**: Extensible to AWS, GCP, and on-premises systems
- **Connection Pooling**: Efficient resource management

**Supported Connectors:**
- Azure Blob Storage
- Azure AI Search
- Azure AI Document Intelligence
- Azure OpenAI / AI Inference
- Azure Content Understanding
- Azure Cosmos DB (Graph API)
- Azure Container Registry

### ⚙️ Extensive Executor Library

ContentFlow provides **40+ pre-built executors** organized into categories:

#### **Content Ingestion**
- **BlobInputExecutor** - Retrieve documents from Azure Blob Storage
- **WebScrapingExecutor** - Extract content from websites
- **ContentRetrieverExecutor** - Universal content retrieval from multiple sources

#### **Document Extraction**
- **PDFExtractorExecutor** - Extract text, tables, and images from PDFs
- **WordExtractorExecutor** - Process Microsoft Word documents
- **PowerPointExtractorExecutor** - Extract content from presentations
- **ExcelExtractorExecutor** - Process spreadsheets and tabular data
- **AzureDocumentIntelligenceExtractor** - AI-powered document analysis
- **AzureContentUnderstandingExtractor** - 70+ prebuilt analyzers for invoices, receipts, forms

#### **Content Processing**
- **RecursiveTextChunkerExecutor** - Smart document chunking for RAG
- **TableRowSplitterExecutor** - Split tables into individual rows
- **FieldMapperExecutor** - Transform and map document fields
- **FieldSelectorExecutor** - Extract specific fields from documents

#### **AI-Powered Analysis**
- **EntityExtractionExecutor** - Extract entities (people, organizations, locations)
- **SummarizationExecutor** - Generate document summaries
- **SentimentAnalysisExecutor** - Analyze document sentiment
- **KeywordExtractorExecutor** - Extract key terms and phrases
- **LanguageDetectorExecutor** - Detect document language
- **TranslationExecutor** - Translate content between languages
- **PIIDetectorExecutor** - Identify personally identifiable information
- **ContentClassifierExecutor** - Classify documents by type/category
- **AzureOpenAIAgentExecutor** - Custom AI processing with prompts

#### **Knowledge Graph & Semantic Understanding**
- **KnowledgeGraphEntityExtractor** - Extract entities and relationships for graph
- **KnowledgeGraphWriter** - Store entities in graph database
- **KnowledgeGraphQuery** - Query and traverse knowledge graphs
- **KnowledgeGraphEnrichment** - Enhance graph with AI insights

#### **Embeddings & Search**
- **AzureOpenAIEmbeddingsExecutor** - Generate vector embeddings
- **AISearchIndexWriter** - Index documents for semantic search

#### **Orchestration & Control Flow**
- **BatchSplitterExecutor** - Split work into batches for parallel processing
- **BatchAggregatorExecutor** - Merge results from batch processing
- **ParallelExecutor** - Execute multiple paths concurrently
- **SubworkflowExecutor** - Nest pipelines for complex hierarchies
- **PassThroughExecutor** - Pass data without modification

#### **Output**
- **BlobOutputExecutor** - Write results to Azure Blob Storage

### 🔄 Powerful Workflow Patterns

ContentFlow supports sophisticated workflow orchestration:

#### **Sequential Processing**
```yaml
workflow:
  - id: retrieve
    type: content_retriever
  - id: extract
    type: pdf_extractor
  - id: analyze
    type: azure_openai_agent
  - id: index
    type: ai_search_index_output
```

#### **Parallel Processing (Fan-Out/Fan-In)**
Process multiple paths simultaneously and merge results:
```yaml
workflow:
  edges:
    - from: retrieve
      to: [extract_text, extract_tables, extract_images]
    - from: [extract_text, extract_tables, extract_images]
      to: merge
```

#### **Conditional Routing**
Route documents based on properties or AI decisions:
```yaml
workflow:
  edges:
    - from: classifier
      to: invoice_processor
      condition: "document.type == 'invoice'"
    - from: classifier
      to: contract_processor
      condition: "document.type == 'contract'"
```

#### **Batch Processing**
Process large document collections efficiently:
```yaml
workflow:
  - id: split
    type: batch_splitter
    settings:
      batch_size: 10
  - id: process
    type: pdf_extractor
  - id: aggregate
    type: batch_aggregator
```

#### **Nested Subworkflows**
Build complex multi-level processing hierarchies:
```yaml
workflow:
  - id: process_pages
    type: subworkflow
    settings:
      workflow_name: page_processor
      process_field: pages
```

### 📊 Production Features

- **Event Streaming**: Real-time monitoring and observability
- **Error Handling**: Configurable retry policies and fallback strategies
- **Async/Await**: High-performance asynchronous execution
- **Type Safety**: Full Pydantic model integration
- **Schema Validation**: Automatic validation of executor configurations
- **Executor Catalog**: Dynamic loading and discovery of executors
- **Environment Variables**: `${VAR_NAME}` syntax in YAML configs
- **Lifecycle Management**: Context managers for resource cleanup

## Use Cases & Industry Applications

### 📄 Document Intelligence & Automation

#### **Invoice & Receipt Processing**
- Extract structured data from invoices using Azure Content Understanding
- Classify documents by type (invoice, receipt, purchase order)
- Validate extracted fields and flag anomalies
- Export to ERP systems or databases

#### **Contract Analysis**
- Extract key clauses and obligations
- Identify parties, dates, and monetary values
- Flag risky terms using AI analysis
- Generate summaries for legal review

#### **Form Processing**
- Process applications, claims, and forms
- Extract structured fields with 70+ prebuilt analyzers
- Validate completeness and accuracy
- Route to appropriate workflows

### 🔍 Enterprise Search & RAG (Retrieval-Augmented Generation)

#### **Intelligent Document Indexing**
- Chunk documents for optimal retrieval
- Generate vector embeddings
- Index to Azure AI Search
- Enable semantic search across enterprise content

#### **RAG Pipeline for AI Assistants**
```
Ingest → Extract → Chunk → Embed → Index → Query → Generate
```
Build production-grade RAG systems with pre-configured pipelines.

#### **Multi-Modal Search**
- Process documents, images, audio, and video
- Extract content optimized for search
- Build unified search across content types

### 🧠 Knowledge Graph & Semantic Networks

#### **Build Evolving Knowledge Graphs**
- Extract entities (people, organizations, products, locations)
- Identify relationships (works_at, manages, located_in)
- Store in Azure Cosmos DB Graph API
- Query and traverse the knowledge graph
- Enrich with AI-generated insights

#### **Organization Intelligence**
- Map organizational structures
- Track relationships between entities
- Discover hidden connections
- Analyze network patterns

### 📊 Content Analytics & Intelligence

#### **Large-Scale Document Analysis**
- Batch process thousands of documents
- Extract key entities and topics
- Perform sentiment analysis
- Generate summaries and insights
- Aggregate statistics across corpus

#### **Compliance & Risk Management**
- Detect PII (Personally Identifiable Information)
- Classify documents by sensitivity
- Flag compliance issues
- Track document lineage

### 🌐 Web Content Processing

#### **Web Scraping & Monitoring**
- Extract content from websites
- Monitor changes over time
- Process web pages for RAG
- Build web content repositories

### 🔄 Data Migration & Transformation

#### **Content Migration Pipelines**
- Retrieve documents from legacy systems
- Transform formats and structures
- Enrich with AI-generated metadata
- Load into modern systems

#### **ETL for Unstructured Data**
- Extract from multiple sources (Blob, SharePoint, local)
- Transform with AI processing
- Load into search indexes or databases

### 📈 Business Process Automation

#### **Email Attachment Processing**
- Monitor blob containers for new uploads
- Classify attachments by type
- Extract data based on document type
- Route to appropriate systems
- Notify stakeholders

#### **Report Generation**
- Aggregate data from multiple documents
- Generate summaries and insights
- Create structured outputs
- Distribute to stakeholders

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    ContentFlow Platform                      │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────────┐         ┌──────────────────┐          │
│  │  YAML Config     │────────▶│ PipelineFactory  │          │
│  │  (Declarative)   │         │  (Orchestrator)  │          │
│  └──────────────────┘         └─────────┬────────┘          │
│                                          │                    │
│         ┌────────────────────────────────┼──────────┐        │
│         │                                │          │        │
│         ▼                                ▼          ▼        │
│  ┌─────────────┐              ┌──────────────────────────┐  │
│  │ Connector   │              │   Executor Registry      │  │
│  │  Registry   │              │   - 40+ Pre-built        │  │
│  │             │              │   - Dynamic Loading      │  │
│  │ • Blob      │              │   - Schema Validation    │  │
│  │ • AI Search │              └────────┬─────────────────┘  │
│  │ • OpenAI    │                       │                    │
│  │ • Doc Intel │                       │                    │
│  │ • Cosmos DB │                       │                    │
│  └─────────────┘                       │                    │
│                                         │                    │
│                      ┌──────────────────┴──────────────┐    │
│                      │                                  │    │
│               ┌──────▼───────┐               ┌─────────▼────┐
│               │   Workflow   │               │   Workflow   │
│               │   Engine     │───Events─────▶│  Monitoring  │
│               │ (Agent Fwk)  │               │   & Logging  │
│               └──────────────┘               └──────────────┘
│                                                               │
└─────────────────────────────────────────────────────────────┘
                          │
                          │ Azure Services
                          ▼
        ┌────────────────────────────────────────┐
        │  • Blob Storage                         │
        │  • AI Search                            │
        │  • OpenAI / AI Inference                │
        │  • Document Intelligence                │
        │  • Content Understanding                │
        │  • Cosmos DB (Graph API)                │
        └────────────────────────────────────────┘
```

## Getting Started

### Quick Start (5 Minutes)

```bash
# 1. Set environment variables
export STORAGE_ACCOUNT=mystorageaccount
export DOCUMENT_INTELLIGENCE_ENDPOINT=https://mydocint.cognitiveservices.azure.com
export SEARCH_ENDPOINT=https://mysearch.search.windows.net
export OPENAI_ENDPOINT=https://myopenai.openai.azure.com

# 2. Create config.yaml
cat > config.yaml << EOF
connectors:
  - name: storage
    type: blob_storage
  - name: doc_intel
    type: document_intelligence
  - name: search
    type: ai_search

workflows:
  process_invoice:
    start: retrieve
    executors:
      - id: retrieve
        type: content_retriever
      - id: extract
        type: azure_document_intelligence_extractor
      - id: index
        type: ai_search_index_output
    edges:
      - from: retrieve
        to: extract
      - from: extract
        to: index
EOF

# 3. Run pipeline
python run_pipeline.py --config config.yaml --workflow process_invoice
```

### Installation

```bash
# Install Microsoft Agent Framework
pip install agent-framework-azure-ai --pre

# Install ContentFlow
cd contentflow-lib
pip install -e .
```

## Example: RAG Pipeline in 10 Lines

```python
from contentflow.pipeline import PipelineExecutor

# Load and execute pre-configured RAG workflow
async with PipelineExecutor.from_config_file(
    "rag_pipeline.yaml",
    "ingest_for_rag"
) as executor:
    result = await executor.execute({
        "source": "az://mycontainer/documents/annual_report.pdf"
    })
    print(f"Indexed {result.data['chunks_indexed']} chunks")
```

## Platform Components

### ContentFlow-Lib (Core Library)

**Description:** The core Python library that provides the foundation for building document processing workflows. It contains all executor implementations, connector integrations, pipeline orchestration logic, and configuration management. This is the heart of the ContentFlow platform that can be used standalone or as part of the larger platform.

**Key Responsibilities:**
- Executor implementations (40+ pre-built processors)
- Connector registry and Azure service integrations
- Pipeline orchestration using Microsoft Agent Framework
- Schema validation and type safety
- YAML configuration parsing with environment variable support
- Event streaming and monitoring
- Sample workflows and documentation

#### Project Structure

```
contentflow-lib/
├── contentflow/                      # Main package directory
│   ├── __init__.py
│   ├── connectors/                   # Azure service connectors
│   │   ├── __init__.py
│   │   ├── base.py                   # Base connector interface
│   │   ├── connector_registry.py     # Connector registration
│   │   ├── azure_blob_connector.py   # Azure Blob Storage
│   │   ├── ai_search_connector.py    # Azure AI Search
│   │   ├── ai_inference_connector.py # Azure OpenAI/AI Inference
│   │   ├── document_intelligence_connector.py  # Document Intelligence
│   │   ├── content_understanding_connector.py  # Content Understanding
│   │   └── cosmos_gremlin_connector.py         # Cosmos DB Graph API
│   │
│   ├── executors/                    # Workflow executors (40+)
│   │   ├── __init__.py
│   │   ├── base.py                   # Base executor interface
│   │   ├── executor_registry.py      # Executor registration
│   │   ├── executor_config.py        # Configuration models
│   │   │
│   │   # Input executors
│   │   ├── content_retriever.py      # Universal content retrieval
│   │   ├── azure_blob_input_executor.py
│   │   ├── web_scraping_executor.py
│   │   │
│   │   # Document extraction executors
│   │   ├── pdf_extractor.py
│   │   ├── word_extractor.py
│   │   ├── powerpoint_extractor.py
│   │   ├── excel_extractor.py
│   │   ├── azure_document_intelligence_extractor.py
│   │   ├── azure_content_understanding_extractor.py
│   │   │
│   │   # Content processing executors
│   │   ├── recursive_text_chunker_executor.py
│   │   ├── table_row_splitter_executor.py
│   │   ├── field_mapper_executor.py
│   │   ├── field_selector_executor.py
│   │   │
│   │   # AI-powered analysis executors
│   │   ├── entity_extraction_executor.py
│   │   ├── summarization_executor.py
│   │   ├── sentiment_analysis_executor.py
│   │   ├── keyword_extractor_executor.py
│   │   ├── language_detector_executor.py
│   │   ├── translation_executor.py
│   │   ├── pii_detector_executor.py
│   │   ├── content_classifier_executor.py
│   │   ├── azure_openai_agent_executor.py
│   │   │
│   │   # Knowledge graph executors
│   │   ├── knowledge_graph_entity_extractor.py
│   │   ├── knowledge_graph_writer.py
│   │   ├── knowledge_graph_query.py
│   │   ├── knowledge_graph_enrichment.py
│   │   │
│   │   # Embeddings & search executors
│   │   ├── azure_openai_embeddings_executor.py
│   │   ├── ai_search_index_output.py
│   │   │
│   │   # Orchestration executors
│   │   ├── batch_splitter.py
│   │   ├── batch_aggregator.py
│   │   ├── batch_processor.py
│   │   ├── parallel_executor.py
│   │   ├── parallel.py
│   │   ├── subworkflow.py
│   │   ├── pass_through.py
│   │   │
│   │   # Output executors
│   │   └── azure_blob_output_executor.py
│   │
│   ├── pipeline/                     # Pipeline orchestration
│   │   ├── __init__.py
│   │   ├── _pipeline.py              # Core pipeline logic
│   │   ├── _pipeline_executor.py     # Execution engine
│   │   └── pipeline_factory.py       # Factory for creating pipelines
│   │
│   ├── models/                       # Data models
│   │   ├── __init__.py
│   │   └── _content.py               # Document content models
│   │
│   └── utils/                        # Utility functions
│       ├── __init__.py
│       ├── config_provider.py        # Configuration management
│       ├── credential_provider.py    # Azure credential handling
│       ├── make_safe_json.py         # JSON sanitization
│       └── ttl_cache.py              # Caching utilities
│
├── samples/                          # Example workflows (28+)
│   ├── README.md                     # Sample documentation
│   ├── 01-simple/                    # Basic workflow example
│   ├── 02-batch-processing/          # Batch processing patterns
│   ├── 03-pdf-extractor_chunker/     # PDF extraction & chunking
│   ├── 04-word-extractor/            # Word document processing
│   ├── 05-powerpoint-extractor/      # PowerPoint processing
│   ├── 06-ai-analysis/               # AI-powered analysis
│   ├── 07-embeddings/                # Vector embeddings
│   ├── 08-content-understanding/     # Content Understanding service
│   ├── 09-blob-input/                # Blob storage input
│   ├── 10-table-row-splitter/        # Table processing
│   ├── 11-excel-extractor/           # Excel processing
│   ├── 12-field-transformation/      # Field mapping
│   ├── 13-blob-output-sample/        # Blob storage output
│   ├── 14-gpt-rag-ingestion/         # RAG pipeline
│   ├── 15-document-analysis/         # Document analysis
│   ├── 16-spreadsheet-pipeline/      # Spreadsheet workflows
│   ├── 17-knowledge-graph/           # Knowledge graph construction
│   ├── 18-web-scraping/              # Web content extraction
│   ├── 19-sub-pipelines/             # Nested workflows
│   ├── 27-subpipeline-processing/    # Advanced subworkflows
│   ├── 28-advanced-batch/            # Advanced batch patterns
│   ├── 32-parallel-processing/       # Parallel execution
│   ├── 44-conditional-routing/       # Conditional logic
│   └── 99-assets/                    # Sample documents
│
├── tests/                            # Unit and integration tests
│
├── executor_catalog.yaml             # Executor definitions & schemas
├── pyproject.toml                    # Python project configuration
├── requirements.txt                  # Python dependencies
├── setup.sh                          # Environment setup script
├── README.md                         # Getting started guide
├── PROJECT_OVERVIEW.md               # This file
├── KNOWLEDGE_GRAPH_SUMMARY.md        # Knowledge graph documentation
├── EXECUTOR_CATALOG.md               # Executor reference
├── PIPELINE_EXECUTOR.md              # Pipeline execution guide
└── todo.txt                          # Development roadmap
```

### ContentFlow-API (REST API)
- RESTful endpoints for pipeline execution
- Job management and monitoring
- Async execution support
- API authentication and authorization

### ContentFlow-Web (Web UI)
- Visual pipeline designer
- Executor catalog browser
- Real-time execution monitoring
- Configuration management

### ContentFlow-Worker (Background Processor)
- Queue-based processing
- Horizontal scalability
- Long-running job execution
- Error recovery and retries

## Why Choose ContentFlow?

### ✅ Rapid Development
- Build production pipelines in **hours, not weeks**
- Pre-built executors eliminate 80% of custom code
- YAML configuration reduces development time by 90%

### ✅ Enterprise Ready
- Production-proven with Azure managed identity
- Built-in error handling and retries
- Comprehensive monitoring and observability
- Scales horizontally with worker architecture

### ✅ Flexible & Extensible
- Add custom executors in Python
- Extend with custom connectors
- Plugin architecture for new capabilities
- Open and hackable codebase

### ✅ Cost Efficient
- Optimize Azure API usage with batching
- Parallel processing reduces processing time
- Smart caching reduces redundant operations
- Pay-per-use model with Azure services

### ✅ Developer Friendly
- Intuitive YAML syntax
- Type-safe Python codebase
- Comprehensive documentation
- Rich sample library (28+ examples)

## Learn More

- **[README.md](README.md)** - Installation and quick start guide
- **[samples/](samples/)** - 28+ working examples covering all patterns
- **[EXECUTOR_CATALOG.md](EXECUTOR_CATALOG.md)** - Complete executor reference
- **[PIPELINE_EXECUTOR.md](PIPELINE_EXECUTOR.md)** - Pipeline execution guide
- **[KNOWLEDGE_GRAPH_SUMMARY.md](KNOWLEDGE_GRAPH_SUMMARY.md)** - Knowledge graph capabilities

## License

MIT License - see LICENSE file for details

---

**Built on [Microsoft Agent Framework](https://github.com/microsoft/agent-framework)** | **Powered by Azure AI**
