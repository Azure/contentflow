import { apiClient } from './apiClient';
import { ExecutorType, ExecutorCatalog, ApiResponse } from './apiTypes';

/**
 * Executors API
 * Functions to interact with executor endpoints
 */

/**
 * Get all available executors from the catalog
 */
export const getExecutors = async (): Promise<ExecutorType[]> => {
  const response = await apiClient.get<ApiResponse<ExecutorCatalog>>('/executors');
  return response.data.executors;
};

/**
 * Get executor catalog with full metadata
 */
export const getExecutorCatalog = async (): Promise<ExecutorCatalog> => {
  const response = await apiClient.get<ApiResponse<ExecutorCatalog>>('/executors/catalog');
  return response.data;
};

/**
 * Get a specific executor by ID
 */
export const getExecutorById = async (executorId: string): Promise<ExecutorType> => {
  const response = await apiClient.get<ApiResponse<ExecutorType>>(`/executors/${executorId}`);
  return response.data;
};

/**
 * Get executors by category
 */
export const getExecutorsByCategory = async (category: string): Promise<ExecutorType[]> => {
  const response = await apiClient.get<ApiResponse<ExecutorType[]>>(`/executors/category/${category}`);
  return response.data;
};

/**
 * Get all executor categories
 */
export const getExecutorCategories = async (): Promise<string[]> => {
  const response = await apiClient.get<ApiResponse<string[]>>('/executors/categories');
  return response.data;
};

/**
 * Search executors by query
 */
export const searchExecutors = async (query: string): Promise<ExecutorType[]> => {
  const response = await apiClient.get<ApiResponse<ExecutorType[]>>('/executors/search', {
    params: { q: query },
  });
  return response.data;
};

/**
 * Validate executor configuration
 */
export const validateExecutorConfig = async (
  executorId: string,
  config: Record<string, any>
): Promise<{ valid: boolean; errors?: string[] }> => {
  const response = await apiClient.post<ApiResponse<{ valid: boolean; errors?: string[] }>>(
    `/executors/${executorId}/validate`,
    config
  );
  return response.data;
};
