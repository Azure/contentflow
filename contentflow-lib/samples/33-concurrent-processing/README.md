# Concurrent Processing Sample

This sample demonstrates concurrent processing of document sections.

## Features

- **ParallelExecutor**: Process document sections concurrently
- **Worker Pool Management**: Configure max workers and timeouts
- **Event Streaming**: Real-time visibility into parallel execution

## Configuration

See `concurrent_config.yaml` for the pipeline configuration.

## Usage

```bash
python concurrent_example.py
```

## Key Concepts

1. **Concurrency**: Multiple sections processed simultaneously
2. **Worker Pools**: Configurable parallelism level
3. **Timeout Management**: Prevent hanging tasks
4. **Event Tracking**: Monitor concurrent execution progress
