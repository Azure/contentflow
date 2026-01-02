# ContentFlow API

> **Fast, scalable REST API for managing content processing pipelines and orchestrating document workflows**


## 📋 Overview

ContentFlow API is the core REST API service for the ContentFlow platform. It provides a comprehensive set of endpoints for managing pipelines, executing workflows, managing vaults, and accessing the executor catalog. Built with FastAPI and designed for cloud-native deployment on Azure.

### Key Characteristics
- **RESTful Architecture** - Clean, intuitive API design following REST conventions
- **Asynchronous** - Built on async/await for high concurrency and performance
- **Cloud-Native** - First-class support for Azure services (Cosmos DB, Blob Storage, App Configuration)
- **Fully Documented** - Automatic API documentation via Swagger UI and ReDoc
- **Production-Ready** - Comprehensive error handling, logging, and health checks

---

## 🚀 Getting Started

### Prerequisites

- **Python 3.12+**
- **pip** or **conda** for package management
- **Azure Account** (optional, for cloud deployment)
- **Docker** (for containerized deployment)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd contentflow/contentflow-api
   ```

2. **Install dependencies**
   ```bash
   # Using pip
   pip install -r requirements.txt
   
   # Or using conda
   conda create -n contentflow python=3.12
   conda activate contentflow
   pip install -r requirements.txt
   ```

3. **Configure environment variables**
   ```bash
   # Copy the sample environment file
   cp .env.sample .env
   
   # Edit .env with your configuration
   # Required variables:
   # - AZURE_APP_CONFIG_CONNECTION_STRING or AZURE_APP_CONFIG_ENDPOINT
   # - COSMOS_DB_ENDPOINT
   # - BLOB_STORAGE_ACCOUNT_NAME
   # - STORAGE_ACCOUNT_WORKER_QUEUE_URL
   ```

4. **Run the API server**
   ```bash
   # Development mode (with auto-reload)
   python main.py
   
   # Production mode (using uvicorn directly)
   uvicorn main:app --host 0.0.0.0 --port 8090 --workers 4
   ```

5. **Access the API**
   - API Base: `http://localhost:8090`
   - Swagger UI: `http://localhost:8090/docs`
   - ReDoc: `http://localhost:8090/redoc`
   - OpenAPI Schema: `http://localhost:8090/openapi.json`

---

## 📁 Project Structure

```
contentflow-api/
├── main.py                    # Application entry point
├── requirements.txt           # Python dependencies
├── Dockerfile                 # Container image definition
├── .env.sample               # Sample environment configuration
│
└── app/
    ├── __init__.py
    ├── settings.py           # Application configuration settings
    ├── dependencies.py       # Dependency injection setup
    ├── startup.py            # Lifecycle hooks (startup/shutdown)
    │
    ├── core/
    │   └── auth.py          # Authentication/authorization logic
    │
    ├── database/
    │   └── cosmos.py        # Azure Cosmos DB client initialization
    │
    ├── models/
    │   ├── _base.py         # Base model classes
    │   ├── _pipeline.py     # Pipeline data models
    │   ├── _pipeline_execution.py  # Execution tracking models
    │   ├── _executor.py     # Executor definition models
    │   └── _vault.py        # Vault management models
    │
    ├── routers/
    │   ├── health.py        # Health check endpoints
    │   ├── pipelines.py     # Pipeline management & execution
    │   ├── executors.py     # Executor catalog endpoints
    │   └── vaults.py        # Vault management endpoints
    │
    ├── services/
    │   ├── base_service.py  # Base service class
    │   ├── health_service.py           # Health check logic
    │   ├── pipeline_service.py         # Pipeline operations
    │   ├── pipeline_execution_service.py  # Execution management
    │   ├── executor_catalog_service.py    # Executor catalog ops
    │   └── vault_service.py            # Vault operations
    │
    └── utils/
        └── blob_storage.py  # Azure Blob Storage utilities
```

---

## 🔌 API Endpoints

### Health Check Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/health/` | Full system health check (all services) |
| `GET` | `/api/health/{service_name}` | Check specific service health |

**Available Services:**
- `cosmos_db` - Azure Cosmos DB connectivity
- `storage_queue` - Azure Storage Queue connectivity
- `app_config` - Azure App Configuration connectivity

