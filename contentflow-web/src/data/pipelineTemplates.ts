import { PipelineTemplate } from "@/types/pipeline";
import yaml from "js-yaml";
import type { PipelineYamlFormat } from "@/lib/pipelineYamlConverter";

// Helper function to create pipeline from YAML
function createPipelineFromYaml(yamlString: string): { nodes: any[]; edges: any[] } {
  const data = yaml.load(yamlString) as PipelineYamlFormat;
  const { pipeline } = data;

  // Convert executors to nodes (simplified for template purposes)
  const nodes = (pipeline.executors || []).map((executor) => ({
    id: executor.id,
    type: executor.type === "subpipeline" ? "subpipeline" : "executor",
    position: executor.position || { x: 0, y: 0 },
    data: {
      label: executor.name,
      executor: {
        id: executor.type,
        type: executor.type,
        name: executor.name,
      },
      config: {
        name: executor.name,
        description: executor.description || "",
        settings: executor.settings || {},
      },
    },
  }));

  // Convert edges
  const edges: any[] = [];
  const edgeMap = new Map<string, boolean>();

  (pipeline.edges || []).forEach((edgeDef, index) => {
    const from = edgeDef.from;
    const to = edgeDef.to;

    // Handle parallel edges: from -> [to1, to2, to3]
    if (typeof from === "string" && Array.isArray(to)) {
      to.forEach((target) => {
        const edgeKey = `${from}->${target}`;
        if (!edgeMap.has(edgeKey)) {
          edges.push({
            id: `${from}-${target}`,
            source: from,
            target: target,
          });
          edgeMap.set(edgeKey, true);
        }
      });
    }
    // Handle join edges: [from1, from2] -> to
    else if (Array.isArray(from) && typeof to === "string") {
      from.forEach((source) => {
        const edgeKey = `${source}->${to}`;
        if (!edgeMap.has(edgeKey)) {
          edges.push({
            id: `${source}-${to}`,
            source: source,
            target: to,
          });
          edgeMap.set(edgeKey, true);
        }
      });
    }
    // Handle sequential edge: from -> to
    else if (typeof from === "string" && typeof to === "string") {
      const edgeKey = `${from}->${to}`;
      if (!edgeMap.has(edgeKey)) {
        edges.push({
          id: `${from}-${to}`,
          source: from,
          target: to,
        });
        edgeMap.set(edgeKey, true);
      }
    }
  });

  return { nodes, edges };
}

// Template 1: PDF Document Extraction with Azure Document Intelligence
const pdfExtractionYaml = `
pipeline:
  name: "PDF Document Extraction"
  description: "Extract text, tables, and images from PDF documents using Azure Document Intelligence"
  executors:
    - id: blob-discovery-1
      name: "Azure Blob Input Discovery"
      type: azure_blob_input_discovery
      position: { x: 250, y: 50 }
      description: "Discover PDF files from Azure Blob Storage"
      settings:
        file_extensions: ".pdf"
        blob_container_name: "content"
        max_depth: 3
        max_results: 25

    - id: blob-content-retrieval-1
      name: "Azure Blob Content Retrieval"
      type: azure_blob_content_retriever
      position: { x: 250, y: 200 }
      description: "Retrieve files from Azure Blob Storage"
      settings:
        use_temp_file_for_content: true
        
    - id: doc-intel-1
      name: "Document Intelligence"
      type: azure_document_intelligence_extractor
      position: { x: 250, y: 350 }
      description: "Extract content using Azure Document Intelligence"
      settings:
        model_id: "prebuilt-layout"
        output_format: "markdown"
        
    - id: chunker-1
      name: "Smart Chunking"
      type: recursive_text_chunker
      position: { x: 250, y: 500 }
      description: "Split text into semantic chunks"
      settings:
        chunk_size: 1000
        chunk_overlap: 200
        input_field: doc_intell_output.text
        output_field: chunks
        
    - id: blob-output-1
      name: "Save Results"
      type: azure_blob_output
      position: { x: 250, y: 650 }
      description: "Save extracted content to blob storage"
      
  edges:
    - from: blob-discovery-1
      to: blob-content-retrieval-1
      type: sequential
    - from: blob-content-retrieval-1
      to: doc-intel-1
      type: sequential
    - from: doc-intel-1
      to: chunker-1
      type: sequential
    - from: chunker-1
      to: blob-output-1
      type: sequential
`;

// Template 2: Article Summarization with AI
const articleSummarizationYaml = `
pipeline:
  name: "Article Summarization"
  description: "Automatically summarize articles and extract key points using AI"
  executors:
    - id: blob-discovery-1
      name: "Discover Articles"
      type: azure_blob_input_discovery
      position: { x: 250, y: 50 }
      description: "Discover article documents from Azure Blob Storage"
      settings:
        file_extensions: ".pdf,.docx,.txt"
        max_depth: 1
        max_results: 5
        blob_container_name: "content"
    
    - id: blob-content-retrieval-1
      name: "Retrieve Articles"
      type: azure_blob_content_retriever
      position: { x: 250, y: 200 }
      description: "Retrieve articles from Azure Blob Storage"
      settings:
        use_temp_file_for_content: true
        
    - id: content-understanding-1
      name: "Content Extraction"
      type: azure_content_understanding_extractor
      position: { x: 250, y: 350 }
      description: "Extract content with Azure Content Understanding"
      settings:
        analyzer_id: "prebuilt-documentSearch"
        output_content_format: "markdown"
        output_field: content_understanding_result
        content_understanding_endpoint: "https://<foundry-resource>.services.ai.azure.com/"
        content_understanding_model_mappings: |
          {"gpt-4.1":"gpt-4.1","gpt-4.1-mini":"gpt-4.1-mini","text-embedding-3-large":"text-embedding-3-large"}
    
    - id: field_mapper-1
      name: Content Understanding Output Mapper
      type: field_mapper
      position: { x: 250, y: 500 }
      description: Rename, move, and remap fields within Content items for standardization and compatibility
      settings:
        enabled: true
        fail_pipeline_on_error: true
        debug_mode: false
        mappings: |-
          {
          "content_understanding_result.result.contents.markdown": "markdown"
          }
        object_mappings: ''
        copy_mode: copy
        create_nested: false
        overwrite_existing: true
        template_fields: true
        nested_delimiter: .
        list_handling: concatenate
        join_separator: '---'
        merge_filter_empty: true

    - id: summarizer-1
      name: "AI Summarization"
      type: text_summarizer
      position: { x: 110, y: 650 }
      description: "Generate concise summary"
      settings:
        summary_length: "medium"
        summary_style: "bullet_points"
        endpoint: "https://<foundry-resource>.openai.azure.com/openai/v1/"
        deployment_name: "gpt-4.1-mini"
        input_field: "markdown"
        output_field: "summary"
        
    - id: entity-1
      name: "Key Points Extraction"
      type: entity_extractor
      position: { x: 400, y: 650 }
      description: "Extract main entities and concepts"
      settings:
        entity_types: "person, organization, location, concept, event"
        endpoint: "https://<foundry-resource>.openai.azure.com/openai/v1/"
        deployment_name: "gpt-4.1-mini"
        input_field: "markdown"
        output_field: "entities"

    - id: "fan_in_aggregator-1"
      name: "Results Aggregator"
      type: "fan_in_aggregator"
      position: { x: 250, y: 850 }
      description: |
        "Aggregate results from multiple parallel branches by merging content items based on canonical 
        IDs. Must always be used as the joining executor after parallel (fan-out) execution branches."
      settings:
        enabled: true
        fail_pipeline_on_error: true
        debug_mode: false
        
    - id: blob-output-1
      name: "Save Results"
      type: azure_blob_output
      position: { x: 250, y: 1000 }
      description: "Save summaries and entities"
      
  edges:
    - from: blob-discovery-1
      to: blob-content-retrieval-1
      type: sequential
    - from: blob-content-retrieval-1
      to: content-understanding-1
      type: sequential
    - from: content-understanding-1
      to: field_mapper-1
      type: sequential
    - from: field_mapper-1
      to: [entity-1, summarizer-1]
      type: parallel
    - from: [summarizer-1, entity-1]
      to: fan_in_aggregator-1
      type: join
      wait_strategy: all
    - from: fan_in_aggregator-1
      to: blob-output-1
      type: sequential
`;

// Template 3: Entity & Knowledge Mapping
const entityMappingYaml = `
pipeline:
  name: "Entity & Knowledge Mapping"
  description: "Extract entities and build knowledge graphs with relationship detection"
  executors:
    - id: blob-discovery-1
      name: "Discover Content"
      type: azure_blob_input_discovery
      position: { x: 250, y: 50 }
      description: "Discover documents from Azure Blob Storage"
      settings:
        file_extensions: ".pdf,.docx"
        blob_container_name: "content"
        max_depth: 1
        max_results: 5
    
    - id: blob-content-retrieval-1
      name: "Retrieve Content"
      type: azure_blob_content_retriever
      position: { x: 250, y: 200 }
      description: "Retrieve content from Azure Blob Storage"
      settings:
        use_temp_file_for_content: true

    - id: content-understanding-1
      name: "Content Extraction"
      type: azure_content_understanding_extractor
      position: { x: 250, y: 350 }
      description: "Extract content with Azure Content Understanding"
      settings:
        analyzer_id: "prebuilt-documentSearch"
        output_content_format: "markdown"
        output_field: content_understanding_result
        content_understanding_endpoint: "https://<foundry-resource>.services.ai.azure.com/"
        content_understanding_model_mappings: |
          {"gpt-4.1":"gpt-4.1","gpt-4.1-mini":"gpt-4.1-mini","text-embedding-3-large":"text-embedding-3-large"}
    
    - id: field_mapper-1
      name: Content Understanding Output Mapper
      type: field_mapper
      position: { x: 250, y: 500 }
      description: Rename, move, and remap fields within Content items for standardization and compatibility
      settings:
        enabled: true
        fail_pipeline_on_error: true
        debug_mode: false
        mappings: |-
          {
          "content_understanding_result.result.contents.markdown": "markdown"
          }
        object_mappings: ''
        copy_mode: copy
        create_nested: false
        overwrite_existing: true
        template_fields: true
        nested_delimiter: .
        list_handling: concatenate
        join_separator: '---'
        merge_filter_empty: true
        
    - id: entity-1
      name: "Entity Extraction"
      type: entity_extractor
      position: { x: 250, y: 650 }
      description: "Identify entities and relationships"
      settings:
        entity_types: "person, organization, location, concept, event"
        include_context: true
        endpoint: "https://<foundry-resource>.openai.azure.com/openai/v1/"
        deployment_name: "gpt-4.1-mini"
        input_field: "markdown"
        output_field: "entities"
        
    - id: blob-output-1
      name: "Write to Blob Storage"
      type: azure_blob_output
      position: { x: 250, y: 800 }
      description: "Save entities and knowledge graph data"
      
  edges:
    - from: blob-discovery-1
      to: blob-content-retrieval-1
      type: sequential
    - from: blob-content-retrieval-1
      to: content-understanding-1
      type: sequential
    - from: content-understanding-1
      to: field_mapper-1
      type: sequential
    - from: field_mapper-1
      to: entity-1
      type: sequential
    - from: entity-1
      to: blob-output-1
      type: sequential
`;

// // Template 4: Email Content Analysis
// const emailAnalysisYaml = `
// pipeline:
//   name: "Email Content Analysis"
//   description: "Analyze email threads to extract action items and sentiment"
//   executors:
//     - id: blob-input-1
//       name: "Email Source"
//       type: azure_blob_input
//       position: { x: 250, y: 50 }
//       description: "Load email files"
//       settings:
//         file_extensions: ".eml,.msg,.txt"
        
//     - id: word-extractor-1
//       name: "Email Parser"
//       type: word_extractor
//       position: { x: 250, y: 200 }
//       description: "Parse email structure and content"
      
//     - id: sentiment-1
//       name: "Sentiment Analysis"
//       type: sentiment_analyser
//       position: { x: 250, y: 350 }
//       description: "Detect tone and emotions"
//       settings:
//         detect_emotions: true
        
//     - id: entity-1
//       name: "Action Items Extraction"
//       type: entity_extractor
//       position: { x: 250, y: 500 }
//       description: "Extract tasks and deadlines"
//       settings:
//         entity_types: ["ACTION_ITEM", "DATE", "PERSON"]
        
