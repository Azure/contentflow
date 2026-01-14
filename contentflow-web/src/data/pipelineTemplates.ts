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

// Template 6: GPT-RAG Document Ingestion
const ragIngestionYaml = `
pipeline:
  name: "GPT-RAG Document Ingestion"
  description: "Enterprise RAG pipeline with intelligent chunking and embedding generation"
  executors:
    - id: blob-input-1
      name: "Source Scanning"
      type: azure_blob_input
      position: { x: 250, y: 50 }
      description: "Discover documents from blob storage"
      settings:
        file_extensions: ".pdf,.docx,.pptx,.xlsx,.jpg,.png"
        
    - id: content-understanding-1
      name: "Content Extraction"
      type: azure_content_understanding_extractor
      position: { x: 250, y: 200 }
      description: "Extract content with Azure Content Understanding"
      settings:
        analyzer: "prebuilt-documentSearch"
        output_content_format: "markdown"
        
    - id: chunker-1
      name: "Smart Chunking"
      type: recursive_text_chunker
      position: { x: 70, y: 370 }
      description: "Apply intelligent chunking strategies"
      settings:
        chunk_size: 1000
        chunk_overlap: 200
        preserve_page_numbers: true
        
    - id: entity-1
      name: "Content Enrichment"
      type: entity_extractor
      position: { x: 400, y: 370 }
      description: "Add metadata and context"
      
    - id: embeddings-1
      name: "Embedding Generation"
      type: azure_openai_embeddings
      position: { x: 250, y: 550 }
      description: "Generate vector embeddings"
      settings:
        model: "text-embedding-3-large"
        dimensions: 1536
        
    - id: search-index-1
      name: "Azure AI Search Indexing"
      type: ai_search_index_output
      position: { x: 500, y: 700 }
      description: "Index chunks for semantic search"
      
  edges:
    - from: blob-input-1
      to: content-understanding-1
      type: sequential
    - from: content-understanding-1
      to: [chunker-1, entity-1]
      type: parallel
    - from: [chunker-1, entity-1]
      to: embeddings-1
      type: join
      wait_strategy: all
    - from: embeddings-1
      to: search-index-1
      type: sequential
`;

// Template 7: Multi-Format Document Processing
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

// Template 8: Multi-Format Document Processing using Azure Document Intelligence
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


// Template 9: Content Understanding & Classification
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

// Template 9: PII Detection & Redaction
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

// Template 10: Language Detection & Translation
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
];
