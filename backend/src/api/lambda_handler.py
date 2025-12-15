"""
AWS Lambda handler for the Regulatory Jobs API.

This module provides the main Lambda function handler for processing
API Gateway requests for job listings with filtering and authentication.
"""
import json
import logging
import os
from datetime import datetime
from typing import Dict, Any, Optional
import traceback

import boto3
from botocore.exceptions import ClientError

from ..shared.models import JobFilters, ErrorResponse
from .job_service import JobService

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add request ID to all log messages
class RequestContextFilter(logging.Filter):
    def filter(self, record):
        record.request_id = getattr(record, 'request_id', 'unknown')
        return True

logger.addFilter(RequestContextFilter())


class APIHandler:
    """
    Main API handler class for processing Lambda requests.
    """
    
    def __init__(self):
        """Initialize the API handler with required services."""
        self.job_service = JobService()
        
    def create_response(
        self, 
        status_code: int, 
        body: Any, 
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Create a standardized API Gateway response.
        
        Args:
            status_code: HTTP status code
            body: Response body (will be JSON serialized)
            headers: Optional additional headers
            
        Returns:
            API Gateway response dictionary
        """
        default_headers = {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,X-Api-Key,X-Amz-Security-Token',
            'Access-Control-Allow-Methods': 'GET,OPTIONS'
        }
        
        if headers:
            default_headers.update(headers)
        
        # Ensure body is JSON serializable
        if hasattr(body, 'dict'):
            # Pydantic model
            body_json = body.json()
        elif isinstance(body, dict):
            body_json = json.dumps(body, default=str)
        else:
            body_json = json.dumps(body, default=str)
        
        return {
            'statusCode': status_code,
            'headers': default_headers,
            'body': body_json
        }
    
    def create_error_response(
        self, 
        status_code: int, 
        error_type: str, 
        message: str
    ) -> Dict[str, Any]:
        """
        Create a standardized error response.
        
        Args:
            status_code: HTTP status code
            error_type: Error type identifier
            message: Human-readable error message
            
        Returns:
            API Gateway error response
            
        Requirements: 7.1 - Appropriate error messages and HTTP status codes
        """
        error_response = ErrorResponse(
            error=error_type,
            message=message,
            timestamp=datetime.utcnow().isoformat()
        )
        
        return self.create_response(status_code, error_response)
    
    def parse_query_parameters(self, event: Dict[str, Any]) -> JobFilters:
        """
        Parse and validate query parameters from API Gateway event.
        
        Args:
            event: API Gateway event dictionary
            
        Returns:
            JobFilters object with parsed parameters
            
        Raises:
            ValueError: If parameters are invalid
            
        Requirements: 2.1, 2.2, 2.3 - Filter parameter parsing and validation
        """
        query_params = event.get('queryStringParameters') or {}
        
        # Parse individual parameters with type conversion
        filters_data = {}
        
        if 'published_after' in query_params:
            filters_data['published_after'] = query_params['published_after']
        
        if 'min_experience' in query_params:
            try:
                filters_data['min_experience'] = int(query_params['min_experience'])
            except ValueError:
                raise ValueError("min_experience must be a valid integer")
        
        if 'max_experience' in query_params:
            try:
                filters_data['max_experience'] = int(query_params['max_experience'])
            except ValueError:
                raise ValueError("max_experience must be a valid integer")
        
        if 'city' in query_params:
            filters_data['city'] = query_params['city'].strip()
        
        # Create and validate JobFilters object
        try:
            return JobFilters(**filters_data)
        except Exception as e:
            raise ValueError(f"Invalid filter parameters: {str(e)}")
    
    def handle_jobs_get(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle GET /jobs endpoint requests.
        
        Args:
            event: API Gateway event dictionary
            
        Returns:
            API Gateway response dictionary
            
        Requirements: 1.1, 2.1, 2.2, 2.3 - Job listing with filtering
        """
        try:
            # Parse query parameters
            filters = self.parse_query_parameters(event)
            
            # Get pagination parameters
            query_params = event.get('queryStringParameters') or {}
            page_size = min(int(query_params.get('limit', 50)), 100)
            page_token = query_params.get('next_token')
            
            # Query jobs using the service
            jobs_response = self.job_service.get_jobs_with_pagination(
                filters=filters,
                page_size=page_size,
                page_token=page_token
            )
            
            logger.info(f"Successfully retrieved {len(jobs_response.jobs)} jobs with filters: {filters.dict(exclude_none=True)}")
            
            return self.create_response(200, jobs_response)
            
        except ValueError as e:
            logger.warning(f"Invalid request parameters: {str(e)}")
            return self.create_error_response(400, "INVALID_PARAMETERS", str(e))
        
        except ClientError as e:
            logger.error(f"DynamoDB error: {str(e)}")
            error_code = e.response.get('Error', {}).get('Code', 'UnknownError')
            
            if error_code in ['ResourceNotFoundException', 'TableNotFoundException']:
                return self.create_error_response(503, "SERVICE_UNAVAILABLE", "Job database is temporarily unavailable")
            else:
                return self.create_error_response(500, "DATABASE_ERROR", "Database operation failed")
        
        except Exception as e:
            logger.error(f"Unexpected error in jobs GET handler: {str(e)}")
            logger.error(traceback.format_exc())
            return self.create_error_response(500, "INTERNAL_ERROR", "An unexpected error occurred")
    
    def handle_options(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle OPTIONS requests for CORS preflight.
        
        Args:
            event: API Gateway event dictionary
            
        Returns:
            API Gateway response dictionary with CORS headers
        """
        return self.create_response(200, {})
    
    def handle_health_check(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle health check requests.
        
        Args:
            event: API Gateway event dictionary
            
        Returns:
            API Gateway response dictionary with health status
        """
        try:
            # Check database connectivity
            db_healthy = self.job_service.health_check()
            
            health_status = {
                'status': 'healthy' if db_healthy else 'unhealthy',
                'timestamp': datetime.utcnow().isoformat(),
                'services': {
                    'database': 'healthy' if db_healthy else 'unhealthy'
                }
            }
            
            status_code = 200 if db_healthy else 503
            return self.create_response(status_code, health_status)
            
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            health_status = {
                'status': 'unhealthy',
                'timestamp': datetime.utcnow().isoformat(),
                'error': str(e)
            }
            return self.create_response(503, health_status)


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Main Lambda function handler for API Gateway requests.
    
    Args:
        event: API Gateway event dictionary
        context: Lambda context object
        
    Returns:
        API Gateway response dictionary
        
    Requirements: 1.1, 7.1 - API endpoint with API Key authentication and error handling
    """
    # Extract request ID for correlation
    request_id = context.aws_request_id if context else 'unknown'
    
    # Add request ID to logger context
    extra = {'request_id': request_id}
    
    # Log request start with key information
    logger.info(
        "API request started",
        extra={
            **extra,
            'http_method': event.get('httpMethod'),
            'resource_path': event.get('resource'),
            'source_ip': event.get('requestContext', {}).get('identity', {}).get('sourceIp'),
            'user_agent': event.get('headers', {}).get('User-Agent', 'unknown')
        }
    )
    
    start_time = datetime.utcnow()
    
    try:
        # Initialize handler
        handler = APIHandler()
        
        # Extract request information
        http_method = event.get('httpMethod', '').upper()
        resource_path = event.get('resource', '')
        
        # Handle CORS preflight requests
        if http_method == 'OPTIONS':
            response = handler.handle_options(event)
        # Handle health check
        elif resource_path == '/health':
            response = handler.handle_health_check(event)
        # Route to appropriate handler based on method and path
        elif resource_path == '/jobs' and http_method == 'GET':
            response = handler.handle_jobs_get(event)
        else:
            response = handler.create_error_response(
                404, 
                "NOT_FOUND", 
                f"Endpoint {http_method} {resource_path} not found"
            )
        
        # Log successful response
        duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
        logger.info(
            "API request completed successfully",
            extra={
                **extra,
                'status_code': response.get('statusCode'),
                'duration_ms': duration_ms,
                'memory_used_mb': getattr(context, 'memory_limit_in_mb', 0) if context else 0
            }
        )
        
        return response
    
    except Exception as e:
        # Log error with full context
        duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
        logger.error(
            "Unhandled error in lambda_handler",
            extra={
                **extra,
                'error_type': type(e).__name__,
                'error_message': str(e),
                'duration_ms': duration_ms,
                'traceback': traceback.format_exc()
            }
        )
        
        # Create a minimal error response
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'X-Request-ID': request_id
            },
            'body': json.dumps({
                'error': 'INTERNAL_ERROR',
                'message': 'An unexpected error occurred',
                'timestamp': datetime.utcnow().isoformat(),
                'request_id': request_id
            })
        }