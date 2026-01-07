import { useState, useEffect, useCallback } from 'react';
import { apiClient, ApiError } from '../services/api';
import type { JobRecord, JobFilters } from '../services/api';

const MAX_RETRIES = 3;
const RETRY_DELAY = 1000; // 1 second
const DEFAULT_PAGE_SIZE = 10;

type PaginationToken = string | null;

interface FetchConfig {
  pageIndex: number;
  token: PaginationToken;
  filters: JobFilters;
  limit: number;
}

export interface UseJobsReturn {
  jobs: JobRecord[];
  loading: boolean;
  error: string | null;
  totalCount: number;
  filters: JobFilters;
  pageSize: number;
  currentPage: number;
  hasNextPage: boolean;
  hasPreviousPage: boolean;
  nextToken: string | null;
  setFilters: (filters: JobFilters) => void;
  setPageSize: (size: number) => void;
  refreshJobs: () => Promise<void>;
  clearError: () => void;
  goToNextPage: () => Promise<void>;
  goToPreviousPage: () => Promise<void>;
}

const sleep = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

export const useJobs = (): UseJobsReturn => {
  const [jobs, setJobs] = useState<JobRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filters, setFiltersState] = useState<JobFilters>({});
  const [pageSize, setPageSizeState] = useState(DEFAULT_PAGE_SIZE);
  const [currentPage, setCurrentPage] = useState(1);
  const [pageTokens, setPageTokens] = useState<PaginationToken[]>([null]);
  const [nextToken, setNextToken] = useState<string | null>(null);
  const [totalCount, setTotalCount] = useState(0);

  const fetchJobsWithRetry = useCallback(async (config: FetchConfig, retryCount = 0): Promise<void> => {
    const attemptFetch = async (currentRetryCount: number): Promise<void> => {
      const { pageIndex, token, filters: activeFilters, limit } = config;

      try {
        setLoading(true);
        setError(null);

        const response = await apiClient.getJobs(activeFilters, {
          limit,
          nextToken: token ?? undefined,
        });

        setJobs(response.items);
        setTotalCount(response.items.length);
        setNextToken(response.nextToken ?? null);
        setCurrentPage(pageIndex);

        setPageTokens(prev => {
          const updated = [...prev];
          updated[pageIndex - 1] = token ?? null;
          updated[pageIndex] = response.nextToken ?? null;
          return updated.slice(0, pageIndex + 1 + (response.nextToken ? 1 : 0));
        });

        setLoading(false);
      } catch (error) {
        console.error('Error fetching jobs:', error);

        const shouldRetry = currentRetryCount < MAX_RETRIES && (
          error instanceof ApiError && (
            error.status === 0 ||
            error.status >= 500 ||
            error.status === 429
          )
        );

        if (shouldRetry) {
          await sleep(RETRY_DELAY * Math.pow(2, currentRetryCount));
          return attemptFetch(currentRetryCount + 1);
        }

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
        } else if (error instanceof Error) {
          errorMessage = error.message;
        }

        setError(errorMessage);
        setLoading(false);
      }
    };

    return attemptFetch(retryCount);
  }, []);

  const setFilters = useCallback((newFilters: JobFilters) => {
    setFiltersState(newFilters);
  }, []);

  const setPageSize = useCallback((size: number) => {
    const sanitizedSize = Number.isFinite(size) && size > 0 ? Math.floor(size) : DEFAULT_PAGE_SIZE;
    setPageSizeState(sanitizedSize);
  }, []);

  const refreshJobs = useCallback(async () => {
    const tokenForPage = pageTokens[currentPage - 1] ?? null;
    await fetchJobsWithRetry({
      pageIndex: currentPage,
      token: tokenForPage,
      filters,
      limit: pageSize,
    });
  }, [currentPage, pageTokens, filters, pageSize, fetchJobsWithRetry]);

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  const goToNextPage = useCallback(async () => {
    const tokenForNextPage = pageTokens[currentPage] ?? null;
    if (!tokenForNextPage) {
      return;
    }

    await fetchJobsWithRetry({
      pageIndex: currentPage + 1,
      token: tokenForNextPage,
      filters,
      limit: pageSize,
    });
  }, [currentPage, pageTokens, filters, pageSize, fetchJobsWithRetry]);

  const goToPreviousPage = useCallback(async () => {
    if (currentPage <= 1) {
      return;
    }

    const tokenForPrevPage = pageTokens[currentPage - 2] ?? null;

    await fetchJobsWithRetry({
      pageIndex: currentPage - 1,
      token: tokenForPrevPage,
      filters,
      limit: pageSize,
    });
  }, [currentPage, pageTokens, filters, pageSize, fetchJobsWithRetry]);

  // Reset pagination and fetch first page when filters or page size change
  useEffect(() => {
    setPageTokens([null]);
    setCurrentPage(1);

    fetchJobsWithRetry({
      pageIndex: 1,
      token: null,
      filters,
      limit: pageSize,
    });
  }, [filters, pageSize, fetchJobsWithRetry]);

  return {
    jobs,
    loading,
    error,
    totalCount,
    filters,
    pageSize,
    currentPage,
    hasNextPage: Boolean(nextToken),
    hasPreviousPage: currentPage > 1,
    nextToken,
    setFilters,
    setPageSize,
    refreshJobs,
    clearError,
    goToNextPage,
    goToPreviousPage,
  };
};