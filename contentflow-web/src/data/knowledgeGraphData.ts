import { Node as FlowNode, Edge as FlowEdge, MarkerType } from "reactflow";

export interface NodeData {
  label: string;
  type: "person" | "organization" | "concept" | "document" | "technology" | "event";
  description?: string;
  metadata?: Record<string, string>;
}

export interface EdgeData {
  label?: string;
  description?: string;
  type?: string;
  strength?: number;
}

export interface KnowledgeGraphTemplate {
  id: string;
  name: string;
  description: string;
  domain: "finance" | "insurance" | "technology" | "general" | "legal";
  nodes: FlowNode<NodeData>[];
  edges: FlowEdge<EdgeData>[];
}

// Technology Domain Graph (Original)
const technologyGraphNodes: FlowNode<NodeData>[] = [
  // Core AI Concepts - Center top area
  { id: "1", type: "default", position: { x: 700, y: 100 }, data: { label: "AI Technology", type: "concept", description: "Artificial Intelligence and machine learning technologies" } },
  { id: "2", type: "default", position: { x: 450, y: 250 }, data: { label: "Machine Learning", type: "concept", description: "Subset of AI focused on learning from data" } },
  { id: "3", type: "default", position: { x: 950, y: 250 }, data: { label: "Neural Networks", type: "concept", description: "Computing systems inspired by biological neural networks" } },
  { id: "7", type: "default", position: { x: 700, y: 400 }, data: { label: "Deep Learning", type: "technology", description: "Advanced machine learning using neural networks" } },
  { id: "8", type: "default", position: { x: 300, y: 550 }, data: { label: "Computer Vision", type: "technology", description: "AI field dealing with visual data processing" } },
  { id: "9", type: "default", position: { x: 1100, y: 550 }, data: { label: "NLP", type: "technology", description: "Natural Language Processing technologies" } },
  
  // Documents - PDFs - Bottom left quadrant
  { id: "4", type: "default", position: { x: 200, y: 850 }, data: { label: "Research Paper AI.pdf", type: "document", description: "Academic paper on AI advancements - extracted from PDF" } },
  { id: "13", type: "default", position: { x: 450, y: 950 }, data: { label: "ML Handbook.pdf", type: "document", description: "Comprehensive ML guide - PDF document" } },
  { id: "14", type: "default", position: { x: 950, y: 950 }, data: { label: "Neural Net Thesis.pdf", type: "document", description: "PhD thesis on neural networks - PDF" } },
  { id: "15", type: "default", position: { x: 150, y: 1100 }, data: { label: "Vision Systems.pdf", type: "document", description: "Computer vision research - PDF document" } },
  { id: "16", type: "default", position: { x: 1200, y: 850 }, data: { label: "NLP Survey.pdf", type: "document", description: "Survey paper on NLP techniques - PDF" } },
  
  // Documents - Word & PowerPoint - Bottom right quadrant
  { id: "17", type: "default", position: { x: 500, y: 1100 }, data: { label: "Project Plan.docx", type: "document", description: "AI project planning document - Word file" } },
  { id: "18", type: "default", position: { x: 700, y: 1200 }, data: { label: "Technical Spec.docx", type: "document", description: "Technical specifications - Word document" } },
  { id: "19", type: "default", position: { x: 900, y: 1100 }, data: { label: "AI Overview.pptx", type: "document", description: "Executive presentation on AI - PowerPoint" } },
  { id: "20", type: "default", position: { x: 1100, y: 1200 }, data: { label: "Training Data.pptx", type: "document", description: "Data preparation slides - PowerPoint" } },
  { id: "21", type: "default", position: { x: 1300, y: 1050 }, data: { label: "Meeting Notes.docx", type: "document", description: "AI team meeting minutes - Word" } },
  
  // Organizations - Left side
  { id: "5", type: "default", position: { x: 100, y: 400 }, data: { label: "Tech Corp", type: "organization", description: "Leading technology company" } },
  { id: "11", type: "default", position: { x: 1300, y: 400 }, data: { label: "Data Science Team", type: "organization", description: "Internal data science department" } },
  { id: "22", type: "default", position: { x: 250, y: 100 }, data: { label: "AI Research Lab", type: "organization", description: "University research laboratory" } },
  { id: "23", type: "default", position: { x: 1150, y: 100 }, data: { label: "OpenAI", type: "organization", description: "AI research and deployment company" } },
  
  // People - Spread around top
  { id: "6", type: "default", position: { x: 450, y: 50 }, data: { label: "Dr. Smith", type: "person", description: "AI researcher and author" } },
  { id: "12", type: "default", position: { x: 950, y: 50 }, data: { label: "Dr. Johnson", type: "person", description: "Machine learning expert" } },
  { id: "24", type: "default", position: { x: 100, y: 700 }, data: { label: "Prof. Chen", type: "person", description: "Computer vision specialist" } },
  { id: "25", type: "default", position: { x: 1300, y: 700 }, data: { label: "Dr. Williams", type: "person", description: "NLP researcher" } },
  { id: "26", type: "default", position: { x: 850, y: 1300 }, data: { label: "Sarah Mitchell", type: "person", description: "Data engineer" } },
  { id: "27", type: "default", position: { x: 950, y: 1350 }, data: { label: "John Davis", type: "person", description: "ML engineer" } },
  
  // Events - Middle area
  { id: "10", type: "default", position: { x: 500, y: 700 }, data: { label: "AI Conference 2024", type: "event", description: "Major AI research conference" } },
  { id: "28", type: "default", position: { x: 300, y: 1250 }, data: { label: "ML Workshop", type: "event", description: "Hands-on machine learning workshop" } },
  { id: "29", type: "default", position: { x: 1150, y: 1250 }, data: { label: "Tech Summit", type: "event", description: "Annual technology summit" } },
  
  // Extracted Concepts from Documents - Middle layer
  { id: "30", type: "default", position: { x: 200, y: 550 }, data: { label: "Graph RAG", type: "concept", description: "Retrieval-Augmented Generation using knowledge graphs" } },
  { id: "31", type: "default", position: { x: 1200, y: 550 }, data: { label: "Vector Embeddings", type: "concept", description: "Dense vector representations of text" } },
  { id: "32", type: "default", position: { x: 550, y: 550 }, data: { label: "Transformer Architecture", type: "technology", description: "Attention-based neural network architecture" } },
  { id: "33", type: "default", position: { x: 850, y: 550 }, data: { label: "BERT Model", type: "technology", description: "Bidirectional encoder representations" } },
  { id: "34", type: "default", position: { x: 350, y: 700 }, data: { label: "Knowledge Extraction", type: "concept", description: "Automated extraction of structured information" } },
  { id: "35", type: "default", position: { x: 1050, y: 700 }, data: { label: "Entity Recognition", type: "technology", description: "NER for identifying entities in text" } },
  { id: "36", type: "default", position: { x: 550, y: 400 }, data: { label: "Semantic Search", type: "technology", description: "Meaning-based information retrieval" } },
  { id: "37", type: "default", position: { x: 850, y: 400 }, data: { label: "Document Chunking", type: "concept", description: "Splitting documents into processable segments" } },
];

