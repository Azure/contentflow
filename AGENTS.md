# AGENTS.md - Technical Architecture & Repository Structure

> **Documentation for AI agents and developers** - Technical stack, architecture patterns, and detailed repository structure for ContentFlow.

---

## 📋 Project Overview

**ContentFlow** is an enterprise-grade, cloud-native document and content processing platform built on Azure. It provides intelligent, scalable content processing pipelines powered by Azure AI services and orchestrated by Microsoft Agent Framework.

### Core Purpose
Transform unstructured content (PDFs, Word docs, Excel files, web content, etc.) into intelligent, actionable data through orchestrated AI-powered workflows.

### Architecture Pattern
- **Microservices**: Distributed services (API, Worker, Web) deployed independently
- **Event-Driven**: Queue-based task distribution with async processing
- **Cloud-Native**: Built for Azure Container Apps with managed Azure services
- **Declarative Workflows**: YAML-based pipeline definitions with Python execution

---

## 🛠️ Technical Stack

### Backend Services (Python)

#### Core Framework & API
- **Python**: 3.12+
- **FastAPI**: 0.128.0 - Modern async web framework for REST API
- **Uvicorn**: 0.40.0 - ASGI server with support for HTTP/2
- **Pydantic**: 2.12+ - Data validation and settings management
- **aiohttp/httpx**: Async HTTP clients for external service calls

#### Azure SDK Integration
- **azure-identity**: 1.25.1 - Managed identity and authentication
- **azure-storage-blob**: 12.27.1 - Blob storage for content persistence
- **azure-storage-queue**: 12.14.1 - Queue-based task distribution
- **azure-cosmos**: 4.14.3 - NoSQL database for metadata and state
- **azure-appconfiguration-provider**: 2.3.1 - Centralized configuration

#### Content Processing
- **ContentFlow Library**: Custom pipeline orchestration engine
- **40+ Executors**: Document parsing, AI analysis, embeddings, web scraping
- **Async Processing**: Built on asyncio for non-blocking operations

### Frontend (TypeScript/React)

#### Core Framework
- **React**: 18+ with TypeScript 5.8+
- **Vite**: Modern build tool with HMR and optimized production builds
- **Node.js**: 18+ runtime

#### UI & Styling
- **Shadcn/ui**: High-quality accessible component library
- **Radix UI**: Unstyled, accessible component primitives
- **Tailwind CSS**: Utility-first CSS framework
- **PostCSS**: CSS processing and optimization

#### State Management & Data
- **TanStack Query (React Query)**: Server state management and caching
- **React Hook Form**: Form state management with validation
- **Zod**: TypeScript-first schema validation

#### Specialized Libraries
- **ReactFlow**: Visual pipeline builder and graph visualization
- **Monaco Editor**: YAML/code editor with syntax highlighting
- **js-yaml**: YAML parsing and serialization
- **Lucide React**: Icon library

### Infrastructure & DevOps

#### Cloud Platform
- **Azure Container Apps**: Serverless container hosting
- **Azure Cosmos DB**: Globally distributed NoSQL database
- **Azure Blob Storage**: Scalable object storage
- **Azure Storage Queue**: Message queuing service
- **Azure AI Services**: Document Intelligence, OpenAI, Computer Vision
- **Azure App Configuration**: Centralized configuration management
- **Azure Application Insights**: Monitoring and diagnostics

#### Infrastructure as Code
- **Bicep**: Azure infrastructure templates
- **Azure Developer CLI (azd)**: Deployment orchestration
- **Docker**: Container packaging for all services

#### CI/CD & Tools
- **Git**: Version control
- **Shell Scripts**: Deployment automation
- **Azure AI Landing Zone**: Enterprise security and compliance framework

---

## 📁 Repository Structure

### Root Level Files

```
contentflow/
├── azure.yaml                 # Azure Developer CLI configuration
├── README.md                  # Project documentation
├── LICENSE                    # MIT License
├── CODE_OF_CONDUCT.md        # Community guidelines
├── SECURITY.md               # Security policies and reporting
└── assets/                   # Static assets (images, diagrams, demos)
```

**Key Files:**
- `azure.yaml`: Defines Azure deployment configuration, service mappings, and deployment hooks
- `README.md`: Main project documentation with overview, features, and quick start
- `SECURITY.md`: Security vulnerability reporting and best practices

---

### `/contentflow-api` - REST API Service

**Purpose:** Core REST API service for pipeline management, execution orchestration, and vault operations.

**Technology:** FastAPI, Python 3.12+, Azure Cosmos DB, Azure Blob Storage

