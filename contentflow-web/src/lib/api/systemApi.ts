import { apiClient } from './apiClient';
import { HealthCheck, SystemInfo, ApiResponse } from './apiTypes';

/**
 * System API
 * Functions to interact with system health and information endpoints
 */

export const getApiClientConfig = () => {
  return apiClient.getConfig();
}

/**
 * Get system health status
 */
export const getHealthCheck = async (): Promise<HealthCheck> => {
  const response = await apiClient.get<HealthCheck>('/health');
  return response;
};

/**
 * Get detailed system health with all services
 */
export const getDetailedHealth = async (): Promise<HealthCheck> => {
  const response = await apiClient.get<HealthCheck>('/health/detailed');
  return response;
};

/**
 * Get system information
 */
export const getSystemInfo = async (): Promise<SystemInfo> => {
  const response = await apiClient.get<SystemInfo>('/system/info');
  return response;
};

/**
 * Get API version
 */
export const getApiVersion = async (): Promise<string> => {
  const response = await apiClient.get<{ version: string }>('/system/version');
  return response.version;
};

/**
 * Ping the API (simple connectivity test)
 */
export const ping = async (): Promise<{ message: string; timestamp: string }> => {
  const response = await apiClient.get<{ message: string; timestamp: string }>('/ping');
  return response;
};

/**
 * Get system metrics (if available)
 */
export const getSystemMetrics = async (): Promise<{
  cpu?: number;
  memory?: number;
  disk?: number;
  uptime?: number;
  requestCount?: number;
}> => {
  const response = await apiClient.get<{
    cpu?: number;
    memory?: number;
    disk?: number;
    uptime?: number;
    requestCount?: number;
  }>('/system/metrics');
  return response;
};