//     - id: classifier-1
//       name: "Email Categorization"
//       type: content_classifier
//       position: { x: 250, y: 650 }
//       description: "Classify and prioritize emails"
//       settings:
//         categories: ["urgent", "important", "routine", "informational"]
        
//     - id: blob-output-1
//       name: "Save Analysis"
//       type: azure_blob_output
//       position: { x: 500, y: 650 }
//       description: "Save analysis results"
      
//   edges:
//     - from: blob-input-1
//       to: word-extractor-1
//       type: sequential
//     - from: word-extractor-1
//       to: sentiment-1
//       type: sequential
//     - from: sentiment-1
//       to: entity-1
//       type: sequential
//     - from: entity-1
//       to: classifier-1
//       type: sequential
//     - from: classifier-1
//       to: blob-output-1
//       type: sequential
// `;

// Template 5: Image Content Extraction & Analysis
const imageAnalysisYaml = `
pipeline:
  name: "Image & Visual Content Analysis"
  description: "Demonstrates text extraction from images and analyzing of visual content using Azure Document Intelligence and Azure Content Understanding"
  executors:
    - id: blob-discovery-1
      name: "Discover Images"
      type: azure_blob_input_discovery
      position: { x: 250, y: 50 }
      description: "Discover images from Azure Blob Storage"
      settings:
        file_extensions: ".jpg,.jpeg,.png,.tiff"
        blob_container_name: "content"
        max_depth: 1
        max_results: 5
    
    - id: blob-content-retrieval-1
      name: "Retrieve Content"
      type: azure_blob_content_retriever
      position: { x: 250, y: 200 }
      description: "Retrieve content from Azure Blob Storage"
      settings:
        use_temp_file_for_content: true
        
    - id: doc-intel-1
      name: "OCR Processing using Azure Document Intelligence"
      type: azure_document_intelligence_extractor
      position: { x: 100, y: 350 }
      description: "Extract text from images"
      settings:
        model_id: "prebuilt-read"
        doc_intelligence_endpoint: "https://<foundry-resource>.cognitiveservices.azure.com/"
        
    - id: content-understanding-1
      name: "Visual Analysis using Azure Content Understanding"
      type: azure_content_understanding_extractor
      position: { x: 400, y: 350 }
      description: "Analyze visual content"
      settings:
        analyzer_id: "prebuilt-layout"
        output_content_format: "markdown"
        output_field: content_understanding_result
        content_understanding_endpoint: "https://<foundry-resource>.services.ai.azure.com/"
        content_understanding_model_mappings: |
          {"gpt-4.1":"gpt-4.1","gpt-4.1-mini":"gpt-4.1-mini","text-embedding-3-large":"text-embedding-3-large"}
        
    - id: "fan_in_aggregator-1"
      name: "Results Aggregator"
      type: "fan_in_aggregator"
      position: { x: 250, y: 500 }
      description: |
        "Aggregate results from multiple parallel branches by merging content items based on canonical 
        IDs. Must always be used as the joining executor after parallel (fan-out) execution branches."
      settings:
        enabled: true
        fail_pipeline_on_error: true
        debug_mode: false
      
    - id: blob-output-1
      name: "Save Results"
      type: azure_blob_output
      position: { x: 250, y: 650 }
      description: "Save extracted content and metadata"
      
  edges:
    - from: blob-discovery-1
      to: blob-content-retrieval-1
      type: sequential
    - from: blob-content-retrieval-1
      to: [doc-intel-1, content-understanding-1]
      type: parallel
    - from: [doc-intel-1, content-understanding-1]
      to: fan_in_aggregator-1
      type: join
      wait_strategy: all
    - from: fan_in_aggregator-1
      to: blob-output-1
      type: sequential
`;

// Template: GPT-RAG Document Ingestion
const ragIngestionYaml = `
pipeline:
  name: "GPT-RAG Document Ingestion"
  description: "Enterprise RAG pipeline with intelligent chunking and embedding generation"
  executors:
    - id: blob-discovery-1
      name: Discover Documents
      type: azure_blob_input_discovery
      position: { x: 0, y: 50 }
      description: Scan for various document from blob storage
      settings:
        blob_container_name: content
        file_extensions: ".pdf,.docx,.pptx,.xlsx,.jpg,.png"
        max_results: 0
        batch_size: 2
        include_metadata: true
  
    - id: blob-content-retrieval-1
      name: "Retrieve Content"
      type: azure_blob_content_retriever
      position: { x: 300, y: 50 }
      description: "Retrieve content from Azure Blob Storage"
      settings:
        use_temp_file_for_content: true
        
    - id: content-understanding-1
      name: "Azure Content Understanding Analysis"
      type: azure_content_understanding_extractor
      position: { x: 550, y: 50 }
      description: "Analyze visual content"
      settings:
        analyzer_id: "prebuilt-layout"
        output_content_format: "markdown"
        output_field: content_understanding_result
        content_understanding_endpoint: "https://<foundry-resource>.services.ai.azure.com/"
        content_understanding_model_mappings: |
          {"gpt-4.1":"gpt-4.1","gpt-4.1-mini":"gpt-4.1-mini","text-embedding-3-large":"text-embedding-3-large"}
          
    - id: field_mapper-non-pdf
      name: Non-PDF Field Mapper
      type: field_mapper
      position: { x: 300, y: 250 }
      description: Map extracted fields to unified structure
      settings:
        condition: id.metadata.content_type != "application/pdf"
        mappings: |-
          {
            "content_understanding_result.result.contents.markdown": "markdown"
          }
        copy_mode: copy
        create_nested: true
        overwrite_existing: true
        template_fields: true
        nested_delimiter: .
        list_handling: concatenate
        join_separator: '--'
        fail_on_missing_source: false
        remove_empty_objects: true

    - id: field_mapper-pdf
      name: PDF Field Mapper
      type: field_mapper
      position: { x: 550, y: 250 }
      description: Rename, move, and remap fields within Content items for standardization and compatibility
      settings:
        condition: id.metadata.content_type == "application/pdf"
        object_mappings: |-
          {
               "chunks": {
                        "chunk_index": "content_understanding_result.result.contents.pages.pageNumber",
                        "page_number": "content_understanding_result.result.contents.pages.pageNumber",
                        "text": "content_understanding_result.result.contents.pages.lines.content"
               }
          }
        copy_mode: copy
        create_nested: true
        overwrite_existing: true
        template_fields: true
        nested_delimiter: .
        list_handling: concatenate
        join_separator: '--'
        merge_filter_empty: true
        fail_on_missing_source: false
        remove_empty_objects: false

    - id: recursive_text_chunker-1
      name: Recursive Text Chunker
      type: recursive_text_chunker
      position: { x: 300, y: 450 }
      description: Creates chunks using recursive text splitting with configurable separator hierarchy for optimal RAG retrieval
      settings:
        condition: id.metadata.content_type != "application/pdf"
        input_field: markdown
        output_field: chunks
        chunk_size: 1000
        chunk_overlap: 200
        separators: |-


          ,
          ,.
        min_chunk_size: 100
        add_metadata: true
        include_page_numbers: true
        max_concurrent: 3
        continue_on_error: true
    
    - id: fan_in_aggregator-1
      name: Result Aggregator
      type: fan_in_aggregator
      position: { x: 550, y: 500 }
      description: |
        "Aggregate results from multiple parallel branches by merging content items based on canonical 
        IDs. Must always be used as the joining executor after parallel (fan-out) execution branches."
      settings:

    - id: field_mapper-3
      name: ID Fields Mapper
      type: field_mapper
      position: { x: 800, y: 500 }
      description: Rename, move, and remap fields within Content items for standardization and compatibility
      settings:
        fail_pipeline_on_error: false
        source_id_mappings: |-
          {
          "unique_id": "id.unique_id",
          "url": "id.canonical_id",
          "parent_id": "/{id.container}/{id.path}",
          "metadata_storage_path": "/{id.container}/{id.path}",
          "metadata_storage_name": "{id.filename}",
          "metadata_storage_last_modified": "{id.metadata.last_modified}",
          "metadata_security_id": "[]",
          "source": "blob"
          }
        copy_mode: copy
        create_nested: true
        overwrite_existing: true
        template_fields: true
        nested_delimiter: .
        list_handling: concatenate
        join_separator: '---'
        fail_on_missing_source: false

    - id: gptrag_search_index_document_generator-1
      name: GPT-RAG Search Index Document Generator
      type: gptrag_search_index_document_generator
      position: {x: 800, y: 650 }
      description: Transform Content items into Azure AI Search indexable documents following the GPT-RAG index schema.
      settings:
        enabled: true
        condition: ''
        fail_pipeline_on_error: true
        debug_mode: false
        chunk_field: chunks
        content_field: text
        max_chunk_size: 32766
        extract_title: true
        title_field: ''
        max_title_length: 50
        category_field: ''
        default_category: document
        summary_field: summary
        source_value: ''
        related_images_field: ''
        related_files_field: ''
        id_prefix: ''
        parent_id_field: ''
        url_field: ''
        output_field: search_documents
        add_output_metadata: true

    - id: ai_search_index_output-1
      name: AI Search Index Output
      type: ai_search_index_output
      position: { x: 800, y: 800 }
      description: Indexes documents or chunks to Azure AI Search
      settings:
        enabled: true
        condition: ''
        fail_pipeline_on_error: true
        debug_mode: false
        ai_search_account: <enterprise-search-service-name>
        ai_search_credential_type: default_azure_credential
        ai_search_api_key: ''
        ai_search_api_version: 2025-11-01-preview
        ai_search_index: <gpt-rag-index-name>
        index_mode: chunks
        chunk_iterator_field: search_documents
        content_to_index_mappings: |-
          { "id": "id",
            "parent_id": "parent_id",
            "metadata_storage_path": "metadata_storage_path",
            "metadata_storage_name": "metadata_storage_name",
            "metadata_storage_last_modified": "metadata_storage_last_modified",
            "metadata_security_group_ids": "metadata_security_group_ids",
            "metadata_security_user_ids": "metadata_security_user_ids",
            "metadata_security_rbac_scope": "metadata_security_rbac_scope",
            "chunk_id": "chunk_id",
            "content": "content",
            "imageCaptions": "imageCaptions",
            "page": "page",
            "offset": "offset",
            "length": "length",
            "title": "title",
            "category": "category",
            "filepath": "filepath",
            "url": "url",
            "summary": "summary",
            "relatedImages": "relatedImages",
            "relatedFiles": "relatedFiles",
            "source": "source"
          }
        index_action_type: mergeOrUpload
        batch_size: 100
        max_retries: 3
        retry_delay: 1
        max_concurrent: 3
        timeout_secs: 30
        continue_on_error: true

    - id: blob-output-1
      name: "Save Results to Blob"
      type: azure_blob_output
      position: { x: 800, y: 950 }
      description: "Save processed content"
      
  edges:
    - from: blob-discovery-1
      to: blob-content-retrieval-1
      type: sequential
    - from: blob-content-retrieval-1
      to: content-understanding-1
      type: sequential
    - from: content-understanding-1
      to:
        - field_mapper-non-pdf
        - field_mapper-pdf
      type: parallel
    - from: field_mapper-non-pdf
      to: recursive_text_chunker-1
      type: sequential
    - from:
        - field_mapper-pdf
        - recursive_text_chunker-1
      to: fan_in_aggregator-1
      type: join
      wait_strategy: all
    - from: fan_in_aggregator-1
      to: field_mapper-3
      type: sequential
    - from: field_mapper-3
      to: gptrag_search_index_document_generator-1
      type: sequential
    - from: gptrag_search_index_document_generator-1
      to: ai_search_index_output-1
      type: sequential
    - from: ai_search_index_output-1
      to: blob-output-1
      type: sequential
`;

