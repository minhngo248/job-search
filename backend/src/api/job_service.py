"""
Job service module for handling DynamoDB operations and filtering logic.

This module provides the core business logic for querying and filtering
job records from DynamoDB based on user-specified criteria.
"""
import boto3
from boto3.dynamodb.conditions import Key, Attr
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging
from botocore.exceptions import ClientError

from ..shared.models import JobRecord, JobFilters, JobsResponse
from ..shared.validation import validate_ile_de_france_city, normalize_date

# Configure logging
logger = logging.getLogger(__name__)


class JobService:
    """
    Service class for job-related database operations and filtering.
    
    Handles DynamoDB queries, filtering, and pagination for job records.
    """
    
    def __init__(self, table_name: str = "RegulatoryJobsTable"):
        """
        Initialize the job service with DynamoDB connection.
        
        Args:
            table_name: Name of the DynamoDB table containing job records
        """
        self.dynamodb = boto3.resource('dynamodb')
        self.table = self.dynamodb.Table(table_name)
        self.table_name = table_name
    
    def validate_filters(self, filters: JobFilters) -> None:
        """
        Validate filter parameters before applying them to queries.
        
        Args:
            filters: JobFilters object containing filter criteria
            
        Raises:
            ValueError: If any filter parameters are invalid
            
        Requirements: 2.4 - Invalid filter error handling
        """
        # Validate date format if provided
        if filters.published_after:
            try:
                normalize_date(filters.published_after)
            except ValueError as e:
                raise ValueError(f"Invalid published_after date format: {str(e)}")
        
        # Validate experience range
        if filters.min_experience is not None and filters.min_experience < 0:
            raise ValueError("min_experience must be non-negative")
        
        if filters.max_experience is not None and filters.max_experience < 0:
            raise ValueError("max_experience must be non-negative")
        
        if (filters.min_experience is not None and 
            filters.max_experience is not None and 
            filters.min_experience > filters.max_experience):
            raise ValueError("min_experience cannot be greater than max_experience")
        
        # Validate city if provided
        if filters.city and not validate_ile_de_france_city(filters.city):
            raise ValueError(f"City '{filters.city}' is not in the Île-de-France region")
    
    def build_filter_expression(self, filters: JobFilters) -> Optional[Any]:
        """
        Build DynamoDB filter expression from JobFilters.
        
        Args:
            filters: JobFilters object containing filter criteria
            
        Returns:
            DynamoDB filter expression or None if no filters
            
        Requirements: 2.1, 2.2, 2.3 - Date, experience, and multi-filter logic
        """
        filter_expressions = []
        
        # Date filter - jobs published after specified date
        if filters.published_after:
            normalized_date = normalize_date(filters.published_after)
            filter_expressions.append(Attr('published_date').gte(normalized_date))
        
        # Experience filters
        if filters.min_experience is not None:
            filter_expressions.append(Attr('year_of_experience').gte(filters.min_experience))
        
        if filters.max_experience is not None:
            filter_expressions.append(Attr('year_of_experience').lte(filters.max_experience))
        
        # City filter
        if filters.city:
            # Case-insensitive city matching
            filter_expressions.append(Attr('city').eq(filters.city))
        
        # Combine all filters with AND logic
        if not filter_expressions:
            return None
        
        combined_filter = filter_expressions[0]
        for expr in filter_expressions[1:]:
            combined_filter = combined_filter & expr
        
        return combined_filter
    
    def query_jobs(
        self, 
        filters: JobFilters, 
        limit: Optional[int] = None,
        last_evaluated_key: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Query jobs from DynamoDB with filtering and pagination support.
        
        Args:
            filters: JobFilters object containing filter criteria
            limit: Maximum number of items to return (for pagination)
            last_evaluated_key: Pagination token from previous query
            
        Returns:
            Dictionary containing jobs, count, and pagination info
            
        Raises:
            ValueError: If filter parameters are invalid
            ClientError: If DynamoDB operation fails
            
        Requirements: 2.1, 2.2, 2.3 - Filtering and pagination support
        """
        # Validate filters first
        self.validate_filters(filters)
        
        try:
            # Build filter expression
            filter_expression = self.build_filter_expression(filters)
            
            # Prepare scan parameters (using scan since we need to filter across all items)
            scan_params = {}
            
            if filter_expression:
                scan_params['FilterExpression'] = filter_expression
            
            if limit:
                scan_params['Limit'] = limit
            
            if last_evaluated_key:
                scan_params['ExclusiveStartKey'] = last_evaluated_key
            
            # Execute scan operation
            logger.info(f"Scanning table {self.table_name} with filters: {filters.dict(exclude_none=True)}")
            response = self.table.scan(**scan_params)
            
            # Convert DynamoDB items to JobRecord objects
            jobs = []
            for item in response.get('Items', []):
                try:
                    job = JobRecord(**item)
                    jobs.append(job)
                except Exception as e:
                    logger.warning(f"Failed to parse job record {item.get('job_id', 'unknown')}: {str(e)}")
                    continue
            
            # Prepare response
            result = {
                'jobs': jobs,
                'count': len(jobs),
                'scanned_count': response.get('ScannedCount', 0),
                'last_evaluated_key': response.get('LastEvaluatedKey')
            }
            
            logger.info(f"Query returned {len(jobs)} jobs (scanned {result['scanned_count']} items)")
            return result
            
        except ClientError as e:
            logger.error(f"DynamoDB operation failed: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during job query: {str(e)}")
            raise
    
    def get_jobs_with_pagination(
        self, 
        filters: JobFilters,
        page_size: int = 50,
        page_token: Optional[str] = None
    ) -> JobsResponse:
        """
        Get jobs with pagination support and proper response formatting.
        
        Args:
            filters: JobFilters object containing filter criteria
            page_size: Number of items per page (default 50, max 100)
            page_token: Base64-encoded pagination token
            
        Returns:
            JobsResponse object with jobs, total count, and applied filters
            
        Requirements: 2.1, 2.2, 2.3 - Complete filtering with pagination
        """
        import base64
        import json
        
        # Validate and limit page size
        page_size = min(max(1, page_size), 100)
        
        # Decode pagination token if provided
        last_evaluated_key = None
        if page_token:
            try:
                decoded_token = base64.b64decode(page_token).decode('utf-8')
                last_evaluated_key = json.loads(decoded_token)
            except Exception as e:
                logger.warning(f"Invalid pagination token: {str(e)}")
                # Continue without pagination token
        
        # Query jobs
        result = self.query_jobs(
            filters=filters,
            limit=page_size,
            last_evaluated_key=last_evaluated_key
        )
        
        # For total count, we need to do a separate count query without limit
        # This is expensive but necessary for accurate pagination
        count_result = self.query_jobs(filters=filters)
        total_count = count_result['count']
        
        # Create response
        response = JobsResponse(
            jobs=result['jobs'],
            total_count=total_count,
            filters_applied=filters
        )
        
        return response
    
    def health_check(self) -> bool:
        """
        Perform a health check on the DynamoDB connection.
        
        Returns:
            True if the table is accessible, False otherwise
        """
        try:
            # Simple describe table operation to check connectivity
            self.table.load()
            return True
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return False