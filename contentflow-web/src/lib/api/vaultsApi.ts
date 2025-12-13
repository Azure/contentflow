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
  const response = await apiClient.get<Vault[]>('/vaults');
  return response;
};

/**
 * Get a specific vault by ID
 */
export const getVaultById = async (vaultId: string): Promise<Vault> => {
  const response = await apiClient.get<Vault>(`/vaults/${vaultId}`);
  return response;
};

/**
 * Create a new vault
 */
export const createVault = async (vault: CreateVaultRequest): Promise<Vault> => {
  const response = await apiClient.post<Vault>('/vaults', vault);
  return response;
};

/**
 * Update an existing vault
 */
export const updateVault = async (vaultId: string, updates: UpdateVaultRequest): Promise<Vault> => {
  const response = await apiClient.put<Vault>(`/vaults/${vaultId}`, updates);
  return response;
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
  const response = await apiClient.get<Vault>('/vaults/default');
  return response;
};

/**
 * Set a vault as default
 */
export const setDefaultVault = async (vaultId: string): Promise<Vault> => {
  const response = await apiClient.post<Vault>(`/vaults/${vaultId}/set-default`);
  return response;
};

/**
 * Test vault connection
 */
export const testVaultConnection = async (vaultId: string): Promise<{
  success: boolean;
  message?: string;
  latency?: number;
}> => {
  const response = await apiClient.post<{ success: boolean; message?: string; latency?: number }>(`/vaults/${vaultId}/test`);
  return response;
};

// ============================================================================
// Secrets Management
// ============================================================================

/**
 * Get all secrets from a vault (returns secret names only, not values)
 */
export const getVaultSecrets = async (vaultId: string): Promise<VaultSecret[]> => {
  const response = await apiClient.get<VaultSecret[]>(`/vaults/${vaultId}/secrets`);
  return response;
};

/**
 * Get a specific secret from a vault
 */
export const getVaultSecret = async (vaultId: string, secretName: string): Promise<VaultSecret> => {
  const response = await apiClient.get<VaultSecret>(
    `/vaults/${vaultId}/secrets/${secretName}`
  );
  return response;
};

/**
 * Create a new secret in a vault
 */
export const createVaultSecret = async (
  vaultId: string,
  secret: CreateSecretRequest
): Promise<VaultSecret> => {
  const response = await apiClient.post<VaultSecret>(
    `/vaults/${vaultId}/secrets`,
    secret
  );
  return response;
};

/**
 * Update a secret in a vault
 */
export const updateVaultSecret = async (
  vaultId: string,
  secretName: string,
  updates: UpdateSecretRequest
): Promise<VaultSecret> => {
  const response = await apiClient.put<VaultSecret>(
    `/vaults/${vaultId}/secrets/${secretName}`,
    updates
  );
  return response;
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
  const response = await apiClient.get<{ exists: boolean }>(
    `/vaults/${vaultId}/secrets/${secretName}/exists`
  );
  return response;
};

/**
 * Rotate/regenerate a secret value
 */
export const rotateVaultSecret = async (vaultId: string, secretName: string): Promise<VaultSecret> => {
  const response = await apiClient.post<VaultSecret>(
    `/vaults/${vaultId}/secrets/${secretName}/rotate`
  );
  return response;
};

/**
 * Bulk create secrets
 */
export const bulkCreateSecrets = async (
  vaultId: string,
  secrets: CreateSecretRequest[]
): Promise<VaultSecret[]> => {
  const response = await apiClient.post<VaultSecret[]>(
    `/vaults/${vaultId}/secrets/bulk`,
    { secrets }
  );
  return response;
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

  const response = await apiClient.post<Vault>('/vaults/import', formData);
  return response as Vault;
};
