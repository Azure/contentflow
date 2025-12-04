# Parallel Processing & Advanced Workflow Patterns

This guide shows how to configure complex workflow patterns in YAML, including:
- Parallel processing with subworkflows
- Fan-out/fan-in patterns
- Conditional routing
- Dynamic parallel execution

## Pattern 1: Subworkflows for Parallel Processing

### Excel Row Processing (Fan-Out Pattern)

Process each row in an Excel file through a dedicated subworkflow:

```yaml
connectors:
  - name: storage
    type: blob_storage
    settings:
      account_name: ${STORAGE_ACCOUNT}
  
  - name: ai_model
    type: ai_inference
    settings:
      endpoint: ${AI_ENDPOINT}

# Define the subworkflow for processing individual rows
subworkflows:
  - name: process_single_row
    description: Process one Excel row through validation and enrichment
    executors:
      - id: validate_row
        type: custom_ai_prompt
        settings:
          system_prompt: "You are a data validator."
          user_prompt: "Validate this row data: {row_data}. Check for required fields."
        connectors: [ai_model]
      
      - id: enrich_row
        type: custom_ai_prompt
        settings:
          system_prompt: "You are a data enricher."
          user_prompt: "Enrich this validated data: {row_data}. Add computed fields."
        connectors: [ai_model]
    
    execution_sequence: [validate_row, enrich_row]

# Main workflow that fans out to subworkflows
workflows:
  - name: excel_parallel_processing
    executors:
      - id: load_excel
        type: content_retriever
        settings:
          container_name: excel-files
        connectors: [storage]
      
      # Fan-out: Process each row in parallel
      - id: process_rows_parallel
        type: excel_row_processor
        settings:
          subworkflow: process_single_row  # Reference to subworkflow
          max_parallel: 10                  # Process 10 rows at a time
          excel_field: excel_data
          row_id_field: row_number
        connectors: []
      
      # Fan-in: Aggregate results
      - id: aggregate_results
        type: result_aggregator
        settings:
          aggregation_strategy: summarize
          include_all_results: true
        connectors: []
    
    execution_sequence: [load_excel, process_rows_parallel, aggregate_results]
```

**How it works:**
1. `load_excel` retrieves the Excel file
2. `process_rows_parallel` fans out, creating a subworkflow instance for each row
3. Each row goes through `validate_row` → `enrich_row`
4. `aggregate_results` fans in, collecting all results

## Pattern 2: Document Splitting (Fan-Out to Chunks)

Split large documents into chunks and process in parallel:

```yaml
connectors:
  - name: storage
    type: blob_storage
    settings:
      account_name: ${STORAGE_ACCOUNT}
  
  - name: doc_intelligence
    type: document_intelligence
    settings:
      endpoint: ${DOCUMENT_INTELLIGENCE_ENDPOINT}
  
  - name: ai_model
    type: ai_inference
    settings:
      endpoint: ${AI_ENDPOINT}

# Subworkflow for processing individual chunks
subworkflows:
  - name: process_chunk
    description: Extract and analyze a single document chunk
    executors:
      - id: extract_text
        type: document_intelligence_extractor
        settings:
          extract_text: true
          extract_tables: true
        connectors: [doc_intelligence]
      
      - id: analyze_chunk
        type: custom_ai_prompt
        settings:
          system_prompt: "Extract key information from this chunk."
          user_prompt: "Analyze: {content}. Find: entities, dates, amounts."
        connectors: [ai_model]
    
    execution_sequence: [extract_text, analyze_chunk]

# Main workflow
workflows:
  - name: large_document_processing
    executors:
      - id: retrieve_doc
        type: content_retriever
        connectors: [storage]
      
      # Split document into chunks
      - id: split_document
        type: document_splitter
        settings:
          split_by: pages
          chunk_size: 5  # 5 pages per chunk
        connectors: []
      
      # Fan-out: Process chunks in parallel
      - id: process_chunks_parallel
        type: chunk_processor
        settings:
          subworkflow: process_chunk
          max_parallel: 5
          chunk_field: chunks
        connectors: []
      
      # Fan-in: Merge chunk results
      - id: merge_results
        type: result_aggregator
        settings:
          aggregation_strategy: merge
          merge_field: analyzed_data
        connectors: []
    
    execution_sequence: [retrieve_doc, split_document, process_chunks_parallel, merge_results]
```

## Pattern 3: Multi-Path Fan-Out/Fan-In

