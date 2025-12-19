# Project Structure

## Root Level
```
├── assets/            # Architecture diagrams and images
├── backend/           # AWS SAM serverless backend (Python)
├── frontend/          # React SPA (TypeScript)
├── .kiro/             # Kiro configuration and specs
└── README.md          # Project documentation
```

## Backend Structure (`backend/`)
```
backend/
├── src/
│   └── handlers/      # Lambda function handlers
│       ├── get_all_jobs.py     # Get all jobs API
│       ├── get_by_id.py        # Get job by ID API
│       ├── put_job.py          # Create/update job API
│       └── delete_by_id.py     # Delete job API
├── tests/
│   └── unit/
│       └── handlers/  # Pytest unit tests
├── events/            # Test event files for local testing
├── template.yaml      # AWS SAM infrastructure template
├── pyproject.toml     # Python project configuration
├── requirements.txt   # Python dependencies
├── samconfig.toml     # SAM deployment configuration
└── README.md          # Backend documentation
```

## Frontend Structure (`frontend/`)
```
frontend/
├── src/
│   ├── components/    # React components
│   │   ├── JobCard.tsx       # Individual job display
│   │   ├── JobList.tsx       # Job listing container
│   │   ├── JobFilters.tsx    # Filter controls
│   │   └── index.ts          # Component exports
│   ├── hooks/         # Custom React hooks
│   │   └── useJobs.ts        # Job data fetching
│   ├── services/      # API integration
│   │   └── api.ts            # API client
│   ├── config/        # Configuration
│   │   └── index.ts          # Environment config
│   ├── App.tsx        # Main application
│   └── main.tsx       # Application entry point
├── public/            # Static assets
└── dist/              # Build output
```

## Deployment & CI/CD
```
.github/
└── workflows/         # GitHub Actions workflows
    └── deploy.yml     # Automated deployment pipeline

backend/template.yaml  # AWS SAM infrastructure as code
```

## Key Conventions

### Lambda Functions
- Each Lambda has its own handler in `src/handlers/`
- Python modules with `.py` extension
- Environment variables for resource names (e.g., `DYNAMODB_TABLE`)
- Pydantic models for request/response validation

### API Structure
- `GET /` - Get all jobs (requires API key)
- `GET /{id}` - Get job by ID (requires API key)  
- `PUT /` - Create/update job (requires API key)
- `DELETE /{id}` - Delete job (requires API key)

### DynamoDB Schema
- **Primary Key**: `id` (string)
- Simple table structure with basic CRUD operations
- No GSI indexes in current implementation

### File Naming
- **Python**: snake_case for functions and files, PascalCase for classes
- **TypeScript**: PascalCase for components, camelCase for utilities
- **Tests**: pytest test files in `tests/unit/` directory with `test_` prefix

### Deployment
- **Backend**: Deployed to AWS using SAM CLI via GitHub Actions
- **Frontend**: Local development only (deployment strategy TBD)

## Architecture Overview

```
┌─────────────────┐    ┌──────────────────────────────────────────────────┐
│                 │    │                 AWS Cloud                        │
│  React Frontend │    │                                                  │
│  (Port 5173)    │────┤  ┌─────────────────┐   ┌─────────────────────┐   │
│  Local Dev      │    │  │   API Gateway   │   │    EventBridge      │   │
│                 │    │  │  (API Key Auth) │   │   (Scheduler)       │   │
└─────────────────┘    │  └─────────────────┘   │  6h, 14h, 22h       │   │
                       │           │            └─────────────────────┘   │
                       │           │                        │             │
                       │  ┌─────────────────┐               │             │
                       │  │ Lambda Functions│               │             │
                       │  │                 │               │             │
                       │  │ ┌─────────────┐ │               │             │
                       │  │ │ GET /       │ │               │             │
                       │  │ │ GET /{id}   │ │               │             │
                       │  │ │ PUT /       │ │               │             │
                       │  │ │ DELETE /{id}│ │               │             │
                       │  │ └─────────────┘ │               │             │
                       │  │                 │               │             │
                       │  │ ┌─────────────┐ │               │             │
                       │  │ │   Worker    │◄────────────────┘             │
                       │  │ │ (Job Scraper│ │                             │
                       │  │ │  Function)  │ │                             │
                       │  │ └─────────────┘ │                             │
                       │  └─────────────────┘                             │
                       │           │                                      │
                       │           │                                      │
                       │  ┌─────────────────┐   ┌─────────────────────┐   │
                       │  │   DynamoDB      │   │    CloudWatch       │   │
                       │  │  (Jobs Table)   │   │  (Logs & Metrics)   │   │
                       │  └─────────────────┘   └─────────────────────┘   │
                       │                                                  │
                       └──────────────────────────────────────────────────┘

┌─────────────────┐
│  GitHub Actions │
│   (CI/CD)       │────► Deploys Backend to AWS
└─────────────────┘
```