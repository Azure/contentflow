import { Node, Edge } from "reactflow";
import yaml from "js-yaml";
import type { ExecutorWithUI } from "./executorUiMapper";

export interface PipelineYamlFormat {
  pipeline: {
    name?: string;
    description?: string;
    executors: Array<{
      id: string;
      name: string;
      type: string;
      position: { x: number; y: number };
      description?: string;
      settings?: Record<string, any>;
    }>;
    edges: Array<{
      from: string | string[];
      to: string | string[];
      type?: "sequential" | "parallel" | "join" | "conditional";
      wait_strategy?: "all" | "any";
      description?: string;
    }>;
  };
}

/**
 * Convert ReactFlow nodes and edges to YAML format
 */
export function nodesToYaml(
  nodes: Node[],
  edges: Edge[],
  pipelineName?: string,
  pipelineDescription?: string
): string {
  // Group edges by source to detect parallel patterns
  const edgesBySource = new Map<string, string[]>();
  const edgesByTarget = new Map<string, string[]>();
  
  edges.forEach((edge) => {
    // Group by source
    if (!edgesBySource.has(edge.source)) {
      edgesBySource.set(edge.source, []);
    }
    edgesBySource.get(edge.source)!.push(edge.target);
    
    // Group by target
    if (!edgesByTarget.has(edge.target)) {
      edgesByTarget.set(edge.target, []);
    }
    edgesByTarget.get(edge.target)!.push(edge.source);
  });
  
  // Convert edges to YAML format
  const yamlEdges: Array<{
    from: string | string[];
    to: string | string[];
    type?: "sequential" | "parallel" | "join";
    wait_strategy?: "all";
  }> = [];
  
  const processedPairs = new Set<string>();
  
  edges.forEach((edge) => {
    const sourceTargets = edgesBySource.get(edge.source) || [];
    const targetSources = edgesByTarget.get(edge.target) || [];
    
    // Check if this is a parallel fan-out (one source, multiple targets)
    if (sourceTargets.length > 1) {
      const pairKey = `${edge.source}->${sourceTargets.sort().join(",")}`;
      if (!processedPairs.has(pairKey)) {
        yamlEdges.push({
          from: edge.source,
          to: sourceTargets,
          type: "parallel",
        });
        processedPairs.add(pairKey);
      }
    }
    // Check if this is a join fan-in (multiple sources, one target)
    else if (targetSources.length > 1) {
      const pairKey = `${targetSources.sort().join(",")}->${edge.target}`;
      if (!processedPairs.has(pairKey)) {
        yamlEdges.push({
          from: targetSources,
          to: edge.target,
          type: "join",
          wait_strategy: "all",
        });
        processedPairs.add(pairKey);
      }
    }
    // Simple sequential edge
    else {
      const pairKey = `${edge.source}->${edge.target}`;
      if (!processedPairs.has(pairKey)) {
        yamlEdges.push({
          from: edge.source,
          to: edge.target,
          type: "sequential",
        });
        processedPairs.add(pairKey);
      }
    }
  });

  const pipelineData: PipelineYamlFormat = {
    pipeline: {
      name: pipelineName || "Untitled Pipeline",
      description: pipelineDescription || "",
      executors: nodes.map((node) => {
        // Extract the actual settings from node.data.config
        const actualSettings = node.data.config?.settings || {};
        
        const executor: any = {
          id: node.id,
          name: node.data.config?.name || node.data.label || node.data.executor?.name || "Unnamed",
          type: node.data.executor?.id || "unknown",
          position: {
            x: Math.round(node.position.x),
            y: Math.round(node.position.y),
          },
          ...(node.data.config?.description || node.data.executor?.description
            ? { description: node.data.config?.description || node.data.executor.description }
            : {}),
          ...(Object.keys(actualSettings).length > 0
            ? { settings: actualSettings }
            : {}),
        };

        // Handle sub-pipeline with pipeline reference
        if (node.type === "subpipeline" && (node.data.selectedPipelineId || node.data.config?.selectedPipelineId)) {
          executor.settings = {
            ...(executor.settings || {}),
            pipeline_id: node.data.selectedPipelineId || node.data.config?.selectedPipelineId,
          };
        }

        return executor;
      }),
      edges: yamlEdges,
    },
  };

  return yaml.dump(pipelineData, {
    indent: 2,
    lineWidth: 120,
    noRefs: true,
    //flowLevel: 3, // Use flow style for nested arrays (like edge to/from arrays)
  });
}

