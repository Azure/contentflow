import { useState, useCallback, useEffect } from "react";
import ReactFlow, {
  Node,
  Edge,
  Controls,
  Background,
  useNodesState,
  useEdgesState,
  addEdge,
  Connection,
  MarkerType,
  BackgroundVariant,
} from "reactflow";
import "reactflow/dist/style.css";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";
import { 
  Plus, Play, ChevronDown, ChevronRight,
  Film, Wand2, Network, FolderInput, Save, Brain, GitBranch, FileText, Search,
  FileUp, FilePlus, Code, Layout
} from "lucide-react";
import { toast } from "sonner";
import { ExecutorNode } from "@/components/pipeline/ExecutorNode";
import { SubPipelineNode } from "@/components/pipeline/SubPipelineNode";
import { ExecutorConfigDialog } from "@/components/pipeline/ExecutorConfigDialog";
import { PipelineSaveDialog } from "@/components/pipeline/PipelineSaveDialog";
import { SavedPipelinesDialog, SavedPipeline } from "@/components/pipeline/SavedPipelinesDialog";
import { PipelineTemplate } from "@/types/pipeline";
import { executorTypes, ExecutorType } from "@/data/executorTypes";
import { nodesToYaml, yamlToNodes } from "@/lib/pipelineYamlConverter";
import { PipelineYamlEditor } from "@/components/pipeline/PipelineYamlEditor";
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";

const nodeTypes = {
  executor: ExecutorNode,
  subpipeline: SubPipelineNode,
};