const technologyGraphEdges: FlowEdge<EdgeData>[] = [
  // Core AI hierarchy
  { id: "e1-2", source: "1", target: "2", label: "includes", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "includes", type: "includes", strength: 8 } },
  { id: "e1-3", source: "1", target: "3", label: "utilizes", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "utilizes", type: "utilizes", strength: 7 } },
  { id: "e2-7", source: "2", target: "7", label: "includes", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "includes", type: "includes", strength: 9 } },
  { id: "e7-8", source: "7", target: "8", label: "enables", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "enables", type: "relates-to", strength: 7 } },
  { id: "e7-9", source: "7", target: "9", label: "enables", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "enables", type: "relates-to", strength: 7 } },
  { id: "e3-7", source: "3", target: "7", label: "foundation of", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "foundation of", type: "relates-to", strength: 9 } },
  
  // Document to concept relationships (PDF extractions)
  { id: "e4-1", source: "4", target: "1", label: "discusses", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "discusses", type: "documented-in", strength: 8 } },
  { id: "e4-30", source: "4", target: "30", label: "mentions", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "mentions", type: "documented-in", strength: 7 } },
  { id: "e13-2", source: "13", target: "2", label: "covers", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "covers", type: "documented-in", strength: 9 } },
  { id: "e13-34", source: "13", target: "34", label: "explains", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "explains", type: "documented-in", strength: 6 } },
  { id: "e14-3", source: "14", target: "3", label: "analyzes", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "analyzes", type: "documented-in", strength: 9 } },
  { id: "e14-32", source: "14", target: "32", label: "describes", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "describes", type: "documented-in", strength: 8 } },
  { id: "e15-8", source: "15", target: "8", label: "focuses on", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "focuses on", type: "documented-in", strength: 8 } },
  { id: "e15-35", source: "15", target: "35", label: "demonstrates", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "demonstrates", type: "documented-in", strength: 7 } },
  { id: "e16-9", source: "16", target: "9", label: "surveys", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "surveys", type: "documented-in", strength: 9 } },
  { id: "e16-31", source: "16", target: "31", label: "discusses", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "discusses", type: "documented-in", strength: 7 } },
  
  // Word & PowerPoint document relationships
  { id: "e17-1", source: "17", target: "1", label: "plans", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "plans", type: "documented-in", strength: 7 } },
  { id: "e17-5", source: "17", target: "5", label: "authored by", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "authored by", type: "developed-by", strength: 8 } },
  { id: "e18-7", source: "18", target: "7", label: "specifies", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "specifies", type: "documented-in", strength: 8 } },
  { id: "e18-26", source: "18", target: "26", label: "written by", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "written by", type: "developed-by", strength: 9 } },
  { id: "e19-1", source: "19", target: "1", label: "presents", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "presents", type: "documented-in", strength: 7 } },
  { id: "e19-36", source: "19", target: "36", label: "introduces", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "introduces", type: "documented-in", strength: 6 } },
  { id: "e20-37", source: "20", target: "37", label: "explains", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "explains", type: "documented-in", strength: 7 } },
  { id: "e20-27", source: "20", target: "27", label: "created by", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "created by", type: "developed-by", strength: 8 } },
  { id: "e21-11", source: "21", target: "11", label: "records", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "records", type: "documented-in", strength: 7 } },
  { id: "e21-30", source: "21", target: "30", label: "mentions", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "mentions", type: "documented-in", strength: 6 } },
  
  // Organization relationships
  { id: "e5-1", source: "5", target: "1", label: "develops", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "develops", type: "developed-by", strength: 9 } },
  { id: "e5-11", source: "5", target: "11", label: "owns", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "owns", type: "relates-to", strength: 10 } },
  { id: "e11-2", source: "11", target: "2", label: "works on", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "works on", type: "relates-to", strength: 8 } },
  { id: "e22-4", source: "22", target: "4", label: "publishes", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "publishes", type: "developed-by", strength: 8 } },
  { id: "e22-14", source: "22", target: "14", label: "produces", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "produces", type: "developed-by", strength: 9 } },
  { id: "e23-33", source: "23", target: "33", label: "develops", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "develops", type: "developed-by", strength: 9 } },
  
  // People relationships
  { id: "e6-1", source: "6", target: "1", label: "researches", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "researches", type: "researched-by", strength: 8 } },
  { id: "e6-4", source: "6", target: "4", label: "authored", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "authored", type: "developed-by", strength: 9 } },
  { id: "e6-22", source: "6", target: "22", label: "works at", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "works at", type: "relates-to", strength: 8 } },
  { id: "e12-3", source: "12", target: "3", label: "specializes in", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "specializes in", type: "relates-to", strength: 9 } },
  { id: "e12-13", source: "12", target: "13", label: "wrote", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "wrote", type: "developed-by", strength: 9 } },
  { id: "e24-8", source: "24", target: "8", label: "expert in", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "expert in", type: "relates-to", strength: 9 } },
  { id: "e24-15", source: "24", target: "15", label: "authored", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "authored", type: "developed-by", strength: 8 } },
  { id: "e25-9", source: "25", target: "9", label: "researches", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "researches", type: "researched-by", strength: 9 } },
  { id: "e25-16", source: "25", target: "16", label: "authored", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "authored", type: "developed-by", strength: 8 } },
  { id: "e26-11", source: "26", target: "11", label: "member of", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "member of", type: "relates-to", strength: 8 } },
  { id: "e27-11", source: "27", target: "11", label: "member of", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "member of", type: "relates-to", strength: 8 } },
  
  // Event relationships
  { id: "e10-4", source: "10", target: "4", label: "features", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "features", type: "relates-to", strength: 7 } },
  { id: "e10-6", source: "10", target: "6", label: "presented by", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "presented by", type: "relates-to", strength: 6 } },
  { id: "e28-2", source: "28", target: "2", label: "teaches", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "teaches", type: "relates-to", strength: 7 } },
  { id: "e28-27", source: "28", target: "27", label: "led by", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "led by", type: "relates-to", strength: 8 } },
  { id: "e29-5", source: "29", target: "5", label: "hosted by", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "hosted by", type: "relates-to", strength: 8 } },
  
  // Graph RAG specific relationships
  { id: "e30-31", source: "30", target: "31", label: "uses", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "uses", type: "utilizes", strength: 9 } },
  { id: "e30-34", source: "30", target: "34", label: "requires", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "requires", type: "utilizes", strength: 8 } },
  { id: "e30-36", source: "30", target: "36", label: "enables", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "enables", type: "relates-to", strength: 8 } },
  { id: "e31-9", source: "31", target: "9", label: "derived from", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "derived from", type: "relates-to", strength: 7 } },
  { id: "e32-33", source: "32", target: "33", label: "basis for", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "basis for", type: "relates-to", strength: 9 } },
  { id: "e33-9", source: "33", target: "9", label: "implements", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "implements", type: "utilizes", strength: 9 } },
  { id: "e34-35", source: "34", target: "35", label: "uses", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "uses", type: "utilizes", strength: 8 } },
  { id: "e35-9", source: "35", target: "9", label: "component of", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "component of", type: "relates-to", strength: 8 } },
  { id: "e36-31", source: "36", target: "31", label: "leverages", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "leverages", type: "utilizes", strength: 9 } },
  { id: "e37-34", source: "37", target: "34", label: "precedes", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "precedes", type: "relates-to", strength: 7 } },
];

