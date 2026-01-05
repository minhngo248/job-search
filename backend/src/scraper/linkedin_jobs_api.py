"""
LinkedIn Jobs API - Python Implementation
Advanced Python package for getting job listings from LinkedIn
"""

import time
import random
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from urllib.parse import urlencode
import requests
import logging
from bs4 import BeautifulSoup

logger = logging.getLogger()

class JobCache:
    """Cache implementation for job listings"""
    
    def __init__(self, ttl: int = 3600):
        """
        Initialize cache with TTL (Time To Live)
        
        Args:
            ttl: Time to live in seconds (default: 3600 = 1 hour)
        """
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.ttl = ttl
    
    def set(self, key: str, value: Any) -> None:
        """Store value in cache with timestamp"""
        self.cache[key] = {
            'data': value,
            'timestamp': time.time()
        }
    
    def get(self, key: str) -> Optional[Any]:
        """Retrieve value from cache if not expired"""
        item = self.cache.get(key)
        if not item:
            return None
        
        if time.time() - item['timestamp'] > self.ttl:
            del self.cache[key]
            return None
        
        return item['data']
    
    def clear(self) -> None:
        """Clear expired items from cache"""
        now = time.time()
        expired_keys = [
            key for key, value in self.cache.items()
            if now - value['timestamp'] > self.ttl
        ]
        for key in expired_keys:
            del self.cache[key]


# Global cache instance
_cache = JobCache()


