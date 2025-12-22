"""
Lambda handler for getting all jobs from DynamoDB table.
"""
import json
import logging
import os
from typing import Any, Dict

import boto3
from botocore.exceptions import ClientError

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
    Lambda handler to get all jobs from DynamoDB table.
    
    Args:
        event: API Gateway event
        context: Lambda context
        
    Returns:
        API Gateway response
    """
    if event.get('httpMethod') != 'GET':
        raise ValueError(f"getAllJobs only accept GET method, you tried: {event.get('httpMethod')}")
    
    logger.info(f"Received event: {json.dumps(event)}")
    
    # Get table name from environment
    table_name = os.environ.get('DYNAMODB_TABLE')
    if not table_name:
        raise ValueError("DYNAMODB_TABLE environment variable is required")
    
    table = dynamodb.Table(table_name)
    
    try:
        # Scan all items from the table (only first 1MB data)
        response = table.scan()
        items = response.get('Items', [])
        
        logger.info(f"Retrieved {len(items)} items from table")
        
    except ClientError as e:
        logger.error(f"Error scanning table: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Failed to retrieve items'})
        }
    
    response_body = {
        'statusCode': 200,
        'body': json.dumps(items, default=str)  # default=str handles datetime serialization
    }
    
    logger.info(f"Response from {event.get('path')}: statusCode: {response_body['statusCode']}")
    return response_body