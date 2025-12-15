# Technology Stack

## Architecture
- **Serverless**: AWS Lambda functions with API Gateway
- **Database**: DynamoDB with GSI for filtering
- **Infrastructure**: AWS CDK (TypeScript)
- **Monitoring**: CloudWatch with custom dashboards and alarms

## Backend
- **Runtime**: Python 3.11
- **Framework**: Lambda functions with boto3
- **Dependencies**: requests, aiohttp, beautifulsoup4, pydantic
- **Code Quality**: Black formatter, flake8 linter, mypy type checking
- **Testing**: pytest with asyncio support

## Frontend
- **Framework**: React 19 with TypeScript
- **Build Tool**: Vite
- **Development Server**: Port 3000 with API proxy
- **Linting**: ESLint with React hooks plugin

## Infrastructure
- **IaC**: AWS CDK 2.100.0 with TypeScript
- **Deployment**: CDK deploy with usage plans and API keys
- **Scheduling**: EventBridge rules for scraper (3x daily)
- **Lambda Config**: Auto-managed concurrency, 15min timeout for scraper

## Common Commands

### Setup
```bash
make install                    # Install all dependencies
make install-backend           # Backend only
make install-frontend          # Frontend only
make install-infrastructure    # CDK only
```

### Testing
```bash
make test                      # Run all tests
make test-backend             # Backend tests with pytest
make test-frontend            # Frontend tests (--run flag for CI)
```

### Code Quality
```bash
make lint-backend             # flake8 + mypy
make format-backend           # Black formatting
```

### Development
```bash
cd frontend && npm run dev    # Start dev server (port 3000)
cd infrastructure && npm run watch  # CDK watch mode
```

### Deployment
```bash
cd infrastructure && npm run deploy    # Deploy stack
cd infrastructure && npm run get-api-key  # Get API key for frontend
```

## Code Style
- **Python**: Black formatting (88 char line length), type hints required
- **TypeScript**: ESLint configuration with React rules
- **Testing**: Descriptive test names with `test_` prefix