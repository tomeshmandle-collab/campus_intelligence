import axios, { AxiosInstance, AxiosError } from 'axios';

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

export const api = apiClient;
export default apiClient;