// Finance Domain Graph - Investment Banking & Trading
const financeGraphNodes: FlowNode<NodeData>[] = [
  // Core Financial Entities
  { id: "f1", type: "default", position: { x: 700, y: 100 }, data: { label: "Goldman Sachs", type: "organization", description: "Global investment banking firm" } },
  { id: "f2", type: "default", position: { x: 400, y: 100 }, data: { label: "JPMorgan Chase", type: "organization", description: "Multinational investment bank" } },
  { id: "f3", type: "default", position: { x: 1000, y: 100 }, data: { label: "BlackRock Inc", type: "organization", description: "World's largest asset manager" } },
  
  // Investment Products & Concepts
  { id: "f4", type: "default", position: { x: 700, y: 250 }, data: { label: "Equity Trading", type: "concept", description: "Buying and selling of company stocks" } },
  { id: "f5", type: "default", position: { x: 400, y: 250 }, data: { label: "Fixed Income", type: "concept", description: "Bond and debt securities trading" } },
  { id: "f6", type: "default", position: { x: 1000, y: 250 }, data: { label: "Derivatives", type: "concept", description: "Financial contracts derived from underlying assets" } },
  { id: "f7", type: "default", position: { x: 550, y: 400 }, data: { label: "Risk Management", type: "concept", description: "Assessment and mitigation of financial risks" } },
  { id: "f8", type: "default", position: { x: 850, y: 400 }, data: { label: "Portfolio Optimization", type: "concept", description: "Maximizing returns while managing risk" } },
  
  // Key Personnel
  { id: "f9", type: "default", position: { x: 250, y: 400 }, data: { label: "Sarah Chen", type: "person", description: "Chief Investment Officer" } },
  { id: "f10", type: "default", position: { x: 1150, y: 400 }, data: { label: "Michael Roberts", type: "person", description: "Head of Trading Desk" } },
  { id: "f11", type: "default", position: { x: 250, y: 550 }, data: { label: "David Kumar", type: "person", description: "Risk Management Director" } },
  { id: "f12", type: "default", position: { x: 1150, y: 550 }, data: { label: "Emily Zhang", type: "person", description: "Quantitative Analyst" } },
  
  // Documents
  { id: "f13", type: "default", position: { x: 300, y: 700 }, data: { label: "Q3 2024 Report.pdf", type: "document", description: "Quarterly financial performance report" } },
  { id: "f14", type: "default", position: { x: 550, y: 700 }, data: { label: "Market Analysis.docx", type: "document", description: "Comprehensive market trend analysis" } },
  { id: "f15", type: "default", position: { x: 800, y: 700 }, data: { label: "Risk Assessment.xlsx", type: "document", description: "Portfolio risk metrics and analysis" } },
  { id: "f16", type: "default", position: { x: 1050, y: 700 }, data: { label: "Trading Strategy.pptx", type: "document", description: "Algorithmic trading strategy presentation" } },
  { id: "f17", type: "default", position: { x: 400, y: 850 }, data: { label: "Compliance Guide.pdf", type: "document", description: "Regulatory compliance documentation" } },
  { id: "f18", type: "default", position: { x: 900, y: 850 }, data: { label: "Investment Thesis.docx", type: "document", description: "Technology sector investment analysis" } },
  
  // Technologies & Systems
  { id: "f19", type: "default", position: { x: 200, y: 250 }, data: { label: "Bloomberg Terminal", type: "technology", description: "Financial data and trading platform" } },
  { id: "f20", type: "default", position: { x: 1200, y: 250 }, data: { label: "Algorithmic Trading", type: "technology", description: "Automated trading systems" } },
  { id: "f21", type: "default", position: { x: 700, y: 550 }, data: { label: "Financial Modeling", type: "technology", description: "Quantitative analysis tools" } },
  
  // Events
  { id: "f22", type: "default", position: { x: 450, y: 1000 }, data: { label: "Fed Meeting", type: "event", description: "Federal Reserve policy meeting 2024" } },
  { id: "f23", type: "default", position: { x: 750, y: 1000 }, data: { label: "Earnings Call", type: "event", description: "Q3 investor earnings announcement" } },
  
  // Regulatory & Compliance
  { id: "f24", type: "default", position: { x: 100, y: 550 }, data: { label: "SEC Regulations", type: "concept", description: "Securities and Exchange Commission rules" } },
  { id: "f25", type: "default", position: { x: 1300, y: 550 }, data: { label: "Basel III", type: "concept", description: "International banking regulations" } },
];

const financeGraphEdges: FlowEdge<EdgeData>[] = [
  // Organization relationships
  { id: "ef1-4", source: "f1", target: "f4", label: "specializes in", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "specializes in", type: "relates-to", strength: 9 } },
  { id: "ef2-5", source: "f2", target: "f5", label: "trades", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "trades", type: "relates-to", strength: 8 } },
  { id: "ef3-8", source: "f3", target: "f8", label: "focuses on", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "focuses on", type: "relates-to", strength: 9 } },
  
  // Product relationships
  { id: "ef4-6", source: "f4", target: "f6", label: "relates to", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "relates to", type: "relates-to", strength: 7 } },
  { id: "ef5-6", source: "f5", target: "f6", label: "underlies", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "underlies", type: "relates-to", strength: 7 } },
  { id: "ef4-7", source: "f4", target: "f7", label: "requires", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "requires", type: "utilizes", strength: 8 } },
  { id: "ef6-7", source: "f6", target: "f7", label: "managed by", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "managed by", type: "utilizes", strength: 9 } },
  { id: "ef8-7", source: "f8", target: "f7", label: "incorporates", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "incorporates", type: "utilizes", strength: 8 } },
  
  // People relationships
  { id: "ef9-2", source: "f9", target: "f2", label: "works at", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "works at", type: "relates-to", strength: 9 } },
  { id: "ef9-8", source: "f9", target: "f8", label: "oversees", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "oversees", type: "relates-to", strength: 9 } },
  { id: "ef10-1", source: "f10", target: "f1", label: "employed by", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "employed by", type: "relates-to", strength: 9 } },
  { id: "ef10-4", source: "f10", target: "f4", label: "manages", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "manages", type: "relates-to", strength: 9 } },
  { id: "ef11-7", source: "f11", target: "f7", label: "leads", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "leads", type: "relates-to", strength: 9 } },
  { id: "ef12-21", source: "f12", target: "f21", label: "develops", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "develops", type: "developed-by", strength: 9 } },
  { id: "ef12-3", source: "f12", target: "f3", label: "works at", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "works at", type: "relates-to", strength: 8 } },
  
  // Document relationships
  { id: "ef13-1", source: "f13", target: "f1", label: "published by", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "published by", type: "developed-by", strength: 8 } },
  { id: "ef13-4", source: "f13", target: "f4", label: "analyzes", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "analyzes", type: "documented-in", strength: 8 } },
  { id: "ef14-6", source: "f14", target: "f6", label: "discusses", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "discusses", type: "documented-in", strength: 7 } },
  { id: "ef14-9", source: "f14", target: "f9", label: "authored by", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "authored by", type: "developed-by", strength: 8 } },
  { id: "ef15-7", source: "f15", target: "f7", label: "covers", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "covers", type: "documented-in", strength: 9 } },
  { id: "ef15-11", source: "f15", target: "f11", label: "created by", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "created by", type: "developed-by", strength: 9 } },
  { id: "ef16-20", source: "f16", target: "f20", label: "presents", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "presents", type: "documented-in", strength: 8 } },
  { id: "ef16-10", source: "f16", target: "f10", label: "prepared by", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "prepared by", type: "developed-by", strength: 8 } },
  { id: "ef17-24", source: "f17", target: "f24", label: "explains", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "explains", type: "documented-in", strength: 9 } },
  { id: "ef18-8", source: "f18", target: "f8", label: "supports", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "supports", type: "documented-in", strength: 7 } },
  
  // Technology relationships
  { id: "ef19-4", source: "f19", target: "f4", label: "enables", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "enables", type: "utilizes", strength: 9 } },
  { id: "ef19-5", source: "f19", target: "f5", label: "supports", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "supports", type: "utilizes", strength: 9 } },
  { id: "ef20-4", source: "f20", target: "f4", label: "automates", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "automates", type: "utilizes", strength: 8 } },
  { id: "ef21-8", source: "f21", target: "f8", label: "powers", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "powers", type: "utilizes", strength: 9 } },
  
  // Event relationships
  { id: "ef22-5", source: "f22", target: "f5", label: "impacts", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "impacts", type: "relates-to", strength: 9 } },
  { id: "ef23-13", source: "f23", target: "f13", label: "resulted in", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "resulted in", type: "relates-to", strength: 8 } },
  
  // Regulatory relationships
  { id: "ef24-1", source: "f24", target: "f1", label: "governs", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "governs", type: "relates-to", strength: 8 } },
  { id: "ef24-2", source: "f24", target: "f2", label: "regulates", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "regulates", type: "relates-to", strength: 8 } },
  { id: "ef25-3", source: "f25", target: "f3", label: "applies to", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "applies to", type: "relates-to", strength: 9 } },
  { id: "ef25-7", source: "f25", target: "f7", label: "mandates", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "mandates", type: "relates-to", strength: 8 } },
];

