import boto3
from botocore.exceptions import ClientError, BotoCoreError
import logging
from src.shared.models import JobModel
from typing import List, Dict, Any
import asyncio
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger()
logger.setLevel(logging.INFO)

class DynamoDBBatchWriter:
    def __init__(self, table_name='JobTable', endpoint_url=''):
        self.table_name = table_name
        self.endpoint_url = endpoint_url
        self.dynamodb = None
        self.table = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize DynamoDB client and table resource."""
        try:
            self.dynamodb = boto3.resource('dynamodb', endpoint_url=self.endpoint_url)
            self.table = self.dynamodb.Table(self.table_name)
            logger.info(f"[db_writer] Initialized DynamoDB client for table: {self.table_name}")
        except Exception as e:
            logger.error(f"[db_writer] Failed to initialize DynamoDB client: {e}")
            raise

    async def batch_write_jobs(self, job_records: List[JobModel]) -> Dict[str, Any]:
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
                    logger.error(f"[db_writer] Batch write failed: {result}")
                else:
                    success_count += result.get('success_count', 0)
                    error_count += result.get('error_count', 0)
                    errors.extend(result.get('errors', []))
        
        logger.info(f"[db_writer] Batch write completed: {success_count} success, {error_count} errors")
        return {
            'success_count': success_count,
            'error_count': error_count,
            'errors': errors
        }
    
    def _write_batch(self, job_records: List[JobModel]) -> Dict[str, Any]:
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
            
            logger.debug(f"[db_writer] Successfully wrote batch of {len(job_records)} jobs")
            return {
                'success_count': len(job_records),
                'error_count': 0,
                'errors': []
            }
            
        except ClientError as e:
            error_msg = f"[db_writer] DynamoDB ClientError: {e.response['Error']['Message']}"
            logger.error(error_msg)
            return {
                'success_count': 0,
                'error_count': len(job_records),
                'errors': [error_msg]
            }
        except BotoCoreError as e:
            error_msg = f"[db_writer] DynamoDB BotoCoreError: {str(e)}"
            logger.error(error_msg)
            return {
                'success_count': 0,
                'error_count': len(job_records),
                'errors': [error_msg]
            }
        except Exception as e:
            error_msg = f"[db_writer] Unexpected error writing batch: {str(e)}"
            logger.error(error_msg)
            return {
                'success_count': 0,
                'error_count': len(job_records),
                'errors': [error_msg]
            }