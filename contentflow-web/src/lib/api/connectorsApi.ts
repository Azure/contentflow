import { apiClient } from './apiClient';
import {
  Connector,
  CreateConnectorRequest,
  UpdateConnectorRequest,
  ApiResponse,
} from './apiTypes';

/**
 * Connectors API
 * Functions to interact with connector configuration endpoints
 */

/**
 * Get all connectors
 */
export const getConnectors = async (): Promise<Connector[]> => {
  const response = await apiClient.get<ApiResponse<Connector[]>>('/connectors');
  return response.data;
};

/**
 * Get a specific connector by ID
 */
export const getConnectorById = async (connectorId: string): Promise<Connector> => {
  const response = await apiClient.get<ApiResponse<Connector>>(`/connectors/${connectorId}`);
  return response.data;
};

/**
 * Get connectors by type
 */
export const getConnectorsByType = async (type: string): Promise<Connector[]> => {
  const response = await apiClient.get<ApiResponse<Connector[]>>(`/connectors/type/${type}`);
  return response.data;
};

/**
 * Create a new connector
 */
export const createConnector = async (connector: CreateConnectorRequest): Promise<Connector> => {
  const response = await apiClient.post<ApiResponse<Connector>>('/connectors', connector);
  return response.data;
};

/**
 * Update an existing connector
 */
export const updateConnector = async (
  connectorId: string,
  updates: UpdateConnectorRequest
): Promise<Connector> => {
  const response = await apiClient.put<ApiResponse<Connector>>(`/connectors/${connectorId}`, updates);
  return response.data;
};

/**
 * Delete a connector
 */
export const deleteConnector = async (connectorId: string): Promise<void> => {
  await apiClient.delete(`/connectors/${connectorId}`);
};

/**
 * Test connector connection
 */
export const testConnectorConnection = async (connectorId: string): Promise<{
  success: boolean;
  message?: string;
  latency?: number;
}> => {
  const response = await apiClient.post<
    ApiResponse<{ success: boolean; message?: string; latency?: number }>
  >(`/connectors/${connectorId}/test`);
  return response.data;
};

/**
 * Activate a connector
 */
export const activateConnector = async (connectorId: string): Promise<Connector> => {
  const response = await apiClient.post<ApiResponse<Connector>>(`/connectors/${connectorId}/activate`);
  return response.data;
};

/**
 * Deactivate a connector
 */
export const deactivateConnector = async (connectorId: string): Promise<Connector> => {
  const response = await apiClient.post<ApiResponse<Connector>>(`/connectors/${connectorId}/deactivate`);
  return response.data;
};

/**
 * Get available connector types
 */
export const getConnectorTypes = async (): Promise<string[]> => {
  const response = await apiClient.get<ApiResponse<string[]>>('/connectors/types');
  return response.data;
};

/**
 * Validate connector configuration
 */
export const validateConnectorConfig = async (
  type: string,
  config: Record<string, any>
): Promise<{ valid: boolean; errors?: string[] }> => {
  const response = await apiClient.post<ApiResponse<{ valid: boolean; errors?: string[] }>>(
    '/connectors/validate',
    { type, configuration: config }
  );
  return response.data;
};