// Template: Multi-Format Document Processing
const multiFormatPyLibsYaml = `
pipeline:
  name: "Multi-Format Document Processing using Python Libraries"
  description: "Process multiple document formats in parallel with format-specific extractors."
  executors:
    - id: blob-discovery-1
      name: "Discover Documents"
      type: azure_blob_input_discovery
      position: { x: 250, y: 50 }
      description: "Scan for various document types"
      settings:
        file_extensions: ".pdf,.docx,.pptx,.xlsx"
        blob_container_name: "content"
        max_depth: 1
        max_results: 5
    
    - id: blob-content-retrieval-1
      name: "Retrieve Content"
      type: azure_blob_content_retriever
      position: { x: 250, y: 200 }
      description: "Retrieve content from Azure Blob Storage"
      settings:
        use_temp_file_for_content: true
        
    - id: pdf-extractor-1
      name: "PDF Extraction"
      type: pdf_extractor
      position: { x: -50, y: 350 }
      description: "Extract from PDF documents using pymupdf"
      settings:
        extract_images: false
        extract_tables: true
        
    - id: word-extractor-1
      name: "Word Extraction"
      type: word_extractor
      position: { x: 200, y: 350 }
      description: "Extract from Word documents using python-docx"
      settings:
        extract_tables: true
        extract_properties: true
        extract_images: false
        
    - id: ppt-extractor-1
      name: "PowerPoint Extraction"
      type: powerpoint_extractor
      position: { x: 450, y: 350 }
      description: "Extract from presentations using python-pptx"
      settings:
        extract_slides: true
        extract_notes: true
        extract_images: false
        
    - id: excel-extractor-1
      name: "Excel Extraction"
      type: excel_extractor
      position: { x: 700, y: 350 }
      description: "Extract from spreadsheets using openpyxl"
      settings:
        extract_sheets: true
        extract_formulas: true
        extract_images: false
    
    - id: "fan_in_aggregator-1"
      name: "Results Aggregator"
      type: "fan_in_aggregator"
      position: { x: 250, y: 500 }
      description: "Aggregate results from the parallel branches above and merge content items based on canonical IDs"
      settings:
        enabled: true
        fail_pipeline_on_error: true
        debug_mode: false

    - id: field_mapper-1
      name: Field Mapper
      type: field_mapper
      position: { x: 250, y: 650 }
      description: "Map extracted fields to unified structure"
      settings:
        enabled: true
        fail_pipeline_on_error: true
        debug_mode: false
        mappings: |-
          {
           "pdf_output.text": "text",
           "word_output.text": "text",
           "pptx_output.text": "text",
           "excel_output.text": "text"
          }
        object_mappings: ''
        copy_mode: copy
        create_nested: false
        overwrite_existing: true
        template_fields: true
        nested_delimiter: .
        list_handling: concatenate
        join_separator: '---'
        merge_filter_empty: true
        merge_deduplicate: false
        case_transform: ''
        fail_on_missing_source: false
        remove_empty_objects: true
      
    - id: chunker-1
      name: "Unified Chunking"
      type: recursive_text_chunker
      position: { x: 250, y: 800 }
      description: "Chunk all extracted content"
      settings:
        chunk_size: 1000
        chunk_overlap: 200
        input_field: text
        output_field: chunks
        
    - id: blob-output-1
      name: "Save Results to Blob"
      type: azure_blob_output
      position: { x: 250, y: 950 }
      description: "Save processed content"
      
  edges:
    - from: blob-discovery-1
      to: blob-content-retrieval-1
      type: sequential
    - from: blob-content-retrieval-1
      to: [pdf-extractor-1, word-extractor-1, ppt-extractor-1, excel-extractor-1]
      type: parallel
    - from: [pdf-extractor-1, word-extractor-1, ppt-extractor-1, excel-extractor-1]
      to: fan_in_aggregator-1
      type: join
      wait_strategy: all
    - from: fan_in_aggregator-1
      to: field_mapper-1
      type: sequential
    - from: field_mapper-1
      to: chunker-1
      type: sequential
    - from: chunker-1
      to: blob-output-1
      type: sequential
`;

// Template: Multi-Format Document Processing using Azure Document Intelligence
const multiFormatDocIntelligenceYaml  = `
pipeline:
  name: "Multi-Format Document Processing using Azure Document Intelligence"
  description: "Process multiple document formats using Azure Document Intelligence extractor."
  executors:
    - id: blob-discovery-1
      name: "Discover Documents"
      type: azure_blob_input_discovery
      position: { x: 250, y: 50 }
      description: "Scan for various document types"
      settings:
        file_extensions: ".pdf,.docx,.pptx,.xlsx,.png,.jpg,.jpeg,.tiff"
        blob_container_name: "content"
        max_depth: 1
        batch_size: 3
        max_results: 5
    
    - id: blob-content-retrieval-1
      name: "Retrieve Content"
      type: azure_blob_content_retriever
      position: { x: 250, y: 200 }
      description: "Retrieve content from Azure Blob Storage"
      settings:
        use_temp_file_for_content: true
        
    - id: doc-intel-1
      name: "Processing using Azure Document Intelligence"
      type: azure_document_intelligence_extractor
      position: { x: 250, y: 350 }
      description: "Extract text from documents of various formats"
      settings:
        model_id: "prebuilt-layout"
        doc_intelligence_endpoint: "https://<foundry-resource>.cognitiveservices.azure.com/"

    - id: field_mapper-1
      name: Field Mapper
      type: field_mapper
      position: { x: 250, y: 500 }
      description: "Map extracted fields to unified structure"
      settings:
        enabled: true
        fail_pipeline_on_error: true
        debug_mode: false
        mappings: |-
          {
           "pdf_output.text": "text",
           "word_output.text": "text",
           "pptx_output.text": "text",
           "excel_output.text": "text"
          }
        object_mappings: ''
        copy_mode: copy
        create_nested: false
        overwrite_existing: true
        template_fields: true
        nested_delimiter: .
        list_handling: concatenate
        join_separator: '---'
        merge_filter_empty: true
        merge_deduplicate: false
        case_transform: ''
        fail_on_missing_source: false
        remove_empty_objects: true
        
    - id: blob-output-1
      name: "Save Results to Blob"
      type: azure_blob_output
      position: { x: 250, y: 650 }
      description: "Save processed content"
      
  edges:
    - from: blob-discovery-1
      to: blob-content-retrieval-1
      type: sequential
    - from: blob-content-retrieval-1
      to: doc-intel-1
      type: sequential
    - from: doc-intel-1
      to: field_mapper-1
      type: sequential
    - from: field_mapper-1
      to: blob-output-1
      type: sequential
`;


// Template 9: Multi-Format Document Processing using Azure Content Understanding
const multiFormatContentUnderstandingYaml  = `
pipeline:
  name: "Multi-Format Document Processing using Azure Content Understanding"
  description: "Process multiple document formats using Azure Content Understanding extractor."
  executors:
    - id: blob-discovery-1
      name: "Discover Documents"
      type: azure_blob_input_discovery
      position: { x: 250, y: 50 }
      description: "Scan for various document types"
      settings:
        file_extensions: ".pdf,.docx,.pptx,.xlsx,.png,.jpg,.jpeg,.tiff"
        blob_container_name: "content"
        max_depth: 1
        batch_size: 3
        max_results: 5
    
    - id: blob-content-retrieval-1
      name: "Retrieve Content"
      type: azure_blob_content_retriever
      position: { x: 250, y: 200 }
      description: "Retrieve content from Azure Blob Storage"
      settings:
        use_temp_file_for_content: true
        
    - id: content-understanding-1
      name: "Content Extraction"
      type: azure_content_understanding_extractor
      position: { x: 250, y: 350 }
      description: "Extract content with Azure Content Understanding"
      settings:
        analyzer_id: "prebuilt-documentSearch"
        output_content_format: "markdown"
        output_field: content_understanding_result
        content_understanding_endpoint: "https://<foundry-resource>.services.ai.azure.com/"
        content_understanding_model_mappings: |
          {"gpt-4.1":"gpt-4.1","gpt-4.1-mini":"gpt-4.1-mini","text-embedding-3-large":"text-embedding-3-large"}

    - id: field_mapper-1
      name: Field Mapper
      type: field_mapper
      position: { x: 250, y: 500 }
      description: "Map extracted fields to unified structure"
      settings:
        enabled: true
        fail_pipeline_on_error: true
        debug_mode: false
        mappings: |-
          {
           "pdf_output.text": "text",
           "word_output.text": "text",
           "pptx_output.text": "text",
           "excel_output.text": "text"
          }
        object_mappings: ''
        copy_mode: copy
        create_nested: false
        overwrite_existing: true
        template_fields: true
        nested_delimiter: .
        list_handling: concatenate
        join_separator: '---'
        merge_filter_empty: true
        merge_deduplicate: false
        case_transform: ''
        fail_on_missing_source: false
        remove_empty_objects: true
        
    - id: blob-output-1
      name: "Save Results to Blob"
      type: azure_blob_output
      position: { x: 250, y: 650 }
      description: "Save processed content"
      
  edges:
    - from: blob-discovery-1
      to: blob-content-retrieval-1
      type: sequential
    - from: blob-content-retrieval-1
      to: content-understanding-1
      type: sequential
    - from: content-understanding-1
      to: field_mapper-1
      type: sequential
    - from: field_mapper-1
      to: blob-output-1
      type: sequential
`;

// Template 10: Content Understanding & Classification
const contentClassificationYaml = `
pipeline:
  name: "Content Understanding & Classification"
  description: "Analyze documents with AI for comprehensive content understanding"
  executors:
    - id: blob-input-1
      name: "Content Source"
      type: azure_blob_input
      position: { x: 250, y: 50 }
      description: "Load documents for analysis"
      
    - id: content-understanding-1
      name: "Content Extraction"
      type: azure_content_understanding_extractor
      position: { x: 250, y: 150 }
      description: "Extract content with Azure Content Understanding"
      settings:
        analyzer_id: "prebuilt-documentSearch"
        output_content_format: "markdown"
        
    - id: classifier-1
      name: "Content Classification"
      type: content_classifier
      position: { x: 150, y: 250 }
      description: "Classify document types"
      settings:
        categories: ["contract", "invoice", "report", "correspondence"]
        
    - id: sentiment-1
      name: "Sentiment Analysis"
      type: sentiment_analyser
      position: { x: 250, y: 250 }
      description: "Analyze document sentiment"
      
    - id: entity-1
      name: "Entity Extraction"
      type: entity_extractor
      position: { x: 350, y: 250 }
      description: "Extract key entities"
      
    - id: keyword-1
      name: "Keyword Extraction"
      type: keyword_extractor
      position: { x: 250, y: 350 }
      description: "Extract important keywords"
      settings:
        max_keywords: 20
        
    - id: blob-output-1
      name: "Save Analysis"
      type: azure_blob_output
      position: { x: 250, y: 450 }
      description: "Save comprehensive analysis"
      
  edges:
    - from: blob-input-1
      to: content-understanding-1
      type: sequential
    - from: content-understanding-1
      to: [classifier-1, sentiment-1, entity-1]
      type: parallel
    - from: [classifier-1, sentiment-1, entity-1]
      to: keyword-1
      type: join
      wait_strategy: all
    - from: keyword-1
      to: blob-output-1
      type: sequential
`;

// Template: PII Detection & Redaction
const piiDetectionYaml = `
pipeline:
  name: "PII Detection & Redaction"
  description: "Detect and optionally redact sensitive information from documents"
  executors:
    - id: blob-input-1
      name: "Document Source"
      type: azure_blob_input
      position: { x: 250, y: 50 }
      description: "Load documents for PII scanning"
      
    - id: content-understanding-1
      name: "Content Extraction"
      type: azure_content_understanding_extractor
      position: { x: 250, y: 150 }
      description: "Extract text content"
      settings:
        analyzer_id: "prebuilt-layout"
        
    - id: pii-detector-1
      name: "PII Detection"
      type: pii_detector
      position: { x: 250, y: 250 }
      description: "Detect sensitive information"
      settings:
        pii_types: ["SSN", "EMAIL", "PHONE", "CREDIT_CARD", "ADDRESS"]
        redaction_mode: "mask"
        
    - id: field-mapper-1
      name: "Format Results"
      type: field_mapper
      position: { x: 250, y: 350 }
      description: "Structure PII detection results"
      
    - id: blob-output-1
      name: "Save Results"
      type: azure_blob_output
      position: { x: 250, y: 450 }
      description: "Save redacted documents and reports"
      
  edges:
    - from: blob-input-1
      to: content-understanding-1
      type: sequential
    - from: content-understanding-1
      to: pii-detector-1
      type: sequential
    - from: pii-detector-1
      to: field-mapper-1
      type: sequential
    - from: field-mapper-1
      to: blob-output-1
      type: sequential
`;

