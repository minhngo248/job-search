"""
Main Lambda handler for the job scraper function.

This module orchestrates all scrapers and handles the complete job scraping workflow
triggered by EventBridge Scheduler.
"""

import asyncio
import logging
import os
import json
import traceback
from datetime import datetime
from typing import Dict, Any, List

from .web_utils import AsyncWebScraper
from .linkedin_scraper import LinkedInScraper
from .glassdoor_scraper import GlassdoorScraper
from .specialized_scrapers import SpecializedScrapersManager
from .job_processor import JobProcessor

# Configure structured logging with CloudWatch integration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Custom metrics for CloudWatch
class CloudWatchMetrics:
    """Helper class for sending custom metrics to CloudWatch."""
    
    def __init__(self):
        try:
            import boto3
            self.cloudwatch = boto3.client('cloudwatch')
            self.namespace = 'RegulatoryJobs/Scraper'
        except Exception as e:
            logger.warning(f"Failed to initialize CloudWatch metrics: {e}")
            self.cloudwatch = None
    
    def put_metric(self, metric_name: str, value: float, unit: str = 'Count', dimensions: Dict[str, str] = None):
        """Send a custom metric to CloudWatch."""
        if not self.cloudwatch:
            return
        
        try:
            metric_data = {
                'MetricName': metric_name,
                'Value': value,
                'Unit': unit
            }
            
            if dimensions:
                metric_data['Dimensions'] = [
                    {'Name': k, 'Value': v} for k, v in dimensions.items()
                ]
            
            self.cloudwatch.put_metric_data(
                Namespace=self.namespace,
                MetricData=[metric_data]
            )
        except Exception as e:
            logger.warning(f"Failed to send metric {metric_name}: {e}")

# Global metrics instance
metrics = CloudWatchMetrics()


