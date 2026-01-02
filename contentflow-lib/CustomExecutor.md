# Creating Custom Executors in ContentFlow

This guide details the process of creating custom executors for the ContentFlow document processing framework. Custom executors extend the base executor classes to implement specific content processing logic.

## Table of Contents

1. [Executor Architecture Overview](#executor-architecture-overview)
2. [Base Executor Classes](#base-executor-classes)
3. [Step-by-Step Guide](#step-by-step-guide)
4. [Configuration Management](#configuration-management)
5. [Error Handling and Logging](#error-handling-and-logging)
6. [Examples](#examples)
7. [Registering Custom Executors in executor_catalog.yaml](#registering-custom-executors-in-executor_catalogyaml)
   - [File Location](#file-location)
   - [Catalog Entry Structure](#catalog-entry-structure)
   - [Step-by-Step Registration](#step-by-step-registration)
   - [Settings Schema Field Reference](#settings-schema-field-reference)
   - [Common Executor Categories](#common-executor-categories)
   - [Example: Complete Custom Executor Registration](#example-complete-custom-executor-registration)
   - [Using Your Custom Executor in Workflows](#using-your-custom-executor-in-workflows)
   - [API and Worker Discovery](#api-and-worker-discovery)
   - [Validation and Error Handling](#validation-and-error-handling)
   - [Best Practices](#best-practices)

---

## Executor Architecture Overview

The ContentFlow executor framework is built on the Agent Framework's `Executor` pattern, enhanced with document processing capabilities. All executors follow a hierarchical inheritance structure:

```
Executor (Agent Framework)
├── BaseExecutor
│   ├── ParallelExecutor
│   ├── InputExecutor
│   └── [Custom Executors]
```

### Core Concepts

- **Handler Pattern**: Executors use the `@handler` decorator to define entry points
- **Workflow Context**: Provides access to shared state and message passing
- **Content Model**: All executors work with the `Content` model for unified data handling
- **Dict-Based Configuration**: Settings are provided as Python dictionaries with environment variable resolution support
- **Async/Await**: All executors use async/await patterns for non-blocking execution

---

## Base Executor Classes

### 1. BaseExecutor

**Purpose**: The foundational class for all executors. Provides core functionality for configuration management, error handling, logging, and the basic content processing handler.

**When to Use**: 
- Simple content transformations
- Synchronous operations that don't require parallelization
- Data validation and filtering
- Single-document processing

**Key Methods to Implement**:

| Method | Purpose | Required |
|--------|---------|----------|
| `__init__(self, id: str, settings: Dict[str, Any], **kwargs)` | Initialize the executor with configuration | Yes |
| `process_input(self, input, ctx)` | Core processing logic for content | Yes |

**Handler Signature**:
```python
@handler
async def handle_content(
    self,
    input: Union[Content, List[Content]],
    ctx: WorkflowContext[Union[Content, List[Content]], Union[Content, List[Content]]]
) -> None
```

**Key Features**:
- Environment variable resolution in settings
- Debug mode for enhanced logging
- Enable/disable toggles
- Error handling with `fail_pipeline_on_error` option
- Statistics tracking (execution time)

**Example Configuration**:
```python
executor = MyCustomExecutor(
    id="my_executor",
    settings={
        "enabled": True,
        "debug_mode": False,
        "fail_pipeline_on_error": False,
        "my_custom_setting": "${MY_ENV_VAR}",  # Auto-resolved
        "another_setting": "default_value"
    }
)
```

---

### 2. ParallelExecutor

**Purpose**: Extends `BaseExecutor` for processing multiple content items concurrently with controlled concurrency levels.

**When to Use**:
- Processing lists of content items independently
- Operations requiring parallelization (e.g., API calls, AI model inference)
- Batch processing with resource constraints
- I/O-bound operations that benefit from concurrency

**Key Methods to Implement**:

| Method | Purpose | Required |
|--------|---------|----------|
| `process_content_item(self, content: Content)` | Process a single content item | Yes |

**Handler Signature**: Same as BaseExecutor, but optimized for parallel processing

**Key Features**:
- Automatic semaphore-based concurrency control
- Per-item timeout handling
- Partial failure handling with `continue_on_error`
- Graceful degradation to sequential processing if `max_concurrent <= 1`
- Individual error tracking per content item

**Configuration Options**:
```python
settings={
    "max_concurrent": 5,        # Max parallel operations
    "timeout_secs": 300,        # Per-item timeout
    "continue_on_error": True   # Skip failed items vs. fail pipeline
}
```

**Processing Flow**:
1. Receives `Content` or `List[Content]`
2. Creates async tasks with semaphore control
3. Processes each item via `process_content_item()`
4. Aggregates results with error tracking
5. Returns processed content(s)

---

### 3. InputExecutor

**Purpose**: Extends `BaseExecutor` for crawling/discovering content from external sources with pagination and checkpoint support.

**When to Use**:
- Fetching documents from external sources (databases, APIs, cloud storage)
- Implementing incremental updates via checkpoints
- Paginated data retrieval
- Content discovery and crawling operations

**Key Methods to Implement**:

| Method | Purpose | Required |
|--------|---------|----------|
| `crawl(self, checkpoint_timestamp, continuation_token)` | Fetch content from source | Yes |
| `process_input(self, input, ctx)` | Process crawled content | Yes |

**Handler Signature**: Same as BaseExecutor

**Key Features**:
- Checkpoint-based incremental crawling
- Pagination support with `continuation_token`
- Batch yielding via `crawl_all()` async generator
- Change detection via content hashing
- Configurable polling intervals and batch sizes

**Configuration Options**:
```python
settings={
    "polling_interval_seconds": 300,  # Polling frequency
    "max_results": 1000,               # Total items to fetch
    "batch_size": 100                  # Items per crawl call
}
```

**Crawling Patterns**:

**Pattern 1: Single Page**
```python
async def crawl(self, checkpoint_timestamp, continuation_token):
    items = await fetch_from_source()
    contents = [create_content(item) for item in items]
    return contents, None  # No more pages
```

**Pattern 2: Pagination**
```python
async def crawl(self, checkpoint_timestamp, continuation_token):
    items = await fetch_from_source(start_token=continuation_token)
    contents = [create_content(item) for item in items]
    next_token = items[-1].id if len(items) >= batch_size else None
    return contents, next_token  # Return token for next page
```

**Pattern 3: Incremental with Checkpoint**
```python
async def crawl(self, checkpoint_timestamp, continuation_token):
    items = await fetch_from_source(
        since=checkpoint_timestamp,
        start_token=continuation_token
    )
    contents = [create_content(item) for item in items]
    return contents, continuation_token
```

---

## Step-by-Step Guide

### Step 1: Choose the Base Class

```
BaseExecutor
  ↓
  └─ Simple transformation, single item? → BaseExecutor
  └─ Process multiple items in parallel? → ParallelExecutor
  └─ Fetch from external source? → InputExecutor
```

### Step 2: Import Required Modules

```python
import logging
from typing import Dict, Any, Optional, Union, List
from datetime import datetime

from agent_framework import WorkflowContext, handler

from ..models import Content
from .base import BaseExecutor  # or ParallelExecutor, InputExecutor
```

### Step 3: Define the Class

```python
class MyCustomExecutor(BaseExecutor):  # or appropriate base class
    """
    Brief description of what your executor does.
    
    Detailed explanation of functionality, use cases, and behavior.
    
    Configuration (settings dict):
        - setting_1 (type): Description
          Default: value
        - setting_2 (type): Description
          Default: value
    
    Example:
        ```python
        executor = MyCustomExecutor(
            id="my_executor",
            settings={
                "setting_1": "value",
                "setting_2": 42
            }
        )
        ```
    """
```

### Step 4: Implement `__init__`

```python
def __init__(
    self,
    id: str,
    settings: Optional[Dict[str, Any]] = None,
    **kwargs
):
    super().__init__(id=id, settings=settings, **kwargs)
    
    # Extract and resolve settings with defaults
    self.my_setting = self.get_setting("my_setting", default="default_value")
    self.required_setting = self.get_setting("required_setting", required=True)
    self.timeout = self.get_setting("timeout", default=30)
    
    # Validate settings
    if self.timeout <= 0:
        raise ValueError("timeout must be positive")
    
    if self.debug_mode:
        logger.debug(f"Initialized {self.__class__.__name__}: {id}")
```

### Step 5: Implement Processing Methods

**For BaseExecutor**:
```python
async def process_input(
    self,
    input: Union[Content, List[Content]],
    ctx: WorkflowContext[Union[Content, List[Content]], Union[Content, List[Content]]]
) -> Union[Content, List[Content]]:
    """Implement your processing logic here."""
    
    if isinstance(input, list):
        return [await self._process_single(item) for item in input]
    else:
        return await self._process_single(input)

async def _process_single(self, content: Content) -> Content:
    """Process a single content item."""
    # Your transformation logic
    content.data["processed"] = True
    return content
```

**For ParallelExecutor**:
```python
async def process_content_item(self, content: Content) -> Content:
    """Process a single content item (called in parallel)."""
    # Your processing logic
    # Note: ParallelExecutor handles parallelization automatically
    result = await expensive_operation(content)
    content.summary_data["result"] = result
    return content
```

**For InputExecutor**:
```python
async def crawl(
    self,
    checkpoint_timestamp: Optional[datetime] = None,
    continuation_token: Optional[str] = None
) -> Tuple[List[Content], Optional[str]]:
    """Fetch content from source."""
    # Implement your crawling logic
    items = await fetch_from_source(since=checkpoint_timestamp)
    contents = [Content(...) for item in items]
    return contents, None  # or next_token for pagination

async def process_input(
    self,
    input: Union[Content, List[Content]],
    ctx: WorkflowContext[...]
) -> Union[Content, List[Content]]:
    """Process crawled content."""
    # Implement your processing logic
    return input  # or modified input
```

### Step 6: Add Logging

```python
logger = logging.getLogger("contentflow.executors.my_executor")

class MyCustomExecutor(BaseExecutor):
    async def process_input(self, input, ctx):
        if self.debug_mode:
            logger.debug(f"Processing input: {input}")
        
        try:
            result = await self._do_work(input)
            logger.info(f"Successfully processed: {input.id}")
            return result
        except Exception as e:
            logger.error(f"Processing failed: {str(e)}", exc_info=True)
            raise
```

### Step 7: Test Your Executor

```python
import pytest

@pytest.mark.asyncio
async def test_my_executor():
    executor = MyCustomExecutor(
        id="test_executor",
        settings={"my_setting": "test"}
    )
    
    content = Content(...)
    result = await executor.process_input(content, ctx)
    
    assert result.data["processed"] == True
```

### Step 8: Register Your Executor in executor_catalog.yaml

**See details below on how to [register in executor_catalog.yaml](#registering-custom-executors-in-executor_catalogyaml)**

---

## Configuration Management

### Setting Resolution

Settings support environment variable substitution using `${VAR_NAME}` syntax:

```python
settings={
    "api_key": "${API_KEY}",              # Resolved at runtime
    "endpoint": "https://api.example.com", # Literal value
    "retry_count": 3,                      # Type preserved
    "nested": {
        "value": "${NESTED_VAR}"           # Not auto-resolved in nested dicts
    }
}
```

### Accessing Settings

```python
# With default value
value = self.get_setting("setting_key", default="default")

# Required (raises if missing)
value = self.get_setting("setting_key", required=True)

# Direct access
value = self.settings.get("setting_key")
```

### Common Configuration Patterns

**Credentials**:
```python
settings={
    "api_key": "${AZURE_API_KEY}",
    "api_endpoint": "${API_ENDPOINT}",
    "auth_type": "key"
}
```

**Concurrency Control**:
```python
settings={
    "max_concurrent": 10,
    "timeout_secs": 300,
    "continue_on_error": True
}
```

**Feature Toggles**:
```python
settings={
    "enabled": True,
    "debug_mode": False,
    "fail_pipeline_on_error": False
}
```

---

## Error Handling and Logging

### Error Handling Patterns

**Pattern 1: Fail on Error**
```python
executor = MyExecutor(
    id="strict_executor",
    settings={
        "fail_pipeline_on_error": True  # Stop pipeline on error
    }
)
```

**Pattern 2: Continue on Error (ParallelExecutor)**
```python
executor = MyExecutor(
    id="tolerant_executor",
    settings={
        "continue_on_error": True,  # Skip failed items, process others
        "max_concurrent": 5
    }
)
```

**Pattern 3: Retry Logic**
```python
async def process_content_item(self, content: Content) -> Content:
    max_retries = self.get_setting("max_retries", default=3)
    retry_delay = self.get_setting("retry_delay", default=1.0)
    
    for attempt in range(max_retries):
        try:
            return await self._do_work(content)
        except Exception as e:
            if attempt < max_retries - 1:
                await asyncio.sleep(retry_delay)
                logger.warning(f"Retry {attempt + 1}/{max_retries}")
            else:
                logger.error(f"Failed after {max_retries} retries")
                raise
```

### Logging Best Practices

```python
logger = logging.getLogger(__name__)

class MyExecutor(BaseExecutor):
    async def process_input(self, input, ctx):
        # Debug info
        if self.debug_mode:
            logger.debug(f"Input: {input}")
        
        # Info level
        logger.info(f"Processing started for: {input.id}")
        
        try:
            result = await self._do_work(input)
            logger.info(f"Processing completed successfully")
            return result
        except SpecificError as e:
            logger.warning(f"Non-critical error: {e}")
            # Handle gracefully
        except Exception as e:
            logger.error(f"Critical error: {e}", exc_info=True)
            raise
```

---

## Examples

### Example 1: Simple Text Transformation Executor

```python
class TextTransformerExecutor(BaseExecutor):
    """Transform text content using simple operations."""
    
    def __init__(self, id: str, settings: Optional[Dict[str, Any]] = None, **kwargs):
        super().__init__(id=id, settings=settings, **kwargs)
        self.operation = self.get_setting("operation", required=True)  # "upper", "lower", "reverse"
    
    async def process_input(
        self,
        input: Union[Content, List[Content]],
        ctx: WorkflowContext[Union[Content, List[Content]], Union[Content, List[Content]]]
    ) -> Union[Content, List[Content]]:
        if isinstance(input, list):
            return [await self._transform_content(item) for item in input]
        return await self._transform_content(input)
    
    async def _transform_content(self, content: Content) -> Content:
        text = content.data.get("text", "")
        
        if self.operation == "upper":
            content.data["text"] = text.upper()
        elif self.operation == "lower":
            content.data["text"] = text.lower()
        elif self.operation == "reverse":
            content.data["text"] = text[::-1]
        
        return content
```

### Example 2: Parallel API Call Executor

```python
import aiohttp

class APICallExecutor(ParallelExecutor):
    """Make API calls to external service in parallel."""
    
    def __init__(self, id: str, settings: Optional[Dict[str, Any]] = None, **kwargs):
        super().__init__(id=id, settings=settings, **kwargs)
        self.api_endpoint = self.get_setting("api_endpoint", required=True)
        self.api_key = self.get_setting("api_key", required=True)
    
    async def process_content_item(self, content: Content) -> Content:
        """Called in parallel for each content item."""
        item_id = content.id.canonical_id
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.api_endpoint,
                json=content.data,
                headers={"Authorization": f"Bearer {self.api_key}"}
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    content.summary_data["api_result"] = result
                else:
                    raise Exception(f"API error: {response.status}")
        
        return content
```

### Example 3: Input Crawler Executor

```python
class DatabaseCrawlerExecutor(InputExecutor):
    """Crawl documents from database with pagination."""
    
    def __init__(self, id: str, settings: Optional[Dict[str, Any]] = None, **kwargs):
        super().__init__(id=id, settings=settings, **kwargs)
        self.connection_string = self.get_setting("connection_string", required=True)
        self.query = self.get_setting("query", required=True)
    
    async def crawl(
        self,
        checkpoint_timestamp: Optional[datetime] = None,
        continuation_token: Optional[str] = None
    ) -> Tuple[List[Content], Optional[str]]:
        """Fetch documents from database."""
        # Pseudo-code for illustration
        offset = int(continuation_token or 0)
        
        async with self.get_db_connection() as conn:
            query = self.query
            if checkpoint_timestamp:
                query += f" WHERE updated_at > {checkpoint_timestamp}"
            
            rows = await conn.fetch(
                query,
                limit=self.batch_size,
                offset=offset
            )
        
        if not rows:
            return [], None  # No more data
        
        contents = []
        for row in rows:
            content = Content(
                id=ContentIdentifier(canonical_id=str(row['id'])),
                data=dict(row)
            )
            contents.append(content)
        
        next_token = str(offset + len(rows)) if len(rows) >= self.batch_size else None
        return contents, next_token
    
    async def process_input(
        self,
        input: Union[Content, List[Content]],
        ctx: WorkflowContext[Union[Content, List[Content]], Union[Content, List[Content]]]
    ) -> Union[Content, List[Content]]:
        """Process crawled content (optional)."""
        return input
```

---

## Registering Custom Executors in executor_catalog.yaml

After creating your custom executor, you must register it in the `executor_catalog.yaml` file so the API and worker apps can discover and use it. This YAML file serves as the source of truth for all available executors.

### File Location

The executor catalog is located at:
```
/contentflow-lib/executor_catalog.yaml
```

### Catalog Entry Structure

Each executor entry in the catalog is a dictionary with the following structure:

```yaml
- id: unique_executor_id
  name: "Human-Readable Executor Name"
  description: "Description of what this executor does"
  module_path: contentflow.executors.module_name
  class_name: MyCustomExecutorClass
  tags: [tag1, tag2, tag3]  # For filtering and discovery
  category: "category_name"  # input, extract, transform, analyse, output
  version: "1.0"
  
  # Settings schema for validation and UI generation
  settings_schema:
    # Define all configurable settings here
    setting_1:
      type: string
      title: "Setting Display Name"
      description: "What this setting does"
      required: true
      default: null
      ui_component: "input"  # or select, checkbox, number, etc.
    
    setting_2:
      type: integer
      title: "Max Concurrent"
      description: "Maximum concurrent operations"
      required: false
      default: 5
      min: 1
      max: 20
      ui_component: "number"
  
  # UI metadata for dashboard/API display
  ui_metadata:
    icon: "icon_name"  # Reference to lucide icon
    description_short: "Brief one-line description"
    description_long: "Detailed description for help/documentation"
```

### Step-by-Step Registration

#### Step 1: Prepare Your Executor Module

Ensure your executor is:
- Located in `contentflow/executors/` directory
- Named with lowercase with underscores (e.g., `my_custom_executor.py`)
- Contains a class that extends `BaseExecutor`, `ParallelExecutor` or `InputExecutor`

Example structure:
```
contentflow/executors/
├── my_custom_executor.py
├── __init__.py
└── [other executors...]
```

#### Step 2: Identify Your Module Path and Class Name

- **module_path**: Full Python import path (e.g., `contentflow.executors.my_custom_executor`)
- **class_name**: Exact class name in that module (e.g., `MyCustomExecutorClass`)

#### Step 3: Extract Settings Schema

List all configuration settings from your `__init__` method and create schema entries:

```python
# From your executor
def __init__(self, id: str, settings: Optional[Dict[str, Any]] = None, **kwargs):
    super().__init__(id=id, settings=settings, **kwargs)
    
    self.api_endpoint = self.get_setting("api_endpoint", required=True)
    self.timeout = self.get_setting("timeout", default=30)
    self.retry_count = self.get_setting("retry_count", default=3)
    self.debug_enabled = self.get_setting("debug_enabled", default=False)
```

Becomes:
```yaml
settings_schema:
  api_endpoint:
    type: string
    title: "API Endpoint"
    description: "The API endpoint URL"
    required: true
    default: "https://api.example.com"
    ui_component: "input"
  
  timeout:
    type: integer
    title: "Timeout (seconds)"
    description: "Request timeout in seconds"
    required: false
    default: 30
    min: 1
    max: 300
    ui_component: "number"
  
  retry_count:
    type: integer
    title: "Retry Count"
    description: "Number of retries on failure"
    required: false
    default: 3
    min: 0
    max: 10
    ui_component: "number"
  
  debug_enabled:
    type: boolean
    title: "Debug Mode"
    description: "Enable debug logging"
    required: false
    default: false
    ui_component: "checkbox"
```

#### Step 4: Add to executor_catalog.yaml

Append your executor entry to the end of the executors list in `executor_catalog.yaml`:

```yaml
  ########################################################
  # My Custom Executor
  - id: my_custom_executor
    name: "My Custom Executor"
    description: "A custom executor that performs specific processing tasks"
    module_path: contentflow.executors.my_custom_executor
    class_name: MyCustomExecutorClass
    tags: [custom, processing, analysis]
    category: "analyse"
    version: "1.0"
    
    settings_schema:
      # ... your settings schema here ...
    
    ui_metadata:
      icon: "sparkles"
      description_short: "Custom processing"
      description_long: "Performs custom processing on content items with configurable parameters."
```

### Settings Schema Field Reference

#### Type Options

```yaml
type: string      # Text input
type: integer     # Whole number
type: number      # Decimal number
type: boolean     # True/false checkbox
```

#### UI Component Options

```yaml
ui_component: input           # Text input field
ui_component: textarea        # Multi-line text
ui_component: number          # Number spinner
ui_component: checkbox        # Boolean toggle
ui_component: select          # Dropdown (requires 'options')
ui_component: password        # Masked input (for sensitive data)
```

#### Common Attributes

| Attribute | Type | Purpose | Required |
|-----------|------|---------|----------|
| `type` | string | Data type: `string`, `integer`, `number`, `boolean` | Yes |
| `title` | string | Display name in UI | Yes |
| `description` | string | Help text explaining the setting | Yes |
| `required` | boolean | Whether user must provide a value | No (default: false) |
| `default` | any | Default value if not provided | No |
| `ui_component` | string | How to render in UI | No |
| `placeholder` | string | Placeholder text for input fields | No |
| `options` | array | Choices for select dropdown | No |
| `min` | number | Minimum value for numbers | No |
| `max` | number | Maximum value for numbers | No |
| `pattern` | string | Regex pattern for validation | No |

### Common Executor Categories

Use one of these standard categories:

```
input      - Input discovery/crawling (InputExecutor)
extract    - Content extraction from documents
transform  - Data transformation and chunking
analyse    - AI analysis and processing
output     - Writing results to destinations
```

### Example: Complete Custom Executor Registration

```yaml
  ########################################################
  # Text Sentiment Analyzer
  - id: text_sentiment_analyzer
    name: "Text Sentiment Analyzer"
    description: "Analyzes text sentiment using Azure AI Language Services"
    module_path: contentflow.executors.text_sentiment_analyzer
    class_name: TextSentimentAnalyzerExecutor
    tags: [analysis, nlp, sentiment, azure-ai, parallel]
    category: "analyse"
    version: "1.0"
    
    settings_schema:
      # Common settings (shown in all executors)
      enabled:
        type: boolean
        title: "Enabled"
        description: "Enable or disable this executor"
        required: false
        default: true
        ui_component: "checkbox"
      
      fail_pipeline_on_error:
        type: boolean
        title: "Fail Pipeline On Error"
        description: "Fail the entire pipeline if analysis fails"
        required: false
        default: false
        ui_component: "checkbox"
      
      debug_mode:
        type: boolean
        title: "Debug Mode"
        description: "Enable debug logging"
        required: false
        default: false
        ui_component: "checkbox"
      
      # Executor-specific settings
      text_field:
        type: string
        title: "Text Field"
        description: "Field containing text to analyze (e.g., 'text', 'content')"
        required: false
        default: "text"
        ui_component: "input"
      
      output_field:
        type: string
        title: "Output Field"
        description: "Field to store sentiment analysis results"
        required: false
        default: "sentiment"
        ui_component: "input"
      
      language:
        type: string
        title: "Language"
        description: "Language code of the text (e.g., 'en', 'es', 'fr')"
        required: false
        default: "en"
        ui_component: "select"
        options: ["en", "es", "fr", "de", "it", "pt", "zh-Hans", "ja", "ko"]
      
      include_scores:
        type: boolean
        title: "Include Confidence Scores"
        description: "Include confidence scores for each sentiment"
        required: false
        default: true
        ui_component: "checkbox"
      
      min_confidence:
        type: number
        title: "Minimum Confidence"
        description: "Only include results with confidence above this threshold"
        required: false
        default: 0.5
        min: 0.0
        max: 1.0
        ui_component: "number"
      
      max_concurrent:
        type: integer
        title: "Max Concurrent Analysis"
        description: "Maximum parallel analysis operations"
        required: false
        default: 5
        min: 1
        max: 20
        ui_component: "number"
      
      continue_on_error:
        type: boolean
        title: "Continue On Error"
        description: "Continue with remaining items if one fails"
        required: false
        default: true
        ui_component: "checkbox"
      
      ai_language_endpoint:
        type: string
        title: "Azure AI Language Endpoint"
        description: "Azure AI Language service endpoint"
        required: true
        default: null
        ui_component: "input"
        placeholder: "https://<region>.api.cognitive.microsoft.com/"
      
      ai_language_credential_type:
        type: string
        title: "Credential Type"
        description: "Authentication method"
        required: false
        default: "default_azure_credential"
        ui_component: "select"
        options: ["default_azure_credential", "api_key"]
      
      ai_language_api_key:
        type: string
        title: "API Key"
        description: "Azure AI Language API key (if using api_key credential)"
        required: false
        default: null
        ui_component: "password"
    
    ui_metadata:
      icon: "brain"
      description_short: "Analyze text sentiment"
      description_long: "Analyzes sentiment of text content using Azure AI Language Services. Returns sentiment labels (positive, negative, mixed, neutral) with confidence scores. Perfect for content classification and feedback analysis."
```

### Using Your Custom Executor in Workflows

Once registered, your executor can be used in workflow YAML:

```yaml
# workflow.yaml
executors:
  - id: my_analyzer
    type: my_custom_executor  # Use the 'id' from catalog
    settings:
      api_endpoint: "${API_ENDPOINT}"
      timeout: 60
      retry_count: 3
      debug_enabled: true
```

Or programmatically:

```python
from contentflow.executors import MyCustomExecutorClass

executor = MyCustomExecutorClass(
    id="my_analyzer",
    settings={
        "api_endpoint": "https://api.example.com",
        "timeout": 60,
        "retry_count": 3
    }
)
```

### API and Worker Discovery

The API and worker apps automatically:
1. **Load** the executor catalog at startup
2. **Validate** executor settings against the schema
3. **Generate UI** components for the dashboard
4. **Instantiate** executors with provided settings
5. **Execute** them in workflows

This means once you add your executor to the catalog, it's automatically available to:
- **contentflow-api**: REST API endpoints for workflow execution
- **contentflow-worker**: Async worker processing queued workflows
- **contentflow-web**: Dashboard UI for configuring and running workflows

### Validation and Error Handling

The catalog settings schema is used for:
- **Type validation**: Ensuring settings are the correct type
- **Required field checking**: Verifying all required settings are provided
- **Range checking**: Validating min/max for numeric fields
- **Enum validation**: Checking values against defined options
- **Pattern matching**: Validating strings against regex patterns

If an executor is instantiated with invalid settings, it will raise a `ValueError` with details about what's wrong.

### Best Practices

1. **Use descriptive IDs**: Use `snake_case` for executor IDs (e.g., `text_sentiment_analyzer`)
2. **Include all settings**: Document every setting your executor accepts
3. **Provide defaults**: Set sensible defaults for optional settings
4. **Use proper categories**: Choose the category that best describes your executor's function
5. **Add helpful descriptions**: Write clear descriptions for each setting
6. **Choose appropriate UI components**: Match the component to the data type
7. **Include validation ranges**: Set min/max for numeric settings
8. **Use meaningful tags**: Add tags for filtering and discovery
9. **Update version**: Increment version when making breaking changes
10. **Test before deploying**: Verify the settings schema works with your executor

---

## Summary

| Base Class | Use Case | Key Method | Handler Type |
|-----------|----------|-----------|--------------|
| **BaseExecutor** | Simple transformations | `process_input()` | `@handler` |
| **ParallelExecutor** | Parallel processing | `process_content_item()` | `@handler` |
| **InputExecutor** | Content crawling | `crawl()` | `@handler` |

All executors support:
- Dict-based configuration
- Environment variable resolution
- Debug logging
- Error handling with configurable behavior
- Integration with Agent Framework workflows
- Async/await patterns

### Registration Checklist

When adding a custom executor:
- [ ] Create executor class inheriting from appropriate base class
- [ ] Implement required abstract methods
- [ ] Add comprehensive docstring with configuration details
- [ ] Create module in `contentflow/executors/` directory
- [ ] Add entry to `executor_catalog.yaml`
- [ ] Include full `settings_schema` with all configurable options
- [ ] Add `ui_metadata` with icon and descriptions
- [ ] Test executor with API and worker apps
- [ ] Update project documentation if needed
