import { apiClient } from './apiClient';

import type {   
  Vault,
  CreateVaultRequest,
  UpdateVaultRequest
} from '@/types/components';

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
