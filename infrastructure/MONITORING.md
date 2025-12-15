# Regulatory Jobs Application - Monitoring & Observability

This document describes the comprehensive monitoring and observability setup for the Regulatory Jobs application.

## Overview

The application includes multiple layers of monitoring:

- **CloudWatch Logs**: Structured logging for all Lambda functions
- **CloudWatch Metrics**: Custom metrics and AWS service metrics
- **CloudWatch Alarms**: Automated alerting for critical issues
- **CloudWatch Dashboard**: Visual monitoring interface
- **SNS Alerts**: Email/SMS notifications for critical events
- **Log Insights**: Predefined queries for log analysis

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Lambda Logs   │───▶│  CloudWatch Logs │───▶│  Log Insights   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                                ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│ Custom Metrics  │───▶│CloudWatch Metrics│───▶│   Dashboard     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                                ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│     Alarms      │───▶│   SNS Topics     │───▶│  Notifications  │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## Components

### 1. CloudWatch Log Groups

**API Lambda Log Group**: `/aws/lambda/{FunctionName}`
- Retention: 30 days
- Structured logging with request correlation
- Performance metrics embedded in logs

**Scraper Lambda Log Group**: `/aws/lambda/{FunctionName}`
- Retention: 30 days
- Execution statistics and error tracking
- Per-source scraping metrics

### 2. CloudWatch Metrics

#### Lambda Function Metrics
- `Invocations`: Function execution count
- `Errors`: Function error count
- `Duration`: Function execution time
- `Throttles`: Function throttling events

#### Custom Application Metrics
- `RegulatoryJobs/Scraper/ExecutionTime`: Scraper execution duration
- `RegulatoryJobs/Scraper/JobsScraped`: Number of jobs scraped
- `RegulatoryJobs/Scraper/JobsProcessed`: Number of jobs processed
- `RegulatoryJobs/Scraper/ErrorCount`: Number of errors encountered
- `RegulatoryJobs/Scraper/JobsScrapedBySource`: Jobs scraped per source
- `RegulatoryJobs/Scraper/SourceErrors`: Errors per scraping source

#### API Gateway Metrics
- `Count`: Total API requests
- `4XXError`: Client error responses
- `5XXError`: Server error responses
- `Latency`: API response time

#### DynamoDB Metrics
- `ConsumedReadCapacityUnits`: Read capacity consumption
- `ConsumedWriteCapacityUnits`: Write capacity consumption
- `ThrottledRequests`: Throttling events

### 3. CloudWatch Alarms

#### API Lambda Alarms
- **API Errors**: Triggers when error count ≥ 5 in 10 minutes
- **API Duration**: Triggers when average duration > 10 seconds

#### Scraper Lambda Alarms
- **Scraper Errors**: Triggers on any scraper execution error
- **Scraper Timeout**: Triggers when execution approaches timeout (14+ minutes)

#### API Gateway Alarms
- **4XX Errors**: Triggers when 4XX errors > 20 in 10 minutes
- **5XX Errors**: Triggers when 5XX errors ≥ 5 in 5 minutes

#### DynamoDB Alarms
- **Throttling**: Triggers when throttled requests > 5 in 10 minutes

### 4. SNS Error Alerts

**Topic**: `regulatory-jobs-error-alerts`
- Receives notifications from all critical alarms
- Can be configured for email, SMS, or webhook notifications

### 5. CloudWatch Dashboard

**Dashboard Name**: `regulatory-jobs-monitoring`

**Widgets**:
- API Lambda metrics (invocations, errors, duration)
- Scraper Lambda metrics (invocations, errors, duration)
- API Gateway metrics (requests, errors, latency)
- DynamoDB metrics (capacity, throttling)

## Setup Instructions

### 1. Deploy Infrastructure

The monitoring infrastructure is automatically deployed with the CDK stack:

```bash
cd infrastructure
cdk deploy
```

### 2. Configure SNS Notifications

Subscribe to error alerts:

```bash
# Get the SNS topic ARN from CDK outputs
aws cloudformation describe-stacks \
  --stack-name RegulatoryJobsStack \
  --query 'Stacks[0].Outputs[?OutputKey==`ErrorAlertTopicArn`].OutputValue' \
  --output text

# Subscribe to email notifications
aws sns subscribe \
  --topic-arn <TOPIC_ARN> \
  --protocol email \
  --notification-endpoint your-email@example.com
```

### 3. Set Up Log Insights Queries

Run the setup script to create predefined queries:

