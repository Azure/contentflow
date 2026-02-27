---
name: contentflow-custom-executor
description: Create custom ContentFlow executors for document processing pipelines. Use when building new executors, extending BaseExecutor/ParallelExecutor/InputExecutor, working with the Content data model, registering executors in executor_catalog.yaml, or implementing process_input/process_content_item/crawl methods. Triggers on custom executor, new executor, ContentFlow executor, pipeline step, Content model, executor catalog, process_input, process_content_item, BaseExecutor, ParallelExecutor, InputExecutor.
---

# ContentFlow Custom Executor Development

Build custom pipeline executors for the ContentFlow document processing framework.

## Architecture Overview

ContentFlow executors follow a hierarchical inheritance structure built on the Agent Framework's `Executor` pattern:

```
Executor (Agent Framework)
├── BaseExecutor           — Simple transformations, single/list content processing
│   ├── ParallelExecutor   — Concurrent processing of multiple content items
│   │   └── AzureOpenAIAgentExecutor — AI-powered content processing
│   ├── InputExecutor      — Content discovery/crawling from external sources
│   └── [Your Custom Executor]
```

## Content Data Model

All executors work with the `Content` Pydantic model, defined in `contentflow-lib/contentflow/models/_content.py`:

```python
from contentflow.models import Content, ContentIdentifier, ExecutorLogEntry

class ContentIdentifier(BaseModel):
    canonical_id: str       # Canonical identifier
    unique_id: str          # Unique identifier
    source_name: str | None # Source instance name
    source_type: str | None # Data source type (azure_blob, sharepoint, etc.)
    container: str | None   # Container/bucket name
    path: str | None        # Path within the source
    filename: str | None    # Filename
    metadata: dict | None   # Associated metadata

class Content(BaseModel):
    id: ContentIdentifier           # Content identifier
    summary_data: dict[str, Any]    # Summary/aggregated data
    data: dict[str, Any]            # Main data dictionary
    executor_logs: List[ExecutorLogEntry]  # Execution tracking
```

**Key data access patterns:**
- `content.data["field_name"]` — read/write main data fields
- `content.summary_data["key"]` — read/write summary-level data
- `content.id.canonical_id` — get the content's canonical identifier
- `self.try_extract_nested_field_from_content(content, "nested.field.path")` — extract nested fields using dot notation

## Base Classes

### 1. BaseExecutor

**When to use:** Simple transformations, data validation, filtering, single-document processing.

**Required imports:**
```python
import logging
from typing import Dict, Any, Optional, Union, List
from agent_framework import WorkflowContext, handler
from contentflow.models import Content
from contentflow.executors.base import BaseExecutor
```

**Required method:** `process_input(self, input, ctx) -> Union[Content, List[Content]]`

**Template:**
```python
logger = logging.getLogger("contentflow.executors.my_executor")

class MyExecutor(BaseExecutor):
    """
    Brief description of what this executor does.

    Configuration (settings dict):
        - my_setting (str): Description. Default: "default"
        - another_setting (int): Description. Default: 10
    """

    def __init__(self, id: str, settings: Optional[Dict[str, Any]] = None, **kwargs):
        super().__init__(id=id, settings=settings, **kwargs)
        self.my_setting = self.get_setting("my_setting", default="default")
        self.another_setting = self.get_setting("another_setting", default=10)

    async def process_input(
        self,
        input: Union[Content, List[Content]],
        ctx: WorkflowContext[Union[Content, List[Content]], Union[Content, List[Content]]]
    ) -> Union[Content, List[Content]]:
        if isinstance(input, list):
            return [await self._process_single(item) for item in input]
        return await self._process_single(input)

    async def _process_single(self, content: Content) -> Content:
        # Your transformation logic here
        content.data["result"] = "processed"
        return content
```

### 2. ParallelExecutor

**When to use:** Concurrent processing of multiple items, API calls, AI model inference, I/O-bound operations.

**Required imports:**
```python
from contentflow.executors.parallel_executor import ParallelExecutor
```

**Required method:** `process_content_item(self, content: Content) -> Content`

**Built-in settings:** `max_concurrent` (default: 5), `timeout_secs` (default: 300), `continue_on_error` (default: True)

**Template:**
```python
class MyParallelExecutor(ParallelExecutor):
    def __init__(self, id: str, settings: Optional[Dict[str, Any]] = None, **kwargs):
        super().__init__(id=id, settings=settings, **kwargs)
        self.api_endpoint = self.get_setting("api_endpoint", required=True)

    async def process_content_item(self, content: Content) -> Content:
        # Called in parallel for each content item
        result = await call_api(self.api_endpoint, content.data)
        content.data["api_result"] = result
        return content
```

