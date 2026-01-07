<p align="center">
    <h1 align="left" style="font-size:3em;">
    <picture>
    <img src="./contentflow-web/public/contentflow.svg" alt="ContentFlow Logo" style="width:34px;" />
    </picture>
    ContentFlow
    </h1>
</p>

> **Intelligent, scalable content processing pipelines powered by Azure AI and orchestrated by Microsoft Agent Framework**

[![Azure](https://img.shields.io/badge/Azure-Powered-0078D4?logo=microsoft-azure)](https://azure.microsoft.com)
[![Python 3.12+](https://img.shields.io/badge/Python-3.12+-3776ab?logo=python)](https://www.python.org)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.8+-3178c6?logo=typescript)](https://www.typescriptlang.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-Modern_API-009485)](https://fastapi.tiangolo.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 📋 What is ContentFlow?

**ContentFlow** is an enterprise-grade document and content processing platform that transforms unstructured content into intelligent, actionable data. It combines:

- 🔄 **Orchestrated Workflows** - YAML-based pipeline definitions with conditional routing and parallel execution
- 🤖 **AI-Powered Processing** - Integration with Azure AI services for document intelligence, embeddings, and analysis
- 📦 **Modular Executors** - 40+ pre-built processors for PDF, Word, Excel, PowerPoint, and more
- 🌐 **Cloud-Native Architecture** - Deployed on Azure Container Apps with distributed processing
- 💻 **Intuitive Web UI** - React-based interface for pipeline design and monitoring
- ⚡ **Scalable & Distributed** - Multi-worker architecture for processing at scale

---

## ✨ Key Features

### 🎯 Powerful Content Processing
- **Multi-Format Support**: PDF, Word, Excel, PowerPoint, plain text, web content, audio, video
- **OCR & Layout Analysis**: Extract text from scanned documents with layout preservation
- **Intelligent Extraction**: Tables, images, metadata, document structure
- **Content Understanding**: Chunking, embedding generation, semantic analysis
- **Knowledge Graphs**: Extract and build relationships between entities

### 🔗 Advanced Workflow Capabilities
- **Conditional Routing**: Dynamic paths based on document properties
- **Parallel Processing**: Fan-out/fan-in patterns with result aggregation
- **Batch Operations**: Efficient processing of large document collections
- **Sub-Pipelines**: Hierarchical workflow composition for complex scenarios
- **Error Handling**: Automatic retry logic and graceful degradation

### 🧠 AI Integration
- **Document Intelligence**: Extract text, tables, key-value pairs from documents
- **Embeddings**: Generate semantic vectors for similarity search and RAG
- **Content Analysis**: Sentiment, entity extraction, topic classification
- **Web Scraping**: Dynamic content extraction with Playwright

### 🔐 Enterprise Ready
- **Azure AI Landing Zone Integration**: Secure deployment within enterprise environments
- **RBAC & Identity**: Managed identities and role-based access control
- **Audit & Monitoring**: Comprehensive logging and Application Insights
- **Data Isolation**: Blob storage and Cosmos DB for persistent data management

---

## 🎬 Quick Start

### Prerequisites
- Azure subscription with necessary services configured
- Python 3.12+
- Docker (for running locally)
- Node.js 18+ (for web UI development)


### Deploy to Azure
Supports two modes:
 - Basic mode for quick setup for development and testing
 - Azure AI Landing Zone integrated mode for an Enterprise level deployment

 ➡️ **[View deployment docs for more details](./infra/README.md)**

```shell
git clone https://github.com/Azure/contentflow
cd contentflow

# One-command deployment
azd up

# This will:
# 1. Provision Azure infrastructure (Container Apps, Storage, Cosmos DB, etc.)
# 2. Build and push container images
# 3. Deploy services
# 4. Configure post-deployment settings
# 5. Output service URLs
```

### Local Development

```shell
# API service
cd contentflow-api
pip install -r requirements.txt
python main.py

# Worker service
cd contentflow-worker
pip install -r requirements.txt
python main.py

# Web UI
cd contentflow-web
npm install
npm run dev
```

---

## 📚 Real-World Use Cases

### 📄 Document Intelligence & Archival
**Scenario**: Enterprise needs to digitize and catalog thousands of historical documents

```
Input Documents → PDF Extraction → OCR & Layout Analysis → Metadata Extraction → Full-Text Indexing → Archive Storage
```

**Benefits**: Searchable digital archives, compliance automation, instant retrieval

---

### 🧠 RAG (Retrieval-Augmented Generation) Pipeline
**Scenario**: Build a knowledge base from company documents for AI-powered Q&A

```
Documents → Chunking → Embedding Generation → Vector Search Indexing → LLM Query Augmentation
```

**ContentFlow Powers**: Batch processing thousands of documents, generating embeddings, storing in vector DB

---

### 📊 Financial Document Analysis
**Scenario**: Extract financial data from quarterly reports, earnings calls, and regulatory filings

```
Financial Documents → Extract Tables → Parse Key Metrics → Classify Document Type → Store in Data Warehouse
```

**Smart Features**: 
- Conditional routing based on document type
- Parallel processing of multiple sections
- Automatic retry on extraction failure

---

### 🛒 E-Commerce Content Catalog
**Scenario**: Process product descriptions, images, and specifications across multiple formats

```
Product Files (PDF, DOC, XLSX) → Content Extraction → Image Processing → Standardization → Catalog Upload
```

**Powered By**: Batch operations, format-specific extractors, validation logic

---

### 🏥 Healthcare Records Processing
**Scenario**: Convert paper records and scanned documents into structured patient data

```
Scanned Records → OCR → Medical Entity Extraction → HIPAA Compliance Validation → EHR Integration
```

**Enterprise Features**: Audit logging, encryption, RBAC, data isolation

---

### 📰 News & Content Aggregation
**Scenario**: Crawl websites and aggregate news articles with AI analysis

```
Web URLs → Web Scraping → Content Extraction → Sentiment Analysis → Topic Classification → Distribution
```

**Automation**: Parallel scraping, conditional routing, scheduled execution

---

## 🏗️ High-Level Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                    ContentFlow Platform                      │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│                      User Interfaces                         │
├──────────────────────────────┬───────────────────────────────┤
│   Web Dashboard (React)      │   REST API (FastAPI)          │
│  • Pipeline Designer         │   • Execute Pipelines         │
│  • Execution Monitoring      │   • Get Results               │
│  • Result Visualization      │   • Query History             │
└──────────────────────────────┴───────────────────────────────┘
                               ↓
┌──────────────────────────────────────────────────────────────┐
│              ContentFlow API Service                         │
│  (containerapp-api)                                          │
│  ✓ Pipeline Management & Execution                           │
│  ✓ Credential & Vault Integration                            │
│  ✓ Event Streaming & Monitoring                              │
└──────────────────────────────────────────────────────────────┘
         ↑                              ↓
    Config/Tasks             Results & Events
         ↑                              ↓
┌──────────────────────────────────────────────────────────────┐
│           ContentFlow Library (Core Engine)                  │
├──────────────────────────────────────────────────────────────┤
│                    Pipeline Factory                          │
│  • Parses YAML configurations                                │
│  • Validates executor dependencies                           │
│  • Creates optimized execution graphs                        │
├──────────────────────────────────────────────────────────────┤
│              40+ Pre-Built Executors                         │
├───────────────────────────┬──────────────────────────────────┤
│  Input Executors          │  Processing Executors            │
│  • Azure Blob Discovery   │  • PDF Text Extraction           │
│  • Local File Reader      │  • Document Intelligence         │
│  • Web Scraper            │  • Image Processing              │
│  • Database Query         │  • Embeddings Generation         │
├───────────────────────────┼──────────────────────────────────┤
│  Routing Executors        │  Output Executors                │
│  • Conditional Router     │  • Azure Blob Writer             │
│  • Batch Splitter         │  • Cosmos DB Storage             │
│  • Parallel Executor      │  • CSV/JSON Export               │
│  • Merge Aggregator       │  • Search Index Upload           │
└───────────────────────────┴──────────────────────────────────┘
                        ↓
┌──────────────────────────────────────────────────────────────┐
│        ContentFlow Worker Service                            │
│  (containerapp-worker)                                       │
│  ✓ Processes queued work items                               │
│  ✓ Manages worker pool & scaling                             │
│  ✓ Executes pipeline instances                               │
│  ✓ Handles failures & retries                                │
└──────────────────────────────────────────────────────────────┘
                        ↓
┌──────────────────────────────────────────────────────────────┐
│            Azure Services Integration                        │
├───────────────────────┬─────────────────┬────────────────────┤
│ Storage & Data        │ AI Services     │ Infrastructure     │
│ • Azure Blob Storage  │ • Document      │ • Container Apps   │
│ • Cosmos DB           │   Intelligence  │ • App Config       │
│ • Queue Storage       │ • AI Services   │ • Key Vault        │
│ • Search Index        │ • OpenAI/Models │ • Log Analytics    │
│                       │ • Embeddings    │ • App Insights     │
└───────────────────────┴─────────────────┴────────────────────┘
```

### Component Details

**[Web Dashboard (`contentflow-web`)](./contentflow-web/README.md)**
- Modern React application with Vite
- Visual pipeline designer with React Flow
- Real-time execution monitoring
- Results viewer with syntax highlighting
- Responsive Tailwind CSS design

**[API Service (`contentflow-api`)](./contentflow-api/README.md)**
- FastAPI REST endpoints for pipeline operations
- AsyncIO-based for high concurrency
- WebSocket support for real-time events
- Integration with Azure Key Vault for secrets
- CORS configured for web UI

**[Worker Service (`contentflow-worker`)](./contentflow-worker/README.md)**
- Multi-threaded content processing engine
- Queue-based job distribution
- Automatic scaling based on load
- Health monitoring and graceful shutdown
- Error handling with exponential backoff

**[Core Library (`contentflow-lib`)](./contentflow-lib/README.md)**
- Pipeline Factory: Compiles YAML to execution graphs
- Executor Framework: Base classes and 40+ implementations
- Content Models: Strongly-typed data structures
- Event System: Real-time pipeline execution tracking
- Plugin Architecture: Easy extension with custom executors

---

## 🔧 Configuration & Customization

### Define a Pipeline (YAML)

```yaml
pipeline:
  name: document_processing
  description: "Process documents with intelligence"
  
  executors:
    - id: get_content
      type: azure_blob_input_discovery
      settings:
        blob_storage_account: "${STORAGE_ACCOUNT}"
        blob_container_name: "documents"
        file_extensions: ".pdf,.docx"
    
    - id: extract_text
      type: azure_document_intelligence_extractor
      settings:
        doc_intelligence_endpoint: "${DOC_INT_ENDPOINT}"
    
    - id: generate_embeddings
      type: embeddings_executor
      settings:
        model: "text-embedding-3-large"
    
    - id: store_results
      type: cosmos_db_writer
      settings:
        database_name: "contentflow"
        container_name: "documents"
  
  # Execution sequence with conditional routing
  edges:
    - from: get_content
      to: extract_text
    
    - from: extract_text
      to: generate_embeddings
      condition: "output.pages > 0"
    
    - from: generate_embeddings
      to: store_results
```

### Run Programmatically (Python)

```python
from contentflow.pipeline import PipelineExecutor
from contentflow.models import Content, ContentIdentifier

async with PipelineExecutor.from_config_file(
    config_path="my_pipeline.yaml",
    pipeline_name="document_processing"
) as executor:
    
    # Create content to process
    document = Content(
        id=ContentIdentifier(
            canonical_id="doc_001",
            unique_id="doc_001",
            source_name="azure_blob",
            source_type="pdf",
            path="documents/report.pdf"
        )
    )
    
    # Execute pipeline
    result = await executor.execute(document)
    
    # Check results
    print(f"Status: {result.status}")
    print(f"Duration: {result.duration_seconds}s")
    for event in result.events:
        print(f"  {event.executor_id}: {event.message}")
```

---

## 📦 Project Structure

```
contentflow/
├── contentflow-api/              # FastAPI REST service
│   ├── app/
│   │   ├── routers/             # API endpoint definitions
│   │   ├── services/            # Business logic
│   │   ├── dependencies.py      # Dependency injection
│   │   └── settings.py          # Configuration
│   ├── main.py                  # Application entry
│   └── Dockerfile
│
├── contentflow-lib/              # Core processing library
│   ├── contentflow/
│   │   ├── pipeline/            # Pipeline execution engine
│   │   ├── executors/           # 40+ executor implementations
│   │   ├── connectors/          # Data source connectors
│   │   ├── models/              # Data models
│   │   └── utils/               # Utilities
│   ├── samples/                 # 20+ example pipelines
│   ├── executor_catalog.yaml    # Executor registry
│   └── pyproject.toml
│
├── contentflow-web/              # React web dashboard
│   ├── src/
│   │   ├── components/          # Reusable UI components
│   │   ├── pages/               # Page components
│   │   ├── hooks/               # Custom React hooks
│   │   └── lib/                 # Utilities & helpers
│   ├── vite.config.ts           # Build configuration
│   └── Dockerfile
│
├── contentflow-worker/           # Processing worker service
│   ├── app/
│   │   ├── engine.py            # Worker engine
│   │   ├── api.py               # Health/status endpoints
│   │   └── settings.py          # Configuration
│   ├── main.py                  # Entry point
│   └── Dockerfile
│
└── infra/                        # Infrastructure as Code
    ├── bicep/
    │   ├── main.bicep          # Main template
    │   └── modules/            # Reusable Bicep modules
    └── scripts/                # Deployment automation
```

---

## 🎯 Executor Catalog

ContentFlow includes **40+ pre-built executors** for common content processing tasks:

### Input Executors
- `azure_blob_input_discovery` - Discover files in Blob Storage
- `local_file_reader` - Read files from local filesystem
- `web_scraper` - Extract content from web pages
- `database_query` - Retrieve content from databases

### Extraction Executors
- `azure_document_intelligence_extractor` - Extract text, tables, layout
- `pdf_text_extractor` - PDF-specific text extraction
- `pdf_image_extractor` - Extract images from PDFs
- `word_document_extractor` - Process Word documents
- `excel_spreadsheet_extractor` - Extract Excel data
- `powerpoint_extractor` - Process PowerPoint presentations

### Processing Executors
- `text_chunker` - Split text into optimal chunks
- `embeddings_executor` - Generate semantic embeddings
- `classifier_executor` - Text classification
- `entity_extractor` - Named entity recognition
- `sentiment_analyzer` - Sentiment analysis
- `table_row_splitter` - Extract table rows as documents
- `field_transformer` - Transform and normalize fields

### Routing Executors
- `conditional_router` - Route based on conditions
- `batch_splitter` - Split large batches
- `parallel_executor` - Execute in parallel
- `merge_aggregator` - Aggregate results from parallel paths

### Output Executors
- `azure_blob_writer` - Write to Blob Storage
- `cosmos_db_writer` - Store in Cosmos DB
- `search_index_writer` - Index for search

---

## 📊 Example Pipelines

ContentFlow comes with **20+ sample pipelines** demonstrating various patterns:

| Sample | Demonstrates | Files |
|--------|--------------|-------|
| `01-simple` | Basic pipeline setup | Config + simple execution |
| `02-batch-processing` | Processing large collections | Batch splitting & aggregation |
| `03-pdf-extractor` | PDF content extraction | Multi-stage PDF processing |
| `04-word-extractor` | Word document processing | Document intelligence |
| `05-powerpoint-extractor` | PowerPoint analysis | Slide extraction |
| `06-ai-analysis` | AI-powered analysis | LLM integration |
| `07-embeddings` | Embedding generation | Vector search prep |
| `08-content-understanding` | Semantic analysis | Chunking & classification |
| `09-blob-input` | Blob storage integration | Cloud file discovery |
| `14-gpt-rag-ingestion` | RAG pipeline | GPT + embeddings |
| `15-document-analysis` | Advanced intelligence | Comprehensive analysis |
| `17-knowledge-graph` | Entity relationships | Graph construction |
| `18-web-scraping` | Web content extraction | Dynamic scraping |
| `32-parallel-processing` | Concurrent execution | Multi-path workflows |
| `44-conditional-routing` | Smart routing | Condition-based paths |

Run any sample:

```bash
cd contentflow-lib/samples/01-simple
python run.py
```

---

## 🔐 Security & Compliance

✅ **Managed Identity Authentication** - No exposed credentials  
✅ **Azure Key Vault Integration** - Secure secret storage  
✅ **RBAC & Access Control** - Fine-grained permissions  
✅ **Encrypted Communication** - TLS for all endpoints  
✅ **Audit & Logging** - Full audit trail with Application Insights  
✅ **Data Isolation** - Separate storage containers per tenant/environment  
✅ **Compliance Ready** - Supports HIPAA, SOC 2, GDPR patterns  

---

## 📈 Performance & Scalability

| Metric | Capability |
|--------|------------|
| **Throughput** | 100+ documents/hour per worker |
| **Concurrency** | Unlimited parallel pipelines |
| **Scaling** | Auto-scale Container Apps based on queue depth |
| **Latency** | <1s for simple operations, <30s for complex AI |
| **Reliability** | Automatic retry, fault tolerance, graceful degradation |
| **Storage** | Unlimited with Blob Storage + Cosmos DB |

---

## 📖 Documentation & Resources

- **[Infrastructure Guide](infra/README.md)** - Deploy to Azure
- **[API Documentation](contentflow-api/README.md)** - REST endpoints
- **[Sample Pipelines](contentflow-lib/samples/README.md)** - Learn by example
- **[Web UI Guide](contentflow-web/README.md)** - Dashboard features

---

## 🤝 Contributing

We welcome contributions! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🚀 Getting Help

- **Issues**: Report bugs and request features on [GitHub Issues](../../issues)
- **Discussions**: Ask questions and share ideas in [Discussions](../../discussions)
- **Documentation**: Check our comprehensive [docs](docs/)
- **Examples**: Explore [sample pipelines](contentflow-lib/samples/)

---

<div align="center">

### 💡 Start Processing Content Intelligently Today

[Deploy to Azure](infra/README.md) · [View Samples](contentflow-lib/samples/) · [API Reference](contentflow-api/README.md) · [Report Issue](../../issues)

**Made with ❤️ using Microsoft Azure & Agent Framework**

</div>
