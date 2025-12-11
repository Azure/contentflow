import { apiClient } from './apiClient';
import {
  Vault,
  CreateVaultRequest,
  UpdateVaultRequest,
  VaultSecret,
  CreateSecretRequest,
  UpdateSecretRequest,
  ApiResponse,
} from './apiTypes';

/**
 * Vaults API
 * Functions to interact with vault/secrets management endpoints
 */

/**
 * Get all vaults
 */
export const getVaults = async (): Promise<Vault[]> => {
  const response = await apiClient.get<ApiResponse<Vault[]>>('/vaults');
  return response.data;
};

/**
 * Get a specific vault by ID
 */
export const getVaultById = async (vaultId: string): Promise<Vault> => {
  const response = await apiClient.get<ApiResponse<Vault>>(`/vaults/${vaultId}`);
  return response.data;
};

/**
 * Create a new vault
 */
export const createVault = async (vault: CreateVaultRequest): Promise<Vault> => {
  const response = await apiClient.post<ApiResponse<Vault>>('/vaults', vault);
  return response.data;
};

/**
 * Update an existing vault
 */
export const updateVault = async (vaultId: string, updates: UpdateVaultRequest): Promise<Vault> => {
  const response = await apiClient.put<ApiResponse<Vault>>(`/vaults/${vaultId}`, updates);
  return response.data;
};

/**
 * Delete a vault
 */
export const deleteVault = async (vaultId: string): Promise<void> => {
  await apiClient.delete(`/vaults/${vaultId}`);
};

/**
 * Get the default vault
 */
export const getDefaultVault = async (): Promise<Vault> => {
  const response = await apiClient.get<ApiResponse<Vault>>('/vaults/default');
  return response.data;
};

/**
 * Set a vault as default
 */
export const setDefaultVault = async (vaultId: string): Promise<Vault> => {
  const response = await apiClient.post<ApiResponse<Vault>>(`/vaults/${vaultId}/set-default`);
  return response.data;
};

/**
 * Test vault connection
 */
export const testVaultConnection = async (vaultId: string): Promise<{
  success: boolean;
  message?: string;
  latency?: number;
}> => {
  const response = await apiClient.post<
    ApiResponse<{ success: boolean; message?: string; latency?: number }>
  >(`/vaults/${vaultId}/test`);
  return response.data;
};

// ============================================================================
// Secrets Management
// ============================================================================

/**
 * Get all secrets from a vault (returns secret names only, not values)
 */
export const getVaultSecrets = async (vaultId: string): Promise<VaultSecret[]> => {
  const response = await apiClient.get<ApiResponse<VaultSecret[]>>(`/vaults/${vaultId}/secrets`);
  return response.data;
};

/**
 * Get a specific secret from a vault
 */
export const getVaultSecret = async (vaultId: string, secretName: string): Promise<VaultSecret> => {
  const response = await apiClient.get<ApiResponse<VaultSecret>>(
    `/vaults/${vaultId}/secrets/${secretName}`
  );
  return response.data;
};

/**
 * Create a new secret in a vault
 */
export const createVaultSecret = async (
  vaultId: string,
  secret: CreateSecretRequest
): Promise<VaultSecret> => {
  const response = await apiClient.post<ApiResponse<VaultSecret>>(
    `/vaults/${vaultId}/secrets`,
    secret
  );
  return response.data;
};

/**
 * Update a secret in a vault
 */
export const updateVaultSecret = async (
  vaultId: string,
  secretName: string,
  updates: UpdateSecretRequest
): Promise<VaultSecret> => {
  const response = await apiClient.put<ApiResponse<VaultSecret>>(
    `/vaults/${vaultId}/secrets/${secretName}`,
    updates
  );
  return response.data;
};

/**
 * Delete a secret from a vault
 */
export const deleteVaultSecret = async (vaultId: string, secretName: string): Promise<void> => {
  await apiClient.delete(`/vaults/${vaultId}/secrets/${secretName}`);
};

/**
 * Check if a secret exists in a vault
 */
export const checkSecretExists = async (
  vaultId: string,
  secretName: string
): Promise<{ exists: boolean }> => {
  const response = await apiClient.get<ApiResponse<{ exists: boolean }>>(
    `/vaults/${vaultId}/secrets/${secretName}/exists`
  );
  return response.data;
};

/**
 * Rotate/regenerate a secret value
 */
export const rotateVaultSecret = async (vaultId: string, secretName: string): Promise<VaultSecret> => {
  const response = await apiClient.post<ApiResponse<VaultSecret>>(
    `/vaults/${vaultId}/secrets/${secretName}/rotate`
  );
  return response.data;
};

/**
 * Bulk create secrets
 */
export const bulkCreateSecrets = async (
  vaultId: string,
  secrets: CreateSecretRequest[]
): Promise<VaultSecret[]> => {
  const response = await apiClient.post<ApiResponse<VaultSecret[]>>(
    `/vaults/${vaultId}/secrets/bulk`,
    { secrets }
  );
  return response.data;
};

/**
 * Export vault configuration (without secret values)
 */
export const exportVaultConfig = async (vaultId: string): Promise<Blob> => {
  return await apiClient.get<Blob>(`/vaults/${vaultId}/export`, {
    responseType: 'blob',
  });
};

/**
 * Import vault configuration
 */
export const importVaultConfig = async (file: File): Promise<Vault> => {
  const formData = new FormData();
  formData.append('file', file);

  const response = await apiClient.post<ApiResponse<Vault>>('/vaults/import', formData);
  return response.data as Vault;
};
