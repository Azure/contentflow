import { PipelineTemplate } from "@/types/pipeline";

export const pipelineTemplates: PipelineTemplate[] = [
  {
    id: "pdf-extraction",
    name: "PDF Document Extraction",
    description: "Extract text, tables, and images from PDF documents with intelligent structure detection and content organization.",
    category: "extraction",
    steps: 4,
    estimatedTime: "2-3 min",
    useCases: [
      "Extract data from research papers",
      "Parse invoices and receipts",
      "Convert PDF reports to structured data",
    ],
    features: [
      "OCR for scanned documents",
      "Table detection and extraction",
      "Image extraction with metadata",
      "Preserves document hierarchy",
    ],
    nodes: [
      {
        id: "pdf-1",
        type: "executor",
        position: { x: 250, y: 100 },
        data: {
          label: "PDF Upload",
          executor: {
            id: "doc-crack",
            type: "extract",
            name: "Document Cracker",
            color: "bg-primary",
            category: "extract",
          },
          config: {
            name: "PDF Upload",
            description: "Upload and validate PDF documents",
            format: "pdf",
          },
        },
      },
      {
        id: "pdf-2",
        type: "executor",
        position: { x: 250, y: 200 },
        data: {
          label: "Text Extraction",
          executor: {
            id: "doc-crack",
            type: "extract",
            name: "Document Cracker",
            color: "bg-primary",
            category: "extract",
          },
          config: {
            name: "Text Extraction",
            description: "Extract all text content with OCR",
            enableOCR: true,
          },
        },
      },
      {
        id: "pdf-3",
        type: "executor",
        position: { x: 250, y: 300 },
        data: {
          label: "Structure Analysis",
          executor: {
            id: "transform",
            type: "transform",
            name: "Content Transformer",
            color: "bg-secondary",
            category: "transform",
          },
          config: {
            name: "Structure Analysis",
            description: "Detect sections, headers, and hierarchy",
          },
        },
      },
      {
        id: "pdf-4",
        type: "executor",
        position: { x: 250, y: 400 },
        data: {
          label: "Output Formatting",
          executor: {
            id: "transform",
            type: "transform",
            name: "Content Transformer",
            color: "bg-secondary",
            category: "transform",
          },
          config: {
            name: "Output Formatting",
            description: "Convert to JSON/Markdown format",
            outputFormat: "json",
          },
        },
      },
    ],
    edges: [
      { id: "e1-2", source: "pdf-1", target: "pdf-2" },
      { id: "e2-3", source: "pdf-2", target: "pdf-3" },
      { id: "e3-4", source: "pdf-3", target: "pdf-4" },
    ],
  },
  {
    id: "article-summarization",
    name: "Article Summarization",
    description: "Automatically summarize long-form articles, research papers, and blog posts using advanced AI models with key point extraction.",
    category: "analysis",
    steps: 5,
    estimatedTime: "1-2 min",
    useCases: [
      "Summarize news articles for newsletters",
      "Create executive summaries from reports",
      "Generate social media snippets",
    ],
    features: [
      "Multi-level summarization (short/medium/detailed)",
      "Key point extraction",
      "Sentiment analysis",
      "Topic detection",
    ],
    nodes: [
      {
        id: "sum-1",
        type: "executor",
        position: { x: 250, y: 50 },
        data: {
          label: "Content Input",
          executor: {
            id: "doc-crack",
            type: "extract",
            name: "Document Cracker",
            color: "bg-primary",
            category: "extract",
          },
          config: {
            name: "Content Input",
            description: "Accept article URL or text",
          },
        },
      },
      {
        id: "sum-2",
        type: "executor",
        position: { x: 250, y: 150 },
        data: {
          label: "Text Preprocessing",
          executor: {
            id: "transform",
            type: "transform",
            name: "Content Transformer",
            color: "bg-secondary",
            category: "transform",
          },
          config: {
            name: "Text Preprocessing",
            description: "Clean and normalize text",
          },
        },
      },
      {
        id: "sum-3",
        type: "executor",
        position: { x: 150, y: 250 },
        data: {
          label: "AI Summarization",
          executor: {
            id: "summarize",
            type: "analyze",
            name: "AI Summarizer",
            color: "bg-accent",
            category: "analyze",
          },
          config: {
            name: "AI Summarization",
            description: "Generate concise summary",
            model: "gpt-4",
            temperature: 0.3,
          },
        },
      },
      {
        id: "sum-4",
        type: "executor",
        position: { x: 350, y: 250 },
        data: {
          label: "Key Points",
          executor: {
            id: "entity",
            type: "analyze",
            name: "Entity Extractor",
            color: "bg-primary",
            category: "analyze",
          },
          config: {
            name: "Key Points",
            description: "Extract main ideas and facts",
          },
        },
      },
      {
        id: "sum-5",
        type: "executor",
        position: { x: 250, y: 350 },
        data: {
          label: "Format Output",
          executor: {
            id: "transform",
            type: "transform",
            name: "Content Transformer",
            color: "bg-secondary",
            category: "transform",
          },
          config: {
            name: "Format Output",
            description: "Structure summary with metadata",
          },
        },
      },
    ],
    edges: [
      { id: "e1-2", source: "sum-1", target: "sum-2" },
      { id: "e2-3", source: "sum-2", target: "sum-3" },
      { id: "e2-4", source: "sum-2", target: "sum-4" },
      { id: "e3-5", source: "sum-3", target: "sum-5" },
      { id: "e4-5", source: "sum-4", target: "sum-5" },
    ],
  },
  {
    id: "entity-mapping",
    name: "Entity & Knowledge Mapping",
    description: "Extract entities from documents and automatically build knowledge graphs with relationship detection and semantic linking.",
    category: "knowledge",
    steps: 6,
    estimatedTime: "3-5 min",
    useCases: [
      "Build knowledge bases from documentation",
      "Map relationships in research papers",
      "Create organizational charts from text",
    ],
    features: [
      "Named Entity Recognition (NER)",
      "Relationship extraction",
      "Automatic knowledge graph generation",
      "Entity disambiguation",
    ],
    nodes: [
      {
        id: "ent-1",
        type: "executor",
        position: { x: 250, y: 50 },
        data: {
          label: "Document Input",
          executor: {
            id: "doc-crack",
            type: "extract",
            name: "Document Cracker",
            color: "bg-primary",
            category: "extract",
          },
          config: {
            name: "Document Input",
            description: "Process multiple documents",
          },
        },
      },
      {
        id: "ent-2",
        type: "executor",
        position: { x: 250, y: 150 },
        data: {
          label: "Entity Extraction",
          executor: {
            id: "entity",
            type: "analyze",
            name: "Entity Extractor",
            color: "bg-primary",
            category: "analyze",
          },
          config: {
            name: "Entity Extraction",
            description: "Identify people, orgs, concepts",
            model: "gpt-4",
          },
        },
      },
      {
        id: "ent-3",
        type: "executor",
        position: { x: 150, y: 250 },
        data: {
          label: "Relationship Detection",
          executor: {
            id: "entity",
            type: "analyze",
            name: "Entity Extractor",
            color: "bg-primary",
            category: "analyze",
          },
          config: {
            name: "Relationship Detection",
            description: "Find connections between entities",
          },
        },
      },
      {
        id: "ent-4",
        type: "executor",
        position: { x: 350, y: 250 },
        data: {
          label: "Entity Enrichment",
          executor: {
            id: "transform",
            type: "transform",
            name: "Content Transformer",
            color: "bg-secondary",
            category: "transform",
          },
          config: {
            name: "Entity Enrichment",
            description: "Add metadata and context",
          },
        },
      },
      {
        id: "ent-5",
        type: "executor",
        position: { x: 250, y: 350 },
        data: {
          label: "Graph Builder",
          executor: {
            id: "transform",
            type: "transform",
            name: "Content Transformer",
            color: "bg-secondary",
            category: "transform",
          },
          config: {
            name: "Graph Builder",
            description: "Construct knowledge graph",
          },
        },
      },
      {
        id: "ent-6",
        type: "executor",
        position: { x: 250, y: 450 },
        data: {
          label: "Export Graph",
          executor: {
            id: "transform",
            type: "transform",
            name: "Content Transformer",
            color: "bg-secondary",
            category: "transform",
          },
          config: {
            name: "Export Graph",
            description: "Save as Neo4j/JSON format",
            outputFormat: "json",
          },
        },
      },
    ],
    edges: [
      { id: "e1-2", source: "ent-1", target: "ent-2" },
      { id: "e2-3", source: "ent-2", target: "ent-3" },
      { id: "e2-4", source: "ent-2", target: "ent-4" },
      { id: "e3-5", source: "ent-3", target: "ent-5" },
      { id: "e4-5", source: "ent-4", target: "ent-5" },
      { id: "e5-6", source: "ent-5", target: "ent-6" },
    ],
  },
  {
    id: "email-content-analysis",
    name: "Email Content Analysis",
    description: "Analyze email threads to extract action items, sentiment, key topics, and automatically categorize messages.",
    category: "analysis",
    steps: 4,
    estimatedTime: "1-2 min",
    useCases: [
      "Extract tasks from email threads",
      "Analyze customer support sentiment",
      "Auto-categorize incoming emails",
    ],
    features: [
      "Action item extraction",
      "Sentiment scoring",
      "Topic classification",
      "Priority detection",
    ],
    nodes: [
      {
        id: "email-1",
        type: "executor",
        position: { x: 250, y: 100 },
        data: {
          label: "Email Parser",
          executor: {
            id: "doc-crack",
            type: "extract",
            name: "Document Cracker",
            color: "bg-primary",
            category: "extract",
          },
          config: {
            name: "Email Parser",
            description: "Parse email structure and metadata",
          },
        },
      },
      {
        id: "email-2",
        type: "executor",
        position: { x: 250, y: 200 },
        data: {
          label: "Sentiment Analysis",
          executor: {
            id: "summarize",
            type: "analyze",
            name: "AI Summarizer",
            color: "bg-accent",
            category: "analyze",
          },
          config: {
            name: "Sentiment Analysis",
            description: "Detect tone and sentiment",
            model: "gpt-4",
          },
        },
      },
      {
        id: "email-3",
        type: "executor",
        position: { x: 250, y: 300 },
        data: {
          label: "Action Items",
          executor: {
            id: "entity",
            type: "analyze",
            name: "Entity Extractor",
            color: "bg-primary",
            category: "analyze",
          },
          config: {
            name: "Action Items",
            description: "Extract tasks and deadlines",
          },
        },
      },
      {
        id: "email-4",
        type: "executor",
        position: { x: 250, y: 400 },
        data: {
          label: "Categorization",
          executor: {
            id: "transform",
            type: "transform",
            name: "Content Transformer",
            color: "bg-secondary",
            category: "transform",
          },
          config: {
            name: "Categorization",
            description: "Classify and prioritize",
          },
        },
      },
    ],
    edges: [
      { id: "e1-2", source: "email-1", target: "email-2" },
      { id: "e2-3", source: "email-2", target: "email-3" },
      { id: "e3-4", source: "email-3", target: "email-4" },
    ],
  },
  {
    id: "image-content-extraction",
    name: "Image & Visual Content Analysis",
    description: "Extract text from images, analyze visual content, detect objects, and generate descriptive metadata.",
    category: "extraction",
    steps: 5,
    estimatedTime: "2-4 min",
    useCases: [
      "Digitize handwritten notes",
      "Extract text from screenshots",
      "Generate image descriptions for accessibility",
    ],
    features: [
      "OCR for handwritten and printed text",
      "Object detection and labeling",
      "Scene understanding",
      "Metadata generation",
    ],
    nodes: [
      {
        id: "img-1",
        type: "executor",
        position: { x: 250, y: 50 },
        data: {
          label: "Image Upload",
          executor: {
            id: "doc-crack",
            type: "extract",
            name: "Document Cracker",
            color: "bg-primary",
            category: "extract",
          },
          config: {
            name: "Image Upload",
            description: "Accept images in various formats",
          },
        },
      },
      {
        id: "img-2",
        type: "executor",
        position: { x: 150, y: 150 },
        data: {
          label: "OCR Processing",
          executor: {
            id: "doc-crack",
            type: "extract",
            name: "Document Cracker",
            color: "bg-primary",
            category: "extract",
          },
          config: {
            name: "OCR Processing",
            description: "Extract all visible text",
            enableOCR: true,
          },
        },
      },
      {
        id: "img-3",
        type: "executor",
        position: { x: 350, y: 150 },
        data: {
          label: "Visual Analysis",
          executor: {
            id: "summarize",
            type: "analyze",
            name: "AI Summarizer",
            color: "bg-accent",
            category: "analyze",
          },
          config: {
            name: "Visual Analysis",
            description: "Detect objects and scenes",
            model: "gpt-4",
          },
        },
      },
      {
        id: "img-4",
        type: "executor",
        position: { x: 250, y: 250 },
        data: {
          label: "Entity Extraction",
          executor: {
            id: "entity",
            type: "analyze",
            name: "Entity Extractor",
            color: "bg-primary",
            category: "analyze",
          },
          config: {
            name: "Entity Extraction",
            description: "Extract structured data",
          },
        },
      },
      {
        id: "img-5",
        type: "executor",
        position: { x: 250, y: 350 },
        data: {
          label: "Metadata Builder",
          executor: {
            id: "transform",
            type: "transform",
            name: "Content Transformer",
            color: "bg-secondary",
            category: "transform",
          },
          config: {
            name: "Metadata Builder",
            description: "Generate comprehensive metadata",
          },
        },
      },
    ],
    edges: [
      { id: "e1-2", source: "img-1", target: "img-2" },
      { id: "e1-3", source: "img-1", target: "img-3" },
      { id: "e2-4", source: "img-2", target: "img-4" },
      { id: "e3-4", source: "img-3", target: "img-4" },
      { id: "e4-5", source: "img-4", target: "img-5" },
    ],
  },
  {
    id: "research-synthesis",
    name: "Research Paper Synthesis",
    description: "Process multiple research papers to extract methodologies, findings, citations, and synthesize a comprehensive literature review.",
    category: "knowledge",
    steps: 7,
    estimatedTime: "5-8 min",
    useCases: [
      "Generate literature reviews",
      "Compare research methodologies",
      "Build citation networks",
    ],
    features: [
      "Citation extraction and linking",
      "Methodology comparison",
      "Key findings summarization",
      "Research gap identification",
    ],
    nodes: [
      {
        id: "res-1",
        type: "executor",
        position: { x: 250, y: 50 },
        data: {
          label: "Paper Collection",
          executor: {
            id: "doc-crack",
            type: "extract",
            name: "Document Cracker",
            color: "bg-primary",
            category: "extract",
          },
          config: {
            name: "Paper Collection",
            description: "Upload multiple research papers",
          },
        },
      },
      {
        id: "res-2",
        type: "subworkflow",
        position: { x: 250, y: 150 },
        data: {
          label: "Paper Analysis Pipeline",
          executor: {
            id: "subworkflow",
            type: "workflow",
            name: "Sub-Workflow",
            color: "bg-gradient-primary",
            category: "workflow",
          },
          config: {
            name: "Paper Analysis Pipeline",
            description: "Process each paper independently",
            steps: 4,
          },
        },
      },
      {
        id: "res-3",
        type: "executor",
        position: { x: 150, y: 250 },
        data: {
          label: "Citation Network",
          executor: {
            id: "entity",
            type: "analyze",
            name: "Entity Extractor",
            color: "bg-primary",
            category: "analyze",
          },
          config: {
            name: "Citation Network",
            description: "Build citation graph",
          },
        },
      },
      {
        id: "res-4",
        type: "executor",
        position: { x: 350, y: 250 },
        data: {
          label: "Findings Extraction",
          executor: {
            id: "entity",
            type: "analyze",
            name: "Entity Extractor",
            color: "bg-primary",
            category: "analyze",
          },
          config: {
            name: "Findings Extraction",
            description: "Extract key results and conclusions",
          },
        },
      },
      {
        id: "res-5",
        type: "executor",
        position: { x: 250, y: 350 },
        data: {
          label: "Cross-Paper Analysis",
          executor: {
            id: "summarize",
            type: "analyze",
            name: "AI Summarizer",
            color: "bg-accent",
            category: "analyze",
          },
          config: {
            name: "Cross-Paper Analysis",
            description: "Compare and contrast findings",
            model: "gpt-4",
          },
        },
      },
      {
        id: "res-6",
        type: "executor",
        position: { x: 250, y: 450 },
        data: {
          label: "Synthesis Generator",
          executor: {
            id: "summarize",
            type: "analyze",
            name: "AI Summarizer",
            color: "bg-accent",
            category: "analyze",
          },
          config: {
            name: "Synthesis Generator",
            description: "Create literature review",
            model: "gpt-4",
            temperature: 0.5,
          },
        },
      },
      {
        id: "res-7",
        type: "executor",
        position: { x: 250, y: 550 },
        data: {
          label: "Knowledge Graph Export",
          executor: {
            id: "transform",
            type: "transform",
            name: "Content Transformer",
            color: "bg-secondary",
            category: "transform",
          },
          config: {
            name: "Knowledge Graph Export",
            description: "Export comprehensive knowledge graph",
          },
        },
      },
    ],
    edges: [
      { id: "e1-2", source: "res-1", target: "res-2" },
      { id: "e2-3", source: "res-2", target: "res-3" },
      { id: "e2-4", source: "res-2", target: "res-4" },
      { id: "e3-5", source: "res-3", target: "res-5" },
      { id: "e4-5", source: "res-4", target: "res-5" },
      { id: "e5-6", source: "res-5", target: "res-6" },
      { id: "e6-7", source: "res-6", target: "res-7" },
    ],
  },
  {
    id: "gpt-rag-ingestion",
    name: "GPT-RAG Document Ingestion",
    description: "Enterprise-grade RAG ingestion pipeline for processing diverse documents with intelligent chunking, embedding generation, and Azure AI Search indexing.",
    category: "extraction",
    steps: 6,
    estimatedTime: "3-5 min",
    useCases: [
      "Build searchable knowledge bases from enterprise documents",
      "Process multi-format content for AI-powered chat",
      "Create embeddings for semantic search",
    ],
    features: [
      "Multi-format support (PDF, DOCX, PPTX, images, spreadsheets)",
      "Intelligent chunking strategies per format",
      "Text and image embedding generation",
      "Azure AI Search integration",
    ],
    nodes: [
      {
        id: "rag-1",
        type: "executor",
        position: { x: 250, y: 50 },
        data: {
          label: "Source Scanning",
          executor: {
            id: "doc-crack",
            type: "extract",
            name: "Document Cracker",
            color: "bg-primary",
            category: "extract",
          },
          config: {
            name: "Source Scanning",
            description: "Detect new/updated content from Blob Storage or SharePoint",
          },
        },
      },
      {
        id: "rag-2",
        type: "executor",
        position: { x: 250, y: 150 },
        data: {
          label: "Document Intelligence",
          executor: {
            id: "doc-crack",
            type: "extract",
            name: "Document Cracker",
            color: "bg-primary",
            category: "extract",
          },
          config: {
            name: "Document Intelligence",
            description: "Extract structured content with Azure Document Intelligence",
            enableOCR: true,
          },
        },
      },
      {
        id: "rag-3",
        type: "executor",
        position: { x: 150, y: 250 },
        data: {
          label: "Smart Chunking",
          executor: {
            id: "transform",
            type: "transform",
            name: "Content Transformer",
            color: "bg-secondary",
            category: "transform",
          },
          config: {
            name: "Smart Chunking",
            description: "Apply format-specific chunking strategies",
          },
        },
      },
      {
        id: "rag-4",
        type: "executor",
        position: { x: 350, y: 250 },
        data: {
          label: "Enrichment",
          executor: {
            id: "entity",
            type: "analyze",
            name: "Entity Extractor",
            color: "bg-primary",
            category: "analyze",
          },
          config: {
            name: "Enrichment",
            description: "Add metadata and context to chunks",
          },
        },
      },
      {
        id: "rag-5",
        type: "executor",
        position: { x: 250, y: 350 },
        data: {
          label: "Embedding Generation",
          executor: {
            id: "summarize",
            type: "analyze",
            name: "AI Summarizer",
            color: "bg-accent",
            category: "analyze",
          },
          config: {
            name: "Embedding Generation",
            description: "Generate text and image embeddings",
            model: "text-embedding-3-large",
          },
        },
      },
      {
        id: "rag-6",
        type: "executor",
        position: { x: 250, y: 450 },
        data: {
          label: "Azure AI Search Indexing",
          executor: {
            id: "transform",
            type: "transform",
            name: "Content Transformer",
            color: "bg-secondary",
            category: "transform",
          },
          config: {
            name: "Azure AI Search Indexing",
            description: "Index processed chunks for retrieval",
          },
        },
      },
    ],
    edges: [
      { id: "e1-2", source: "rag-1", target: "rag-2" },
      { id: "e2-3", source: "rag-2", target: "rag-3" },
      { id: "e2-4", source: "rag-2", target: "rag-4" },
      { id: "e3-5", source: "rag-3", target: "rag-5" },
      { id: "e4-5", source: "rag-4", target: "rag-5" },
      { id: "e5-6", source: "rag-5", target: "rag-6" },
    ],
  },
  {
    id: "video-transcript-analysis",
    name: "Video Transcript Processing",
    description: "Extract, analyze, and index video transcripts with speaker identification, topic segmentation, and searchable timestamps.",
    category: "extraction",
    steps: 5,
    estimatedTime: "4-6 min",
    useCases: [
      "Create searchable video libraries",
      "Generate meeting summaries from recordings",
      "Extract insights from educational content",
    ],
    features: [
      "VTT/SRT transcript parsing",
      "Speaker diarization",
      "Topic segmentation by time",
      "Key moment extraction",
    ],
    nodes: [
      {
        id: "vid-1",
        type: "executor",
        position: { x: 250, y: 50 },
        data: {
          label: "Transcript Upload",
          executor: {
            id: "doc-crack",
            type: "extract",
            name: "Document Cracker",
            color: "bg-primary",
            category: "extract",
          },
          config: {
            name: "Transcript Upload",
            description: "Accept VTT/SRT transcript files",
            format: "vtt",
          },
        },
      },
      {
        id: "vid-2",
        type: "executor",
        position: { x: 250, y: 150 },
        data: {
          label: "Time-based Chunking",
          executor: {
            id: "transform",
            type: "transform",
            name: "Content Transformer",
            color: "bg-secondary",
            category: "transform",
          },
          config: {
            name: "Time-based Chunking",
            description: "Split content by time codes and scenes",
          },
        },
      },
      {
        id: "vid-3",
        type: "executor",
        position: { x: 250, y: 250 },
        data: {
          label: "Topic Detection",
          executor: {
            id: "summarize",
            type: "analyze",
            name: "AI Summarizer",
            color: "bg-accent",
            category: "analyze",
          },
          config: {
            name: "Topic Detection",
            description: "Identify topics and themes per segment",
            model: "gpt-4",
          },
        },
      },
      {
        id: "vid-4",
        type: "executor",
        position: { x: 250, y: 350 },
        data: {
          label: "Key Moments",
          executor: {
            id: "entity",
            type: "analyze",
            name: "Entity Extractor",
            color: "bg-primary",
            category: "analyze",
          },
          config: {
            name: "Key Moments",
            description: "Extract important quotes and decisions",
          },
        },
      },
      {
        id: "vid-5",
        type: "executor",
        position: { x: 250, y: 450 },
        data: {
          label: "Searchable Index",
          executor: {
            id: "transform",
            type: "transform",
            name: "Content Transformer",
            color: "bg-secondary",
            category: "transform",
          },
          config: {
            name: "Searchable Index",
            description: "Create timestamp-linked index",
          },
        },
      },
    ],
    edges: [
      { id: "e1-2", source: "vid-1", target: "vid-2" },
      { id: "e2-3", source: "vid-2", target: "vid-3" },
      { id: "e3-4", source: "vid-3", target: "vid-4" },
      { id: "e4-5", source: "vid-4", target: "vid-5" },
    ],
  },
  {
    id: "spreadsheet-data-pipeline",
    name: "Spreadsheet Data Processing",
    description: "Process Excel/CSV files with schema detection, data validation, transformation, and structured output generation.",
    category: "extraction",
    steps: 5,
    estimatedTime: "2-3 min",
    useCases: [
      "Clean and validate customer data imports",
      "Transform financial reports",
      "Normalize multi-sheet datasets",
    ],
    features: [
      "Automatic schema detection",
      "Data type validation",
      "Missing value handling",
      "Multi-sheet processing",
    ],
    nodes: [
      {
        id: "sheet-1",
        type: "executor",
        position: { x: 250, y: 50 },
        data: {
          label: "File Upload",
          executor: {
            id: "doc-crack",
            type: "extract",
            name: "Document Cracker",
            color: "bg-primary",
            category: "extract",
          },
          config: {
            name: "File Upload",
            description: "Accept XLSX/CSV files",
            format: "xlsx",
          },
        },
      },
      {
        id: "sheet-2",
        type: "executor",
        position: { x: 250, y: 150 },
        data: {
          label: "Schema Detection",
          executor: {
            id: "entity",
            type: "analyze",
            name: "Entity Extractor",
            color: "bg-primary",
            category: "analyze",
          },
          config: {
            name: "Schema Detection",
            description: "Identify columns, types, and relationships",
          },
        },
      },
      {
        id: "sheet-3",
        type: "executor",
        position: { x: 250, y: 250 },
        data: {
          label: "Data Validation",
          executor: {
            id: "transform",
            type: "transform",
            name: "Content Transformer",
            color: "bg-secondary",
            category: "transform",
          },
          config: {
            name: "Data Validation",
            description: "Check data quality and constraints",
          },
        },
      },
      {
        id: "sheet-4",
        type: "executor",
        position: { x: 250, y: 350 },
        data: {
          label: "Transformation",
          executor: {
            id: "transform",
            type: "transform",
            name: "Content Transformer",
            color: "bg-secondary",
            category: "transform",
          },
          config: {
            name: "Transformation",
            description: "Clean, normalize, and enrich data",
          },
        },
      },
      {
        id: "sheet-5",
        type: "executor",
        position: { x: 250, y: 450 },
        data: {
          label: "Structured Output",
          executor: {
            id: "transform",
            type: "transform",
            name: "Content Transformer",
            color: "bg-secondary",
            category: "transform",
          },
          config: {
            name: "Structured Output",
            description: "Export as JSON/Parquet/SQL",
            outputFormat: "json",
          },
        },
      },
    ],
    edges: [
      { id: "e1-2", source: "sheet-1", target: "sheet-2" },
      { id: "e2-3", source: "sheet-2", target: "sheet-3" },
      { id: "e3-4", source: "sheet-3", target: "sheet-4" },
      { id: "e4-5", source: "sheet-4", target: "sheet-5" },
    ],
  },
  {
    id: "social-media-monitoring",
    name: "Social Media Content Analysis",
    description: "Monitor and analyze social media posts with sentiment tracking, trend detection, and automated reporting.",
    category: "analysis",
    steps: 6,
    estimatedTime: "2-4 min",
    useCases: [
      "Track brand mentions and sentiment",
      "Identify trending topics",
      "Monitor competitor activity",
    ],
    features: [
      "Multi-platform aggregation",
      "Real-time sentiment analysis",
      "Trend and hashtag tracking",
      "Influencer identification",
    ],
    nodes: [
      {
        id: "social-1",
        type: "executor",
        position: { x: 250, y: 50 },
        data: {
          label: "Content Collection",
          executor: {
            id: "doc-crack",
            type: "extract",
            name: "Document Cracker",
            color: "bg-primary",
            category: "extract",
          },
          config: {
            name: "Content Collection",
            description: "Aggregate posts from multiple platforms",
          },
        },
      },
      {
        id: "social-2",
        type: "executor",
        position: { x: 150, y: 150 },
        data: {
          label: "Sentiment Analysis",
          executor: {
            id: "summarize",
            type: "analyze",
            name: "AI Summarizer",
            color: "bg-accent",
            category: "analyze",
          },
          config: {
            name: "Sentiment Analysis",
            description: "Score sentiment per post",
            model: "gpt-4",
          },
        },
      },
      {
        id: "social-3",
        type: "executor",
        position: { x: 350, y: 150 },
        data: {
          label: "Entity Extraction",
          executor: {
            id: "entity",
            type: "analyze",
            name: "Entity Extractor",
            color: "bg-primary",
            category: "analyze",
          },
          config: {
            name: "Entity Extraction",
            description: "Identify brands, people, and topics",
          },
        },
      },
      {
        id: "social-4",
        type: "executor",
        position: { x: 250, y: 250 },
        data: {
          label: "Trend Detection",
          executor: {
            id: "summarize",
            type: "analyze",
            name: "AI Summarizer",
            color: "bg-accent",
            category: "analyze",
          },
          config: {
            name: "Trend Detection",
            description: "Identify emerging patterns and topics",
            model: "gpt-4",
          },
        },
      },
      {
        id: "social-5",
        type: "executor",
        position: { x: 250, y: 350 },
        data: {
          label: "Insights Generation",
          executor: {
            id: "summarize",
            type: "analyze",
            name: "AI Summarizer",
            color: "bg-accent",
            category: "analyze",
          },
          config: {
            name: "Insights Generation",
            description: "Generate actionable insights",
            model: "gpt-4",
          },
        },
      },
      {
        id: "social-6",
        type: "executor",
        position: { x: 250, y: 450 },
        data: {
          label: "Report Builder",
          executor: {
            id: "transform",
            type: "transform",
            name: "Content Transformer",
            color: "bg-secondary",
            category: "transform",
          },
          config: {
            name: "Report Builder",
            description: "Create visual dashboards and alerts",
          },
        },
      },
    ],
    edges: [
      { id: "e1-2", source: "social-1", target: "social-2" },
      { id: "e1-3", source: "social-1", target: "social-3" },
      { id: "e2-4", source: "social-2", target: "social-4" },
      { id: "e3-4", source: "social-3", target: "social-4" },
      { id: "e4-5", source: "social-4", target: "social-5" },
      { id: "e5-6", source: "social-5", target: "social-6" },
    ],
  },
  {
    id: "contract-review",
    name: "Legal Contract Review",
    description: "Automated contract analysis with clause extraction, risk assessment, obligation tracking, and compliance checking.",
    category: "analysis",
    steps: 6,
    estimatedTime: "3-5 min",
    useCases: [
      "Review vendor contracts",
      "Extract key terms and obligations",
      "Identify non-standard clauses",
    ],
    features: [
      "Clause type identification",
      "Risk scoring",
      "Obligation and deadline tracking",
      "Template compliance checking",
    ],
    nodes: [
      {
        id: "contract-1",
        type: "executor",
        position: { x: 250, y: 50 },
        data: {
          label: "Document Upload",
          executor: {
            id: "doc-crack",
            type: "extract",
            name: "Document Cracker",
            color: "bg-primary",
            category: "extract",
          },
          config: {
            name: "Document Upload",
            description: "Process PDF/DOCX contracts",
            format: "pdf",
            enableOCR: true,
          },
        },
      },
      {
        id: "contract-2",
        type: "executor",
        position: { x: 250, y: 150 },
        data: {
          label: "Clause Extraction",
          executor: {
            id: "entity",
            type: "analyze",
            name: "Entity Extractor",
            color: "bg-primary",
            category: "analyze",
          },
          config: {
            name: "Clause Extraction",
            description: "Identify and categorize contract clauses",
          },
        },
      },
      {
        id: "contract-3",
        type: "executor",
        position: { x: 150, y: 250 },
        data: {
          label: "Risk Assessment",
          executor: {
            id: "summarize",
            type: "analyze",
            name: "AI Summarizer",
            color: "bg-accent",
            category: "analyze",
          },
          config: {
            name: "Risk Assessment",
            description: "Score risk level of clauses",
            model: "gpt-4",
            temperature: 0.2,
          },
        },
      },
      {
        id: "contract-4",
        type: "executor",
        position: { x: 350, y: 250 },
        data: {
          label: "Obligation Tracker",
          executor: {
            id: "entity",
            type: "analyze",
            name: "Entity Extractor",
            color: "bg-primary",
            category: "analyze",
          },
          config: {
            name: "Obligation Tracker",
            description: "Extract obligations and deadlines",
          },
        },
      },
      {
        id: "contract-5",
        type: "executor",
        position: { x: 250, y: 350 },
        data: {
          label: "Compliance Check",
          executor: {
            id: "summarize",
            type: "analyze",
            name: "AI Summarizer",
            color: "bg-accent",
            category: "analyze",
          },
          config: {
            name: "Compliance Check",
            description: "Compare against standard templates",
            model: "gpt-4",
          },
        },
      },
      {
        id: "contract-6",
        type: "executor",
        position: { x: 250, y: 450 },
        data: {
          label: "Review Report",
          executor: {
            id: "transform",
            type: "transform",
            name: "Content Transformer",
            color: "bg-secondary",
            category: "transform",
          },
          config: {
            name: "Review Report",
            description: "Generate comprehensive review summary",
            outputFormat: "json",
          },
        },
      },
    ],
    edges: [
      { id: "e1-2", source: "contract-1", target: "contract-2" },
      { id: "e2-3", source: "contract-2", target: "contract-3" },
      { id: "e2-4", source: "contract-2", target: "contract-4" },
      { id: "e3-5", source: "contract-3", target: "contract-5" },
      { id: "e4-5", source: "contract-4", target: "contract-5" },
      { id: "e5-6", source: "contract-5", target: "contract-6" },
    ],
  },
  {
    id: "multilingual-translation",
    name: "Multilingual Content Translation",
    description: "Translate documents across multiple languages while preserving formatting, context, and domain-specific terminology.",
    category: "analysis",
    steps: 5,
    estimatedTime: "2-4 min",
    useCases: [
      "Translate product documentation",
      "Localize marketing content",
      "Create multilingual knowledge bases",
    ],
    features: [
      "Context-aware translation",
      "Terminology consistency",
      "Format preservation",
      "Quality scoring",
    ],
    nodes: [
      {
        id: "trans-1",
        type: "executor",
        position: { x: 250, y: 50 },
        data: {
          label: "Source Document",
          executor: {
            id: "doc-crack",
            type: "extract",
            name: "Document Cracker",
            color: "bg-primary",
            category: "extract",
          },
          config: {
            name: "Source Document",
            description: "Extract content with structure preservation",
          },
        },
      },
      {
        id: "trans-2",
        type: "executor",
        position: { x: 250, y: 150 },
        data: {
          label: "Terminology Extraction",
          executor: {
            id: "entity",
            type: "analyze",
            name: "Entity Extractor",
            color: "bg-primary",
            category: "analyze",
          },
          config: {
            name: "Terminology Extraction",
            description: "Identify domain-specific terms",
          },
        },
      },
      {
        id: "trans-3",
        type: "executor",
        position: { x: 250, y: 250 },
        data: {
          label: "AI Translation",
          executor: {
            id: "summarize",
            type: "analyze",
            name: "AI Summarizer",
            color: "bg-accent",
            category: "analyze",
          },
          config: {
            name: "AI Translation",
            description: "Translate with context awareness",
            model: "gpt-4",
            temperature: 0.3,
          },
        },
      },
      {
        id: "trans-4",
        type: "executor",
        position: { x: 250, y: 350 },
        data: {
          label: "Quality Check",
          executor: {
            id: "summarize",
            type: "analyze",
            name: "AI Summarizer",
            color: "bg-accent",
            category: "analyze",
          },
          config: {
            name: "Quality Check",
            description: "Validate translation accuracy",
            model: "gpt-4",
          },
        },
      },
      {
        id: "trans-5",
        type: "executor",
        position: { x: 250, y: 450 },
        data: {
          label: "Format Reconstruction",
          executor: {
            id: "transform",
            type: "transform",
            name: "Content Transformer",
            color: "bg-secondary",
            category: "transform",
          },
          config: {
            name: "Format Reconstruction",
            description: "Rebuild original formatting",
          },
        },
      },
    ],
    edges: [
      { id: "e1-2", source: "trans-1", target: "trans-2" },
      { id: "e2-3", source: "trans-2", target: "trans-3" },
      { id: "e3-4", source: "trans-3", target: "trans-4" },
      { id: "e4-5", source: "trans-4", target: "trans-5" },
    ],
  },
  {
    id: "enterprise-rag-pipeline",
    name: "Enterprise RAG Document Pipeline",
    description: "Complete RAG ingestion pipeline for enterprise documents with Azure AI Search indexing, intelligent chunking, and embeddings generation.",
    category: "extraction",
    steps: 7,
    estimatedTime: "5-8 min",
    useCases: [
      "Build enterprise knowledge bases from documents",
      "Index corporate documentation for AI chat",
      "Create searchable document repositories",
    ],
    features: [
      "Azure Blob Storage integration",
      "Document Intelligence extraction",
      "Recursive text chunking for optimal retrieval",
      "Vector embeddings with Azure OpenAI",
      "Azure AI Search indexing",
    ],
    nodes: [
      {
        id: "rag-1",
        type: "executor",
        position: { x: 250, y: 50 },
        data: {
          label: "Blob Storage Input",
          executor: {
            id: "azure_blob_input",
            type: "input",
            name: "Azure Blob Input",
            color: "bg-blue-500",
            category: "input",
          },
          config: {
            name: "Blob Storage Input",
            description: "Discover documents from Azure Blob Storage",
            file_extensions: [".pdf", ".docx", ".pptx", ".xlsx"],
          },
        },
      },
      {
        id: "rag-2",
        type: "executor",
        position: { x: 250, y: 150 },
        data: {
          label: "Content Retrieval",
          executor: {
            id: "content_retriever",
            type: "input",
            name: "Content Retriever",
            color: "bg-blue-500",
            category: "input",
          },
          config: {
            name: "Content Retrieval",
            description: "Download document content",
            use_temp_file_for_content: true,
          },
        },
      },
      {
        id: "rag-3",
        type: "executor",
        position: { x: 250, y: 250 },
        data: {
          label: "Document Intelligence",
          executor: {
            id: "azure_document_intelligence_extractor",
            type: "extract",
            name: "Document Intelligence",
            color: "bg-primary",
            category: "extract",
          },
          config: {
            name: "Document Intelligence",
            description: "Extract structured content with Azure AI",
            model_id: "prebuilt-layout",
            extract_text: true,
            extract_tables: true,
          },
        },
      },
      {
        id: "rag-4",
        type: "executor",
        position: { x: 250, y: 350 },
        data: {
          label: "Recursive Chunking",
          executor: {
            id: "recursive_text_chunker_executor",
            type: "transform",
            name: "Text Chunker",
            color: "bg-secondary",
            category: "transform",
          },
          config: {
            name: "Recursive Chunking",
            description: "Smart chunking for optimal RAG retrieval",
            chunk_size: 1000,
            chunk_overlap: 200,
          },
        },
      },
      {
        id: "rag-5",
        type: "executor",
        position: { x: 250, y: 450 },
        data: {
          label: "Generate Embeddings",
          executor: {
            id: "azure_openai_embeddings_executor",
            type: "analyze",
            name: "Embeddings Generator",
            color: "bg-accent",
            category: "analyze",
          },
          config: {
            name: "Generate Embeddings",
            description: "Create vector embeddings for semantic search",
            deployment_name: "text-embedding-3-large",
          },
        },
      },
      {
        id: "rag-6",
        type: "executor",
        position: { x: 250, y: 550 },
        data: {
          label: "AI Search Indexing",
          executor: {
            id: "ai_search_index_writer",
            type: "output",
            name: "AI Search Writer",
            color: "bg-green-500",
            category: "output",
          },
          config: {
            name: "AI Search Indexing",
            description: "Index to Azure AI Search",
            index_mode: "chunks",
            batch_size: 100,
          },
        },
      },
    ],
    edges: [
      { id: "e1-2", source: "rag-1", target: "rag-2" },
      { id: "e2-3", source: "rag-2", target: "rag-3" },
      { id: "e3-4", source: "rag-3", target: "rag-4" },
      { id: "e4-5", source: "rag-4", target: "rag-5" },
      { id: "e5-6", source: "rag-5", target: "rag-6" },
    ],
  },
  {
    id: "multimodal-rag-pipeline",
    name: "Multi-Modal RAG Pipeline",
    description: "Advanced RAG pipeline that processes text, images, tables, and figures from documents for comprehensive multi-modal search.",
    category: "extraction",
    steps: 8,
    estimatedTime: "6-10 min",
    useCases: [
      "Index technical documentation with diagrams",
      "Process research papers with charts and graphs",
      "Build searchable product catalogs with images",
    ],
    features: [
      "Content Understanding with 70+ analyzers",
      "Image and figure extraction",
      "Table detection and processing",
      "Multi-modal embeddings (text + images)",
      "Advanced AI Search integration",
    ],
    nodes: [
      {
        id: "mm-1",
        type: "executor",
        position: { x: 250, y: 50 },
        data: {
          label: "Document Discovery",
          executor: {
            id: "azure_blob_input",
            type: "input",
            name: "Azure Blob Input",
            color: "bg-blue-500",
            category: "input",
          },
          config: {
            name: "Document Discovery",
            description: "Scan blob storage for multi-modal content",
          },
        },
      },
      {
        id: "mm-2",
        type: "executor",
        position: { x: 250, y: 150 },
        data: {
          label: "Content Retrieval",
          executor: {
            id: "content_retriever",
            type: "input",
            name: "Content Retriever",
            color: "bg-blue-500",
            category: "input",
          },
          config: {
            name: "Content Retrieval",
            description: "Download documents and assets",
          },
        },
      },
      {
        id: "mm-3",
        type: "executor",
        position: { x: 250, y: 250 },
        data: {
          label: "Content Understanding",
          executor: {
            id: "azure_content_understanding_extractor",
            type: "extract",
            name: "Content Understanding",
            color: "bg-primary",
            category: "extract",
          },
          config: {
            name: "Content Understanding",
            description: "Extract text, images, tables, and figures",
            analyzer_id: "prebuilt-documentSearch",
            extract_text: true,
            extract_markdown: true,
            extract_tables: true,
            extract_figures: true,
          },
        },
      },
      {
        id: "mm-4",
        type: "executor",
        position: { x: 150, y: 350 },
        data: {
          label: "Text Chunking",
          executor: {
            id: "recursive_text_chunker_executor",
            type: "transform",
            name: "Text Chunker",
            color: "bg-secondary",
            category: "transform",
          },
          config: {
            name: "Text Chunking",
            description: "Chunk text content optimally",
          },
        },
      },
      {
        id: "mm-5",
        type: "executor",
        position: { x: 350, y: 350 },
        data: {
          label: "Entity Extraction",
          executor: {
            id: "entity_extraction_executor",
            type: "analyze",
            name: "Entity Extractor",
            color: "bg-accent",
            category: "analyze",
          },
          config: {
            name: "Entity Extraction",
            description: "Extract entities from images and tables",
          },
        },
      },
      {
        id: "mm-6",
        type: "executor",
        position: { x: 250, y: 450 },
        data: {
          label: "Text Embeddings",
          executor: {
            id: "azure_openai_embeddings_executor",
            type: "analyze",
            name: "Text Embeddings",
            color: "bg-accent",
            category: "analyze",
          },
          config: {
            name: "Text Embeddings",
            description: "Generate text embeddings",
            deployment_name: "text-embedding-3-large",
          },
        },
      },
      {
        id: "mm-7",
        type: "executor",
        position: { x: 250, y: 550 },
        data: {
          label: "AI Search Index",
          executor: {
            id: "ai_search_index_writer",
            type: "output",
            name: "AI Search Writer",
            color: "bg-green-500",
            category: "output",
          },
          config: {
            name: "AI Search Index",
            description: "Index multi-modal content",
            index_mode: "chunks",
          },
        },
      },
    ],
    edges: [
      { id: "e1-2", source: "mm-1", target: "mm-2" },
      { id: "e2-3", source: "mm-2", target: "mm-3" },
      { id: "e3-4", source: "mm-3", target: "mm-4" },
      { id: "e3-5", source: "mm-3", target: "mm-5" },
      { id: "e4-6", source: "mm-4", target: "mm-6" },
      { id: "e5-6", source: "mm-5", target: "mm-6" },
      { id: "e6-7", source: "mm-6", target: "mm-7" },
    ],
  },
  {
    id: "financial-document-analysis",
    name: "Financial Document Analysis",
    description: "Industry-specific pipeline for processing financial documents like invoices, bank statements, and tax forms with specialized extractors.",
    category: "analysis",
    steps: 6,
    estimatedTime: "4-6 min",
    useCases: [
      "Process invoices and receipts at scale",
      "Extract data from bank statements",
      "Analyze tax forms and financial reports",
    ],
    features: [
      "Prebuilt financial document analyzers",
      "PII detection and redaction",
      "Entity extraction for financial data",
      "Compliance-ready data extraction",
    ],
    nodes: [
      {
        id: "fin-1",
        type: "executor",
        position: { x: 250, y: 50 },
        data: {
          label: "Document Upload",
          executor: {
            id: "content_retriever",
            type: "input",
            name: "Content Retriever",
            color: "bg-blue-500",
            category: "input",
          },
          config: {
            name: "Document Upload",
            description: "Load financial documents",
          },
        },
      },
      {
        id: "fin-2",
        type: "executor",
        position: { x: 250, y: 150 },
        data: {
          label: "Content Understanding",
          executor: {
            id: "azure_content_understanding_extractor",
            type: "extract",
            name: "Content Understanding",
            color: "bg-primary",
            category: "extract",
          },
          config: {
            name: "Content Understanding",
            description: "Extract with financial analyzers",
            analyzer_id: "prebuilt-invoice",
          },
        },
      },
      {
        id: "fin-3",
        type: "executor",
        position: { x: 250, y: 250 },
        data: {
          label: "Entity Extraction",
          executor: {
            id: "entity_extraction_executor",
            type: "analyze",
            name: "Entity Extractor",
            color: "bg-accent",
            category: "analyze",
          },
          config: {
            name: "Entity Extraction",
            description: "Extract financial entities",
            entity_types: ["money", "date", "organization", "quantity"],
          },
        },
      },
      {
        id: "fin-4",
        type: "executor",
        position: { x: 250, y: 350 },
        data: {
          label: "PII Detection",
          executor: {
            id: "pii_detector_executor",
            type: "analyze",
            name: "PII Detector",
            color: "bg-accent",
            category: "analyze",
          },
          config: {
            name: "PII Detection",
            description: "Detect and redact sensitive data",
            pii_types: ["ssn", "credit_card", "email", "phone"],
            action: "redact",
          },
        },
      },
      {
        id: "fin-5",
        type: "executor",
        position: { x: 250, y: 450 },
        data: {
          label: "Classification",
          executor: {
            id: "content_classifier_executor",
            type: "analyze",
            name: "Classifier",
            color: "bg-accent",
            category: "analyze",
          },
          config: {
            name: "Classification",
            description: "Categorize financial documents",
            categories: ["invoice", "receipt", "statement", "tax_form"],
          },
        },
      },
      {
        id: "fin-6",
        type: "executor",
        position: { x: 250, y: 550 },
        data: {
          label: "Index Results",
          executor: {
            id: "ai_search_index_writer",
            type: "output",
            name: "AI Search Writer",
            color: "bg-green-500",
            category: "output",
          },
          config: {
            name: "Index Results",
            description: "Store processed financial data",
          },
        },
      },
    ],
    edges: [
      { id: "e1-2", source: "fin-1", target: "fin-2" },
      { id: "e2-3", source: "fin-2", target: "fin-3" },
      { id: "e3-4", source: "fin-3", target: "fin-4" },
      { id: "e4-5", source: "fin-4", target: "fin-5" },
      { id: "e5-6", source: "fin-5", target: "fin-6" },
    ],
  },
  {
    id: "healthcare-document-processing",
    name: "Healthcare Document Processing",
    description: "HIPAA-compliant pipeline for processing medical records, prescriptions, and healthcare documents with PII protection.",
    category: "analysis",
    steps: 7,
    estimatedTime: "5-8 min",
    useCases: [
      "Process patient medical records",
      "Extract data from prescriptions",
      "Analyze clinical trial documents",
    ],
    features: [
      "Healthcare-specific document analysis",
      "HIPAA-compliant PII redaction",
      "Medical entity recognition",
      "Sentiment analysis for patient feedback",
    ],
    nodes: [
      {
        id: "hc-1",
        type: "executor",
        position: { x: 250, y: 50 },
        data: {
          label: "Document Input",
          executor: {
            id: "azure_blob_input",
            type: "input",
            name: "Azure Blob Input",
            color: "bg-blue-500",
            category: "input",
          },
          config: {
            name: "Document Input",
            description: "Scan healthcare document storage",
          },
        },
      },
      {
        id: "hc-2",
        type: "executor",
        position: { x: 250, y: 150 },
        data: {
          label: "Content Retrieval",
          executor: {
            id: "content_retriever",
            type: "input",
            name: "Content Retriever",
            color: "bg-blue-500",
            category: "input",
          },
          config: {
            name: "Content Retrieval",
            description: "Securely retrieve documents",
          },
        },
      },
      {
        id: "hc-3",
        type: "executor",
        position: { x: 250, y: 250 },
        data: {
          label: "Document Intelligence",
          executor: {
            id: "azure_document_intelligence_extractor",
            type: "extract",
            name: "Document Intelligence",
            color: "bg-primary",
            category: "extract",
          },
          config: {
            name: "Document Intelligence",
            description: "Extract medical document content",
          },
        },
      },
      {
        id: "hc-4",
        type: "executor",
        position: { x: 250, y: 350 },
        data: {
          label: "PII Detection & Redaction",
          executor: {
            id: "pii_detector_executor",
            type: "analyze",
            name: "PII Detector",
            color: "bg-accent",
            category: "analyze",
          },
          config: {
            name: "PII Detection & Redaction",
            description: "HIPAA-compliant PII handling",
            pii_types: ["name", "email", "phone", "ssn", "address"],
            action: "redact",
          },
        },
      },
      {
        id: "hc-5",
        type: "executor",
        position: { x: 150, y: 450 },
        data: {
          label: "Medical Entity Extraction",
          executor: {
            id: "entity_extraction_executor",
            type: "analyze",
            name: "Entity Extractor",
            color: "bg-accent",
            category: "analyze",
          },
          config: {
            name: "Medical Entity Extraction",
            description: "Extract medical entities",
            custom_entities: ["medication", "diagnosis", "procedure", "symptom"],
          },
        },
      },
      {
        id: "hc-6",
        type: "executor",
        position: { x: 350, y: 450 },
        data: {
          label: "Sentiment Analysis",
          executor: {
            id: "sentiment_analysis_executor",
            type: "analyze",
            name: "Sentiment Analyzer",
            color: "bg-accent",
            category: "analyze",
          },
          config: {
            name: "Sentiment Analysis",
            description: "Analyze patient feedback sentiment",
          },
        },
      },
      {
        id: "hc-7",
        type: "executor",
        position: { x: 250, y: 550 },
        data: {
          label: "Secure Indexing",
          executor: {
            id: "ai_search_index_writer",
            type: "output",
            name: "AI Search Writer",
            color: "bg-green-500",
            category: "output",
          },
          config: {
            name: "Secure Indexing",
            description: "Store with access controls",
          },
        },
      },
    ],
    edges: [
      { id: "e1-2", source: "hc-1", target: "hc-2" },
      { id: "e2-3", source: "hc-2", target: "hc-3" },
      { id: "e3-4", source: "hc-3", target: "hc-4" },
      { id: "e4-5", source: "hc-4", target: "hc-5" },
      { id: "e4-6", source: "hc-4", target: "hc-6" },
      { id: "e5-7", source: "hc-5", target: "hc-7" },
      { id: "e6-7", source: "hc-6", target: "hc-7" },
    ],
  },
  {
    id: "legal-ediscovery",
    name: "Legal eDiscovery Pipeline",
    description: "Enterprise-grade pipeline for legal document discovery, analysis, and classification with PII protection and keyword extraction.",
    category: "analysis",
    steps: 8,
    estimatedTime: "6-10 min",
    useCases: [
      "Process litigation documents at scale",
      "Perform document review and classification",
      "Extract privileged communications",
    ],
    features: [
      "Batch document processing",
      "Advanced entity and keyword extraction",
      "PII and sensitive data detection",
      "Multi-level classification",
      "Full-text search indexing",
    ],
    nodes: [
      {
        id: "legal-1",
        type: "executor",
        position: { x: 250, y: 50 },
        data: {
          label: "Document Collection",
          executor: {
            id: "azure_blob_input",
            type: "input",
            name: "Azure Blob Input",
            color: "bg-blue-500",
            category: "input",
          },
          config: {
            name: "Document Collection",
            description: "Discover legal documents",
            file_extensions: [".pdf", ".docx", ".msg", ".eml"],
          },
        },
      },
      {
        id: "legal-2",
        type: "executor",
        position: { x: 250, y: 150 },
        data: {
          label: "Content Retrieval",
          executor: {
            id: "content_retriever",
            type: "input",
            name: "Content Retriever",
            color: "bg-blue-500",
            category: "input",
          },
          config: {
            name: "Content Retrieval",
            description: "Download documents for processing",
          },
        },
      },
      {
        id: "legal-3",
        type: "executor",
        position: { x: 250, y: 250 },
        data: {
          label: "Document Extraction",
          executor: {
            id: "azure_content_understanding_extractor",
            type: "extract",
            name: "Content Understanding",
            color: "bg-primary",
            category: "extract",
          },
          config: {
            name: "Document Extraction",
            description: "Extract with contract analyzer",
            analyzer_id: "prebuilt-contract",
          },
        },
      },
      {
        id: "legal-4",
        type: "executor",
        position: { x: 150, y: 350 },
        data: {
          label: "Entity Extraction",
          executor: {
            id: "entity_extraction_executor",
            type: "analyze",
            name: "Entity Extractor",
            color: "bg-accent",
            category: "analyze",
          },
          config: {
            name: "Entity Extraction",
            description: "Extract parties, dates, obligations",
            entity_types: ["person", "organization", "date", "money"],
          },
        },
      },
      {
        id: "legal-5",
        type: "executor",
        position: { x: 350, y: 350 },
        data: {
          label: "Keyword Extraction",
          executor: {
            id: "keyword_extractor_executor",
            type: "analyze",
            name: "Keyword Extractor",
            color: "bg-accent",
            category: "analyze",
          },
          config: {
            name: "Keyword Extraction",
            description: "Extract legal keywords and phrases",
            max_keywords: 20,
          },
        },
      },
      {
        id: "legal-6",
        type: "executor",
        position: { x: 250, y: 450 },
        data: {
          label: "PII Detection",
          executor: {
            id: "pii_detector_executor",
            type: "analyze",
            name: "PII Detector",
            color: "bg-accent",
            category: "analyze",
          },
          config: {
            name: "PII Detection",
            description: "Identify sensitive information",
            action: "detect",
          },
        },
      },
      {
        id: "legal-7",
        type: "executor",
        position: { x: 250, y: 550 },
        data: {
          label: "Classification",
          executor: {
            id: "content_classifier_executor",
            type: "analyze",
            name: "Classifier",
            color: "bg-accent",
            category: "analyze",
          },
          config: {
            name: "Classification",
            description: "Classify document types",
            categories: ["contract", "correspondence", "pleading", "discovery"],
            multi_label: true,
          },
        },
      },
      {
        id: "legal-8",
        type: "executor",
        position: { x: 250, y: 650 },
        data: {
          label: "Search Indexing",
          executor: {
            id: "ai_search_index_writer",
            type: "output",
            name: "AI Search Writer",
            color: "bg-green-500",
            category: "output",
          },
          config: {
            name: "Search Indexing",
            description: "Index for eDiscovery search",
          },
        },
      },
    ],
    edges: [
      { id: "e1-2", source: "legal-1", target: "legal-2" },
      { id: "e2-3", source: "legal-2", target: "legal-3" },
      { id: "e3-4", source: "legal-3", target: "legal-4" },
      { id: "e3-5", source: "legal-3", target: "legal-5" },
      { id: "e4-6", source: "legal-4", target: "legal-6" },
      { id: "e5-6", source: "legal-5", target: "legal-6" },
      { id: "e6-7", source: "legal-6", target: "legal-7" },
      { id: "e7-8", source: "legal-7", target: "legal-8" },
    ],
  },
  {
    id: "customer-support-analytics",
    name: "Customer Support Analytics",
    description: "Analyze customer support tickets, emails, and chat transcripts with sentiment analysis, classification, and keyword extraction.",
    category: "analysis",
    steps: 6,
    estimatedTime: "3-5 min",
    useCases: [
      "Analyze support ticket sentiment trends",
      "Auto-categorize customer inquiries",
      "Extract common issues and keywords",
    ],
    features: [
      "Multi-language detection",
      "Sentiment and emotion analysis",
      "Automatic ticket classification",
      "Priority detection",
    ],
    nodes: [
      {
        id: "cs-1",
        type: "executor",
        position: { x: 250, y: 50 },
        data: {
          label: "Ticket Collection",
          executor: {
            id: "content_retriever",
            type: "input",
            name: "Content Retriever",
            color: "bg-blue-500",
            category: "input",
          },
          config: {
            name: "Ticket Collection",
            description: "Load support tickets and transcripts",
          },
        },
      },
      {
        id: "cs-2",
        type: "executor",
        position: { x: 250, y: 150 },
        data: {
          label: "Language Detection",
          executor: {
            id: "language_detector_executor",
            type: "analyze",
            name: "Language Detector",
            color: "bg-accent",
            category: "analyze",
          },
          config: {
            name: "Language Detection",
            description: "Identify ticket language",
          },
        },
      },
      {
        id: "cs-3",
        type: "executor",
        position: { x: 150, y: 250 },
        data: {
          label: "Sentiment Analysis",
          executor: {
            id: "sentiment_analysis_executor",
            type: "analyze",
            name: "Sentiment Analyzer",
            color: "bg-accent",
            category: "analyze",
          },
          config: {
            name: "Sentiment Analysis",
            description: "Analyze customer sentiment",
            granularity: "document",
            include_emotions: true,
          },
        },
      },
      {
        id: "cs-4",
        type: "executor",
        position: { x: 350, y: 250 },
        data: {
          label: "Keyword Extraction",
          executor: {
            id: "keyword_extractor_executor",
            type: "analyze",
            name: "Keyword Extractor",
            color: "bg-accent",
            category: "analyze",
          },
          config: {
            name: "Keyword Extraction",
            description: "Extract issue keywords",
            max_keywords: 15,
          },
        },
      },
      {
        id: "cs-5",
        type: "executor",
        position: { x: 250, y: 350 },
        data: {
          label: "Ticket Classification",
          executor: {
            id: "content_classifier_executor",
            type: "analyze",
            name: "Classifier",
            color: "bg-accent",
            category: "analyze",
          },
          config: {
            name: "Ticket Classification",
            description: "Categorize by issue type",
            categories: ["billing", "technical", "product", "account", "general"],
          },
        },
      },
      {
        id: "cs-6",
        type: "executor",
        position: { x: 250, y: 450 },
        data: {
          label: "Analytics Index",
          executor: {
            id: "ai_search_index_writer",
            type: "output",
            name: "AI Search Writer",
            color: "bg-green-500",
            category: "output",
          },
          config: {
            name: "Analytics Index",
            description: "Store for analytics and reporting",
          },
        },
      },
    ],
    edges: [
      { id: "e1-2", source: "cs-1", target: "cs-2" },
      { id: "e2-3", source: "cs-2", target: "cs-3" },
      { id: "e2-4", source: "cs-2", target: "cs-4" },
      { id: "e3-5", source: "cs-3", target: "cs-5" },
      { id: "e4-5", source: "cs-4", target: "cs-5" },
      { id: "e5-6", source: "cs-5", target: "cs-6" },
    ],
  },
  {
    id: "hr-resume-screening",
    name: "HR Resume Screening & Analysis",
    description: "Automated resume processing with skill extraction, candidate classification, and PII-compliant data handling.",
    category: "analysis",
    steps: 6,
    estimatedTime: "3-5 min",
    useCases: [
      "Screen resumes at scale",
      "Extract skills and qualifications",
      "Match candidates to job requirements",
    ],
    features: [
      "Multi-format resume parsing",
      "Skill and entity extraction",
      "Candidate classification",
      "PII-compliant processing",
    ],
    nodes: [
      {
        id: "hr-1",
        type: "executor",
        position: { x: 250, y: 50 },
        data: {
          label: "Resume Upload",
          executor: {
            id: "azure_blob_input",
            type: "input",
            name: "Azure Blob Input",
            color: "bg-blue-500",
            category: "input",
          },
          config: {
            name: "Resume Upload",
            description: "Collect resumes from storage",
            file_extensions: [".pdf", ".docx"],
          },
        },
      },
      {
        id: "hr-2",
        type: "executor",
        position: { x: 250, y: 150 },
        data: {
          label: "Content Retrieval",
          executor: {
            id: "content_retriever",
            type: "input",
            name: "Content Retriever",
            color: "bg-blue-500",
            category: "input",
          },
          config: {
            name: "Content Retrieval",
            description: "Download resumes",
          },
        },
      },
      {
        id: "hr-3",
        type: "executor",
        position: { x: 250, y: 250 },
        data: {
          label: "Document Extraction",
          executor: {
            id: "azure_document_intelligence_extractor",
            type: "extract",
            name: "Document Intelligence",
            color: "bg-primary",
            category: "extract",
          },
          config: {
            name: "Document Extraction",
            description: "Extract resume content",
          },
        },
      },
      {
        id: "hr-4",
        type: "executor",
        position: { x: 250, y: 350 },
        data: {
          label: "Entity & Skill Extraction",
          executor: {
            id: "entity_extraction_executor",
            type: "analyze",
            name: "Entity Extractor",
            color: "bg-accent",
            category: "analyze",
          },
          config: {
            name: "Entity & Skill Extraction",
            description: "Extract candidate info and skills",
            entity_types: ["person", "email", "phone", "organization"],
            custom_entities: ["skill", "degree", "certification"],
          },
        },
      },
      {
        id: "hr-5",
        type: "executor",
        position: { x: 250, y: 450 },
        data: {
          label: "Candidate Classification",
          executor: {
            id: "content_classifier_executor",
            type: "analyze",
            name: "Classifier",
            color: "bg-accent",
            category: "analyze",
          },
          config: {
            name: "Candidate Classification",
            description: "Classify by experience level",
            categories: ["entry_level", "mid_level", "senior", "executive"],
          },
        },
      },
      {
        id: "hr-6",
        type: "executor",
        position: { x: 250, y: 550 },
        data: {
          label: "Candidate Database",
          executor: {
            id: "ai_search_index_writer",
            type: "output",
            name: "AI Search Writer",
            color: "bg-green-500",
            category: "output",
          },
          config: {
            name: "Candidate Database",
            description: "Index for candidate search",
          },
        },
      },
    ],
    edges: [
      { id: "e1-2", source: "hr-1", target: "hr-2" },
      { id: "e2-3", source: "hr-2", target: "hr-3" },
      { id: "e3-4", source: "hr-3", target: "hr-4" },
      { id: "e4-5", source: "hr-4", target: "hr-5" },
      { id: "e5-6", source: "hr-5", target: "hr-6" },
    ],
  },
  {
    id: "excel-data-rag",
    name: "Excel Data RAG Pipeline",
    description: "Process Excel spreadsheets with table splitting, row-level processing, and semantic search indexing for data analytics.",
    category: "extraction",
    steps: 6,
    estimatedTime: "3-5 min",
    useCases: [
      "Build searchable product catalogs from Excel",
      "Index customer data for semantic search",
      "Process financial data tables",
    ],
    features: [
      "Excel workbook extraction",
      "Table and sheet-level processing",
      "Row-by-row splitting for granular search",
      "Metadata preservation",
    ],
    nodes: [
      {
        id: "excel-1",
        type: "executor",
        position: { x: 250, y: 50 },
        data: {
          label: "Excel Upload",
          executor: {
            id: "azure_blob_input",
            type: "input",
            name: "Azure Blob Input",
            color: "bg-blue-500",
            category: "input",
          },
          config: {
            name: "Excel Upload",
            description: "Discover Excel files",
            file_extensions: [".xlsx", ".xlsm"],
          },
        },
      },
      {
        id: "excel-2",
        type: "executor",
        position: { x: 250, y: 150 },
        data: {
          label: "Content Retrieval",
          executor: {
            id: "content_retriever",
            type: "input",
            name: "Content Retriever",
            color: "bg-blue-500",
            category: "input",
          },
          config: {
            name: "Content Retrieval",
            description: "Download Excel files",
          },
        },
      },
      {
        id: "excel-3",
        type: "executor",
        position: { x: 250, y: 250 },
        data: {
          label: "Excel Extraction",
          executor: {
            id: "excel_extractor",
            type: "extract",
            name: "Excel Extractor",
            color: "bg-primary",
            category: "extract",
          },
          config: {
            name: "Excel Extraction",
            description: "Extract sheets and tables",
            extract_sheets: true,
            extract_tables: true,
          },
        },
      },
      {
        id: "excel-4",
        type: "executor",
        position: { x: 250, y: 350 },
        data: {
          label: "Table Row Splitting",
          executor: {
            id: "table_row_splitter",
            type: "transform",
            name: "Row Splitter",
            color: "bg-secondary",
            category: "transform",
          },
          config: {
            name: "Table Row Splitting",
            description: "Split tables into individual rows",
            has_header: true,
            include_headers: true,
          },
        },
      },
      {
        id: "excel-5",
        type: "executor",
        position: { x: 250, y: 450 },
        data: {
          label: "Generate Embeddings",
          executor: {
            id: "azure_openai_embeddings_executor",
            type: "analyze",
            name: "Embeddings Generator",
            color: "bg-accent",
            category: "analyze",
          },
          config: {
            name: "Generate Embeddings",
            description: "Create embeddings for each row",
          },
        },
      },
      {
        id: "excel-6",
        type: "executor",
        position: { x: 250, y: 550 },
        data: {
          label: "Index to Search",
          executor: {
            id: "ai_search_index_writer",
            type: "output",
            name: "AI Search Writer",
            color: "bg-green-500",
            category: "output",
          },
          config: {
            name: "Index to Search",
            description: "Index rows for semantic search",
            index_mode: "chunks",
          },
        },
      },
    ],
    edges: [
      { id: "e1-2", source: "excel-1", target: "excel-2" },
      { id: "e2-3", source: "excel-2", target: "excel-3" },
      { id: "e3-4", source: "excel-3", target: "excel-4" },
      { id: "e4-5", source: "excel-4", target: "excel-5" },
      { id: "e5-6", source: "excel-5", target: "excel-6" },
    ],
  },
  {
    id: "multilingual-content-processing",
    name: "Multilingual Content Processing",
    description: "Process documents in multiple languages with automatic detection, translation, and language-specific analysis.",
    category: "analysis",
    steps: 7,
    estimatedTime: "4-6 min",
    useCases: [
      "Process global customer feedback",
      "Translate and index international documents",
      "Build multilingual knowledge bases",
    ],
    features: [
      "Automatic language detection",
      "AI-powered translation",
      "Language-aware sentiment analysis",
      "Cross-lingual search indexing",
    ],
    nodes: [
      {
        id: "ml-1",
        type: "executor",
        position: { x: 250, y: 50 },
        data: {
          label: "Document Input",
          executor: {
            id: "content_retriever",
            type: "input",
            name: "Content Retriever",
            color: "bg-blue-500",
            category: "input",
          },
          config: {
            name: "Document Input",
            description: "Load multilingual documents",
          },
        },
      },
      {
        id: "ml-2",
        type: "executor",
        position: { x: 250, y: 150 },
        data: {
          label: "Content Extraction",
          executor: {
            id: "azure_document_intelligence_extractor",
            type: "extract",
            name: "Document Intelligence",
            color: "bg-primary",
            category: "extract",
          },
          config: {
            name: "Content Extraction",
            description: "Extract document content",
          },
        },
      },
      {
        id: "ml-3",
        type: "executor",
        position: { x: 250, y: 250 },
        data: {
          label: "Language Detection",
          executor: {
            id: "language_detector_executor",
            type: "analyze",
            name: "Language Detector",
            color: "bg-accent",
            category: "analyze",
          },
          config: {
            name: "Language Detection",
            description: "Identify document language",
            detect_multiple: true,
          },
        },
      },
      {
        id: "ml-4",
        type: "executor",
        position: { x: 250, y: 350 },
        data: {
          label: "Translation",
          executor: {
            id: "translation_executor",
            type: "analyze",
            name: "Translator",
            color: "bg-accent",
            category: "analyze",
          },
          config: {
            name: "Translation",
            description: "Translate to English",
            target_language: "English",
          },
        },
      },
      {
        id: "ml-5",
        type: "executor",
        position: { x: 150, y: 450 },
        data: {
          label: "Sentiment Analysis",
          executor: {
            id: "sentiment_analysis_executor",
            type: "analyze",
            name: "Sentiment Analyzer",
            color: "bg-accent",
            category: "analyze",
          },
          config: {
            name: "Sentiment Analysis",
            description: "Analyze translated content sentiment",
          },
        },
      },
      {
        id: "ml-6",
        type: "executor",
        position: { x: 350, y: 450 },
        data: {
          label: "Keyword Extraction",
          executor: {
            id: "keyword_extractor_executor",
            type: "analyze",
            name: "Keyword Extractor",
            color: "bg-accent",
            category: "analyze",
          },
          config: {
            name: "Keyword Extraction",
            description: "Extract keywords from translation",
          },
        },
      },
      {
        id: "ml-7",
        type: "executor",
        position: { x: 250, y: 550 },
        data: {
          label: "Multilingual Index",
          executor: {
            id: "ai_search_index_writer",
            type: "output",
            name: "AI Search Writer",
            color: "bg-green-500",
            category: "output",
          },
          config: {
            name: "Multilingual Index",
            description: "Index with language metadata",
          },
        },
      },
    ],
    edges: [
      { id: "e1-2", source: "ml-1", target: "ml-2" },
      { id: "e2-3", source: "ml-2", target: "ml-3" },
      { id: "e3-4", source: "ml-3", target: "ml-4" },
      { id: "e4-5", source: "ml-4", target: "ml-5" },
      { id: "e4-6", source: "ml-4", target: "ml-6" },
      { id: "e5-7", source: "ml-5", target: "ml-7" },
      { id: "e6-7", source: "ml-6", target: "ml-7" },
    ],
  },
  {
    id: "intelligent-document-summarization",
    name: "Intelligent Document Summarization",
    description: "Create comprehensive summaries of long documents with key point extraction, topic detection, and configurable summary styles.",
    category: "analysis",
    steps: 5,
    estimatedTime: "3-5 min",
    useCases: [
      "Summarize research papers and reports",
      "Create executive summaries from long documents",
      "Generate meeting notes from transcripts",
    ],
    features: [
      "Multi-level summarization",
      "Key point and entity extraction",
      "Configurable summary length and style",
      "Topic and keyword extraction",
    ],
    nodes: [
      {
        id: "sum-1",
        type: "executor",
        position: { x: 250, y: 50 },
        data: {
          label: "Document Input",
          executor: {
            id: "content_retriever",
            type: "input",
            name: "Content Retriever",
            color: "bg-blue-500",
            category: "input",
          },
          config: {
            name: "Document Input",
            description: "Load documents to summarize",
          },
        },
      },
      {
        id: "sum-2",
        type: "executor",
        position: { x: 250, y: 150 },
        data: {
          label: "Content Extraction",
          executor: {
            id: "azure_content_understanding_extractor",
            type: "extract",
            name: "Content Understanding",
            color: "bg-primary",
            category: "extract",
          },
          config: {
            name: "Content Extraction",
            description: "Extract structured content",
          },
        },
      },
      {
        id: "sum-3",
        type: "executor",
        position: { x: 150, y: 250 },
        data: {
          label: "AI Summarization",
          executor: {
            id: "summarization_executor",
            type: "analyze",
            name: "Summarizer",
            color: "bg-accent",
            category: "analyze",
          },
          config: {
            name: "AI Summarization",
            description: "Generate intelligent summary",
            summary_length: "medium",
            summary_style: "paragraph",
            preserve_key_facts: true,
          },
        },
      },
      {
        id: "sum-4",
        type: "executor",
        position: { x: 350, y: 250 },
        data: {
          label: "Keyword & Topic Extraction",
          executor: {
            id: "keyword_extractor_executor",
            type: "analyze",
            name: "Keyword Extractor",
            color: "bg-accent",
            category: "analyze",
          },
          config: {
            name: "Keyword & Topic Extraction",
            description: "Extract key terms and topics",
            extract_topics: true,
          },
        },
      },
      {
        id: "sum-5",
        type: "executor",
        position: { x: 250, y: 350 },
        data: {
          label: "Index Summaries",
          executor: {
            id: "ai_search_index_writer",
            type: "output",
            name: "AI Search Writer",
            color: "bg-green-500",
            category: "output",
          },
          config: {
            name: "Index Summaries",
            description: "Store summaries for quick access",
          },
        },
      },
    ],
    edges: [
      { id: "e1-2", source: "sum-1", target: "sum-2" },
      { id: "e2-3", source: "sum-2", target: "sum-3" },
      { id: "e2-4", source: "sum-2", target: "sum-4" },
      { id: "e3-5", source: "sum-3", target: "sum-5" },
      { id: "e4-5", source: "sum-4", target: "sum-5" },
    ],
  },
  {
    id: "foia-request-processing",
    name: "FOIA Request Processing",
    description: "Automate Freedom of Information Act requests by redacting PII, classifying documents, and generating disclosure logs with audit trails.",
    category: "compliance",
    steps: 5,
    estimatedTime: "3-4 min",
    useCases: [
      "Automatically redact PII from public records",
      "Extract and organize responsive documents",
      "Generate disclosure logs with audit trails",
    ],
    features: [
      "Automated PII redaction with compliance checks",
      "Document classification by sensitivity level",
      "Audit trail generation",
      "Response time tracking",
    ],
    nodes: [
      {
        id: "foia-1",
        type: "executor",
        position: { x: 250, y: 50 },
        data: {
          label: "Document Collection",
          executor: {
            id: "doc-crack",
            type: "extract",
            name: "Document Cracker",
            color: "bg-primary",
            category: "extract",
          },
          config: {
            name: "Document Collection",
            description: "Load and process request documents",
          },
        },
      },
      {
        id: "foia-2",
        type: "executor",
        position: { x: 250, y: 150 },
        data: {
          label: "PII Detection",
          executor: {
            id: "entity",
            type: "analyze",
            name: "Entity Extractor",
            color: "bg-primary",
            category: "analyze",
          },
          config: {
            name: "PII Detection",
            description: "Identify personal information",
          },
        },
      },
      {
        id: "foia-3",
        type: "executor",
        position: { x: 250, y: 250 },
        data: {
          label: "Auto Redaction",
          executor: {
            id: "transform",
            type: "transform",
            name: "Content Transformer",
            color: "bg-secondary",
            category: "transform",
          },
          config: {
            name: "Auto Redaction",
            description: "Redact sensitive information",
          },
        },
      },
      {
        id: "foia-4",
        type: "executor",
        position: { x: 250, y: 350 },
        data: {
          label: "Document Classification",
          executor: {
            id: "summarize",
            type: "analyze",
            name: "AI Summarizer",
            color: "bg-accent",
            category: "analyze",
          },
          config: {
            name: "Document Classification",
            description: "Classify by sensitivity and responsiveness",
          },
        },
      },
      {
        id: "foia-5",
        type: "executor",
        position: { x: 250, y: 450 },
        data: {
          label: "Disclosure Log",
          executor: {
            id: "transform",
            type: "transform",
            name: "Content Transformer",
            color: "bg-secondary",
            category: "transform",
          },
          config: {
            name: "Disclosure Log",
            description: "Generate compliance documentation",
          },
        },
      },
    ],
    edges: [
      { id: "e1-2", source: "foia-1", target: "foia-2" },
      { id: "e2-3", source: "foia-2", target: "foia-3" },
      { id: "e3-4", source: "foia-3", target: "foia-4" },
      { id: "e4-5", source: "foia-4", target: "foia-5" },
    ],
  },
  {
    id: "permit-application-processing",
    name: "Permit & License Application Processing",
    description: "Streamline permit and license applications with automated data extraction, validation, and intelligent routing to appropriate departments.",
    category: "automation",
    steps: 4,
    estimatedTime: "2-3 min",
    useCases: [
      "Extract data from submitted application forms",
      "Validate supporting documents",
      "Route to appropriate departments",
    ],
    features: [
      "Multi-format document acceptance",
      "Completeness validation",
      "Automated workflow routing",
      "Status notification system",
    ],
    nodes: [
      {
        id: "permit-1",
        type: "executor",
        position: { x: 250, y: 50 },
        data: {
          label: "Application Intake",
          executor: {
            id: "doc-crack",
            type: "extract",
            name: "Document Cracker",
            color: "bg-primary",
            category: "extract",
          },
          config: {
            name: "Application Intake",
            description: "Process submitted forms and documents",
          },
        },
      },
      {
        id: "permit-2",
        type: "executor",
        position: { x: 250, y: 150 },
        data: {
          label: "Data Extraction",
          executor: {
            id: "entity",
            type: "analyze",
            name: "Entity Extractor",
            color: "bg-primary",
            category: "analyze",
          },
          config: {
            name: "Data Extraction",
            description: "Extract application details",
          },
        },
      },
      {
        id: "permit-3",
        type: "executor",
        position: { x: 250, y: 250 },
        data: {
          label: "Validation Check",
          executor: {
            id: "transform",
            type: "transform",
            name: "Content Transformer",
            color: "bg-secondary",
            category: "transform",
          },
          config: {
            name: "Validation Check",
            description: "Verify completeness and requirements",
          },
        },
      },
      {
        id: "permit-4",
        type: "executor",
        position: { x: 250, y: 350 },
        data: {
          label: "Route Application",
          executor: {
            id: "summarize",
            type: "analyze",
            name: "AI Summarizer",
            color: "bg-accent",
            category: "analyze",
          },
          config: {
            name: "Route Application",
            description: "Determine appropriate department",
          },
        },
      },
    ],
    edges: [
      { id: "e1-2", source: "permit-1", target: "permit-2" },
      { id: "e2-3", source: "permit-2", target: "permit-3" },
      { id: "e3-4", source: "permit-3", target: "permit-4" },
    ],
  },
  {
    id: "contract-review-analysis",
    name: "Contract Review & Analysis",
    description: "Analyze contracts to extract key terms, identify non-standard clauses, flag risks, and ensure compliance with organizational templates.",
    category: "analysis",
    steps: 5,
    estimatedTime: "3-4 min",
    useCases: [
      "Extract key terms and obligations",
      "Identify non-standard clauses",
      "Flag potential risks and compliance issues",
    ],
    features: [
      "Clause library comparison",
      "Risk scoring and assessment",
      "Term extraction (dates, parties, amounts)",
      "Compliance checking against templates",
    ],
    nodes: [
      {
        id: "contract-1",
        type: "executor",
        position: { x: 250, y: 50 },
        data: {
          label: "Contract Upload",
          executor: {
            id: "doc-crack",
            type: "extract",
            name: "Document Cracker",
            color: "bg-primary",
            category: "extract",
          },
          config: {
            name: "Contract Upload",
            description: "Load contract documents",
          },
        },
      },
      {
        id: "contract-2",
        type: "executor",
        position: { x: 250, y: 150 },
        data: {
          label: "Clause Extraction",
          executor: {
            id: "entity",
            type: "analyze",
            name: "Entity Extractor",
            color: "bg-primary",
            category: "analyze",
          },
          config: {
            name: "Clause Extraction",
            description: "Extract key terms and clauses",
          },
        },
      },
      {
        id: "contract-3",
        type: "executor",
        position: { x: 150, y: 250 },
        data: {
          label: "Risk Analysis",
          executor: {
            id: "summarize",
            type: "analyze",
            name: "AI Summarizer",
            color: "bg-accent",
            category: "analyze",
          },
          config: {
            name: "Risk Analysis",
            description: "Identify and score risks",
          },
        },
      },
      {
        id: "contract-4",
        type: "executor",
        position: { x: 350, y: 250 },
        data: {
          label: "Compliance Check",
          executor: {
            id: "summarize",
            type: "analyze",
            name: "AI Summarizer",
            color: "bg-accent",
            category: "analyze",
          },
          config: {
            name: "Compliance Check",
            description: "Compare against standard templates",
          },
        },
      },
      {
        id: "contract-5",
        type: "executor",
        position: { x: 250, y: 350 },
        data: {
          label: "Review Report",
          executor: {
            id: "transform",
            type: "transform",
            name: "Content Transformer",
            color: "bg-secondary",
            category: "transform",
          },
          config: {
            name: "Review Report",
            description: "Generate comprehensive analysis",
          },
        },
      },
    ],
    edges: [
      { id: "e1-2", source: "contract-1", target: "contract-2" },
      { id: "e2-3", source: "contract-2", target: "contract-3" },
      { id: "e2-4", source: "contract-2", target: "contract-4" },
      { id: "e3-5", source: "contract-3", target: "contract-5" },
      { id: "e4-5", source: "contract-4", target: "contract-5" },
    ],
  },
  {
    id: "legal-discovery-processing",
    name: "Legal Discovery Document Processing",
    description: "Process large volumes of discovery documents to extract privileged communications, identify key evidence, and build case timelines.",
    category: "extraction",
    steps: 6,
    estimatedTime: "4-5 min",
    useCases: [
      "Process large volumes of discovery documents",
      "Extract privileged communications",
      "Identify key evidence and build timelines",
    ],
    features: [
      "Privilege detection and tagging",
      "Entity and relationship mapping",
      "Timeline generation from documents",
      "Responsive document classification",
    ],
    nodes: [
      {
        id: "discovery-1",
        type: "executor",
        position: { x: 250, y: 50 },
        data: {
          label: "Document Intake",
          executor: {
            id: "doc-crack",
            type: "extract",
            name: "Document Cracker",
            color: "bg-primary",
            category: "extract",
          },
          config: {
            name: "Document Intake",
            description: "Batch process discovery documents",
          },
        },
      },
      {
        id: "discovery-2",
        type: "executor",
        position: { x: 250, y: 150 },
        data: {
          label: "Document Classification",
          executor: {
            id: "summarize",
            type: "analyze",
            name: "AI Summarizer",
            color: "bg-accent",
            category: "analyze",
          },
          config: {
            name: "Document Classification",
            description: "Classify document types",
          },
        },
      },
      {
        id: "discovery-3",
        type: "executor",
        position: { x: 150, y: 250 },
        data: {
          label: "Privilege Detection",
          executor: {
            id: "entity",
            type: "analyze",
            name: "Entity Extractor",
            color: "bg-primary",
            category: "analyze",
          },
          config: {
            name: "Privilege Detection",
            description: "Identify attorney-client communications",
          },
        },
      },
      {
        id: "discovery-4",
        type: "executor",
        position: { x: 350, y: 250 },
        data: {
          label: "Entity Extraction",
          executor: {
            id: "entity",
            type: "analyze",
            name: "Entity Extractor",
            color: "bg-primary",
            category: "analyze",
          },
          config: {
            name: "Entity Extraction",
            description: "Extract parties, dates, and facts",
          },
        },
      },
      {
        id: "discovery-5",
        type: "executor",
        position: { x: 250, y: 350 },
        data: {
          label: "Timeline Builder",
          executor: {
            id: "transform",
            type: "transform",
            name: "Content Transformer",
            color: "bg-secondary",
            category: "transform",
          },
          config: {
            name: "Timeline Builder",
            description: "Create chronological event timeline",
          },
        },
      },
      {
        id: "discovery-6",
        type: "executor",
        position: { x: 250, y: 450 },
        data: {
          label: "Production Set",
          executor: {
            id: "transform",
            type: "transform",
            name: "Content Transformer",
            color: "bg-secondary",
            category: "transform",
          },
          config: {
            name: "Production Set",
            description: "Organize responsive documents",
          },
        },
      },
    ],
    edges: [
      { id: "e1-2", source: "discovery-1", target: "discovery-2" },
      { id: "e2-3", source: "discovery-2", target: "discovery-3" },
      { id: "e2-4", source: "discovery-2", target: "discovery-4" },
      { id: "e3-5", source: "discovery-3", target: "discovery-5" },
      { id: "e4-5", source: "discovery-4", target: "discovery-5" },
      { id: "e5-6", source: "discovery-5", target: "discovery-6" },
    ],
  },
  {
    id: "case-law-research",
    name: "Case Law Research & Summarization",
    description: "Summarize court opinions, extract legal precedents, and identify relevant case citations with jurisdiction classification.",
    category: "analysis",
    steps: 5,
    estimatedTime: "2-3 min",
    useCases: [
      "Summarize court opinions and decisions",
      "Extract legal precedents and holdings",
      "Identify relevant case citations",
    ],
    features: [
      "Citation extraction and validation",
      "Key holdings identification",
      "Jurisdiction classification",
      "Precedent mapping and analysis",
    ],
    nodes: [
      {
        id: "caselaw-1",
        type: "executor",
        position: { x: 250, y: 50 },
        data: {
          label: "Opinion Upload",
          executor: {
            id: "doc-crack",
            type: "extract",
            name: "Document Cracker",
            color: "bg-primary",
            category: "extract",
          },
          config: {
            name: "Opinion Upload",
            description: "Load court opinions and decisions",
          },
        },
      },
      {
        id: "caselaw-2",
        type: "executor",
        position: { x: 250, y: 150 },
        data: {
          label: "Citation Extraction",
          executor: {
            id: "entity",
            type: "analyze",
            name: "Entity Extractor",
            color: "bg-primary",
            category: "analyze",
          },
          config: {
            name: "Citation Extraction",
            description: "Extract and validate case citations",
          },
        },
      },
      {
        id: "caselaw-3",
        type: "executor",
        position: { x: 250, y: 250 },
        data: {
          label: "Holdings Analysis",
          executor: {
            id: "summarize",
            type: "analyze",
            name: "AI Summarizer",
            color: "bg-accent",
            category: "analyze",
          },
          config: {
            name: "Holdings Analysis",
            description: "Identify key legal holdings",
          },
        },
      },
      {
        id: "caselaw-4",
        type: "executor",
        position: { x: 250, y: 350 },
        data: {
          label: "Jurisdiction Classification",
          executor: {
            id: "transform",
            type: "transform",
            name: "Content Transformer",
            color: "bg-secondary",
            category: "transform",
          },
          config: {
            name: "Jurisdiction Classification",
            description: "Classify by court and jurisdiction",
          },
        },
      },
      {
        id: "caselaw-5",
        type: "executor",
        position: { x: 250, y: 450 },
        data: {
          label: "Research Summary",
          executor: {
            id: "transform",
            type: "transform",
            name: "Content Transformer",
            color: "bg-secondary",
            category: "transform",
          },
          config: {
            name: "Research Summary",
            description: "Generate comprehensive case summary",
          },
        },
      },
    ],
    edges: [
      { id: "e1-2", source: "caselaw-1", target: "caselaw-2" },
      { id: "e2-3", source: "caselaw-2", target: "caselaw-3" },
      { id: "e3-4", source: "caselaw-3", target: "caselaw-4" },
      { id: "e4-5", source: "caselaw-4", target: "caselaw-5" },
    ],
  },
  {
    id: "claims-document-processing",
    name: "Claims Document Processing",
    description: "Automate insurance claims processing by extracting data from forms, medical records, and reports with fraud indicator detection.",
    category: "extraction",
    steps: 5,
    estimatedTime: "3-4 min",
    useCases: [
      "Extract data from claim forms",
      "Process medical records and reports",
      "Analyze police and incident reports",
    ],
    features: [
      "Structured data extraction from forms",
      "Document type classification",
      "Key information validation",
      "Fraud indicator detection",
    ],
    nodes: [
      {
        id: "claims-1",
        type: "executor",
        position: { x: 250, y: 50 },
        data: {
          label: "Document Upload",
          executor: {
            id: "doc-crack",
            type: "extract",
            name: "Document Cracker",
            color: "bg-primary",
            category: "extract",
          },
          config: {
            name: "Document Upload",
            description: "Load claim documents",
          },
        },
      },
      {
        id: "claims-2",
        type: "executor",
        position: { x: 250, y: 150 },
        data: {
          label: "Data Extraction",
          executor: {
            id: "entity",
            type: "analyze",
            name: "Entity Extractor",
            color: "bg-primary",
            category: "analyze",
          },
          config: {
            name: "Data Extraction",
            description: "Extract claim details and amounts",
          },
        },
      },
      {
        id: "claims-3",
        type: "executor",
        position: { x: 250, y: 250 },
        data: {
          label: "Document Classification",
          executor: {
            id: "summarize",
            type: "analyze",
            name: "AI Summarizer",
            color: "bg-accent",
            category: "analyze",
          },
          config: {
            name: "Document Classification",
            description: "Classify document types",
          },
        },
      },
      {
        id: "claims-4",
        type: "executor",
        position: { x: 250, y: 350 },
        data: {
          label: "Fraud Detection",
          executor: {
            id: "summarize",
            type: "analyze",
            name: "AI Summarizer",
            color: "bg-accent",
            category: "analyze",
          },
          config: {
            name: "Fraud Detection",
            description: "Analyze for fraud indicators",
          },
        },
      },
      {
        id: "claims-5",
        type: "executor",
        position: { x: 250, y: 450 },
        data: {
          label: "Claims Summary",
          executor: {
            id: "transform",
            type: "transform",
            name: "Content Transformer",
            color: "bg-secondary",
            category: "transform",
          },
          config: {
            name: "Claims Summary",
            description: "Generate processing report",
          },
        },
      },
    ],
    edges: [
      { id: "e1-2", source: "claims-1", target: "claims-2" },
      { id: "e2-3", source: "claims-2", target: "claims-3" },
      { id: "e3-4", source: "claims-3", target: "claims-4" },
      { id: "e4-5", source: "claims-4", target: "claims-5" },
    ],
  },
  {
    id: "policy-document-analysis",
    name: "Policy Document Analysis",
    description: "Analyze insurance policies to compare terms, extract coverage details, identify exclusions, and validate policy periods.",
    category: "analysis",
    steps: 4,
    estimatedTime: "2-3 min",
    useCases: [
      "Compare policy terms across documents",
      "Extract coverage details and limits",
      "Identify exclusions and conditions",
    ],
    features: [
      "Coverage comparison across policies",
      "Premium calculation assistance",
      "Endorsement tracking",
      "Policy period validation",
    ],
    nodes: [
      {
        id: "policy-1",
        type: "executor",
        position: { x: 250, y: 50 },
        data: {
          label: "Policy Upload",
          executor: {
            id: "doc-crack",
            type: "extract",
            name: "Document Cracker",
            color: "bg-primary",
            category: "extract",
          },
          config: {
            name: "Policy Upload",
            description: "Load policy documents",
          },
        },
      },
      {
        id: "policy-2",
        type: "executor",
        position: { x: 250, y: 150 },
        data: {
          label: "Coverage Extraction",
          executor: {
            id: "entity",
            type: "analyze",
            name: "Entity Extractor",
            color: "bg-primary",
            category: "analyze",
          },
          config: {
            name: "Coverage Extraction",
            description: "Extract coverage terms and limits",
          },
        },
      },
      {
        id: "policy-3",
        type: "executor",
        position: { x: 250, y: 250 },
        data: {
          label: "Policy Analysis",
          executor: {
            id: "summarize",
            type: "analyze",
            name: "AI Summarizer",
            color: "bg-accent",
            category: "analyze",
          },
          config: {
            name: "Policy Analysis",
            description: "Analyze exclusions and conditions",
          },
        },
      },
      {
        id: "policy-4",
        type: "executor",
        position: { x: 250, y: 350 },
        data: {
          label: "Comparison Report",
          executor: {
            id: "transform",
            type: "transform",
            name: "Content Transformer",
            color: "bg-secondary",
            category: "transform",
          },
          config: {
            name: "Comparison Report",
            description: "Generate policy comparison",
          },
        },
      },
    ],
    edges: [
      { id: "e1-2", source: "policy-1", target: "policy-2" },
      { id: "e2-3", source: "policy-2", target: "policy-3" },
      { id: "e3-4", source: "policy-3", target: "policy-4" },
    ],
  },
  {
    id: "medical-records-review",
    name: "Medical Records Review",
    description: "Extract diagnoses, treatments, and medical histories from records with HIPAA-compliant processing and medical code extraction.",
    category: "extraction",
    steps: 5,
    estimatedTime: "3-4 min",
    useCases: [
      "Extract diagnoses and treatments",
      "Identify pre-existing conditions",
      "Summarize medical histories",
    ],
    features: [
      "HIPAA-compliant processing",
      "Medical code extraction (ICD, CPT)",
      "Treatment timeline generation",
      "Provider information extraction",
    ],
    nodes: [
      {
        id: "medical-1",
        type: "executor",
        position: { x: 250, y: 50 },
        data: {
          label: "Records Upload",
          executor: {
            id: "doc-crack",
            type: "extract",
            name: "Document Cracker",
            color: "bg-primary",
            category: "extract",
          },
          config: {
            name: "Records Upload",
            description: "Load medical records securely",
          },
        },
      },
      {
        id: "medical-2",
        type: "executor",
        position: { x: 250, y: 150 },
        data: {
          label: "Medical Code Extraction",
          executor: {
            id: "entity",
            type: "analyze",
            name: "Entity Extractor",
            color: "bg-primary",
            category: "analyze",
          },
          config: {
            name: "Medical Code Extraction",
            description: "Extract ICD and CPT codes",
          },
        },
      },
      {
        id: "medical-3",
        type: "executor",
        position: { x: 250, y: 250 },
        data: {
          label: "Diagnosis Extraction",
          executor: {
            id: "entity",
            type: "analyze",
            name: "Entity Extractor",
            color: "bg-primary",
            category: "analyze",
          },
          config: {
            name: "Diagnosis Extraction",
            description: "Identify conditions and treatments",
          },
        },
      },
      {
        id: "medical-4",
        type: "executor",
        position: { x: 250, y: 350 },
        data: {
          label: "Timeline Builder",
          executor: {
            id: "transform",
            type: "transform",
            name: "Content Transformer",
            color: "bg-secondary",
            category: "transform",
          },
          config: {
            name: "Timeline Builder",
            description: "Create treatment timeline",
          },
        },
      },
      {
        id: "medical-5",
        type: "executor",
        position: { x: 250, y: 450 },
        data: {
          label: "Medical Summary",
          executor: {
            id: "summarize",
            type: "analyze",
            name: "AI Summarizer",
            color: "bg-accent",
            category: "analyze",
          },
          config: {
            name: "Medical Summary",
            description: "Generate comprehensive summary",
          },
        },
      },
    ],
    edges: [
      { id: "e1-2", source: "medical-1", target: "medical-2" },
      { id: "e2-3", source: "medical-2", target: "medical-3" },
      { id: "e3-4", source: "medical-3", target: "medical-4" },
      { id: "e4-5", source: "medical-4", target: "medical-5" },
    ],
  },
  {
    id: "property-damage-assessment",
    name: "Property Damage Assessment",
    description: "Analyze damage photos, extract repair estimates, and process adjuster reports with comparable claim analysis.",
    category: "analysis",
    steps: 5,
    estimatedTime: "3-4 min",
    useCases: [
      "Analyze damage photos and images",
      "Extract and validate repair estimates",
      "Process adjuster reports",
    ],
    features: [
      "Image analysis for damage detection",
      "Estimate validation and comparison",
      "Comparable claim analysis",
      "Total loss determination assistance",
    ],
    nodes: [
      {
        id: "damage-1",
        type: "executor",
        position: { x: 250, y: 50 },
        data: {
          label: "Photo Upload",
          executor: {
            id: "doc-crack",
            type: "extract",
            name: "Document Cracker",
            color: "bg-primary",
            category: "extract",
          },
          config: {
            name: "Photo Upload",
            description: "Load damage photos and reports",
          },
        },
      },
      {
        id: "damage-2",
        type: "executor",
        position: { x: 250, y: 150 },
        data: {
          label: "Image Analysis",
          executor: {
            id: "summarize",
            type: "analyze",
            name: "AI Summarizer",
            color: "bg-accent",
            category: "analyze",
          },
          config: {
            name: "Image Analysis",
            description: "Detect and classify damage",
          },
        },
      },
      {
        id: "damage-3",
        type: "executor",
        position: { x: 250, y: 250 },
        data: {
          label: "Estimate Extraction",
          executor: {
            id: "entity",
            type: "analyze",
            name: "Entity Extractor",
            color: "bg-primary",
            category: "analyze",
          },
          config: {
            name: "Estimate Extraction",
            description: "Extract repair costs and details",
          },
        },
      },
      {
        id: "damage-4",
        type: "executor",
        position: { x: 250, y: 350 },
        data: {
          label: "Comparable Analysis",
          executor: {
            id: "summarize",
            type: "analyze",
            name: "AI Summarizer",
            color: "bg-accent",
            category: "analyze",
          },
          config: {
            name: "Comparable Analysis",
            description: "Compare with similar claims",
          },
        },
      },
      {
        id: "damage-5",
        type: "executor",
        position: { x: 250, y: 450 },
        data: {
          label: "Assessment Report",
          executor: {
            id: "transform",
            type: "transform",
            name: "Content Transformer",
            color: "bg-secondary",
            category: "transform",
          },
          config: {
            name: "Assessment Report",
            description: "Generate damage assessment",
          },
        },
      },
    ],
    edges: [
      { id: "e1-2", source: "damage-1", target: "damage-2" },
      { id: "e2-3", source: "damage-2", target: "damage-3" },
      { id: "e3-4", source: "damage-3", target: "damage-4" },
      { id: "e4-5", source: "damage-4", target: "damage-5" },
    ],
  },
  {
    id: "underwriting-document-processing",
    name: "Underwriting Document Processing",
    description: "Process underwriting applications, analyze financial statements, and review inspection reports with automated risk scoring.",
    category: "extraction",
    steps: 5,
    estimatedTime: "3-4 min",
    useCases: [
      "Process application documents",
      "Analyze financial statements",
      "Review inspection reports",
    ],
    features: [
      "Risk factor extraction",
      "Financial ratio calculation",
      "Document completeness checking",
      "Automated risk scoring",
    ],
    nodes: [
      {
        id: "underwrite-1",
        type: "executor",
        position: { x: 250, y: 50 },
        data: {
          label: "Application Intake",
          executor: {
            id: "doc-crack",
            type: "extract",
            name: "Document Cracker",
            color: "bg-primary",
            category: "extract",
          },
          config: {
            name: "Application Intake",
            description: "Load underwriting documents",
          },
        },
      },
      {
        id: "underwrite-2",
        type: "executor",
        position: { x: 250, y: 150 },
        data: {
          label: "Data Extraction",
          executor: {
            id: "entity",
            type: "analyze",
            name: "Entity Extractor",
            color: "bg-primary",
            category: "analyze",
          },
          config: {
            name: "Data Extraction",
            description: "Extract applicant and financial data",
          },
        },
      },
      {
        id: "underwrite-3",
        type: "executor",
        position: { x: 250, y: 250 },
        data: {
          label: "Risk Analysis",
          executor: {
            id: "summarize",
            type: "analyze",
            name: "AI Summarizer",
            color: "bg-accent",
            category: "analyze",
          },
          config: {
            name: "Risk Analysis",
            description: "Identify and assess risk factors",
          },
        },
      },
      {
        id: "underwrite-4",
        type: "executor",
        position: { x: 250, y: 350 },
        data: {
          label: "Financial Analysis",
          executor: {
            id: "transform",
            type: "transform",
            name: "Content Transformer",
            color: "bg-secondary",
            category: "transform",
          },
          config: {
            name: "Financial Analysis",
            description: "Calculate key ratios",
          },
        },
      },
      {
        id: "underwrite-5",
        type: "executor",
        position: { x: 250, y: 450 },
        data: {
          label: "Risk Score",
          executor: {
            id: "transform",
            type: "transform",
            name: "Content Transformer",
            color: "bg-secondary",
            category: "transform",
          },
          config: {
            name: "Risk Score",
            description: "Generate automated risk score",
          },
        },
      },
    ],
    edges: [
      { id: "e1-2", source: "underwrite-1", target: "underwrite-2" },
      { id: "e2-3", source: "underwrite-2", target: "underwrite-3" },
      { id: "e3-4", source: "underwrite-3", target: "underwrite-4" },
      { id: "e4-5", source: "underwrite-4", target: "underwrite-5" },
    ],
  },
  {
    id: "regulatory-compliance-review",
    name: "Regulatory Compliance Document Review",
    description: "Review policies for compliance, extract regulatory requirements, and generate compliance reports with gap analysis.",
    category: "compliance",
    steps: 5,
    estimatedTime: "3-4 min",
    useCases: [
      "Review policies for regulatory compliance",
      "Extract regulatory requirements",
      "Generate compliance reports and audits",
    ],
    features: [
      "Regulation mapping and tracking",
      "Gap analysis and identification",
      "Compliance checklist generation",
      "Audit trail creation",
    ],
    nodes: [
      {
        id: "compliance-1",
        type: "executor",
        position: { x: 250, y: 50 },
        data: {
          label: "Document Upload",
          executor: {
            id: "doc-crack",
            type: "extract",
            name: "Document Cracker",
            color: "bg-primary",
            category: "extract",
          },
          config: {
            name: "Document Upload",
            description: "Load policy and regulatory documents",
          },
        },
      },
      {
        id: "compliance-2",
        type: "executor",
        position: { x: 250, y: 150 },
        data: {
          label: "Requirement Extraction",
          executor: {
            id: "entity",
            type: "analyze",
            name: "Entity Extractor",
            color: "bg-primary",
            category: "analyze",
          },
          config: {
            name: "Requirement Extraction",
            description: "Extract regulatory requirements",
          },
        },
      },
      {
        id: "compliance-3",
        type: "executor",
        position: { x: 250, y: 250 },
        data: {
          label: "Gap Analysis",
          executor: {
            id: "summarize",
            type: "analyze",
            name: "AI Summarizer",
            color: "bg-accent",
            category: "analyze",
          },
          config: {
            name: "Gap Analysis",
            description: "Identify compliance gaps",
          },
        },
      },
      {
        id: "compliance-4",
        type: "executor",
        position: { x: 250, y: 350 },
        data: {
          label: "Checklist Generation",
          executor: {
            id: "transform",
            type: "transform",
            name: "Content Transformer",
            color: "bg-secondary",
            category: "transform",
          },
          config: {
            name: "Checklist Generation",
            description: "Create compliance checklist",
          },
        },
      },
      {
        id: "compliance-5",
        type: "executor",
        position: { x: 250, y: 450 },
        data: {
          label: "Compliance Report",
          executor: {
            id: "transform",
            type: "transform",
            name: "Content Transformer",
            color: "bg-secondary",
            category: "transform",
          },
          config: {
            name: "Compliance Report",
            description: "Generate audit report",
          },
        },
      },
    ],
    edges: [
      { id: "e1-2", source: "compliance-1", target: "compliance-2" },
      { id: "e2-3", source: "compliance-2", target: "compliance-3" },
      { id: "e3-4", source: "compliance-3", target: "compliance-4" },
      { id: "e4-5", source: "compliance-4", target: "compliance-5" },
    ],
  },
  {
    id: "employee-onboarding-automation",
    name: "Employee Onboarding Automation",
    description: "Streamline new hire onboarding by processing documents, extracting employee data, and generating onboarding checklists and reports.",
    category: "automation",
    steps: 5,
    estimatedTime: "2-3 min",
    useCases: [
      "Process new hire paperwork and forms",
      "Extract employee information for HR systems",
      "Generate personalized onboarding checklists",
    ],
    features: [
      "Multi-document intake (I-9, W-4, benefits forms)",
      "Automated data validation",
      "System provisioning checklist generation",
      "Compliance verification",
    ],
    nodes: [
      {
        id: "onboard-1",
        type: "executor",
        position: { x: 250, y: 50 },
        data: {
          label: "Document Upload",
          executor: {
            id: "doc-crack",
            type: "extract",
            name: "Document Cracker",
            color: "bg-primary",
            category: "extract",
          },
          config: {
            name: "Document Upload",
            description: "Load onboarding documents",
          },
        },
      },
      {
        id: "onboard-2",
        type: "executor",
        position: { x: 250, y: 150 },
        data: {
          label: "Data Extraction",
          executor: {
            id: "entity",
            type: "analyze",
            name: "Entity Extractor",
            color: "bg-primary",
            category: "analyze",
          },
          config: {
            name: "Data Extraction",
            description: "Extract employee details",
          },
        },
      },
      {
        id: "onboard-3",
        type: "executor",
        position: { x: 250, y: 250 },
        data: {
          label: "Validation Check",
          executor: {
            id: "transform",
            type: "transform",
            name: "Content Transformer",
            color: "bg-secondary",
            category: "transform",
          },
          config: {
            name: "Validation Check",
            description: "Verify data completeness",
          },
        },
      },
      {
        id: "onboard-4",
        type: "executor",
        position: { x: 250, y: 350 },
        data: {
          label: "Checklist Generation",
          executor: {
            id: "summarize",
            type: "analyze",
            name: "AI Summarizer",
            color: "bg-accent",
            category: "analyze",
          },
          config: {
            name: "Checklist Generation",
            description: "Create personalized onboarding plan",
          },
        },
      },
      {
        id: "onboard-5",
        type: "executor",
        position: { x: 250, y: 450 },
        data: {
          label: "HR System Data",
          executor: {
            id: "transform",
            type: "transform",
            name: "Content Transformer",
            color: "bg-secondary",
            category: "transform",
          },
          config: {
            name: "HR System Data",
            description: "Format for HRIS integration",
          },
        },
      },
    ],
    edges: [
      { id: "e1-2", source: "onboard-1", target: "onboard-2" },
      { id: "e2-3", source: "onboard-2", target: "onboard-3" },
      { id: "e3-4", source: "onboard-3", target: "onboard-4" },
      { id: "e4-5", source: "onboard-4", target: "onboard-5" },
    ],
  },
  {
    id: "expense-report-processing",
    name: "Expense Report Processing",
    description: "Automate expense report validation by extracting receipt data, verifying policy compliance, and flagging anomalies for review.",
    category: "automation",
    steps: 5,
    estimatedTime: "2-3 min",
    useCases: [
      "Extract data from receipts and invoices",
      "Validate expenses against company policy",
      "Flag duplicate or suspicious expenses",
    ],
    features: [
      "OCR for receipt scanning",
      "Policy compliance checking",
      "Duplicate detection",
      "Multi-currency support",
    ],
    nodes: [
      {
        id: "expense-1",
        type: "executor",
        position: { x: 250, y: 50 },
        data: {
          label: "Receipt Upload",
          executor: {
            id: "doc-crack",
            type: "extract",
            name: "Document Cracker",
            color: "bg-primary",
            category: "extract",
          },
          config: {
            name: "Receipt Upload",
            description: "Load receipts and invoices",
          },
        },
      },
      {
        id: "expense-2",
        type: "executor",
        position: { x: 250, y: 150 },
        data: {
          label: "Data Extraction",
          executor: {
            id: "entity",
            type: "analyze",
            name: "Entity Extractor",
            color: "bg-primary",
            category: "analyze",
          },
          config: {
            name: "Data Extraction",
            description: "Extract amounts, dates, vendors",
          },
        },
      },
      {
        id: "expense-3",
        type: "executor",
        position: { x: 250, y: 250 },
        data: {
          label: "Policy Validation",
          executor: {
            id: "summarize",
            type: "analyze",
            name: "AI Summarizer",
            color: "bg-accent",
            category: "analyze",
          },
          config: {
            name: "Policy Validation",
            description: "Check against expense policies",
          },
        },
      },
      {
        id: "expense-4",
        type: "executor",
        position: { x: 250, y: 350 },
        data: {
          label: "Anomaly Detection",
          executor: {
            id: "summarize",
            type: "analyze",
            name: "AI Summarizer",
            color: "bg-accent",
            category: "analyze",
          },
          config: {
            name: "Anomaly Detection",
            description: "Flag duplicates and unusual expenses",
          },
        },
      },
      {
        id: "expense-5",
        type: "executor",
        position: { x: 250, y: 450 },
        data: {
          label: "Expense Report",
          executor: {
            id: "transform",
            type: "transform",
            name: "Content Transformer",
            color: "bg-secondary",
            category: "transform",
          },
          config: {
            name: "Expense Report",
            description: "Generate validation summary",
          },
        },
      },
    ],
    edges: [
      { id: "e1-2", source: "expense-1", target: "expense-2" },
      { id: "e2-3", source: "expense-2", target: "expense-3" },
      { id: "e3-4", source: "expense-3", target: "expense-4" },
      { id: "e4-5", source: "expense-4", target: "expense-5" },
    ],
  },
  {
    id: "vendor-invoice-processing",
    name: "Vendor Invoice Processing",
    description: "Process vendor invoices automatically by extracting data, matching against purchase orders, and routing for approval.",
    category: "automation",
    steps: 6,
    estimatedTime: "3-4 min",
    useCases: [
      "Extract invoice data for AP processing",
      "Match invoices to purchase orders",
      "Route invoices for approval workflows",
    ],
    features: [
      "3-way matching (PO, receipt, invoice)",
      "Automated data extraction",
      "Exception handling and routing",
      "Duplicate invoice detection",
    ],
    nodes: [
      {
        id: "invoice-1",
        type: "executor",
        position: { x: 250, y: 50 },
        data: {
          label: "Invoice Upload",
          executor: {
            id: "doc-crack",
            type: "extract",
            name: "Document Cracker",
            color: "bg-primary",
            category: "extract",
          },
          config: {
            name: "Invoice Upload",
            description: "Load vendor invoices",
          },
        },
      },
      {
        id: "invoice-2",
        type: "executor",
        position: { x: 250, y: 150 },
        data: {
          label: "Data Extraction",
          executor: {
            id: "entity",
            type: "analyze",
            name: "Entity Extractor",
            color: "bg-primary",
            category: "analyze",
          },
          config: {
            name: "Data Extraction",
            description: "Extract invoice details and line items",
          },
        },
      },
      {
        id: "invoice-3",
        type: "executor",
        position: { x: 250, y: 250 },
        data: {
          label: "PO Matching",
          executor: {
            id: "summarize",
            type: "analyze",
            name: "AI Summarizer",
            color: "bg-accent",
            category: "analyze",
          },
          config: {
            name: "PO Matching",
            description: "Match to purchase orders",
          },
        },
      },
      {
        id: "invoice-4",
        type: "executor",
        position: { x: 250, y: 350 },
        data: {
          label: "Duplicate Check",
          executor: {
            id: "transform",
            type: "transform",
            name: "Content Transformer",
            color: "bg-secondary",
            category: "transform",
          },
          config: {
            name: "Duplicate Check",
            description: "Identify duplicate invoices",
          },
        },
      },
      {
        id: "invoice-5",
        type: "executor",
        position: { x: 250, y: 450 },
        data: {
          label: "Exception Routing",
          executor: {
            id: "summarize",
            type: "analyze",
            name: "AI Summarizer",
            color: "bg-accent",
            category: "analyze",
          },
          config: {
            name: "Exception Routing",
            description: "Route exceptions for review",
          },
        },
      },
      {
        id: "invoice-6",
        type: "executor",
        position: { x: 250, y: 550 },
        data: {
          label: "Approval Package",
          executor: {
            id: "transform",
            type: "transform",
            name: "Content Transformer",
            color: "bg-secondary",
            category: "transform",
          },
          config: {
            name: "Approval Package",
            description: "Prepare for AP system",
          },
        },
      },
    ],
    edges: [
      { id: "e1-2", source: "invoice-1", target: "invoice-2" },
      { id: "e2-3", source: "invoice-2", target: "invoice-3" },
      { id: "e3-4", source: "invoice-3", target: "invoice-4" },
      { id: "e4-5", source: "invoice-4", target: "invoice-5" },
      { id: "e5-6", source: "invoice-5", target: "invoice-6" },
    ],
  },
  {
    id: "it-ticket-classification",
    name: "IT Support Ticket Classification",
    description: "Automatically classify and route IT support tickets based on content analysis, priority detection, and category assignment.",
    category: "automation",
    steps: 4,
    estimatedTime: "1-2 min",
    useCases: [
      "Classify tickets by category and urgency",
      "Extract key issues and error codes",
      "Auto-route to appropriate support teams",
    ],
    features: [
      "Intelligent category classification",
      "Priority scoring",
      "Sentiment analysis for escalation",
      "Similar ticket matching",
    ],
    nodes: [
      {
        id: "ticket-1",
        type: "executor",
        position: { x: 250, y: 50 },
        data: {
          label: "Ticket Intake",
          executor: {
            id: "doc-crack",
            type: "extract",
            name: "Document Cracker",
            color: "bg-primary",
            category: "extract",
          },
          config: {
            name: "Ticket Intake",
            description: "Load support ticket content",
          },
        },
      },
      {
        id: "ticket-2",
        type: "executor",
        position: { x: 250, y: 150 },
        data: {
          label: "Issue Analysis",
          executor: {
            id: "summarize",
            type: "analyze",
            name: "AI Summarizer",
            color: "bg-accent",
            category: "analyze",
          },
          config: {
            name: "Issue Analysis",
            description: "Analyze problem description",
          },
        },
      },
      {
        id: "ticket-3",
        type: "executor",
        position: { x: 250, y: 250 },
        data: {
          label: "Classification",
          executor: {
            id: "entity",
            type: "analyze",
            name: "Entity Extractor",
            color: "bg-primary",
            category: "analyze",
          },
          config: {
            name: "Classification",
            description: "Categorize and prioritize",
          },
        },
      },
      {
        id: "ticket-4",
        type: "executor",
        position: { x: 250, y: 350 },
        data: {
          label: "Routing Decision",
          executor: {
            id: "transform",
            type: "transform",
            name: "Content Transformer",
            color: "bg-secondary",
            category: "transform",
          },
          config: {
            name: "Routing Decision",
            description: "Assign to support team",
          },
        },
      },
    ],
    edges: [
      { id: "e1-2", source: "ticket-1", target: "ticket-2" },
      { id: "e2-3", source: "ticket-2", target: "ticket-3" },
      { id: "e3-4", source: "ticket-3", target: "ticket-4" },
    ],
  },
  {
    id: "meeting-notes-summarization",
    name: "Meeting Notes & Action Items",
    description: "Process meeting transcripts and notes to extract action items, decisions, and key discussion points with participant tracking.",
    category: "analysis",
    steps: 5,
    estimatedTime: "2-3 min",
    useCases: [
      "Extract action items from meeting notes",
      "Identify key decisions and outcomes",
      "Track participant contributions",
    ],
    features: [
      "Action item extraction with owners",
      "Decision point identification",
      "Topic segmentation",
      "Follow-up reminder generation",
    ],
    nodes: [
      {
        id: "meeting-1",
        type: "executor",
        position: { x: 250, y: 50 },
        data: {
          label: "Notes Upload",
          executor: {
            id: "doc-crack",
            type: "extract",
            name: "Document Cracker",
            color: "bg-primary",
            category: "extract",
          },
          config: {
            name: "Notes Upload",
            description: "Load meeting transcripts or notes",
          },
        },
      },
      {
        id: "meeting-2",
        type: "executor",
        position: { x: 250, y: 150 },
        data: {
          label: "Content Analysis",
          executor: {
            id: "summarize",
            type: "analyze",
            name: "AI Summarizer",
            color: "bg-accent",
            category: "analyze",
          },
          config: {
            name: "Content Analysis",
            description: "Analyze meeting content",
          },
        },
      },
      {
        id: "meeting-3",
        type: "executor",
        position: { x: 150, y: 250 },
        data: {
          label: "Action Items",
          executor: {
            id: "entity",
            type: "analyze",
            name: "Entity Extractor",
            color: "bg-primary",
            category: "analyze",
          },
          config: {
            name: "Action Items",
            description: "Extract tasks and owners",
          },
        },
      },
      {
        id: "meeting-4",
        type: "executor",
        position: { x: 350, y: 250 },
        data: {
          label: "Key Decisions",
          executor: {
            id: "entity",
            type: "analyze",
            name: "Entity Extractor",
            color: "bg-primary",
            category: "analyze",
          },
          config: {
            name: "Key Decisions",
            description: "Identify decisions and outcomes",
          },
        },
      },
      {
        id: "meeting-5",
        type: "executor",
        position: { x: 250, y: 350 },
        data: {
          label: "Meeting Summary",
          executor: {
            id: "transform",
            type: "transform",
            name: "Content Transformer",
            color: "bg-secondary",
            category: "transform",
          },
          config: {
            name: "Meeting Summary",
            description: "Generate structured summary",
          },
        },
      },
    ],
    edges: [
      { id: "e1-2", source: "meeting-1", target: "meeting-2" },
      { id: "e2-3", source: "meeting-2", target: "meeting-3" },
      { id: "e2-4", source: "meeting-2", target: "meeting-4" },
      { id: "e3-5", source: "meeting-3", target: "meeting-5" },
      { id: "e4-5", source: "meeting-4", target: "meeting-5" },
    ],
  },
  {
    id: "nda-contract-processing",
    name: "NDA & Contract Processing",
    description: "Streamline NDA and contract review by extracting key terms, identifying parties, tracking effective dates, and flagging unusual clauses.",
    category: "analysis",
    steps: 5,
    estimatedTime: "2-3 min",
    useCases: [
      "Extract parties and effective dates",
      "Identify confidentiality terms",
      "Track contract obligations and expiration",
    ],
    features: [
      "Automatic term extraction",
      "Party identification",
      "Expiration date tracking",
      "Non-standard clause detection",
    ],
    nodes: [
      {
        id: "nda-1",
        type: "executor",
        position: { x: 250, y: 50 },
        data: {
          label: "Contract Upload",
          executor: {
            id: "doc-crack",
            type: "extract",
            name: "Document Cracker",
            color: "bg-primary",
            category: "extract",
          },
          config: {
            name: "Contract Upload",
            description: "Load NDA or contract",
          },
        },
      },
      {
        id: "nda-2",
        type: "executor",
        position: { x: 250, y: 150 },
        data: {
          label: "Key Terms Extraction",
          executor: {
            id: "entity",
            type: "analyze",
            name: "Entity Extractor",
            color: "bg-primary",
            category: "analyze",
          },
          config: {
            name: "Key Terms Extraction",
            description: "Extract dates, parties, obligations",
          },
        },
      },
      {
        id: "nda-3",
        type: "executor",
        position: { x: 250, y: 250 },
        data: {
          label: "Clause Analysis",
          executor: {
            id: "summarize",
            type: "analyze",
            name: "AI Summarizer",
            color: "bg-accent",
            category: "analyze",
          },
          config: {
            name: "Clause Analysis",
            description: "Analyze confidentiality terms",
          },
        },
      },
      {
        id: "nda-4",
        type: "executor",
        position: { x: 250, y: 350 },
        data: {
          label: "Risk Assessment",
          executor: {
            id: "summarize",
            type: "analyze",
            name: "AI Summarizer",
            color: "bg-accent",
            category: "analyze",
          },
          config: {
            name: "Risk Assessment",
            description: "Flag unusual or risky terms",
          },
        },
      },
      {
        id: "nda-5",
        type: "executor",
        position: { x: 250, y: 450 },
        data: {
          label: "Contract Summary",
          executor: {
            id: "transform",
            type: "transform",
            name: "Content Transformer",
            color: "bg-secondary",
            category: "transform",
          },
          config: {
            name: "Contract Summary",
            description: "Generate contract metadata",
          },
        },
      },
    ],
    edges: [
      { id: "e1-2", source: "nda-1", target: "nda-2" },
      { id: "e2-3", source: "nda-2", target: "nda-3" },
      { id: "e3-4", source: "nda-3", target: "nda-4" },
      { id: "e4-5", source: "nda-4", target: "nda-5" },
    ],
  },
  {
    id: "procurement-request-processing",
    name: "Procurement Request Processing",
    description: "Automate procurement requests by extracting requirements, validating budgets, and routing for approvals based on spend thresholds.",
    category: "automation",
    steps: 5,
    estimatedTime: "2-3 min",
    useCases: [
      "Extract item details and justifications",
      "Validate against budget allocations",
      "Route based on approval hierarchy",
    ],
    features: [
      "Requirement extraction",
      "Budget validation",
      "Approval workflow routing",
      "Vendor suggestion based on history",
    ],
    nodes: [
      {
        id: "procure-1",
        type: "executor",
        position: { x: 250, y: 50 },
        data: {
          label: "Request Upload",
          executor: {
            id: "doc-crack",
            type: "extract",
            name: "Document Cracker",
            color: "bg-primary",
            category: "extract",
          },
          config: {
            name: "Request Upload",
            description: "Load procurement request",
          },
        },
      },
      {
        id: "procure-2",
        type: "executor",
        position: { x: 250, y: 150 },
        data: {
          label: "Data Extraction",
          executor: {
            id: "entity",
            type: "analyze",
            name: "Entity Extractor",
            color: "bg-primary",
            category: "analyze",
          },
          config: {
            name: "Data Extraction",
            description: "Extract items, quantities, costs",
          },
        },
      },
      {
        id: "procure-3",
        type: "executor",
        position: { x: 250, y: 250 },
        data: {
          label: "Budget Validation",
          executor: {
            id: "transform",
            type: "transform",
            name: "Content Transformer",
            color: "bg-secondary",
            category: "transform",
          },
          config: {
            name: "Budget Validation",
            description: "Check budget availability",
          },
        },
      },
      {
        id: "procure-4",
        type: "executor",
        position: { x: 250, y: 350 },
        data: {
          label: "Approval Routing",
          executor: {
            id: "summarize",
            type: "analyze",
            name: "AI Summarizer",
            color: "bg-accent",
            category: "analyze",
          },
          config: {
            name: "Approval Routing",
            description: "Determine approval path",
          },
        },
      },
      {
        id: "procure-5",
        type: "executor",
        position: { x: 250, y: 450 },
        data: {
          label: "Request Package",
          executor: {
            id: "transform",
            type: "transform",
            name: "Content Transformer",
            color: "bg-secondary",
            category: "transform",
          },
          config: {
            name: "Request Package",
            description: "Prepare approval package",
          },
        },
      },
    ],
    edges: [
      { id: "e1-2", source: "procure-1", target: "procure-2" },
      { id: "e2-3", source: "procure-2", target: "procure-3" },
      { id: "e3-4", source: "procure-3", target: "procure-4" },
      { id: "e4-5", source: "procure-4", target: "procure-5" },
    ],
  },
  {
    id: "security-incident-reporting",
    name: "Security Incident Report Analysis",
    description: "Process security incident reports to extract threat indicators, classify severity, and generate response recommendations.",
    category: "analysis",
    steps: 5,
    estimatedTime: "2-3 min",
    useCases: [
      "Extract threat indicators and IOCs",
      "Classify incident severity",
      "Generate incident response plans",
    ],
    features: [
      "Threat indicator extraction",
      "Severity classification",
      "Timeline reconstruction",
      "Response recommendation generation",
    ],
    nodes: [
      {
        id: "security-1",
        type: "executor",
        position: { x: 250, y: 50 },
        data: {
          label: "Report Upload",
          executor: {
            id: "doc-crack",
            type: "extract",
            name: "Document Cracker",
            color: "bg-primary",
            category: "extract",
          },
          config: {
            name: "Report Upload",
            description: "Load incident reports",
          },
        },
      },
      {
        id: "security-2",
        type: "executor",
        position: { x: 250, y: 150 },
        data: {
          label: "IOC Extraction",
          executor: {
            id: "entity",
            type: "analyze",
            name: "Entity Extractor",
            color: "bg-primary",
            category: "analyze",
          },
          config: {
            name: "IOC Extraction",
            description: "Extract indicators of compromise",
          },
        },
      },
      {
        id: "security-3",
        type: "executor",
        position: { x: 250, y: 250 },
        data: {
          label: "Severity Classification",
          executor: {
            id: "summarize",
            type: "analyze",
            name: "AI Summarizer",
            color: "bg-accent",
            category: "analyze",
          },
          config: {
            name: "Severity Classification",
            description: "Assess incident severity",
          },
        },
      },
      {
        id: "security-4",
        type: "executor",
        position: { x: 250, y: 350 },
        data: {
          label: "Timeline Analysis",
          executor: {
            id: "transform",
            type: "transform",
            name: "Content Transformer",
            color: "bg-secondary",
            category: "transform",
          },
          config: {
            name: "Timeline Analysis",
            description: "Reconstruct incident timeline",
          },
        },
      },
      {
        id: "security-5",
        type: "executor",
        position: { x: 250, y: 450 },
        data: {
          label: "Response Plan",
          executor: {
            id: "summarize",
            type: "analyze",
            name: "AI Summarizer",
            color: "bg-accent",
            category: "analyze",
          },
          config: {
            name: "Response Plan",
            description: "Generate response recommendations",
          },
        },
      },
    ],
    edges: [
      { id: "e1-2", source: "security-1", target: "security-2" },
      { id: "e2-3", source: "security-2", target: "security-3" },
      { id: "e3-4", source: "security-3", target: "security-4" },
      { id: "e4-5", source: "security-4", target: "security-5" },
    ],
  },
  {
    id: "knowledge-base-article-generation",
    name: "Knowledge Base Article Generation",
    description: "Transform technical documentation and troubleshooting guides into searchable knowledge base articles with metadata tagging.",
    category: "knowledge",
    steps: 5,
    estimatedTime: "2-3 min",
    useCases: [
      "Convert documentation to KB articles",
      "Extract common issues and solutions",
      "Generate article metadata and tags",
    ],
    features: [
      "Content summarization and structuring",
      "Automatic tagging and categorization",
      "FAQ generation from content",
      "Related article linking",
    ],
    nodes: [
      {
        id: "kb-1",
        type: "executor",
        position: { x: 250, y: 50 },
        data: {
          label: "Document Upload",
          executor: {
            id: "doc-crack",
            type: "extract",
            name: "Document Cracker",
            color: "bg-primary",
            category: "extract",
          },
          config: {
            name: "Document Upload",
            description: "Load source documentation",
          },
        },
      },
      {
        id: "kb-2",
        type: "executor",
        position: { x: 250, y: 150 },
        data: {
          label: "Content Analysis",
          executor: {
            id: "summarize",
            type: "analyze",
            name: "AI Summarizer",
            color: "bg-accent",
            category: "analyze",
          },
          config: {
            name: "Content Analysis",
            description: "Analyze and summarize content",
          },
        },
      },
      {
        id: "kb-3",
        type: "executor",
        position: { x: 250, y: 250 },
        data: {
          label: "Issue Extraction",
          executor: {
            id: "entity",
            type: "analyze",
            name: "Entity Extractor",
            color: "bg-primary",
            category: "analyze",
          },
          config: {
            name: "Issue Extraction",
            description: "Extract problems and solutions",
          },
        },
      },
      {
        id: "kb-4",
        type: "executor",
        position: { x: 250, y: 350 },
        data: {
          label: "Tagging",
          executor: {
            id: "entity",
            type: "analyze",
            name: "Entity Extractor",
            color: "bg-primary",
            category: "analyze",
          },
          config: {
            name: "Tagging",
            description: "Generate metadata and tags",
          },
        },
      },
      {
        id: "kb-5",
        type: "executor",
        position: { x: 250, y: 450 },
        data: {
          label: "Article Format",
          executor: {
            id: "transform",
            type: "transform",
            name: "Content Transformer",
            color: "bg-secondary",
            category: "transform",
          },
          config: {
            name: "Article Format",
            description: "Format for KB publication",
          },
        },
      },
    ],
    edges: [
      { id: "e1-2", source: "kb-1", target: "kb-2" },
      { id: "e2-3", source: "kb-2", target: "kb-3" },
      { id: "e3-4", source: "kb-3", target: "kb-4" },
      { id: "e4-5", source: "kb-4", target: "kb-5" },
    ],
  },
  {
    id: "timesheet-validation",
    name: "Timesheet Validation & Processing",
    description: "Automate timesheet processing by extracting hours, validating against project codes, and flagging discrepancies for review.",
    category: "automation",
    steps: 4,
    estimatedTime: "1-2 min",
    useCases: [
      "Extract hours by project and task",
      "Validate against work schedules",
      "Flag overtime and anomalies",
    ],
    features: [
      "Time entry extraction",
      "Project code validation",
      "Overtime calculation",
      "Pattern-based anomaly detection",
    ],
    nodes: [
      {
        id: "time-1",
        type: "executor",
        position: { x: 250, y: 50 },
        data: {
          label: "Timesheet Upload",
          executor: {
            id: "doc-crack",
            type: "extract",
            name: "Document Cracker",
            color: "bg-primary",
            category: "extract",
          },
          config: {
            name: "Timesheet Upload",
            description: "Load timesheet data",
          },
        },
      },
      {
        id: "time-2",
        type: "executor",
        position: { x: 250, y: 150 },
        data: {
          label: "Data Extraction",
          executor: {
            id: "entity",
            type: "analyze",
            name: "Entity Extractor",
            color: "bg-primary",
            category: "analyze",
          },
          config: {
            name: "Data Extraction",
            description: "Extract hours and project codes",
          },
        },
      },
      {
        id: "time-3",
        type: "executor",
        position: { x: 250, y: 250 },
        data: {
          label: "Validation",
          executor: {
            id: "transform",
            type: "transform",
            name: "Content Transformer",
            color: "bg-secondary",
            category: "transform",
          },
          config: {
            name: "Validation",
            description: "Validate hours and codes",
          },
        },
      },
      {
        id: "time-4",
        type: "executor",
        position: { x: 250, y: 350 },
        data: {
          label: "Exception Report",
          executor: {
            id: "summarize",
            type: "analyze",
            name: "AI Summarizer",
            color: "bg-accent",
            category: "analyze",
          },
          config: {
            name: "Exception Report",
            description: "Flag discrepancies",
          },
        },
      },
    ],
    edges: [
      { id: "e1-2", source: "time-1", target: "time-2" },
      { id: "e2-3", source: "time-2", target: "time-3" },
      { id: "e3-4", source: "time-3", target: "time-4" },
    ],
  },
];