```
contentflow-api/
├── main.py                   # FastAPI application entry point
├── requirements.txt          # Python dependencies
├── Dockerfile               # Container image definition
├── README.md                # API documentation
└── app/
    ├── __init__.py
    ├── dependencies.py       # Dependency injection (DB, storage clients)
    ├── settings.py          # Configuration and environment variables
    ├── startup.py           # Application lifecycle and initialization
    ├── core/                # Core utilities and shared logic
    ├── database/            # Cosmos DB client and operations
    ├── models/              # Pydantic models (request/response schemas)
    ├── routers/             # FastAPI route handlers (endpoints)
    ├── services/            # Business logic layer
    └── utils/               # Helper functions and utilities
```

**Key Components:**
- **Routers**: API endpoints for pipelines, vaults, executions, executor catalog
- **Services**: Business logic for pipeline execution, vault management, catalog operations
- **Database**: Cosmos DB integration for persistent storage
- **Models**: Request/response schemas and validation
- **Dependencies**: Shared clients (Cosmos DB, Blob Storage, Queue)

**Endpoints:**
- `/pipelines` - CRUD operations for pipeline definitions
- `/vaults` - Document vault management
- `/executions` - Pipeline execution status and history
- `/catalog` - Executor catalog browsing
- `/health` - Health checks and readiness probes

---

### `/contentflow-lib` - Core Processing Library

**Purpose:** Python library containing the pipeline orchestration engine, executor catalog, and content processing logic.

**Technology:** Python 3.12+, asyncio, Azure SDK, Document Intelligence, OpenAI

```
contentflow-lib/
├── __init__.py
├── setup.sh                 # Installation script
├── pyproject.toml           # Package configuration
├── requirements.txt         # Library dependencies
├── executor_catalog.yaml    # Executor registry and metadata
├── CustomExecutor.md        # Guide for creating custom executors
├── README.md
├── contentflow/            # Main library package
│   ├── __init__.py
│   ├── connectors/         # Azure service connectors (Blob, Search, AI)
│   ├── executors/          # 40+ executor implementations
│   ├── models/             # Content model and data structures
│   ├── pipeline/           # Pipeline engine and orchestration
│   └── utils/              # Helper utilities
└── samples/                # Example pipelines and workflows
    ├── README.md
    ├── PARALLEL_WORKFLOWS_GUIDE.md
    ├── 00_run/             # Pipeline runner scripts
    ├── 01-simple/          # Basic pipeline examples
    ├── 02-batch-processing/
    ├── 03-pdf-extractor_chunker/
    ├── 04-word-extractor/
    ├── 05-powerpoint-extractor/
    ├── 06-ai-analysis/
    ├── 07-embeddings/
    ├── 08-content-understanding/
    ├── 09-blob-input/
    ├── 10-table-row-splitter/
    ├── 11-excel-extractor/
    ├── 12-field-transformation/
    ├── 13-blob-output-sample/
    ├── 14-gpt-rag-ingestion/
    ├── 15-document-analysis/
    ├── 16-spreadsheet-pipeline/
    ├── 17-knowledge-graph/
    ├── 18-web-scraping/
    ├── 19-sub-pipelines/
    ├── 27-subpipeline-processing/
    ├── 28-advanced-batch/
    ├── 32-parallel-processing/
    ├── 44-conditional-routing/
    └── 99-assets/          # Sample documents and test data
```

**Key Components:**

#### Executors (40+ implementations)
Categories include:
- **Input**: Blob, file system, database readers
- **Extraction**: PDF, Word, Excel, PowerPoint, image OCR
- **AI Processing**: Embeddings, document intelligence, content analysis
- **Transformation**: Chunking, splitting, field mapping, aggregation
- **Output**: Blob writers, database writers, API integrations
- **Routing**: Conditional logic, parallel fan-out/fan-in
- **Specialized**: Web scraping (Playwright), knowledge graphs

#### Pipeline Engine
- **YAML Parser**: Converts declarative pipelines to execution graphs
- **DAG Executor**: Async execution with dependency resolution
- **Content Model**: Standardized data structure for pipeline flow
- **Event System**: Publish/subscribe for executor communication
- **Error Handling**: Retries, fallbacks, error propagation

#### Connectors
- Azure Blob Storage connector
- Azure AI Search connector
- Azure Document Intelligence connector
- Azure OpenAI connector

---

### `/contentflow-web` - React Web Interface

**Purpose:** Modern web UI for visual pipeline building, vault management, and execution monitoring.

**Technology:** React 18, TypeScript, Vite, Tailwind CSS, ReactFlow

