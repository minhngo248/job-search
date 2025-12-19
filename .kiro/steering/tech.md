# Technology Stack

## Architecture
- **Serverless**: AWS Lambda functions with API Gateway
- **Database**: DynamoDB with simple table structure
- **Infrastructure**: AWS SAM (Serverless Application Model) with YAML templates
- **Monitoring**: CloudWatch with Lambda function logs
- **Deployment**: GitHub Actions with SAM CLI

## Backend
- **Runtime**: Python 3.12
- **Framework**: AWS Lambda functions with boto3 SDK
- **Infrastructure**: AWS SAM template (template.yaml)
- **API**: API Gateway with API key authentication
- **Database**: DynamoDB SimpleTable with CRUD operations
- **Testing**: pytest framework for unit tests
- **Validation**: Pydantic for request/response validation

## Frontend
- **Framework**: React 19 with TypeScript
- **Build Tool**: Vite
- **Development Server**: Port 5173 (Vite default)
- **Linting**: ESLint with React hooks plugin
- **Deployment**: Local development only (deployment TBD)

## Common Commands

### Backend Development
```bash
cd backend
uv sync                         # Install dependencies (recommended)
# or pip install -r requirements.txt
sam validate                    # Validate SAM template
sam build                       # Build Lambda functions
sam local start-api            # Start API locally (port 3000)
sam deploy --guided            # Deploy to AWS (first time)
sam deploy                     # Deploy updates
```

### Frontend Development
```bash
cd frontend
npm install                     # Install dependencies
npm run dev                     # Start dev server (port 5173)
npm run build                   # Build for production
npm run lint                    # Run ESLint
```

### Local DynamoDB
```bash
# Start DynamoDB Local (requires Docker)
docker run -p 8000:8000 amazon/dynamodb-local
# Use with SAM local
sam local start-api --docker-network host
```

### Testing
```bash
cd backend
pytest                         # Run pytest tests
pytest -v                      # Run with verbose output
pytest --cov=src              # Run with coverage
```

## Code Style
- **Python**: Black formatter, flake8 linter, mypy type checking
- **JavaScript/TypeScript**: ESLint configuration with standard rules
- **SAM Templates**: YAML formatting with proper indentation
- **Testing**: pytest framework with descriptive test names