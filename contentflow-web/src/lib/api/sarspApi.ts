import { apiClient } from "./apiClient";

export interface SarspStartValidationRequest {
  pipeline_id?: string;
  pipeline_name?: string;
  configuration?: Record<string, unknown>;
}

export interface SarspStartValidationResponse {
  case_id: string;
  execution_id: string;
  status: string;
  message: string;
}

export interface SarspCheckResult {
  name?: string;
  result?: string;
  detail?: string;
  [key: string]: unknown;
}

export interface SarspFinding {
  document?: string;
  status?: string;
  finding?: string;
  guidance?: string;
  [key: string]: unknown;
}

export interface SarspExecutionStatusResponse {
  case_id: string;
  execution_id: string;
  status: string;
  platform_status: string;
  message: string;
  recommendation?: string | null;
  confidence?: number | null;
  completed_at?: string | null;
  checks?: SarspCheckResult[];
  missing_documents?: string[];
  findings?: SarspFinding[];
  results_available: boolean;
  report?: Record<string, unknown> | null;
}

export const startSarspCaseValidation = async (
  caseId: string,
  payload?: SarspStartValidationRequest,
): Promise<SarspStartValidationResponse> => {
  return apiClient.post<SarspStartValidationResponse>(`/sarsp/cases/${encodeURIComponent(caseId)}/validate`, payload ?? {});
};

export const getSarspCaseExecutionStatus = async (
  caseId: string,
  executionId: string,
): Promise<SarspExecutionStatusResponse> => {
  return apiClient.get<SarspExecutionStatusResponse>(
    `/sarsp/cases/${encodeURIComponent(caseId)}/executions/${encodeURIComponent(executionId)}`,
  );
};
