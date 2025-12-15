"""
Job data processing and storage module for the regulatory jobs scraper.

This module handles job deduplication, data validation, DynamoDB batch operations,
and async processing pipeline for concurrent job processing.
"""

import asyncio
import hashlib
import logging
from typing import List, Dict, Any, Optional, Set
from datetime import datetime
import boto3
from botocore.exceptions import ClientError, BotoCoreError
from concurrent.futures import ThreadPoolExecutor

from ..shared.models import JobRecord
from ..shared.validation import validate_ile_de_france_city, normalize_date

logger = logging.getLogger(__name__)


class JobDeduplicator:
    """Handles job deduplication using URL hashing."""
    
    def __init__(self):
        self.seen_urls: Set[str] = set()
        self.url_to_job_id: Dict[str, str] = {}
    
    def generate_job_id(self, url: str) -> str:
        """Generate a unique job ID from URL using SHA-256 hash."""
        # Normalize URL by removing query parameters and fragments
        clean_url = url.split('?')[0].split('#')[0].strip().lower()
        
        # Generate hash
        hash_object = hashlib.sha256(clean_url.encode('utf-8'))
        job_id = hash_object.hexdigest()[:16]  # Use first 16 characters
        
        return job_id
    
    def is_duplicate(self, url: str) -> bool:
        """Check if a job URL has already been processed."""
        clean_url = url.split('?')[0].split('#')[0].strip().lower()
        return clean_url in self.seen_urls
    
    def add_job(self, url: str) -> str:
        """Add a job URL to the deduplication set and return job ID."""
        clean_url = url.split('?')[0].split('#')[0].strip().lower()
        job_id = self.generate_job_id(url)
        
        self.seen_urls.add(clean_url)
        self.url_to_job_id[clean_url] = job_id
        
        return job_id
    
    def get_job_id(self, url: str) -> Optional[str]:
        """Get job ID for a URL if it exists."""
        clean_url = url.split('?')[0].split('#')[0].strip().lower()
        return self.url_to_job_id.get(clean_url)


