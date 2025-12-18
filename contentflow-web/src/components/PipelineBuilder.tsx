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
  FileUp, FilePlus, Code, Layout, Loader2, Clock,
  Settings
} from "lucide-react";
import { toast } from "sonner";
import { ExecutorNode } from "@/components/pipeline/ExecutorNode";
import { SubPipelineNode } from "@/components/pipeline/SubPipelineNode";
import { ExecutorConfigDialog } from "@/components/pipeline/ExecutorConfigDialog";
import { PipelineSaveDialog, PipelineSaveDialogDataProps } from "@/components/pipeline/PipelineSaveDialog";
import { LoadPipelinesDialog } from "@/components/pipeline/LoadPipelinesDialog";
import { PipelineYamlEditor } from "@/components/pipeline/PipelineYamlEditor";
import { PipelineExecutionStatus } from "@/components/pipeline/PipelineExecutionStatus";
import { PipelineExecutionsListDialog } from "@/components/pipeline/PipelineExecutionsListDialog";
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";
import { PipelineTemplate, ExecutorCatalogDefinition, Pipeline, SavePipelineRequest } from "@/types/components";
import { nodesToYaml, yamlToNodes } from "@/lib/pipelineYamlConverter";
import { getPipelines, savePipeline as savePipelineApi, deletePipeline as deletePipelineApi, executePipeline, getExecutionHistory } from "@/lib/api/pipelinesApi";
import { getExecutors } from "@/lib/api/executorsApi";
import { ExecutorWithUI, enrichExecutorsWithUI } from "@/lib/executorUiMapper";

const nodeTypes = {
  executor: ExecutorNode,
  subpipeline: SubPipelineNode,
};

