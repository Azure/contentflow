import { useState, useCallback } from "react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Network, Maximize2, Download, Plus, Edit, Trash2, Link as LinkIcon, ZoomIn, ZoomOut, Compass } from "lucide-react";
import { NodeEditDialog } from "@/components/knowledge/NodeEditDialog";
import { EdgeEditDialog } from "@/components/knowledge/EdgeEditDialog";
import { toast } from "sonner";
import ReactFlow, {
  Node as FlowNode,
  Edge as FlowEdge,
  Controls,
  Background,
  BackgroundVariant,
  useNodesState,
  useEdgesState,
  addEdge,
  Connection,
  MarkerType,
  Panel,
  NodeMouseHandler,
  EdgeMouseHandler,
  MiniMap,
} from "reactflow";
import "reactflow/dist/style.css";

interface NodeData {
  label: string;
  type: "person" | "organization" | "concept" | "document" | "technology" | "event";
  description?: string;
  metadata?: Record<string, string>;
}

interface EdgeData {
  label?: string;
  description?: string;
  type?: string;
  strength?: number;
}

const initialNodes: FlowNode<NodeData>[] = [
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

const initialEdges: FlowEdge<EdgeData>[] = [
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

const getNodeColor = (type: NodeData["type"]) => {
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

export const KnowledgeGraph = () => {
  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);
  const [selectedNode, setSelectedNode] = useState<FlowNode<NodeData> | null>(null);
  const [selectedEdge, setSelectedEdge] = useState<FlowEdge<EdgeData> | null>(null);
  const [editNodeDialogOpen, setEditNodeDialogOpen] = useState(false);
  const [editEdgeDialogOpen, setEditEdgeDialogOpen] = useState(false);

  const onConnect = useCallback(
    (params: Connection) => {
      const newEdge = {
        ...params,
        type: "straight",
        markerEnd: { type: MarkerType.ArrowClosed },
        data: { label: "relates to", type: "relates-to", strength: 5 },
        label: "relates to",
      };
      setEdges((eds) => addEdge(newEdge, eds));
      toast.success("Relationship created");
    },
    [setEdges]
  );

  const handleNodeClick: NodeMouseHandler = useCallback((event, node) => {
    setSelectedNode(node as FlowNode<NodeData>);
    setSelectedEdge(null);
  }, []);

  const handleEdgeClick: EdgeMouseHandler = useCallback((event, edge) => {
    setSelectedEdge(edge as FlowEdge<EdgeData>);
    setSelectedNode(null);
  }, []);

  const handleEditNode = () => {
    if (selectedNode) {
      setEditNodeDialogOpen(true);
    }
  };

  const handleEditEdge = () => {
    if (selectedEdge) {
      setEditEdgeDialogOpen(true);
    }
  };

  const handleSaveNode = (updatedData: NodeData) => {
    if (selectedNode) {
      const updatedNode = {
        ...selectedNode,
        data: updatedData,
      };
      setNodes((nds) => nds.map((n) => (n.id === selectedNode.id ? updatedNode : n)));
      setSelectedNode(updatedNode);
      toast.success("Node updated successfully");
    }
  };

  const handleSaveEdge = (updatedEdge: FlowEdge<EdgeData>) => {
    setEdges((eds) =>
      eds.map((e) =>
        e.id === updatedEdge.id
          ? { ...updatedEdge, label: updatedEdge.data?.label || updatedEdge.label }
          : e
      )
    );
    setSelectedEdge(updatedEdge);
    toast.success("Relationship updated");
  };

  const handleAddNode = () => {
    const newNode: FlowNode<NodeData> = {
      id: `node-${Date.now()}`,
      type: "default",
      position: { x: 400, y: 250 },
      data: {
        label: "New Node",
        type: "concept",
        description: "",
      },
    };
    setNodes((nds) => [...nds, newNode]);
    setSelectedNode(newNode);
    setEditNodeDialogOpen(true);
  };

  const handleDeleteNode = () => {
    if (selectedNode) {
      setNodes((nds) => nds.filter((n) => n.id !== selectedNode.id));
      setEdges((eds) =>
        eds.filter((e) => e.source !== selectedNode.id && e.target !== selectedNode.id)
      );
      setSelectedNode(null);
      toast.success("Node deleted");
    }
  };

  const handleDeleteEdge = (edgeId: string) => {
    setEdges((eds) => eds.filter((e) => e.id !== edgeId));
    setSelectedEdge(null);
    toast.success("Relationship deleted");
  };

  const handleDownload = () => {
    const data = {
      nodes: nodes.map((n) => ({ id: n.id, position: n.position, data: n.data })),
      edges: edges.map((e) => ({ id: e.id, source: e.source, target: e.target, data: e.data })),
    };
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "knowledge-graph.json";
    a.click();
    toast.success("Graph exported");
  };

  return (
    <>
      <div className="container mx-auto px-6 py-12">
        <div className="mb-8">
          <h1 className="font-display text-4xl font-bold mb-2 text-foreground">Knowledge Graph</h1>
          <p className="text-muted-foreground">Explore and edit extracted entities and relationships</p>
        </div>

        <div className="grid lg:grid-cols-4 gap-6">
          {/* Graph Canvas */}
          <Card className="lg:col-span-3 p-0 relative overflow-hidden" style={{ height: "700px" }}>
            <ReactFlow
              nodes={nodes.map((node) => ({
                ...node,
                style: {
                  backgroundColor: getNodeColor(node.data.type),
                  color: "white",
                  border: selectedNode?.id === node.id ? "3px solid #fbbf24" : "2px solid transparent",
                  borderRadius: "50%",
                  padding: "20px",
                  fontSize: "11px",
                  fontWeight: "600",
                  width: "100px",
                  height: "100px",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  textAlign: "center",
                  boxShadow: selectedNode?.id === node.id
                    ? "0 0 20px rgba(251, 191, 36, 0.5)"
                    : "0 4px 6px rgba(0, 0, 0, 0.1)",
                },
              }))}
              edges={edges.map((edge) => ({
                ...edge,
                style: {
                  stroke: selectedEdge?.id === edge.id ? "#fbbf24" : "#94a3b8",
                  strokeWidth: selectedEdge?.id === edge.id ? 3 : 2,
                },
                labelStyle: {
                  fill: "#475569",
                  fontWeight: 600,
                  fontSize: 11,
                },
              }))}
              onNodesChange={onNodesChange}
              onEdgesChange={onEdgesChange}
              onConnect={onConnect}
              onNodeClick={handleNodeClick}
              onEdgeClick={handleEdgeClick}
              fitView
              attributionPosition="bottom-right"
            >
              <Background variant={BackgroundVariant.Dots} gap={16} size={1} />
              <Controls />
              <MiniMap
                nodeColor={(node) => getNodeColor((node.data as NodeData).type)}
                nodeStrokeWidth={3}
                zoomable
                pannable
              />
              <Panel position="top-right" className="flex gap-2">
                <Button size="icon" variant="outline" onClick={handleDownload}>
                  <Download className="w-4 h-4" />
                </Button>
                <Button size="icon" className="bg-gradient-secondary" onClick={handleAddNode}>
                  <Plus className="w-4 h-4" />
                </Button>
              </Panel>
            </ReactFlow>
          </Card>

          {/* Details Panel */}
          <Card className="lg:col-span-1 p-6">
            {selectedNode ? (
              <>
                <h3 className="font-display text-lg font-bold mb-4 text-foreground">Node Details</h3>
                <div className="space-y-4">
                  <div>
                    <label className="text-sm text-muted-foreground">Label</label>
                    <p className="font-medium text-foreground">{selectedNode.data.label}</p>
                  </div>
                  
                  <div>
                    <label className="text-sm text-muted-foreground">Type</label>
                    <div className="mt-1">
                      <Badge variant="outline" className="capitalize">
                        {selectedNode.data.type}
                      </Badge>
                    </div>
                  </div>

                  {selectedNode.data.description && (
                    <div>
                      <label className="text-sm text-muted-foreground">Description</label>
                      <p className="text-sm text-foreground mt-1">{selectedNode.data.description}</p>
                    </div>
                  )}

                  {selectedNode.data.metadata && Object.keys(selectedNode.data.metadata).length > 0 && (
                    <div>
                      <label className="text-sm text-muted-foreground">Metadata</label>
                      <div className="mt-2 space-y-1">
                        {Object.entries(selectedNode.data.metadata).map(([key, value]) => (
                          <div key={key} className="text-xs">
                            <span className="font-mono text-muted-foreground">{key}:</span>{" "}
                            <span className="text-foreground">{value}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  <div>
                    <label className="text-sm text-muted-foreground">Connections</label>
                    <p className="text-2xl font-bold text-foreground">
                      {edges.filter((e) => e.source === selectedNode.id || e.target === selectedNode.id).length}
                    </p>
                  </div>

                  <div className="pt-4 space-y-2 border-t border-border">
                    <Button className="w-full gap-2" onClick={handleEditNode}>
                      <Edit className="w-4 h-4" />
                      Edit Node
                    </Button>
                    <Button 
                      className="w-full" 
                      variant="destructive"
                      onClick={handleDeleteNode}
                    >
                      <Trash2 className="w-4 h-4 mr-2" />
                      Delete Node
                    </Button>
                  </div>
                </div>
              </>
            ) : selectedEdge ? (
              <>
                <h3 className="font-display text-lg font-bold mb-4 text-foreground">Relationship Details</h3>
                <div className="space-y-4">
                  <div>
                    <label className="text-sm text-muted-foreground">Label</label>
                    <p className="font-medium text-foreground">{selectedEdge.data?.label || selectedEdge.label || "No label"}</p>
                  </div>
                  
                  <div>
                    <label className="text-sm text-muted-foreground">Type</label>
                    <div className="mt-1">
                      <Badge variant="outline" className="capitalize">
                        {selectedEdge.data?.type || "relates-to"}
                      </Badge>
                    </div>
                  </div>

                  <div>
                    <label className="text-sm text-muted-foreground">From</label>
                    <p className="text-sm text-foreground mt-1">
                      {nodes.find((n) => n.id === selectedEdge.source)?.data.label || selectedEdge.source}
                    </p>
                  </div>

                  <div>
                    <label className="text-sm text-muted-foreground">To</label>
                    <p className="text-sm text-foreground mt-1">
                      {nodes.find((n) => n.id === selectedEdge.target)?.data.label || selectedEdge.target}
                    </p>
                  </div>

                  {selectedEdge.data?.description && (
                    <div>
                      <label className="text-sm text-muted-foreground">Description</label>
                      <p className="text-sm text-foreground mt-1">{selectedEdge.data.description}</p>
                    </div>
                  )}

                  {selectedEdge.data?.strength && (
                    <div>
                      <label className="text-sm text-muted-foreground">Strength</label>
                      <p className="text-sm text-foreground mt-1">{selectedEdge.data.strength}/10</p>
                    </div>
                  )}

                  <div className="pt-4 space-y-2 border-t border-border">
                    <Button className="w-full gap-2" onClick={handleEditEdge}>
                      <Edit className="w-4 h-4" />
                      Edit Relationship
                    </Button>
                    <Button 
                      className="w-full" 
                      variant="destructive"
                      onClick={() => handleDeleteEdge(selectedEdge.id)}
                    >
                      <Trash2 className="w-4 h-4 mr-2" />
                      Delete Relationship
                    </Button>
                  </div>
                </div>
              </>
            ) : (
              <div className="text-center py-12">
                <Network className="w-12 h-12 text-muted-foreground mx-auto mb-3" />
                <p className="text-sm text-muted-foreground">Click a node or edge to view details</p>
                <p className="text-xs text-muted-foreground mt-2">Drag to reposition • Connect nodes to create relationships</p>
              </div>
            )}
          </Card>
        </div>
      </div>

      <NodeEditDialog
        open={editNodeDialogOpen}
        onOpenChange={setEditNodeDialogOpen}
        node={selectedNode}
        onSave={handleSaveNode}
      />

      <EdgeEditDialog
        open={editEdgeDialogOpen}
        onOpenChange={setEditEdgeDialogOpen}
        edge={selectedEdge}
        onSave={handleSaveEdge}
        onDelete={handleDeleteEdge}
      />
    </>
  );
};