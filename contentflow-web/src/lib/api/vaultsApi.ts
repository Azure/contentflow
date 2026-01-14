import { apiClient } from './apiClient';

import type {   
  Vault,
  CreateVaultRequest,
  UpdateVaultRequest,
  VaultExecution,
  VaultCrawlCheckpoint
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

/**
 * Get vault executions for a specific vault
 */
export const getVaultExecutions = async (vaultId: string, dateRange?: { start_date?: string; end_date?: string }): Promise<VaultExecution[]> => {
  const params = new URLSearchParams();
  if (dateRange?.start_date) {
    params.append('start_date', dateRange.start_date);
  }
  if (dateRange?.end_date) {
    params.append('end_date', dateRange.end_date);
  }
  
  const queryString = params.toString();
  const url = `/vaults/executions/${vaultId}${queryString ? `?${queryString}` : ''}`;
  const response = await apiClient.get<VaultExecution[]>(url);
  return response;
};

/**
 * Get vault crawl checkpoints for a specific vault
 */
export const getVaultCrawlCheckpoints = async (vaultId: string): Promise<VaultCrawlCheckpoint[]> => {
  const response = await apiClient.get<VaultCrawlCheckpoint[]>(`/vaults/crawl-checkpoints/${vaultId}`);
  return response;
};