// Insurance Domain Graph - Claims & Underwriting
const insuranceGraphNodes: FlowNode<NodeData>[] = [
  // Insurance Companies
  { id: "i1", type: "default", position: { x: 700, y: 100 }, data: { label: "State Farm", type: "organization", description: "Leading property and casualty insurer" } },
  { id: "i2", type: "default", position: { x: 400, y: 100 }, data: { label: "Allstate Insurance", type: "organization", description: "Auto and home insurance provider" } },
  { id: "i3", type: "default", position: { x: 1000, y: 100 }, data: { label: "Prudential Financial", type: "organization", description: "Life insurance and annuities" } },
  
  // Insurance Concepts
  { id: "i4", type: "default", position: { x: 550, y: 250 }, data: { label: "Underwriting", type: "concept", description: "Risk assessment and policy pricing" } },
  { id: "i5", type: "default", position: { x: 850, y: 250 }, data: { label: "Claims Processing", type: "concept", description: "Managing and settling insurance claims" } },
  { id: "i6", type: "default", position: { x: 300, y: 400 }, data: { label: "Actuarial Analysis", type: "concept", description: "Statistical analysis of insurance risks" } },
  { id: "i7", type: "default", position: { x: 700, y: 400 }, data: { label: "Fraud Detection", type: "concept", description: "Identifying fraudulent insurance claims" } },
  { id: "i8", type: "default", position: { x: 1100, y: 400 }, data: { label: "Policy Administration", type: "concept", description: "Managing policy lifecycle" } },
  
  // Insurance Products
  { id: "i9", type: "default", position: { x: 200, y: 250 }, data: { label: "Auto Insurance", type: "concept", description: "Vehicle coverage policies" } },
  { id: "i10", type: "default", position: { x: 1200, y: 250 }, data: { label: "Life Insurance", type: "concept", description: "Death benefit coverage" } },
  { id: "i11", type: "default", position: { x: 450, y: 550 }, data: { label: "Health Insurance", type: "concept", description: "Medical coverage policies" } },
  { id: "i12", type: "default", position: { x: 950, y: 550 }, data: { label: "Property Insurance", type: "concept", description: "Home and property coverage" } },
  
  // Key Personnel
  { id: "i13", type: "default", position: { x: 150, y: 550 }, data: { label: "Jennifer Martinez", type: "person", description: "Chief Underwriter" } },
  { id: "i14", type: "default", position: { x: 1250, y: 550 }, data: { label: "Robert Thompson", type: "person", description: "Claims Director" } },
  { id: "i15", type: "default", position: { x: 250, y: 700 }, data: { label: "Dr. Lisa Wong", type: "person", description: "Chief Actuary" } },
  { id: "i16", type: "default", position: { x: 1150, y: 700 }, data: { label: "James Patterson", type: "person", description: "Fraud Investigation Lead" } },
  
  // Documents
  { id: "i17", type: "default", position: { x: 350, y: 850 }, data: { label: "Policy Terms.pdf", type: "document", description: "Standard policy terms and conditions" } },
  { id: "i18", type: "default", position: { x: 600, y: 850 }, data: { label: "Claims Report Q4.xlsx", type: "document", description: "Quarterly claims statistics" } },
  { id: "i19", type: "default", position: { x: 850, y: 850 }, data: { label: "Risk Model.docx", type: "document", description: "Actuarial risk modeling documentation" } },
  { id: "i20", type: "default", position: { x: 1100, y: 850 }, data: { label: "Fraud Cases.pdf", type: "document", description: "Investigation case studies" } },
  { id: "i21", type: "default", position: { x: 450, y: 1000 }, data: { label: "Underwriting Guide.docx", type: "document", description: "Best practices for underwriters" } },
  { id: "i22", type: "default", position: { x: 750, y: 1000 }, data: { label: "Customer Data.xlsx", type: "document", description: "Policyholder information database" } },
  
  // Technologies
  { id: "i23", type: "default", position: { x: 100, y: 400 }, data: { label: "Predictive Analytics", type: "technology", description: "AI-powered risk prediction" } },
  { id: "i24", type: "default", position: { x: 1300, y: 400 }, data: { label: "Claims Management System", type: "technology", description: "Digital claims processing platform" } },
  { id: "i25", type: "default", position: { x: 550, y: 700 }, data: { label: "OCR Technology", type: "technology", description: "Document processing automation" } },
  { id: "i26", type: "default", position: { x: 850, y: 700 }, data: { label: "Machine Learning", type: "technology", description: "Pattern recognition for fraud detection" } },
  
  // Events & Regulations
  { id: "i27", type: "default", position: { x: 350, y: 1150 }, data: { label: "Hurricane Season", type: "event", description: "Major weather event increasing claims" } },
  { id: "i28", type: "default", position: { x: 850, y: 1150 }, data: { label: "Industry Conference", type: "event", description: "Annual insurance innovation summit" } },
  { id: "i29", type: "default", position: { x: 100, y: 100 }, data: { label: "State Regulations", type: "concept", description: "Insurance regulatory compliance" } },
  { id: "i30", type: "default", position: { x: 1300, y: 100 }, data: { label: "HIPAA Compliance", type: "concept", description: "Health insurance privacy rules" } },
];

