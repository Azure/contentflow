/**
 * ContentFlow API Client
 * Centralized exports for all API modules
 */

// API Client and utilities
export { apiClient, createApiClient, handleApiError, buildQueryParams } from './apiClient';
export type { ApiConfig, ApiError } from './apiClient';

// Type definitions
export * from './apiTypes';

// Executors API
export * from './executorsApi';

// Pipelines API
export * from './pipelinesApi';

// Templates API
export * from './templatesApi';

// Vaults API
export * from './vaultsApi';

// Connectors API
export * from './connectorsApi';

// System/Health API
export * from './systemApi';

// React Hooks for API
export * from './useApi';

/**
 * Example usage:
 * 
 * import { 
 *   getExecutors, 
 *   getPipelines, 
 *   createPipeline,
 *   getTemplates,
 *   getVaults
 * } from '@/lib/api';
 * 
 * // Fetch executors
 * const executors = await getExecutors();
 * 
 * // Create a pipeline
 * const newPipeline = await createPipeline({
 *   name: "My Pipeline",
 *   description: "Processing pipeline",
 *   yaml: "..."
 * });
 * 
 * // Get templates
 * const templates = await getTemplates({ category: 'data-processing' });
 */