**Example Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-02T10:30:00Z",
  "services": {
    "cosmos_db": {
      "status": "healthy",
      "response_time_ms": 45
    },
    "storage_queue": {
      "status": "healthy",
      "response_time_ms": 32
    }
  }
}
```

---

### Pipeline Endpoints

Manage and execute content processing pipelines.

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/pipelines/` | List all pipelines |
| `GET` | `/api/pipelines/{id_or_name}` | Get specific pipeline by ID or name |
| `POST` | `/api/pipelines/` | Create new pipeline |
| `DELETE` | `/api/pipelines/{id}` | Delete a pipeline |
| `POST` | `/api/pipelines/{id}/execute` | Execute a pipeline |
| `GET` | `/api/pipelines/executions/{execution_id}` | Get execution status |

#### Create Pipeline
```bash
POST /api/pipelines/
Content-Type: application/json

{
  "name": "Document Processing Pipeline",
  "description": "Processes PDF documents and extracts content",
  "yaml": "version: '1.0'\nsteps:\n  - name: pdf_extract\n    executor: pdf_extractor\n    inputs:\n      - file_path\n    outputs:\n      - extracted_text",
  "tags": ["pdf", "extraction"],
  "enabled": true,
  "retry_delay": 5,
  "timeout": 600,
  "retries": 3
}
```

#### Execute Pipeline
```bash
POST /api/pipelines/{pipeline_id}/execute
Content-Type: application/json

{
  "inputs": {
    "file_path": "s3://bucket/document.pdf",
    "document_type": "invoice"
  },
  "configuration": {
    "timeout": 300,
    "priority": "high"
  }
}
```

**Response:**
```json
{
  "execution_id": "exec_abc123def456",
  "status": "started",
  "message": "Pipeline execution started with ID: exec_abc123def456"
}
```

---

### Executor Catalog Endpoints

Access the catalog of available executors for pipeline building.

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/executors/` | List all available executors |
| `GET` | `/api/executors/{executor_id}` | Get specific executor definition |

**Example Response:**
```json
[
  {
    "id": "pdf_extractor",
    "name": "PDF Text Extractor",
    "description": "Extracts text, tables, and metadata from PDF files",
    "version": "1.0.0",
    "category": "document_extraction",
    "inputs": [
      {
        "name": "file_path",
        "type": "string",
        "required": true
      }
    ],
    "outputs": [
      {
        "name": "extracted_text",
        "type": "string"
      }
    ]
  }
]
```

---

### Vault Endpoints

Manage content vaults - secure storage associated with pipelines.

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/vaults/` | List all vaults (with filtering) |
| `POST` | `/api/vaults/` | Create new vault |
| `GET` | `/api/vaults/{vault_id}` | Get specific vault |
| `PUT` | `/api/vaults/{vault_id}` | Update vault |
| `DELETE` | `/api/vaults/{vault_id}` | Delete vault |

#### Create Vault
```bash
POST /api/vaults/
Content-Type: application/json

{
  "name": "Invoice Processing Vault",
  "description": "Storage for invoice documents and processing results",
  "pipeline_id": "pipeline_123",
  "tags": ["invoices", "accounting"],
  "retention_days": 90
}
```

#### List Vaults with Filtering
```bash
GET /api/vaults/?search=invoice&tags=accounting,invoices
```

---

## ⚙️ Configuration

### Environment Variables

The API is configured via environment variables, which can be set in a `.env` file or Azure App Configuration.

**Core Application Settings:**
```env
# API Server
API_SERVER_HOST=0.0.0.0
API_SERVER_PORT=8090
API_SERVER_WORKERS=1

# Application
DEBUG=True
LOG_LEVEL=DEBUG
TITLE=ContentFlow API
VERSION=0.1.0

# CORS Settings
ALLOW_CREDENTIALS=True
ALLOW_ORIGINS=["*"]
ALLOW_METHODS=["*"]
ALLOW_HEADERS=["*"]
```