```
contentflow-web/
├── index.html
├── package.json             # npm dependencies and scripts
├── vite.config.ts          # Vite build configuration
├── tsconfig.json           # TypeScript configuration
├── tailwind.config.ts      # Tailwind CSS configuration
├── postcss.config.js       # PostCSS plugins
├── eslint.config.js        # ESLint rules
├── components.json         # Shadcn/ui configuration
├── Dockerfile
├── README.md
├── public/                 # Static assets
└── src/
    ├── main.tsx            # Application entry point
    ├── App.tsx             # Root component
    ├── index.css           # Global styles
    ├── App.css
    ├── vite-env.d.ts       # Vite type definitions
    ├── components/         # React components
    │   ├── ui/             # Shadcn/ui components (buttons, dialogs, etc.)
    │   ├── pipeline/       # Pipeline builder components
    │   ├── vault/          # Vault management components
    │   └── common/         # Shared components
    ├── pages/              # Page-level components (routes)
    │   ├── Home.tsx
    │   ├── PipelineBuilder.tsx
    │   ├── VaultManager.tsx
    │   └── ExecutionHistory.tsx
    ├── hooks/              # Custom React hooks
    ├── types/              # TypeScript type definitions
    ├── lib/                # Utility functions and configurations
    └── data/               # Mock data and constants
```

**Key Features:**
- **Pipeline Builder**: Visual drag-and-drop interface using ReactFlow
- **YAML Editor**: Monaco-based editor with syntax highlighting
- **Template Gallery**: Pre-built pipeline templates
- **Vault Management**: Document upload, organization, and browsing
- **Execution Dashboard**: Real-time pipeline execution monitoring
- **Catalog Browser**: Explore available executors and their configurations

**Routing:**
- `/` - Home dashboard
- `/pipelines` - Pipeline list and management
- `/pipelines/builder` - Visual pipeline builder
- `/vaults` - Vault management
- `/executions` - Execution history
- `/catalog` - Executor catalog

---

### `/contentflow-worker` - Processing Worker Service

**Purpose:** Distributed worker engine for executing pipelines and discovering content from input sources.

**Technology:** Python 3.12+, multiprocessing, Azure Storage Queue

```
contentflow-worker/
├── main.py                  # Worker entry point
├── requirements.txt         # Python dependencies
├── Dockerfile
├── README.md
└── app/
    ├── __init__.py
    ├── engine.py            # Multi-processing worker engine
    ├── models.py            # Task models and data structures
    ├── queue_client.py      # Azure Storage Queue client
    ├── api.py               # Optional health check API
    ├── settings.py          # Configuration
    ├── startup.py           # Initialization
    ├── utils.py             # Helper functions
    └── worker/              # Worker implementations
        ├── content_worker.py    # Content processing worker
        └── input_worker.py      # Input source discovery worker
```

**Worker Types:**

1. **Content Processing Workers** (Multiple processes)
   - Poll Azure Storage Queue for processing tasks
   - Execute pipeline on content items (skip input executors)
   - Update execution status in Cosmos DB
   - Handle retries and error recovery

2. **Input Source Workers** (Single process)
   - Query Cosmos DB for enabled pipelines
   - Execute input executors to discover content
   - Create processing tasks for discovered items
   - Queue tasks for content workers

**Processing Flow:**
```
Input Worker → Discovers Content → Creates Tasks → Queue
                                                      ↓
Content Workers ← Poll Queue ← Process Content ← Update Status
```

---

### `/infra` - Infrastructure as Code

**Purpose:** Azure infrastructure definitions, deployment scripts, and configuration.

**Technology:** Bicep, Azure CLI, Shell scripts

```
infra/
├── README.md               # Infrastructure documentation
├── bicep/                  # Bicep templates
│   ├── main.bicep         # Main infrastructure template
│   ├── main.parameters.json # Parameter file
│   └── modules/           # Modular Bicep components
│       ├── container-app.bicep
│       ├── cosmos-db.bicep
│       ├── storage.bicep
│       ├── app-insights.bicep
│       └── ...
└── scripts/               # Deployment and management scripts
    ├── get-ailz-resources.sh      # Azure AI Landing Zone resource discovery
    ├── post-deploy-api.sh         # API post-deployment configuration
    ├── post-deploy-worker.sh      # Worker post-deployment configuration
    └── ...
```

**Deployment Modes:**
1. **Basic Mode**: Standalone deployment for development/testing
2. **Azure AI Landing Zone (AILZ)**: Enterprise deployment with security, compliance, and networking

**Provisioned Resources:**
- Azure Container Apps (API, Worker, Web)
- Azure Cosmos DB (NoSQL database)
- Azure Storage Account (Blob + Queue)
- Azure App Configuration
- Azure Application Insights
- Azure Container Registry
- Azure Key Vault (optional)
- Azure AI Services (Document Intelligence, OpenAI)

**Deployment Process:**
```bash
azd up  # One-command deployment
```
1. Provision infrastructure (Bicep templates)
2. Build container images
3. Push to Azure Container Registry
4. Deploy to Container Apps
5. Run post-deployment scripts
6. Output service URLs

---

## 🔄 System Architecture

### Request Flow