### 3. InputExecutor

**When to use:** Content discovery/crawling from external sources, paginated retrieval, incremental updates.

**Required imports:**
```python
from contentflow.executors.input_executor import InputExecutor
```

**Required methods:** `crawl(self, checkpoint_timestamp, continuation_token)` and `process_input(self, input, ctx)`

**Built-in settings:** `polling_interval_seconds` (default: 300), `max_results` (default: 1000), `batch_size` (default: 100)

**Template:**
```python
class MyCrawlerExecutor(InputExecutor):
    def __init__(self, id: str, settings: Optional[Dict[str, Any]] = None, **kwargs):
        super().__init__(id=id, settings=settings, **kwargs)
        self.source_url = self.get_setting("source_url", required=True)

    async def crawl(self, checkpoint_timestamp=None, continuation_token=None):
        items = await fetch_from_source(self.source_url, since=checkpoint_timestamp)
        contents = [
            Content(
                id=ContentIdentifier(canonical_id=item["id"], unique_id=item["id"]),
                data=item
            )
            for item in items
        ]
        return contents, None  # (results, next_continuation_token)

    async def process_input(self, input, ctx):
        return input
```

### 4. AzureOpenAIAgentExecutor (AI-Powered)

**When to use:** AI/LLM-powered content processing (summarization, entity extraction, classification, etc.)

**Required imports:**
```python
from contentflow.executors.azure_openai_agent_executor import AzureOpenAIAgentExecutor
```

**Key pattern:** Override `__init__` to set specialized `instructions`, `input_field`, `output_field` in settings, then call `super().__init__()`.

**Built-in settings:** `endpoint`, `deployment_name`, `credential_type`, `input_field`, `output_field`, `instructions`, `parse_response_as_json`, `temperature`, `max_tokens`

**Template (follows the SummarizationExecutor/EntityExtractionExecutor pattern):**
```python
class MyAIExecutor(AzureOpenAIAgentExecutor):
    def __init__(self, id: str, settings: Optional[Dict[str, Any]] = None, **kwargs):
        settings = settings or {}

        # Build specialized instructions
        instructions = "You are an expert at [task]. [Detailed instructions...]"

        if "input_field" not in settings:
            settings["input_field"] = "text"
        if "output_field" not in settings:
            settings["output_field"] = "my_result"

        settings["instructions"] = instructions
        settings["parse_response_as_json"] = True  # or False for plain text

        super().__init__(id=id, settings=settings, **kwargs)

    async def process_content_item(self, content: Content) -> Content:
        content = await super().process_content_item(content)
        # Optional post-processing
        return content
```

## Configuration Management

### Setting Resolution
- Use `self.get_setting("key", default=value)` for optional settings
- Use `self.get_setting("key", required=True)` for required settings
- Environment variables: `"${ENV_VAR_NAME}"` syntax is auto-resolved
- Access raw settings: `self.settings.get("key")`
- Nested field extraction: `self.try_extract_nested_field_from_content(content, "field.subfield")`

### Common Base Settings (inherited)
All executors automatically support:
- `enabled` (bool, default: True)
- `condition` (str, default: None) — condition expression evaluated per content item
- `fail_pipeline_on_error` (bool, default: False)
- `debug_mode` (bool, default: False)

## Handler Pattern

The `@handler` decorator on `handle_content` in BaseExecutor is the entry point called by the Agent Framework workflow engine. You do NOT need to implement a handler — just implement the abstract methods (`process_input`, `process_content_item`, or `crawl`). The base handler manages:

1. Checking if executor is enabled
2. Evaluating conditions per content item
3. Calling your `process_input()` method
4. Error handling (fail vs. pass-through)
5. Sending processed content downstream via `ctx.send_message()` and `ctx.yield_output()`

## Registering in executor_catalog.yaml

After creating your executor, register it in `contentflow-lib/executor_catalog.yaml`:

```yaml
  ########################################################
  # My Custom Executor
  - id: my_custom_executor
    name: "My Custom Executor"
    description: "Description of what it does"
    module_path: contentflow.executors.my_custom_executor
    class_name: MyCustomExecutor
    tags: [custom, processing]
    category: "transform"  # input | extract | transform | analyse | output
    version: "1.0"

    settings_schema:
      enabled:
        type: boolean
        title: "Enabled"
        description: "Enable or disable this executor"
        required: false
        default: true
        ui_component: "checkbox"

      condition:
        type: string
        title: "Condition"
        description: "Condition to evaluate for each content item"
        required: false
        default: null
        ui_component: "textarea"

      fail_pipeline_on_error:
        type: boolean
        title: "Fail Pipeline On Error"
        description: "Fail the entire pipeline on error"
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

      # Add your custom settings here...
      my_setting:
        type: string
        title: "My Setting"
        description: "What this setting does"
        required: true
        default: null
        ui_component: "input"

    ui_metadata:
      icon: "sparkles"
      description_short: "Brief one-liner"
      description_long: "Detailed description for docs"
```

