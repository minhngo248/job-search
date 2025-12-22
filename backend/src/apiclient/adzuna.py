import requests
import logging
import os

ADZUNA_APP_ID = os.environ.get('ADZUNA_APP_ID', '')
ADZUNA_APP_KEY = os.environ.get('ADZUNA_APP_KEY', '')

logger = logging.getLogger()

class AdzunaApiClient:
    async def call_api(self):
        logger.info("[apiclient=ADZUNA] Starting API call")
        logger.info(f"[apiclient=ADZUNA] Start calling API")
        try:
            params = {
                'app_id': ADZUNA_APP_ID,
                'app_key': ADZUNA_APP_KEY, 
                'what': 'regulatory affairs medical device',
                'where': 'Île-de-France',
                #'max_days_old': 14, 
                'sort_direction': 'down',
                'sort_by': 'date',
                'results_per_page': 50
            }
            logger.info(f"[apiclient=ADZUNA] Request params: {params}")
            
            response = requests.get('https://api.adzuna.com/v1/api/jobs/fr/search/1', params=params)
            
            logger.info(f"[apiclient=ADZUNA] Response status: {response.status_code}")
            logger.info(f"[apiclient=ADZUNA] Response headers: {dict(response.headers)}")
            
            if response.status_code != 200:
                logger.error(f"[apiclient=ADZUNA] Error - Status {response.status_code}: {response.text[:200]}")
                logger.error(f"[apiclient=ADZUNA] API returned status {response.status_code}: {response.text}")
                return None
            
            if not response.text.strip():
                logger.error("[apiclient=ADZUNA] Error - Empty response")
                logger.error(f"[apiclient=ADZUNA] Empty response from API")
                return None
                
            job_result = response.json()
            job_count = job_result.get('count', 0)
            results_count = len(job_result.get('results', []))
            logger.info(f"[apiclient=ADZUNA] Success - Found {job_count} total jobs, {results_count} in this page")
            logger.info(f"[apiclient=ADZUNA] Found {job_count} results")
            return job_result
        except requests.exceptions.RequestException as e:
            logger.error(f"[apiclient=ADZUNA] Request error: {e}")
            return None
        except ValueError as e:
            logger.error(f"[apiclient=ADZUNA] JSON decode error: {e}")
            logger.error(f"[apiclient=ADZUNA] Response text: {response.text[:500]}")
            return None
        except Exception as e:
            logger.error(f"[apiclient=ADZUNA] Unexpected error: {e}")
            return None