**Azure Integration:**
```env
# Azure App Configuration
AZURE_APP_CONFIG_CONNECTION_STRING=DefaultEndpointsProtocol=https;...
AZURE_APP_CONFIG_ENDPOINT=https://<resource-name>.azconfig.io

# Azure Cosmos DB
COSMOS_DB_ENDPOINT=https://<cosmos-account>.documents.azure.com:443/
COSMOS_DB_NAME=contentflow

# Azure Storage (Blobs)
BLOB_STORAGE_ACCOUNT_NAME=mystorageaccount
BLOB_STORAGE_CONTAINER_NAME=content

# Azure Storage (Queues)
STORAGE_ACCOUNT_WORKER_QUEUE_URL=https://mystorageaccount.queue.core.windows.net/
STORAGE_WORKER_QUEUE_NAME=contentflow-execution-requests

# Worker Engine
WORKER_ENGINE_API_ENDPOINT=http://contentflow-worker:8099
```

**Cosmos DB Containers:**
```env
COSMOS_DB_CONTAINER_EXECUTOR_CATALOG=executor_catalog
COSMOS_DB_CONTAINER_PIPELINES=pipelines
COSMOS_DB_CONTAINER_VAULTS=vaults
COSMOS_DB_CONTAINER_BATCH_EXECUTIONS=batch_executions
COSMOS_DB_CONTAINER_PIPELINE_EXECUTIONS=pipeline_executions
```

### Configuration Sources

The API loads configuration in the following order:
1. Environment variables (highest priority)
2. `.env` file (local development)
3. Azure App Configuration (when available)
4. Default values in `AppSettings` class

---

## 🔧 Services Architecture

### Health Service (`services/health_service.py`)
Provides system health checks for all integrated Azure services.

**Features:**
- Cosmos DB connectivity verification
- Storage Queue health status
- App Configuration connectivity
- Response time metrics

### Pipeline Service (`services/pipeline_service.py`)
Manages pipeline CRUD operations and retrieval.

**Key Methods:**
- `get_pipelines()` - List all pipelines
- `get_pipeline_by_id(id)` - Retrieve by ID
- `get_pipeline_by_name(name)` - Retrieve by name
- `create_or_save_pipeline(data)` - Create or update
- `delete_pipeline_by_id(id)` - Delete a pipeline

### Pipeline Execution Service (`services/pipeline_execution_service.py`)
Handles pipeline execution orchestration and monitoring.

**Key Methods:**
- `create_execution()` - Create execution record
- `start_execution()` - Begin pipeline execution
- `get_execution_status()` - Check execution progress
- `get_execution_events()` - Retrieve execution events

### Executor Catalog Service (`services/executor_catalog_service.py`)
Manages the catalog of available executors.

**Key Methods:**
- `get_catalog_executors()` - List all executors
- `get_catalog_executor_by_id()` - Get specific executor
- `initialize_executor_catalog()` - Load default executors

### Vault Service (`services/vault_service.py`)
Handles vault management and content organization.

**Key Methods:**
- `list_vaults()` - List with search and filtering
- `create_vault()` - Create new vault
- `get_vault()` - Retrieve vault details
- `update_vault()` - Update vault properties
- `delete_vault()` - Delete vault and content

---

## 🗄️ Data Models