Process document through multiple parallel paths, then combine:

```yaml
connectors:
  - name: storage
    type: blob_storage
    settings:
      account_name: ${STORAGE_ACCOUNT}
  
  - name: doc_intelligence
    type: document_intelligence
    settings:
      endpoint: ${DOCUMENT_INTELLIGENCE_ENDPOINT}
  
  - name: ai_model
    type: ai_inference
    settings:
      endpoint: ${AI_ENDPOINT}
  
  - name: search
    type: ai_search
    settings:
      endpoint: ${SEARCH_ENDPOINT}
      index_name: documents

workflows:
  - name: multi_path_processing
    executors:
      # Single entry point
      - id: retrieve_content
        type: content_retriever
        connectors: [storage]
      
      # Path 1: Structure extraction
      - id: extract_structure
        type: document_intelligence_extractor
        settings:
          extract_text: true
          extract_tables: true
          extract_key_value_pairs: true
        connectors: [doc_intelligence]
      
      # Path 2: AI analysis
      - id: ai_analysis
        type: custom_ai_prompt
        settings:
          system_prompt: "Analyze document structure and content."
          user_prompt: "Provide detailed analysis of: {content}"
        connectors: [ai_model]
      
      # Path 3: Metadata extraction
      - id: extract_metadata
        type: custom_ai_prompt
        settings:
          system_prompt: "Extract metadata from documents."
          user_prompt: "Extract: title, author, date, type from: {content}"
        connectors: [ai_model]
      
      # Fan-in: Combine all paths
      - id: combine_results
        type: result_combiner
        settings:
          combine_strategy: merge_fields
          wait_for_all: true
        connectors: []
      
      # Final output
      - id: index_combined
        type: ai_search_index_writer
        connectors: [search]
    
    # Edge configuration for fan-out/fan-in
    edges:
      # Fan-out from retrieve_content to 3 parallel paths
      - from: retrieve_content
        to: [extract_structure, ai_analysis, extract_metadata]
        type: parallel
      
      # Fan-in: All 3 paths converge to combine_results
      - from: [extract_structure, ai_analysis, extract_metadata]
        to: combine_results
        type: join  # Wait for all inputs
      
      # Sequential final step
      - from: combine_results
        to: index_combined
        type: sequential
```

## Pattern 4: Conditional Fan-Out

Route documents to different processing paths based on content:

```yaml
connectors:
  - name: storage
    type: blob_storage
    settings:
      account_name: ${STORAGE_ACCOUNT}
  
  - name: doc_intelligence
    type: document_intelligence
    settings:
      endpoint: ${DOCUMENT_INTELLIGENCE_ENDPOINT}
  
  - name: ai_model
    type: ai_inference
    settings:
      endpoint: ${AI_ENDPOINT}

# Subworkflows for different document types
subworkflows:
  - name: process_pdf
    description: PDF-specific processing
    executors:
      - id: extract_pdf
        type: document_intelligence_extractor
        settings:
          model_id: prebuilt-layout
        connectors: [doc_intelligence]
      
      - id: analyze_pdf
        type: custom_ai_prompt
        settings:
          system_prompt: "Analyze PDF documents."
          user_prompt: "Extract structured information from: {content}"
        connectors: [ai_model]
    execution_sequence: [extract_pdf, analyze_pdf]
  
  - name: process_image
    description: Image-specific processing
    executors:
      - id: extract_image
        type: document_intelligence_extractor
        settings:
          model_id: prebuilt-read
        connectors: [doc_intelligence]
      
      - id: describe_image
        type: custom_ai_prompt
        settings:
          system_prompt: "Describe images in detail."
          user_prompt: "Describe this image: {content}"
        connectors: [ai_model]
    execution_sequence: [extract_image, describe_image]
  
  - name: process_text
    description: Text-specific processing
    executors:
      - id: analyze_text
        type: custom_ai_prompt
        settings:
          system_prompt: "Analyze text documents."
          user_prompt: "Summarize and extract key points: {content}"
        connectors: [ai_model]
    execution_sequence: [analyze_text]

# Main workflow with conditional routing
workflows:
  - name: conditional_document_processing
    executors:
      - id: retrieve_doc
        type: content_retriever
        connectors: [storage]
      
      # Classifier determines document type
      - id: classify_type
        type: document_classifier
        settings:
          classification_field: file_type
          supported_types: [pdf, image, text]
        connectors: []
      
      # Conditional routing to subworkflows
      - id: route_by_type
        type: conditional_router
        settings:
          # Route based on classification result
          routes:
            - condition: "file_type == 'pdf'"
              subworkflow: process_pdf
            - condition: "file_type == 'image'"
              subworkflow: process_image
            - condition: "file_type == 'text'"
              subworkflow: process_text
            - condition: "default"
              subworkflow: process_text
        connectors: []
    
    execution_sequence: [retrieve_doc, classify_type, route_by_type]
```

