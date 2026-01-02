# Conditional Routing Sample

This sample demonstrates routing documents based on their properties.

## Features

- **Conditional Edges**: Route based on document metadata
- **Type-Specific Processing**: Different executors for different document types
- **Dynamic Paths**: Pipeline path determined at runtime
- **Fallback Handling**: Handle unknown or unexpected document types

## Configuration

See `conditional_config.yaml` for the pipeline configuration.

## Usage

```bash
python conditional_example.py
```

## Key Concepts

1. **Conditional Expressions**: Use Python expressions to determine routing
2. **Metadata-Based Routing**: Make decisions based on document properties
3. **Multiple Paths**: Different processing for different document types
4. **Error Handling**: Graceful handling of unexpected document types
