import { useState, useEffect, useCallback } from 'react';
import { apiClient, ApiError } from '../services/api';
import type { JobRecord, JobFilters } from '../services/api';

interface UseJobsState {
  jobs: JobRecord[];
  loading: boolean;
  error: string | null;
  totalCount: number;
  filters: JobFilters;
}

interface UseJobsActions {
  setFilters: (filters: JobFilters) => void;
  refreshJobs: () => Promise<void>;
  clearError: () => void;
}

export interface UseJobsReturn extends UseJobsState, UseJobsActions {}

const MAX_RETRIES = 3;
const RETRY_DELAY = 1000; // 1 second

export const useJobs = (): UseJobsReturn => {
  const [state, setState] = useState<UseJobsState>({
    jobs: [],
    loading: true,
    error: null,
    totalCount: 0,
    filters: {}
  });

  const sleep = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

  const fetchJobsWithRetry = useCallback(async (filters: JobFilters, retryCount = 0): Promise<void> => {
    const attemptFetch = async (currentRetryCount: number): Promise<void> => {
      try {
        setState(prev => ({ ...prev, loading: true, error: null }));
        
        const response = await apiClient.getJobs(filters);
        
        setState(prev => ({
          ...prev,
          jobs: response.jobs,
          totalCount: response.total_count,
          loading: false,
          error: null
        }));
      } catch (error) {
        console.error('Error fetching jobs:', error);
        
        // Determine if we should retry
        const shouldRetry = currentRetryCount < MAX_RETRIES && (
          error instanceof ApiError && (
            error.status === 0 || // Network error
            error.status >= 500 || // Server error
            error.status === 429 // Rate limiting
          )
        );

        if (shouldRetry) {
          console.log(`Retrying request (attempt ${currentRetryCount + 1}/${MAX_RETRIES})...`);
          await sleep(RETRY_DELAY * Math.pow(2, currentRetryCount)); // Exponential backoff
          return attemptFetch(currentRetryCount + 1);
        }

        // Handle different error types
        let errorMessage = 'Une erreur est survenue lors du chargement des offres d\'emploi.';
        
        if (error instanceof ApiError) {
          switch (error.status) {
            case 0:
              errorMessage = 'Impossible de se connecter au serveur. Vérifiez votre connexion internet.';
              break;
            case 401:
              errorMessage = 'Erreur d\'authentification. Veuillez vérifier votre configuration.';
              break;
            case 403:
              errorMessage = 'Accès refusé. Vérifiez vos permissions.';
              break;
            case 404:
              errorMessage = 'Service non trouvé. Veuillez contacter le support.';
              break;
            case 429:
              errorMessage = 'Trop de requêtes. Veuillez patienter avant de réessayer.';
              break;
            case 500:
            case 502:
            case 503:
            case 504:
              errorMessage = 'Erreur du serveur. Veuillez réessayer dans quelques instants.';
              break;
            default:
              errorMessage = error.message || errorMessage;
          }
        }

        setState(prev => ({
          ...prev,
          loading: false,
          error: errorMessage
        }));
      }
    };

    return attemptFetch(retryCount);
  }, []);

  const setFilters = useCallback((newFilters: JobFilters) => {
    setState(prev => ({ ...prev, filters: newFilters }));
  }, []);

  const refreshJobs = useCallback(async () => {
    await fetchJobsWithRetry(state.filters);
  }, [state.filters, fetchJobsWithRetry]);

  const clearError = useCallback(() => {
    setState(prev => ({ ...prev, error: null }));
  }, []);

  // Fetch jobs when filters change
  useEffect(() => {
    fetchJobsWithRetry(state.filters);
  }, [state.filters, fetchJobsWithRetry]);

  return {
    jobs: state.jobs,
    loading: state.loading,
    error: state.error,
    totalCount: state.totalCount,
    filters: state.filters,
    setFilters,
    refreshJobs,
    clearError
  };
};