const insuranceGraphEdges: FlowEdge<EdgeData>[] = [
  // Organization to concept relationships
  { id: "ei1-4", source: "i1", target: "i4", label: "performs", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "performs", type: "relates-to", strength: 9 } },
  { id: "ei1-12", source: "i1", target: "i12", label: "offers", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "offers", type: "relates-to", strength: 8 } },
  { id: "ei2-9", source: "i2", target: "i9", label: "specializes in", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "specializes in", type: "relates-to", strength: 9 } },
  { id: "ei2-5", source: "i2", target: "i5", label: "manages", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "manages", type: "relates-to", strength: 8 } },
  { id: "ei3-10", source: "i3", target: "i10", label: "provides", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "provides", type: "relates-to", strength: 9 } },
  { id: "ei3-6", source: "i3", target: "i6", label: "utilizes", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "utilizes", type: "utilizes", strength: 9 } },
  
  // Concept relationships
  { id: "ei4-6", source: "i4", target: "i6", label: "relies on", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "relies on", type: "utilizes", strength: 9 } },
  { id: "ei5-7", source: "i5", target: "i7", label: "includes", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "includes", type: "includes", strength: 8 } },
  { id: "ei4-8", source: "i4", target: "i8", label: "precedes", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "precedes", type: "relates-to", strength: 7 } },
  { id: "ei5-8", source: "i5", target: "i8", label: "part of", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "part of", type: "relates-to", strength: 8 } },
  
  // Product relationships
  { id: "ei9-4", source: "i9", target: "i4", label: "requires", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "requires", type: "utilizes", strength: 8 } },
  { id: "ei10-6", source: "i10", target: "i6", label: "priced by", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "priced by", type: "utilizes", strength: 9 } },
  { id: "ei11-30", source: "i11", target: "i30", label: "governed by", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "governed by", type: "relates-to", strength: 9 } },
  { id: "ei12-5", source: "i12", target: "i5", label: "generates", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "generates", type: "relates-to", strength: 7 } },
  
  // People relationships
  { id: "ei13-1", source: "i13", target: "i1", label: "works at", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "works at", type: "relates-to", strength: 9 } },
  { id: "ei13-4", source: "i13", target: "i4", label: "leads", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "leads", type: "relates-to", strength: 9 } },
  { id: "ei14-2", source: "i14", target: "i2", label: "employed by", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "employed by", type: "relates-to", strength: 9 } },
  { id: "ei14-5", source: "i14", target: "i5", label: "oversees", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "oversees", type: "relates-to", strength: 9 } },
  { id: "ei15-6", source: "i15", target: "i6", label: "specializes in", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "specializes in", type: "relates-to", strength: 10 } },
  { id: "ei15-3", source: "i15", target: "i3", label: "works for", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "works for", type: "relates-to", strength: 9 } },
  { id: "ei16-7", source: "i16", target: "i7", label: "manages", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "manages", type: "relates-to", strength: 9 } },
  { id: "ei16-1", source: "i16", target: "i1", label: "employed by", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "employed by", type: "relates-to", strength: 8 } },
  
  // Document relationships
  { id: "ei17-8", source: "i17", target: "i8", label: "defines", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "defines", type: "documented-in", strength: 9 } },
  { id: "ei17-12", source: "i17", target: "i12", label: "covers", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "covers", type: "documented-in", strength: 8 } },
  { id: "ei18-5", source: "i18", target: "i5", label: "analyzes", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "analyzes", type: "documented-in", strength: 9 } },
  { id: "ei18-14", source: "i18", target: "i14", label: "prepared by", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "prepared by", type: "developed-by", strength: 8 } },
  { id: "ei19-6", source: "i19", target: "i6", label: "documents", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "documents", type: "documented-in", strength: 9 } },
  { id: "ei19-15", source: "i19", target: "i15", label: "authored by", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "authored by", type: "developed-by", strength: 9 } },
  { id: "ei20-7", source: "i20", target: "i7", label: "describes", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "describes", type: "documented-in", strength: 8 } },
  { id: "ei20-16", source: "i20", target: "i16", label: "created by", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "created by", type: "developed-by", strength: 9 } },
  { id: "ei21-4", source: "i21", target: "i4", label: "guides", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "guides", type: "documented-in", strength: 8 } },
  { id: "ei21-13", source: "i21", target: "i13", label: "written by", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "written by", type: "developed-by", strength: 7 } },
  { id: "ei22-8", source: "i22", target: "i8", label: "supports", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "supports", type: "documented-in", strength: 8 } },
  
  // Technology relationships
  { id: "ei23-6", source: "i23", target: "i6", label: "enhances", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "enhances", type: "utilizes", strength: 9 } },
  { id: "ei23-4", source: "i23", target: "i4", label: "improves", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "improves", type: "utilizes", strength: 8 } },
  { id: "ei24-5", source: "i24", target: "i5", label: "automates", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "automates", type: "utilizes", strength: 9 } },
  { id: "ei25-17", source: "i25", target: "i17", label: "processes", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "processes", type: "utilizes", strength: 7 } },
  { id: "ei25-5", source: "i25", target: "i5", label: "assists", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "assists", type: "utilizes", strength: 8 } },
  { id: "ei26-7", source: "i26", target: "i7", label: "powers", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "powers", type: "utilizes", strength: 9 } },
  
  // Event relationships
  { id: "ei27-12", source: "i27", target: "i12", label: "affects", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "affects", type: "relates-to", strength: 9 } },
  { id: "ei27-5", source: "i27", target: "i5", label: "increases", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "increases", type: "relates-to", strength: 8 } },
  { id: "ei28-16", source: "i28", target: "i16", label: "attended by", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "attended by", type: "relates-to", strength: 6 } },
  
  // Regulatory relationships
  { id: "ei29-1", source: "i29", target: "i1", label: "regulates", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "regulates", type: "relates-to", strength: 9 } },
  { id: "ei29-2", source: "i29", target: "i2", label: "governs", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "governs", type: "relates-to", strength: 9 } },
  { id: "ei30-11", source: "i30", target: "i11", label: "applies to", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "applies to", type: "relates-to", strength: 10 } },
];