export const PipelineBuilder = () => {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [selectedExecutor, setSelectedExecutor] = useState<ExecutorWithUI | null>(null);
  const [configDialogOpen, setConfigDialogOpen] = useState(false);
  const [selectedNode, setSelectedNode] = useState<Node | null>(null);
  const [selectedEdges, setSelectedEdges] = useState<string[]>([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [expandedCategories, setExpandedCategories] = useState<Record<string, boolean>>({});
  const [showAllInCategory, setShowAllInCategory] = useState<Record<string, boolean>>({});
  const [executorTypes, setExecutorTypes] = useState<ExecutorWithUI[]>([]);
  const [isLoadingExecutors, setIsLoadingExecutors] = useState(true);
  
  // Pipeline management state
  const [currentPipeline, setCurrentPipeline] = useState<Pipeline | null>(null);
  const [loadedPipelines, setLoadedPipelines] = useState<Pipeline[]>([]);
  const [saveDialogOpen, setSaveDialogOpen] = useState(false);
  const [loadDialogOpen, setLoadDialogOpen] = useState(false);
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  
  // YAML view state
  const [viewMode, setViewMode] = useState<"canvas" | "yaml">("canvas");
  const [yamlContent, setYamlContent] = useState<string>("");
  const [yamlHasChanges, setYamlHasChanges] = useState(false);
  
  // Execution state
  const [executionId, setExecutionId] = useState<string | null>(null);
  const [isExecuting, setIsExecuting] = useState(false);
  const [executionsDialogOpen, setExecutionsDialogOpen] = useState(false);
  const [hasExecutions, setHasExecutions] = useState(false);

  // Load executors from API
  useEffect(() => {
    const loadExecutors = async () => {
      try {
        setIsLoadingExecutors(true);
        const executors = await getExecutors();
        const enrichedExecutors = enrichExecutorsWithUI(executors);
        setExecutorTypes(enrichedExecutors);
      } catch (error) {
        console.error("Failed to load executors:", error);
        toast.error("Failed to load executors");
      } finally {
        setIsLoadingExecutors(false);
      }
    };

    loadExecutors();
  }, []);

  // Load template from localStorage if available
  useEffect(() => {
    // Only load template after executors are loaded
    if (isLoadingExecutors || executorTypes.length === 0) {
      return;
    }
    
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
    
    // Load saved pipelines
    loadSavedPipelines();
  }, [executorTypes, isLoadingExecutors]);

  // Load saved pipelines from API
  const loadSavedPipelines = async () => {
    try {
      const pipelines = await getPipelines();
      setLoadedPipelines(pipelines);
    } catch (error) {
      console.error("Failed to load saved pipelines:", error);
      toast.error("Failed to load pipelines");
    }
  };

  // // Track changes to mark as unsaved
  // useEffect(() => {
  //   if (nodes.length > 0 || edges.length > 0) {
  //     setHasUnsavedChanges(true);
  //   }
  // }, [nodes, edges]);

  // Update sub-pipeline nodes when saved pipelines change
  useEffect(() => {
    setNodes((nds) =>
      nds.map((node) =>
        node.type === "subpipeline"
          ? { ...node, data: { ...node.data, availablePipelines: loadedPipelines } }
          : node
      )
    );
  }, [loadedPipelines, setNodes]);

  // Sync canvas to YAML when switching to YAML view
  useEffect(() => {
    if (viewMode === "yaml") {
      const yaml = nodesToYaml(nodes, edges, currentPipeline?.name || "", currentPipeline?.description || "");
      setYamlContent(yaml);
      setYamlHasChanges(false);
    }
  }, [viewMode, nodes, edges, currentPipeline]);

  const loadTemplate = (template: PipelineTemplate) => {
    setNodes(template.nodes.map(node => {
      // Re-hydrate executor with full details from catalog
      const fullExecutor = executorTypes.find(et => et.id === node.data.executor?.id);
      
      return {
        ...node,
        data: {
          ...node.data,
          executor: fullExecutor || node.data.executor,
          onDelete: () => handleDeleteNode(node.id),
          ...(node.type === "subpipeline" && {
            selectedPipelineId: node.data.selectedPipelineId || "",
            availablePipelines: loadedPipelines,
          }),
        },
      };
    }));
    
    setEdges(template.edges.map(edge => ({
      ...edge,
      type: "default",
      animated: true,
      markerEnd: { type: MarkerType.ArrowClosed },
      style: { stroke: "hsl(var(--secondary))", strokeWidth: 2 },
    })));
    setSelectedEdges([]);
  };

  const onConnect = useCallback(
    (params: Connection) => {
      setEdges((eds) =>
        addEdge(
          {
            ...params,
            type: "default",
            animated: true,
            markerEnd: { type: MarkerType.ArrowClosed },
            style: { stroke: "hsl(var(--secondary))", strokeWidth: 2 },
          },
          eds
        )
      );
      
      setSelectedEdges([]);
      setHasUnsavedChanges(true);
    },
    [setEdges]
  );

  const addExecutorNode = (executor: ExecutorWithUI, config?: any) => {
    const nodeId = `${executor.id}-${Date.now()}`;
    const newNode: Node = {
      id: nodeId,
      type: executor.category === "pipeline" ? "subpipeline" : "executor",
      position: { x: Math.random() * 400 + 100, y: Math.random() * 300 + 100 },
      data: {
        label: config?.name || executor.name,
        executor: {
          ...executor,
          description: config?.description || executor.description,
        },
        config: config || {},
        onDelete: () => handleDeleteNode(nodeId),
        ...(executor.category === "pipeline" && {
          selectedPipelineId: config?.selectedPipelineId || "",
          availablePipelines: loadedPipelines,
        }),
      },
    };
    setNodes((nds) => [...nds, newNode]);
    toast.success(`Added ${executor.name}`);
  };

  const handleExecutorClick = (executor: ExecutorWithUI) => {
    setSelectedExecutor(executor);
    setSelectedNode(null); // Clear any previously selected node when adding new executor
    setConfigDialogOpen(true);
  };

  // Handle drag start for executors - only serialize essential data
  const handleExecutorDragStart = (e: React.DragEvent, executor: ExecutorWithUI) => {
    const executorData = {
      id: executor.id,
      name: executor.name,
      category: executor.category,
      description: executor.description,
    };
    e.dataTransfer.setData("application/reactflow", JSON.stringify(executorData));
    e.dataTransfer.effectAllowed = "move";
  };

  const handleConfigDialogOpenChange = (open: boolean) => {
    setConfigDialogOpen(open);
    if (!open) {
      // Clear selection when dialog is closed
      setSelectedNode(null);
      setSelectedExecutor(null);
    }
  };

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
                    onDelete: node.data.onDelete,
                    ...(selectedExecutor.category === "pipeline" && {
                      selectedPipelineId: config.selectedPipelineId || "",
                      availablePipelines: loadedPipelines,
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
    setHasUnsavedChanges(true);
  };

  const handleNodeDoubleClick = useCallback((_event: React.MouseEvent, node: Node) => {
    setSelectedNode(node);
    setSelectedExecutor(node.data.executor);
    setConfigDialogOpen(true);
  }, []);

  const handleDeleteNode = useCallback((nodeId: string) => {
    setNodes((nds) => nds.filter((node) => node.id !== nodeId));
    setEdges((eds) => eds.filter((edge) => edge.source !== nodeId && edge.target !== nodeId));
    setHasUnsavedChanges(true);
    toast.success("Executor removed");
  }, [setNodes, setEdges]);

  const handleEdgeClick = useCallback((_event: React.MouseEvent, edge: Edge) => {
    setSelectedEdges([edge.id]);
  }, []);

  const handlePaneClick = useCallback(() => {
    setSelectedEdges([]);
  }, []);

  const handleDeleteSelectedEdges = useCallback(() => {
    if (selectedEdges.length > 0) {
      setEdges((eds) => eds.filter((edge) => !selectedEdges.includes(edge.id)));
      setSelectedEdges([]);
      setHasUnsavedChanges(true);
      toast.success("Connection removed");
    }
  }, [selectedEdges, setEdges]);

  // Handle keyboard deletion
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Delete" || event.key === "Backspace") {
        if (selectedEdges.length > 0 && document.activeElement?.tagName !== "INPUT" && document.activeElement?.tagName !== "TEXTAREA") {
          event.preventDefault();
          handleDeleteSelectedEdges();
        }
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [selectedEdges, handleDeleteSelectedEdges]);

  // Group executors by category
  const groupedExecutors = executorTypes.reduce((acc, executor) => {
    const category = executor.category.toLocaleLowerCase();
    if (!acc[category]) {
      acc[category] = [];
    }
    acc[category].push(executor);
    return acc;
  }, {} as Record<string, ExecutorWithUI[]>);

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
  }, {} as Record<string, ExecutorWithUI[]>);

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
      analyse: <Brain className="w-4 h-4" />,
      enrichment: <Wand2 className="w-4 h-4" />,
      output: <Save className="w-4 h-4" />,
      pipeline: <Network className="w-4 h-4" />,
      utility: <Settings className="w-4 h-4" />,
    };
    return icons[category.toLocaleLowerCase()] || null;
  };

  const getCategoryLabel = (category: string) => {
    const labels: Record<string, string> = {
      input: "Input Sources",
      extract: "Content Extraction",
      media: "Media Processing",
      transform: "Transformation",
      analyse: "AI Analysis",
      enrichment: "Enrichment",
      output: "Output Destinations",
      pipeline: "Pipeline Control",
      utility: "Utility",
    };
    return labels[category.toLocaleLowerCase()] || category;
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
    setCurrentPipeline(null);
    setHasUnsavedChanges(false);
    toast.success("New pipeline created");
  };

  const savePipeline = async (data: PipelineSaveDialogDataProps) => {
    setIsSaving(true);
    try {
      const yaml = nodesToYaml(nodes, edges, data.name, data.description);
      
      // Serialize nodes and edges for storage (remove non-serializable data like React components)
      const serializableNodes = nodes.map(node => ({
        ...node,
        data: {
          ...node.data,
          executor: node.data.executor ? {
            id: node.data.executor.id,
            type: node.data.executor.type,
            name: node.data.executor.name,
            color: node.data.executor.color,
            category: node.data.executor.category,
            description: node.data.executor.description,
          } : undefined,
          // Explicitly preserve config
          config: node.data.config,
          // Explicitly preserve selectedPipelineId for sub-pipelines
          selectedPipelineId: node.data.selectedPipelineId,
        },
      }));

      const pipelineData: SavePipelineRequest = {
        id: currentPipeline?.id || undefined,
        name: data.name,
        description: data.description,
        yaml,
        nodes: serializableNodes,
        edges: edges,
        tags: data.tags,
        version: data.version,
        enabled: data.enabled,
        retry_delay: data.retry_delay,
        timeout: data.timeout,
        retries: data.retries,
      };

      const savedPipeline = await savePipelineApi(pipelineData);
      
      // Reload all pipelines to get updated list
      await loadSavedPipelines();
      
      setCurrentPipeline(savedPipeline);
      setHasUnsavedChanges(false);
      
      toast.success(currentPipeline?.id ? "Pipeline updated" : "Pipeline saved");
    } catch (error) {
      console.error("Failed to save pipeline:", error);
      toast.error("Failed to save pipeline");
    } finally {
      setIsSaving(false);
    }
  };

  const handleSavePipeline = () => {
    if (nodes.length === 0) {
      toast.error("Cannot save an empty pipeline");
      return;
    }
    setSaveDialogOpen(true);
  };

  const handleExecutePipeline = async () => {
    if (!currentPipeline?.id) {
      toast.error("Please save the pipeline before executing");
      return;
    }

    try {
      setIsExecuting(true);
      const result = await executePipeline(currentPipeline.id, {}, {});
      setExecutionId(result.execution_id);
      setHasExecutions(true);
      toast.success("Pipeline execution started");
    } catch (error) {
      console.error("Failed to execute pipeline:", error);
      toast.error("Failed to execute pipeline");
      setIsExecuting(false);
    }
  };

  const checkPipelineExecutions = async () => {
    if (!currentPipeline?.id) {
      setHasExecutions(false);
      return;
    }
    
    try {
      const executions = await getExecutionHistory(currentPipeline.id, 1);
      setHasExecutions(executions.length > 0);
    } catch (error) {
      console.error("Failed to check executions:", error);
      setHasExecutions(false);
    }
  };

  const loadPipeline = (pipeline: Pipeline) => {
    setNodes(pipeline.nodes.map(node => {
      // Re-hydrate executor with full details from catalog
      const fullExecutor = executorTypes.find(et => et.id === node.data.executor?.id);
      
      return {
        ...node,
        data: {
          ...node.data,
          executor: fullExecutor || node.data.executor,
          onDelete: () => handleDeleteNode(node.id),
          ...(node.type === "subpipeline" && {
            selectedPipelineId: node.data.selectedPipelineId || "",
            availablePipelines: loadedPipelines,
          }),
        },
      };
    }));
    setEdges(pipeline.edges);
    setSelectedEdges([]);
    setCurrentPipeline(pipeline);
    setHasUnsavedChanges(false);
    toast.success(`Loaded: ${pipeline.name}`);
    // Check if this pipeline has executions
    checkPipelineExecutions();
  };

  // Check for executions when current pipeline changes
  useEffect(() => {
    checkPipelineExecutions();
  }, [currentPipeline?.id]);

  const deletePipeline = async (pipelineId: string) => {
    try {
      await deletePipelineApi(pipelineId);
      
      // Reload pipelines after deletion
      await loadSavedPipelines();
      
      if (currentPipeline?.id === pipelineId) {
        setCurrentPipeline(null);
      }
      
      toast.success("Pipeline deleted");
    } catch (error) {
      console.error("Failed to delete pipeline:", error);
      toast.error("Failed to delete pipeline");
    }
  };

  // Handle YAML content changes
  const handleYamlChange = (newYaml: string) => {
    setYamlContent(newYaml);
    setYamlHasChanges(true);
    setHasUnsavedChanges(true);
  };

  // Apply YAML changes to canvas
  const handleApplyYaml = () => {
    try {
      const { nodes: newNodes, edges: newEdges, pipelineName, pipelineDescription } = 
        yamlToNodes(yamlContent, executorTypes);
      
      setNodes(newNodes);
      setEdges(newEdges);
      setCurrentPipeline(prev => ({
        ...(prev || { id: '', 
                      yaml: '', 
                      updated_at: '', 
                      created_at: '', 
                      nodes: [], 
                      edges: [], 
                      name: '', 
                      description: '' }),
        name: pipelineName,
        description: pipelineDescription,
      }));
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
                {currentPipeline?.name || "Pipeline Builder"}
              </h1>
              <p className="text-muted-foreground">
                {currentPipeline?.description || "Design complex processing pipelines with sub-pipelines."}
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
                disabled={isSaving}
                className="gap-2"
              >
                {isSaving ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <Save className="w-4 h-4" />
                )}
                {hasUnsavedChanges ? "*" : ""} Save Pipeline
              </Button>
              <div className="flex gap-2">
                <Button
                  onClick={handleExecutePipeline}
                  disabled={!currentPipeline?.id || isExecuting}
                  className="gap-2"
                >
                  {isExecuting ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <Play className="w-4 h-4" />
                  )}
                  Execute
                </Button>
                <Button
                  variant="outline"
                  onClick={() => setExecutionsDialogOpen(true)}
                  disabled={!currentPipeline?.id || !hasExecutions}
                  className="gap-2"
                >
                  <Clock className="w-4 h-4" />
                  View Executions
                </Button>
              </div>
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
              {isLoadingExecutors ? (
                <div className="flex items-center justify-center py-8">
                  <Loader2 className="w-6 h-6 animate-spin text-muted-foreground" />
                </div>
              ) : Object.entries(filteredGroupedExecutors).map(([category, executors]) => {
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
                      <div className="flex items-center justify-between w-full px-1.5 py-1.5 hover:bg-accent rounded-lg transition-colors">
                        <div className="flex items-center gap-2">
                          <div className="text-muted-foreground">
                            {getCategoryIcon(category)}
                          </div>
                          <span 
                            className="text-xs font-semibold text-foreground text-left truncate flex-1"
                            title={getCategoryLabel(category)}
                          >
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

              {!isLoadingExecutors && Object.keys(filteredGroupedExecutors).length === 0 && (
                <div className="text-center py-8">
                  <p className="text-sm text-muted-foreground">No executors found</p>
                </div>
              )}
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
                    edges={edges.map(edge => ({
                      ...edge,
                      selected: selectedEdges.includes(edge.id),
                      style: {
                        ...edge.style,
                        stroke: selectedEdges.includes(edge.id) ? "hsl(var(--destructive))" : edge.style?.stroke,
                        strokeWidth: selectedEdges.includes(edge.id) ? 3 : edge.style?.strokeWidth || 2,
                      },
                    }))}
                    onNodesChange={onNodesChange}
                    onEdgesChange={onEdgesChange}
                    onConnect={onConnect}
                    onNodeDoubleClick={handleNodeDoubleClick}
                    onEdgeClick={handleEdgeClick}
                    onPaneClick={handlePaneClick}
                    nodeTypes={nodeTypes}
                    defaultViewport={{ x: 0, y: 0, zoom: 0.8 }}
                    attributionPosition="bottom-left"
                    deleteKeyCode="Delete"
                    edgesFocusable={true}
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
        onOpenChange={handleConfigDialogOpenChange}
        executor={selectedExecutor}
        initialConfig={selectedNode?.data.config}
        onSave={handleConfigSave}
        availablePipelines={loadedPipelines}
      />

      <PipelineSaveDialog
        open={saveDialogOpen}
        onOpenChange={setSaveDialogOpen}
        onSave={savePipeline}
        pipeline={currentPipeline || undefined}
      />

      <LoadPipelinesDialog
        open={loadDialogOpen}
        onOpenChange={setLoadDialogOpen}
        pipelines={loadedPipelines}
        onLoad={loadPipeline}
        onDelete={deletePipeline}
      />

      {executionId && (
        <PipelineExecutionStatus
          executionId={executionId}
          onClose={() => {
            setExecutionId(null);
            setIsExecuting(false);
          }}
        />
      )}

      {currentPipeline && (
        <PipelineExecutionsListDialog
          pipelineId={currentPipeline.id}
          pipelineName={currentPipeline.name}
          open={executionsDialogOpen}
          onOpenChange={setExecutionsDialogOpen}
        />
      )}
    </>
  );
};