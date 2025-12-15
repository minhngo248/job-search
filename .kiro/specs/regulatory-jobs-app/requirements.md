# Requirements Document

## Introduction

A web application for displaying the latest regulatory jobs in medical devices within the Île-de-France region. The system consists of a serverless infrastructure deployed on AWS, a Python backend for job scraping and API services, and a React frontend for job browsing and filtering. The application automatically scrapes job postings from multiple sources including LinkedIn, Glassdoor, pharmaceutical company career pages, and specialized medical device job boards, then provides users with a filtered view of relevant opportunities.

## Glossary

- **Regulatory_Jobs_System**: The complete web application system for medical device regulatory job listings
- **Job_Scraper**: The Lambda function responsible for crawling and extracting job postings from external sources
- **API_Service**: The Lambda function that serves filtered job data through API Gateway
- **Job_Filter**: The filtering mechanism that allows users to search jobs by criteria
- **Île-de-France**: The administrative region of France that includes Paris and surrounding departments
- **Medical_Device_Job**: A job posting specifically related to regulatory affairs in the medical device industry
- **DynamoDB_Table**: The NoSQL database table storing job posting records
- **EventBridge_Scheduler**: AWS service that triggers the job scraping function three times daily

## Requirements

### Requirement 1

**User Story:** As a job seeker in medical device regulatory affairs, I want to view the latest job postings in Île-de-France, so that I can find relevant career opportunities without manually searching multiple websites.

#### Acceptance Criteria

1. WHEN a user visits the application THEN the Regulatory_Jobs_System SHALL display all available medical device regulatory jobs in Île-de-France
2. WHEN job postings are displayed THEN the Regulatory_Jobs_System SHALL show job title, company, location, experience requirements, and publication date
3. WHEN a user clicks on a job posting THEN the Regulatory_Jobs_System SHALL redirect them to the original job listing
4. THE Regulatory_Jobs_System SHALL load and display job listings within 3 seconds of page load
5. WHEN the job database is empty THEN the Regulatory_Jobs_System SHALL display an appropriate message indicating no jobs are available

### Requirement 2

**User Story:** As a job seeker, I want to filter job postings by publication date and years of experience, so that I can find jobs that match my specific criteria and timeline.

#### Acceptance Criteria

1. WHEN a user selects a publication date filter THEN the API_Service SHALL return only jobs published within the specified timeframe
2. WHEN a user selects an experience level filter THEN the API_Service SHALL return only jobs matching the specified experience requirements
3. WHEN multiple filters are applied THEN the API_Service SHALL return jobs that satisfy all selected criteria
4. WHEN filter parameters are invalid THEN the API_Service SHALL return an appropriate error message and maintain system stability
5. WHEN no jobs match the applied filters THEN the Regulatory_Jobs_System SHALL display a message indicating no matching results

### Requirement 3

**User Story:** As a system administrator, I want job data to be automatically updated three times daily, so that users always see the most current job postings without manual intervention.

#### Acceptance Criteria

1. WHEN EventBridge_Scheduler triggers the scraping process THEN the Job_Scraper SHALL execute and collect new job postings
2. WHEN the Job_Scraper runs THEN it SHALL crawl LinkedIn, Glassdoor, emploi.leem.org, snitem.fr, and pharmaceutical company career pages
3. WHEN new job postings are found THEN the Job_Scraper SHALL store them in the DynamoDB_Table with all required fields
4. WHEN the scraping process completes THEN the Job_Scraper SHALL log the number of jobs processed and any errors encountered
5. WHEN scraping fails for a specific source THEN the Job_Scraper SHALL continue processing other sources and log the failure

### Requirement 4

**User Story:** As a system administrator, I want job data to be stored with comprehensive metadata, so that the system can provide accurate filtering and display capabilities.

#### Acceptance Criteria

1. WHEN a job posting is stored THEN the DynamoDB_Table SHALL contain fields for year_of_experience, published_date, link, city, job_title, and company_name
2. WHEN storing job data THEN the Job_Scraper SHALL validate that the city is within the Île-de-France region
3. WHEN duplicate job postings are detected THEN the Job_Scraper SHALL update existing records rather than create duplicates
4. WHEN job data is invalid or incomplete THEN the Job_Scraper SHALL log the issue and skip the invalid posting
5. WHEN storing published_date THEN the Job_Scraper SHALL normalize all dates to ISO 8601 format

### Requirement 5

**User Story:** As a developer, I want the system to be deployed using Infrastructure as Code, so that the deployment is reproducible and the infrastructure is properly managed.

#### Acceptance Criteria

1. WHEN the infrastructure is deployed THEN the AWS_CDK SHALL create API Gateway with API Key authentication, Lambda functions, DynamoDB table, and EventBridge Scheduler
2. WHEN the CDK stack is deployed THEN all AWS resources SHALL be properly configured with appropriate permissions and security settings
3. WHEN the deployment completes THEN the system SHALL provide API Gateway endpoint and API Key for frontend integration
4. WHEN infrastructure updates are needed THEN the AWS_CDK SHALL support incremental updates without data loss
5. WHEN the stack is destroyed THEN the AWS_CDK SHALL clean up all created resources except for data storage components if configured for retention

### Requirement 6

**User Story:** As a frontend developer, I want environment configuration for API integration, so that the React application can connect to the backend services securely.

#### Acceptance Criteria

1. WHEN the frontend application starts THEN it SHALL read API Gateway endpoint and API Key from environment variables
2. WHEN making API calls THEN the frontend SHALL authenticate requests using API Key in X-API-Key header
3. WHEN API requests fail THEN the frontend SHALL display appropriate error messages to users
4. WHEN environment variables are missing THEN the frontend SHALL display a configuration error and prevent application startup
5. WHEN API Key authentication fails THEN the frontend SHALL display appropriate authentication error messages

### Requirement 7

**User Story:** As a job seeker, I want the application to handle errors gracefully, so that I can continue using the system even when some components experience issues.

#### Acceptance Criteria

1. WHEN the API_Service encounters an error THEN it SHALL return appropriate HTTP status codes and error messages
2. WHEN the Job_Scraper fails to access a job source THEN it SHALL continue processing other sources and log the failure
3. WHEN the DynamoDB_Table is unavailable THEN the API_Service SHALL return a service unavailable message
4. WHEN the frontend loses network connectivity THEN it SHALL display an offline message and retry requests when connectivity returns
5. WHEN invalid filter parameters are provided THEN the system SHALL return validation errors without crashing