// Contract Analysis Domain Graph - Legal & Procurement
const contractGraphNodes: FlowNode<NodeData>[] = [
  // Core Contracting Parties
  { id: "c1", type: "default", position: { x: 300, y: 100 }, data: { label: "Acme Corporation", type: "organization", description: "Buyer - Technology company" } },
  { id: "c2", type: "default", position: { x: 700, y: 100 }, data: { label: "Global Tech Services", type: "organization", description: "Vendor - IT services provider" } },
  { id: "c3", type: "default", position: { x: 1100, y: 100 }, data: { label: "Legal Department", type: "organization", description: "Internal legal counsel" } },
  
  // Contract Types & Documents
  { id: "c4", type: "default", position: { x: 200, y: 250 }, data: { label: "Master Service Agreement.pdf", type: "document", description: "Primary MSA governing relationship" } },
  { id: "c5", type: "default", position: { x: 500, y: 250 }, data: { label: "Statement of Work.docx", type: "document", description: "SOW detailing specific deliverables" } },
  { id: "c6", type: "default", position: { x: 800, y: 250 }, data: { label: "NDA Agreement.pdf", type: "document", description: "Non-disclosure agreement" } },
  { id: "c7", type: "default", position: { x: 1100, y: 250 }, data: { label: "Amendment No. 3.pdf", type: "document", description: "Contract modification document" } },
  { id: "c8", type: "default", position: { x: 350, y: 400 }, data: { label: "Purchase Order.xlsx", type: "document", description: "PO for cloud services" } },
  { id: "c9", type: "default", position: { x: 950, y: 400 }, data: { label: "SLA Document.docx", type: "document", description: "Service level agreement terms" } },
  
  // Key Contract Data Points & Concepts
  { id: "c10", type: "default", position: { x: 200, y: 550 }, data: { label: "Contract Value", type: "concept", description: "$2.5M total contract value" } },
  { id: "c11", type: "default", position: { x: 400, y: 550 }, data: { label: "Effective Date", type: "concept", description: "January 1, 2024" } },
  { id: "c12", type: "default", position: { x: 600, y: 550 }, data: { label: "Termination Date", type: "concept", description: "December 31, 2026" } },
  { id: "c13", type: "default", position: { x: 800, y: 550 }, data: { label: "Payment Terms", type: "concept", description: "Net 30 days from invoice" } },
  { id: "c14", type: "default", position: { x: 1000, y: 550 }, data: { label: "Renewal Clause", type: "concept", description: "Auto-renewal with 90-day notice" } },
  { id: "c15", type: "default", position: { x: 1200, y: 550 }, data: { label: "Termination Clause", type: "concept", description: "30-day termination for convenience" } },
  
  // Obligations & Deliverables
  { id: "c16", type: "default", position: { x: 150, y: 700 }, data: { label: "Cloud Infrastructure", type: "concept", description: "24/7 cloud hosting services" } },
  { id: "c17", type: "default", position: { x: 400, y: 700 }, data: { label: "Technical Support", type: "concept", description: "Tier 1-3 support coverage" } },
  { id: "c18", type: "default", position: { x: 650, y: 700 }, data: { label: "Data Security", type: "concept", description: "SOC 2 Type II compliance required" } },
  { id: "c19", type: "default", position: { x: 900, y: 700 }, data: { label: "SLA Metrics", type: "concept", description: "99.9% uptime guarantee" } },
  { id: "c20", type: "default", position: { x: 1150, y: 700 }, data: { label: "Disaster Recovery", type: "concept", description: "4-hour RTO requirement" } },
  
  // Risk & Compliance
  { id: "c21", type: "default", position: { x: 250, y: 850 }, data: { label: "Liability Cap", type: "concept", description: "Limited to 12 months fees" } },
  { id: "c22", type: "default", position: { x: 500, y: 850 }, data: { label: "Indemnification", type: "concept", description: "Mutual indemnification clause" } },
  { id: "c23", type: "default", position: { x: 750, y: 850 }, data: { label: "Confidentiality", type: "concept", description: "5-year confidentiality obligation" } },
  { id: "c24", type: "default", position: { x: 1000, y: 850 }, data: { label: "IP Rights", type: "concept", description: "Work product ownership terms" } },
  { id: "c25", type: "default", position: { x: 1250, y: 850 }, data: { label: "Audit Rights", type: "concept", description: "Annual compliance audit provision" } },
  
  // Key Personnel
  { id: "c26", type: "default", position: { x: 100, y: 1000 }, data: { label: "Sarah Johnson", type: "person", description: "Chief Procurement Officer" } },
  { id: "c27", type: "default", position: { x: 350, y: 1000 }, data: { label: "Michael Chen", type: "person", description: "Contract Manager" } },
  { id: "c28", type: "default", position: { x: 600, y: 1000 }, data: { label: "Emily Davis", type: "person", description: "General Counsel" } },
  { id: "c29", type: "default", position: { x: 850, y: 1000 }, data: { label: "David Martinez", type: "person", description: "Vendor Account Manager" } },
  { id: "c30", type: "default", position: { x: 1100, y: 1000 }, data: { label: "Rachel Kim", type: "person", description: "Compliance Officer" } },
  
  // Technologies & Tools
  { id: "c31", type: "default", position: { x: 100, y: 400 }, data: { label: "CLM System", type: "technology", description: "Contract lifecycle management platform" } },
  { id: "c32", type: "default", position: { x: 1200, y: 400 }, data: { label: "AI Contract Analysis", type: "technology", description: "Automated clause extraction" } },
  { id: "c33", type: "default", position: { x: 350, y: 1150 }, data: { label: "E-Signature Platform", type: "technology", description: "DocuSign for execution" } },
  { id: "c34", type: "default", position: { x: 850, y: 1150 }, data: { label: "Contract Analytics", type: "technology", description: "Dashboard for contract insights" } },
  
  // Events & Milestones
  { id: "c35", type: "default", position: { x: 200, y: 1300 }, data: { label: "Contract Execution", type: "event", description: "Agreement signed Dec 15, 2023" } },
  { id: "c36", type: "default", position: { x: 500, y: 1300 }, data: { label: "Go-Live Date", type: "event", description: "Services commenced Jan 1, 2024" } },
  { id: "c37", type: "default", position: { x: 800, y: 1300 }, data: { label: "Annual Review", type: "event", description: "Performance review meeting" } },
  { id: "c38", type: "default", position: { x: 1100, y: 1300 }, data: { label: "Renewal Notice", type: "event", description: "90-day notice deadline" } },
  
  // Extracted Obligations & Risks
  { id: "c39", type: "default", position: { x: 100, y: 1450 }, data: { label: "Price Increase Cap", type: "concept", description: "5% annual increase maximum" } },
  { id: "c40", type: "default", position: { x: 400, y: 1450 }, data: { label: "Change Order Process", type: "concept", description: "Written approval required for scope changes" } },
  { id: "c41", type: "default", position: { x: 700, y: 1450 }, data: { label: "Dispute Resolution", type: "concept", description: "Arbitration in New York" } },
  { id: "c42", type: "default", position: { x: 1000, y: 1450 }, data: { label: "Force Majeure", type: "concept", description: "Suspension of obligations clause" } },
  { id: "c43", type: "default", position: { x: 1300, y: 1450 }, data: { label: "Insurance Requirements", type: "concept", description: "$5M general liability coverage" } },
];

