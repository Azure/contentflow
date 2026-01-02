# Advanced Batch Processor Sample

This sample provides comprehensive demonstrations of batch processing capabilities using specialized executors.

## Features

### BatchProcessor
- **Generic batch processing** with configurable batch sizes
- **Controlled concurrency** with max_concurrent setting
- **Automatic retry** for failed items
- **Order preservation** option
- **Performance metrics** and monitoring

### FilterProcessor
- **Pre-processing filtering** to select relevant items
- **Post-processing filtering** for results
- **Multiple filter operators**: equals, not_equals, contains, greater_than, less_than
- **Duplicate removal** capability
- **Filter inversion** for negative matching

### ParallelDocumentProcessor
- **Concurrent document processing** with controlled parallelism
- **Timeout management** per document
- **Error handling** with continue-on-error option
- **Throughput optimization** for document batches

## Configuration

See `batch_processor_config.yaml` for pipeline configurations demonstrating:
- Basic batch processing
- Parallel batch processing with filtering
- Parallel document processing
- Complete multi-stage pipeline

## Usage

```bash
python batch_processor_example.py
```

## Examples Included

### 1. Basic Batch Processing
- Sequential batch processing
- Simple batching strategy
- Processing metrics

### 2. Parallel Batch Processing
- Multiple concurrent batches
- Pre-filtering records
- Duplicate removal
- Retry logic

### 3. Parallel Document Processing
- Concurrent processing of multiple documents
- Timeout handling
- Error recovery
- Performance optimization

### 4. Complete Multi-Stage Pipeline
- Data loading
- Filtering (status-based)
- Batch processing with retries
- Result filtering
- End-to-end metrics

### 5. Performance Comparison
- Sequential vs parallel benchmarking
- Speedup analysis
- Optimization recommendations

## Configuration Options

### BatchProcessor Settings

```yaml
settings:
  items_key: records           # Key containing items list
  batch_size: 20              # Items per batch
  max_concurrent: 3           # Concurrent batches
  retry_failures: true        # Enable retries
  max_retries: 2              # Max retry attempts
  preserve_order: true        # Maintain item order
```

### FilterProcessor Settings

```yaml
settings:
  items_key: records          # Key containing items
  filter_field: status        # Field to filter on
  filter_value: active        # Value to match
  filter_operator: equals     # Comparison operator
  invert: false              # Invert filter
  remove_duplicates: true    # Remove duplicates
```

### ParallelDocumentProcessor Settings

```yaml
settings:
  documents_key: documents    # Key containing documents
  max_concurrent: 10         # Concurrent documents
  timeout_secs: 60           # Timeout per document
  continue_on_error: true    # Continue on failures
```

## Performance Considerations

1. **Batch Size**: Balance between throughput and memory usage
   - Small batches: Lower memory, more overhead
   - Large batches: Higher memory, better throughput

2. **Concurrency**: Optimize based on workload
   - CPU-bound: max_concurrent ≈ CPU cores
   - I/O-bound: max_concurrent > CPU cores
   - Network-bound: Higher concurrency beneficial

3. **Retries**: Configure based on failure patterns
   - Transient errors: Enable retries
   - Permanent errors: Disable retries
   - Exponential backoff: Configure max_retries

4. **Filtering**: Reduce processing load
   - Pre-filter: Reduce items to process
   - Post-filter: Select successful results
   - Duplicate removal: Save processing time

## Use Cases

### Large Dataset Processing
```yaml
- Filter unwanted records
- Batch into manageable chunks
- Process with controlled concurrency
- Filter successful results
```

### Document Collection Processing
```yaml
- Load document batch
- Process documents in parallel
- Handle timeouts gracefully
- Aggregate results
```

### ETL Pipelines
```yaml
- Extract data
- Transform in batches
- Load with retry logic
- Validate results
```

## Best Practices

1. **Start with small batches** and increase based on performance
2. **Monitor memory usage** with large batch sizes
3. **Enable retries** for network/transient errors
4. **Use filtering** to reduce processing load
5. **Test concurrency levels** to find optimal setting
6. **Set appropriate timeouts** based on workload
7. **Handle errors gracefully** with continue_on_error

## Metrics Tracked

- Total items processed
- Successful/failed counts
- Processing duration
- Batch count
- Success rate
- Throughput (items/second)

## Error Handling

- **Retry logic**: Automatic retry for failed items
- **Error isolation**: Continue processing other batches
- **Error tracking**: Failed items logged separately
- **Timeout handling**: Prevent hanging on slow items
