# Project Structure

## Root Level
```
├── infrastructure/     # AWS CDK infrastructure (TypeScript)
├── backend/           # Lambda functions (Python)
├── frontend/          # React SPA (TypeScript)
├── .kiro/             # Kiro configuration and specs
└── Makefile           # Build automation
```

## Backend Structure (`backend/`)
```
backend/
├── src/
│   ├── api/           # API Lambda function
│   │   ├── auth.py           # Authentication logic
│   │   ├── job_service.py    # Job data service
│   │   └── lambda_handler.py # API entry point
│   ├── scraper/       # Job scraper Lambda function
│   │   ├── glassdoor_scraper.py
│   │   ├── linkedin_scraper.py
│   │   ├── specialized_scrapers.py
│   │   ├── job_processor.py
│   │   ├── web_utils.py
│   │   └── lambda_handler.py # Scraper entry point
│   └── shared/        # Shared utilities
│       ├── models.py         # Pydantic data models
│       ├── monitoring.py     # CloudWatch integration
│       └── validation.py     # Input validation
├── tests/
│   ├── unit/          # Unit tests
│   └── property/      # Property-based tests
├── requirements.txt   # Production dependencies
└── requirements-dev.txt # Development dependencies
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

## Infrastructure Structure (`infrastructure/`)
```
infrastructure/
├── lib/
│   └── regulatory-jobs-stack.ts  # Main CDK stack
├── scripts/           # Deployment utilities
│   ├── get-api-key.ts
│   ├── deploy-frontend-config.ts
│   └── setup-log-insights.ts
├── cdk.out/           # CDK synthesis output
└── app.ts             # CDK app entry point
```

## Key Conventions

### Lambda Functions
- Each Lambda has its own handler in `lambda_handler.py`
- Shared code goes in `src/shared/`
- Environment variables for resource names (e.g., `JOBS_TABLE_NAME`)

### API Structure
- `/jobs` - Main jobs endpoint (requires API key)
- `/health` - Health check (no auth required)
- Query parameters: `published_after`, `min_experience`, `max_experience`, `city`

### DynamoDB Schema
- **Primary Key**: `job_id` (string)
- **GSI 1**: `published-date-index` (published_date, city)
- **GSI 2**: `experience-index` (year_of_experience, published_date)

### File Naming
- **Python**: snake_case for files and functions
- **TypeScript**: PascalCase for components, camelCase for utilities
- **Tests**: `test_*.py` pattern for pytest discovery