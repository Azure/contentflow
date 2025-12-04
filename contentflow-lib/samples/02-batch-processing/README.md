# Batch Processing Sample

This sample demonstrates efficient batch processing of multiple documents.

## Features

- **BatchSplitterExecutor**: Divides documents into manageable batches
- **BatchAggregatorExecutor**: Merges results from processed batches
- **Efficient resource usage**: Process large document sets without overwhelming resources

## Configuration

See `batch_config.yaml` for the pipeline configuration.

## Usage

```bash
python batch_example.py
```

## Key Concepts

1. **Batch Size**: Controls how many documents are processed together
2. **Merge Strategy**: How results from batches are combined
3. **Scalability**: Handles large document collections efficiently
