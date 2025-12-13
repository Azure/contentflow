/**
 * API Type Definitions for ContentFlow Backend
 */

// ============================================================================
// Common Types
// ============================================================================

export interface ApiResponse<T> {
  data: T;
  message?: string;
  status: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  pageSize: number;
  totalPages: number;
}

// // ============================================================================
// // Executor Types
// // ============================================================================

// export interface ExecutorType {
//   id: string;
//   name: string;
//   category: string;
//   description: string;
//   color: string;
//   icon?: string;
//   parameters?: ExecutorParameter[];
//   inputSchema?: Record<string, any>;
//   outputSchema?: Record<string, any>;
// }

// export interface ExecutorParameter {
//   name: string;
//   type: string;
//   description: string;
//   required: boolean;
//   default?: any;
//   enum?: string[];
//   validation?: Record<string, any>;
// }

// export interface ExecutorCatalog {
//   executors: ExecutorType[];
//   categories: string[];
//   version: string;
//   updatedAt: string;
// }

// // ============================================================================
// // Pipeline Types
// // ============================================================================

// export interface SavePipelineRequest {
//   id?: string; // id of the pipeline (optional for creation)
//   name: string; // name of the pipeline
//   description?: string; // description of the pipeline
//   yaml: string; // updated YAML configuration
//   nodes?: any[]; // visual nodes for UI
//   edges?: any[]; // visual edges for UI
//   tags?: string[]; // updated tags
//   version?: string; // updated version
//   enabled?: boolean; // updated enabled status
//   retry_delay?: number; // updated retry delay in seconds
//   timeout?: number; // updated timeout in seconds
//   retries?: number; // updated number of retries
// }

// // export interface PipelineListQuery {
// //   page?: number;
// //   pageSize?: number;
// //   search?: string;
// //   tags?: string[];
// //   sortBy?: 'name' | 'createdAt' | 'updatedAt';
// //   sortOrder?: 'asc' | 'desc';
// // }

// export interface PipelineExecutionRequest {
//   pipelineId: string;
//   inputs?: Record<string, any>;
//   configuration?: Record<string, any>;
// }

// export interface PipelineExecutionResponse {
//   executionId: string;
//   status: 'pending' | 'running' | 'completed' | 'failed';
//   startedAt: string;
//   completedAt?: string;
//   outputs?: Record<string, any>;
//   error?: string;
// }

// ============================================================================
// Template Types (Backend API)
// ============================================================================

export interface PipelineTemplate {
  id: string;
  name: string;
  description: string;
  category: string;
  thumbnail?: string;
  yaml: string;
  nodes?: any[];
  edges?: any[];
  tags?: string[];
  usageCount?: number;
  createdAt: string;
  updatedAt: string;
  author?: string;
  difficulty?: 'beginner' | 'intermediate' | 'advanced';
}

export interface TemplateCategory {
  id: string;
  name: string;
  description: string;
  icon?: string;
  templateCount: number;
}

export interface TemplateListQuery {
  page?: number;
  pageSize?: number;
  category?: string;
  search?: string;
  tags?: string[];
  difficulty?: 'beginner' | 'intermediate' | 'advanced';
  sortBy?: 'name' | 'usageCount' | 'createdAt';
  sortOrder?: 'asc' | 'desc';
}

// ============================================================================
// Vault Types
// ============================================================================

export interface Vault {
  id: string;
  name: string;
  description?: string;
  type: 'azure-keyvault' | 'local' | 'aws-secrets' | 'gcp-secrets';
  configuration: VaultConfiguration;
  isDefault?: boolean;
  createdAt: string;
  updatedAt: string;
}

export interface VaultConfiguration {
  vaultUrl?: string;
  tenantId?: string;
  clientId?: string;
  region?: string;
  projectId?: string;
  [key: string]: any;
}

export interface CreateVaultRequest {
  name: string;
  description?: string;
  type: 'azure-keyvault' | 'local' | 'aws-secrets' | 'gcp-secrets';
  configuration: VaultConfiguration;
  isDefault?: boolean;
}

export interface UpdateVaultRequest {
  name?: string;
  description?: string;
  configuration?: VaultConfiguration;
  isDefault?: boolean;
}

export interface VaultSecret {
  name: string;
  value?: string;
  createdAt: string;
  updatedAt: string;
  version?: string;
}

export interface CreateSecretRequest {
  name: string;
  value: string;
}

export interface UpdateSecretRequest {
  value: string;
}

// ============================================================================
// Connector Types
// ============================================================================

export interface Connector {
  id: string;
  name: string;
  type: string;
  description: string;
  configuration: Record<string, any>;
  vaultId?: string;
  isActive: boolean;
  createdAt: string;
  updatedAt: string;
}

export interface CreateConnectorRequest {
  name: string;
  type: string;
  description?: string;
  configuration: Record<string, any>;
  vaultId?: string;
}

export interface UpdateConnectorRequest {
  name?: string;
  description?: string;
  configuration?: Record<string, any>;
  vaultId?: string;
  isActive?: boolean;
}

// ============================================================================
// System Types
// ============================================================================

export interface HealthCheck {
  status: 'healthy' | 'degraded' | 'unhealthy';
  version: string;
  timestamp: string;
  services: {
    database?: ServiceStatus;
    cache?: ServiceStatus;
    storage?: ServiceStatus;
  };
}

export interface ServiceStatus {
  status: 'up' | 'down';
  latency?: number;
  message?: string;
}

export interface SystemInfo {
  version: string;
  environment: string;
  features: string[];
  limits: {
    maxPipelineSize?: number;
    maxExecutorsPerPipeline?: number;
    [key: string]: any;
  };
}