export const PipelineBuilder = () => {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [selectedExecutor, setSelectedExecutor] = useState<ExecutorType | null>(null);
  const [configDialogOpen, setConfigDialogOpen] = useState(false);
  const [selectedNode, setSelectedNode] = useState<Node | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [expandedCategories, setExpandedCategories] = useState<Record<string, boolean>>({});
  const [showAllInCategory, setShowAllInCategory] = useState<Record<string, boolean>>({});
  
  // Pipeline management state
  const [currentPipelineId, setCurrentPipelineId] = useState<string | null>(null);
  const [currentPipelineName, setCurrentPipelineName] = useState<string>("");
  const [currentPipelineDescription, setCurrentPipelineDescription] = useState<string>("");
  const [savedPipelines, setSavedPipelines] = useState<SavedPipeline[]>([]);
  const [saveDialogOpen, setSaveDialogOpen] = useState(false);
  const [loadDialogOpen, setLoadDialogOpen] = useState(false);
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);
  
  // YAML view state
  const [viewMode, setViewMode] = useState<"canvas" | "yaml">("canvas");
  const [yamlContent, setYamlContent] = useState<string>("");
  const [yamlHasChanges, setYamlHasChanges] = useState(false);

  // Load template from localStorage if available
  useEffect(() => {
    const templateData = localStorage.getItem("selectedTemplate");
    if (templateData) {
      try {
        const template: PipelineTemplate = JSON.parse(templateData);
        loadTemplate(template);
        localStorage.removeItem("selectedTemplate");
        toast.success(`Loaded template: ${template.name}`);
      } catch (error) {
        console.error("Failed to load template:", error);
      }
    }
    
    // Load saved pipelines from localStorage
    loadSavedPipelines();
  }, []);

  // Load saved pipelines from localStorage
  const loadSavedPipelines = () => {
    try {
      const saved = localStorage.getItem("savedPipelines");
      if (saved) {
        setSavedPipelines(JSON.parse(saved));
      }
    } catch (error) {
      console.error("Failed to load saved pipelines:", error);
    }
  };

  // Track changes to mark as unsaved
  useEffect(() => {
    if (nodes.length > 0 || edges.length > 0) {
      setHasUnsavedChanges(true);
    }
  }, [nodes, edges]);

  // Update sub-pipeline nodes when saved pipelines change
  useEffect(() => {
    setNodes((nds) =>
      nds.map((node) =>
        node.type === "subpipeline"
          ? { ...node, data: { ...node.data, savedPipelines: savedPipelines } }
          : node
      )
    );
  }, [savedPipelines, setNodes]);

  // Sync canvas to YAML when switching to YAML view
  useEffect(() => {
    if (viewMode === "yaml") {
      const yaml = nodesToYaml(nodes, edges, currentPipelineName, currentPipelineDescription);
      setYamlContent(yaml);
      setYamlHasChanges(false);
    }
  }, [viewMode, nodes, edges, currentPipelineName, currentPipelineDescription]);

  const loadTemplate = (template: PipelineTemplate) => {
    setNodes(template.nodes.map(node => ({
      ...node,
      data: {
        ...node.data,
        executor: node.data.executor,
        ...(node.type === "subpipeline" && {
          selectedPipelineId: node.data.selectedPipelineId || "",
          savedPipelines: savedPipelines,
        }),
      },
    })));
    
    setEdges(template.edges.map(edge => ({
      ...edge,
      type: "smoothstep",
      animated: true,
      markerEnd: { type: MarkerType.ArrowClosed },
      style: { stroke: "hsl(var(--secondary))", strokeWidth: 2 },
    })));
  };

  const onConnect = useCallback(
    (params: Connection) => {
      setEdges((eds) =>
        addEdge(
          {
            ...params,
            type: "smoothstep",
            animated: true,
            markerEnd: { type: MarkerType.ArrowClosed },
            style: { stroke: "hsl(var(--secondary))", strokeWidth: 2 },
          },
          eds
        )
      );
    },
    [setEdges]
  );

  const addExecutorNode = (executor: ExecutorType, config?: any) => {
    const newNode: Node = {
      id: `${executor.id}-${Date.now()}`,
      type: executor.category === "pipeline" ? "subpipeline" : "executor",
      position: { x: Math.random() * 400 + 100, y: Math.random() * 300 + 100 },
      data: {
        label: config?.name || executor.name,
        executor: {
          ...executor,
          description: config?.description || executor.description,
        },
        config: config || {},
        ...(executor.category === "pipeline" && {
          selectedPipelineId: config?.selectedPipelineId || "",
          savedPipelines: savedPipelines,
        }),
      },
    };
    setNodes((nds) => [...nds, newNode]);
    toast.success(`Added ${executor.name}`);
  };

  const handleExecutorClick = (executor: ExecutorType) => {
    setSelectedExecutor(executor);
    setConfigDialogOpen(true);
  };

  // Handle drag start for executors - only serialize essential data
  const handleExecutorDragStart = (e: React.DragEvent, executor: ExecutorType) => {
    const executorData = {
      id: executor.id,
      name: executor.name,
      category: executor.category,
      color: executor.color,
      description: executor.description,
    };
    e.dataTransfer.setData("application/reactflow", JSON.stringify(executorData));
    e.dataTransfer.effectAllowed = "move";
  };

  // Handle child nodes change in sub-pipeline - no longer needed but keeping for compatibility
  const handleChildNodesChange = useCallback((subPipelineId: string, childNodes: Node[]) => {
    // This function is deprecated as sub-pipelines now reference saved pipelines
    console.log('handleChildNodesChange deprecated', subPipelineId, childNodes);
  }, []);

  // Handle child edges change in sub-pipeline - no longer needed but keeping for compatibility
  const handleChildEdgesChange = useCallback((subPipelineId: string, childEdges: Edge[]) => {
    // This function is deprecated as sub-pipelines now reference saved pipelines
    console.log('handleChildEdgesChange deprecated', subPipelineId, childEdges);
  }, []);

  const handleConfigSave = (config: any) => {
    if (selectedExecutor) {
      if (selectedNode) {
        // Update existing node
        setNodes((nds) =>
          nds.map((node) =>
            node.id === selectedNode.id
              ? { 
                  ...node, 
                  data: { 
                    ...node.data, 
                    label: config.name,
                    executor: {
                      ...node.data.executor,
                      description: config.description || node.data.executor.description,
                    },
                    config,
                    ...(selectedExecutor.category === "pipeline" && {
                      selectedPipelineId: config.selectedPipelineId || "",
                      savedPipelines: savedPipelines,
                    }),
                  } 
                }
              : node
          )
        );
        toast.success("Executor updated");
      } else {
        // Add new node
        addExecutorNode(selectedExecutor, config);
      }
    }
    setConfigDialogOpen(false);
    setSelectedNode(null);
    setSelectedExecutor(null);
  };

  const handleNodeDoubleClick = useCallback((_event: React.MouseEvent, node: Node) => {
    setSelectedNode(node);
    setSelectedExecutor(node.data.executor);
    setConfigDialogOpen(true);
  }, []);

  const runPipeline = () => {
    if (nodes.length === 0) {
      toast.error("Add at least one executor to run the pipeline");
      return;
    }
    toast.success("Pipeline executed successfully!");
  };

  // Group executors by category
  const groupedExecutors = executorTypes.reduce((acc, executor) => {
    if (!acc[executor.category]) {
      acc[executor.category] = [];
    }
    acc[executor.category].push(executor);
    return acc;
  }, {} as Record<string, ExecutorType[]>);

  // Filter executors based on search
  const filteredGroupedExecutors = Object.entries(groupedExecutors).reduce((acc, [category, executors]) => {
    const filtered = executors.filter(executor =>
      executor.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      executor.category.toLowerCase().includes(searchQuery.toLowerCase())
    );
    if (filtered.length > 0) {
      acc[category] = filtered;
    }
    return acc;
  }, {} as Record<string, ExecutorType[]>);

  const toggleCategory = (category: string) => {
    setExpandedCategories(prev => ({ ...prev, [category]: !prev[category] }));
  };

  const toggleShowAll = (category: string) => {
    setShowAllInCategory(prev => ({ ...prev, [category]: !prev[category] }));
  };

  const getCategoryIcon = (category: string) => {
    const icons: Record<string, React.ReactNode> = {
      input: <FolderInput className="w-4 h-4" />,
      extract: <FileText className="w-4 h-4" />,
      media: <Film className="w-4 h-4" />,
      transform: <GitBranch className="w-4 h-4" />,
      analyze: <Brain className="w-4 h-4" />,
      enrichment: <Wand2 className="w-4 h-4" />,
      output: <Save className="w-4 h-4" />,
      pipeline: <Network className="w-4 h-4" />
    };
    return icons[category] || null;
  };

  const getCategoryLabel = (category: string) => {
    const labels: Record<string, string> = {
      input: "Input Sources",
      extract: "Document Extraction",
      media: "Media Processing",
      transform: "Content Transformation",
      analyze: "AI Analysis",
      enrichment: "Content Enrichment",
      output: "Output Destinations",
      pipeline: "Pipeline Control"
    };
    return labels[category] || category;
  };

  // Pipeline management functions
  const createNewPipeline = () => {
    if (hasUnsavedChanges && nodes.length > 0) {
      if (!confirm("You have unsaved changes. Create a new pipeline anyway?")) {
        return;
      }
    }
    setNodes([]);
    setEdges([]);
    setCurrentPipelineId(null);
    setCurrentPipelineName("");
    setCurrentPipelineDescription("");
    setHasUnsavedChanges(false);
    toast.success("New pipeline created");
  };

  const savePipeline = (name: string, description: string) => {
    const now = new Date().toISOString();
    const pipeline: SavedPipeline = {
      id: currentPipelineId || `pipeline-${Date.now()}`,
      name,
      description,
      nodes,
      edges,
      createdAt: currentPipelineId
        ? savedPipelines.find((p) => p.id === currentPipelineId)?.createdAt || now
        : now,
      updatedAt: now,
    };

    const updatedPipelines = currentPipelineId
      ? savedPipelines.map((p) => (p.id === currentPipelineId ? pipeline : p))
      : [...savedPipelines, pipeline];

    setSavedPipelines(updatedPipelines);
    localStorage.setItem("savedPipelines", JSON.stringify(updatedPipelines));
    
    setCurrentPipelineId(pipeline.id);
    setCurrentPipelineName(name);
    setCurrentPipelineDescription(description);
    setHasUnsavedChanges(false);
    
    toast.success(currentPipelineId ? "Pipeline updated" : "Pipeline saved");
  };

  const handleSavePipeline = () => {
    if (nodes.length === 0) {
      toast.error("Cannot save an empty pipeline");
      return;
    }
    setSaveDialogOpen(true);
  };

  const loadPipeline = (pipeline: SavedPipeline) => {
    setNodes(pipeline.nodes.map(node => ({
      ...node,
      data: {
        ...node.data,
        ...(node.type === "subpipeline" && {
          selectedPipelineId: node.data.selectedPipelineId || "",
          savedPipelines: savedPipelines,
        }),
      },
    })));
    setEdges(pipeline.edges);
    setCurrentPipelineId(pipeline.id);
    setCurrentPipelineName(pipeline.name);
    setCurrentPipelineDescription(pipeline.description);
    setHasUnsavedChanges(false);
    toast.success(`Loaded: ${pipeline.name}`);
  };

  const deletePipeline = (pipelineId: string) => {
    const updatedPipelines = savedPipelines.filter((p) => p.id !== pipelineId);
    setSavedPipelines(updatedPipelines);
    localStorage.setItem("savedPipelines", JSON.stringify(updatedPipelines));
    
    if (currentPipelineId === pipelineId) {
      setCurrentPipelineId(null);
      setCurrentPipelineName("");
      setCurrentPipelineDescription("");
    }
    
    toast.success("Pipeline deleted");
  };

  // Handle YAML content changes
  const handleYamlChange = (newYaml: string) => {
    setYamlContent(newYaml);
    setYamlHasChanges(true);
  };

  // Apply YAML changes to canvas
  const handleApplyYaml = () => {
    try {
      const { nodes: newNodes, edges: newEdges, pipelineName, pipelineDescription } = 
        yamlToNodes(yamlContent, executorTypes);
      
      setNodes(newNodes);
      setEdges(newEdges);
      setCurrentPipelineName(pipelineName);
      setCurrentPipelineDescription(pipelineDescription);
      setYamlHasChanges(false);
      setHasUnsavedChanges(true);
      
      toast.success("Pipeline updated from YAML");
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Failed to parse YAML");
    }
  };

  return (
    <>
      <div className="container mx-auto px-6 py-12">
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="font-display text-4xl font-bold mb-2 text-foreground">
                {currentPipelineName || "Pipeline Builder"}
              </h1>
              <p className="text-muted-foreground">
                {currentPipelineDescription || "Design complex processing pipelines with sub-pipelines."}
              </p>
            </div>
            
            {/* Pipeline Action Buttons */}
            <div className="flex gap-2">
              <Button
                variant="outline"
                onClick={createNewPipeline}
                className="gap-2"
              >
                <FilePlus className="w-4 h-4" />
                New Pipeline
              </Button>
              <Button
                variant="outline"
                onClick={() => setLoadDialogOpen(true)}
                className="gap-2"
              >
                <FileUp className="w-4 h-4" />
                Load Pipeline
              </Button>
              <Button
                variant="outline"
                onClick={handleSavePipeline}
                className="gap-2"
              >
                <Save className="w-4 h-4" />
                {currentPipelineId ? "Update" : "Save"} Pipeline
              </Button>
            </div>
          </div>
        </div>

        <div className="grid lg:grid-cols-5 gap-6">
          {/* Executor Palette */}
          <Card className="p-6 lg:col-span-1 h-fit max-h-[700px] overflow-hidden flex flex-col">
            <h3 className="font-display text-lg font-bold mb-4 text-foreground">Executors</h3>
            
            {/* Search Box */}
            <div className="mb-4 relative">
              <Search className="w-4 h-4 absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground" />
              <Input
                placeholder="Search executors..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-9"
              />
            </div>

            {/* Scrollable Executor List */}
            <div className="space-y-2 overflow-y-auto flex-1 pr-2">
              {Object.entries(filteredGroupedExecutors).map(([category, executors]) => {
                const isExpanded = expandedCategories[category];
                const showAll = showAllInCategory[category];
                const displayExecutors = showAll ? executors : executors.slice(0, 2);
                const hasMore = executors.length > 2;

                return (
                  <Collapsible
                    key={category}
                    open={isExpanded}
                    onOpenChange={() => toggleCategory(category)}
                  >
                    <CollapsibleTrigger className="w-full">
                      <div className="flex items-center justify-between w-full px-2 py-1.5 hover:bg-accent rounded-lg transition-colors">
                        <div className="flex items-center gap-2">
                          <div className="text-muted-foreground">
                            {getCategoryIcon(category)}
                          </div>
                          <span className="text-xs font-semibold text-foreground">
                            {getCategoryLabel(category)}
                          </span>
                        </div>
                        <div className="flex items-center gap-1.5">
                          <span className="text-xs text-muted-foreground bg-muted px-1.5 py-0.5 rounded text-[10px]">
                            {executors.length}
                          </span>
                          {isExpanded ? (
                            <ChevronDown className="w-3.5 h-3.5" />
                          ) : (
                            <ChevronRight className="w-3.5 h-3.5" />
                          )}
                        </div>
                      </div>
                    </CollapsibleTrigger>
                    
                    <CollapsibleContent className="mt-1 space-y-1">
                      {displayExecutors.map((executor) => (
                        <Button
                          key={executor.id}
                          variant="outline"
                          className="w-full justify-start gap-2 h-auto py-1.5 px-2 hover:shadow-sm transition-all text-left cursor-grab active:cursor-grabbing"
                          onClick={() => handleExecutorClick(executor)}
                          draggable
                          onDragStart={(e) => handleExecutorDragStart(e, executor)}
                        >
                          <div className={`${executor.color} text-white p-1 rounded flex-shrink-0`}>
                            {executor.icon}
                          </div>
                          <span className="text-[11px] font-medium flex-1 leading-tight truncate">
                            {executor.name}
                          </span>
                          <Plus className="w-3 h-3 flex-shrink-0" />
                        </Button>
                      ))}
                      
                      {hasMore && !showAll && (
                        <Button
                          variant="ghost"
                          size="sm"
                          className="w-full text-[10px] text-muted-foreground hover:text-foreground py-1 h-auto"
                          onClick={(e) => {
                            e.stopPropagation();
                            toggleShowAll(category);
                          }}
                        >
                          View {executors.length - 2} more...
                        </Button>
                      )}
                      
                      {hasMore && showAll && (
                        <Button
                          variant="ghost"
                          size="sm"
                          className="w-full text-[10px] text-muted-foreground hover:text-foreground py-1 h-auto"
                          onClick={(e) => {
                            e.stopPropagation();
                            toggleShowAll(category);
                          }}
                        >
                          Show less
                        </Button>
                      )}
                    </CollapsibleContent>
                  </Collapsible>
                );
              })}

              {Object.keys(filteredGroupedExecutors).length === 0 && (
                <div className="text-center py-8">
                  <p className="text-sm text-muted-foreground">No executors found</p>
                </div>
              )}
            </div>

            <div className="mt-6 pt-6 border-t border-border">
              <Button 
                onClick={runPipeline}
                className="w-full bg-gradient-secondary hover:opacity-90 gap-2"
              >
                <Play className="w-4 h-4" />
                Run Pipeline
              </Button>
            </div>
          </Card>

          {/* ReactFlow Canvas / YAML Editor */}
          <Card className="lg:col-span-4 relative overflow-hidden" style={{ height: "700px" }}>
            {/* View Toggle */}
            <div className="absolute top-4 right-4 z-10">
              <ToggleGroup
                type="single"
                value={viewMode}
                onValueChange={(value) => value && setViewMode(value as "canvas" | "yaml")}
                className="bg-card border border-border rounded-lg shadow-lg"
              >
                <ToggleGroupItem value="canvas" aria-label="Canvas view" className="gap-2">
                  <Layout className="w-4 h-4" />
                  Canvas
                </ToggleGroupItem>
                <ToggleGroupItem value="yaml" aria-label="YAML view" className="gap-2">
                  <Code className="w-4 h-4" />
                  YAML
                </ToggleGroupItem>
              </ToggleGroup>
            </div>

            {viewMode === "canvas" ? (
              <>
                <div className="absolute inset-0">
                  <ReactFlow
                    nodes={nodes}
                    edges={edges}
                    onNodesChange={onNodesChange}
                    onEdgesChange={onEdgesChange}
                    onConnect={onConnect}
                    onNodeDoubleClick={handleNodeDoubleClick}
                    nodeTypes={nodeTypes}
                    defaultViewport={{ x: 0, y: 0, zoom: 0.8 }}
                    attributionPosition="bottom-left"
                  >
                    <Background variant={BackgroundVariant.Dots} gap={16} size={1} color="hsl(var(--border))" />
                    <Controls className="bg-card border border-border rounded-lg shadow-lg" />
                  </ReactFlow>
                </div>

                {nodes.length === 0 && (
                  <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                    <div className="text-center">
                      <GitBranch className="w-12 h-12 text-muted-foreground mx-auto mb-3" />
                      <p className="text-muted-foreground">Click executors to add them to the canvas</p>
                      <p className="text-sm text-muted-foreground mt-2">Double-click nodes to configure</p>
                    </div>
                  </div>
                )}
              </>
            ) : (
              <div className="p-6 h-full">
                <PipelineYamlEditor
                  value={yamlContent}
                  onChange={handleYamlChange}
                  onApply={handleApplyYaml}
                  hasChanges={yamlHasChanges}
                />
              </div>
            )}
          </Card>
        </div>
      </div>

      <ExecutorConfigDialog
        open={configDialogOpen}
        onOpenChange={setConfigDialogOpen}
        executor={selectedExecutor}
        initialConfig={selectedNode?.data.config}
        onSave={handleConfigSave}
        savedPipelines={savedPipelines}
      />

      <PipelineSaveDialog
        open={saveDialogOpen}
        onOpenChange={setSaveDialogOpen}
        onSave={savePipeline}
        initialName={currentPipelineName}
        initialDescription={currentPipelineDescription}
      />

      <SavedPipelinesDialog
        open={loadDialogOpen}
        onOpenChange={setLoadDialogOpen}
        pipelines={savedPipelines}
        onLoad={loadPipeline}
        onDelete={deletePipeline}
      />
    </>
  );
};