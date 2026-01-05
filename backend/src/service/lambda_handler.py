import asyncio
import time
import logging
import sys
from typing import Any, Dict
from src.apiclient.adzuna import AdzunaApiClient
from src.scraper.linkedin import LinkedInClient
from src.service.mapper import JobMapper
from src.service.db_writer import DynamoDBBatchWriter

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

    # Adzuna parameters can be customized here or passed via event
    adzuna_what = event.get('adzuna_what', 'Affaires réglementaires')
    adzuna_what_and = event.get('adzuna_what_and', '')
    adzuna_where = event.get('adzuna_where', 'Île-de-France')
    adzuna_max_days_old = event.get('adzuna_max_days_old', 60)
    adzuna_salary_min = event.get('adzuna_salary_min', 46000)
    adzuna_salary_max = event.get('adzuna_salary_max', 70000)

    adzuna_client = AdzunaApiClient(adzuna_what, adzuna_where, adzuna_max_days_old, adzuna_salary_min, adzuna_salary_max, what_and=adzuna_what_and)

    # LinkedIn client can be initialized similarly if needed
    linkedin_keyword = event.get('linkedin_keyword', 'Affaires réglementaires')
    linkedin_location = event.get('linkedin_location', 'Île-de-France')

    linkedin_client = LinkedInClient(keyword=linkedin_keyword, location=linkedin_location)

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
            logger.info(f"[lambda_handler] Got Adzuna API response with {response.get('count', 0)} total jobs")
            jobs = job_mapper.map_adzuna_job(response)
            logger.info(f"[lambda_handler] Mapped {len(jobs)} Adzuna jobs")
            all_jobs.extend(jobs)
            result = await db_writer.batch_write_jobs(jobs)
            logger.info(f"[lambda_handler] Database write result: {result}")
            logger.info(f"[lambda_handler] Added {len(jobs)} jobs to DynamoDB")
        else:
            logger.warning("[lambda_handler] No response from AdzunaAPI")

        linkedin_response = await linkedin_client.call_api()
        if linkedin_response:
            logger.info(f"[lambda_handler] Got LinkedIn API response with {len(linkedin_response)} jobs")
            linkedin_jobs = job_mapper.map_linkedin_job(linkedin_response)
            logger.info(f"[lambda_handler] Mapped {len(linkedin_jobs)} LinkedIn jobs")
            all_jobs.extend(linkedin_jobs)
            linkedin_result = await db_writer.batch_write_jobs(linkedin_jobs)
            logger.info(f"[lambda_handler] LinkedIn Database write result: {linkedin_result}")
            logger.info(f"[lambda_handler] Added {len(linkedin_jobs)} LinkedIn jobs to DynamoDB")
        else:
            logger.warning("[lambda_handler] No response from LinkedIn API")

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