const contractGraphEdges: FlowEdge<EdgeData>[] = [
  // Party relationships
  { id: "ec1-2", source: "c1", target: "c2", label: "contracts with", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "contracts with", type: "relates-to", strength: 10 } },
  { id: "ec1-3", source: "c1", target: "c3", label: "advised by", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "advised by", type: "relates-to", strength: 8 } },
  { id: "ec3-2", source: "c3", target: "c2", label: "negotiates with", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "negotiates with", type: "relates-to", strength: 7 } },
  
  // Document relationships
  { id: "ec4-1", source: "c4", target: "c1", label: "signed by", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "signed by", type: "developed-by", strength: 9 } },
  { id: "ec4-2", source: "c4", target: "c2", label: "signed by", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "signed by", type: "developed-by", strength: 9 } },
  { id: "ec5-4", source: "c5", target: "c4", label: "references", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "references", type: "relates-to", strength: 9 } },
  { id: "ec6-4", source: "c6", target: "c4", label: "attached to", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "attached to", type: "relates-to", strength: 8 } },
  { id: "ec7-4", source: "c7", target: "c4", label: "modifies", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "modifies", type: "relates-to", strength: 9 } },
  { id: "ec8-5", source: "c8", target: "c5", label: "authorizes", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "authorizes", type: "relates-to", strength: 8 } },
  { id: "ec9-4", source: "c9", target: "c4", label: "defines terms for", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "defines terms for", type: "documented-in", strength: 9 } },
  
  // Contract data points to documents
  { id: "ec10-4", source: "c10", target: "c4", label: "specified in", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "specified in", type: "documented-in", strength: 9 } },
  { id: "ec11-4", source: "c11", target: "c4", label: "defined in", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "defined in", type: "documented-in", strength: 9 } },
  { id: "ec12-4", source: "c12", target: "c4", label: "stated in", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "stated in", type: "documented-in", strength: 9 } },
  { id: "ec13-4", source: "c13", target: "c4", label: "outlined in", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "outlined in", type: "documented-in", strength: 8 } },
  { id: "ec14-4", source: "c14", target: "c4", label: "included in", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "included in", type: "documented-in", strength: 8 } },
  { id: "ec15-4", source: "c15", target: "c4", label: "described in", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "described in", type: "documented-in", strength: 8 } },
  
  // Obligations to documents
  { id: "ec16-5", source: "c16", target: "c5", label: "deliverable in", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "deliverable in", type: "documented-in", strength: 9 } },
  { id: "ec17-5", source: "c17", target: "c5", label: "required by", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "required by", type: "documented-in", strength: 9 } },
  { id: "ec18-6", source: "c18", target: "c6", label: "mandated in", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "mandated in", type: "documented-in", strength: 9 } },
  { id: "ec19-9", source: "c19", target: "c9", label: "defined in", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "defined in", type: "documented-in", strength: 10 } },
  { id: "ec20-9", source: "c20", target: "c9", label: "specified in", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "specified in", type: "documented-in", strength: 9 } },
  
  // Vendor obligations
  { id: "ec2-16", source: "c2", target: "c16", label: "provides", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "provides", type: "relates-to", strength: 9 } },
  { id: "ec2-17", source: "c2", target: "c17", label: "delivers", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "delivers", type: "relates-to", strength: 9 } },
  { id: "ec2-19", source: "c2", target: "c19", label: "commits to", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "commits to", type: "relates-to", strength: 9 } },
  
  // Risk & compliance to documents
  { id: "ec21-4", source: "c21", target: "c4", label: "limited by", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "limited by", type: "documented-in", strength: 8 } },
  { id: "ec22-4", source: "c22", target: "c4", label: "covered in", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "covered in", type: "documented-in", strength: 9 } },
  { id: "ec23-6", source: "c23", target: "c6", label: "governed by", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "governed by", type: "documented-in", strength: 10 } },
  { id: "ec24-4", source: "c24", target: "c4", label: "addressed in", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "addressed in", type: "documented-in", strength: 8 } },
  { id: "ec25-4", source: "c25", target: "c4", label: "stipulated in", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "stipulated in", type: "documented-in", strength: 7 } },
  
  // People relationships
  { id: "ec26-1", source: "c26", target: "c1", label: "represents", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "represents", type: "relates-to", strength: 9 } },
  { id: "ec26-4", source: "c26", target: "c4", label: "negotiated", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "negotiated", type: "developed-by", strength: 8 } },
  { id: "ec27-4", source: "c27", target: "c4", label: "manages", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "manages", type: "relates-to", strength: 9 } },
  { id: "ec27-1", source: "c27", target: "c1", label: "works for", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "works for", type: "relates-to", strength: 9 } },
  { id: "ec28-3", source: "c28", target: "c3", label: "leads", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "leads", type: "relates-to", strength: 10 } },
  { id: "ec28-4", source: "c28", target: "c4", label: "reviewed", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "reviewed", type: "developed-by", strength: 9 } },
  { id: "ec29-2", source: "c29", target: "c2", label: "represents", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "represents", type: "relates-to", strength: 9 } },
  { id: "ec29-27", source: "c29", target: "c27", label: "coordinates with", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "coordinates with", type: "relates-to", strength: 7 } },
  { id: "ec30-25", source: "c30", target: "c25", label: "monitors", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "monitors", type: "relates-to", strength: 8 } },
  { id: "ec30-1", source: "c30", target: "c1", label: "employed by", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "employed by", type: "relates-to", strength: 9 } },
  
  // Technology relationships
  { id: "ec31-4", source: "c31", target: "c4", label: "stores", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "stores", type: "utilizes", strength: 9 } },
  { id: "ec31-5", source: "c31", target: "c5", label: "manages", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "manages", type: "utilizes", strength: 9 } },
  { id: "ec32-10", source: "c32", target: "c10", label: "extracts", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "extracts", type: "utilizes", strength: 8 } },
  { id: "ec32-21", source: "c32", target: "c21", label: "identifies", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "identifies", type: "utilizes", strength: 8 } },
  { id: "ec32-4", source: "c32", target: "c4", label: "analyzes", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "analyzes", type: "utilizes", strength: 9 } },
  { id: "ec33-4", source: "c33", target: "c4", label: "executed", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "executed", type: "utilizes", strength: 8 } },
  { id: "ec34-10", source: "c34", target: "c10", label: "tracks", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "tracks", type: "utilizes", strength: 8 } },
  { id: "ec34-12", source: "c34", target: "c12", label: "monitors", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "monitors", type: "utilizes", strength: 8 } },
  
  // Event relationships
  { id: "ec35-4", source: "c35", target: "c4", label: "finalized", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "finalized", type: "relates-to", strength: 9 } },
  { id: "ec35-11", source: "c35", target: "c11", label: "triggered", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "triggered", type: "relates-to", strength: 8 } },
  { id: "ec36-16", source: "c36", target: "c16", label: "commenced", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "commenced", type: "relates-to", strength: 9 } },
  { id: "ec37-19", source: "c37", target: "c19", label: "reviews", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "reviews", type: "relates-to", strength: 7 } },
  { id: "ec37-27", source: "c37", target: "c27", label: "led by", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "led by", type: "relates-to", strength: 8 } },
  { id: "ec38-14", source: "c38", target: "c14", label: "activates", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "activates", type: "relates-to", strength: 9 } },
  { id: "ec38-12", source: "c38", target: "c12", label: "precedes", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "precedes", type: "relates-to", strength: 7 } },
  
  // Extracted obligations
  { id: "ec39-4", source: "c39", target: "c4", label: "constrained by", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "constrained by", type: "documented-in", strength: 8 } },
  { id: "ec39-13", source: "c39", target: "c13", label: "relates to", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "relates to", type: "relates-to", strength: 7 } },
  { id: "ec40-5", source: "c40", target: "c5", label: "governs", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "governs", type: "documented-in", strength: 9 } },
  { id: "ec40-7", source: "c40", target: "c7", label: "applies to", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "applies to", type: "relates-to", strength: 8 } },
  { id: "ec41-4", source: "c41", target: "c4", label: "specified in", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "specified in", type: "documented-in", strength: 8 } },
  { id: "ec42-4", source: "c42", target: "c4", label: "included in", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "included in", type: "documented-in", strength: 7 } },
  { id: "ec43-4", source: "c43", target: "c4", label: "required by", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "required by", type: "documented-in", strength: 9 } },
  { id: "ec43-2", source: "c43", target: "c2", label: "mandated for", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "mandated for", type: "relates-to", strength: 8 } },
  
  // Cross-concept relationships
  { id: "ec10-13", source: "c10", target: "c13", label: "determines", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "determines", type: "relates-to", strength: 7 } },
  { id: "ec11-12", source: "c11", target: "c12", label: "defines term with", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "defines term with", type: "relates-to", strength: 9 } },
  { id: "ec14-15", source: "c14", target: "c15", label: "conflicts with", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "conflicts with", type: "relates-to", strength: 6 } },
  { id: "ec19-20", source: "c19", target: "c20", label: "supports", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "supports", type: "relates-to", strength: 8 } },
  { id: "ec21-22", source: "c21", target: "c22", label: "limits", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "limits", type: "relates-to", strength: 7 } },
];