```bash
cd infrastructure
python setup-log-insights.py --region eu-west-3
```

### 4. Access Monitoring Resources

**CloudWatch Dashboard**:
```
https://eu-west-3.console.aws.amazon.com/cloudwatch/home?region=eu-west-3#dashboards:name=regulatory-jobs-monitoring
```

**Log Insights**:
```
https://eu-west-3.console.aws.amazon.com/cloudwatch/home?region=eu-west-3#logsV2:logs-insights
```

## Predefined Log Insights Queries

### API Lambda Queries

1. **API Errors - Last 24 Hours**
   - Shows all API errors with context
   - Includes request ID for correlation

2. **API Performance - Slow Requests**
   - Identifies requests taking > 5 seconds
   - Helps identify performance bottlenecks

3. **API Request Volume by Hour**
   - Shows request patterns over time
   - Useful for capacity planning

4. **API Error Rate Analysis**
   - Calculates error percentage
   - Monitors service reliability

### Scraper Lambda Queries

1. **Scraper Execution Summary**
   - Shows recent scraper runs with statistics
   - Includes jobs scraped and processed counts

2. **Scraper Errors by Source**
   - Groups errors by scraping source
   - Identifies problematic websites

3. **Scraper Performance Trends**
   - Shows performance trends over time
   - Helps identify degradation

4. **Critical Scraper Errors**
   - Shows critical errors requiring attention
   - Includes full error context

### General Queries

1. **Overall Error Summary**
   - Cross-function error overview
   - Shows error distribution

2. **Memory Usage Analysis**
   - Monitors Lambda memory consumption
   - Helps optimize memory allocation

3. **Cold Start Analysis**
   - Tracks cold start frequency and duration
   - Helps optimize performance

## Monitoring Best Practices

### 1. Log Correlation
- All logs include request IDs for correlation
- Use structured logging with consistent fields
- Include execution context in all log messages

### 2. Metric Naming
- Use consistent namespace: `RegulatoryJobs/{Component}`
- Include relevant dimensions for filtering
- Use appropriate units (Count, Seconds, Bytes)

### 3. Alert Thresholds
- Set thresholds based on normal operation patterns
- Use multiple evaluation periods to reduce false positives
- Configure different thresholds for different times of day

### 4. Dashboard Design
- Group related metrics together
- Use appropriate time ranges for different metrics
- Include both absolute and rate-based metrics

## Troubleshooting Guide

### High Error Rate
1. Check CloudWatch Dashboard for error patterns
2. Use "API Errors" Log Insights query to identify specific errors
3. Check DynamoDB throttling metrics
4. Verify API Gateway configuration

### Poor Performance
1. Use "API Performance - Slow Requests" query
2. Check Lambda memory and timeout settings
3. Monitor DynamoDB read/write capacity
4. Analyze cold start frequency

### Scraper Issues
1. Use "Scraper Errors by Source" to identify problematic sources
2. Check "Scraper Performance Trends" for degradation
3. Monitor scraper execution duration vs timeout
4. Verify network connectivity and rate limiting

### Missing Data
1. Check scraper execution logs for failures
2. Verify EventBridge rule is enabled and triggering
3. Check DynamoDB write throttling
4. Validate job data processing pipeline

## Cost Optimization

### Log Retention
- API logs: 30 days (adjust based on compliance needs)
- Scraper logs: 30 days (contains execution statistics)
- Consider archiving to S3 for longer retention

### Metric Costs
- Custom metrics are charged per metric per month
- Use dimensions wisely to avoid metric explosion
- Consider sampling for high-frequency metrics

### Dashboard Costs
- Dashboards are charged per dashboard per month
- Consolidate related metrics into fewer dashboards
- Use Log Insights for ad-hoc analysis instead of permanent widgets

## Security Considerations

### IAM Permissions
- Lambda functions have minimal CloudWatch permissions
- Monitoring scripts require CloudWatch read/write access
- SNS subscriptions require appropriate permissions

### Data Privacy
- Logs may contain sensitive information
- Use log filtering to exclude PII
- Consider encryption for sensitive metrics

### Access Control
- Restrict dashboard access to authorized users
- Use IAM policies to control metric access
- Monitor CloudWatch API usage

## Maintenance

### Regular Tasks
- Review alarm thresholds monthly
- Update Log Insights queries as needed
- Clean up unused metrics and dashboards
- Monitor CloudWatch costs

### Quarterly Reviews
- Analyze performance trends
- Adjust monitoring based on usage patterns
- Update alerting thresholds
- Review and update documentation