class LinkedInJobsQuery:
    """Query builder and executor for LinkedIn job searches"""
    
    DATE_RANGES = {
        'past month': 'r2592000',
        'past week': 'r604800',
        '24hr': 'r86400',
    }
    
    EXPERIENCE_LEVELS = {
        'internship': '1',
        'entry level': '2',
        'associate': '3',
        'senior': '4',
        'director': '5',
        'executive': '6',
    }
    
    JOB_TYPES = {
        'full time': 'F',
        'full-time': 'F',
        'part time': 'P',
        'part-time': 'P',
        'contract': 'C',
        'temporary': 'T',
        'volunteer': 'V',
        'internship': 'I',
    }
    
    REMOTE_FILTERS = {
        'on-site': '1',
        'on site': '1',
        'remote': '2',
        'hybrid': '3',
    }
    
    SALARY_RANGES = {
        40000: '1',
        60000: '2',
        80000: '3',
        100000: '4',
        120000: '5',
    }
    
    def __init__(self, query_options: Dict[str, Any]):
        """
        Initialize query with options
        
        Args:
            query_options: Dictionary containing query parameters
        """
        self.host = query_options.get('host', 'www.linkedin.com')
        self.keyword = query_options.get('keyword', '').strip().replace(' ', '+')
        self.location = query_options.get('location', '').strip().replace(' ', '+')
        self.date_since_posted = query_options.get('dateSincePosted', '')
        self.job_type = query_options.get('jobType', '')
        self.remote_filter = query_options.get('remoteFilter', '')
        self.salary = query_options.get('salary', '')
        self.experience_level = query_options.get('experienceLevel', '')
        self.sort_by = query_options.get('sortBy', '')
        self.limit = int(query_options.get('limit', 0))
        self.page = int(query_options.get('page', 0))
        self.has_verification = query_options.get('has_verification', False)
        self.under_10_applicants = query_options.get('under_10_applicants', False)
    
    def _get_date_since_posted(self) -> str:
        """Convert date range to LinkedIn format"""
        return self.DATE_RANGES.get(self.date_since_posted.lower(), '')
    
    def _get_experience_level(self) -> str:
        """Convert experience level to LinkedIn format"""
        return self.EXPERIENCE_LEVELS.get(self.experience_level.lower(), '')
    
    def _get_job_type(self) -> str:
        """Convert job type to LinkedIn format"""
        return self.JOB_TYPES.get(self.job_type.lower(), '')
    
    def _get_remote_filter(self) -> str:
        """Convert remote filter to LinkedIn format"""
        return self.REMOTE_FILTERS.get(self.remote_filter.lower(), '')
    
    def _get_salary(self) -> str:
        """Convert salary to LinkedIn format"""
        try:
            salary_int = int(self.salary)
            return self.SALARY_RANGES.get(salary_int, '')
        except (ValueError, TypeError):
            return ''
    
    def _get_has_verification(self) -> str:
        """Convert verification flag to string"""
        return 'true' if self.has_verification else 'false'
    
    def _get_under_10_applicants(self) -> str:
        """Convert under 10 applicants flag to string"""
        return 'true' if self.under_10_applicants else 'false'
    
    def _get_page_offset(self) -> int:
        """Calculate page offset"""
        return self.page * 25
    
    def _build_url(self, start: int = 0) -> str:
        """
        Build LinkedIn API URL with query parameters
        
        Args:
            start: Starting index for pagination
            
        Returns:
            Complete URL string
        """
        base_url = f'https://{self.host}/jobs-guest/jobs/api/seeMoreJobPostings/search?'
        params = {}
        
        if self.keyword:
            params['keywords'] = self.keyword
        if self.location:
            params['location'] = self.location
        if self._get_date_since_posted():
            params['f_TPR'] = self._get_date_since_posted()
        if self._get_salary():
            params['f_SB2'] = self._get_salary()
        if self._get_experience_level():
            params['f_E'] = self._get_experience_level()
        if self._get_remote_filter():
            params['f_WT'] = self._get_remote_filter()
        if self._get_job_type():
            params['f_JT'] = self._get_job_type()
        if self._get_has_verification():
            params['f_VJ'] = self._get_has_verification()
        if self._get_under_10_applicants():
            params['f_EA'] = self._get_under_10_applicants()
        
        params['start'] = start + self._get_page_offset()
        
        if self.sort_by == 'recent':
            params['sortBy'] = 'DD'
        elif self.sort_by == 'relevant':
            params['sortBy'] = 'R'
        
        return base_url + urlencode(params)
    
    def _get_cache_key(self) -> str:
        """Generate unique cache key based on query parameters"""
        return f"{self._build_url(0)}_limit:{self.limit}"
    
    def _get_random_user_agent(self) -> str:
        """Generate random user agent"""
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
        ]
        return random.choice(user_agents)
    
    def _parse_job_list(self, html_content: str) -> List[Dict[str, str]]:
        """
        Parse HTML content and extract job listings
        
        Args:
            html_content: HTML string from LinkedIn API
            
        Returns:
            List of job dictionaries
        """
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            jobs = soup.find_all('li')
            
            parsed_jobs = []
            for job_element in jobs:
                try:
                    # Extract job details
                    position_elem = job_element.find(class_='base-search-card__title')
                    company_elem = job_element.find(class_='base-search-card__subtitle')
                    location_elem = job_element.find(class_='job-search-card__location')
                    date_elem = job_element.find('time')
                    salary_elem = job_element.find(class_='job-search-card__salary-info')
                    job_url_elem = job_element.find(class_='base-card__full-link')
                    logo_elem = job_element.find(class_='artdeco-entity-image')
                    ago_time_elem = job_element.find(class_='job-search-card__listdate')
                    
                    position = position_elem.get_text(strip=True) if position_elem else None
                    company = company_elem.get_text(strip=True) if company_elem else None
                    
                    # Only include job if we have at least position and company
                    if not position or not company:
                        continue
                    
                    location = location_elem.get_text(strip=True) if location_elem else ''
                    date = date_elem.get('datetime', '') if date_elem else ''
                    salary = salary_elem.get_text(strip=True).replace('\n', ' ').replace('  ', ' ') if salary_elem else 'Not specified'
                    job_url = job_url_elem.get('href', '') if job_url_elem else ''
                    company_logo = logo_elem.get('data-delayed-url', '') if logo_elem else ''
                    ago_time = ago_time_elem.get_text(strip=True) if ago_time_elem else ''
                    
                    parsed_jobs.append({
                        'position': position,
                        'company': company,
                        'location': location,
                        'date': date,
                        'salary': salary,
                        'jobUrl': job_url,
                        'companyLogo': company_logo,
                        'agoTime': ago_time,
                    })
                except Exception as e:
                    logger.warning(f"[class=LinkedInJobsQuery] Warning: Error parsing job element: {e}")
                    continue
            
            return parsed_jobs
        except Exception as e:
            logger.error(f"[class=LinkedInJobsQuery] Error parsing job list: {e}")
            return []
    
    def _fetch_job_batch(self, start: int) -> List[Dict[str, str]]:
        """
        Fetch a batch of jobs from LinkedIn API
        
        Args:
            start: Starting index for pagination
            
        Returns:
            List of job dictionaries
        """
        headers = {
            'User-Agent': self._get_random_user_agent(),
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Referer': 'https://www.linkedin.com/jobs',
            'X-Requested-With': 'XMLHttpRequest',
            'Connection': 'keep-alive',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache',
        }
        
        try:
            response = requests.get(
                self._build_url(start),
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 429:
                raise Exception('Rate limit reached')
            
            response.raise_for_status()
            return self._parse_job_list(response.text)
        except requests.exceptions.RequestException as e:
            raise Exception(f"Request failed: {e}")
    
    def get_jobs(self) -> List[Dict[str, str]]:
        """
        Execute query and retrieve job listings
        
        Returns:
            List of job dictionaries
        """
        all_jobs = []
        start = 0
        batch_size = 25
        has_more = True
        consecutive_errors = 0
        max_consecutive_errors = 3
        
        logger.info(f"[class=LinkedInJobsQuery] {self._build_url()}")
        logger.info(f"[class=LinkedInJobsQuery] {self._get_cache_key()}")
        
        try:
            # Check cache first
            cache_key = self._get_cache_key()
            cached_jobs = _cache.get(cache_key)
            if cached_jobs:
                logger.info("[class=LinkedInJobsQuery] Returning cached results")
                return cached_jobs
            
            while has_more:
                try:
                    jobs = self._fetch_job_batch(start)
                    
                    if not jobs or len(jobs) == 0:
                        has_more = False
                        break
                    
                    all_jobs.extend(jobs)
                    logger.info(f"[class=LinkedInJobsQuery] Fetched {len(jobs)} jobs. Total: {len(all_jobs)}")
                    
                    if self.limit and len(all_jobs) >= self.limit:
                        all_jobs = all_jobs[:self.limit]
                        break
                    
                    # Reset error counter on successful fetch
                    consecutive_errors = 0
                    start += batch_size
                    
                    # Add reasonable delay between requests
                    time.sleep(2 + random.random())
                except Exception as e:
                    consecutive_errors += 1
                    logger.error(f"[class=LinkedInJobsQuery] Error fetching batch (attempt {consecutive_errors}): {e}")
                    
                    if consecutive_errors >= max_consecutive_errors:
                        logger.error("[class=LinkedInJobsQuery] Max consecutive errors reached. Stopping.")
                        break
                    
                    # Exponential backoff
                    time.sleep(2 ** consecutive_errors)
            
            # Cache results if we got any
            if len(all_jobs) > 0:
                _cache.set(cache_key, all_jobs)
            
            return all_jobs
        except Exception as e:
            logger.error(f"[class=LinkedInJobsQuery] Fatal error in job fetching: {e}")
            raise


def query(query_options: Dict[str, Any]) -> List[Dict[str, str]]:
    """
    Main query function to fetch LinkedIn jobs
    
    Args:
        query_options: Dictionary containing query parameters:
            - keyword (str): Search keywords
            - location (str): Job location
            - dateSincePosted (str): 'past month', 'past week', '24hr'
            - jobType (str): 'full time', 'part time', 'contract', etc.
            - remoteFilter (str): 'on-site', 'remote', 'hybrid'
            - salary (str/int): Minimum salary (40000, 60000, 80000, 100000, 120000)
            - experienceLevel (str): 'internship', 'entry level', 'associate', etc.
            - limit (int): Maximum number of jobs to return
            - sortBy (str): 'recent' or 'relevant'
            - page (int): Page number (0-indexed)
            - has_verification (bool): Filter for verified jobs
            - under_10_applicants (bool): Filter for jobs with under 10 applicants
    
    Returns:
        List of job dictionaries with keys:
            - position, company, location, date, salary, jobUrl, companyLogo, agoTime
    """
    linkedin_query = LinkedInJobsQuery(query_options)
    return linkedin_query.get_jobs()


def clear_cache() -> None:
    """Clear the job cache"""
    _cache.clear()


def get_cache_size() -> int:
    """Get the current cache size"""
    return len(_cache.cache)