// Legal Contract Data Model Graph
const legalModelGraphNodes: FlowNode<NodeData>[] = [
  // Core Entities
  { id: "lm1", type: "default", position: { x: 600, y: 100 }, data: { label: "Contract", type: "concept", description: "A legally binding agreement between parties" } },
  { id: "lm2", type: "default", position: { x: 300, y: 250 }, data: { label: "Party", type: "organization", description: "An entity entering into the contract" } },
  { id: "lm3", type: "default", position: { x: 900, y: 250 }, data: { label: "Clause", type: "document", description: "A distinct section or provision in the contract" } },
  
  // Key Attributes
  { id: "lm4", type: "default", position: { x: 450, y: 100 }, data: { label: "Effective Date", type: "event", description: "When the contract becomes active" } },
  { id: "lm5", type: "default", position: { x: 750, y: 100 }, data: { label: "Termination Date", type: "event", description: "When the contract ends" } },
  { id: "lm6", type: "default", position: { x: 600, y: 0 }, data: { label: "Jurisdiction", type: "concept", description: "Legal authority governing the contract" } },
  
  // Clause Types
  { id: "lm7", type: "default", position: { x: 700, y: 400 }, data: { label: "Obligation", type: "concept", description: "A duty or commitment" } },
  { id: "lm8", type: "default", position: { x: 900, y: 400 }, data: { label: "Right", type: "concept", description: "An entitlement or privilege" } },
  { id: "lm9", type: "default", position: { x: 1100, y: 400 }, data: { label: "Definition", type: "concept", description: "Meaning of a specific term" } },
  
  // Financials
  { id: "lm10", type: "default", position: { x: 100, y: 400 }, data: { label: "Payment Term", type: "concept", description: "Conditions for payment" } },
  { id: "lm11", type: "default", position: { x: 300, y: 400 }, data: { label: "Asset", type: "concept", description: "Property or item of value" } },
  { id: "lm12", type: "default", position: { x: 200, y: 550 }, data: { label: "Currency", type: "concept", description: "Monetary unit" } },
  
  // Risk & Compliance
  { id: "lm13", type: "default", position: { x: 500, y: 550 }, data: { label: "Breach", type: "event", description: "Violation of contract terms" } },
  { id: "lm14", type: "default", position: { x: 700, y: 550 }, data: { label: "Remedy", type: "concept", description: "Redress for a breach" } },
  { id: "lm15", type: "default", position: { x: 900, y: 550 }, data: { label: "Liability", type: "concept", description: "Legal responsibility" } },
  { id: "lm16", type: "default", position: { x: 1100, y: 550 }, data: { label: "Indemnity", type: "concept", description: "Security against loss" } },
  
  // Execution
  { id: "lm17", type: "default", position: { x: 450, y: 250 }, data: { label: "Signature", type: "technology", description: "Proof of agreement" } },
  { id: "lm18", type: "default", position: { x: 150, y: 250 }, data: { label: "Signatory", type: "person", description: "Person signing the contract" } },
];

const legalModelGraphEdges: FlowEdge<EdgeData>[] = [
  // Contract Structure
  { id: "elm1-2", source: "lm1", target: "lm2", label: "has party", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "has party", type: "relates-to", strength: 10 } },
  { id: "elm1-3", source: "lm1", target: "lm3", label: "contains", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "contains", type: "includes", strength: 10 } },
  { id: "elm1-4", source: "lm1", target: "lm4", label: "starts on", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "starts on", type: "relates-to", strength: 9 } },
  { id: "elm1-5", source: "lm1", target: "lm5", label: "ends on", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "ends on", type: "relates-to", strength: 9 } },
  { id: "elm1-6", source: "lm1", target: "lm6", label: "governed by", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "governed by", type: "relates-to", strength: 8 } },
  
  // Clause Relationships
  { id: "elm3-7", source: "lm3", target: "lm7", label: "defines", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "defines", type: "includes", strength: 9 } },
  { id: "elm3-8", source: "lm3", target: "lm8", label: "grants", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "grants", type: "includes", strength: 9 } },
  { id: "elm3-9", source: "lm3", target: "lm9", label: "specifies", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "specifies", type: "includes", strength: 8 } },
  
  // Party Relationships
  { id: "elm2-7", source: "lm2", target: "lm7", label: "must perform", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "must perform", type: "relates-to", strength: 9 } },
  { id: "elm2-8", source: "lm2", target: "lm8", label: "holds", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "holds", type: "relates-to", strength: 9 } },
  { id: "elm2-18", source: "lm2", target: "lm18", label: "represented by", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "represented by", type: "relates-to", strength: 8 } },
  { id: "elm18-17", source: "lm18", target: "lm17", label: "provides", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "provides", type: "relates-to", strength: 10 } },
  { id: "elm17-1", source: "lm17", target: "lm1", label: "executes", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "executes", type: "relates-to", strength: 10 } },
  
  // Financials
  { id: "elm1-10", source: "lm1", target: "lm10", label: "specifies", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "specifies", type: "includes", strength: 8 } },
  { id: "elm10-12", source: "lm10", target: "lm12", label: "uses", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "uses", type: "relates-to", strength: 9 } },
  { id: "elm1-11", source: "lm1", target: "lm11", label: "concerns", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "concerns", type: "relates-to", strength: 7 } },
  
  // Risk & Compliance
  { id: "elm13-14", source: "lm13", target: "lm14", label: "triggers", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "triggers", type: "relates-to", strength: 9 } },
  { id: "elm13-15", source: "lm13", target: "lm15", label: "results in", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "results in", type: "relates-to", strength: 9 } },
  { id: "elm16-15", source: "lm16", target: "lm15", label: "covers", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "covers", type: "relates-to", strength: 8 } },
  { id: "elm3-16", source: "lm3", target: "lm16", label: "contains", type: "straight", markerEnd: { type: MarkerType.ArrowClosed }, data: { label: "contains", type: "includes", strength: 8 } },
];

// Export all templates
export const knowledgeGraphTemplates: KnowledgeGraphTemplate[] = [
  {
    id: "technology",
    name: "AI & Technology Research",
    description: "Knowledge graph showing AI concepts, research papers, organizations, and relationships in the technology domain",
    domain: "technology",
    nodes: technologyGraphNodes,
    edges: technologyGraphEdges,
  },
  {
    id: "finance",
    name: "Investment Banking & Trading",
    description: "Financial services knowledge graph covering trading, risk management, regulatory compliance, and market analysis",
    domain: "finance",
    nodes: financeGraphNodes,
    edges: financeGraphEdges,
  },
  {
    id: "insurance",
    name: "Insurance Claims & Underwriting",
    description: "Insurance industry knowledge graph featuring claims processing, underwriting, fraud detection, and policy administration",
    domain: "insurance",
    nodes: insuranceGraphNodes,
    edges: insuranceGraphEdges,
  },
  {
    id: "contract",
    name: "Contract Analysis & Management",
    description: "Legal contract knowledge graph showing key data points, obligations, parties, terms, risk clauses, and compliance requirements",
    domain: "legal",
    nodes: contractGraphNodes,
    edges: contractGraphEdges,
  },
  {
    id: "legal-model",
    name: "Legal Contract Data Model",
    description: "Abstract data model representing the structure, entities, and relationships in legal contracts",
    domain: "legal",
    nodes: legalModelGraphNodes,
    edges: legalModelGraphEdges,
  },
];

// Export default template (technology) for backward compatibility
export const initialNodes = technologyGraphNodes;
export const initialEdges = technologyGraphEdges;

export const getNodeColor = (type: NodeData["type"]) => {
  switch (type) {
    case "person": return "#8b5cf6";
    case "organization": return "#3b82f6";
    case "concept": return "#10b981";
    case "document": return "#f59e0b";
    case "technology": return "#ec4899";
    case "event": return "#06b6d4";
    default: return "#6b7280";
  }
};
