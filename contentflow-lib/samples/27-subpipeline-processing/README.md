# Sub-Pipeline Processing Sample

This sample demonstrates nested pipeline execution for hierarchical processing.

## Features

- **SubworkflowExecutor**: Execute pipelines within pipelines
- **Page-Level Processing**: Process each page with its own pipeline
- **Chunk-Level Processing**: Process document chunks independently
- **Hierarchical Aggregation**: Combine results across levels

## Configuration

See `subpipeline_config.yaml` for the pipeline configurations.

## Usage

```bash
python subpipeline_example.py
```

## Key Concepts

1. **Nested Pipelines**: Pipelines can invoke other pipelines
2. **Granular Processing**: Different processing levels (document → page → element)
3. **Modular Design**: Reusable sub-pipelines
4. **Result Aggregation**: Combine outputs from sub-pipelines

## Pipeline Hierarchy

```
Main Pipeline
├─ get_content
├─ extract  
├─ process_pages (SubworkflowExecutor)
│  └─ Page Pipeline
│     ├─ analyze_page
│     └─ extract_page_metadata
└─ aggregate
```

## Use Cases

- **Complex Documents**: Books, technical manuals, reports
- **Multi-Stage Processing**: Different analysis at different levels
- **Recursive Patterns**: Apply same logic at different granularities
- **Modular Composition**: Mix and match sub-pipelines