```
User → Web UI → API → Queue → Worker → Azure AI Services
                 ↓                ↓
            Cosmos DB      Blob Storage
```

1. **Web UI**: User creates/edits pipeline YAML
2. **API**: Stores pipeline in Cosmos DB, creates execution record
3. **Worker (Input)**: Discovers content from input sources
4. **Queue**: Distributes tasks to content workers
5. **Worker (Content)**: Executes pipeline on content
6. **Azure AI**: Processes documents (OCR, embeddings, analysis)
7. **Blob Storage**: Stores processed content and artifacts
8. **Cosmos DB**: Tracks execution status and metadata

### Data Flow

```yaml
Input Source → Content Discovery → Pipeline Execution → Output Destination
     ↓                ↓                    ↓                    ↓
  Azure Blob    Task Creation      AI Processing        Azure Blob
  Local File    Queuing Process    Transformations      Cosmos DB
  Database      Status Updates     Enrichment           Search Index
```

---

## 🧩 Key Concepts

### Pipeline Definition (YAML)
```yaml
name: document-processing
steps:
  - executor: blob_input          # Input executor
    params:
      container: documents
  
  - executor: pdf_extractor        # Document parsing
  
  - executor: text_splitter        # Chunking
    params:
      chunk_size: 1000
  
  - executor: embedding_generator  # AI embeddings
    params:
      model: text-embedding-3-small
  
  - executor: blob_output          # Output
    params:
      container: processed
```

### Content Model
Standardized data structure that flows through pipelines:
```python
{
    "id": "unique_id",
    "source": "blob://container/file.pdf",
    "content": "extracted text",
    "metadata": {...},
    "chunks": [...],
    "embeddings": [...],
    "analysis": {...}
}
```

### Executor
Self-contained processing unit with:
- Input: Content object
- Processing: Transform, enrich, or analyze
- Output: Modified content object
- Configuration: YAML parameters

---

## 🚀 Development Workflow

### Local Development

1. **Library Development**
   ```bash
   cd contentflow-lib
   pip install -e .
   pytest
   ```

2. **API Development**
   ```bash
   cd contentflow-api
   pip install -r requirements.txt
   uvicorn main:app --reload
   ```

3. **Worker Development**
   ```bash
   cd contentflow-worker
   pip install -r requirements.txt
   python main.py
   ```

4. **Web Development**
   ```bash
   cd contentflow-web
   npm install
   npm run dev
   ```

### Testing

- **Unit Tests**: Each component has its own test suite
- **Integration Tests**: Test inter-service communication
- **Sample Pipelines**: `contentflow-lib/samples/` for end-to-end testing

### Debugging

- **API**: FastAPI automatic documentation at `/docs` and `/redoc`
- **Worker**: Logs to console and Application Insights
- **Web**: React DevTools and browser console
- **Azure**: Application Insights for distributed tracing

---

## 📚 Additional Resources

- **Main README**: [README.md](./README.md) - Project overview and quick start
- **API Documentation**: [contentflow-api/README.md](./contentflow-api/README.md)
- **Library Documentation**: [contentflow-lib/README.md](./contentflow-lib/README.md)
- **Web Documentation**: [contentflow-web/README.md](./contentflow-web/README.md)
- **Worker Documentation**: [contentflow-worker/README.md](./contentflow-worker/README.md)
- **Infrastructure Guide**: [infra/README.md](./infra/README.md)
- **Custom Executors**: [contentflow-lib/CustomExecutor.md](./contentflow-lib/CustomExecutor.md)
- **Parallel Workflows**: [contentflow-lib/samples/PARALLEL_WORKFLOWS_GUIDE.md](./contentflow-lib/samples/PARALLEL_WORKFLOWS_GUIDE.md)

---

## 🎯 Agent Development Guidelines

### When Working on This Codebase

1. **Understand the Layer**: Identify which service/component you're modifying
2. **Follow Patterns**: Each service has established patterns (FastAPI routes, React components, executor structure)
3. **Check Dependencies**: Services depend on `contentflow-lib` for pipeline logic
4. **Test Locally**: Use sample pipelines and local dev servers
5. **Review Samples**: The `samples/` directory contains comprehensive examples
6. **Update Documentation**: Keep README files in sync with code changes

### Common Tasks

- **Add Executor**: Create in `contentflow-lib/contentflow/executors/`, register in `executor_catalog.yaml`
- **Add API Endpoint**: Create route in `contentflow-api/app/routers/`, add service logic
- **Add UI Feature**: Create component in `contentflow-web/src/components/`, add route if needed
- **Modify Pipeline**: Edit YAML in samples or through Web UI
- **Add Azure Resource**: Update `infra/bicep/main.bicep` and parameter file

---

**Last Updated**: February 2026  
**License**: MIT  
**Repository**: ContentFlow - Intelligent Content Processing Platform