// Template: Language Detection & Translation
const translationYaml = `
pipeline:
  name: "Language Detection & Translation"
  description: "Detect document languages and translate to target languages"
  executors:
    - id: blob-input-1
      name: "Document Source"
      type: azure_blob_input
      position: { x: 250, y: 50 }
      description: "Load multilingual documents"
      
    - id: content-understanding-1
      name: "Content Extraction"
      type: azure_content_understanding_extractor
      position: { x: 250, y: 150 }
      description: "Extract text content"
      settings:
        analyzer_id: "prebuilt-layout"
        
    - id: language-detector-1
      name: "Language Detection"
      type: language_detector
      position: { x: 250, y: 250 }
      description: "Detect document language"
      settings:
        detect_multiple: true
        
    - id: translator-1
      name: "Translation"
      type: content_translator
      position: { x: 250, y: 350 }
      description: "Translate to target language"
      settings:
        target_language: "en"
        preserve_formatting: true
        
    - id: blob-output-1
      name: "Save Translations"
      type: azure_blob_output
      position: { x: 250, y: 450 }
      description: "Save translated documents"
      
  edges:
    - from: blob-input-1
      to: content-understanding-1
      type: sequential
    - from: content-understanding-1
      to: language-detector-1
      type: sequential
    - from: language-detector-1
      to: translator-1
      type: sequential
    - from: translator-1
      to: blob-output-1
      type: sequential
`;

