# ContentFlow Worker

Multi-processing based worker engine for processing content through ContentFlow pipelines.

## Overview

The ContentFlow Worker is a distributed, multi-processing engine designed to:
- Process content items through ContentFlow pipelines
- Discover content from input sources (Azure Blob Storage, etc.)
- Scale processing across multiple worker processes
- Handle task queuing, retries, and fault tolerance

## Architecture

The worker engine consists of two types of worker processes:

### 1. Content Processing Workers
- Listen to the Azure Storage Queue for processing tasks
- Execute ContentFlow pipelines on content items (excluding already-executed input executors)
- Report execution status to Cosmos DB
- Handle task retries and error recovery

### 2. Input Source Workers
- Poll Cosmos DB for enabled pipelines associated with vaults
- Parse pipeline configuration to identify input executors
- Execute input executors to discover content from sources
- Create processing tasks for discovered content items
- Queue tasks for processing workers

## Components

```
contentflow-worker/
├── engine.py              # Main worker engine (manages processes)
├── processing_worker.py   # Content processing worker
├── source_worker.py       # Input source loading worker
├── queue_client.py        # Azure Storage Queue wrapper
├── models.py              # Task models (Pydantic)
├── settings.py            # Configuration and settings
├── main.py                # Entry point
└── requirements.txt       # Dependencies
```

## Configuration

Configuration is loaded from:
1. Environment variables (`.env` file)
2. Azure App Configuration (if available)

### Environment Variables

```bash
# Worker Settings
WORKER_NAME=contentflow-worker
NUM_PROCESSING_WORKERS=4
NUM_SOURCE_WORKERS=2

# Azure Storage Queue
STORAGE_ACCOUNT_WORKER_QUEUE_URL=https://your-storage.queue.core.windows.net
STORAGE_WORKER_QUEUE_NAME=contentflow-execution-requests

# Cosmos DB
COSMOS_DB_ENDPOINT=https://your-cosmos.documents.azure.com:443/
COSMOS_DB_NAME=contentflow
COSMOS_DB_CONTAINER_PIPELINES=pipelines
COSMOS_DB_CONTAINER_PIPELINE_EXECUTIONS=pipeline_executions
COSMOS_DB_CONTAINER_VAULTS=vaults
COSMOS_DB_CONTAINER_LOCKS=locks

# Source Workers (Continuous Scheduling)
DEFAULT_POLLING_INTERVAL_SECONDS=300    # Default 5 min if executor doesn't specify
SCHEDULER_SLEEP_INTERVAL_SECONDS=5      # How often to check schedule
LOCK_TTL_SECONDS=300                    # Distributed lock TTL (5 minutes)

# Logging
LOG_LEVEL=INFO
```

**Per-Executor Polling Intervals**: Configure polling intervals directly in executor settings:
```yaml
executors:
  - id: blob_input
    type: azure_blob_input
    settings:
      polling_interval_seconds: 300  # Check every 5 minutes
      blob_storage_account: "mystorageaccount"
```

See `.env.example` for complete configuration options.

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure environment:
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. Ensure contentflow-lib is available:
```bash
# Worker expects contentflow-lib in parent directory
# ../contentflow-lib
```

## Usage

### Running the Worker

```bash
python main.py
```

The worker will:
1. Start configured number of processing and source workers
2. Connect to Azure Storage Queue
3. Begin processing tasks
4. Monitor worker health and restart failed workers
5. Handle graceful shutdown on SIGINT/SIGTERM

### Graceful Shutdown

Press `Ctrl+C` or send SIGTERM to gracefully stop all workers:
```bash
kill -TERM <worker-pid>
```

## Task Types

### ContentProcessingTask
Executes a pipeline on a content item.

```python
{
    "task_id": "task_abc123",
    "task_type": "content_processing",
    "pipeline_id": "pipeline_xyz",
    "pipeline_name": "Document Processing",
    "execution_id": "exec_123",
    "content_id": "content_456",
    "content_data": {...},
    "executed_input_executor": "blob_input",  # Already-executed input executor
    "priority": "normal",
    "max_retries": 3
}
```

## Workflow

