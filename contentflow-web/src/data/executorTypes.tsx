import {
  FileText, Brain, GitBranch, Database, FileImage, FileVideo, FileAudio, 
  Languages, Image, Video, Music, Sparkles, Tag, Search, Filter, Combine, 
  Split, Link, FileCode, Mail, Globe, BookOpen, Hash, Clock, AlertCircle, 
  CheckCircle, XCircle, Zap, Settings, FileJson, FileSpreadsheet, Percent, 
  Type, Palette, Film, Wand2, Network, Cloud, HardDrive, FolderInput, Save, 
  CloudUpload, Server, Container, Eye, MessageSquare, FileSearch, Mic, 
  ScanText, BookText, Sparkle, Layers, Box, Workflow
} from "lucide-react";
import type { ExecutorType } from "@/types/components";

export type { ExecutorType } from "@/types/components";

export const executorTypes: ExecutorType[] = [
  // Input Sources
  { 
    id: "blob-input", 
    type: "input", 
    name: "Azure Blob Storage", 
    icon: <Cloud className="w-5 h-5" />, 
    color: "bg-sky-500", 
    category: "input",
    description: "Read files from Azure Blob Storage containers"
  },
  { 
    id: "adls-input", 
    type: "input", 
    name: "Azure Data Lake", 
    icon: <HardDrive className="w-5 h-5" />, 
    color: "bg-sky-600", 
    category: "input",
    description: "Access data from Azure Data Lake Storage Gen2"
  },
  { 
    id: "cosmos-input", 
    type: "input", 
    name: "Cosmos DB Input", 
    icon: <Database className="w-5 h-5" />, 
    color: "bg-sky-700", 
    category: "input",
    description: "Query documents from Azure Cosmos DB"
  },
  { 
    id: "sql-input", 
    type: "input", 
    name: "Azure SQL Input", 
    icon: <Server className="w-5 h-5" />, 
    color: "bg-sky-800", 
    category: "input",
    description: "Read data from Azure SQL Database"
  },
  { 
    id: "file-input", 
    type: "input", 
    name: "Local File Input", 
    icon: <FolderInput className="w-5 h-5" />, 
    color: "bg-sky-500", 
    category: "input",
    description: "Upload and process local files"
  },
  { 
    id: "sharepoint-input", 
    type: "input", 
    name: "SharePoint Input", 
    icon: <Globe className="w-5 h-5" />, 
    color: "bg-sky-600", 
    category: "input",
    description: "Access documents from SharePoint sites"
  },
  { 
    id: "onedrive-input", 
    type: "input", 
    name: "OneDrive Input", 
    icon: <CloudUpload className="w-5 h-5" />, 
    color: "bg-sky-700", 
    category: "input",
    description: "Read files from OneDrive for Business"
  },
  
  // Document & Text Extraction
  { 
    id: "doc-crack", 
    type: "extract", 
    name: "Document Cracker", 
    icon: <FileText className="w-5 h-5" />, 
    color: "bg-blue-500", 
    category: "extract",
    description: "Extract content from various document formats"
  },
  { 
    id: "azure-doc-intelligence", 
    type: "extract", 
    name: "Azure Document Intelligence", 
    icon: <ScanText className="w-5 h-5" />, 
    color: "bg-blue-500", 
    category: "extract",
    description: "Extract text, tables, and structure from documents using Azure AI"
  },
  { 
    id: "azure-content-understanding", 
    type: "extract", 
    name: "Azure Content Understanding", 
    icon: <Eye className="w-5 h-5" />, 
    color: "bg-blue-600", 
    category: "extract",
    description: "Analyze and understand document content with Azure AI"
  },
  { 
    id: "pdf-extract", 
    type: "extract", 
    name: "PDF Extractor", 
    icon: <FileText className="w-5 h-5" />, 
    color: "bg-blue-700", 
    category: "extract",
    description: "Extract text and metadata from PDF files"
  },
  { 
    id: "ocr", 
    type: "extract", 
    name: "OCR Scanner", 
    icon: <FileImage className="w-5 h-5" />, 
    color: "bg-blue-800", 
    category: "extract",
    description: "Optical character recognition for images"
  },
  { 
    id: "web-scraper", 
    type: "extract", 
    name: "Web Scraper", 
    icon: <Globe className="w-5 h-5" />, 
    color: "bg-blue-500", 
    category: "extract",
    description: "Extract content from web pages"
  },
  { 
    id: "email-parser", 
    type: "extract", 
    name: "Email Parser", 
    icon: <Mail className="w-5 h-5" />, 
    color: "bg-blue-600", 
    category: "extract",
    description: "Parse and extract data from email messages"
  },
  { 
    id: "code-parser", 
    type: "extract", 
    name: "Code Parser", 
    icon: <FileCode className="w-5 h-5" />, 
    color: "bg-blue-700", 
    category: "extract",
    description: "Analyze and extract information from source code"
  },
  
  // Media Extraction & Processing
  { 
    id: "azure-speech-transcription", 
    type: "media", 
    name: "Azure Speech Transcription", 
    icon: <Mic className="w-5 h-5" />, 
    color: "bg-purple-500", 
    category: "media",
    description: "Transcribe audio to text using Azure Speech Services"
  },
  { 
    id: "azure-video-indexer", 
    type: "media", 
    name: "Azure Video Indexer", 
    icon: <Film className="w-5 h-5" />, 
    color: "bg-purple-600", 
    category: "media",
    description: "Extract insights from videos using Azure Video Indexer"
  },
  { 
    id: "azure-computer-vision", 
    type: "media", 
    name: "Azure Computer Vision", 
    icon: <Eye className="w-5 h-5" />, 
    color: "bg-purple-700", 
    category: "media",
    description: "Analyze images with Azure Computer Vision"
  },
  { 
    id: "image-extract", 
    type: "extract", 
    name: "Image Extractor", 
    icon: <Image className="w-5 h-5" />, 
    color: "bg-purple-500", 
    category: "media",
    description: "Extract images from documents and media"
  },
  { 
    id: "video-extract", 
    type: "extract", 
    name: "Video Extractor", 
    icon: <Video className="w-5 h-5" />, 
    color: "bg-purple-600", 
    category: "media",
    description: "Extract video content and metadata"
  },
  { 
    id: "audio-extract", 
    type: "extract", 
    name: "Audio Extractor", 
    icon: <Music className="w-5 h-5" />, 
    color: "bg-purple-700", 
    category: "media",
    description: "Extract audio tracks from media files"
  },
  { 
    id: "speech-to-text", 
    type: "extract", 
    name: "Speech to Text", 
    icon: <FileAudio className="w-5 h-5" />, 
    color: "bg-purple-800", 
    category: "media",
    description: "Convert speech to text"
  },
  { 
    id: "video-to-text", 
    type: "extract", 
    name: "Video Transcriber", 
    icon: <FileVideo className="w-5 h-5" />, 
    color: "bg-purple-500", 
    category: "media",
    description: "Transcribe spoken content from videos"
  },
  
  // Content Transformation
  { 
    id: "transform", 
    type: "transform", 
    name: "Content Transformer", 
    icon: <GitBranch className="w-5 h-5" />, 
    color: "bg-green-500", 
    category: "transform",
    description: "Transform content between different formats"
  },
  { 
    id: "azure-translator", 
    type: "transform", 
    name: "Azure Translator", 
    icon: <Languages className="w-5 h-5" />, 
    color: "bg-green-600", 
    category: "transform",
    description: "Translate text using Azure Translator Service"
  },
  { 
    id: "translate", 
    type: "transform", 
    name: "Language Translator", 
    icon: <Languages className="w-5 h-5" />, 
    color: "bg-green-700", 
    category: "transform",
    description: "Translate content between languages"
  },
  { 
    id: "format-convert", 
    type: "transform", 
    name: "Format Converter", 
    icon: <FileJson className="w-5 h-5" />, 
    color: "bg-green-800", 
    category: "transform",
    description: "Convert between different file formats"
  },
  { 
    id: "text-clean", 
    type: "transform", 
    name: "Text Cleaner", 
    icon: <Sparkles className="w-5 h-5" />, 
    color: "bg-green-500", 
    category: "transform",
    description: "Clean and normalize text content"
  },
  { 
    id: "merge", 
    type: "transform", 
    name: "Content Merger", 
    icon: <Combine className="w-5 h-5" />, 
    color: "bg-green-600", 
    category: "transform",
    description: "Combine multiple content items"
  },
  { 
    id: "split", 
    type: "transform", 
    name: "Content Splitter", 
    icon: <Split className="w-5 h-5" />, 
    color: "bg-green-700", 
    category: "transform",
    description: "Split content into smaller parts"
  },
  { 
    id: "chunk", 
    type: "transform", 
    name: "Text Chunker", 
    icon: <FileSpreadsheet className="w-5 h-5" />, 
    color: "bg-green-800", 
    category: "transform",
    description: "Break text into semantic chunks"
  },
  { 
    id: "normalize", 
    type: "transform", 
    name: "Data Normalizer", 
    icon: <Settings className="w-5 h-5" />, 
    color: "bg-green-500", 
    category: "transform",
    description: "Normalize data formats and structures"
  },
  
  // AI Analysis
  { 
    id: "azure-openai-analyze", 
    type: "analyze", 
    name: "Azure OpenAI Analysis", 
    icon: <Sparkle className="w-5 h-5" />, 
    color: "bg-orange-500", 
    category: "analyze",
    description: "Analyze content using Azure OpenAI models"
  },
  { 
    id: "azure-text-analytics", 
    type: "analyze", 
    name: "Azure Text Analytics", 
    icon: <FileSearch className="w-5 h-5" />, 
    color: "bg-orange-600", 
    category: "analyze",
    description: "Extract insights with Azure Text Analytics"
  },
  { 
    id: "azure-content-safety", 
    type: "analyze", 
    name: "Azure Content Safety", 
    icon: <AlertCircle className="w-5 h-5" />, 
    color: "bg-orange-700", 
    category: "analyze",
    description: "Detect harmful content using Azure Content Safety"
  },
  { 
    id: "summarize", 
    type: "analyze", 
    name: "AI Summarizer", 
    icon: <Brain className="w-5 h-5" />, 
    color: "bg-orange-800", 
    category: "analyze",
    description: "Generate summaries using AI"
  },
  { 
    id: "entity", 
    type: "analyze", 
    name: "Entity Extractor", 
    icon: <Database className="w-5 h-5" />, 
    color: "bg-orange-500", 
    category: "analyze",
    description: "Extract named entities from text"
  },
  { 
    id: "sentiment", 
    type: "analyze", 
    name: "Sentiment Analyzer", 
    icon: <Percent className="w-5 h-5" />, 
    color: "bg-orange-600", 
    category: "analyze",
    description: "Analyze sentiment in text"
  },
  { 
    id: "classify", 
    type: "analyze", 
    name: "Content Classifier", 
    icon: <Tag className="w-5 h-5" />, 
    color: "bg-orange-700", 
    category: "analyze",
    description: "Classify content into categories"
  },
  { 
    id: "keyword", 
    type: "analyze", 
    name: "Keyword Extractor", 
    icon: <Hash className="w-5 h-5" />, 
    color: "bg-orange-800", 
    category: "analyze",
    description: "Extract key terms and phrases"
  },
  { 
    id: "topic", 
    type: "analyze", 
    name: "Topic Modeler", 
    icon: <BookOpen className="w-5 h-5" />, 
    color: "bg-orange-500", 
    category: "analyze",
    description: "Identify topics in text collections"
  },
  { 
    id: "intent", 
    type: "analyze", 
    name: "Intent Detector", 
    icon: <Search className="w-5 h-5" />, 
    color: "bg-orange-600", 
    category: "analyze",
    description: "Detect user intent in text"
  },
  { 
    id: "similarity", 
    type: "analyze", 
    name: "Similarity Matcher", 
    icon: <Link className="w-5 h-5" />, 
    color: "bg-orange-700", 
    category: "analyze",
    description: "Find similar content"
  },
  { 
    id: "pii-detect", 
    type: "analyze", 
    name: "PII Detector", 
    icon: <AlertCircle className="w-5 h-5" />, 
    color: "bg-orange-800", 
    category: "analyze",
    description: "Detect personally identifiable information"
  },
  
  // Enrichment
  { 
    id: "azure-openai-embeddings", 
    type: "enrichment", 
    name: "Azure OpenAI Embeddings", 
    icon: <Box className="w-5 h-5" />, 
    color: "bg-cyan-500", 
    category: "enrichment",
    description: "Generate vector embeddings using Azure OpenAI"
  },
  { 
    id: "metadata", 
    type: "enrichment", 
    name: "Metadata Enricher", 
    icon: <Database className="w-5 h-5" />, 
    color: "bg-cyan-600", 
    category: "enrichment",
    description: "Add metadata to content"
  },
  { 
    id: "timestamp", 
    type: "enrichment", 
    name: "Timestamp Adder", 
    icon: <Clock className="w-5 h-5" />, 
    color: "bg-cyan-700", 
    category: "enrichment",
    description: "Add temporal information"
  },
  { 
    id: "auto-tag", 
    type: "enrichment", 
    name: "Auto Tagger", 
    icon: <Tag className="w-5 h-5" />, 
    color: "bg-cyan-800", 
    category: "enrichment",
    description: "Automatically tag content"
  },
  { 
    id: "link-extract", 
    type: "enrichment", 
    name: "Link Extractor", 
    icon: <Link className="w-5 h-5" />, 
    color: "bg-cyan-500", 
    category: "enrichment",
    description: "Extract URLs and references"
  },
  { 
    id: "color-extract", 
    type: "enrichment", 
    name: "Color Extractor", 
    icon: <Palette className="w-5 h-5" />, 
    color: "bg-cyan-600", 
    category: "enrichment",
    description: "Extract color palettes from images"
  },
  { 
    id: "style-detect", 
    type: "enrichment", 
    name: "Style Detector", 
    icon: <Type className="w-5 h-5" />, 
    color: "bg-cyan-700", 
    category: "enrichment",
    description: "Detect content style and tone"
  },
  
  // Validation & Quality
  { 
    id: "validate", 
    type: "analyze", 
    name: "Content Validator", 
    icon: <CheckCircle className="w-5 h-5" />, 
    color: "bg-red-500", 
    category: "analyze",
    description: "Validate content structure and quality"
  },
  { 
    id: "quality-check", 
    type: "analyze", 
    name: "Quality Checker", 
    icon: <Zap className="w-5 h-5" />, 
    color: "bg-red-600", 
    category: "analyze",
    description: "Assess content quality"
  },
  { 
    id: "duplicate-detect", 
    type: "analyze", 
    name: "Duplicate Detector", 
    icon: <XCircle className="w-5 h-5" />, 
    color: "bg-red-700", 
    category: "analyze",
    description: "Find duplicate content"
  },
  { 
    id: "filter", 
    type: "transform", 
    name: "Content Filter", 
    icon: <Filter className="w-5 h-5" />, 
    color: "bg-red-800", 
    category: "transform",
    description: "Filter content based on criteria"
  },
  
  // Output Destinations
  { 
    id: "ai-search-output", 
    type: "output", 
    name: "Azure AI Search", 
    icon: <Search className="w-5 h-5" />, 
    color: "bg-indigo-500", 
    category: "output",
    description: "Index content in Azure AI Search"
  },
  { 
    id: "cosmos-output", 
    type: "output", 
    name: "Cosmos DB Output", 
    icon: <Database className="w-5 h-5" />, 
    color: "bg-indigo-600", 
    category: "output",
    description: "Store documents in Azure Cosmos DB"
  },
  { 
    id: "postgres-output", 
    type: "output", 
    name: "PostgreSQL Output", 
    icon: <Server className="w-5 h-5" />, 
    color: "bg-indigo-700", 
    category: "output",
    description: "Write data to PostgreSQL"
  },
  { 
    id: "sql-output", 
    type: "output", 
    name: "Azure SQL Output", 
    icon: <Database className="w-5 h-5" />, 
    color: "bg-indigo-800", 
    category: "output",
    description: "Store data in Azure SQL Database"
  },
  { 
    id: "blob-output", 
    type: "output", 
    name: "Blob Storage Output", 
    icon: <Cloud className="w-5 h-5" />, 
    color: "bg-indigo-500", 
    category: "output",
    description: "Write files to Azure Blob Storage"
  },
  { 
    id: "adls-output", 
    type: "output", 
    name: "Data Lake Output", 
    icon: <HardDrive className="w-5 h-5" />, 
    color: "bg-indigo-600", 
    category: "output",
    description: "Store data in Azure Data Lake"
  },
  { 
    id: "eventhub-output", 
    type: "output", 
    name: "Event Hub Output", 
    icon: <Container className="w-5 h-5" />, 
    color: "bg-indigo-700", 
    category: "output",
    description: "Stream events to Azure Event Hub"
  },
  { 
    id: "file-output", 
    type: "output", 
    name: "Local File Output", 
    icon: <Save className="w-5 h-5" />, 
    color: "bg-indigo-800", 
    category: "output",
    description: "Save files locally"
  },
  { 
    id: "azure-functions-output", 
    type: "output", 
    name: "Azure Functions Trigger", 
    icon: <Zap className="w-5 h-5" />, 
    color: "bg-indigo-500", 
    category: "output",
    description: "Trigger Azure Functions with processed content"
  },
  { 
    id: "service-bus-output", 
    type: "output", 
    name: "Service Bus Output", 
    icon: <MessageSquare className="w-5 h-5" />, 
    color: "bg-indigo-600", 
    category: "output",
    description: "Send messages to Azure Service Bus"
  },
  
  // Workflow
  { 
    id: "subpipeline", 
    type: "pipeline", 
    name: "Sub-Pipeline", 
    icon: <Workflow className="w-5 h-5" />, 
    color: "bg-gradient-primary", 
    category: "pipeline",
    description: "Execute a nested pipeline within the main pipeline"
  },
];