### Pipeline Model
```python
{
  "id": "string",                    # Unique identifier
  "name": "string",                  # Pipeline name
  "description": "string",           # Description
  "yaml": "string",                  # YAML pipeline definition
  "nodes": [{}],                     # Visual nodes (optional)
  "edges": [{}],                     # Visual connections (optional)
  "tags": ["string"],                # Tags for organization
  "enabled": boolean,                # Enable/disable flag
  "retry_delay": number,             # Retry delay in seconds
  "timeout": number,                 # Timeout in seconds
  "retries": number,                 # Number of retries
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

### Pipeline Execution Model
```python
{
  "id": "string",                    # Execution ID
  "pipeline_id": "string",           # Parent pipeline ID
  "status": "string",                # started|running|completed|failed
  "inputs": {},                      # Input parameters
  "configuration": {},               # Execution configuration
  "outputs": {},                     # Execution results
  "error": "string",                 # Error details if failed
  "created_by": "string",            # User who triggered execution
  "created_at": "datetime",
  "updated_at": "datetime",
  "completed_at": "datetime"
}
```

### Vault Model
```python
{
  "id": "string",                    # Unique identifier
  "name": "string",                  # Vault name
  "description": "string",           # Description
  "pipeline_id": "string",           # Associated pipeline
  "tags": ["string"],                # Tags for organization
  "retention_days": number,          # Content retention period
  "size_bytes": number,              # Current vault size
  "item_count": number,              # Number of items
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

### ExecutorCatalogDefinition Model
```python
{
  "id": "string",                    # Executor identifier
  "name": "string",                  # Display name
  "description": "string",           # Purpose and functionality
  "version": "string",               # Semantic version
  "category": "string",              # Category (extraction, analysis, etc)
  "inputs": [                        # Input parameters
    {
      "name": "string",
      "type": "string",
      "required": boolean,
      "description": "string"
    }
  ],
  "outputs": [                       # Output parameters
    {
      "name": "string",
      "type": "string",
      "description": "string"
    }
  ]
}
```

---

## 🧪 Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app

# Run specific test file
pytest tests/test_pipelines.py

# Run in verbose mode
pytest -v
```

### Code Quality

```bash
# Format code with Black
black app/

# Lint with Pylint
pylint app/

# Type checking with mypy
mypy app/

# All checks
black app/ && pylint app/ && mypy app/
```

### Local Development with Docker

```bash
# Build the Docker image
docker build -t contentflow-api:latest .

# Run container locally
docker run -p 8090:8090 \
  --env-file .env \
  contentflow-api:latest

# Run with Docker Compose (if available)
docker-compose up contentflow-api
```

---

## 📊 Logging

The API uses structured logging with configurable levels.

**Log Levels:**
- `DEBUG` - Detailed diagnostic information
- `INFO` - General informational messages
- `WARNING` - Warning messages for potentially problematic situations
- `ERROR` - Error messages for serious problems
- `CRITICAL` - Critical messages for very serious problems

**Set log level via environment:**
```env
LOG_LEVEL=INFO
```

**Example log output:**
```
2024-01-02 10:30:45,123 - contentflow.api - INFO - Pipeline execution started: exec_abc123
2024-01-02 10:31:02,456 - contentflow.api - DEBUG - Executor 'pdf_extractor' processing document.pdf
2024-01-02 10:31:45,789 - contentflow.api - INFO - Pipeline execution completed: exec_abc123
```

---

## 🚀 Deployment

### Azure Container Apps

The API can be deployed to Azure Container Apps:

```bash
# Build and push image
az acr build --registry <registry-name> --image contentflow-api:latest .

# Deploy to Container Apps
az containerapp create \
  --name contentflow-api \
  --resource-group <resource-group> \
  --image <registry-name>.azurecr.io/contentflow-api:latest \
  --environment <container-app-env> \
  --target-port 8090 \
  --env-vars \
    COSMOS_DB_ENDPOINT="$COSMOS_DB_ENDPOINT" \
    BLOB_STORAGE_ACCOUNT_NAME="$BLOB_STORAGE_ACCOUNT_NAME"
```

### Docker Deployment

```bash
# Build image
docker build -t contentflow-api:latest .

# Run container
docker run -d \
  -p 8090:8090 \
  --name contentflow-api \
  --env-file .env \
  contentflow-api:latest
```

---

## 🔐 Security

### Authentication & Authorization

- Authentication via Azure Identity (Managed Identity or Service Principal)
- CORS support for cross-origin requests
- Secure credential management via Azure Key Vault
- Environment-based configuration for sensitive data

### Best Practices

- Always use HTTPS in production
- Keep `.env` files out of version control
- Use Azure Key Vault for secrets management
- Enable Application Insights for security monitoring
- Implement API rate limiting for production deployments
- Regularly update dependencies for security patches

---

## 📝 Error Handling

The API returns standard HTTP status codes and error responses:

| Status Code | Meaning |
|-------------|---------|
| `200` | Success |
| `201` | Created |
| `204` | No Content |
| `400` | Bad Request |
| `404` | Not Found |
| `500` | Internal Server Error |
| `503` | Service Unavailable |

**Error Response Format:**
```json
{
  "detail": "Error message describing what went wrong"
}
```

---

## 📚 Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Azure Cosmos DB Python SDK](https://learn.microsoft.com/en-us/python/api/overview/azure/cosmos-db)
- [Azure Storage Python SDK](https://learn.microsoft.com/en-us/python/api/overview/azure/storage)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [ContentFlow Main Repository](../README.md)