/**
 * Convert YAML string back to ReactFlow nodes and edges
 */
export function yamlToNodes(
  yamlString: string,
  executorTypes: ExecutorWithUI[]
): {
  nodes: Node[];
  edges: Edge[];
  pipelineName: string;
  pipelineDescription: string;
} {
  try {
    const data = yaml.load(yamlString) as PipelineYamlFormat;

    if (!data.pipeline) {
      throw new Error("Invalid pipeline YAML: missing 'pipeline' key");
    }

    const { pipeline } = data;

    // Convert executors to nodes
    const nodes: Node[] = (pipeline.executors || []).map((executor) => {
      // Find the executor type from the catalog
      const executorType = executorTypes.find((et) => et.id === executor.type);

      // Separate pipeline_id from regular settings for sub-pipelines
      const { pipeline_id, ...regularSettings } = executor.settings || {};
      
      const nodeData: any = {
        label: executor.name,
        executor: executorType || {
          id: executor.type,
          name: executor.name,
          category: "unknown",
          color: "bg-gray-500",
          icon: null,
          description: executor.description || "",
        },
        config: {
          name: executor.name,
          description: executor.description || "",
          settings: regularSettings,
        },
      };

      // Handle sub-pipeline with pipeline reference
      if (executorType?.category === "pipeline" && pipeline_id) {
        nodeData.selectedPipelineId = pipeline_id;
        nodeData.config.selectedPipelineId = pipeline_id;
      }

      return {
        id: executor.id,
        type: executorType?.category === "pipeline" ? "subpipeline" : "executor",
        position: executor.position || { x: 0, y: 0 },
        data: nodeData,
      };
    });

    // Convert connections to edges
    const edges: Edge[] = [];
    const edgeMap = new Map<string, boolean>(); // Track processed edges
    
    (pipeline.edges || []).forEach((edgeDef, index) => {
      const from = edgeDef.from;
      const to = edgeDef.to;
      
      // Handle parallel edges: from -> [to1, to2, to3]
      if (typeof from === "string" && Array.isArray(to)) {
        to.forEach((target) => {
          const edgeKey = `${from}->${target}`;
          if (!edgeMap.has(edgeKey)) {
            edges.push({
              id: `${from}-${target}-${edges.length}`,
              source: from,
              target: target,
              type: "default",
              animated: true,
              markerEnd: { type: "arrowclosed" as any },
              style: { stroke: "hsl(var(--secondary))", strokeWidth: 2 },
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
              id: `${source}-${to}-${edges.length}`,
              source: source,
              target: to,
              type: "default",
              animated: true,
              markerEnd: { type: "arrowclosed" as any },
              style: { stroke: "hsl(var(--secondary))", strokeWidth: 2 },
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
            id: `${from}-${to}-${edges.length}`,
            source: from,
            target: to,
            type: "default",
            animated: true,
            markerEnd: { type: "arrowclosed" as any },
            style: { stroke: "hsl(var(--secondary))", strokeWidth: 2 },
          });
          edgeMap.set(edgeKey, true);
        }
      }
    });

    return {
      nodes,
      edges,
      pipelineName: pipeline.name || "Untitled Pipeline",
      pipelineDescription: pipeline.description || "",
    };
  } catch (error) {
    throw new Error(
      `Failed to parse YAML: ${error instanceof Error ? error.message : "Unknown error"}`
    );
  }
}

/**
 * Validate YAML syntax without converting
 */
export function validateYaml(yamlString: string): {
  isValid: boolean;
  error?: string;
} {
  try {
    yaml.load(yamlString);
    return { isValid: true };
  } catch (error) {
    return {
      isValid: false,
      error: error instanceof Error ? error.message : "Invalid YAML syntax",
    };
  }
}
