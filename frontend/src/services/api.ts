import axios, { AxiosInstance, AxiosError } from 'axios';
import {
  NoticeListResponse,
  NoticeFilterParams,
  NoticeDetailResponse,
  ErrorReportRequest,
  ErrorReportResponse,
} from '../types/notice';

export interface HealthResponse {
  status: string;
  timestamp: string;
  version: string;
}

export interface ApiErrorDetail {
  field?: string;
  issue: string;
}

export interface ApiErrorBody {
  code: string;
  message: string;
  details?: ApiErrorDetail[];
  request_id?: string;
}

export interface ApiErrorEnvelope {
  error: ApiErrorBody;
}

export const API_BASE_URL: string =
  import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

/**
 * Pre-configured Axios API client instance for CAI Campus Intelligence backend.
 */
export const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 15000,
});

// Response interceptor to handle standard API_CONTRACTS error envelopes
apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError<ApiErrorEnvelope>) => {
    // If backend returned standard error envelope, pass it through
    if (error.response?.data?.error) {
      return Promise.reject(error.response.data.error);
    }
    return Promise.reject(error);
  }
);

/**
 * Fetch health status from backend /health endpoint.
 */
export async function checkHealth(): Promise<HealthResponse> {
  const response = await apiClient.get<HealthResponse>('/health');
  return response.data;
}

/**
 * Fetch published notices from backend /notices endpoint per docs/API_CONTRACTS.md §7.4.
 */
export async function fetchNotices(params?: NoticeFilterParams): Promise<NoticeListResponse> {
  const response = await apiClient.get<NoticeListResponse>('/notices', { params });
  return response.data;
}

/**
 * Fetch notice detail by ID per docs/API_CONTRACTS.md §7.5.
 */
export async function fetchNoticeById(id: string): Promise<NoticeDetailResponse> {
  const response = await apiClient.get<NoticeDetailResponse>(`/notices/${id}`);
  return response.data;
}

/**
 * Submit an error report for a notice per docs/API_CONTRACTS.md §7.8.
 * Endpoint: POST /api/v1/notices/{id}/reports
 */
export async function submitErrorReport(
  noticeId: string,
  payload: ErrorReportRequest
): Promise<ErrorReportResponse> {
  const response = await apiClient.post<ErrorReportResponse>(
    `/notices/${noticeId}/reports`,
    payload
  );
  return response.data;
}

/**
 * Mock helper for submitting error reports in offline / preview environments.
 */
export async function mockSubmitErrorReport(
  _noticeId: string,
  _payload: ErrorReportRequest
): Promise<ErrorReportResponse> {
  // Simulate network latency
  await new Promise((resolve) => setTimeout(resolve, 600));
  return {
    report_id: `rep_${Date.now().toString(36)}_${Math.random().toString(36).substring(2, 6)}`,
    status: 'received',
  };
}

export const api = apiClient;
export default apiClient;

