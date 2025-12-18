

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

export interface PipelineExecution {
  id: string;
  pipeline_id: string;
  pipeline_name: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';
  inputs?: Record<string, any>;
  configuration?: Record<string, any>;
  outputs?: Record<string, any>;
  started_at?: string;
  completed_at?: string;
  duration_seconds?: number;
  error?: string;
  executor_outputs?: Record<string, ExecutorOutput>;
  events?: PipelineExecutionEvent[];
  created_by?: string;
}

export interface ExecutorOutput {
  executor_id: string;
  timestamp: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'skipped';
  data?: any;
  error?: any;
  duration_ms?: number;
}

export interface PipelineExecutionEvent {
  event_type: string;
  executor_id?: string;
  timestamp: string;
  data?: any;
  additional_info?: any;
  error?: any;
  status?: string;
}


// ============================================================================
// Vault Types
// ============================================================================

export interface Vault {
  id: string;
  name: string;
  description?: string;
  pipeline_id: string;
  pipeline_name?: string;
  tags: string[];
  storage_config?: VaultStorageConfig;
  enabled?: boolean;
  created_by?: string;
  created_at: string;
  updated_at: string;
}

export interface VaultStorageConfig {
  account_name: string;
  container_name: string;
  credential_type: string;
  credential_key?: string;
}

export interface CreateVaultRequest {
  name: string;
  description?: string;
  pipeline_id: string;
  tags?: string[];
  storage_config?: VaultStorageConfig;
}

export interface UpdateVaultRequest {
  name?: string;
  description?: string;
  tags?: string[];
  enabled?: boolean;
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
  yaml: string;
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
