# Implementation Plan

- [x] 1. Set up project structure and core infrastructure
  - Create directory structure for infrastructure, backend, and frontend components
  - Initialize CDK project with TypeScript configuration
  - Set up Python project structure for Lambda functions
  - Configure development dependencies and build tools
  - _Requirements: 5.1, 5.2_

- [x] 2. Implement AWS CDK infrastructure stack
  - [x] 2.1 Create DynamoDB table with GSI for job filtering
    - Define job table schema with partition key and GSI for filtering
    - Configure table settings for serverless workload
    - _Requirements: 4.1, 4.2_

  - [x] 2.2 Set up Cognito User Pool and authentication
    - Create Cognito User Pool with appropriate policies
    - Configure user pool client for frontend integration
    - _Requirements: 6.1, 6.2_

  - [x] 2.3 Create Lambda functions and IAM roles
    - Define API Lambda function with DynamoDB permissions
    - Define Scraper Lambda function with DynamoDB and internet access
    - Configure Scraper Lambda with reserved concurrency of 20
    - Configure appropriate timeout (15 minutes) and memory (1024MB) for scraper
    - Configure least-privilege IAM policies
    - _Requirements: 3.1, 3.2_

  - [x] 2.4 Set up API Gateway with Cognito authorization
    - Create REST API with CORS configuration
    - Configure Cognito authorizer for protected endpoints
    - Define /jobs endpoint with query parameter support
    - _Requirements: 2.1, 2.2, 6.2_

  - [x] 2.5 Configure EventBridge Scheduler for scraping
    - Create EventBridge rule for 3-times-daily execution
    - Configure rule to trigger scraper Lambda function
    - _Requirements: 3.1_

- [x] 3. Implement core data models and validation
  - [x] 3.1 Create job data model and validation functions
    - Define JobRecord class with all required fields
    - Implement validation for Île-de-France cities
    - Create date normalization utilities
    - _Requirements: 4.1, 4.2, 4.5_

  - [ ]* 3.2 Write property test for job data validation
    - **Property 7: Job Storage Completeness**
    - **Validates: Requirements 4.1**

  - [ ]* 3.3 Write property test for geographic validation
    - **Property 8: Geographic Validation**
    - **Validates: Requirements 4.2**

  - [ ]* 3.4 Write property test for date normalization
    - **Property 11: Date Normalization**
    - **Validates: Requirements 4.5**

- [x] 4. Implement API Lambda function
  - [x] 4.1 Create job filtering and query logic
    - Implement DynamoDB query operations with filters
    - Create filter parameter validation
    - Implement pagination support
    - _Requirements: 2.1, 2.2, 2.3_

  - [x] 4.2 Implement API request handlers
    - Create Lambda handler for /jobs GET endpoint
    - Implement Cognito token validation
    - Add error handling and logging
    - _Requirements: 1.1, 6.2, 7.1_

  - [ ]* 4.3 Write property test for date filtering
    - **Property 3: Date Filter Accuracy**
    - **Validates: Requirements 2.1**

  - [ ]* 4.4 Write property test for experience filtering
    - **Property 4: Experience Filter Accuracy**
    - **Validates: Requirements 2.2**

  - [ ]* 4.5 Write property test for multi-filter logic
    - **Property 5: Multi-Filter Conjunction**
    - **Validates: Requirements 2.3**

  - [ ]* 4.6 Write property test for error handling
    - **Property 6: Invalid Filter Error Handling**
    - **Validates: Requirements 2.4**

  - [ ]* 4.7 Write unit tests for API handlers
    - Test Lambda handler with various filter combinations
    - Test error conditions and edge cases
    - Test Cognito integration
    - _Requirements: 2.1, 2.2, 6.2, 7.1_