const financialAnnualReportYaml = `
pipeline:
  name: "Annual Report KPI + Risk Extraction (Agent Teams)"
  description: "Long-doc extraction + specialist agents + executive brief synthesis"

  executors:
    - id: blob-discovery-1
      name: "Discover Annual Reports"
      type: azure_blob_input_discovery
      position: { x: 250, y: 50 }
      description: "Discover annual/quarterly report PDFs"
      settings:
        file_extensions: ".pdf"
        blob_container_name: "annual-reports"
        max_results: 10

    - id: blob-content-retrieval-1
      name: "Retrieve Reports"
      type: azure_blob_content_retriever
      position: { x: 250, y: 180 }
      description: "Retrieve report content"
      settings:
        use_temp_file_for_content: true

    - id: pdf_extractor-1
      name: PDF Extractor
      type: pdf_extractor
      position: { x: 250, y: 320 }
      description: Extracts text, pages, and images from PDF documents using PyMuPDF
      settings:
        enabled: true
        condition: ''
        fail_pipeline_on_error: true
        debug_mode: false
        content_field: ''
        temp_file_path_field: temp_file_path
        output_field: pdf_output
        max_concurrent: 3
        continue_on_error: true
        extract_text: true
        extract_pages: true
        extract_images: false
        image_format: png
        image_output_mode: base64
        min_image_size: 100
        page_separator: |+


          ---

    - id: field-mapper-1
      name: "Normalize Input"
      type: field_mapper
      position: { x: 250, y: 460 }
      description: "Map markdown to agent input"
      settings:
        mappings: |-
          {
            "pdf_output.text": "text"
          }
        join_separator: "---"

    - id: agent-cashflow
      name: "Agent: Cash Flow & Liquidity"
      type: azure_openai_agent
      position: { x: -250, y: 320 }
      description: "Extract cash flow, liquidity, and debt maturity highlights"
      settings:
        endpoint: "https://<foundry-resource>.openai.azure.com/openai/v1/"
        deployment_name: "gpt-4.1-mini"
        input_field: "text"
        output_field: "cash_flow_liquidity"
        temperature: 0.1
        parse_response_as_json: true
        timeout_secs: 600
        max_tokens: 4000
        instructions: |-
          You are a financial analyst specializing in cash flow and liquidity analysis. Extract all cash flow and liquidity information from the annual report.
          
          Return a valid JSON object with the following structure:
          {
            "reporting_period": "string (e.g., 'FY2024', 'Q4 2024')",
            "currency": "string (e.g., 'USD', 'EUR')",
            "operating_activities": {
              "net_cash_from_operations": "number or null",
              "net_income": "number or null",
              "depreciation_amortization": "number or null",
              "stock_based_compensation": "number or null",
              "working_capital_changes": "number or null",
              "other_adjustments": "number or null",
              "yoy_change_percent": "number or null"
            },
            "investing_activities": {
              "capital_expenditures": "number or null",
              "acquisitions": "number or null",
              "asset_sales": "number or null",
              "investment_purchases": "number or null",
              "net_cash_from_investing": "number or null"
            },
            "financing_activities": {
              "debt_issuance": "number or null",
              "debt_repayment": "number or null",
              "dividends_paid": "number or null",
              "share_repurchases": "number or null",
              "net_cash_from_financing": "number or null"
            },
            "free_cash_flow": "number or null",
            "free_cash_flow_margin_percent": "number or null",
            "liquidity_position": {
              "cash_and_equivalents": "number or null",
              "short_term_investments": "number or null",
              "total_liquidity": "number or null",
              "revolving_credit_facility": {
                "total_capacity": "number or null",
                "drawn_amount": "number or null",
                "available_capacity": "number or null"
              },
              "current_ratio": "number or null",
              "quick_ratio": "number or null"
            },
            "debt_profile": {
              "total_debt": "number or null",
              "net_debt": "number or null",
              "debt_to_equity": "number or null",
              "debt_to_ebitda": "number or null",
              "interest_coverage_ratio": "number or null",
              "maturities": [
                {"year": "string", "amount": "number", "instrument": "string"}
              ],
              "weighted_avg_interest_rate": "number or null",
              "credit_ratings": [
                {"agency": "string", "rating": "string", "outlook": "string"}
              ]
            },
            "covenants": [
              {"covenant_type": "string", "required_ratio": "string", "actual_ratio": "string", "status": "compliant|non-compliant|waived"}
            ],
            "working_capital_notes": "string or null",
            "evidence_snippets": ["array of relevant quotes from the document"]
          }
          
          Only include fields where data is found. Use null for missing numeric values. Always return valid JSON.

    - id: agent-kpi
      name: "Agent: KPI Extractor"
      type: azure_openai_agent
      position: { x: -250, y: 460 }
      description: "Extract KPIs and periods"
      settings:
        endpoint: "https://<foundry-resource>.openai.azure.com/openai/v1/"
        deployment_name: "gpt-4.1"
        input_field: "text"
        output_field: "kpis"
        temperature: 0.1
        parse_response_as_json: true
        max_tokens: 4000
        timeout_secs: 600
        instructions: |-
          You are a financial analyst specializing in KPI extraction. Extract all key performance indicators from the annual report with period-over-period comparisons.
          
          Return a valid JSON object with the following structure:
          {
            "company_name": "string",
            "ticker_symbol": "string or null",
            "fiscal_year_end": "string (e.g., 'December 31, 2024')",
            "reporting_period": "string",
            "currency": "string",
            "revenue_metrics": {
              "total_revenue": "number or null",
              "yoy_growth_percent": "number or null",
              "organic_growth_percent": "number or null",
              "recurring_revenue": "number or null",
              "recurring_revenue_percent": "number or null",
              "arpu": "number or null",
              "revenue_by_type": [
                {"type": "string", "amount": "number", "percent_of_total": "number"}
              ]
            },
            "profitability_metrics": {
              "gross_profit": "number or null",
              "gross_margin_percent": "number or null",
              "operating_income": "number or null",
              "operating_margin_percent": "number or null",
              "ebitda": "number or null",
              "ebitda_margin_percent": "number or null",
              "net_income": "number or null",
              "net_margin_percent": "number or null",
              "eps_basic": "number or null",
              "eps_diluted": "number or null",
              "eps_yoy_growth_percent": "number or null"
            },
            "balance_sheet_metrics": {
              "total_assets": "number or null",
              "total_liabilities": "number or null",
              "shareholders_equity": "number or null",
              "book_value_per_share": "number or null",
              "return_on_equity_percent": "number or null",
              "return_on_assets_percent": "number or null",
              "return_on_invested_capital_percent": "number or null"
            },
            "operational_metrics": {
              "headcount": "number or null",
              "revenue_per_employee": "number or null",
              "customer_count": "number or null",
              "customer_retention_rate_percent": "number or null",
              "net_promoter_score": "number or null",
              "market_share_percent": "number or null"
            },
            "per_share_data": {
              "dividends_per_share": "number or null",
              "dividend_yield_percent": "number or null",
              "payout_ratio_percent": "number or null",
              "shares_outstanding_basic": "number or null",
              "shares_outstanding_diluted": "number or null"
            },
            "historical_comparison": [
              {"period": "string", "revenue": "number", "net_income": "number", "eps": "number"}
            ],
            "guidance_vs_actual": [
              {"metric": "string", "guidance_range": "string", "actual": "number", "status": "beat|met|missed"}
            ],
            "evidence_snippets": ["array of relevant quotes from the document"]
          }
          
          Only include fields where data is found. Use null for missing numeric values. Always return valid JSON.

    - id: agent-risks
      name: "Agent: Risk Factors"
      type: azure_openai_agent
      position: { x: -250, y: 600 }
      description: "Extract and rank risk factors"
      settings:
        endpoint: "https://<foundry-resource>.openai.azure.com/openai/v1/"
        deployment_name: "gpt-4.1-mini"
        input_field: "text"
        output_field: "risk_factors"
        temperature: 0.1
        parse_response_as_json: true
        max_tokens: 4000
        timeout_secs: 600
        instructions: |-
          You are a risk analyst specializing in corporate risk assessment. Extract and categorize all risk factors disclosed in the annual report.
          
          Return a valid JSON object with the following structure:
          {
            "risk_summary": {
              "total_risks_identified": "number",
              "new_risks_this_period": "number or null",
              "removed_risks_from_prior": "number or null",
              "highest_materiality_category": "string"
            },
            "risk_factors": [
              {
                "risk_id": "string (e.g., 'R001')",
                "risk_title": "string",
                "risk_category": "strategic|operational|financial|compliance|reputational|cybersecurity|market|credit|liquidity|technology|regulatory|environmental|geopolitical|supply_chain|human_capital",
                "description": "string",
                "materiality_rank": "number (1=highest risk)",
                "likelihood": "high|medium|low|not_specified",
                "potential_impact": "high|medium|low|not_specified",
                "trend_vs_prior_year": "increased|decreased|unchanged|new|not_specified",
                "mitigation_strategies": ["array of mitigation measures mentioned"],
                "quantified_exposure": "string or null (e.g., '$50M maximum loss')",
                "affected_business_areas": ["array of business segments affected"],
                "regulatory_references": ["array of relevant regulations mentioned"],
                "evidence_snippet": "string"
              }
            ],
            "risk_categories_breakdown": [
              {"category": "string", "count": "number", "top_risk": "string"}
            ],
            "emerging_risks": [
              {"risk": "string", "description": "string", "first_disclosed": "string"}
            ],
            "risk_management_framework": {
              "governance_structure": "string or null",
              "risk_committee": "boolean",
              "enterprise_risk_management": "boolean",
              "internal_audit_function": "boolean"
            },
            "insurance_coverage": {
              "types_of_coverage": ["array of insurance types"],
              "adequacy_statement": "string or null"
            },
            "evidence_snippets": ["array of relevant quotes from the document"]
          }
          
          Rank risks by materiality based on language emphasis and quantified impacts. Always return valid JSON.

    - id: agent-nongaap
      name: "Agent: Non-GAAP & Adjustments"
      type: azure_openai_agent
      position: { x: -250, y: 750 }
      description: "Extract non-GAAP metrics and key adjustments"
      settings:
        endpoint: "https://<foundry-resource>.openai.azure.com/openai/v1/"
        deployment_name: "gpt-4.1-mini"
        input_field: "text"
        output_field: "non_gaap_adjustments"
        temperature: 0.1
        parse_response_as_json: true
        max_tokens: 4000
        timeout_secs: 600
        instructions: |-
          You are a financial analyst specializing in non-GAAP metrics and earnings quality analysis. Extract all non-GAAP measures and reconciliation details from the annual report.
          
          Return a valid JSON object with the following structure:
          {
            "non_gaap_measures": [
              {
                "measure_name": "string (e.g., 'Adjusted EBITDA', 'Non-GAAP EPS')",
                "gaap_equivalent": "string (e.g., 'Net Income', 'GAAP EPS')",
                "non_gaap_value": "number or null",
                "gaap_value": "number or null",
                "difference": "number or null",
                "difference_percent": "number or null",
                "period": "string",
                "prior_period_value": "number or null",
                "yoy_change_percent": "number or null",
                "adjustments": [
                  {
                    "adjustment_label": "string",
                    "amount": "number",
                    "direction": "add|subtract",
                    "recurring": "boolean",
                    "explanation": "string or null"
                  }
                ],
                "management_rationale": "string or null",
                "evidence_snippet": "string"
              }
            ],
            "reconciliation_tables": [
              {
                "from_metric": "string",
                "to_metric": "string",
                "starting_value": "number",
                "ending_value": "number",
                "line_items": [
                  {"description": "string", "amount": "number"}
                ]
              }
            ],
            "adjusted_metrics_summary": {
              "adjusted_revenue": "number or null",
              "adjusted_gross_profit": "number or null",
              "adjusted_operating_income": "number or null",
              "adjusted_ebitda": "number or null",
              "adjusted_net_income": "number or null",
              "adjusted_eps": "number or null",
              "adjusted_free_cash_flow": "number or null"
            },
            "stock_based_compensation": {
              "total_expense": "number or null",
              "percent_of_revenue": "number or null",
              "breakdown_by_type": [
                {"type": "string", "amount": "number"}
              ]
            },
            "restructuring_charges": {
              "total_charges": "number or null",
              "components": [
                {"type": "string", "amount": "number", "expected_completion": "string or null"}
              ]
            },
            "acquisition_related_costs": {
              "total_costs": "number or null",
              "amortization_of_intangibles": "number or null",
              "integration_costs": "number or null",
              "transaction_costs": "number or null"
            },
            "quality_of_earnings_flags": [
              {"concern": "string", "description": "string", "severity": "high|medium|low"}
            ],
            "caveats_and_limitations": ["array of disclosed limitations of non-GAAP measures"],
            "evidence_snippets": ["array of relevant quotes from the document"]
          }
          
          Flag significant adjustments that may warrant investor scrutiny. Always return valid JSON.

    - id: agent-accounting
      name: "Agent: Critical Estimates & Accounting Changes"
      type: azure_openai_agent
      position: { x: -250, y: 900 }
      description: "Extract critical accounting estimates and policy changes"
      settings:
        endpoint: "https://<foundry-resource>.openai.azure.com/openai/v1/"
        deployment_name: "gpt-4.1-mini"
        input_field: "text"
        output_field: "accounting_estimates_changes"
        temperature: 0.1
        parse_response_as_json: true
        max_tokens: 4000
        timeout_secs: 600
        instructions: |-
          You are a financial analyst specializing in accounting policy analysis and critical estimates. Extract all critical accounting estimates, policy changes, and significant judgments from the annual report.
          
          Return a valid JSON object with the following structure:
          {
            "accounting_standards": {
              "framework": "string (e.g., 'US GAAP', 'IFRS')",
              "new_standards_adopted": [
                {
                  "standard": "string (e.g., 'ASC 842', 'IFRS 16')",
                  "description": "string",
                  "adoption_date": "string",
                  "adoption_method": "string (e.g., 'modified retrospective')",
                  "financial_impact": {
                    "assets_impact": "number or null",
                    "liabilities_impact": "number or null",
                    "equity_impact": "number or null",
                    "income_statement_impact": "string or null"
                  },
                  "evidence_snippet": "string"
                }
              ],
              "upcoming_standards": [
                {
                  "standard": "string",
                  "effective_date": "string",
                  "expected_impact": "material|immaterial|under_evaluation",
                  "description": "string"
                }
              ]
            },
            "critical_accounting_estimates": [
              {
                "estimate_area": "string (e.g., 'Goodwill Impairment', 'Revenue Recognition', 'Allowance for Credit Losses')",
                "description": "string",
                "key_assumptions": ["array of key assumptions used"],
                "sensitivity_analysis": {
                  "variable": "string",
                  "change_tested": "string",
                  "impact_on_results": "string"
                },
                "management_judgment_level": "high|medium|low",
                "year_over_year_change": "string or null",
                "quantified_amount": "number or null",
                "audit_risk_area": "boolean",
                "evidence_snippet": "string"
              }
            ],
            "accounting_policy_changes": [
              {
                "policy_area": "string",
                "nature_of_change": "string",
                "reason_for_change": "string",
                "effective_date": "string",
                "retrospective_application": "boolean",
                "financial_impact": "string or null",
                "evidence_snippet": "string"
              }
            ],
            "significant_judgments": [
              {
                "judgment_area": "string",
                "description": "string",
                "alternatives_considered": "string or null",
                "rationale": "string",
                "evidence_snippet": "string"
              }
            ],
            "error_corrections": [
              {
                "nature_of_error": "string",
                "periods_affected": ["array of affected periods"],
                "correction_method": "string",
                "financial_impact": "string",
                "evidence_snippet": "string"
              }
            ],
            "auditor_concerns": {
              "critical_audit_matters": [
                {"matter": "string", "auditor_response": "string"}
              ],
              "emphasis_of_matter": "string or null",
              "audit_opinion_type": "unqualified|qualified|adverse|disclaimer"
            },
            "evidence_snippets": ["array of relevant quotes from the document"]
          }
          
          Focus on areas with high estimation uncertainty and potential earnings management. Always return valid JSON.

    - id: agent-esg
      name: "Agent: ESG / Sustainability"
      type: azure_openai_agent
      position: { x: 720, y: 320 }
      description: "Extract ESG and sustainability disclosures when present"
      settings:
        endpoint: "https://<foundry-resource>.openai.azure.com/openai/v1/"
        deployment_name: "gpt-4.1-mini"
        input_field: "text"
        output_field: "esg_disclosures"
        temperature: 0.1
        parse_response_as_json: true
        max_tokens: 4000
        timeout_secs: 600
        instructions: |-
          You are an ESG analyst specializing in sustainability disclosures and corporate responsibility. Extract all ESG-related information from the annual report.
          
          Return a valid JSON object with the following structure (return empty arrays if no ESG content is present):
          {
            "esg_overview": {
              "has_dedicated_esg_section": "boolean",
              "reporting_frameworks": ["array (e.g., 'GRI', 'SASB', 'TCFD', 'CDP', 'UN SDGs')"],
              "third_party_assurance": "boolean",
              "assurance_provider": "string or null",
              "materiality_assessment_conducted": "boolean"
            },
            "environmental": {
              "climate_strategy": {
                "net_zero_commitment": "boolean",
                "target_year": "string or null",
                "science_based_targets": "boolean",
                "carbon_neutral_status": "string or null"
              },
              "emissions": {
                "scope_1": {"value": "number or null", "unit": "string", "yoy_change_percent": "number or null"},
                "scope_2": {"value": "number or null", "unit": "string", "yoy_change_percent": "number or null"},
                "scope_3": {"value": "number or null", "unit": "string", "categories_included": ["array"]},
                "emissions_intensity": {"value": "number or null", "unit": "string"},
                "reduction_target": {"target_percent": "number or null", "baseline_year": "string", "target_year": "string"}
              },
              "energy": {
                "total_consumption": {"value": "number or null", "unit": "string"},
                "renewable_percent": "number or null",
                "renewable_target": {"target_percent": "number or null", "target_year": "string or null"}
              },
              "water": {
                "total_withdrawal": {"value": "number or null", "unit": "string"},
                "recycled_percent": "number or null",
                "water_stress_areas": "boolean"
              },
              "waste": {
                "total_generated": {"value": "number or null", "unit": "string"},
                "recycling_rate_percent": "number or null",
                "zero_waste_target": "boolean"
              },
              "environmental_investments": "number or null",
              "environmental_incidents": "number or null",
              "evidence_snippets": ["array of relevant quotes"]
            },
            "social": {
              "workforce": {
                "total_employees": "number or null",
                "diversity_metrics": {
                  "women_total_percent": "number or null",
                  "women_leadership_percent": "number or null",
                  "minorities_percent": "number or null",
                  "diversity_targets": ["array of targets"]
                },
                "employee_turnover_percent": "number or null",
                "employee_engagement_score": "number or null",
                "training_hours_per_employee": "number or null",
                "training_investment": "number or null"
              },
              "health_and_safety": {
                "injury_rate": "number or null",
                "fatalities": "number or null",
                "safety_certifications": ["array of certifications"]
              },
              "human_rights": {
                "policy_in_place": "boolean",
                "supply_chain_audits": "boolean",
                "incidents_reported": "number or null"
              },
              "community": {
                "charitable_contributions": "number or null",
                "volunteer_hours": "number or null",
                "community_programs": ["array of programs"]
              },
              "evidence_snippets": ["array of relevant quotes"]
            },
            "governance": {
              "board_composition": {
                "total_members": "number or null",
                "independent_percent": "number or null",
                "women_percent": "number or null",
                "average_tenure_years": "number or null",
                "average_age": "number or null",
                "diversity_policy": "boolean"
              },
              "executive_compensation": {
                "ceo_total_compensation": "number or null",
                "ceo_pay_ratio": "number or null",
                "esg_linked_compensation": "boolean",
                "esg_metrics_in_pay": ["array of ESG metrics tied to exec pay"]
              },
              "ethics_and_compliance": {
                "code_of_conduct": "boolean",
                "whistleblower_policy": "boolean",
                "anti_corruption_training_percent": "number or null",
                "ethics_violations": "number or null"
              },
              "cybersecurity": {
                "board_oversight": "boolean",
                "incidents_disclosed": "number or null",
                "security_certifications": ["array of certifications"]
              },
              "evidence_snippets": ["array of relevant quotes"]
            },
            "esg_ratings": [
              {"agency": "string", "rating": "string", "date": "string or null"}
            ],
            "controversies": [
              {"issue": "string", "status": "string", "response": "string"}
            ],
            "sdg_alignment": [
              {"sdg_number": "number", "sdg_name": "string", "initiatives": ["array"]}
            ],
            "evidence_snippets": ["array of relevant quotes from the document"]
          }
          
          Only include sections where data is present. Always return valid JSON.

    - id: agent-capalloc
      name: "Agent: Capital Allocation"
      type: azure_openai_agent
      position: { x: 720, y: 460 }
      description: "Extract capital allocation actions and stated priorities"
      settings:
        endpoint: "https://<foundry-resource>.openai.azure.com/openai/v1/"
        deployment_name: "gpt-4.1-mini"
        input_field: "text"
        output_field: "capital_allocation"
        temperature: 0.1
        parse_response_as_json: true
        max_tokens: 4000
        timeout_secs: 600
        instructions: |-
          You are a financial analyst specializing in capital allocation and shareholder returns. Extract all capital allocation information from the annual report.
          
          Return a valid JSON object with the following structure:
          {
            "capital_allocation_philosophy": "string or null",
            "stated_priorities": [
              {"priority": "string", "rank": "number", "allocation_percent": "number or null"}
            ],
            "dividends": {
              "dividend_policy": "string or null",
              "current_quarterly_dividend": "number or null",
              "annual_dividend_per_share": "number or null",
              "dividend_yield_percent": "number or null",
              "total_dividends_paid": "number or null",
              "payout_ratio_percent": "number or null",
              "yoy_dividend_growth_percent": "number or null",
              "consecutive_years_increased": "number or null",
              "dividend_aristocrat_status": "boolean",
              "special_dividends": {"amount": "number or null", "date": "string or null"},
              "evidence_snippet": "string"
            },
            "share_repurchases": {
              "buyback_program_authorized": "number or null",
              "authorization_date": "string or null",
              "authorization_expiry": "string or null",
              "remaining_authorization": "number or null",
              "shares_repurchased_current_period": "number or null",
              "amount_spent_current_period": "number or null",
              "average_price_paid": "number or null",
              "total_shares_repurchased_historical": "number or null",
              "shares_outstanding_reduction_percent": "number or null",
              "repurchase_method": "open_market|accelerated|tender_offer|mixed",
              "evidence_snippet": "string"
            },
            "capital_expenditures": {
              "total_capex": "number or null",
              "maintenance_capex": "number or null",
              "growth_capex": "number or null",
              "capex_to_revenue_percent": "number or null",
              "capex_to_depreciation_ratio": "number or null",
              "major_projects": [
                {"project": "string", "investment": "number or null", "timeline": "string or null", "expected_return": "string or null"}
              ],
              "capex_guidance_next_year": "string or null",
              "evidence_snippet": "string"
            },
            "mergers_and_acquisitions": {
              "acquisitions_completed": [
                {
                  "target": "string",
                  "acquisition_date": "string",
                  "purchase_price": "number or null",
                  "payment_method": "cash|stock|mixed",
                  "strategic_rationale": "string",
                  "expected_synergies": "number or null",
                  "synergy_timeline": "string or null",
                  "goodwill_recognized": "number or null",
                  "revenue_contribution": "number or null"
                }
              ],
              "divestitures_completed": [
                {
                  "asset_divested": "string",
                  "sale_date": "string",
                  "proceeds": "number or null",
                  "gain_loss": "number or null",
                  "strategic_rationale": "string"
                }
              ],
              "pending_transactions": [
                {"target": "string", "status": "string", "expected_close": "string or null", "value": "number or null"}
              ],
              "total_ma_spending": "number or null",
              "evidence_snippet": "string"
            },
            "debt_management": {
              "debt_issuances": [
                {"instrument": "string", "amount": "number", "rate": "string", "maturity": "string", "use_of_proceeds": "string"}
              ],
              "debt_repayments": [
                {"instrument": "string", "amount": "number", "early_repayment": "boolean"}
              ],
              "refinancing_activities": "string or null",
              "target_leverage_ratio": "string or null",
              "evidence_snippet": "string"
            },
            "rd_investment": {
              "total_rd_spending": "number or null",
              "rd_to_revenue_percent": "number or null",
              "yoy_rd_growth_percent": "number or null",
              "major_rd_initiatives": ["array of key R&D focus areas"],
              "evidence_snippet": "string"
            },
            "capital_returns_summary": {
              "total_returned_to_shareholders": "number or null",
              "dividends_amount": "number or null",
              "buybacks_amount": "number or null",
              "return_yield_percent": "number or null",
              "three_year_total_returned": "number or null"
            },
            "evidence_snippets": ["array of relevant quotes from the document"]
          }
          
          Prioritize quantified allocations and forward guidance. Always return valid JSON.

    - id: agent-segments
      name: "Agent: Segments & Geography"
      type: azure_openai_agent
      position: { x: 720, y: 620 }
      description: "Extract segment reporting and geographic mix"
      settings:
        endpoint: "https://<foundry-resource>.openai.azure.com/openai/v1/"
        deployment_name: "gpt-4.1-mini"
        input_field: "text"
        output_field: "segments_geography"
        temperature: 0.1
        parse_response_as_json: true
        max_tokens: 4000
        timeout_secs: 600
        instructions: |-
          You are a financial analyst specializing in segment analysis and geographic revenue breakdown. Extract all business segment and geographic information from the annual report.
          
          Return a valid JSON object with the following structure:
          {
            "reporting_segments_overview": {
              "number_of_segments": "number",
              "segment_basis": "string (e.g., 'product lines', 'geographic regions', 'customer types')",
              "intersegment_eliminations": "number or null",
              "segment_changes_from_prior_year": "string or null"
            },
            "business_segments": [
              {
                "segment_name": "string",
                "segment_description": "string or null",
                "revenue": "number or null",
                "revenue_percent_of_total": "number or null",
                "yoy_revenue_growth_percent": "number or null",
                "organic_growth_percent": "number or null",
                "operating_income": "number or null",
                "operating_margin_percent": "number or null",
                "yoy_operating_income_growth_percent": "number or null",
                "depreciation_amortization": "number or null",
                "capital_expenditures": "number or null",
                "total_assets": "number or null",
                "goodwill": "number or null",
                "headcount": "number or null",
                "key_products_services": ["array of main offerings"],
                "key_customers": ["array of major customers if disclosed"],
                "competitive_position": "string or null",
                "market_trends": "string or null",
                "growth_drivers": ["array of growth factors"],
                "challenges": ["array of headwinds"],
                "management_outlook": "string or null",
                "evidence_snippet": "string"
              }
            ],
            "geographic_breakdown": {
              "domestic": {
                "region_name": "string (e.g., 'United States', 'Home Country')",
                "revenue": "number or null",
                "revenue_percent_of_total": "number or null",
                "yoy_growth_percent": "number or null",
                "long_lived_assets": "number or null",
                "evidence_snippet": "string"
              },
              "international_total": {
                "revenue": "number or null",
                "revenue_percent_of_total": "number or null",
                "yoy_growth_percent": "number or null"
              },
              "regions": [
                {
                  "region_name": "string (e.g., 'EMEA', 'Asia Pacific', 'Latin America')",
                  "revenue": "number or null",
                  "revenue_percent_of_total": "number or null",
                  "yoy_growth_percent": "number or null",
                  "constant_currency_growth_percent": "number or null",
                  "fx_impact": "number or null",
                  "long_lived_assets": "number or null",
                  "key_markets": ["array of specific countries"],
                  "regional_trends": "string or null",
                  "evidence_snippet": "string"
                }
              ],
              "countries": [
                {
                  "country": "string",
                  "revenue": "number or null",
                  "revenue_percent_of_total": "number or null",
                  "yoy_growth_percent": "number or null",
                  "material_operations": "boolean"
                }
              ]
            },
            "customer_concentration": {
              "top_customer_percent": "number or null",
              "top_5_customers_percent": "number or null",
              "top_10_customers_percent": "number or null",
              "named_major_customers": [
                {"customer": "string", "revenue_percent": "number or null", "relationship_tenure": "string or null"}
              ],
              "government_revenue_percent": "number or null",
              "customer_diversification_trend": "improving|stable|worsening|not_specified",
              "evidence_snippet": "string"
            },
            "product_revenue_breakdown": [
              {
                "product_category": "string",
                "revenue": "number or null",
                "revenue_percent_of_total": "number or null",
                "yoy_growth_percent": "number or null",
                "gross_margin_percent": "number or null"
              }
            ],
            "channel_breakdown": [
              {
                "channel": "string (e.g., 'Direct', 'Distributor', 'OEM', 'Online')",
                "revenue_percent": "number or null",
                "trend": "string or null"
              }
            ],
            "currency_exposure": {
              "primary_currencies": ["array of major currencies"],
              "natural_hedges": "string or null",
              "hedging_strategy": "string or null",
              "fx_sensitivity": "string or null"
            },
            "evidence_snippets": ["array of relevant quotes from the document"]
          }
          
          Include all quantified segment and geographic data. Always return valid JSON.

    - id: agent-footnotes
      name: "Agent: Footnotes"
      type: azure_openai_agent
      position: { x: 720, y: 780 }
      description: "Summarize key footnotes and accounting policies"
      settings:
        endpoint: "https://<foundry-resource>.openai.azure.com/openai/v1/"
        deployment_name: "gpt-4.1-mini"
        input_field: "text"
        output_field: "footnotes"
        temperature: 0.1
        parse_response_as_json: true
        max_tokens: 4000
        timeout_secs: 600
        instructions: |-
          You are a financial analyst specializing in financial statement footnote analysis. Extract and summarize all material footnote disclosures from the annual report.
          
          Return a valid JSON object with the following structure:
          {
            "footnotes_summary": {
              "total_footnotes_identified": "number",
              "most_significant_footnotes": ["array of footnote topics with highest materiality"]
            },
            "significant_accounting_policies": [
              {
                "policy_area": "string",
                "description": "string",
                "key_assumptions": ["array of assumptions"],
                "changes_from_prior_year": "string or null",
                "evidence_snippet": "string"
              }
            ],
            "revenue_recognition": {
              "policy_summary": "string",
              "performance_obligations": ["array of identified performance obligations"],
              "timing_of_recognition": "string",
              "variable_consideration": "string or null",
              "contract_assets": "number or null",
              "contract_liabilities": "number or null",
              "remaining_performance_obligations": "number or null",
              "expected_recognition_timeline": "string or null",
              "evidence_snippet": "string"
            },
            "leases": {
              "operating_lease_rou_assets": "number or null",
              "operating_lease_liabilities": "number or null",
              "finance_lease_assets": "number or null",
              "finance_lease_liabilities": "number or null",
              "weighted_avg_remaining_term_years": "number or null",
              "weighted_avg_discount_rate_percent": "number or null",
              "future_minimum_payments": [
                {"year": "string", "amount": "number"}
              ],
              "evidence_snippet": "string"
            },
            "goodwill_and_intangibles": {
              "goodwill_balance": "number or null",
              "goodwill_by_segment": [
                {"segment": "string", "amount": "number"}
              ],
              "impairment_testing_approach": "string or null",
              "impairment_charges_current_period": "number or null",
              "intangible_assets": [
                {"type": "string", "gross_amount": "number", "accumulated_amortization": "number", "useful_life_years": "string"}
              ],
              "annual_amortization_expense": "number or null",
              "evidence_snippet": "string"
            },
            "income_taxes": {
              "effective_tax_rate_percent": "number or null",
              "statutory_rate_percent": "number or null",
              "rate_reconciliation_items": [
                {"item": "string", "impact_percent": "number"}
              ],
              "deferred_tax_assets": "number or null",
              "valuation_allowance": "number or null",
              "deferred_tax_liabilities": "number or null",
              "unrecognized_tax_benefits": "number or null",
              "tax_jurisdictions": ["array of key jurisdictions"],
              "tax_audits_status": "string or null",
              "evidence_snippet": "string"
            },
            "debt_and_borrowings": {
              "debt_instruments": [
                {
                  "instrument": "string",
                  "principal_amount": "number",
                  "interest_rate": "string",
                  "maturity_date": "string",
                  "fair_value": "number or null",
                  "covenants": ["array of key covenants"]
                }
              ],
              "debt_maturities_schedule": [
                {"year": "string", "amount": "number"}
              ],
              "interest_expense": "number or null",
              "evidence_snippet": "string"
            },
            "pension_and_benefits": {
              "defined_benefit_obligation": "number or null",
              "plan_assets_fair_value": "number or null",
              "funded_status": "number or null",
              "net_periodic_cost": "number or null",
              "discount_rate_percent": "number or null",
              "expected_return_on_assets_percent": "number or null",
              "contribution_next_year": "number or null",
              "evidence_snippet": "string"
            },
            "stock_compensation": {
              "total_expense": "number or null",
              "unrecognized_compensation_cost": "number or null",
              "weighted_avg_recognition_period_years": "number or null",
              "options_outstanding": "number or null",
              "rsus_outstanding": "number or null",
              "fair_value_assumptions": {
                "expected_volatility_percent": "number or null",
                "risk_free_rate_percent": "number or null",
                "expected_term_years": "number or null"
              },
              "evidence_snippet": "string"
            },
            "fair_value_measurements": {
              "level_1_assets": "number or null",
              "level_2_assets": "number or null",
              "level_3_assets": "number or null",
              "level_3_rollforward": "string or null",
              "significant_level_3_inputs": ["array of key unobservable inputs"],
              "evidence_snippet": "string"
            },
            "related_party_transactions": [
              {
                "related_party": "string",
                "nature_of_relationship": "string",
                "transaction_type": "string",
                "amount": "number or null",
                "terms": "string or null",
                "evidence_snippet": "string"
              }
            ],
            "subsequent_events": [
              {
                "event": "string",
                "date": "string",
                "financial_impact": "string or null",
                "recognized_vs_disclosed": "recognized|disclosed",
                "evidence_snippet": "string"
              }
            ],
            "evidence_snippets": ["array of relevant quotes from the document"]
          }
          
          Focus on material disclosures and quantified impacts. Always return valid JSON.

    - id: agent-legal
      name: "Agent: Legal / Commitments / Contingencies"
      type: azure_openai_agent
      position: { x: 720, y: 900 }
      description: "Extract litigation, regulatory matters, commitments, and contingencies"
      settings:
        endpoint: "https://<foundry-resource>.openai.azure.com/openai/v1/"
        deployment_name: "gpt-4.1-mini"
        input_field: "text"
        output_field: "legal_commitments_contingencies"
        temperature: 0.1
        parse_response_as_json: true
        max_tokens: 4000
        timeout_secs: 600
        instructions: |-
          You are a legal and financial analyst specializing in litigation, regulatory matters, and contingent liabilities. Extract all legal, commitment, and contingency disclosures from the annual report.
          
          Return a valid JSON object with the following structure:
          {
            "litigation_summary": {
              "total_pending_matters": "number or null",
              "material_matters_count": "number or null",
              "aggregate_contingent_liability": "number or null",
              "accrued_liabilities_for_litigation": "number or null",
              "insurance_coverage_available": "boolean"
            },
            "legal_proceedings": [
              {
                "case_id": "string (e.g., 'L001')",
                "case_name_or_description": "string",
                "case_type": "class_action|individual|regulatory|patent|antitrust|environmental|employment|securities|product_liability|contract|other",
                "jurisdiction": "string or null",
                "filing_date": "string or null",
                "parties_involved": ["array of party names"],
                "allegations_summary": "string",
                "current_status": "pending|discovery|trial|appeal|settled|dismissed|ongoing",
                "potential_exposure": {
                  "minimum": "number or null",
                  "maximum": "number or null",
                  "management_estimate": "number or null",
                  "reasonably_possible_loss": "number or null"
                },
                "accrual_recorded": "number or null",
                "probability_assessment": "probable|reasonably_possible|remote|not_specified",
                "expected_resolution_timeline": "string or null",
                "insurance_recovery_expected": "number or null",
                "management_assessment": "string or null",
                "evidence_snippet": "string"
              }
            ],
            "regulatory_matters": [
              {
                "matter_description": "string",
                "regulatory_body": "string",
                "nature_of_inquiry": "investigation|audit|examination|enforcement|consent_order",
                "status": "ongoing|resolved|pending",
                "potential_penalties": "number or null",
                "remediation_required": "string or null",
                "compliance_programs_implemented": ["array of programs"],
                "evidence_snippet": "string"
              }
            ],
            "government_investigations": [
              {
                "investigating_agency": "string",
                "subject_matter": "string",
                "status": "ongoing|resolved|pending",
                "potential_impact": "string",
                "evidence_snippet": "string"
              }
            ],
            "commitments": {
              "purchase_commitments": {
                "total_amount": "number or null",
                "schedule": [
                  {"year": "string", "amount": "number"}
                ],
                "major_suppliers": ["array of suppliers if disclosed"],
                "evidence_snippet": "string"
              },
              "lease_commitments": {
                "operating_lease_total": "number or null",
                "finance_lease_total": "number or null",
                "schedule": [
                  {"year": "string", "operating": "number", "finance": "number"}
                ],
                "evidence_snippet": "string"
              },
              "capital_commitments": {
                "total_committed": "number or null",
                "major_projects": ["array of committed projects"],
                "evidence_snippet": "string"
              },
              "other_commitments": [
                {"type": "string", "amount": "number or null", "description": "string", "evidence_snippet": "string"}
              ]
            },
            "contingencies": [
              {
                "contingency_type": "string",
                "description": "string",
                "probability": "probable|reasonably_possible|remote",
                "estimated_loss_range": {
                  "minimum": "number or null",
                  "maximum": "number or null"
                },
                "accrual_amount": "number or null",
                "factors_affecting_outcome": ["array of key factors"],
                "evidence_snippet": "string"
              }
            ],
            "guarantees_and_indemnifications": [
              {
                "type": "string",
                "beneficiary": "string or null",
                "maximum_exposure": "number or null",
                "current_liability": "number or null",
                "expiration": "string or null",
                "evidence_snippet": "string"
              }
            ],
            "environmental_liabilities": {
              "total_accrued": "number or null",
              "remediation_sites": "number or null",
              "superfund_sites": "number or null",
              "estimated_future_costs": "number or null",
              "insurance_recoveries_expected": "number or null",
              "evidence_snippet": "string"
            },
            "product_warranties": {
              "warranty_liability": "number or null",
              "warranty_expense": "number or null",
              "warranty_period": "string or null",
              "evidence_snippet": "string"
            },
            "letters_of_credit": {
              "outstanding_amount": "number or null",
              "purpose": "string or null"
            },
            "evidence_snippets": ["array of relevant quotes from the document"]
          }
          
          Quantify exposures where disclosed. Use probability language from the document. Always return valid JSON.

    - id: agent-outlook
      name: "Agent: Guidance / Outlook"
      type: azure_openai_agent
      position: { x: 720, y: 1050 }
      description: "Extract guidance, outlook, and strategic initiatives"
      settings:
        endpoint: "https://<foundry-resource>.openai.azure.com/openai/v1/"
        deployment_name: "gpt-4.1-mini"
        input_field: "text"
        output_field: "guidance_outlook"
        temperature: 0.1
        parse_response_as_json: true
        max_tokens: 4000
        timeout_secs: 600
        instructions: |-
          You are a financial analyst specializing in forward guidance and strategic analysis. Extract all forward-looking guidance, outlook, and strategic initiatives from the annual report.
          
          Return a valid JSON object with the following structure:
          {
            "guidance_summary": {
              "guidance_provided": "boolean",
              "guidance_period": "string (e.g., 'FY2025', 'Q1 2025')",
              "guidance_style": "annual|quarterly|long_term|range|point_estimate",
              "guidance_basis": "GAAP|non-GAAP|both"
            },
            "financial_guidance": [
              {
                "metric": "string (e.g., 'Revenue', 'EPS', 'Operating Margin')",
                "guidance_type": "range|point_estimate|directional|growth_rate",
                "low_estimate": "number or null",
                "high_estimate": "number or null",
                "point_estimate": "number or null",
                "growth_rate_percent": "number or null",
                "vs_prior_year_actual": "string or null",
                "vs_prior_guidance": "raised|maintained|lowered|new",
                "currency_assumption": "string or null",
                "key_assumptions": ["array of assumptions underlying the guidance"],
                "confidence_level": "high|medium|low|not_specified",
                "evidence_snippet": "string"
              }
            ],
            "segment_guidance": [
              {
                "segment": "string",
                "revenue_growth_expectation": "string or null",
                "margin_expectation": "string or null",
                "key_drivers": ["array of growth drivers"],
                "evidence_snippet": "string"
              }
            ],
            "capital_allocation_guidance": {
              "capex_guidance": "string or null",
              "dividend_guidance": "string or null",
              "buyback_guidance": "string or null",
              "ma_appetite": "string or null",
              "evidence_snippet": "string"
            },
            "operational_guidance": {
              "headcount_plans": "string or null",
              "facility_plans": "string or null",
              "cost_reduction_targets": "string or null",
              "efficiency_initiatives": ["array of initiatives"],
              "evidence_snippet": "string"
            },
            "strategic_initiatives": [
              {
                "initiative_name": "string",
                "description": "string",
                "strategic_priority": "high|medium|low",
                "investment_required": "number or null",
                "expected_timeline": "string or null",
                "expected_benefits": "string or null",
                "progress_status": "planning|in_progress|completed|ongoing",
                "key_milestones": ["array of milestones"],
                "risks_to_execution": ["array of risks"],
                "evidence_snippet": "string"
              }
            ],
            "long_term_targets": [
              {
                "metric": "string",
                "target_value": "string",
                "target_year": "string",
                "baseline_value": "string or null",
                "progress_to_date": "string or null",
                "evidence_snippet": "string"
              }
            ],
            "market_outlook": {
              "industry_growth_expectation": "string or null",
              "market_size_estimate": "string or null",
              "competitive_dynamics": "string or null",
              "demand_drivers": ["array of demand factors"],
              "headwinds": ["array of challenges"],
              "evidence_snippet": "string"
            },
            "macroeconomic_assumptions": {
              "gdp_growth_assumption": "string or null",
              "interest_rate_assumption": "string or null",
              "inflation_assumption": "string or null",
              "currency_assumptions": ["array of FX assumptions"],
              "commodity_price_assumptions": ["array of commodity assumptions"],
              "evidence_snippet": "string"
            },
            "watch_items": [
              {
                "item": "string",
                "description": "string",
                "potential_impact": "positive|negative|uncertain",
                "management_response": "string or null",
                "evidence_snippet": "string"
              }
            ],
            "management_tone": {
              "overall_sentiment": "bullish|cautiously_optimistic|neutral|cautious|bearish",
              "key_positive_themes": ["array of positive themes emphasized"],
              "key_concerns_acknowledged": ["array of concerns mentioned"],
              "notable_language_changes": "string or null"
            },
            "analyst_focus_areas": ["array of topics likely to draw analyst attention"],
            "evidence_snippets": ["array of relevant quotes from the document"]
          }
          
          Capture both quantitative guidance and qualitative outlook statements. Always return valid JSON.

    - id: agent-brief
      name: "Agent: Executive Brief"
      type: azure_openai_agent
      position: { x: 250, y: 1080 }
      description: "Synthesize into executive brief"
      settings:
        endpoint: "https://<foundry-resource>.openai.azure.com/openai/v1/"
        deployment_name: "gpt-4.1"
        input_field: "text"
        output_field: "executive_brief"
        temperature: 0.1
        parse_response_as_json: true
        max_tokens: 8000
        timeout_secs: 600
        instructions: |-
          You are a senior financial analyst preparing an executive briefing for institutional investors. Synthesize all extracted information into a comprehensive executive brief.
          
          Return a valid JSON object with the following structure:
          {
            "executive_summary": {
              "company_name": "string",
              "reporting_period": "string",
              "report_date": "string",
              "one_liner": "string (single sentence capturing the key takeaway)",
              "investment_thesis_summary": "string (2-3 sentences on investment case)"
            },
            "key_highlights": [
              {
                "category": "financial_performance|strategic|operational|capital_allocation|risk|esg",
                "highlight": "string",
                "significance": "positive|negative|neutral",
                "quantification": "string or null",
                "evidence_snippet": "string"
              }
            ],
            "financial_scorecard": {
              "revenue": {"value": "number or null", "yoy_change_percent": "number or null", "vs_guidance": "beat|met|missed|na"},
              "operating_income": {"value": "number or null", "margin_percent": "number or null", "yoy_change_percent": "number or null"},
              "eps": {"value": "number or null", "yoy_change_percent": "number or null", "vs_consensus": "beat|met|missed|na"},
              "free_cash_flow": {"value": "number or null", "yoy_change_percent": "number or null"},
              "roic_percent": "number or null",
              "net_debt_to_ebitda": "number or null"
            },
            "strategic_assessment": {
              "business_model_strength": "strong|adequate|weak",
              "competitive_position": "leader|strong_competitor|average|challenged",
              "growth_trajectory": "accelerating|stable|decelerating|declining",
              "management_execution": "excellent|good|mixed|poor",
              "capital_allocation_quality": "excellent|good|adequate|poor",
              "key_strategic_moves": ["array of significant strategic actions"]
            },
            "concerns_and_risks": [
              {
                "concern": "string",
                "category": "financial|operational|competitive|regulatory|macro|execution",
                "severity": "high|medium|low",
                "probability": "high|medium|low",
                "potential_impact": "string",
                "management_mitigation": "string or null",
                "evidence_snippet": "string"
              }
            ],
            "open_questions": [
              {
                "question": "string",
                "context": "string",
                "importance": "high|medium|low",
                "suggested_follow_up": "string or null"
              }
            ],
            "guidance_assessment": {
              "guidance_quality": "specific|vague|no_guidance",
              "achievability": "conservative|realistic|aggressive|uncertain",
              "key_swing_factors": ["array of factors that could move results"],
              "upside_scenario": "string or null",
              "downside_scenario": "string or null"
            },
            "peer_comparison_indicators": {
              "relative_valuation_signals": "string or null",
              "margin_vs_industry": "above|inline|below|unknown",
              "growth_vs_industry": "above|inline|below|unknown"
            },
            "esg_assessment": {
              "esg_maturity": "leader|developing|nascent|none",
              "material_esg_issues": ["array of material ESG topics"],
              "notable_esg_progress": "string or null",
              "esg_risks": ["array of ESG-related risks"]
            },
            "catalysts_and_events": {
              "upcoming_catalysts": [
                {"event": "string", "expected_date": "string or null", "potential_impact": "positive|negative|uncertain"}
              ],
              "key_dates": [
                {"event": "string", "date": "string"}
              ]
            },
            "action_items": [
              {
                "action": "string",
                "priority": "high|medium|low",
                "audience": "investors|analysts|management|board"
              }
            ],
            "confidence_assessment": {
              "data_quality": "high|medium|low",
              "completeness": "comprehensive|adequate|limited",
              "areas_of_uncertainty": ["array of areas where information was limited"],
              "reliability_score": "number (1-10 scale)"
            },
            "appendix": {
              "key_metrics_table": [
                {"metric": "string", "current_period": "string", "prior_period": "string", "change": "string"}
              ],
              "segment_summary": [
                {"segment": "string", "revenue": "number or null", "growth_percent": "number or null", "margin_percent": "number or null"}
              ],
              "guidance_summary": [
                {"metric": "string", "guidance_range": "string", "prior_guidance": "string or null"}
              ]
            },
            "evidence_snippets": ["array of key quotes supporting the analysis"]
          }
          
          Prioritize actionable insights. Be direct about concerns. Always return valid JSON.

    - id: blob-output-1
      name: "Save Results"
      type: azure_blob_output
      position: { x: 250, y: 1220 }
      description: "Save extracted KPIs and brief"

  edges:
    - from: blob-discovery-1
      to: blob-content-retrieval-1
      type: sequential
    - from: field-mapper-1
      to: agent-cashflow
      type: sequential
    - from: agent-brief
      to: blob-output-1
      type: sequential
    - from: blob-content-retrieval-1
      to: pdf_extractor-1
      type: sequential
    - from: pdf_extractor-1
      to: field-mapper-1
      type: sequential
    - from: agent-cashflow
      to: agent-kpi
      type: sequential
    - from: agent-kpi
      to: agent-risks
      type: sequential
    - from: agent-risks
      to: agent-nongaap
      type: sequential
    - from: agent-nongaap
      to: agent-accounting
      type: sequential
    - from: agent-esg
      to: agent-capalloc
      type: sequential
    - from: agent-capalloc
      to: agent-segments
      type: sequential
    - from: agent-segments
      to: agent-footnotes
      type: sequential
    - from: agent-footnotes
      to: agent-legal
      type: sequential
    - from: agent-legal
      to: agent-outlook
      type: sequential
    - from: agent-accounting
      to: agent-esg
      type: sequential
    - from: agent-outlook
      to: agent-brief
      type: sequential
`;


