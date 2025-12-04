# Document Processing Pipeline Samples

This directory contains comprehensive examples demonstrating various pipeline patterns and capabilities.

## Prerequisites

```bash
# Set up environment
cp .env.example .env
# Edit .env with your Azure credentials

# Install dependencies
pip install -r ../requirements.txt
```

## 📁 Sample Directory

### [01-simple/](01-simple/)
**Basic pipeline configuration and execution**
- Minimal configuration
- Simple document processing  
- Event streaming
- Perfect starting point for beginners

### [02-batch-processing/](02-batch-processing/)
**Efficient batch processing of multiple documents**
- BatchSplitterExecutor usage
- BatchAggregatorExecutor for result merging
- Handling large document collections
- Resource optimization

### [03-concurrent-processing/](03-concurrent-processing/)
**Parallel processing of document sections**
- ParallelExecutor configuration
- Worker pool management
- Timeout handling
- Concurrent event tracking

### [04-conditional-routing/](04-conditional-routing/)
**Dynamic routing based on document properties**
- Conditional edges
- Type-specific processing
- Metadata-based decisions
- Fallback handling

### [05-parallel-processing/](05-parallel-processing/)
**Parallel execution paths with result merging**
- Multiple concurrent branches
- Independent task execution
- Result aggregation from parallel paths
- Performance optimization

### [06-subpipeline-processing/](06-subpipeline-processing/)
**Nested pipelines for hierarchical processing**
- SubworkflowExecutor usage
- Page-level processing
- Chunk-level processing
- Multi-level pipeline composition

## 🚀 Quick Start

1. **Choose a sample**:
   ```bash
   cd 01-simple
   ```

2. **Run the example**:
   ```bash
   python simple_example.py
   ```

## 📚 Learning Path

**Beginner** → 01-simple → 02-batch-processing

**Intermediate** → 03-concurrent-processing → 04-conditional-routing

**Advanced** → 05-parallel-processing → 06-subpipeline-processing

---

## Legacy Examples (Old Pattern)

### 1. Simple Sequential Workflow (`simple_sequential.py`)

Demonstrates basic sequential execution using existing pipeline configurations.

**Key Concepts:**
- Document classification
- Switch-case conditional routing
- Type-specific processing paths
- Default fallback handling

**Run:**
```bash
python conditional_routing.py
```

## Understanding the Examples

### Event Streaming

All examples use event streaming to observe workflow execution:

```python
from agent_framework import (
    ExecutorInvokedEvent,
    ExecutorCompletedEvent,
    WorkflowOutputEvent
)

async for event in workflow.run_stream(input_data):
    if isinstance(event, ExecutorInvokedEvent):
        print(f"Executor {event.executor_id} started")
    elif isinstance(event, ExecutorCompletedEvent):
        print(f"Executor {event.executor_id} completed")
    elif isinstance(event, WorkflowOutputEvent):
        print(f"Final output: {event.data}")
```

### Custom Executors

Examples show how to create custom document processors:

```python
from doc_proc_workflow.executors import DocumentExecutor

class MyProcessor(DocumentExecutor):
    def __init__(self):
        super().__init__(id="my_processor")
    
    async def process_document(self, document, ctx):
        # Your processing logic
        document.summary_data["processed"] = True
        return document
```

### Workflow Patterns

**Sequential:**
```python
workflow = (
    WorkflowBuilder()
    .add_edge(step1, step2)
    .add_edge(step2, step3)
    .set_start_executor(step1)
    .build()
)
```

**Concurrent:**
```python
workflow = (
    ConcurrentBuilder()
    .participants([proc1, proc2, proc3])
    .build()
)
```

**Conditional:**
```python
workflow = (
    WorkflowBuilder()
    .add_switch_case_edge_group(
        classifier,
        [
            Case(condition=lambda x: x.type == "pdf", target=pdf_proc),
            Case(condition=lambda x: x.type == "image", target=img_proc),
            Default(target=default_proc)
        ]
    )
    .build()
)
```

## Next Steps

- Explore the [Agent Framework documentation](https://github.com/microsoft/agent-framework)
- Review [workflow samples](https://github.com/microsoft/agent-framework/tree/main/python/samples/getting_started/workflows)
- Check out advanced patterns like:
  - Loops and iterations
  - Human-in-the-loop
  - Checkpointing and resume
  - Sub-workflows
  - State management

## Troubleshooting

**ImportError: agent_framework not found**
```bash
pip install agent-framework-azure-ai --pre
```

**Configuration files not found**
Ensure you're running from the examples directory and that doc-proc-lib configuration files exist.

**Module import errors**
Make sure doc-proc-lib is in your Python path or installed.
