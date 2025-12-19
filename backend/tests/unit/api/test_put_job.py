"""
Unit tests for put_job handler.
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
def sample_job_data():
    """Sample job data."""
    return {
        'job_title': 'Software Engineer',
        'company_name': 'Tech Corp',
        'link': 'https://example.com/job/123',
        'source': 'LinkedIn',
        'year_of_experience': 3,
        'published_date': '2024-01-15T10:00:00Z',
        'description': 'Great opportunity for a software engineer',
        'salary_range': 75000.0
    }


@pytest.fixture
def sample_event(sample_job_data):
    """Sample API Gateway event."""
    return {
        'httpMethod': 'PUT',
        'path': '/jobs',
        'body': json.dumps(sample_job_data)
    }


@mock_aws
def test_put_job_success(mock_env, sample_event):
    """Test successful job creation."""
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
    
    # Patch the dynamodb resource in the handler module
    with patch('src.handlers.put_job.dynamodb', dynamodb):
        from src.handlers.put_job import handler
        
        # Call handler
        result = handler(sample_event, {})
        
        # Verify response
        assert result['statusCode'] == 200
        response_body = json.loads(result['body'])
        assert response_body['job_title'] == 'Software Engineer'
        assert response_body['company_name'] == 'Tech Corp'
        assert 'id' in response_body
        assert 'created_at' in response_body
        assert 'updated_at' in response_body


def test_put_job_wrong_method(mock_env):
    """Test handler with wrong HTTP method."""
    from src.handlers.put_job import handler
    
    event = {'httpMethod': 'GET'}
    
    with pytest.raises(ValueError, match="putJob only accepts PUT method"):
        handler(event, {})


def test_put_job_invalid_json(mock_env):
    """Test handler with invalid JSON."""
    from src.handlers.put_job import handler
    
    event = {
        'httpMethod': 'PUT',
        'body': 'invalid json'
    }
    
    result = handler(event, {})
    
    assert result['statusCode'] == 400
    response_body = json.loads(result['body'])
    assert 'Invalid JSON' in response_body['error']


def test_put_job_missing_required_fields(mock_env):
    """Test handler with missing required fields."""
    from src.handlers.put_job import handler
    
    event = {
        'httpMethod': 'PUT',
        'body': json.dumps({
            'job_title': 'Software Engineer'
            # Missing other required fields
        })
    }
    
    result = handler(event, {})
    
    assert result['statusCode'] == 400
    response_body = json.loads(result['body'])
    assert 'Invalid request data' in response_body['error']
    assert 'details' in response_body


@mock_aws
def test_put_job_minimal_data(mock_env):
    """Test job creation with minimal required data."""
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
    
    minimal_job = {
        'job_title': 'Data Scientist',
        'company_name': 'Data Corp',
        'link': 'https://example.com/job/456',
        'source': 'Glassdoor',
        'year_of_experience': 2,
        'published_date': '2024-01-16T09:00:00Z'
        # No description or salary_range
    }
    
    event = {
        'httpMethod': 'PUT',
        'body': json.dumps(minimal_job)
    }
    
    # Patch the dynamodb resource in the handler module
    with patch('src.handlers.put_job.dynamodb', dynamodb):
        from src.handlers.put_job import handler
        
        # Call handler
        result = handler(event, {})
        
        # Verify response
        assert result['statusCode'] == 200
        response_body = json.loads(result['body'])
        assert response_body['job_title'] == 'Data Scientist'
        assert 'id' in response_body