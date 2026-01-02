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

// ============================================================================
// System Types
// ============================================================================

export interface HealthCheck {
  status: 'connected' | 'degraded' | 'error';
  version: string;
  timestamp: string;
  services: {
    app_config?: ServiceStatus;
    cosmos_db?: ServiceStatus;
    blob_storage?: ServiceStatus;
    storage_queue?: ServiceStatus;
    worker?: ServiceStatus;
  };
}

export interface ServiceStatus {
  name: string;
  status: 'connected' | 'error';
  response_time_ms?: number;
  message?: string;
  error?: string;
  details?: Record<string, any>;
  last_checked?: string;
  endpoint?: string;
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
