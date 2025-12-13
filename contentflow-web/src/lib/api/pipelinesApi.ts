import { apiClient, buildQueryParams } from './apiClient';
import {
  PaginatedResponse,
} from './apiTypes';
import type {   
  Pipeline,
  SavePipelineRequest,
  PipelineExecutionRequest,
  PipelineExecutionResponse, } from '@/types/components';

/**
 * Pipelines API
 * Functions to interact with pipeline endpoints
 */

/**
 * Get all pipelines with optional filters and pagination
 */
export const getPipelines = async (): Promise<Pipeline[]> => {
  const response = await apiClient.get<Pipeline[]>(
    `/pipelines`
  );
  return response;
};

/**
 * Get a specific pipeline by ID
 */
export const getPipelineById = async (pipelineId: string): Promise<Pipeline> => {
  const response = await apiClient.get<Pipeline>(`/pipelines/${pipelineId}`);
  return response;
};

/**
 * Save a pipeline, either creating a new one or updating an existing one
 */
export const savePipeline = async (pipeline: SavePipelineRequest): Promise<Pipeline> => {
  const response = await apiClient.post<Pipeline>('/pipelines', pipeline);
  return response;
};

/**
 * Delete a pipeline
 */
export const deletePipeline = async (pipelineId: string): Promise<void> => {
  await apiClient.delete(`/pipelines/${pipelineId}`);
};

/**
 * Validate pipeline yaml configuration
 */
export const validatePipeline = async (yaml: string): Promise<{
  valid: boolean;
  errors?: string[];
  warnings?: string[];
}> => {
  const response = await apiClient.post<
    { valid: boolean; errors?: string[]; warnings?: string[] }
  >('/pipelines/validate', { yaml });
  return response;
};

/**
 * Execute a pipeline
 */
export const executePipeline = async (
  request: PipelineExecutionRequest
): Promise<PipelineExecutionResponse> => {
  const response = await apiClient.post<PipelineExecutionResponse>(
    '/pipelines/execute',
    request
  );
  return response;
};

/**
 * Get pipeline execution status
 */
export const getExecutionStatus = async (executionId: string): Promise<PipelineExecutionResponse> => {
  const response = await apiClient.get<PipelineExecutionResponse>(
    `/pipelines/executions/${executionId}`
  );
  return response;
};

/**
 * Cancel a running pipeline execution
 */
export const cancelExecution = async (executionId: string): Promise<void> => {
  await apiClient.post(`/pipelines/executions/${executionId}/cancel`);
};

/**
 * Get pipeline execution history
 */
export const getExecutionHistory = async (
  pipelineId: string,
  page?: number,
  pageSize?: number
): Promise<PaginatedResponse<PipelineExecutionResponse>> => {
  const response = await apiClient.get<PaginatedResponse<PipelineExecutionResponse>>(
    `/pipelines/${pipelineId}/executions`,
    { params: { page, pageSize } }
  );
  return response;
};

/**
 * Duplicate/clone a pipeline
 */
export const duplicatePipeline = async (
  pipelineId: string,
  newName?: string
): Promise<Pipeline> => {
  const response = await apiClient.post<Pipeline>(`/pipelines/${pipelineId}/duplicate`, {
    name: newName,
  });
  return response;
};

/**
 * Export pipeline as YAML file
 */
export const exportPipelineYaml = async (pipelineId: string): Promise<Blob> => {
  return await apiClient.get<Blob>(`/pipelines/${pipelineId}/export`, {
    responseType: 'blob',
  });
};

/**
 * Import pipeline from YAML file
 */
export const importPipelineYaml = async (
  file: File,
  name?: string,
  description?: string
): Promise<Pipeline> => {
  const formData = new FormData();
  formData.append('file', file);
  if (name) formData.append('name', name);
  if (description) formData.append('description', description);

  const response = await apiClient.post<Pipeline>('/pipelines/import', formData);
  return response;
};

/**
 * Get pipeline tags
 */
export const getPipelineTags = async (): Promise<string[]> => {
  const response = await apiClient.get<string[]>('/pipelines/tags');
  return response;
};

/**
 * Search pipelines
 */
export const searchPipelines = async (
  query: string,
  page?: number,
  pageSize?: number
): Promise<PaginatedResponse<Pipeline>> => {
  const response = await apiClient.get<PaginatedResponse<Pipeline>>(
    `/pipelines/search`,
    { params: { q: query, page, pageSize } }
  );
  return response;
};