### Settings Schema Types
- `string` → `ui_component: "input"`, `"textarea"`, `"password"`, `"select"`
- `integer` / `number` → `ui_component: "number"` (supports `min`, `max`)
- `boolean` → `ui_component: "checkbox"`
- For dropdowns: add `options: ["opt1", "opt2"]` with `ui_component: "select"`

### Categories
- `input` — Content discovery/crawling (InputExecutor subclasses)
- `extract` — Content extraction from documents
- `transform` — Data transformation and chunking
- `analyse` — AI analysis and processing
- `output` — Writing results to destinations

## Workflow YAML Usage

Once registered, executors are used in workflow YAML files:

```yaml
executors:
  - id: my_step
    type: my_custom_executor
    settings:
      my_setting: "value"
      debug_mode: true
```

## Error Handling Patterns

**Retry logic (for ParallelExecutor):**
```python
async def process_content_item(self, content: Content) -> Content:
    for attempt in range(self.max_retries):
        try:
            return await self._do_work(content)
        except Exception as e:
            if attempt < self.max_retries - 1:
                await asyncio.sleep(self.retry_delay * (2 ** attempt))
            else:
                raise
```

**Graceful degradation:**
```python
async def _process_single(self, content: Content) -> Content:
    try:
        result = await self._do_work(content)
        content.data["result"] = result
    except SpecificError as e:
        logger.warning(f"Non-critical error for {content.id.canonical_id}: {e}")
        content.data["result"] = None
        content.data["error"] = str(e)
    return content
```

## Testing

```python
import pytest
from contentflow.models import Content, ContentIdentifier

@pytest.mark.asyncio
async def test_my_executor():
    executor = MyExecutor(id="test", settings={"my_setting": "value"})
    content = Content(
        id=ContentIdentifier(canonical_id="test-1", unique_id="test-1"),
        data={"text": "Hello world"}
    )
    result = await executor.process_input(content, None)
    assert result.data["result"] == "expected"
```

## Existing Executor Reference

Key executor files in `contentflow-lib/contentflow/executors/`:

| File | Base Class | Purpose |
|------|-----------|---------|
| `base.py` | — | BaseExecutor with handler, settings, conditions |
| `parallel_executor.py` | BaseExecutor | ParallelExecutor with concurrency control |
| `input_executor.py` | BaseExecutor | InputExecutor with crawl/pagination |
| `azure_openai_agent_executor.py` | ParallelExecutor | AI agent processing |
| `summarization_executor.py` | AzureOpenAIAgentExecutor | Text summarization |
| `entity_extraction_executor.py` | AzureOpenAIAgentExecutor | NER extraction |
| `sentiment_analysis_executor.py` | AzureOpenAIAgentExecutor | Sentiment analysis |
| `content_classifier_executor.py` | AzureOpenAIAgentExecutor | Content classification |
| `web_scraping_executor.py` | BaseExecutor | Web scraping with Playwright |
| `pdf_extractor.py` | ParallelExecutor | PDF content extraction |
| `recursive_text_chunker_executor.py` | BaseExecutor | Text chunking |
| `azure_blob_input_discovery.py` | InputExecutor | Azure Blob crawling |
| `azure_blob_output_executor.py` | BaseExecutor | Write to Azure Blob |
| `executor_registry.py` | — | Dynamic executor loading from catalog |
| `executor_config.py` | — | Pydantic models for catalog config |

## Checklist

When creating a custom executor:
- [ ] Choose the right base class (BaseExecutor, ParallelExecutor, or InputExecutor)
- [ ] Implement required abstract methods
- [ ] Use `self.get_setting()` for all configuration with sensible defaults
- [ ] Add comprehensive docstring with configuration details
- [ ] Include proper logging with `self.debug_mode` checks
- [ ] Handle errors appropriately (retry, graceful degradation, or fail)
- [ ] Create file in `contentflow-lib/contentflow/executors/` directory
- [ ] Register in `contentflow-lib/executor_catalog.yaml` with full settings_schema
- [ ] Write unit tests
