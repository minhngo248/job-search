"""
Unit tests for get_all_jobs handler.
"""
import json
import os
from unittest.mock import patch, MagicMock

import pytest
from moto import mock_aws
import boto3

from src.handlers.get_all_jobs import handler


@pytest.fixture
def mock_env():
    """Mock environment variables."""
    with patch.dict(os.environ, {'DYNAMODB_TABLE': 'test-jobs-table'}):
        yield


@pytest.fixture
def sample_event():
    """Sample API Gateway event."""
    return {
        'httpMethod': 'GET',
        'path': '/jobs'
    }


@mock_aws
def test_get_all_jobs_success(mock_env, sample_event):
    """Test successful retrieval of all jobs."""
    # Create mock DynamoDB table
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    table = dynamodb.create_table(
        TableName='test-jobs-table',
        KeySchema=[{'AttributeName': 'id', 'KeyType': 'HASH'}],
        AttributeDefinitions=[{'AttributeName': 'id', 'AttributeType': 'S'}],
        BillingMode='PAY_PER_REQUEST'
    )
    
    # Add test items
    test_items = [
        {'id': 'job1', 'job_title': 'Software Engineer', 'company_name': 'Tech Corp'},
        {'id': 'job2', 'job_title': 'Data Scientist', 'company_name': 'Data Inc'}
    ]
    
    for item in test_items:
        table.put_item(Item=item)
    
    # Call handler
    result = handler(sample_event, {})
    
    # Verify response
    assert result['statusCode'] == 200
    response_body = json.loads(result['body'])
    assert len(response_body) == 2
    assert any(item['id'] == 'job1' for item in response_body)
    assert any(item['id'] == 'job2' for item in response_body)


def test_get_all_jobs_wrong_method(mock_env):
    """Test handler with wrong HTTP method."""
    event = {'httpMethod': 'POST'}
    
    with pytest.raises(ValueError, match="getAllJobs only accept GET method"):
        handler(event, {})


@mock_aws
def test_get_all_jobs_empty_table(mock_env, sample_event):
    """Test retrieval from empty table."""
    # Create empty mock DynamoDB table
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    dynamodb.create_table(
        TableName='test-jobs-table',
        KeySchema=[{'AttributeName': 'id', 'KeyType': 'HASH'}],
        AttributeDefinitions=[{'AttributeName': 'id', 'AttributeType': 'S'}],
        BillingMode='PAY_PER_REQUEST'
    )
    
    # Call handler
    result = handler(sample_event, {})
    
    # Verify response
    assert result['statusCode'] == 200
    response_body = json.loads(result['body'])
    assert response_body == []