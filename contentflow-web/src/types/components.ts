

// ============================================================================
// Executor Types (for component display and interaction)
// ============================================================================

// export interface ExecutorType {
//   id: string;
//   type: string;
//   name: string;
//   icon: React.ReactNode;
//   color: string;
//   category: "extract" | "transform" | "analyze" | "pipeline" | "media" | "enrichment" | "input" | "output";
//   description?: string;
// }


// ============================================================================
// Executor Types
// ============================================================================

export interface ExecutorCatalogDefinition {
  id: string;
  name: string;
  type: string;
  category: string;
  description?: string;
  version?: string;
  tags?: string[];
  settings_schema?: Record<string, ExecutorSetting>;
  ui_metadata?: ExecutorUIMetadata;
}

export interface ExecutorUIMetadata {
  description_short?: string;
  description_long?: string;
  icon?: string;
}

export interface ExecutorSetting {
  type: string;
  title: string;
  description?: string;
  placeholder?: string;
  required?: boolean;
  default?: any;
  ui_component?: string;
  options?: string[];
  min?: number;
  max?: number;
  increment?: number;
}

// ============================================================================
// Pipeline Types
// ============================================================================

export interface Pipeline {
  id: string;
  name: string;
  description: string;
  yaml: string;
  nodes?: any[];
  edges?: any[];
  created_at: string;
  updated_at: string;
  created_by?: string;
  tags?: string[];
  version?: string;
  enabled?: boolean; // whether the pipeline is enabled
  retry_delay?: number; // delay between retries in seconds
  timeout?: number; // timeout for pipeline execution in seconds
  retries?: number; // number of retries on failure
}

export interface SavePipelineRequest {
  id?: string; // id of the pipeline (optional for creation)
  name: string; // name of the pipeline
  description?: string; // description of the pipeline
  yaml: string; // updated YAML configuration
  nodes?: any[]; // visual nodes for UI
  edges?: any[]; // visual edges for UI
  tags?: string[]; // updated tags
  version?: string; // updated version
  enabled?: boolean; // updated enabled status
  retry_delay?: number; // updated retry delay in seconds
  timeout?: number; // updated timeout in seconds
  retries?: number; // updated number of retries
}


export interface PipelineExecutionRequest {
  pipelineId: string;
  inputs?: Record<string, any>;
  configuration?: Record<string, any>;
}

export interface PipelineExecutionResponse {
  executionId: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  startedAt: string;
  completedAt?: string;
  outputs?: Record<string, any>;
  error?: string;
}

// ============================================================================
// Template Types (for local component use)
// ============================================================================

export interface PipelineTemplate {
  id: string;
  name: string;
  description: string;
  category: "extraction" | "analysis" | "knowledge" | "compliance" | "automation";
  steps: number;
  estimatedTime: string;
  nodes: TemplateNode[];
  edges: TemplateEdge[];
  useCases: string[];
  features: string[];
}

export interface TemplateNode {
  id: string;
  type: string;
  position: { x: number; y: number };
  data: {
    label: string;
    executor: {
      id: string;
      type: string;
      name: string;
      color: string;
      category: string;
    };
    config: Record<string, any>;
    selectedPipelineId?: string;
    savedPipelines?: Pipeline[];
  };
}

export interface TemplateEdge {
  id: string;
  source: string;
  target: string;
  type?: string;
  animated?: boolean;
}
