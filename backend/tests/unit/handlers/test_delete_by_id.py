"""
Unit tests for delete_by_id handler.
"""
import json
import os
from unittest.mock import patch

import pytest
from moto import mock_aws
import boto3


@pytest.fixture
def mock_env():
    """Mock environment variables."""
    with patch.dict(os.environ, {
        'DYNAMODB_TABLE': 'test-jobs-table',
        'AWS_DEFAULT_REGION': 'us-east-1'
    }, clear=True):
        yield


@pytest.fixture
def sample_event():
    """Sample API Gateway event."""
    return {
        'httpMethod': 'DELETE',
        'path': '/jobs/job1',
        'pathParameters': {'id': 'job1'}
    }


@mock_aws
def test_delete_by_id_success(mock_env, sample_event):
    """Test successful job deletion."""
    # Create mock DynamoDB table
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    table = dynamodb.create_table(
        TableName='test-jobs-table',
        KeySchema=[{'AttributeName': 'id', 'KeyType': 'HASH'}],
        AttributeDefinitions=[{'AttributeName': 'id', 'AttributeType': 'S'}],
        BillingMode='PAY_PER_REQUEST'
    )
    
    # Wait for table to be created
    table.wait_until_exists()
    
    # Add test item
    test_item = {
        'id': 'job1',
        'job_title': 'Software Engineer',
        'company_name': 'Tech Corp'
    }
    table.put_item(Item=test_item)
    
    # Patch the dynamodb resource in the handler module
    with patch('src.handlers.delete_by_id.dynamodb', dynamodb):
        from src.handlers.delete_by_id import handler
        
        # Call handler
        result = handler(sample_event, {})
        
        # Verify response
        assert result['statusCode'] == 200
        response_body = json.loads(result['body'])
        assert 'Job deleted successfully' in response_body['message']


def test_delete_by_id_wrong_method(mock_env):
    """Test handler with wrong HTTP method."""
    from src.handlers.delete_by_id import handler
    
    event = {'httpMethod': 'GET'}
    
    with pytest.raises(ValueError, match="deleteId only accept DELETE method"):
        handler(event, {})


def test_delete_by_id_missing_path_parameters(mock_env):
    """Test handler with missing path parameters."""
    from src.handlers.delete_by_id import handler
    
    event = {
        'httpMethod': 'DELETE',
        'pathParameters': None
    }
    
    result = handler(event, {})
    
    assert result['statusCode'] == 400
    response_body = json.loads(result['body'])
    assert 'Missing required parameter: id' in response_body['error']


@mock_aws
def test_delete_by_id_not_found(mock_env):
    """Test deletion of non-existent job."""
    # Create empty mock DynamoDB table
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    table = dynamodb.create_table(
        TableName='test-jobs-table',
        KeySchema=[{'AttributeName': 'id', 'KeyType': 'HASH'}],
        AttributeDefinitions=[{'AttributeName': 'id', 'AttributeType': 'S'}],
        BillingMode='PAY_PER_REQUEST'
    )
    
    # Wait for table to be created
    table.wait_until_exists()
    
    event = {
        'httpMethod': 'DELETE',
        'pathParameters': {'id': 'nonexistent'}
    }
    
    # Patch the dynamodb resource in the handler module
    with patch('src.handlers.delete_by_id.dynamodb', dynamodb):
        from src.handlers.delete_by_id import handler
        
        # Call handler
        result = handler(event, {})
        
        # Verify response
        assert result['statusCode'] == 404
        response_body = json.loads(result['body'])
        assert 'Job not found' in response_body['error']


@mock_aws
def test_delete_by_id_empty_id(mock_env):
    """Test deletion with empty ID."""
    # Create mock DynamoDB table
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    table = dynamodb.create_table(
        TableName='test-jobs-table',
        KeySchema=[{'AttributeName': 'id', 'KeyType': 'HASH'}],
        AttributeDefinitions=[{'AttributeName': 'id', 'AttributeType': 'S'}],
        BillingMode='PAY_PER_REQUEST'
    )
    
    # Wait for table to be created
    table.wait_until_exists()
    
    event = {
        'httpMethod': 'DELETE',
        'pathParameters': {'id': ''}
    }
    
    # Patch the dynamodb resource in the handler module
    with patch('src.handlers.delete_by_id.dynamodb', dynamodb):
        from src.handlers.delete_by_id import handler
        
        # Call handler - this should still work but return 404
        result = handler(event, {})
        
        # Verify response
        assert result['statusCode'] == 404
        response_body = json.loads(result['body'])
        assert 'Job not found' in response_body['error']