## Pattern 5: Nested Subworkflows

Process collections with nested parallelism:

```yaml
connectors:
  - name: storage
    type: blob_storage
    settings:
      account_name: ${STORAGE_ACCOUNT}
  
  - name: doc_intelligence
    type: document_intelligence
    settings:
      endpoint: ${DOCUMENT_INTELLIGENCE_ENDPOINT}
  
  - name: ai_model
    type: ai_inference
    settings:
      endpoint: ${AI_ENDPOINT}

# Level 3: Process individual chunk
subworkflows:
  - name: process_chunk
    description: Analyze a single chunk
    executors:
      - id: extract_chunk
        type: document_intelligence_extractor
        connectors: [doc_intelligence]
      
      - id: analyze_chunk
        type: custom_ai_prompt
        settings:
          system_prompt: "Analyze chunk content."
          user_prompt: "Extract entities from: {content}"
        connectors: [ai_model]
    execution_sequence: [extract_chunk, analyze_chunk]

# Level 2: Process individual document (uses chunk subworkflow)
subworkflows:
  - name: process_document
    description: Split and process one document
    executors:
      - id: split_doc
        type: document_splitter
        settings:
          split_by: pages
          chunk_size: 3
        connectors: []
      
      - id: process_chunks
        type: chunk_processor
        settings:
          subworkflow: process_chunk  # Nested subworkflow
          max_parallel: 5
        connectors: []
      
      - id: merge_chunks
        type: result_aggregator
        connectors: []
    execution_sequence: [split_doc, process_chunks, merge_chunks]

# Level 1: Main workflow (processes batch of documents)
workflows:
  - name: batch_document_processing
    executors:
      - id: load_batch
        type: batch_loader
        settings:
          batch_size: 10
        connectors: [storage]
      
      - id: process_documents_parallel
        type: document_batch_processor
        settings:
          subworkflow: process_document  # Uses nested subworkflows
          max_parallel: 3
        connectors: []
      
      - id: aggregate_batch
        type: result_aggregator
        connectors: []
    
    execution_sequence: [load_batch, process_documents_parallel, aggregate_batch]
```

**Execution flow:**
1. Load batch (10 documents)
2. Fan-out: Process 3 documents at a time (Level 1)
   - Each document is split into chunks (Level 2)
   - Fan-out: Process 5 chunks at a time (Level 3)
     - Each chunk: extract → analyze
   - Fan-in: Merge chunk results
3. Fan-in: Aggregate all document results

## Pattern 6: Dynamic Parallel Execution

Number of parallel executions determined at runtime:

```yaml
connectors:
  - name: storage
    type: blob_storage
    settings:
      account_name: ${STORAGE_ACCOUNT}
  
  - name: ai_model
    type: ai_inference
    settings:
      endpoint: ${AI_ENDPOINT}

subworkflows:
  - name: process_item
    description: Process a single item
    executors:
      - id: analyze_item
        type: custom_ai_prompt
        settings:
          system_prompt: "Analyze data items."
          user_prompt: "Process: {item_data}"
        connectors: [ai_model]
    execution_sequence: [analyze_item]

workflows:
  - name: dynamic_parallel_processing
    executors:
      - id: load_data
        type: content_retriever
        connectors: [storage]
      
      # Dynamically determine parallelism based on data size
      - id: process_items_dynamic
        type: dynamic_parallel_processor
        settings:
          subworkflow: process_item
          # Calculate max_parallel at runtime
          max_parallel_formula: "min(item_count, 20)"  # Up to 20 parallel
          items_field: data_items
          parallelism_strategy: auto  # Auto-adjust based on load
        connectors: []
      
      - id: aggregate
        type: result_aggregator
        connectors: []
    
    execution_sequence: [load_data, process_items_dynamic, aggregate]
```

## Edge Types Reference

### Sequential Edges
```yaml
edges:
  - from: step1
    to: step2
    type: sequential  # Default if type not specified
```

