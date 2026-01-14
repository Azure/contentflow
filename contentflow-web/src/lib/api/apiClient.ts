/// <reference types="vite/client" />

/**
 * API Client Configuration
 */
export interface ApiConfig {
  baseURL: string;
  timeout?: number;
  headers?: Record<string, string>;
}

/**
 * API Error Response
 */
export interface ApiError {
  message: string;
  status?: number;
  detail?: any;
}

/**
 * Request options for fetch
 */
interface RequestOptions extends RequestInit {
  params?: Record<string, any>;
  responseType?: 'json' | 'blob' | 'text';
}

/**
 * Default API configuration
 */
const defaultConfig: ApiConfig = {
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8090/api/',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
};

/**
 * API Client class using native fetch
 */
class ApiClient {
  private config: ApiConfig;

  constructor(config: ApiConfig) {
    this.config = config;
  }

  /**
   * Build full URL with base URL and path
   */
  private buildUrl(path: string, params?: Record<string, any>): string {
    const url = new URL(path.startsWith('/') ? path.slice(1) : path, this.config.baseURL);
    
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null && value !== '') {
          if (Array.isArray(value)) {
            value.forEach((v) => url.searchParams.append(key, String(v)));
          } else {
            url.searchParams.append(key, String(value));
          }
        }
      });
    }
    
    return url.toString();
  }

  /**
   * Get default headers including auth token
   */
  private getHeaders(customHeaders?: HeadersInit): Record<string, string> {
    const headers: Record<string, string> = {
      ...this.config.headers,
    };

    // Merge custom headers
    if (customHeaders) {
      if (customHeaders instanceof Headers) {
        customHeaders.forEach((value, key) => {
          headers[key] = value;
        });
      } else if (Array.isArray(customHeaders)) {
        customHeaders.forEach(([key, value]) => {
          headers[key] = value;
        });
      } else {
        Object.assign(headers, customHeaders);
      }
    }

    // Add auth token if available
    const token = localStorage.getItem('authToken');
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    return headers;
  }

  /**
   * Handle fetch with timeout
   */
  private async fetchWithTimeout(url: string, options: RequestInit): Promise<Response> {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), this.config.timeout);

    try {
      const response = await fetch(url, {
        ...options,
        signal: controller.signal,
      });
      clearTimeout(timeoutId);
      return response;
    } catch (error) {
      clearTimeout(timeoutId);
      if ((error as Error).name === 'AbortError') {
        throw new Error('Request timeout');
      }
      throw error;
    }
  }

  /**
   * Handle response and errors
   */
  private async handleResponse<T>(response: Response, responseType: 'json' | 'blob' | 'text' = 'json'): Promise<T> {
    if (!response.ok) {
      let errorData: any;
      try {
        errorData = await response.json();
      } catch {
        errorData = { message: response.statusText };
      }

      const apiError: ApiError = {
        message: errorData?.message || errorData?.detail || response.statusText,
        status: response.status,
        detail: errorData,
      };

      throw apiError;
    }

    if (responseType === 'blob') {
      return (await response.blob()) as T;
    } else if (responseType === 'text') {
      return (await response.text()) as T;
    } else {
      return await response.json();
    }
  }

  /**
   * Perform request
   */
  private async request<T>(
    method: string,
    path: string,
    options: RequestOptions = {}
  ): Promise<T> {
    const { params, responseType = 'json', headers: customHeaders, body, ...fetchOptions } = options;
    
    const url = this.buildUrl(path, params);
    const headers = this.getHeaders(customHeaders);

    // Don't set Content-Type for FormData (browser will set it with boundary)
    if (body instanceof FormData) {
      delete headers['Content-Type'];
    }

    try {
      const response = await this.fetchWithTimeout(url, {
        method,
        headers,
        body: body instanceof FormData ? body : (body ? JSON.stringify(body) : undefined),
        ...fetchOptions,
      });

      return await this.handleResponse<T>(response, responseType);
    } catch (error) {
      if ((error as ApiError).status !== undefined) {
        throw error; // Already an ApiError
      }

      const apiError: ApiError = {
        message: (error as Error).message || 'No response from server. Please check your connection.',
        detail: error,
      };

      throw apiError;
    }
  }

  /**
   * Get current API client configuration
   */
  getConfig(): ApiConfig {
    return this.config;
  }

  /**
   * GET request
   */
  async get<T>(path: string, options?: RequestOptions): Promise<T> {
    return this.request<T>('GET', path, options);
  }

  /**
   * POST request
   */
  async post<T>(path: string, data?: any, options?: RequestOptions): Promise<T> {
    return this.request<T>('POST', path, { ...options, body: data });
  }

  /**
   * PUT request
   */
  async put<T>(path: string, data?: any, options?: RequestOptions): Promise<T> {
    return this.request<T>('PUT', path, { ...options, body: data });
  }

  /**
   * PATCH request
   */
  async patch<T>(path: string, data?: any, options?: RequestOptions): Promise<T> {
    return this.request<T>('PATCH', path, { ...options, body: data });
  }

  /**
   * DELETE request
   */
  async delete<T>(path: string, options?: RequestOptions): Promise<T> {
    return this.request<T>('DELETE', path, options);
  }
}

/**
 * Create API client with configuration
 */
export const createApiClient = (config?: Partial<ApiConfig>): ApiClient => {
  const mergedConfig = { ...defaultConfig, ...config };
  return new ApiClient(mergedConfig);
};

/**
 * Default API client instance
 */
export const apiClient = createApiClient();

/**
 * Helper function to handle API errors
 */
export const handleApiError = (error: unknown): ApiError => {
  if (typeof error === 'object' && error !== null && 'message' in error) {
    return error as ApiError;
  }
  
  return {
    message: 'An unexpected error occurred',
    detail: error,
  };
};

/**
 * Helper to build query parameters
 */
export const buildQueryParams = (params: Record<string, any>): string => {
  const searchParams = new URLSearchParams();
  
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') {
      if (Array.isArray(value)) {
        value.forEach((v) => searchParams.append(key, String(v)));
      } else {
        searchParams.append(key, String(value));
      }
    }
  });
  
  return searchParams.toString();
};
