import asyncio
import time
import logging
import sys
from typing import Any, Dict
from src.apiclient.adzuna import AdzunaApiClient
from src.apiclient.mapper import JobMapper
from src.apiclient.db_writer import DynamoDBBatchWriter

# Configure logging for better visibility
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    logger.info("[lambda_handler] Lambda Handler Started")
    logger.info('[lambda_handler] event: {}'.format(event))
    logger.info('[lambda_handler] context: {}'.format(context))

    adzuna_client = AdzunaApiClient()
    job_mapper = JobMapper()

    # Get endpoint_url from event
    endpoint_url = event.get('endpoint_url', '')
    db_writer = DynamoDBBatchWriter(endpoint_url=endpoint_url)
    
    logger.info(f"[lambda_handler] Using endpoint_url: {endpoint_url}")

    async def async_handler():
        logger.info("[lambda_handler] Starting async handler")
        all_jobs = []
        response = await adzuna_client.call_api()
        if response:
            logger.info(f"[lambda_handler] Got API response with {response.get('count', 0)} total jobs")
            jobs = job_mapper.map_adzuna_job(response)
            logger.info(f"[lambda_handler] Mapped {len(jobs)} jobs")
            all_jobs.extend(jobs)
            result = await db_writer.batch_write_jobs(jobs)
            logger.info(f"[lambda_handler] Database write result: {result}")
            logger.info(f"[lambda_handler] Added {len(jobs)} jobs to DynamoDB")
        else:
            logger.warning("[lambda_handler] No response from API")

    logger.info("[lambda_handler] Running async handler")
    asyncio.run(async_handler())
    logger.info("[lambda_handler] Lambda Handler Completed")

    return {
        'statusCode': 200,
        'body': f'Successfully processed jobs'
    }

def test_locally():
    event = {
        'endpoint_url': 'http://localhost:8000'
    }
    handler(event, None)

if __name__ == "__main__":
    test_locally()