- [x] 5. Checkpoint - Ensure API tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 6. Implement job scraper Lambda function
  - [x] 6.1 Create web scraping utilities
    - Implement async HTTP client with aiohttp for concurrent requests
    - Create HTML parsing utilities using BeautifulSoup
    - Add user agent rotation and request delays
    - Implement semaphore-based concurrency control (max 3 concurrent requests per source)
    - _Requirements: 3.2, 3.5_

  - [x] 6.2 Implement LinkedIn job scraper
    - Create LinkedIn-specific scraping logic
    - Extract job data from LinkedIn job pages
    - Handle LinkedIn's anti-bot measures
    - _Requirements: 3.2, 3.3_

  - [x] 6.3 Implement Glassdoor job scraper
    - Create Glassdoor-specific scraping logic
    - Extract job data from Glassdoor listings
    - Handle pagination and search results
    - _Requirements: 3.2, 3.3_

  - [x] 6.4 Implement specialized site scrapers
    - Create scraper for emploi.leem.org
    - Create scraper for snitem.fr
    - Implement pharmaceutical company career page scrapers
    - _Requirements: 3.2, 3.3_

  - [x] 6.5 Implement job data processing and storage
    - Create job deduplication logic using URL hashing
    - Implement DynamoDB batch write operations (25 items per batch)
    - Add async processing pipeline for concurrent job processing
    - Add comprehensive logging and error handling
    - _Requirements: 3.3, 3.4, 4.3, 4.4_

  - [ ]* 6.6 Write property test for duplicate prevention
    - **Property 9: Duplicate Prevention**
    - **Validates: Requirements 4.3**

  - [ ]* 6.7 Write property test for invalid data rejection
    - **Property 10: Invalid Data Rejection**
    - **Validates: Requirements 4.4**

  - [ ]* 6.8 Write property test for scraper error resilience
    - **Property 15: Scraper Error Resilience**
    - **Validates: Requirements 3.5, 7.2**

  - [ ]* 6.9 Write unit tests for scraper components
    - Test individual scraper functions with mock HTML
    - Test error handling and retry logic
    - Test data validation and storage
    - _Requirements: 3.2, 3.3, 3.4, 3.5_

- [x] 7. Checkpoint - Ensure scraper tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 8. Set up React frontend project
  - [x] 8.1 Initialize Vite React TypeScript project
    - Create React project with TypeScript configuration
    - Install minimal required dependencies (no authentication libraries)
    - Configure build and development scripts
    - _Requirements: 1.1_

  - [x] 8.2 Configure environment variables for API integration
    - Set up .env file structure for API Gateway endpoint and API Key
    - Create configuration validation utilities
    - Configure CORS settings for local development
    - _Requirements: 1.1_

  - [ ]* 8.3 Write property test for API Key authentication
    - **Property 12: Authenticated API Access**
    - **Validates: Requirements 6.2**

  - [ ]* 8.4 Write property test for API Key error handling
    - **Property 14: API Key Error Handling**
    - **Validates: Requirements 6.5**

- [x] 9. Implement job listing and filtering UI
  - [x] 9.1 Create job listing components
    - Implement job card/list item component
    - Create job listing grid/list view
    - Add loading states and pagination
    - _Requirements: 1.1, 1.2, 1.3_

  - [x] 9.2 Implement filtering interface
    - Create date range picker for publication date filtering
    - Implement experience level filter controls
    - Add city filter dropdown for Île-de-France cities
    - _Requirements: 2.1, 2.2, 2.3_

  - [x] 9.3 Integrate API calls and state management
    - Implement API service layer with native fetch and API Key authentication
    - Create React hooks for job data and filtering
    - Add error handling and retry logic
    - _Requirements: 1.1, 2.1, 2.2, 7.4_

  - [ ]* 9.4 Write property test for job display completeness
    - **Property 1: Job Display Completeness**
    - **Validates: Requirements 1.2**

  - [ ]* 9.5 Write property test for API error handling
    - **Property 13: API Error Response Format**
    - **Validates: Requirements 6.3, 7.1**

  - [ ]* 9.6 Write unit tests for React components
    - Test job listing components with mock data
    - Test filtering interface interactions
    - Test error states and loading indicators
    - _Requirements: 1.1, 1.2, 2.1, 2.2, 6.3_

- [x] 10. Implement responsive design and accessibility
  - [x] 10.1 Add responsive CSS and mobile optimization
    - Implement responsive grid layout for job listings
    - Optimize filtering interface for mobile devices
    - Add touch-friendly interactions
    - _Requirements: 1.1, 1.2_

  - [x] 10.2 Implement accessibility features
    - Add ARIA labels and semantic HTML
    - Ensure keyboard navigation support
    - Implement screen reader compatibility
    - _Requirements: 1.1, 1.2_

- [x] 11. Final integration and deployment preparation
  - [x] 11.1 Configure CDK deployment outputs
    - Export API Gateway endpoint URL
    - Export API Key for frontend authentication
    - Create deployment scripts for frontend environment variables
    - _Requirements: 5.3_

  - [x] 11.2 Add comprehensive error handling and monitoring
    - Implement CloudWatch logging for all Lambda functions
    - Add error tracking and alerting
    - Configure performance monitoring
    - _Requirements: 3.4, 7.1, 7.2, 7.3_

  - [ ]* 11.3 Write integration tests
    - Test complete API workflows with test data
    - Test authentication flows end-to-end
    - Test scraper integration with mock sources
    - _Requirements: 1.1, 2.1, 3.1, 6.2_

- [x] 12. Final Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.