class ScraperOrchestrator:
    """Orchestrates all job scrapers and processing."""
    
    def __init__(self, table_name: str, region_name: str = 'eu-west-3'):
        self.table_name = table_name
        self.region_name = region_name
        
        # Initialize scrapers
        self.linkedin_scraper = LinkedInScraper()
        self.glassdoor_scraper = GlassdoorScraper()
        self.specialized_scrapers = SpecializedScrapersManager()
        
        # Initialize job processor
        self.job_processor = JobProcessor(table_name, region_name)
    
    async def run_all_scrapers(self) -> Dict[str, Any]:
        """
        Run all scrapers concurrently and process results.
        
        Returns:
            Dictionary with scraping and processing statistics
        """
        start_time = datetime.utcnow()
        logger.info("Starting comprehensive job scraping process")
        
        results = {
            'scraping_stats': {},
            'processing_stats': {},
            'total_jobs_scraped': 0,
            'total_jobs_processed': 0,
            'errors': [],
            'execution_time_seconds': 0,
            'start_time': start_time.isoformat()
        }
        
        try:
            # Initialize web scraper with appropriate settings
            async with AsyncWebScraper(
                max_concurrent_per_source=3,
                request_timeout=30
            ) as scraper:
                
                # Run all scrapers concurrently
                logger.info("Starting concurrent scraping from all sources")
                
                scraping_tasks = [
                    self._run_scraper_with_error_handling(
                        'linkedin', self.linkedin_scraper.scrape_jobs(scraper)
                    ),
                    self._run_scraper_with_error_handling(
                        'glassdoor', self.glassdoor_scraper.scrape_jobs(scraper)
                    ),
                    self._run_scraper_with_error_handling(
                        'specialized', self.specialized_scrapers.scrape_all_specialized_sites(scraper)
                    )
                ]
                
                # Wait for all scrapers to complete
                scraping_results = await asyncio.gather(*scraping_tasks, return_exceptions=True)
                
                # Collect all scraped jobs
                all_scraped_jobs = []
                
                for i, result in enumerate(scraping_results):
                    scraper_name = ['linkedin', 'glassdoor', 'specialized'][i]
                    
                    if isinstance(result, Exception):
                        error_msg = f"Scraper '{scraper_name}' failed: {str(result)}"
                        logger.error(error_msg)
                        results['errors'].append(error_msg)
                        results['scraping_stats'][scraper_name] = {
                            'jobs_found': 0,
                            'success': False,
                            'error': str(result)
                        }
                    elif isinstance(result, dict) and 'jobs' in result:
                        jobs = result['jobs']
                        all_scraped_jobs.extend(jobs)
                        results['scraping_stats'][scraper_name] = {
                            'jobs_found': len(jobs),
                            'success': result.get('success', True),
                            'error': result.get('error')
                        }
                        logger.info(f"Scraper '{scraper_name}' found {len(jobs)} jobs")
                    elif isinstance(result, list):
                        all_scraped_jobs.extend(result)
                        results['scraping_stats'][scraper_name] = {
                            'jobs_found': len(result),
                            'success': True,
                            'error': None
                        }
                        logger.info(f"Scraper '{scraper_name}' found {len(result)} jobs")
                
                results['total_jobs_scraped'] = len(all_scraped_jobs)
                logger.info(f"Total jobs scraped from all sources: {len(all_scraped_jobs)}")
                
                # Process all scraped jobs
                if all_scraped_jobs:
                    logger.info("Starting job processing pipeline")
                    processing_stats = await self.job_processor.process_scraped_jobs(all_scraped_jobs)
                    results['processing_stats'] = processing_stats
                    results['total_jobs_processed'] = processing_stats.get('db_write_success', 0)
                    
                    if processing_stats.get('errors'):
                        results['errors'].extend(processing_stats['errors'])
                else:
                    logger.warning("No jobs were scraped from any source")
                    results['processing_stats'] = {
                        'total_scraped': 0,
                        'new_jobs': 0,
                        'updated_jobs': 0,
                        'db_write_success': 0,
                        'errors': ['No jobs scraped from any source']
                    }
        
        except Exception as e:
            error_msg = f"Critical error in scraper orchestrator: {str(e)}"
            logger.error(error_msg, exc_info=True)
            results['errors'].append(error_msg)
            
            # Send error metric to CloudWatch
            metrics.put_metric('ScrapingErrors', 1, 'Count', {'ErrorType': 'CriticalError'})
        
        # Calculate execution time and send metrics
        end_time = datetime.utcnow()
        execution_time = (end_time - start_time).total_seconds()
        results['execution_time_seconds'] = execution_time
        results['end_time'] = end_time.isoformat()
        
        # Send performance metrics to CloudWatch
        metrics.put_metric('ExecutionTime', execution_time, 'Seconds')
        metrics.put_metric('JobsScraped', results['total_jobs_scraped'], 'Count')
        metrics.put_metric('JobsProcessed', results['total_jobs_processed'], 'Count')
        metrics.put_metric('ErrorCount', len(results['errors']), 'Count')
        
        # Send per-source metrics
        for source, stats in results['scraping_stats'].items():
            metrics.put_metric(
                'JobsScrapedBySource', 
                stats.get('jobs_found', 0), 
                'Count', 
                {'Source': source}
            )
            if not stats.get('success', True):
                metrics.put_metric(
                    'SourceErrors', 
                    1, 
                    'Count', 
                    {'Source': source}
                )
        
        logger.info(f"Scraping process completed in {execution_time:.2f}s: {results}")
        return results
    
    async def _run_scraper_with_error_handling(self, scraper_name: str, scraper_task) -> Dict[str, Any]:
        """
        Run a scraper with error handling and return structured results.
        
        Args:
            scraper_name: Name of the scraper for logging
            scraper_task: Async task that returns list of jobs
            
        Returns:
            Dictionary with jobs and metadata
        """
        try:
            jobs = await scraper_task
            return {
                'jobs': jobs if isinstance(jobs, list) else [],
                'success': True,
                'error': None
            }
        except Exception as e:
            logger.error(f"Error in {scraper_name} scraper: {e}")
            return {
                'jobs': [],
                'success': False,
                'error': str(e)
            }


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    AWS Lambda handler for the job scraper function.
    
    This function is triggered by EventBridge Scheduler and orchestrates
    the complete job scraping and storage process.
    
    Args:
        event: Lambda event data (from EventBridge)
        context: Lambda context object
        
    Returns:
        Dictionary with execution results and statistics
    """
    # Extract execution context
    request_id = context.aws_request_id if context else 'unknown'
    function_name = context.function_name if context else 'unknown'
    memory_limit = context.memory_limit_in_mb if context else 0
    
    start_time = datetime.utcnow()
    
    logger.info(
        "Job scraper Lambda function started",
        extra={
            'request_id': request_id,
            'function_name': function_name,
            'memory_limit_mb': memory_limit,
            'event_source': event.get('source', 'unknown')
        }
    )
    
    # Get configuration from environment variables
    table_name = os.environ.get('JOBS_TABLE_NAME', 'regulatory-jobs')
    region_name = os.environ.get('AWS_REGION', 'eu-west-3')
    
    logger.info(f"Configuration: table_name={table_name}, region={region_name}")
    
    try:
        # Create orchestrator and run scraping process
        orchestrator = ScraperOrchestrator(table_name, region_name)
        
        # Run the async scraping process
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            results = loop.run_until_complete(orchestrator.run_all_scrapers())
        finally:
            loop.close()
        
        # Calculate execution metrics
        end_time = datetime.utcnow()
        execution_duration = (end_time - start_time).total_seconds()
        remaining_time_ms = getattr(context, 'get_remaining_time_in_millis', lambda: 0)()
        
        # Log success metrics
        logger.info(
            "Job scraper Lambda function completed successfully",
            extra={
                'request_id': request_id,
                'execution_duration_seconds': execution_duration,
                'remaining_time_ms': remaining_time_ms,
                'jobs_scraped': results.get('total_jobs_scraped', 0),
                'jobs_processed': results.get('total_jobs_processed', 0),
                'error_count': len(results.get('errors', []))
            }
        )
        
        # Send success metrics to CloudWatch
        metrics.put_metric('LambdaExecutions', 1, 'Count', {'Status': 'Success'})
        metrics.put_metric('LambdaExecutionDuration', execution_duration, 'Seconds')
        
        # Prepare response
        response = {
            'statusCode': 200,
            'body': {
                'message': 'Job scraping completed successfully',
                'results': results,
                'execution_context': {
                    'request_id': request_id,
                    'execution_duration_seconds': execution_duration,
                    'remaining_time_ms': remaining_time_ms,
                    'memory_limit_mb': memory_limit
                }
            }
        }
        
        return response
        
    except Exception as e:
        # Calculate execution time for error case
        end_time = datetime.utcnow()
        execution_duration = (end_time - start_time).total_seconds()
        remaining_time_ms = getattr(context, 'get_remaining_time_in_millis', lambda: 0)()
        
        error_msg = f"Critical error in Lambda handler: {str(e)}"
        logger.error(
            error_msg,
            extra={
                'request_id': request_id,
                'execution_duration_seconds': execution_duration,
                'remaining_time_ms': remaining_time_ms,
                'error_type': type(e).__name__,
                'traceback': traceback.format_exc()
            }
        )
        
        # Send error metrics to CloudWatch
        metrics.put_metric('LambdaExecutions', 1, 'Count', {'Status': 'Error'})
        metrics.put_metric('LambdaErrors', 1, 'Count', {'ErrorType': type(e).__name__})
        
        response = {
            'statusCode': 500,
            'body': {
                'message': 'Job scraping failed',
                'error': error_msg,
                'execution_context': {
                    'request_id': request_id,
                    'execution_duration_seconds': execution_duration,
                    'remaining_time_ms': remaining_time_ms,
                    'memory_limit_mb': memory_limit
                }
            }
        }
        
        return response


# For local testing
async def test_scraper_locally():
    """Test function for local development."""
    import os
    
    # Set test environment variables
    os.environ['DYNAMODB_TABLE_NAME'] = 'test-regulatory-jobs-table'
    os.environ['AWS_REGION'] = 'eu-west-3'
    
    # Create mock context
    class MockContext:
        def get_remaining_time_in_millis(self):
            return 300000  # 5 minutes
    
    # Test the handler
    test_event = {
        'source': 'aws.scheduler',
        'detail-type': 'Scheduled Event',
        'detail': {}
    }
    
    result = lambda_handler(test_event, MockContext())
    print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    # Run local test
    asyncio.run(test_scraper_locally())