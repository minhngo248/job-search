"""
Lambda handler for creating/updating a job in DynamoDB table.
"""
import json
import logging
import os
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, Optional

import boto3
from botocore.exceptions import ClientError
from pydantic import ValidationError

from src.shared.models import JobModel

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Create DynamoDB client outside handler for connection reuse
# Check if we're running locally with DynamoDB Local
dynamodb_endpoint = os.environ.get('DYNAMODB_ENDPOINT')
if dynamodb_endpoint:
    # Use local DynamoDB endpoint
    dynamodb = boto3.resource('dynamodb', endpoint_url=dynamodb_endpoint)
else:
    # Use AWS DynamoDB
    dynamodb = boto3.resource('dynamodb')


def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler to create/update a job in DynamoDB table.
    
    Args:
        event: API Gateway event
        context: Lambda context
        
    Returns:
        API Gateway response
    """
    if event.get('httpMethod') != 'PUT':
        raise ValueError(f"putJob only accepts PUT method, you tried: {event.get('httpMethod')}")
    
    logger.info(f"Received event: {json.dumps(event)}")
    
    # Get table name from environment
    table_name = os.environ.get('DYNAMODB_TABLE')
    if not table_name:
        raise ValueError("DYNAMODB_TABLE environment variable is required")
    
    table = dynamodb.Table(table_name)
    
    # Parse request body
    try:
        body = json.loads(event.get('body', '{}'))
    except json.JSONDecodeError:
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'Invalid JSON in request body'})
        }
    
    # Validate request body using Pydantic
    try:
        job_data = JobModel(**body)
    except ValidationError as e:
        logger.error(f"Validation error: {e}")
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'Invalid request data', 'details': e.errors()})
        }
    
    # Generate UUID for the job and current timestamp
    job_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
    
    # Prepare item for DynamoDB
    item = {
        'id': job_id,
        'job_title': job_data.job_title,
        'company_name': job_data.company_name,
        'link': job_data.link,
        'source': job_data.source,
        'year_of_experience': job_data.year_of_experience,
        'published_date': job_data.published_date,
        'created_at': now,
        'updated_at': now
    }
    
    # Add optional fields if provided
    if job_data.description:
        item['description'] = job_data.description
    if job_data.salary_range:
        item['salary_range'] = Decimal(str(job_data.salary_range))
    
    try:
        # Put item in DynamoDB table
        table.put_item(Item=item)
        logger.info(f"Successfully created/updated job with id: {job_id}")
        
    except ClientError as e:
        logger.error(f"Error putting item: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Failed to create/update job'})
        }
    
    response_body = {
        'statusCode': 200,
        'body': json.dumps({**body, 'id': job_id, 'created_at': now, 'updated_at': now})
    }
    
    logger.info(f"Response from {event.get('path')}: statusCode: {response_body['statusCode']}")
    return response_body