### Source Worker Workflow (Continuous Scheduling)
1. **Continuous Scheduling Loop**:
   - Runs continuously, checking pipeline schedule every 5 seconds
   - Maintains next execution time for each pipeline based on per-executor polling intervals
   
2. **Pipeline Discovery**:
   - Queries Cosmos DB for enabled pipelines with associated vaults
   - Extracts `polling_interval_seconds` from input executor settings (default: 300s)
   - Schedules pipelines for execution at appropriate intervals
   
3. **Distributed Locking**:
   - Before executing a pipeline, attempts to acquire a distributed lock in Cosmos DB
   - Prevents multiple workers from processing the same pipeline simultaneously
   - Locks auto-expire after 5 minutes (configurable via `LOCK_TTL_SECONDS`)
   
4. **Content Discovery**:
   - Parse pipeline YAML to find input executor
   - Execute input executor to discover content
   - Create ContentProcessingTask for each discovered content item
   - Mark the input executor as already executed (`executed_input_executor` field)
   - Send tasks to queue
   
5. **Schedule Update**:
   - After successful execution, update next execution time
   - Release distributed lock
   - Pipeline will execute again after polling interval expires

**Example: Pipeline with 1-hour polling**
```yaml
executors:
  - id: blob_input
    type: azure_blob_input
    settings:
      polling_interval_seconds: 3600  # Check every hour
      blob_storage_account: "mystorageaccount"
      blob_container_name: "documents"
```

### Processing Worker Workflow
1. Poll queue for ContentProcessingTask messages
2. For each task:
   - Load pipeline configuration
   - Exclude the already-executed input executor
   - Execute remaining pipeline on content
   - Update execution status
   - Delete message on success

## Sending Tasks to the Queue

You can send tasks from the API or other services:

```python
from contentflow_worker import TaskQueueClient, ContentProcessingTask

# Initialize queue client
queue_client = TaskQueueClient(
    queue_url="https://your-storage.queue.core.windows.net",
    queue_name="contentflow-execution-requests"
)

# Create task
task = ContentProcessingTask(
    task_id="task_123",
    pipeline_id="pipeline_xyz",
    pipeline_name="My Pipeline",
    execution_id="exec_456",
    content_id="content_789",
    content_data={"text": "Sample content"}
)

# Send to queue
queue_client.send_content_processing_task(task)
```

## Monitoring

### Worker Status

The engine provides status information:
```python
from contentflow_worker import WorkerEngine

engine = WorkerEngine()
status = engine.get_status()
print(status)
```

Output:
```json
{
    "running": true,
    "processing_workers": {
        "configured": 4,
        "active": 4,
        "workers": [
            {"id": 0, "pid": 12345, "alive": true},
            {"id": 1, "pid": 12346, "alive": true},
            ...
        ]
    },
    "source_workers": {
        "configured": 2,
        "active": 2,
        "workers": [...]
    }
}
```

### Logs

Workers log to:
- Console (stdout)
- `worker.log` file

## Features

✅ Multi-processing parallelism  
✅ Azure Storage Queue integration  
✅ Automatic worker restart on failure  
✅ Task retry handling  
✅ Graceful shutdown  
✅ Configurable worker counts  
✅ Pipeline execution tracking  
✅ Content source discovery  
✅ Cosmos DB integration  

## Error Handling

- **Task Failures**: Tasks are retried up to `max_retries` times
- **Worker Crashes**: Engine automatically restarts crashed workers
- **Queue Visibility**: Failed tasks become visible again after timeout
- **Execution Tracking**: All execution status updates are recorded in Cosmos DB

## Performance Tuning

Adjust these settings for your workload:

```bash
# More workers = higher throughput
NUM_PROCESSING_WORKERS=8
NUM_SOURCE_WORKERS=4

# Faster polling = lower latency
QUEUE_POLL_INTERVAL_SECONDS=2

# More messages per poll = higher throughput
QUEUE_MAX_MESSAGES=32

# Longer timeout = support longer-running pipelines
TASK_TIMEOUT_SECONDS=1200
```

## Requirements

- Python 3.8+
- Azure Storage Account (Queue)
- Azure Cosmos DB
- contentflow-lib package
- Azure credentials (DefaultAzureCredential)

## License

See main ContentFlow project license.
