# Regulatory Jobs Backend

A serverless backend for the Regulatory Jobs application built with AWS SAM (Serverless Application Model). This backend provides a REST API for managing job postings with CRUD operations, backed by DynamoDB and deployed using AWS Lambda and API Gateway.

## Architecture

- **Lambda Functions**: Python 3.12 handlers for API operations
- **API Gateway**: REST API with API key authentication
- **DynamoDB**: Simple table for job storage
- **Infrastructure**: Defined in `template.yaml` using AWS SAM

## Project Structure

- `src/handlers/` - Lambda function handlers (Python modules)
- `tests/unit/` - Pytest unit tests
- `events/` - Test event files for local testing
- `template.yaml` - AWS SAM infrastructure template
- `pyproject.toml` - Python project configuration and dependencies
- `requirements.txt` - Python dependencies

## Prerequisites

- [AWS SAM CLI](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-install.html)
- [Python 3.12](https://www.python.org/downloads/) or later
- [uv](https://docs.astral.sh/uv/) - Python package manager (recommended)
- [Docker](https://hub.docker.com/search/?type=edition&offering=community) (for local testing)
- AWS CLI configured with appropriate credentials

## Getting Started

### 1. Install Dependencies

Using uv (recommended):
```bash
uv sync
```

Or using pip:
```bash
pip install -r requirements.txt
```

For development dependencies:
```bash
uv sync --dev
# or
pip install -r requirements.txt && pip install pytest pytest-mock moto[dynamodb]
```

### 2. Validate SAM Template

```bash
sam validate
```

### 3. Build the Application

```bash
sam build
```

### 4. Deploy to AWS

For first-time deployment:
```bash
sam deploy --guided
```

For subsequent deployments:
```bash
sam deploy
```

The guided deployment will prompt you for:
- **Stack Name**: Choose a unique name (e.g., `regulatory-jobs-backend`)
- **AWS Region**: Your preferred region (e.g., `us-east-1`)
- **Confirm changes**: Choose `Y` to review changes before deployment
- **Allow SAM CLI IAM role creation**: Choose `Y` to create necessary IAM roles
- **Save parameters**: Choose `Y` to save settings in `samconfig.toml`

## Local Development

### Run a DynamoDB container
```bash
# Create a Docker network
docker network create sam-dynamodb
# Then
docker run -p 8000:8000 --network sam-dynamodb --name dynamodb-local -d amazon/dynamodb-local
# Wait for 5s
sleep 5
# Create a table in DynamoDB
aws dynamodb create-table \
  --endpoint-url http://localhost:8000 \
  --table-name JobTable \
  --attribute-definitions AttributeName=id,AttributeType=S \
  --key-schema AttributeName=id,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST
```

### Start Local API

```bash
sam local start-api --port 8181 --docker-network sam-dynamodb --env-vars ./test-env.json
```

This starts the API Gateway locally on port 8181. You can test the endpoints:

```bash
# Get all jobs
curl http://localhost:8181/

# Get job by ID
curl http://localhost:8181/job-123

# Create a job (requires proper JSON payload)
curl -X PUT http://localhost:8181/ \
  -H "Content-Type: application/json" \
  -d '{"job_title":"Software Engineer","company_name":"Example Corp",...}'

# Delete a job
curl -X DELETE http://localhost:8181/job-123
```

### Test Individual Functions

```bash
# Test with sample events
sam local invoke getAllJobsFunction --event events/event-get-all-items.json \
  --docker-network sam-dynamodb --env-vars ./test-env.json
sam local invoke getByIdFunction --event events/event-get-by-id.json \
  --docker-network sam-dynamodb --env-vars ./test-env.json
sam local invoke putJobFunction --event events/event-put-item.json \
  --docker-network sam-dynamodb --env-vars ./test-env.json
sam local invoke deleteByIdFunction --event events/event-delete-by-id.json \
  --docker-network sam-dynamodb --env-vars ./test-env.json
```

## API Endpoints

The application provides the following REST API endpoints:

### GET /
Get all jobs from the database.
- **Authentication**: API Key required
- **Response**: Array of job objects

### GET /{id}
Get a specific job by ID.
- **Authentication**: API Key required
- **Parameters**: `id` - Job ID
- **Response**: Job object or 404 if not found

### PUT /
Create or update a job.
- **Authentication**: API Key required
- **Body**: Job object (see Job Model schema in template.yaml)
- **Response**: Created/updated job object

### DELETE /{id}
Delete a job by ID.
- **Authentication**: API Key required
- **Parameters**: `id` - Job ID
- **Response**: Success message or 404 if not found

## Job Model Schema

Jobs must include the following required fields:
- `job_title` (string, 1-100 chars)
- `company_name` (string, 1-100 chars)
- `link` (string, valid URL)
- `source` (enum: LinkedIn, Glassdoor, leem, snitem, other)
- `year_of_experience` (number, >= 0)
- `published_date` (string, ISO date-time format)

Optional fields:
- `description` (string, 0-500 chars)
- `salary_range` (number, >= 0)

## Monitoring and Logs

### View Lambda Logs

```bash
# Tail logs for a specific function
sam logs -n getAllJobsFunction --stack-name <your-stack-name> --tail

# View logs for all functions
sam logs --stack-name <your-stack-name> --tail
```

### CloudWatch Integration

All Lambda functions automatically log to CloudWatch. You can view logs in the AWS Console:
1. Go to CloudWatch → Log groups
2. Find log groups named `/aws/lambda/<function-name>`
3. View real-time logs and metrics

## Testing

### Unit Tests

Tests are defined in the `tests/unit/` folder using pytest framework.

```bash
# Run all tests
pytest

# Run tests with verbose output
pytest -v

# Run tests with coverage
pytest --cov=src

# Run specific test file
pytest tests/unit/handlers/test_get_all_jobs.py

# Run tests in watch mode (requires pytest-watch)
ptw
```

## API Key Management

After deployment, you'll need to retrieve the API key for frontend integration:

```bash
# Get the API key value
aws apigateway get-api-key --api-key <api-key-id> --include-value

# Or check the CloudFormation outputs
aws cloudformation describe-stacks --stack-name <your-stack-name> --query 'Stacks[0].Outputs'
```

## Cleanup

To delete the deployed application:

```bash
sam delete --stack-name <your-stack-name>
```

## Resources

- [AWS SAM Developer Guide](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/what-is-sam.html)
- [AWS Lambda Developer Guide](https://docs.aws.amazon.com/lambda/latest/dg/welcome.html)
- [Amazon DynamoDB Developer Guide](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Introduction.html)
