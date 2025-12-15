# Regulatory Jobs Application

A serverless web application for displaying medical device regulatory job postings in the Île-de-France region.

## Project Structure

```
├── infrastructure/     # AWS CDK infrastructure (Python)
├── backend/           # Lambda functions (Python)
│   ├── src/
│   │   ├── api/       # API Lambda function
│   │   ├── scraper/   # Job scraper Lambda function
│   │   └── shared/    # Shared utilities and models
│   └── tests/         # Backend tests
├── frontend/          # React SPA (TypeScript)
└── .kiro/specs/       # Feature specifications
```

## Development Setup

### Infrastructure (CDK)
```bash
cd infrastructure
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Backend (Lambda Functions)
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### Frontend (React)
```bash
cd frontend
npm install
```

## Testing

### Backend Tests
```bash
cd backend
pytest
```

### Frontend Tests
```bash
cd frontend
npm test
```

## Deployment

The application uses AWS CDK for infrastructure deployment. See the infrastructure directory for deployment instructions.