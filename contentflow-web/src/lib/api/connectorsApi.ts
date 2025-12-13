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
  const response = await apiClient.get<Connector[]>('/connectors');
  return response;
};

/**
 * Get a specific connector by ID
 */
export const getConnectorById = async (connectorId: string): Promise<Connector> => {
  const response = await apiClient.get<Connector>(`/connectors/${connectorId}`);
  return response;
};

/**
 * Get connectors by type
 */
export const getConnectorsByType = async (type: string): Promise<Connector[]> => {
  const response = await apiClient.get<Connector[]>(`/connectors/type/${type}`);
  return response;
};

/**
 * Create a new connector
 */
export const createConnector = async (connector: CreateConnectorRequest): Promise<Connector> => {
  const response = await apiClient.post<Connector>('/connectors', connector);
  return response;
};

/**
 * Update an existing connector
 */
export const updateConnector = async (
  connectorId: string,
  updates: UpdateConnectorRequest
): Promise<Connector> => {
  const response = await apiClient.put<Connector>(`/connectors/${connectorId}`, updates);
  return response;
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
  const response = await apiClient.post<{ success: boolean; message?: string; latency?: number }>(`/connectors/${connectorId}/test`);
  return response;
};

/**
 * Activate a connector
 */
export const activateConnector = async (connectorId: string): Promise<Connector> => {
  const response = await apiClient.post<Connector>(`/connectors/${connectorId}/activate`);
  return response;
};

/**
 * Deactivate a connector
 */
export const deactivateConnector = async (connectorId: string): Promise<Connector> => {
  const response = await apiClient.post<Connector>(`/connectors/${connectorId}/deactivate`);
  return response;
};

/**
 * Get available connector types
 */
export const getConnectorTypes = async (): Promise<string[]> => {
  const response = await apiClient.get<string[]>('/connectors/types');
  return response;
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
