/**
 * API service for communicating with the backend
 */

import { apiGatewayUrl, apiKey } from '../config';

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
  jobs: JobRecord[];
  total_count: number;
  filters_applied: {
    published_after?: string;
    min_experience?: number;
    max_experience?: number;
    city?: string;
  };
}

export interface ErrorResponse {
  error: string;
  message: string;
  timestamp: string;
}

export interface JobFilters {
  published_after?: string;
  min_experience?: number;
  max_experience?: number;
  city?: string;
}

/**
 * Base API client with authentication
 */
class ApiClient {
  private baseUrl: string;
  private apiKey: string;

  constructor(baseUrl: string, apiKey: string) {
    this.baseUrl = baseUrl.replace(/\/$/, ''); // Remove trailing slash
    this.apiKey = apiKey;
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
      'X-Api-Key': this.apiKey,
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
  async getJobs(filters: JobFilters = {}): Promise<JobsResponse> {
    const searchParams = new URLSearchParams();
    
    if (filters.published_after) {
      searchParams.append('published_after', filters.published_after);
    }
    if (filters.min_experience !== undefined) {
      searchParams.append('min_experience', filters.min_experience.toString());
    }
    if (filters.max_experience !== undefined) {
      searchParams.append('max_experience', filters.max_experience.toString());
    }
    if (filters.city) {
      searchParams.append('city', filters.city);
    }

    const queryString = searchParams.toString();
    const endpoint = `/jobs${queryString ? `?${queryString}` : ''}`;
    
    // Backend returns array directly, need to transform to expected format
    const rawJobs = await this.request<any[]>(endpoint);
    
    // Transform backend response to match frontend interface
    const jobs: JobRecord[] = rawJobs.map(item => ({
      id: item.id || '',
      job_title: item.job_title || '',
      company_name: item.company_name || '',
      city: item.city || 'Non spécifié',
      year_of_experience: parseInt(item.year_of_experience) || 0,
      published_date: item.published_date || '',
      link: item.link || '',
      source: item.source || '',
      description: item.description || '',
      salary_range: item.salary_range || '',
      created_at: item.created_at || '',
      updated_at: item.updated_at || '',
      company_logo_url: item.company_logo_url,
      tags: item.tags || [],
      is_featured: item.is_featured || false
    }));

    return {
      jobs,
      total_count: jobs.length,
      filters_applied: filters
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
export const apiClient = new ApiClient(apiGatewayUrl, apiKey);