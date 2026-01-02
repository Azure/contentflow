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
import { knowledgeGraphTemplates, getNodeColor, NodeData, EdgeData } from "@/data/knowledgeGraphData";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";





export const KnowledgeGraph = () => {
  const [selectedTemplate, setSelectedTemplate] = useState(knowledgeGraphTemplates[0]);
  const [nodes, setNodes, onNodesChange] = useNodesState(selectedTemplate.nodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(selectedTemplate.edges);
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

  const handleTemplateChange = (templateId: string) => {
    const template = knowledgeGraphTemplates.find(t => t.id === templateId);
    if (template) {
      setSelectedTemplate(template);
      setNodes(template.nodes);
      setEdges(template.edges);
      setSelectedNode(null);
      setSelectedEdge(null);
      toast.success(`Switched to ${template.name}`);
    }
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
    a.download = `knowledge-graph-${selectedTemplate.id}.json`;
    a.click();
    toast.success("Graph exported");
  };

  return (
    <>
      <div className="container mx-auto px-6 py-12">
        <div className="mb-8">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h1 className="font-display text-4xl font-bold mb-2 text-foreground">Knowledge Graph</h1>
              <p className="text-muted-foreground">{selectedTemplate.description}</p>
            </div>
            <div className="min-w-[280px]">
              <Select value={selectedTemplate.id} onValueChange={handleTemplateChange}>
                <SelectTrigger className="w-full">
                  <SelectValue placeholder="Select template" />
                </SelectTrigger>
                <SelectContent>
                  {knowledgeGraphTemplates.map((template) => (
                    <SelectItem key={template.id} value={template.id}>
                      <div className="flex items-center gap-2">
                        <Badge variant="outline" className="capitalize">
                          {template.domain}
                        </Badge>
                        <span>{template.name}</span>
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
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