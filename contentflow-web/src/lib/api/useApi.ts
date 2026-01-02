import { useState, useEffect, useCallback } from 'react';
import { ApiError, handleApiError } from './apiClient';

/**
 * State interface for API requests
 */
export interface ApiState<T> {
  data: T | null;
  loading: boolean;
  error: ApiError | null;
}

/**
 * Hook for making API requests with loading and error states
 */
export function useApi<T>(
  apiFunction: () => Promise<T>,
  dependencies: any[] = [],
  executeOnMount: boolean = true
): ApiState<T> & { refetch: () => Promise<void> } {
  const [state, setState] = useState<ApiState<T>>({
    data: null,
    loading: executeOnMount,
    error: null,
  });

  const execute = useCallback(async () => {
    setState((prev) => ({ ...prev, loading: true, error: null }));
    try {
      const result = await apiFunction();
      setState({ data: result, loading: false, error: null });
    } catch (err) {
      setState({ data: null, loading: false, error: handleApiError(err) });
    }
  }, [apiFunction]);

  useEffect(() => {
    if (executeOnMount) {
      execute();
    }
  }, dependencies);

  return {
    ...state,
    refetch: execute,
  };
}

/**
 * Hook for making API mutations (POST, PUT, DELETE)
 */
export function useMutation<TData, TVariables = void>(
  mutationFunction: (variables: TVariables) => Promise<TData>
): {
  mutate: (variables: TVariables) => Promise<TData>;
  data: TData | null;
  loading: boolean;
  error: ApiError | null;
  reset: () => void;
} {
  const [state, setState] = useState<ApiState<TData>>({
    data: null,
    loading: false,
    error: null,
  });

  const mutate = useCallback(
    async (variables: TVariables): Promise<TData> => {
      setState({ data: null, loading: true, error: null });
      try {
        const result = await mutationFunction(variables);
        setState({ data: result, loading: false, error: null });
        return result;
      } catch (err) {
        const error = handleApiError(err);
        setState({ data: null, loading: false, error });
        throw error;
      }
    },
    [mutationFunction]
  );

  const reset = useCallback(() => {
    setState({ data: null, loading: false, error: null });
  }, []);

  return {
    mutate,
    ...state,
    reset,
  };
}

/**
 * Hook for paginated API requests
 */
export function usePaginatedApi<T>(
  apiFunction: (page: number, pageSize: number) => Promise<{ items: T[]; total: number; totalPages: number }>,
  initialPage: number = 1,
  pageSize: number = 10
): {
  data: T[];
  total: number;
  page: number;
  pageSize: number;
  totalPages: number;
  loading: boolean;
  error: ApiError | null;
  nextPage: () => void;
  prevPage: () => void;
  goToPage: (page: number) => void;
  refetch: () => Promise<void>;
} {
  const [page, setPage] = useState(initialPage);
  const [state, setState] = useState<{
    data: T[];
    total: number;
    totalPages: number;
    loading: boolean;
    error: ApiError | null;
  }>({
    data: [],
    total: 0,
    totalPages: 0,
    loading: true,
    error: null,
  });

  const execute = useCallback(async () => {
    setState((prev) => ({ ...prev, loading: true, error: null }));
    try {
      const result = await apiFunction(page, pageSize);
      setState({
        data: result.items,
        total: result.total,
        totalPages: result.totalPages,
        loading: false,
        error: null,
      });
    } catch (err) {
      setState((prev) => ({
        ...prev,
        loading: false,
        error: handleApiError(err),
      }));
    }
  }, [apiFunction, page, pageSize]);

  useEffect(() => {
    execute();
  }, [execute]);

  const nextPage = useCallback(() => {
    setPage((p) => Math.min(p + 1, state.totalPages));
  }, [state.totalPages]);

  const prevPage = useCallback(() => {
    setPage((p) => Math.max(p - 1, 1));
  }, []);

  const goToPage = useCallback((newPage: number) => {
    setPage(Math.max(1, Math.min(newPage, state.totalPages)));
  }, [state.totalPages]);

  return {
    data: state.data,
    total: state.total,
    page,
    pageSize,
    totalPages: state.totalPages,
    loading: state.loading,
    error: state.error,
    nextPage,
    prevPage,
    goToPage,
    refetch: execute,
  };
}

/**
 * Hook for polling API endpoints
 */
export function usePolling<T>(
  apiFunction: () => Promise<T>,
  interval: number = 5000,
  enabled: boolean = true
): ApiState<T> & { refetch: () => Promise<void> } {
  const [state, setState] = useState<ApiState<T>>({
    data: null,
    loading: true,
    error: null,
  });

  const execute = useCallback(async () => {
    try {
      const result = await apiFunction();
      setState({ data: result, loading: false, error: null });
    } catch (err) {
      setState({ data: null, loading: false, error: handleApiError(err) });
    }
  }, [apiFunction]);

  useEffect(() => {
    if (!enabled) return;

    execute(); // Initial fetch

    const intervalId = setInterval(execute, interval);

    return () => clearInterval(intervalId);
  }, [execute, interval, enabled]);

  return {
    ...state,
    refetch: execute,
  };
}