### Parallel Fan-Out
```yaml
edges:
  - from: source
    to: [path1, path2, path3]
    type: parallel
    # All paths execute simultaneously
```

### Join Fan-In (Wait for All)
```yaml
edges:
  - from: [path1, path2, path3]
    to: combiner
    type: join
    wait_strategy: all  # Wait for all inputs (default)
```

### First-Complete Fan-In
```yaml
edges:
  - from: [path1, path2, path3]
    to: next_step
    type: join
    wait_strategy: first  # Continue when first completes
```

### Conditional Routing
```yaml
edges:
  - from: classifier
    to:
      - target: path_a
        condition: "category == 'A'"
      - target: path_b
        condition: "category == 'B'"
      - target: default_path
        condition: default
    type: conditional
```

## Complete Example: Multi-Pattern Workflow

Combining multiple patterns:

```yaml
connectors:
  - name: storage
    type: blob_storage
    settings:
      account_name: ${STORAGE_ACCOUNT}
  
  - name: doc_intelligence
    type: document_intelligence
    settings:
      endpoint: ${DOCUMENT_INTELLIGENCE_ENDPOINT}
  
  - name: ai_model
    type: ai_inference
    settings:
      endpoint: ${AI_ENDPOINT}
  
  - name: search
    type: ai_search
    settings:
      endpoint: ${SEARCH_ENDPOINT}
      index_name: documents

subworkflows:
  - name: extract_and_analyze
    executors:
      - id: extract
        type: document_intelligence_extractor
        connectors: [doc_intelligence]
      - id: analyze
        type: custom_ai_prompt
        settings:
          system_prompt: "Analyze documents."
          user_prompt: "Extract key information: {content}"
        connectors: [ai_model]
    execution_sequence: [extract, analyze]

workflows:
  - name: advanced_document_pipeline
    executors:
      # Stage 1: Load
      - id: load_docs
        type: batch_loader
        connectors: [storage]
      
      # Stage 2: Classify
      - id: classify
        type: document_classifier
        connectors: []
      
      # Stage 3a: Process high priority (parallel)
      - id: process_high_priority
        type: document_batch_processor
        settings:
          subworkflow: extract_and_analyze
          max_parallel: 10
          filter: "priority == 'high'"
        connectors: []
      
      # Stage 3b: Process normal priority (parallel)
      - id: process_normal
        type: document_batch_processor
        settings:
          subworkflow: extract_and_analyze
          max_parallel: 5
          filter: "priority == 'normal'"
        connectors: []
      
      # Stage 4: Combine (fan-in)
      - id: combine_processed
        type: result_combiner
        connectors: []
      
      # Stage 5: Index (parallel by batch)
      - id: index_results
        type: ai_search_index_writer
        settings:
          index_mode: chunks
          batch_size: 100
        connectors: [search]
    
    # Complex edge configuration
    edges:
      # Sequential start
      - from: load_docs
        to: classify
        type: sequential
      
      # Conditional fan-out based on priority
      - from: classify
        to:
          - target: process_high_priority
            condition: "has_high_priority_docs"
          - target: process_normal
            condition: "has_normal_priority_docs"
        type: conditional_parallel
      
      # Fan-in: Wait for all priority paths
      - from: [process_high_priority, process_normal]
        to: combine_processed
        type: join
        wait_strategy: all
      
      # Sequential end
      - from: combine_processed
        to: index_results
        type: sequential
```

## Key Configuration Settings

### Subworkflow Processor Settings

```yaml
settings:
  subworkflow: name_of_subworkflow  # Required
  max_parallel: 10                   # Max concurrent executions
  items_field: items                 # Field containing items to process
  timeout_seconds: 300               # Timeout per item
  continue_on_error: true            # Don't fail entire batch on error
  collect_results: true              # Collect all results
```

### Aggregator Settings

```yaml
settings:
  aggregation_strategy: summarize    # summarize, merge, custom
  include_all_results: true          # Include individual results
  merge_field: analyzed_data         # Field to merge
  summary_fields: [count, avg, sum]  # Summary statistics
```

### Parallelism Control

```yaml
settings:
  max_parallel: 10                   # Fixed parallelism
  # OR
  parallelism_strategy: auto         # Auto-adjust
  min_parallel: 2                    # Min concurrent
  max_parallel: 20                   # Max concurrent
  adjust_based_on: cpu_usage         # Adjustment metric
```

This comprehensive guide covers all major patterns for parallel processing and complex workflow orchestration in YAML!
