# Regulatory Jobs Infrastructure (TypeScript)

This directory contains the AWS CDK infrastructure code for the Regulatory Jobs application, written in TypeScript.

## Prerequisites

- Node.js (v18 or later)
- AWS CLI configured with appropriate credentials
- AWS CDK CLI (`npm install -g aws-cdk`)

## Setup

1. Install dependencies:
```bash
npm install
```

2. Build the TypeScript code:
```bash
npm run build
```

3. Bootstrap CDK (first time only):
```bash
cdk bootstrap
```

## Deployment

### Quick Deployment
```bash
npm run deploy
```

### Manual Deployment Steps

1. Deploy the CDK stack:
```bash
cdk deploy
```

2. Configure frontend environment:
```bash
npm run deploy-frontend-config
```

3. Set up CloudWatch Log Insights queries:
```bash
npm run setup-log-insights
```

### Get API Key
To retrieve the API key for frontend configuration:
```bash
npm run get-api-key RegulatoryJobsStack
```

This will create a `frontend.env` file with the necessary environment variables for the frontend application.

## Available Scripts

- `npm run build` - Compile TypeScript to JavaScript
- `npm run watch` - Watch for changes and recompile
- `npm run test` - Run tests
- `npm run cdk` - Run CDK commands
- `npm run deploy` - Deploy the stack
- `npm run destroy` - Destroy the stack
- `npm run diff` - Show differences between deployed and local stack
- `npm run synth` - Synthesize CloudFormation template
- `npm run get-api-key` - Retrieve API key value
- `npm run deploy-frontend-config` - Configure frontend environment
- `npm run setup-log-insights` - Set up CloudWatch Log Insights queries

## Architecture

The infrastructure creates:

- **DynamoDB Table**: Stores job postings with GSIs for filtering
- **Lambda Functions**: 
  - API Lambda: Serves job data through REST API
  - Scraper Lambda: Crawls job sites and stores data
- **API Gateway**: REST API with API Key authentication
- **EventBridge**: Schedules scraper execution 3 times daily
- **CloudWatch**: Monitoring, logging, and alerting
- **SNS**: Error notifications

## Configuration

The stack can be configured through environment variables:

- `CDK_DEFAULT_ACCOUNT`: AWS account ID
- `CDK_DEFAULT_REGION`: AWS region (default: eu-west-3)

## API Key Authentication

The API uses API Key authentication for simplicity. The frontend must include the API Key in the `X-API-Key` header for all requests to protected endpoints.

## Monitoring

The infrastructure includes comprehensive monitoring:

- CloudWatch Dashboard for metrics visualization
- CloudWatch Alarms for error detection
- SNS notifications for critical issues
- Log Insights queries for troubleshooting

Access the dashboard at:
```
https://eu-west-3.console.aws.amazon.com/cloudwatch/home?region=eu-west-3#dashboards:name=regulatory-jobs-monitoring
```

## Outputs

After deployment, the stack provides:
- `ApiGatewayUrl`: The base URL for the API
- `ApiKeyId`: The ID of the API Key (use npm run get-api-key to get the actual value)
- `JobsTableName`: The name of the DynamoDB table

## Troubleshooting

### Common Issues

1. **CDK Bootstrap Required**
   ```bash
   cdk bootstrap
   ```

2. **TypeScript Compilation Errors**
   ```bash
   npm run build
   ```

3. **AWS Credentials Not Found**
   ```bash
   aws configure
   # or
   export AWS_PROFILE=your-profile
   ```

4. **Node Modules Issues**
   ```bash
   rm -rf node_modules package-lock.json
   npm install
   ```

## Clean Up

To destroy the infrastructure:
```bash
npm run destroy
```

Note: The DynamoDB table has retention policy, so it won't be automatically deleted.