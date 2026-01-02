# Parallel Processing Sample

This sample demonstrates parallel execution of independent processing branches.

## Features

- **Parallel Branches**: Multiple independent execution paths
- **Concurrent Execution**: Process different aspects simultaneously
- **Result Merging**: Combine outputs from parallel branches
- **Performance Optimization**: Reduce total processing time

## Configuration

See `parallel_config.yaml` for the pipeline configuration.

## Usage

```bash
python parallel_example.py
```

## Key Concepts

1. **Parallel Edges**: Define multiple targets from a single source
2. **Independent Branches**: Each path processes independently
3. **Merge Point**: Combine results from all parallel paths
4. **Concurrency Benefits**: Faster processing for independent tasks

## Pipeline Flow

```
get_content → extract → ┬─→ extract_metadata ─┐
                        ├─→ extract_entities  ─┼→ merge_results
                        └─→ extract_summary   ─┘
```
