import { apiClient } from './apiClient';
import { HealthCheck, SystemInfo, ApiResponse } from './apiTypes';

/**
 * System API
 * Functions to interact with system health and information endpoints
 */

/**
 * Get system health status
 */
export const getHealthCheck = async (): Promise<HealthCheck> => {
  const response = await apiClient.get<ApiResponse<HealthCheck>>('/health');
  return response.data;
};

/**
 * Get detailed system health with all services
 */
export const getDetailedHealth = async (): Promise<HealthCheck> => {
  const response = await apiClient.get<ApiResponse<HealthCheck>>('/health/detailed');
  return response.data;
};

/**
 * Get system information
 */
export const getSystemInfo = async (): Promise<SystemInfo> => {
  const response = await apiClient.get<ApiResponse<SystemInfo>>('/system/info');
  return response.data;
};

/**
 * Get API version
 */
export const getApiVersion = async (): Promise<string> => {
  const response = await apiClient.get<ApiResponse<{ version: string }>>('/system/version');
  return response.data.version;
};

/**
 * Ping the API (simple connectivity test)
 */
export const ping = async (): Promise<{ message: string; timestamp: string }> => {
  const response = await apiClient.get<ApiResponse<{ message: string; timestamp: string }>>('/ping');
  return response.data;
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
  const response = await apiClient.get<
    ApiResponse<{
      cpu?: number;
      memory?: number;
      disk?: number;
      uptime?: number;
      requestCount?: number;
    }>
  >('/system/metrics');
  return response.data;
};
