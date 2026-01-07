/**
 * API service for communicating with the backend
 */

import { apiGatewayUrl } from '../config';

export interface JobRecord {
  id: string;
  job_title: string;
  company_name: string;
  city: string;
  year_of_experience: number;
  published_date: string;
  link: string;
  source: string;
  description?: string;
  salary_range?: string;
  created_at: string;
  updated_at: string;
  // Enhanced display fields for responsive desktop layout
  company_logo_url?: string;
  tags?: string[];
  is_featured?: boolean;
}

export interface JobsResponse {
  items: JobRecord[];
  nextToken: string | null;
  pageSize: number;
}

export interface ErrorResponse {
  error: string;
  message: string;
  timestamp: string;
}

export interface JobFilters {
  title?: string;
  company?: string;
  source?: string;
  date_posted_after?: string;
}

export interface JobQueryOptions {
  limit?: number;
  nextToken?: string | null;
}

/**
 * Base API client with authentication
 */
class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl.replace(/\/$/, ''); // Remove trailing slash
  }

  /**
   * Makes an authenticated API request
   */
  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    
    const headers = {
      'Content-Type': 'application/json',
      ...options.headers,
    };

    try {
      const response = await fetch(url, {
        ...options,
        headers,
      });

      if (!response.ok) {
        const errorData: ErrorResponse = await response.json().catch(() => ({
          error: 'HTTP_ERROR',
          message: `HTTP ${response.status}: ${response.statusText}`,
          timestamp: new Date().toISOString(),
        }));
        
        throw new ApiError(errorData.message, response.status, errorData);
      }

      return await response.json();
    } catch (error) {
      if (error instanceof ApiError) {
        throw error;
      }
      
      // Network or other errors
      throw new ApiError(
        error instanceof Error ? error.message : 'Network error occurred',
        0,
        {
          error: 'NETWORK_ERROR',
          message: error instanceof Error ? error.message : 'Unknown network error',
          timestamp: new Date().toISOString(),
        }
      );
    }
  }

  /**
   * Fetches jobs with optional filters
   */
  async getJobs(filters: JobFilters = {}, options: JobQueryOptions = {}): Promise<JobsResponse> {
    const searchParams = new URLSearchParams();

    if (filters.title) {
      searchParams.append('job_title', filters.title);
    }
    if (filters.company) {
      searchParams.append('company_name', filters.company);
    }
    if (filters.source) {
      searchParams.append('source', filters.source.toLowerCase());
    }
    if (filters.date_posted_after) {
      searchParams.append('date_posted_after', filters.date_posted_after);
    }
    if (options.limit) {
      searchParams.append('limit', options.limit.toString());
    }
    if (options.nextToken) {
      searchParams.append('nextToken', options.nextToken);
    }

    const queryString = searchParams.toString();
    const endpoint = `/jobs${queryString ? `?${queryString}` : ''}`;

    type RawJobsResponse = {
      items: any[];
      nextToken?: string | null;
      pageSize?: number;
    };

    const rawResponse = await this.request<RawJobsResponse>(endpoint);

    const items: JobRecord[] = (rawResponse.items || []).map((item) => ({
      id: item.id || '',
      job_title: item.job_title || '',
      company_name: item.company_name || '',
      city: item.city || 'Non spécifié',
      year_of_experience: Number(item.year_of_experience) || 0,
      published_date: item.published_date || '',
      link: item.link || '',
      source: item.source || '',
      description: item.description || '',
      salary_range: item.salary_range || '',
      created_at: item.created_at || '',
      updated_at: item.updated_at || '',
      company_logo_url: item.company_logo_url,
      tags: item.tags || [],
      is_featured: item.is_featured || false,
    }));

    return {
      items,
      nextToken: rawResponse.nextToken ?? null,
      pageSize: rawResponse.pageSize ?? options.limit ?? 10,
    };
  }
}

/**
 * Custom error class for API errors
 */
export class ApiError extends Error {
  public status: number;
  public errorResponse: ErrorResponse;

  constructor(
    message: string,
    status: number,
    errorResponse: ErrorResponse
  ) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.errorResponse = errorResponse;
  }
}

// Create and export the default API client instance
export const apiClient = new ApiClient(apiGatewayUrl);