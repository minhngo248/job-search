# Regulatory Jobs Backend

A serverless backend for the Regulatory Jobs application built with AWS SAM (Serverless Application Model). This backend provides a REST API for managing job postings with CRUD operations, backed by DynamoDB and deployed using AWS Lambda and API Gateway.

## Architecture

- **Lambda Functions**: Node.js 24.x handlers for API operations
- **API Gateway**: REST API with API key authentication
- **DynamoDB**: Simple table for job storage
- **Infrastructure**: Defined in `template.yaml` using AWS SAM

## Project Structure

- `src/handlers/` - Lambda function handlers (ES6 modules)
- `events/` - Test event files for local testing
- `__tests__/` - Jest unit tests
- `template.yaml` - AWS SAM infrastructure template
- `package.json` - Node.js dependencies and scripts

## Prerequisites

- [AWS SAM CLI](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-install.html)
- [Node.js 24](https://nodejs.org/en/) or later
- [Docker](https://hub.docker.com/search/?type=edition&offering=community) (for local testing)
- AWS CLI configured with appropriate credentials

## Getting Started

### 1. Install Dependencies

```bash
npm install
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

### Start Local API

```bash
sam local start-api
```

This starts the API Gateway locally on port 3000. You can test the endpoints:

```bash
# Get all jobs
curl http://localhost:3000/

# Get job by ID
curl http://localhost:3000/job-123

# Create a job (requires proper JSON payload)
curl -X PUT http://localhost:3000/ \
  -H "Content-Type: application/json" \
  -d '{"job_title":"Software Engineer","company_name":"Example Corp",...}'

# Delete a job
curl -X DELETE http://localhost:3000/job-123
```

### Test Individual Functions

```bash
# Test with sample events
sam local invoke getAllJobsFunction --event events/event-get-all-jobs.json
sam local invoke getByIdFunction --event events/event-get-by-id.json
sam local invoke putJobFunction --event events/event-put-job.json
sam local invoke deleteById --event events/event-delete-job.json
```

### Local DynamoDB

For complete local testing, run DynamoDB Local:

```bash
# Start DynamoDB Local (requires Docker)
docker run -p 8000:8000 amazon/dynamodb-local

# Start SAM with DynamoDB Local
sam local start-api --docker-network host
```

Set the `DYNAMODB_ENDPOINT` environment variable to use local DynamoDB:
```bash
export DYNAMODB_ENDPOINT=http://localhost:8000
sam local start-api
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

Tests are defined in the `__tests__` folder using Jest framework.

```bash
# Run all tests
npm test

# Run tests in watch mode
npm run test:watch

# Run tests with coverage
npm run test:coverage
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
