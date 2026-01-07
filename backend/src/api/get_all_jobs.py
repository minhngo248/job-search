"""Lambda handler for getting all jobs from DynamoDB table."""

import base64
import binascii
import json
import logging
import os
from typing import Any, Dict, Optional

import boto3
from boto3.dynamodb.conditions import Attr, Key
from botocore.exceptions import ClientError

from src.utils.response import cors_response

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


def _encode_pagination_token(last_evaluated_key: Dict[str, Any]) -> str:
    """Encode DynamoDB LastEvaluatedKey into URL-safe string."""
    encoded = base64.urlsafe_b64encode(json.dumps(last_evaluated_key).encode('utf-8'))
    return encoded.decode('utf-8')


def _decode_pagination_token(token: str) -> Dict[str, Any]:
    """Decode the client pagination token back into LastEvaluatedKey."""
    decoded = base64.urlsafe_b64decode(token.encode('utf-8')).decode('utf-8')
    return json.loads(decoded)


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
    
    query_parameters = event.get('queryStringParameters') or {}

    limit_param = query_parameters.get('limit')
    next_token_param = query_parameters.get('nextToken')

    limit = 10  # Default limit
    if limit_param:
        try:
            limit = int(limit_param)
            if limit <= 0:
                raise ValueError
            # Guardrail to avoid massive reads
            limit = min(limit, 100)
        except ValueError:
            return cors_response(400, json.dumps({'error': 'limit must be a positive integer'}))

    job_title = query_parameters.get('job_title')
    company_name = query_parameters.get('company_name')
    source = query_parameters.get('source')
    date_posted_after = query_parameters.get('date_posted_after')
    logger.info(
        "Query parameters - job_title: %s, company_name: %s, source: %s, date_posted_after: %s",
        job_title,
        company_name,
        source,
        date_posted_after,
    )

    # Get table name from environment
    table_name = os.environ.get('DYNAMODB_JOB_TABLE')
    if not table_name:
        raise ValueError("DYNAMODB_JOB_TABLE environment variable is required")
    
    table = dynamodb.Table(table_name)
    
    try:
        query_kwargs: Dict[str, Any] = {
            'IndexName': 'PublishedDatePkIndex',
            'ScanIndexForward': False,
            'Limit': limit,
            'KeyConditionExpression': Key('pk').eq('JOB#ALL'),
        }

        if next_token_param:
            try:
                query_kwargs['ExclusiveStartKey'] = _decode_pagination_token(next_token_param)
            except (ValueError, json.JSONDecodeError, binascii.Error) as error:
                logger.warning('Invalid nextToken provided: %s', error)
                return cors_response(400, json.dumps({'error': 'Invalid nextToken value'}))

        filter_expression = None
        if job_title:
            filter_expression = Attr('job_title').contains(job_title)
        if company_name:
            expr = Attr('company_name').contains(company_name)
            filter_expression = expr if filter_expression is None else filter_expression & expr
        if source:
            expr = Attr('source').eq(source)
            filter_expression = expr if filter_expression is None else filter_expression & expr
        if date_posted_after:
            expr = Attr('published_date').gt(date_posted_after)
            filter_expression = expr if filter_expression is None else filter_expression & expr

        if filter_expression is not None:
            query_kwargs['FilterExpression'] = filter_expression

        response = table.query(**query_kwargs)
        items = response.get('Items', [])
        last_evaluated_key: Optional[Dict[str, Any]] = response.get('LastEvaluatedKey')
        
        logger.info(f"Retrieved {len(items)} items from table")
        
    except ClientError as e:
        logger.error(f"Error scanning table: {e}")
        return cors_response(500, json.dumps({'error': 'Failed to retrieve items'}))
    
    payload = {
        'items': items,
        'nextToken': _encode_pagination_token(last_evaluated_key) if last_evaluated_key else None,
        'pageSize': limit,
    }

    response_body = cors_response(200, json.dumps(payload, default=str))
    
    logger.info(f"Response from {event.get('path')}: statusCode: {response_body['statusCode']}")
    return response_body