import { apiClient } from './apiClient';
import type {   
  ExecutorCatalogDefinition,
  ExecutorUIMetadata,
  ExecutorSetting
} from '@/types/components';

/**
 * Executors API
 * Functions to interact with executor endpoints
 */

/**
 * Get all available executors from the catalog
 */
export const getExecutors = async (): Promise<ExecutorCatalogDefinition[]> => {
  const response = await apiClient.get<ExecutorCatalogDefinition[]>('/executors');
  return response;
};

/**
 * Get a specific executor by ID
 */
export const getExecutorById = async (executorId: string): Promise<ExecutorCatalogDefinition> => {
  const response = await apiClient.get<ExecutorCatalogDefinition>(`/executors/${executorId}`);
  return response;
};

// /**
//  * Get executors by category
//  */
// export const getExecutorsByCategory = async (category: string): Promise<ExecutorType[]> => {
//   const response = await apiClient.get<ExecutorType[]>(`/executors/category/${category}`);
//   return response;
// };

// /**
//  * Get all executor categories
//  */
// export const getExecutorCategories = async (): Promise<string[]> => {
//   const response = await apiClient.get<string[]>('/executors/categories');
//   return response;
// };

// /**
//  * Search executors by query
//  */
// export const searchExecutors = async (query: string): Promise<ExecutorType[]> => {
//   const response = await apiClient.get<ExecutorType[]>('/executors/search', {
//     params: { q: query },
//   });
//   return response;
// };

// /**
//  * Validate executor configuration
//  */
// export const validateExecutorConfig = async (
//   executorId: string,
//   config: Record<string, any>
// ): Promise<{ valid: boolean; errors?: string[] }> => {
//   const response = await apiClient.post<{ valid: boolean; errors?: string[] }>(
//     `/executors/${executorId}/validate`,
//     config
//   );
//   return response;
// };
