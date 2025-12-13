import { apiClient, buildQueryParams } from './apiClient';
import {
  PipelineTemplate,
  TemplateCategory,
  TemplateListQuery,
  ApiResponse,
  PaginatedResponse,
} from './apiTypes';

/**
 * Templates API
 * Functions to interact with pipeline template endpoints
 */

/**
 * Get all pipeline templates with optional filters and pagination
 */
export const getTemplates = async (query?: TemplateListQuery): Promise<PaginatedResponse<PipelineTemplate>> => {
  const response = await apiClient.get<PaginatedResponse<PipelineTemplate>>(
    `/templates`,
    { params: query }
  );
  return response as PaginatedResponse<PipelineTemplate>;
};

/**
 * Get a specific template by ID
 */
export const getTemplateById = async (templateId: string): Promise<PipelineTemplate> => {
  const response = await apiClient.get<PipelineTemplate>(`/templates/${templateId}`);
  return response as PipelineTemplate;
};

/**
 * Get templates by category
 */
export const getTemplatesByCategory = async (
  category: string,
  page?: number,
  pageSize?: number
): Promise<PaginatedResponse<PipelineTemplate>> => {
  const response = await apiClient.get<PaginatedResponse<PipelineTemplate>>(
    `/templates/category/${category}`,
    { params: { page, pageSize } }
  );
  return response as PaginatedResponse<PipelineTemplate>;
};

/**
 * Get all template categories
 */
export const getTemplateCategories = async (): Promise<TemplateCategory[]> => {
  const response = await apiClient.get<TemplateCategory[]>('/templates/categories');
  return response as TemplateCategory[];
};

/**
 * Search templates
 */
export const searchTemplates = async (
  query: string,
  page?: number,
  pageSize?: number
): Promise<PaginatedResponse<PipelineTemplate>> => {
  const response = await apiClient.get<PaginatedResponse<PipelineTemplate>>(
    `/templates/search`,
    { params: { q: query, page, pageSize } }
  );
  return response as PaginatedResponse<PipelineTemplate>;
};

/**
 * Get popular/featured templates
 */
export const getFeaturedTemplates = async (limit?: number): Promise<PipelineTemplate[]> => {
  const response = await apiClient.get<PipelineTemplate[]>(
    `/templates/featured`,
    { params: { limit } }
  );
  return response as PipelineTemplate[];
};

/**
 * Get recent templates
 */
export const getRecentTemplates = async (limit?: number): Promise<PipelineTemplate[]> => {
  const response = await apiClient.get<PipelineTemplate[]>(
    `/templates/recent`,
    { params: { limit } }
  );
  return response as PipelineTemplate[];
};

/**
 * Create a pipeline from a template
 */
export const createPipelineFromTemplate = async (
  templateId: string,
  name?: string,
  description?: string
): Promise<{ pipelineId: string; pipeline: any }> => {
  const response = await apiClient.post<{ pipelineId: string; pipeline: any }>(
    `/templates/${templateId}/create-pipeline`,
    { name, description }
  );
  return response as { pipelineId: string; pipeline: any };
};

/**
 * Increment template usage count
 */
export const incrementTemplateUsage = async (templateId: string): Promise<void> => {
  await apiClient.post(`/templates/${templateId}/usage`);
};

/**
 * Get template YAML
 */
export const getTemplateYaml = async (templateId: string): Promise<string> => {
  const response = await apiClient.get<{ yaml: string }>(`/templates/${templateId}/yaml`);
  return (response as { yaml: string }).yaml;
};

/**
 * Create a new template (admin/authorized users)
 */
export const createTemplate = async (template: {
  name: string;
  description: string;
  category: string;
  yaml: string;
  tags?: string[];
  difficulty?: 'beginner' | 'intermediate' | 'advanced';
  thumbnail?: string;
}): Promise<PipelineTemplate> => {
  const response = await apiClient.post<PipelineTemplate>('/templates', template);
  return response as PipelineTemplate;
};

/**
 * Update a template (admin/authorized users)
 */
export const updateTemplate = async (
  templateId: string,
  updates: {
    name?: string;
    description?: string;
    category?: string;
    yaml?: string;
    tags?: string[];
    difficulty?: 'beginner' | 'intermediate' | 'advanced';
    thumbnail?: string;
  }
): Promise<PipelineTemplate> => {
  const response = await apiClient.put<PipelineTemplate>(
    `/templates/${templateId}`,
    updates
  );
  return response as PipelineTemplate;
};

/**
 * Delete a template (admin/authorized users)
 */
export const deleteTemplate = async (templateId: string): Promise<void> => {
  await apiClient.delete(`/templates/${templateId}`);
};

/**
 * Get template tags
 */
export const getTemplateTags = async (): Promise<string[]> => {
  const response = await apiClient.get<string[]>('/templates/tags');
  return response as string[];
};

/**
 * Export template as YAML file
 */
export const exportTemplateYaml = async (templateId: string): Promise<Blob> => {
  return await apiClient.get<Blob>(`/templates/${templateId}/export`, {
    responseType: 'blob',
  });
};
