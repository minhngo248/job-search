"""
Lambda handler for getting a job by ID from DynamoDB table.
"""
import json
import logging
import os
from typing import Any, Dict
from src.utils.response import cors_response

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
    Lambda handler to get a job by ID from DynamoDB table.
    
    Args:
        event: API Gateway event
        context: Lambda context
        
    Returns:
        API Gateway response
    """
    if event.get('httpMethod') != 'GET':
        raise ValueError(f"getById only accept GET method, you tried: {event.get('httpMethod')}")
    
    logger.info(f"Received event: {json.dumps(event)}")
    
    # Get table name from environment
    table_name = os.environ.get('DYNAMODB_TABLE')
    if not table_name:
        raise ValueError("DYNAMODB_TABLE environment variable is required")
    
    table = dynamodb.Table(table_name)
    
    # Get id from pathParameters from API Gateway
    path_parameters = event.get('pathParameters', {})
    if not path_parameters or 'id' not in path_parameters:
        return cors_response(400, json.dumps({'error': 'Missing required parameter: id'}))
    
    job_id = path_parameters['id']
    
    # Validate that ID is not empty (DynamoDB doesn't allow empty string keys)
    if not job_id or job_id.strip() == '':
        return cors_response(404, json.dumps({'error': 'Job not found'}))
    
    try:
        # Get the item from the table
        response = table.get_item(Key={'id': job_id})
        item = response.get('Item')
        
        if not item:
            return cors_response(404, json.dumps({'error': 'Job not found'}))
        
        logger.info(f"Retrieved item with id: {job_id}")
        
    except ClientError as e:
        logger.error(f"Error getting item: {e}")
        return cors_response(500, json.dumps({'error': 'Failed to retrieve item'}))
    
    response_body = cors_response(200, json.dumps(item, default=str))
    
    logger.info(f"Response from {event.get('path')}: statusCode: {response_body['statusCode']}")
    return response_body