# ContentFlow — Complete Reference Analysis

> **Single-file reference document for AI agents and developers.**  
> This document consolidates all capabilities, architecture, prerequisites, out-of-scope boundaries, and example scenarios for the ContentFlow accelerator. Use it as the authoritative context source before working with this codebase.

---

## Table of Contents

1. [What is ContentFlow?](#1-what-is-contentflow)
2. [Core Concepts](#2-core-concepts)
3. [Full Capabilities](#3-full-capabilities)
   - [3.1 Built-in Executors (37 total)](#31-built-in-executors-37-total)
   - [3.2 Pipeline Engine Features](#32-pipeline-engine-features)
   - [3.3 Web UI Features](#33-web-ui-features)
   - [3.4 API Features](#34-api-features)
   - [3.5 Worker Engine Features](#35-worker-engine-features)
   - [3.6 Extensibility: Custom Executors](#36-extensibility-custom-executors)
4. [Prerequisites](#4-prerequisites)
   - [4.1 Azure Services Required](#41-azure-services-required)
   - [4.2 Developer Toolchain](#42-developer-toolchain)
   - [4.3 Azure Permissions](#43-azure-permissions)
   - [4.4 Service Quotas & Limits](#44-service-quotas--limits)
5. [Final Architecture](#5-final-architecture)
   - [5.1 Component Overview](#51-component-overview)
   - [5.2 Service Communication Map](#52-service-communication-map)
   - [5.3 Data Flow](#53-data-flow)
   - [5.4 Task Lifecycle](#54-task-lifecycle)
   - [5.5 Cosmos DB Schema](#55-cosmos-db-schema)
   - [5.6 Deployment Modes](#56-deployment-modes)
   - [5.7 Security Model](#57-security-model)
6. [Out of Scope](#6-out-of-scope)
7. [Example Scenarios](#7-example-scenarios)
   - [7.1 Invoice & Receipt Processing](#71-invoice--receipt-processing)
   - [7.2 Enterprise Knowledge Base for RAG](#72-enterprise-knowledge-base-for-rag)
   - [7.3 Contract Analysis](#73-contract-analysis)
   - [7.4 Engineering PDF BOM Extraction](#74-engineering-pdf-bom-extraction)
   - [7.5 Compliance & PII Detection](#75-compliance--pii-detection)
   - [7.6 Web Content Ingestion](#76-web-content-ingestion)
   - [7.7 Multilingual Document Translation](#77-multilingual-document-translation)
   - [7.8 Email Attachment Triage](#78-email-attachment-triage)
   - [7.9 Spreadsheet Data Pipeline](#79-spreadsheet-data-pipeline)
   - [7.10 Knowledge Graph Construction](#710-knowledge-graph-construction)
8. [Included Sample Pipelines](#8-included-sample-pipelines)

---

## 1. What is ContentFlow?

**ContentFlow** is an open-source, enterprise-grade, cloud-native document and content processing accelerator built on Azure. It transforms unstructured content — PDFs, Word documents, Excel files, PowerPoint presentations, CSV files, web pages, images — into structured, intelligent, actionable data through orchestrated AI-powered pipelines.

**Primary value proposition**: ContentFlow eliminates the infrastructure plumbing required to build scalable document processing systems on Azure. A developer can go from zero to a production-grade pipeline in hours rather than weeks by combining pre-built executors declaratively via YAML.

**Repository**: [Azure/contentflow](https://github.com/Azure/contentflow)  
**License**: MIT  
**Runtime**: Python 3.12+ (backend), TypeScript/React 18 (frontend)

---

## 2. Core Concepts

### Pipeline
A **pipeline** is the fundamental unit of work. It defines an ordered sequence of executors that content passes through. Pipelines are declared in YAML and stored in Cosmos DB.

```yaml
name: my-pipeline
steps:
  - executor: azure_blob_input_discovery
    settings:
      blob_container_name: documents
  - executor: azure_document_intelligence_extractor
    settings:
      doc_intelligence_endpoint: "${AZURE_DOC_INTELLIGENCE_ENDPOINT}"
  - executor: recursive_text_chunker
    settings:
      chunk_size: 1000
  - executor: azure_openai_embeddings
    settings:
      model: text-embedding-3-small
  - executor: ai_search_index_output
    settings:
      index_name: my-index
```

### Executor
An **executor** is a self-contained processing unit. Each executor receives a `Content` object, transforms or enriches it, and passes the result to the next step. Executors are composable, configurable via YAML settings, and can run in parallel.

### Vault
A **vault** is a logical container that associates a document source with a pipeline. When enabled, the Worker service automatically discovers new documents arriving in the vault and queues them for processing.

### Content Model
The standardized Python object (`Content`) that flows through every pipeline step:

```python
Content
  ├── id: ContentIdentifier  # canonical_id, source_type, container, path, filename
  ├── data: dict             # All executor outputs accumulate here
  ├── summary_data: dict     # Execution metrics per executor
  └── executor_logs: list    # Per-step audit trail
```

All executor outputs are stored as named fields in `content.data`, enabling downstream executors to reference previous results via dot-notation paths (e.g., `doc_intell_output.tables`).

---

## 3. Full Capabilities

### 3.1 Built-in Executors (37 total)

#### Input Executors (3)
| Executor ID | Description |
|---|---|
| `azure_blob_input_discovery` | Discovers files in Azure Blob Storage containers. Supports file extension filtering, prefix filtering, and incremental crawling via checkpoints (processes only new/modified blobs since last run). |
| `azure_blob_content_retriever` | Downloads blob content as bytes or saves to a temp file path for downstream processing. Supports parallel retrieval with configurable concurrency. |
| `content_retriever` | Loads content from local file system or arbitrary byte sources. Primarily used in local development and sample pipelines. |

#### Document Extraction Executors (6)
| Executor ID | Description |
|---|---|
| `azure_document_intelligence_extractor` | Invokes Azure Document Intelligence (prebuilt-layout, prebuilt-document, prebuilt-read) to extract text, tables, key-value pairs, and figures from any document. Supports markdown or plain text output format, page range selection, locale hints, and additional features like `ocrHighResolution`. |
| `azure_content_understanding_extractor` | Uses Azure Content Understanding for advanced document analysis including prebuilt invoice, receipt, business card, and ID models. |
| `pdf_extractor` | Extracts text, page-level chunks, and embedded images from PDF files using PyMuPDF. No Azure service dependency — runs locally. |
| `word_extractor` | Extracts text, headings, tables, and metadata from `.docx` files using python-docx. |
| `powerpoint_extractor` | Extracts slide content, speaker notes, embedded images, and metadata from `.pptx` files using python-pptx. |
| `excel_extractor` | Extracts sheets, tables, cell values, formulas, images, and metadata from `.xlsx`/`.xlsm` files using openpyxl. Supports first-row-as-header detection, sheet filtering, and table range detection. |
| `csv_extractor` | Parses CSV files with configurable delimiter, quoting, and encoding. |

#### AI Processing Executors (8)
| Executor ID | Description |
|---|---|
| `azure_openai_agent` | Sends content to Azure OpenAI (GPT-4.1, GPT-4.1-mini, etc.) with a configurable system prompt and user template. The most flexible executor — suitable for summarization, extraction, classification, transformation, and any custom reasoning task. |
| `azure_openai_embeddings` | Generates vector embeddings using Azure OpenAI embedding models (text-embedding-3-small, text-embedding-3-large). Output format compatible with Azure AI Search vector fields. |
| `text_summarizer` | Generates concise summaries with configurable max length and style. Built on `azure_openai_agent`. |
| `entity_extractor` | Extracts named entities (persons, organizations, dates, amounts, locations) from text. Configurable entity types. Built on `azure_openai_agent`. |
| `sentiment_analyser` | Document-level, sentence-level, or aspect-based sentiment analysis with confidence scores. Supports 3-point and 5-point scales and emotion detection. |
| `content_classifier` | Multi-class and multi-label classification with confidence scores and explanations. Accepts custom category lists and descriptions. |
| `pii_detector` | Detects and optionally redacts Personally Identifiable Information (PII) such as names, emails, phone numbers, SSNs, credit cards, addresses. |
| `keyword_extractor` | Extracts top-N keywords and key phrases from text content. |

#### Transformation Executors (6)
| Executor ID | Description |
|---|---|
| `recursive_text_chunker` | Splits long text into overlapping chunks using recursive character splitting with configurable chunk size, overlap, and separators. |
| `table_row_splitter` | Splits tabular data (list-of-lists, list-of-dicts, CSV string, Word tables, Excel rows) into individual `Content` objects — one per row — enabling per-row parallel processing downstream. |
| `field_mapper` | Renames, remaps, and transforms fields within `content.data` using a declarative mapping configuration. |
| `field_selector` | Includes or excludes specific fields from `content.data` to control what data is passed forward. |
| `language_detector` | Detects the primary language of text content. |
| `content_translator` | Translates content to one or more target languages using Azure OpenAI. |

#### Output Executors (3)
| Executor ID | Description |
|---|---|
| `azure_blob_output` | Writes processed content (JSON, text, binary) back to Azure Blob Storage. Supports custom path templates and content serialization. |
| `ai_search_index_output` | Indexes processed content into Azure AI Search. Supports vector fields, semantic configuration, and batch indexing. |
| `gptrag_search_index_document_generator` | Generates documents in GPT-RAG-compatible format for Azure AI Search, including chunked content and embeddings for RAG scenarios. |

#### Control Flow Executors (5)
| Executor ID | Description |
|---|---|
| `subpipeline` | Executes another pipeline as a nested sub-workflow. Enables pipeline composition and reuse. |
| `for_each_content` | Iterates over a list of content items and applies a sub-pipeline to each one. |
| `fan_in_aggregator` | Collects and merges results from parallel branches back into a single content stream. |
| `document_set_initializer` | Initializes a multi-document analysis session for cross-document operations. |
| `document_set_collector` | Collects documents into a set for batch cross-document processing. |

#### Cross-Document Executors (3)
| Executor ID | Description |
|---|---|
| `cross_document_comparison` | Compares multiple documents side-by-side using AI to identify similarities, differences, and patterns. |
| `cross_document_field_aggregator` | Aggregates specific fields across a document set (e.g., collect all "summary" fields from 50 documents). |
| `cosmos_db_lookup` | Looks up metadata or previously stored results from Cosmos DB during pipeline execution. Useful for enrichment and deduplication. |

#### Utility Executors (3)
| Executor ID | Description |
|---|---|
| `pass_through` | No-op executor. Useful for pipeline testing and debugging. |
| `web_scraper` | Crawls web pages using Playwright (headless Chromium). Supports CSS selectors, depth control, and JavaScript-rendered pages. |
| `cosmos_db_lookup` | Retrieves enrichment data from Cosmos DB based on a key field in the content. |

---

### 3.2 Pipeline Engine Features

- **Declarative YAML definition** — pipelines are stored as YAML and parsed at runtime
- **DAG execution** — pipelines can define explicit `execution_sequence` for dependency control
- **Async/await throughout** — all executors are async; built on Python asyncio
- **Parallel execution** — `ParallelExecutor` base class enables `max_concurrent` processing (default: 3 concurrent items)
- **Conditional execution** — any executor supports a `condition` setting (Python expression evaluated against `content.data`)
- **Error handling** — `fail_pipeline_on_error` and `continue_on_error` per executor; up to 3 retries with configurable delay
- **Timeout control** — per-executor `timeout_secs` setting
- **Debug mode** — verbose logging per executor via `debug_mode: true`
- **Nested fields** — all settings support dot-notation for accessing nested data (e.g., `doc_intell_output.tables`)
- **Environment variable substitution** — any setting value can reference env vars with `${VAR_NAME}` syntax
- **Sub-pipelines** — pipelines can invoke other pipelines as steps, enabling workflow composition
- **Parallel fan-out/fan-in** — native support for splitting content into parallel branches and merging results
- **Incremental processing** — vault crawl checkpoints prevent duplicate reprocessing

---

### 3.3 Web UI Features

**Technology**: React 18, TypeScript, Vite, Tailwind CSS, Shadcn/ui, Radix UI, ReactFlow, Monaco Editor

| Feature | Description |
|---|---|
| **Visual Pipeline Builder** | Drag-and-drop graphical interface built on ReactFlow. Nodes represent executors; edges represent data flow. |
| **YAML Editor** | Monaco-powered code editor with syntax highlighting for editing pipeline definitions directly. |
| **Template Gallery** | Pre-built pipeline templates for common scenarios, ready to clone and customize. |
| **Vault Management** | Create, edit, enable/disable document vaults. Associate vaults with pipelines. |
| **Execution Dashboard** | Real-time view of pipeline execution status, metrics, and per-executor output. |
| **Executor Catalog Browser** | Browse all 37 executors with descriptions, settings schemas, and usage examples. |
| **Knowledge Graph Viewer** | Visualization of entity-relationship graphs produced by knowledge graph pipelines. |

**Routes**:
- `/` — Home dashboard
- `/?view=pipeline` — Pipeline builder
- `/?view=vaults` — Vault management
- `/?view=graph` — Knowledge graph visualization
- `/templates` — Template gallery

---

### 3.4 API Features

**Technology**: FastAPI 0.128, Python 3.12+, Uvicorn, Pydantic v2, Azure SDK  
**Port**: 8090  
**Authentication**: Azure Managed Identity (no API keys in production)

| Endpoint group | Operations |
|---|---|
| `GET /api/health` | System health check — verifies Cosmos DB, Blob, Queue, App Config connectivity |
| `GET/POST/PUT/DELETE /api/pipelines` | Full CRUD for pipeline definitions; trigger manual execution |
| `GET/POST/PUT/DELETE /api/vaults` | Vault management including enable/disable |
| `GET /api/vaults/{id}/executions` | Vault execution history and status |
| `GET /api/executors` | Browse executor catalog with full settings schemas |
| `GET /docs` | Interactive Swagger UI |
| `GET /redoc` | ReDoc documentation |

---

### 3.5 Worker Engine Features

**Technology**: Python 3.12+, multiprocessing, Azure Storage Queue  
**Port**: 8099 (health API)

| Feature | Description |
|---|---|
| **Multi-process architecture** | N Source Workers + M Processing Workers run as independent OS processes |
| **Source Workers** | Poll enabled vaults every 5 minutes (configurable), discover new content, enqueue tasks |
| **Processing Workers** | Poll Azure Storage Queue, execute full pipelines on content items |
| **Incremental crawling** | Checkpoints stored in Cosmos DB prevent reprocessing already-seen documents |
| **Distributed locking** | Lock TTL prevents duplicate processing when multiple workers poll simultaneously |
| **Auto-restart** | Monitor loop detects crashed worker processes and replaces them automatically |
| **Graceful shutdown** | SIGINT/SIGTERM handled via shared `multiprocessing.Event`; workers finish current task before stopping |
| **Configurable parallelism** | `NUM_PROCESSING_WORKERS` and `NUM_SOURCE_WORKERS` env vars |
| **Task retries** | Up to 3 retries per task with configurable delay |

---

### 3.6 Extensibility: Custom Executors

ContentFlow is designed for extension. New executors can be created by subclassing one of three base classes:

| Base Class | Use case |
|---|---|
| `BaseExecutor` | Single content item or list processing; implement `process_input()` |
| `ParallelExecutor` | Automatic parallel processing; implement `process_content_item()` once; framework handles concurrency |
| `InputExecutor` | Input source discovery; implement `crawl()` to yield new content items |

After implementing the class:
1. Register it in `executor_catalog.yaml` with its `id`, `module_path`, `class_name`, tags, and `settings_schema`
2. Import it in `contentflow/executors/__init__.py`

Custom executors work identically to built-in ones — they appear in the Web UI, accept YAML configuration, support all base class features (debug mode, conditions, retries, timeouts), and integrate with the full pipeline engine.

---

## 4. Prerequisites

### 4.1 Azure Services Required

| Service | SKU (Basic mode) | SKU (AILZ mode) | Purpose |
|---|---|---|---|
| **Azure Container Apps Environment** | Consumption | Consumption (Internal) | Hosts API, Worker, Web containers |
| **Azure Cosmos DB** | Serverless | Serverless + Private Endpoint | Pipeline definitions, execution state, vault metadata |
| **Azure Blob Storage** | Standard LRS, Hot | Standard LRS + Private Endpoint | Document storage, processed outputs |
| **Azure Storage Queue** | Standard | Standard + Private Endpoint | Task queue between Source and Processing Workers |
| **Azure App Configuration** | Standard | Standard + Private Endpoint | Centralized runtime configuration |
| **Azure Application Insights** | Pay-per-use | Pay-per-use | Distributed tracing, monitoring |
| **Azure Log Analytics** | PerGB2018 | PerGB2018 (shared) | Log aggregation |
| **Azure Container Registry** | Standard | **Premium** (required for Private Endpoint) | Container image registry |
| **Azure Managed Identity** | User-assigned | User-assigned | Passwordless authentication between all services |

**Optional Azure services** (required for specific executors):

| Service | Required by executor(s) |
|---|---|
| **Azure AI Foundry / OpenAI** | `azure_openai_agent`, `azure_openai_embeddings`, `text_summarizer`, `entity_extractor`, `sentiment_analyser`, `content_classifier`, `pii_detector`, `keyword_extractor`, `content_translator` |
| **Azure Document Intelligence** | `azure_document_intelligence_extractor` |
| **Azure Content Understanding** | `azure_content_understanding_extractor` |
| **Azure AI Search** | `ai_search_index_output`, `gptrag_search_index_document_generator` |

### 4.2 Developer Toolchain

```bash
# Required for local development
python --version        # 3.12+
node --version          # 18+
npm --version           # 9+
docker --version        # Any recent version
az --version            # Azure CLI 2.60+
azd version             # Azure Developer CLI 1.5+

# Required for deployment
git --version           # Any recent version
```

**Python dependencies** (installed from `requirements.txt` per service):
- `fastapi>=0.128.0`, `uvicorn>=0.40.0`, `pydantic>=2.12`
- `azure-identity>=1.25.1`, `azure-cosmos>=4.14.3`
- `azure-storage-blob>=12.27.1`, `azure-storage-queue>=12.14.1`
- `azure-appconfiguration-provider>=2.3.1`
- `azure-ai-documentintelligence` (for Document Intelligence)
- `openai` (for Azure OpenAI)
- `pymupdf` (for PDF extraction)
- `python-docx`, `python-pptx`, `openpyxl` (Office documents)
- `playwright` (for web scraping — requires browser install)
- `agent-framework` (Microsoft Agent Framework — pipeline orchestration)

### 4.3 Azure Permissions

| Permission | Scope | Required for |
|---|---|---|
| `Contributor` | ContentFlow Resource Group | Deploy all resources |
| `User Access Administrator` | ContentFlow Resource Group | Assign RBAC to Managed Identity |
| `Network Contributor` | VNet Resource Group | Create Private Endpoints (AILZ mode only) |
| `Private DNS Zone Contributor` | DNS Zone Resource Group | Register PE records (AILZ mode only) |

**RBAC roles assigned automatically to the Managed Identity during deployment**:
- `Storage Blob Data Contributor` on Storage Account
- `Storage Queue Data Contributor` on Storage Account
- `Cosmos DB Built-in Data Contributor` on Cosmos DB
- `App Configuration Data Reader` on App Configuration
- `AcrPull` on Container Registry
- `Cognitive Services User` on AI Services (when applicable)

### 4.4 Service Quotas & Limits

| Limit | Default | Notes |
|---|---|---|
| Container Apps replicas | 1–2 per service | Auto-scales based on load |
| Worker processes | Configurable | `NUM_PROCESSING_WORKERS` env var |
| Queue message visibility timeout | 300 seconds | Task must complete within 5 minutes or is retried |
| Task max retries | 3 | Configurable via pipeline settings |
| Task timeout | 600 seconds | 10 minutes per pipeline execution |
| Cosmos DB throughput | Serverless (on-demand) | No pre-provisioned RU/s needed |
| Azure OpenAI TPM | Varies by deployment | Should be sized for expected concurrency |

---

## 5. Final Architecture

### 5.1 Component Overview

```
┌──────────────────────────────────────────────────────────────────────┐
│                    AZURE CONTAINER APPS ENVIRONMENT                   │
│                                                                       │
│  ┌─────────────────┐   ┌─────────────────┐   ┌──────────────────┐   │
│  │  contentflow-   │   │  contentflow-   │   │  contentflow-    │   │
│  │  web            │   │  api            │   │  worker          │   │
│  │                 │   │                 │   │                  │   │
│  │  React 18 +     │──▶│  FastAPI        │   │  Multi-process   │   │
│  │  TypeScript     │   │  Python 3.12+   │   │  Python 3.12+    │   │
│  │  Port: 80       │   │  Port: 8090     │   │  Port: 8099      │   │
│  │                 │   │                 │   │  (health only)   │   │
│  │  Pipeline       │   │  Routers:       │   │                  │   │
│  │  Builder UI     │   │  /pipelines     │   │  Source Workers  │   │
│  │  Vault Manager  │   │  /vaults        │   │  (crawl vaults)  │   │
│  │  Exec Dashboard │   │  /executors     │   │                  │   │
│  │  Template Gall. │   │  /health        │   │  Processing      │   │
│  └─────────────────┘   └────────┬────────┘   │  Workers         │   │
│                                  │            │  (run pipelines) │   │
└──────────────────────────────────┼────────────┴──────────────────┘   │
                                   │                    │
         ┌─────────────────────────┼────────────────────┼──────────────┐
         │                         ▼                    ▼              │
         │   ┌──────────────┐  ┌──────────────┐  ┌─────────────────┐  │
         │   │  Cosmos DB   │  │ Blob Storage │  │  Storage Queue  │  │
         │   │  (Serverless)│  │  (LRS, Hot)  │  │  (processing    │  │
         │   │              │  │              │  │   tasks)        │  │
         │   │  pipelines   │  │  vaults/     │  │                 │  │
         │   │  vaults      │  │  processed/  │  │                 │  │
         │   │  executions  │  │  outputs/    │  │                 │  │
         │   │  checkpoints │  │              │  │                 │  │
         │   └──────────────┘  └──────────────┘  └─────────────────┘  │
         │                                                              │
         │   ┌──────────────┐  ┌──────────────┐  ┌─────────────────┐  │
         │   │  App Config  │  │  App Insights│  │  Container      │  │
         │   │  (Standard)  │  │  + Log Anal. │  │  Registry       │  │
         │   └──────────────┘  └──────────────┘  └─────────────────┘  │
         │                                                              │
         │   ┌──────────────┐  ┌──────────────┐  ┌─────────────────┐  │
         │   │  AI Foundry  │  │  Document    │  │  Azure AI       │  │
         │   │  (OpenAI)    │  │  Intelligence│  │  Search         │  │
         │   │  (optional)  │  │  (optional)  │  │  (optional)     │  │
         │   └──────────────┘  └──────────────┘  └─────────────────┘  │
         │                       AZURE MANAGED SERVICES                 │
         └──────────────────────────────────────────────────────────────┘
```

### 5.2 Service Communication Map

| From | To | Protocol | Auth |
|---|---|---|---|
| Web UI | ContentFlow API | HTTPS REST | None (same environment) |
| API | Cosmos DB | Azure SDK over HTTPS | Managed Identity |
| API | Blob Storage | Azure SDK over HTTPS | Managed Identity |
| API | Azure App Configuration | Azure SDK over HTTPS | Managed Identity |
| Worker (Source) | Cosmos DB | Azure SDK over HTTPS | Managed Identity |
| Worker (Source) | Storage Queue | Azure SDK over HTTPS | Managed Identity |
| Worker (Processing) | Storage Queue | Azure SDK over HTTPS | Managed Identity |
| Worker (Processing) | Cosmos DB | Azure SDK over HTTPS | Managed Identity |
| Worker (Processing) | Blob Storage | Azure SDK over HTTPS | Managed Identity |
| Worker (Processing) | Azure OpenAI | Azure SDK over HTTPS | Managed Identity |
| Worker (Processing) | Document Intelligence | Azure SDK over HTTPS | Managed Identity |
| Worker (Processing) | Azure AI Search | Azure SDK over HTTPS | Managed Identity |

### 5.3 Data Flow

```
1. CONTENT DISCOVERY
   Source Worker
     │
     ├── Query Cosmos DB → enabled vaults
     ├── For each vault → read associated pipeline
     ├── Run input executor (e.g., azure_blob_input_discovery)
     ├── Discover new files since last checkpoint
     ├── Create ContentProcessingTask per file
     ├── Enqueue tasks → Azure Storage Queue
     └── Save new crawl checkpoint → Cosmos DB

2. CONTENT PROCESSING
   Processing Worker
     │
     ├── Poll Storage Queue (up to 32 messages)
     ├── Deserialize ContentProcessingTask
     ├── Acquire distributed lock (prevent duplicate processing)
     ├── Load pipeline YAML from Cosmos DB
     ├── For each pipeline step (skipping input executors):
     │     ├── Instantiate executor
     │     ├── Check condition (if set)
     │     ├── Call executor.process_input(content)
     │     └── Accumulate results in content.data
     ├── Update execution status → Cosmos DB (COMPLETED / FAILED)
     ├── Write output → Blob Storage (if configured)
     └── Delete message from queue

3. OUTPUT
   Configured output executors write to:
     ├── Azure Blob Storage (JSON, text, binary)
     ├── Azure AI Search (indexed documents)
     └── Any custom destination via custom executor
```

### 5.4 Task Lifecycle

```
[PENDING]   ← Task created and enqueued
    │
    ▼
[RUNNING]   ← Processing Worker picks up the task
    │
    ├──── Success ──→ [COMPLETED]
    │                      │
    │                 Store results in Cosmos DB + Blob
    │
    ├──── Failure ──→ [FAILED]
    │                      │
    │                      ├── retry_count < max_retries (3)?
    │                      │         └── Yes → re-enqueue → [PENDING]
    │                      └── No → [FAILED] (permanent)
    │
    └──── Cancelled ─→ [CANCELLED]
```

### 5.5 Cosmos DB Schema

**Database**: `contentflow-db`

| Container | Partition Key | Contents |
|---|---|---|
| `pipelines` | `/id` | Pipeline YAML definitions, graph nodes/edges, metadata |
| `vaults` | `/id` | Vault configurations, associated pipeline IDs |
| `vault_executions` | `/vault_id` | Per-document execution records with status and outputs |
| `pipeline_executions` | `/pipeline_id` | Direct pipeline execution records |
| `vault_crawl_checkpoints` | `/vault_id` | Last crawl timestamp per vault+executor |
| `executor_locks` | `/task_id` | Distributed locks for deduplication |
| `executor_catalog` | `/id` | Cached executor catalog (loaded from YAML at startup) |

### 5.6 Deployment Modes

#### Basic Mode (Public Endpoints)
All Azure resources expose public endpoints. Suitable for development, demos, and non-regulated environments.

```
Internet → Container Apps (external ingress) → Azure Services (public endpoints)
```

**Deploy**: `azd up` (one command)

#### AILZ-Integrated Mode (Private Endpoints)
All Azure resources have `publicNetworkAccess: Disabled`. Traffic flows only through Private Endpoints inside a VNet. Suitable for enterprise, regulated environments, and AI Landing Zone integration.

```
JumpBox/VPN → VNet → Container Apps (internal LB) → Azure Services (Private Endpoints)
```

**Differences from Basic**:
- Container Apps Environment: `internal: true` (no public ingress)
- All services: `publicNetworkAccess: Disabled`
- Network ACLs: `defaultAction: Deny`, `bypass: AzureServices`
- Container Registry: must be **Premium** SKU (required for Private Endpoint support)
- Requires pre-existing VNet with subnets: `pe-subnet` and `aca-env-subnet`
- Requires 6 Private DNS Zones linked to the VNet:
  - `privatelink.blob.core.windows.net`
  - `privatelink.queue.core.windows.net`
  - `privatelink.documents.azure.com`
  - `privatelink.azconfig.io`
  - `privatelink.azurecr.io`
  - `privatelink.cognitiveservices.azure.com`

**Deploy**: `azd up` with `ailzMode=ailz-integrated` parameter and pre-existing network resource IDs.

### 5.7 Security Model

| Principle | Implementation |
|---|---|
| **Zero-Trust** | No passwords, no connection strings. All service-to-service communication uses Managed Identity. |
| **Passwordless** | `ChainedTokenCredential` (Managed Identity → `DefaultAzureCredential`) used across all Azure SDK calls. |
| **Least Privilege** | Each service's Managed Identity is assigned only the RBAC roles it needs on each resource. |
| **Network Isolation** | AILZ mode enforces private networking; Basic mode exposes public endpoints with HTTPS. |
| **Secrets Management** | All secrets are either environment variables injected at deployment time or resolved from Azure App Configuration. No secrets in code or Git. |
| **Centralized Config** | Azure App Configuration is the single source of truth for runtime settings; local `.env` is for development only. |
| **CORS** | API configures `allow_origins: ["*"]` (suitable for internal deployments; restrict in production). |

---

## 6. Out of Scope

The following capabilities are **not included** in ContentFlow out-of-the-box and would require custom executor development, additional Azure services, or integration work:

| Capability | Notes |
|---|---|
| **SharePoint read/write connector** | `ContentIdentifier.source_type` mentions "sharepoint" but no executor or connector exists. Would require Microsoft Graph API integration as a custom executor. |
| **OneDrive connector** | Same as SharePoint — no native executor. The Web UI shows it as a planned input type. |
| **Excel/XLSX writer** | `ExcelExtractorExecutor` reads Excel but there is no executor to **write** formatted `.xlsx` files (e.g., with conditional formatting). Requires custom executor using openpyxl. |
| **Confidence score per BOM cell (Document Intelligence)** | The `extract_tables()` method in `DocumentIntelligenceConnector` returns cell content and position but does not expose `cell.confidence` from the SDK response. Requires a code extension to the connector. |
| **Email (Exchange/Outlook) connector** | No native email source executor. Would require Microsoft Graph API integration. |
| **Relational database connector** (SQL, PostgreSQL) | No native DB input executor. Would require a custom `InputExecutor` subclass. |
| **Real-time / streaming processing** | ContentFlow is a batch/async pipeline system. It does not support real-time streaming ingestion (e.g., Kafka, Event Hub consumer). |
| **Chat interface** | No conversational UI or chat bot. ContentFlow processes documents, it does not serve a chat endpoint. Integration with Copilot Studio or Azure Bot Service is out of scope. |
| **Azure AI Search index schema management** | The `ai_search_index_output` executor writes to an existing index but does not create or manage index schemas. Index schema provisioning must happen separately. |
| **Custom Document Intelligence model training** | ContentFlow uses pre-built or previously trained models. Training custom Document Intelligence models is outside the accelerator's scope. |
| **Dynamics 365 / SAP integration** | No native connectors for line-of-business systems. Outputs to Blob or AI Search can be consumed by downstream integrations. |
| **Multi-tenant isolation** | All pipelines and vaults within a deployment share the same Cosmos DB and Blob Storage. There is no tenant-level data separation built in. |
| **Role-based access control in the UI** | The Web UI has no authentication or authorization layer. It is intended for internal use by platform operators. |
| **Built-in pipeline scheduling** | Vaults trigger continuous background polling; there is no cron-style scheduler. Time-based triggers must be implemented externally (e.g., Logic Apps, Azure Functions). |
| **Video or audio processing** | No native executors for audio transcription or video analysis. These would require Azure Speech or Azure Video Indexer custom executors. |

---

## 7. Example Scenarios

### 7.1 Invoice & Receipt Processing

**Goal**: Extract structured data from incoming invoices PDFs and images; classify by document type; flag anomalies; output to Blob Storage.

**Key executors**: `azure_blob_input_discovery` → `azure_blob_content_retriever` → `azure_content_understanding_extractor` (prebuilt-invoice) → `content_classifier` → `field_mapper` → `azure_blob_output`

```yaml
name: invoice-processing
steps:
  - executor: azure_blob_input_discovery
    settings:
      blob_container_name: invoices-incoming
      file_extensions: [".pdf", ".png", ".jpg"]

  - executor: azure_blob_content_retriever

  - executor: azure_content_understanding_extractor
    settings:
      model_id: prebuilt-invoice
      output_field: invoice_data

  - executor: content_classifier
    settings:
      categories: ["invoice", "receipt", "purchase_order", "credit_note"]
      include_confidence: true

  - executor: field_mapper
    settings:
      mappings:
        invoice_data.VendorName: vendor_name
        invoice_data.InvoiceTotal.amount: total_amount
        invoice_data.InvoiceDate: invoice_date

  - executor: azure_blob_output
    settings:
      blob_container_name: invoices-processed
      output_format: json
```

---

### 7.2 Enterprise Knowledge Base for RAG

**Goal**: Process a mixed-format document library (PDF, Word, Excel), chunk text, generate embeddings, and index in Azure AI Search to power a RAG chatbot.

**Key executors**: `azure_blob_input_discovery` → `azure_blob_content_retriever` → `azure_document_intelligence_extractor` → `recursive_text_chunker` → `azure_openai_embeddings` → `gptrag_search_index_document_generator` → `ai_search_index_output`

```yaml
name: knowledge-base-ingestion
steps:
  - executor: azure_blob_input_discovery
    settings:
      blob_container_name: company-documents
      file_extensions: [".pdf", ".docx", ".xlsx"]

  - executor: azure_blob_content_retriever

  - executor: azure_document_intelligence_extractor
    settings:
      doc_intelligence_endpoint: "${AZURE_DOC_INTELLIGENCE_ENDPOINT}"
      model_id: prebuilt-layout
      extract_text: true
      extract_tables: true

  - executor: recursive_text_chunker
    settings:
      chunk_size: 800
      chunk_overlap: 150
      input_field: doc_intell_output.text

  - executor: azure_openai_embeddings
    settings:
      endpoint: "${AZURE_OPENAI_ENDPOINT}"
      deployment_name: text-embedding-3-small
      input_field: chunks

  - executor: gptrag_search_index_document_generator
    settings:
      index_name: company-knowledge-base

  - executor: ai_search_index_output
    settings:
      endpoint: "${AZURE_AI_SEARCH_ENDPOINT}"
      index_name: company-knowledge-base
```

---

### 7.3 Contract Analysis

**Goal**: Extract obligations, parties, dates, monetary values, and risk clauses from legal contracts. Generate an executive summary per document.

**Key executors**: `pdf_extractor` → `entity_extractor` → `azure_openai_agent` → `text_summarizer` → `azure_blob_output`

```yaml
name: contract-analysis
steps:
  - executor: azure_blob_input_discovery
    settings:
      blob_container_name: contracts

  - executor: azure_blob_content_retriever

  - executor: pdf_extractor
    settings:
      extract_text: true
      extract_pages: true

  - executor: entity_extractor
    settings:
      endpoint: "${AZURE_OPENAI_ENDPOINT}"
      deployment_name: gpt-4.1
      entity_types: ["person", "organization", "date", "monetary_amount", "jurisdiction"]
      output_field: entities

  - executor: azure_openai_agent
    settings:
      endpoint: "${AZURE_OPENAI_ENDPOINT}"
      deployment_name: gpt-4.1
      instructions: |
        You are a legal contract analyst. Analyze the contract and extract:
        1. Key obligations per party
        2. Payment terms and amounts
        3. Termination clauses
        4. Governing law and jurisdiction
        5. Risk flags (unusual or one-sided clauses)
        Respond in structured JSON.
      input_field: pdf_output.text
      output_field: contract_analysis

  - executor: text_summarizer
    settings:
      endpoint: "${AZURE_OPENAI_ENDPOINT}"
      deployment_name: gpt-4.1-mini
      max_length: 400
      style: executive summary for legal review
      input_field: pdf_output.text
      output_field: summary

  - executor: azure_blob_output
    settings:
      blob_container_name: contracts-analyzed
```

---

### 7.4 Engineering PDF BOM Extraction

**Goal**: Extract Bill of Materials (BOM) tables from engineering PDFs using Azure Document Intelligence, flag low-confidence line items (<90%), and write output to Azure Blob Storage. *(See fit assessment in previous analysis for implementation gap details.)*

**Key executors**: `azure_blob_input_discovery` → `azure_blob_content_retriever` → `azure_document_intelligence_extractor` → `table_row_splitter` → `field_mapper` → [custom: `bom_excel_writer`] → [custom: `sharepoint_output`]

```yaml
name: engineering-bom-extraction
steps:
  - executor: azure_blob_input_discovery
    settings:
      blob_container_name: engineering-pdfs
      file_extensions: [".pdf"]

  - executor: azure_blob_content_retriever
    settings:
      use_temp_file_for_content: true

  - executor: azure_document_intelligence_extractor
    settings:
      doc_intelligence_endpoint: "${AZURE_DOC_INTELLIGENCE_ENDPOINT}"
      model_id: prebuilt-layout
      extract_tables: true
      extract_text: false
      output_field: doc_intell_output

  - executor: table_row_splitter
    settings:
      table_field: doc_intell_output.tables.0
      table_format: auto
      has_header: true
      skip_empty_rows: true
      include_row_index: true

  - executor: field_mapper
    settings:
      mappings:
        row_data.Item: item_number
        row_data.Description: description
        row_data.Qty: quantity
        row_data.Unit: unit
        row_data.Part_Number: part_number

  # Steps 6 and 7 require custom executors (not built-in):
  # - bom_excel_writer: writes .xlsx with red fill on rows where confidence < 0.90
  # - sharepoint_output: writes file back to SharePoint via Microsoft Graph API

  - executor: azure_blob_output
    settings:
      blob_container_name: bom-output
      output_format: json
```

**Custom executor gaps required for full Phase 1**:
- `bom_excel_writer` — writes formatted Excel with `openpyxl`, applies `PatternFill(red)` to rows where confidence < 0.90
- `sharepoint_output` — uploads file to SharePoint document library via Microsoft Graph API
- Extend `DocumentIntelligenceConnector.extract_tables()` to expose `cell.confidence` from the SDK response

---

### 7.5 Compliance & PII Detection

**Goal**: Scan documents for PII, classify by sensitivity level, and generate compliance risk reports.

**Key executors**: `pdf_extractor` / `word_extractor` → `pii_detector` → `content_classifier` → `azure_openai_agent` → `azure_blob_output`

```yaml
name: compliance-scan
steps:
  - executor: azure_blob_input_discovery
    settings:
      blob_container_name: documents-review

  - executor: azure_blob_content_retriever

  - executor: pdf_extractor
    settings:
      extract_text: true

  - executor: pii_detector
    settings:
      endpoint: "${AZURE_OPENAI_ENDPOINT}"
      deployment_name: gpt-4.1
      pii_types: ["name", "email", "phone", "ssn", "credit_card", "address", "dob"]
      redact: false
      output_field: pii_results

  - executor: content_classifier
    settings:
      endpoint: "${AZURE_OPENAI_ENDPOINT}"
      deployment_name: gpt-4.1-mini
      categories: ["public", "internal", "confidential", "restricted"]
      include_confidence: true
      output_field: classification

  - executor: azure_openai_agent
    settings:
      endpoint: "${AZURE_OPENAI_ENDPOINT}"
      deployment_name: gpt-4.1
      instructions: |
        Based on PII findings and document classification, assess regulatory exposure:
        - GDPR, HIPAA, PCI-DSS applicability
        - Risk level: low / medium / high / critical
        - Required remediation actions
      output_field: compliance_report

  - executor: azure_blob_output
    settings:
      blob_container_name: compliance-reports
```

---

### 7.6 Web Content Ingestion

**Goal**: Crawl product documentation or support sites, chunk content, generate embeddings, and index in Azure AI Search for a RAG chatbot.

**Key executors**: `web_scraper` → `recursive_text_chunker` → `language_detector` → `azure_openai_embeddings` → `ai_search_index_output`

```yaml
name: web-content-ingestion
steps:
  - executor: web_scraper
    settings:
      urls:
        - "https://docs.company.com"
        - "https://support.company.com"
      max_depth: 3
      selectors: ["article", "main", ".content"]
      output_field: scraped_content

  - executor: recursive_text_chunker
    settings:
      chunk_size: 1500
      chunk_overlap: 200
      input_field: scraped_content.text

  - executor: language_detector
    settings:
      input_field: scraped_content.text
      output_field: detected_language

  - executor: azure_openai_embeddings
    settings:
      endpoint: "${AZURE_OPENAI_ENDPOINT}"
      deployment_name: text-embedding-3-small

  - executor: ai_search_index_output
    settings:
      endpoint: "${AZURE_AI_SEARCH_ENDPOINT}"
      index_name: web-content-rag
```

---

### 7.7 Multilingual Document Translation

**Goal**: Detect language of incoming documents, translate to target languages, and index translated content.

**Key executors**: `pdf_extractor` → `language_detector` → `recursive_text_chunker` → `content_translator` → `azure_openai_embeddings` → `ai_search_index_output`

```yaml
name: multilingual-translation
steps:
  - executor: azure_blob_input_discovery
    settings:
      blob_container_name: original-content

  - executor: azure_blob_content_retriever

  - executor: pdf_extractor
    settings:
      extract_text: true

  - executor: language_detector
    settings:
      input_field: pdf_output.text
      output_field: source_language

  - executor: recursive_text_chunker
    settings:
      chunk_size: 2000
      input_field: pdf_output.text

  - executor: content_translator
    settings:
      endpoint: "${AZURE_OPENAI_ENDPOINT}"
      deployment_name: gpt-4.1
      target_languages: ["en", "es", "fr", "de", "pt"]
      output_field: translations

  - executor: azure_openai_embeddings
    settings:
      endpoint: "${AZURE_OPENAI_ENDPOINT}"
      deployment_name: text-embedding-3-small

  - executor: ai_search_index_output
    settings:
      endpoint: "${AZURE_AI_SEARCH_ENDPOINT}"
      index_name: multilingual-content
```

---

### 7.8 Email Attachment Triage

**Goal**: Process email attachments, detect sentiment, extract action items and deadlines, classify by category, and route to the appropriate team queue.

**Key executors**: `pdf_extractor` → `sentiment_analyser` → `entity_extractor` → `azure_openai_agent` → `content_classifier` → `azure_blob_output`

```yaml
name: email-triage
steps:
  - executor: azure_blob_input_discovery
    settings:
      blob_container_name: email-attachments

  - executor: azure_blob_content_retriever

  - executor: pdf_extractor
    settings:
      extract_text: true

  - executor: sentiment_analyser
    settings:
      endpoint: "${AZURE_OPENAI_ENDPOINT}"
      deployment_name: gpt-4.1-mini
      granularity: document
      include_confidence: true
      output_field: sentiment

  - executor: entity_extractor
    settings:
      endpoint: "${AZURE_OPENAI_ENDPOINT}"
      deployment_name: gpt-4.1
      entity_types: ["person", "date", "organization", "action_item"]
      output_field: entities

  - executor: azure_openai_agent
    settings:
      endpoint: "${AZURE_OPENAI_ENDPOINT}"
      deployment_name: gpt-4.1-mini
      instructions: |
        Extract from this email:
        1. Action items and who owns them
        2. Deadlines mentioned
        3. Urgency level: low / medium / high / critical
        4. Subject matter summary in one sentence
      output_field: triage_result

  - executor: content_classifier
    settings:
      endpoint: "${AZURE_OPENAI_ENDPOINT}"
      deployment_name: gpt-4.1-mini
      categories: ["technical_support", "billing", "complaint", "legal", "general_inquiry"]
      output_field: category

  - executor: azure_blob_output
    settings:
      blob_container_name: email-triaged
```

---

### 7.9 Spreadsheet Data Pipeline

**Goal**: Process Excel files row by row, normalize field names, validate data, and export cleaned records to Blob Storage as JSON.

**Key executors**: `content_retriever` → `excel_extractor` → `table_row_splitter` → `field_mapper` → `field_selector` → `azure_blob_output`

```yaml
name: spreadsheet-pipeline
steps:
  - executor: content_retriever
    settings:
      use_temp_file_for_content: true

  - executor: excel_extractor
    settings:
      extract_text: false
      extract_sheets: true
      extract_tables: true
      first_row_as_header: true
      skip_hidden_sheets: true
      output_field: excel_output

  - executor: table_row_splitter
    settings:
      table_field: excel_output.sheets.0.table
      table_format: auto
      has_header: true
      skip_empty_rows: true
      include_row_index: true

  - executor: field_mapper
    settings:
      mappings:
        row_data.CustomerID: customer_id
        row_data.CustomerName: name
        row_data.EmailAddress: email
        row_data.PurchaseAmount: amount

  - executor: field_selector
    settings:
      include_fields: ["customer_id", "name", "email", "amount", "row_index"]

  - executor: azure_blob_output
    settings:
      blob_container_name: processed-data
      output_format: json
```

---

### 7.10 Knowledge Graph Construction

**Goal**: Extract entities and relationships from a corporate document corpus and build a structured knowledge graph for organizational intelligence.

**Key executors**: `azure_document_intelligence_extractor` → `recursive_text_chunker` → `entity_extractor` → `azure_openai_agent` → `document_set_initializer` → `cross_document_comparison` → `azure_blob_output`

```yaml
name: knowledge-graph
steps:
  - executor: azure_blob_input_discovery
    settings:
      blob_container_name: corporate-documents

  - executor: azure_blob_content_retriever

  - executor: azure_document_intelligence_extractor
    settings:
      doc_intelligence_endpoint: "${AZURE_DOC_INTELLIGENCE_ENDPOINT}"
      model_id: prebuilt-layout
      extract_text: true

  - executor: recursive_text_chunker
    settings:
      chunk_size: 2000
      chunk_overlap: 100
      input_field: doc_intell_output.text

  - executor: entity_extractor
    settings:
      endpoint: "${AZURE_OPENAI_ENDPOINT}"
      deployment_name: gpt-4.1
      entity_types: ["person", "organization", "product", "location", "project", "technology"]
      output_field: entities

  - executor: azure_openai_agent
    settings:
      endpoint: "${AZURE_OPENAI_ENDPOINT}"
      deployment_name: gpt-4.1
      instructions: |
        From the extracted entities, identify relationships such as:
        works_at, manages, reports_to, located_in, provides, uses, competes_with
        Return as structured JSON with relationship triples.
      output_field: relationships

  - executor: azure_blob_output
    settings:
      blob_container_name: knowledge-graphs
      output_format: json
```

---

## 8. Included Sample Pipelines

The repository includes 28+ ready-to-run sample pipelines in `contentflow-lib/samples/`:

| Folder | Sample Name | What it demonstrates |
|---|---|---|
| `01-simple/` | Simple pipeline | Minimal pipeline: content retrieval + Document Intelligence |
| `02-batch-processing/` | Batch processing | Processing multiple documents concurrently |
| `03-pdf-extractor_chunker/` | PDF + Chunking | PyMuPDF extraction + recursive text chunker |
| `04-word-extractor/` | Word extractor | `.docx` content extraction with metadata |
| `05-powerpoint-extractor/` | PowerPoint extractor | `.pptx` slide-by-slide extraction |
| `06-ai-analysis/` | AI analysis | GPT-4 analysis with configurable prompts |
| `07-embeddings/` | Embeddings | Azure OpenAI embedding generation |
| `08-content-understanding/` | Content Understanding | Azure Content Understanding prebuilt models |
| `09-blob-input/` | Blob input | Full blob discovery + retrieval + Document Intelligence |
| `10-table-row-splitter/` | Table row splitter | Splitting tables into per-row content items |
| `11-excel-extractor/` | Excel extractor | Full Excel workbook extraction |
| `12-field-transformation/` | Field transformation | Field mapping, selection, and normalization |
| `13-blob-output-sample/` | Blob output | Writing processed results to Blob Storage |
| `14-gpt-rag-ingestion/` | GPT-RAG ingestion | Complete end-to-end RAG knowledge base pipeline |
| `15-document-analysis/` | Document analysis | Full Document Intelligence analysis workflow |
| `16-spreadsheet-pipeline/` | Spreadsheet pipeline | Excel ingestion → row splitting → field normalization |
| `17-knowledge-graph/` | Knowledge graph | Entity + relationship extraction for graph construction |
| `18-web-scraping/` | Web scraping | Playwright-based crawling and content extraction |
| `19-sub-pipelines/` | Sub-pipelines | Pipeline composition and nested workflow execution |
| `20-document-set-static/` | Document set (static) | Fixed multi-document cross-analysis |
| `21-document-set-comparison/` | Document comparison | Side-by-side AI comparison of two documents |
| `22-document-set-dynamic/` | Document set (dynamic) | Dynamically assembled document sets |
| `23-inline-document-set/` | Inline document set | Document sets defined inline in the pipeline |
| `27-subpipeline-processing/` | Subpipeline processing | Advanced sub-pipeline patterns |
| `28-advanced-batch/` | Advanced batch | Complex batch processing with error handling |
| `32-parallel-processing/` | Parallel processing | Fan-out/fan-in with concurrent branches |
| `44-conditional-routing/` | Conditional routing | If/else branching based on content properties |

**Parallel workflow patterns** (documented in `PARALLEL_WORKFLOWS_GUIDE.md`):
- `fan_out_fan_in.yaml` — Split into parallel branches, merge results
- `split_merge.yaml` — Split content list, process in parallel, collect results
- `batch_subworkflow_example.yaml` — Batch processing with nested subworkflows
- `conditional_routing.yaml` — Content-aware routing based on classification results

---

*Document version: March 25, 2026 — Based on ContentFlow repository branch `local-documentation`*
