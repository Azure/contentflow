# Azure Blob Input Executor Example

This example demonstrates how to use the `AzureBlobInputExecutor` to discover and list content files from Azure Blob Storage containers.

## Overview

The Azure Blob Input Executor is a source/input executor that scans Azure Blob Storage to discover content files. It's perfect for:

- Batch processing pipelines that need to discover files
- Building file inventories
- Filtering files by type, size, date, or location
- Creating processing queues from blob storage

## Features

- **Flexible Filtering**: Filter by prefix, file extensions, folder depth, size, and modification dates
- **Sorting**: Sort results by name, size, or last modified date
- **Metadata**: Include blob metadata in output
- **Traversal Control**: Limit folder depth and result count
- **Integration**: Works seamlessly with ContentRetriever and other executors

## Prerequisites

1. **Azure Storage Account**: You need an Azure Storage Account with blob containers
2. **Authentication**: Configure Azure credentials (Default Azure Credential or Account Key)
3. **Environment Variables**:
   ```bash
   export STORAGE_ACCOUNT_NAME=mystorageaccount
   export CONTAINER_NAME=documents
   # Optional: for full pipeline
   export AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT=https://mydocint.cognitiveservices.azure.com
   ```

## Configuration Examples

### Basic Discovery

Discover all files in a container:

```yaml
- id: discover_blobs
  type: azure_blob_input
  settings:
    blob_storage_account: "${STORAGE_ACCOUNT_NAME}"
    blob_container_name: "documents"
```

### Filtered Discovery

Discover specific files with filters:

```yaml
- id: discover_blobs
  type: azure_blob_input
  settings:
    blob_storage_account: "${STORAGE_ACCOUNT_NAME}"
    blob_container_name: "documents"
    prefix: "invoices/2024/"           # Only files in this folder
    file_extensions: [".pdf", ".docx"] # Only these file types
    max_depth: 2                       # Limit folder traversal
    max_results: 100                   # Limit total results
    min_size_bytes: 1024              # Minimum 1KB
    sort_by: "last_modified"          # Sort by date
    sort_ascending: false             # Newest first
```

### Full Pipeline

Discover → Retrieve → Extract:

```yaml
pipelines:
  - name: blob_to_extraction
    executors:
      - id: discover_blobs
        type: azure_blob_input
        settings:
          blob_storage_account: "${STORAGE_ACCOUNT_NAME}"
          blob_container_name: "documents"
          file_extensions: [".pdf"]
          max_results: 10
          
      - id: retrieve_content
        type: content_retriever
        settings:
          blob_storage_account: "${STORAGE_ACCOUNT_NAME}"
          blob_container_name: "documents"
          
      - id: extract_content
        type: azure_document_intelligence_extractor
        settings:
          doc_intelligence_endpoint: "${AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT}"
```

## Running the Examples

### 1. Basic Discovery
```bash
python blob_input_example.py
# Select option 1
```

Lists all files in the configured container.

### 2. Filtered Discovery
```bash
python blob_input_example.py
# Select option 2
```

Demonstrates advanced filtering by prefix, extensions, size, etc.

### 3. Discovery with Streaming
```bash
python blob_input_example.py
# Select option 3
```

Shows real-time event streaming during discovery.

### 4. Full Pipeline
```bash
python blob_input_example.py
# Select option 4
```

Complete pipeline: discover files → retrieve content → extract with AI.

## Output Format

Each discovered blob becomes a `Content` object with:

```python
Content(
    id=ContentIdentifier(
        canonical_id="<hash>",
        source_name="blob",
        path="path/to/file.pdf"
    ),
    data={
        'blob_name': 'file.pdf',
        'blob_path': 'path/to/file.pdf',
        'container_name': 'documents',
        'storage_account': 'mystorageaccount',
        'size': 12345,
        'last_modified': datetime(...),
        'content_type': 'application/pdf',
        'metadata': {...}  # if include_metadata=True
    }
)
```

## Configuration Options

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `blob_storage_account` | string | *required* | Storage account name |
| `blob_container_name` | string | *required* | Container name |
| `blob_storage_credential_type` | string | `default_azure_credential` | Auth type |
| `prefix` | string | `""` | Path prefix filter |
| `file_extensions` | array | `[]` | File types to include |
| `max_depth` | integer | `0` | Max folder depth (0=unlimited) |
| `max_results` | integer | `0` | Max results (0=unlimited) |
| `min_size_bytes` | integer | `0` | Minimum file size |
| `max_size_bytes` | integer | `0` | Maximum file size |
| `sort_by` | string | `name` | Sort field: name, last_modified, size |
| `sort_ascending` | boolean | `true` | Sort order |
| `include_metadata` | boolean | `true` | Include blob metadata |
| `modified_after` | string | `null` | ISO date filter |
| `modified_before` | string | `null` | ISO date filter |

## Use Cases

### 1. Daily Invoice Processing
```yaml
settings:
  prefix: "invoices/2024/"
  file_extensions: [".pdf"]
  modified_after: "2024-12-01T00:00:00"
  sort_by: "last_modified"
```

### 2. Large File Processing
```yaml
settings:
  min_size_bytes: 1048576  # 1MB+
  max_results: 50
  sort_by: "size"
  sort_ascending: false  # Largest first
```

### 3. Specific Folder Depth
```yaml
settings:
  prefix: "documents/"
  max_depth: 2  # Only 2 levels deep
  file_extensions: [".docx", ".pdf"]
```

## Best Practices

1. **Use Prefixes**: Narrow down the search space with specific prefixes
2. **Limit Results**: Use `max_results` for large containers to avoid memory issues
3. **Filter Early**: Use file extensions and size filters to reduce processing
4. **Sort Strategically**: Sort by `last_modified` descending for newest-first processing
5. **Combine with Batching**: Use with batch executors for large-scale processing

## Troubleshooting

### No files discovered
- Check container name and prefix
- Verify authentication (Azure credentials)
- Review filter settings (extensions, size, dates)

### Too many results
- Use `max_results` to limit output
- Add more specific filters (prefix, extensions)
- Increase `min_size_bytes` to exclude small files

### Performance issues
- Use prefix to reduce scan scope
- Limit depth with `max_depth`
- Set reasonable `max_results`

## Integration with Other Executors

The Azure Blob Input Executor is designed to work seamlessly with:

1. **ContentRetrieverExecutor**: Download discovered files
2. **ParallelExecutor**: Process multiple files concurrently
3. **Document Intelligence**: Extract content from discovered documents
4. **Batch Processors**: Split into batches for processing

Example workflow:
```
AzureBlobInputExecutor → ContentRetrieverExecutor → AzureDocumentIntelligenceExtractorExecutor
```