// Export templates with YAML
export const pipelineTemplates: PipelineTemplate[] = [
  {
    id: "pdf-extraction",
    name: "PDF Document Extraction",
    description: "Extract text, tables, and images from PDF documents with Azure Document Intelligence",
    category: "extraction",
    steps: 4,
    estimatedTime: "2-3 min",
    useCases: [
      "Healthcare: Extract patient records, clinical trial data, and medical research papers for EHR systems",
      "Finance: Parse invoices, receipts, and financial reports for automated processing",
      "Legal: Convert contract PDFs and legal documents into structured data",
      "Education: Process academic papers and course materials for digital libraries",
    ],
    features: [
      "Azure Document Intelligence integration",
      "Intelligent table detection",
      "Semantic chunking",
      "Blob storage integration",
    ],
    yaml: pdfExtractionYaml,
    ...createPipelineFromYaml(pdfExtractionYaml),
  },
  {
    id: "article-summarization",
    name: "Article Summarization",
    description: "Automatically summarize articles and extract key points using AI",
    category: "analysis",
    steps: 5,
    estimatedTime: "1-2 min",
    useCases: [
      "Media: Generate article summaries for newsletters and content aggregation",
      "Corporate: Create executive summaries from reports and meeting minutes",
      "Research: Condense research papers and technical documentation",
      "Technology: Generate concise summaries of product updates",
    ],
    features: [
      "AI-powered summarization",
      "Key point extraction",
      "Entity recognition",
      "Parallel processing",
    ],
    yaml: articleSummarizationYaml,
    ...createPipelineFromYaml(articleSummarizationYaml),
  },
  {
    id: "entity-mapping",
    name: "Entity & Knowledge Mapping",
    description: "Extract entities and build knowledge graphs with relationship detection",
    category: "knowledge",
    steps: 5,
    estimatedTime: "3-5 min",
    useCases: [
      "Life Sciences: Build knowledge graphs from research papers for drug discovery",
      "Financial Services: Map company relationships and transactions",
      "Manufacturing: Create supply chain knowledge graphs",
      "Legal: Map legal precedents and regulatory compliance",
    ],
    features: [
      "Named Entity Recognition",
      "Relationship extraction",
      "Knowledge graph generation",
      "Graph export formats",
    ],
    yaml: entityMappingYaml,
    ...createPipelineFromYaml(entityMappingYaml),
  },
  // {
  //   id: "email-content-analysis",
  //   name: "Email Content Analysis",
  //   description: "Analyze email threads to extract action items and sentiment",
  //   category: "analysis",
  //   steps: 6,
  //   estimatedTime: "1-2 min",
  //   useCases: [
  //     "Customer Service: Extract action items and detect sentiment in support emails",
  //     "Sales: Categorize leads and identify high-priority prospects",
  //     "Project Management: Extract tasks and deadlines from project emails",
  //     "HR: Analyze employee communications and prioritize requests",
  //   ],
  //   features: [
  //     "Sentiment analysis",
  //     "Action item extraction",
  //     "Email categorization",
  //     "Priority detection",
  //   ],
  //   yaml: emailAnalysisYaml,
  //   ...createPipelineFromYaml(emailAnalysisYaml),
  // },
  {
    id: "image-content-extraction",
    name: "Image & Visual Content Analysis",
    description: "Extract text from images and analyze visual content using Azure AI",
    category: "extraction",
    steps: 6,
    estimatedTime: "2-4 min",
    useCases: [
      "Healthcare: Digitize handwritten clinical notes and medical imaging reports",
      "Education: Convert handwritten assignments and whiteboard notes",
      "Retail: Extract product information and generate alt-text for images",
      "Real Estate: Extract text from property documents and photos",
    ],
    features: [
      "OCR for images",
      "Visual content analysis",
      "Entity extraction from images",
      "Metadata generation",
    ],
    yaml: imageAnalysisYaml,
    ...createPipelineFromYaml(imageAnalysisYaml),
  },
  {
    id: "gpt-rag-ingestion",
    name: "GPT-RAG Document Ingestion",
    description: "Enterprise RAG pipeline with intelligent chunking and embedding generation",
    category: "extraction",
    steps: 6,
    estimatedTime: "3-5 min",
    useCases: [
      "Enterprise IT: Build knowledge bases from technical documentation",
      "Financial Services: Process regulatory documents for compliance assistants",
      "Healthcare: Index medical guidelines for clinical decision support",
      "Legal: Create searchable repositories of case law and contracts",
    ],
    features: [
      "Multi-format document support",
      "Intelligent chunking strategies",
      "Vector embedding generation",
      "Azure AI Search integration",
    ],
    yaml: ragIngestionYaml,
    ...createPipelineFromYaml(ragIngestionYaml),
  },
  {
    id: "multi-format-processing-python-libs",
    name: "Multi-Format Document Processing (using Python Libraries)",
    description: "Process multiple document formats in parallel with format-specific extractors that use open source Python libraries",
    category: "extraction",
    steps: 7,
    estimatedTime: "3-5 min",
    useCases: [
      "Document Management: Process diverse document types in batch operations",
      "Compliance: Extract data from various format types for regulatory reporting",
      "Knowledge Management: Unified processing of company documentation",
      "Data Migration: Convert legacy documents to modern formats",
    ],
    features: [
      "Parallel format processing",
      "Format-specific extractors",
      "Unified chunking",
      "Batch processing",
    ],
    yaml: multiFormatPyLibsYaml,
    ...createPipelineFromYaml(multiFormatPyLibsYaml),
  },
  {
    id: "multi-format-processing-doc-intell",
    name: "Multi-Format Document Processing (using Document Intelligence)",
    description: "Process multiple document formats with Azure Document Intelligence extractor",
    category: "extraction",
    steps: 7,
    estimatedTime: "3-5 min",
    useCases: [
      "Document Management: Process diverse document types in batch operations",
      "Compliance: Extract data from various format types for regulatory reporting",
      "Knowledge Management: Unified processing of company documentation",
      "Data Migration: Convert legacy documents to modern formats",
    ],
    features: [
      "Multi-format processing",
      "Azure Document Intelligence extractor",
      "Unified field mapping",
      "Batch processing",
    ],
    yaml: multiFormatDocIntelligenceYaml,
    ...createPipelineFromYaml(multiFormatDocIntelligenceYaml),
  },
  {
    id: "multi-format-processing-cu",
    name: "Multi-Format Document Processing (using Content Understanding)",
    description: "Process multiple document formats with Azure Content Understanding extractor",
    category: "extraction",
    steps: 7,
    estimatedTime: "3-5 min",
    useCases: [
      "Document Management: Process diverse document types in batch operations",
      "Compliance: Extract data from various format types for regulatory reporting",
      "Knowledge Management: Unified processing of company documentation",
      "Data Migration: Convert legacy documents to modern formats",
    ],
    features: [
      "Multi-format processing",
      "Azure Content Understanding extractor",
      "Unified field mapping",
      "Batch processing",
    ],
    yaml: multiFormatContentUnderstandingYaml,
    ...createPipelineFromYaml(multiFormatContentUnderstandingYaml),
  },
  {
    id: "content-classification",
    name: "Content Understanding & Classification",
    description: "Analyze documents with AI for comprehensive content understanding",
    category: "analysis",
    steps: 7,
    estimatedTime: "2-3 min",
    useCases: [
      "Document Management: Automatically classify and route documents",
      "Compliance: Identify document types for regulatory compliance",
      "Customer Service: Categorize support documents and correspondence",
      "Legal: Classify legal documents by type and urgency",
    ],
    features: [
      "Document classification",
      "Sentiment analysis",
      "Entity extraction",
      "Keyword extraction",
    ],
    yaml: contentClassificationYaml,
    ...createPipelineFromYaml(contentClassificationYaml),
  },
  {
    id: "pii-detection",
    name: "PII Detection & Redaction",
    description: "Detect and optionally redact sensitive information from documents",
    category: "analysis",
    steps: 5,
    estimatedTime: "1-2 min",
    useCases: [
      "Healthcare: Redact PHI from medical documents for HIPAA compliance",
      "Finance: Remove sensitive financial data from documents",
      "Legal: Redact confidential information from legal documents",
      "HR: Remove PII from employee documents before sharing",
    ],
    features: [
      "PII detection",
      "Automatic redaction",
      "Multiple PII types supported",
      "Compliance reporting",
    ],
    yaml: piiDetectionYaml,
    ...createPipelineFromYaml(piiDetectionYaml),
  },
  {
    id: "language-translation",
    name: "Language Detection & Translation",
    description: "Detect document languages and translate to target languages",
    category: "analysis",
    steps: 5,
    estimatedTime: "2-3 min",
    useCases: [
      "Global Business: Translate business documents for international operations",
      "Customer Service: Translate customer communications across languages",
      "Legal: Translate contracts and legal documents",
      "Education: Translate course materials for multilingual learning",
    ],
    features: [
      "Automatic language detection",
      "High-quality translation",
      "Format preservation",
      "Multi-language support",
    ],
    yaml: translationYaml,
    ...createPipelineFromYaml(translationYaml),
  },
  {
    id: "financial-annual-report-extraction",
    name: "Financial Annual Report KPI + Risk Extraction (Agent Teams)",
    description: "Analyze long-form annual/quarterly reports by splitting responsibilities across specialist agents (KPIs, segments, cash flow, non-GAAP adjustments, accounting policies/estimates, risks, legal contingencies, ESG, and outlook) under a lead coordinator that produces a single evidence-backed executive brief.",
    category: "analysis",
    steps: 18,
    estimatedTime: "5-6 min",
    useCases: [
      "Equity research KPI extraction and summarization",
      "Compliance monitoring of risk disclosures",
      "Corporate strategy competitive benchmarking",
      "Knowledge management (turn narrative reports into structured datasets)",
    ],
    features: [
      "Long-document content understanding",
      "Specialist agent teams for focused extraction tasks",
      "Evidence-backed executive brief synthesis",
      "Azure OpenAI and Content Understanding integration",
    ],
    yaml: financialAnnualReportYaml,
    ...createPipelineFromYaml(financialAnnualReportYaml),
  },
];