class JobValidator:
    """Validates and normalizes job data."""
    
    @staticmethod
    def validate_job_data(job_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Validate and normalize job data.
        
        Args:
            job_data: Raw job data dictionary
            
        Returns:
            Validated and normalized job data, or None if invalid
        """
        try:
            # Required fields check
            required_fields = ['job_title', 'company_name', 'link', 'source']
            for field in required_fields:
                if not job_data.get(field):
                    logger.warning(f"Missing required field '{field}' in job data")
                    return None
            
            # Normalize and validate data
            normalized_data = {
                'job_title': str(job_data['job_title']).strip(),
                'company_name': str(job_data['company_name']).strip(),
                'link': str(job_data['link']).strip(),
                'source': str(job_data['source']).strip(),
            }
            
            # Validate URL format
            if not (normalized_data['link'].startswith('http://') or 
                   normalized_data['link'].startswith('https://')):
                logger.warning(f"Invalid URL format: {normalized_data['link']}")
                return None
            
            # Handle city - validate if provided, default to Paris if missing
            city = job_data.get('city', 'Paris')
            if city and validate_ile_de_france_city(city):
                normalized_data['city'] = city
            else:
                logger.warning(f"Invalid or missing city: {city}, defaulting to Paris")
                normalized_data['city'] = 'Paris'
            
            # Handle experience years
            experience = job_data.get('year_of_experience', 0)
            try:
                experience_int = int(experience) if experience is not None else 0
                if 0 <= experience_int <= 50:
                    normalized_data['year_of_experience'] = experience_int
                else:
                    normalized_data['year_of_experience'] = 0
            except (ValueError, TypeError):
                normalized_data['year_of_experience'] = 0
            
            # Handle published date
            pub_date = job_data.get('published_date')
            if pub_date:
                try:
                    normalized_data['published_date'] = normalize_date(pub_date)
                except Exception:
                    normalized_data['published_date'] = datetime.now().isoformat()
            else:
                normalized_data['published_date'] = datetime.now().isoformat()
            
            # Optional fields
            normalized_data['description'] = job_data.get('description', '')
            normalized_data['salary_range'] = job_data.get('salary_range', '')
            
            # Add timestamps
            now = datetime.now().isoformat()
            normalized_data['created_at'] = now
            normalized_data['updated_at'] = now
            
            return normalized_data
            
        except Exception as e:
            logger.error(f"Error validating job data: {e}")
            return None
    
    @staticmethod
    def create_job_record(job_data: Dict[str, Any], job_id: str) -> Optional[JobRecord]:
        """
        Create a JobRecord instance from validated job data.
        
        Args:
            job_data: Validated job data dictionary
            job_id: Unique job identifier
            
        Returns:
            JobRecord instance or None if creation failed
        """
        try:
            job_data['job_id'] = job_id
            return JobRecord(**job_data)
        except Exception as e:
            logger.error(f"Error creating JobRecord: {e}")
            return None


class DynamoDBBatchWriter:
    """Handles DynamoDB batch write operations."""
    
    def __init__(self, table_name: str, region_name: str = 'eu-west-3'):
        self.table_name = table_name
        self.region_name = region_name
        self.dynamodb = None
        self.table = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize DynamoDB client and table resource."""
        try:
            self.dynamodb = boto3.resource('dynamodb', region_name=self.region_name)
            self.table = self.dynamodb.Table(self.table_name)
            logger.info(f"Initialized DynamoDB client for table: {self.table_name}")
        except Exception as e:
            logger.error(f"Failed to initialize DynamoDB client: {e}")
            raise
    
    async def batch_write_jobs(self, job_records: List[JobRecord]) -> Dict[str, Any]:
        """
        Write job records to DynamoDB in batches of 25.
        
        Args:
            job_records: List of JobRecord instances to write
            
        Returns:
            Dictionary with write statistics
        """
        if not job_records:
            return {'success_count': 0, 'error_count': 0, 'errors': []}
        
        # Split into batches of 25 (DynamoDB limit)
        batch_size = 25
        batches = [job_records[i:i + batch_size] for i in range(0, len(job_records), batch_size)]
        
        success_count = 0
        error_count = 0
        errors = []
        
        # Use ThreadPoolExecutor for async DynamoDB operations
        with ThreadPoolExecutor(max_workers=5) as executor:
            # Create tasks for each batch
            tasks = []
            for batch in batches:
                task = asyncio.get_event_loop().run_in_executor(
                    executor, self._write_batch, batch
                )
                tasks.append(task)
            
            # Wait for all batches to complete
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            for result in results:
                if isinstance(result, Exception):
                    error_count += 1
                    errors.append(str(result))
                    logger.error(f"Batch write failed: {result}")
                else:
                    success_count += result.get('success_count', 0)
                    error_count += result.get('error_count', 0)
                    errors.extend(result.get('errors', []))
        
        logger.info(f"Batch write completed: {success_count} success, {error_count} errors")
        return {
            'success_count': success_count,
            'error_count': error_count,
            'errors': errors
        }
    
    def _write_batch(self, job_records: List[JobRecord]) -> Dict[str, Any]:
        """
        Write a single batch of job records to DynamoDB.
        
        Args:
            job_records: List of JobRecord instances (max 25)
            
        Returns:
            Dictionary with batch write results
        """
        if not self.table:
            raise RuntimeError("DynamoDB table not initialized")
        
        try:
            # Prepare batch write items
            with self.table.batch_writer() as batch:
                for job_record in job_records:
                    # Convert JobRecord to dict for DynamoDB
                    item = job_record.dict()
                    batch.put_item(Item=item)
            
            logger.debug(f"Successfully wrote batch of {len(job_records)} jobs")
            return {
                'success_count': len(job_records),
                'error_count': 0,
                'errors': []
            }
            
        except ClientError as e:
            error_msg = f"DynamoDB ClientError: {e.response['Error']['Message']}"
            logger.error(error_msg)
            return {
                'success_count': 0,
                'error_count': len(job_records),
                'errors': [error_msg]
            }
        except BotoCoreError as e:
            error_msg = f"DynamoDB BotoCoreError: {str(e)}"
            logger.error(error_msg)
            return {
                'success_count': 0,
                'error_count': len(job_records),
                'errors': [error_msg]
            }
        except Exception as e:
            error_msg = f"Unexpected error writing batch: {str(e)}"
            logger.error(error_msg)
            return {
                'success_count': 0,
                'error_count': len(job_records),
                'errors': [error_msg]
            }
    
    async def check_existing_jobs(self, job_ids: List[str]) -> Set[str]:
        """
        Check which job IDs already exist in DynamoDB.
        
        Args:
            job_ids: List of job IDs to check
            
        Returns:
            Set of existing job IDs
        """
        existing_ids = set()
        
        try:
            # Use ThreadPoolExecutor for async DynamoDB operations
            with ThreadPoolExecutor(max_workers=3) as executor:
                # Split job_ids into chunks for batch get operations
                chunk_size = 100  # DynamoDB batch_get_item limit
                chunks = [job_ids[i:i + chunk_size] for i in range(0, len(job_ids), chunk_size)]
                
                tasks = []
                for chunk in chunks:
                    task = asyncio.get_event_loop().run_in_executor(
                        executor, self._check_existing_batch, chunk
                    )
                    tasks.append(task)
                
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                for result in results:
                    if isinstance(result, Exception):
                        logger.error(f"Error checking existing jobs: {result}")
                    elif isinstance(result, set):
                        existing_ids.update(result)
            
        except Exception as e:
            logger.error(f"Error checking existing jobs: {e}")
        
        return existing_ids
    
    def _check_existing_batch(self, job_ids: List[str]) -> Set[str]:
        """Check a batch of job IDs for existence in DynamoDB."""
        existing_ids = set()
        
        try:
            # Prepare batch get request
            request_items = {
                self.table_name: {
                    'Keys': [{'job_id': job_id} for job_id in job_ids],
                    'ProjectionExpression': 'job_id'
                }
            }
            
            response = self.dynamodb.batch_get_item(RequestItems=request_items)
            
            # Extract existing job IDs
            items = response.get('Responses', {}).get(self.table_name, [])
            for item in items:
                existing_ids.add(item['job_id'])
            
        except Exception as e:
            logger.error(f"Error in batch get operation: {e}")
        
        return existing_ids


class JobProcessor:
    """Main job processing pipeline coordinator."""
    
    def __init__(self, table_name: str, region_name: str = 'eu-west-3'):
        self.deduplicator = JobDeduplicator()
        self.validator = JobValidator()
        self.db_writer = DynamoDBBatchWriter(table_name, region_name)
    
    async def process_scraped_jobs(self, scraped_jobs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Process scraped jobs through the complete pipeline.
        
        Args:
            scraped_jobs: List of raw job data dictionaries from scrapers
            
        Returns:
            Processing statistics dictionary
        """
        logger.info(f"Starting job processing pipeline for {len(scraped_jobs)} jobs")
        
        stats = {
            'total_scraped': len(scraped_jobs),
            'duplicates_filtered': 0,
            'validation_failed': 0,
            'new_jobs': 0,
            'updated_jobs': 0,
            'db_write_success': 0,
            'db_write_errors': 0,
            'errors': []
        }
        
        try:
            # Step 1: Deduplicate and validate jobs
            valid_jobs = []
            job_id_mapping = {}
            
            for job_data in scraped_jobs:
                # Check for duplicates
                job_url = job_data.get('link', '')
                if not job_url:
                    stats['validation_failed'] += 1
                    continue
                
                if self.deduplicator.is_duplicate(job_url):
                    stats['duplicates_filtered'] += 1
                    continue
                
                # Validate job data
                validated_data = self.validator.validate_job_data(job_data)
                if not validated_data:
                    stats['validation_failed'] += 1
                    continue
                
                # Generate job ID and add to deduplicator
                job_id = self.deduplicator.add_job(job_url)
                job_id_mapping[job_id] = validated_data
                valid_jobs.append((job_id, validated_data))
            
            logger.info(f"Validation completed: {len(valid_jobs)} valid jobs")
            
            # Step 2: Check which jobs already exist in database
            job_ids = [job_id for job_id, _ in valid_jobs]
            existing_job_ids = await self.db_writer.check_existing_jobs(job_ids)
            
            # Step 3: Separate new jobs from updates
            new_job_records = []
            updated_job_records = []
            
            for job_id, job_data in valid_jobs:
                job_record = self.validator.create_job_record(job_data, job_id)
                if not job_record:
                    stats['validation_failed'] += 1
                    continue
                
                if job_id in existing_job_ids:
                    # Update existing job's updated_at timestamp
                    job_record.updated_at = datetime.now().isoformat()
                    updated_job_records.append(job_record)
                    stats['updated_jobs'] += 1
                else:
                    new_job_records.append(job_record)
                    stats['new_jobs'] += 1
            
            # Step 4: Write to DynamoDB
            all_records = new_job_records + updated_job_records
            if all_records:
                write_result = await self.db_writer.batch_write_jobs(all_records)
                stats['db_write_success'] = write_result['success_count']
                stats['db_write_errors'] = write_result['error_count']
                stats['errors'].extend(write_result['errors'])
            
            logger.info(f"Job processing completed: {stats}")
            return stats
            
        except Exception as e:
            error_msg = f"Error in job processing pipeline: {str(e)}"
            logger.error(error_msg)
            stats['errors'].append(error_msg)
            return stats