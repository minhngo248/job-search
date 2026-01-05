from src.scraper.linkedin_jobs_api import query
import logging

logger = logging.getLogger()

class LinkedInClient:
    def __init__(self, keyword: str, location: str, date_since_posted: str = 'past Month', job_type: str = 'full time',
                 remote_filter: str = '', salary: str = '46000', experience_level: str = 'associate',
                 limit: str = '20', sort_by: str = 'recent', page: str = '1', has_verification: bool = False,
                 under_10_applicants: bool = False):
        self.keyword = keyword
        self.location = location
        self.date_since_posted = date_since_posted
        self.job_type = job_type
        self.remote_filter = remote_filter
        self.salary = salary
        self.experience_level = experience_level
        self.limit = limit
        self.sort_by = sort_by
        self.page = page
        self.has_verification = has_verification
        self.under_10_applicants = under_10_applicants

    async def call_api(self):
        logger.info("[scraper=LINKEDIN] Starting LinkedIn Jobs API call")
        try:
            query_options = {
                'keyword': self.keyword,
                'location': self.location,
                'dateSincePosted': self.date_since_posted,
                'jobType': self.job_type,
                'remoteFilter': self.remote_filter,
                'salary': self.salary,
                'experienceLevel': self.experience_level,
                'limit': self.limit,
                'sortBy': self.sort_by,
                'page': self.page,
                'has_verification': self.has_verification,
                'under_10_applicants': self.under_10_applicants,
            }
            response = query(query_options)
            return response
        except Exception as e:
            logger.error(f"[scraper=LINKEDIN] Error during LinkedIn Jobs API call: {e}")
            return None
