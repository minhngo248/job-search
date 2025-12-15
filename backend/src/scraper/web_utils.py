"""
Web scraping utilities for the regulatory jobs scraper.

This module provides async HTTP client functionality, HTML parsing utilities,
user agent rotation, request delays, and concurrency control for web scraping.
"""

import asyncio
import random
import logging
from typing import List, Optional, Dict, Any
from urllib.parse import urljoin, urlparse
import aiohttp
from bs4 import BeautifulSoup
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# User agents for rotation to avoid detection
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:89.0) Gecko/20100101 Firefox/89.0",
    "Mozilla/5.0 (X11; Linux x86_64; rv:89.0) Gecko/20100101 Firefox/89.0",
]


class RateLimiter:
    """Rate limiter to control request frequency per domain."""
    
    def __init__(self, min_delay: float = 1.0, max_delay: float = 3.0):
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.last_request_times: Dict[str, datetime] = {}
    
    async def wait_if_needed(self, domain: str) -> None:
        """Wait if necessary to respect rate limits for a domain."""
        now = datetime.now()
        
        if domain in self.last_request_times:
            time_since_last = (now - self.last_request_times[domain]).total_seconds()
            delay = random.uniform(self.min_delay, self.max_delay)
            
            if time_since_last < delay:
                wait_time = delay - time_since_last
                logger.debug(f"Rate limiting: waiting {wait_time:.2f}s for {domain}")
                await asyncio.sleep(wait_time)
        
        self.last_request_times[domain] = now


class AsyncWebScraper:
    """Async web scraper with concurrency control and rate limiting."""
    
    def __init__(self, max_concurrent_per_source: int = 3, request_timeout: int = 30):
        self.max_concurrent_per_source = max_concurrent_per_source
        self.request_timeout = request_timeout
        self.rate_limiter = RateLimiter()
        self.semaphores: Dict[str, asyncio.Semaphore] = {}
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        connector = aiohttp.TCPConnector(limit=100, limit_per_host=10)
        timeout = aiohttp.ClientTimeout(total=self.request_timeout)
        
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'}
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    def _get_domain_semaphore(self, url: str) -> asyncio.Semaphore:
        """Get or create a semaphore for the domain to limit concurrent requests."""
        domain = urlparse(url).netloc
        if domain not in self.semaphores:
            self.semaphores[domain] = asyncio.Semaphore(self.max_concurrent_per_source)
        return self.semaphores[domain]
    
    def _get_random_user_agent(self) -> str:
        """Get a random user agent for request headers."""
        return random.choice(USER_AGENTS)
    
    async def fetch_page(self, url: str, headers: Optional[Dict[str, str]] = None) -> Optional[str]:
        """
        Fetch a single page with rate limiting and error handling.
        
        Args:
            url: The URL to fetch
            headers: Optional additional headers
            
        Returns:
            The page content as string, or None if failed
        """
        if not self.session:
            raise RuntimeError("AsyncWebScraper must be used as async context manager")
        
        domain = urlparse(url).netloc
        semaphore = self._get_domain_semaphore(url)
        
        async with semaphore:
            try:
                # Rate limiting
                await self.rate_limiter.wait_if_needed(domain)
                
                # Prepare headers
                request_headers = {
                    'User-Agent': self._get_random_user_agent(),
                    'Accept-Language': 'en-US,en;q=0.9,fr;q=0.8',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'DNT': '1',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',
                }
                
                if headers:
                    request_headers.update(headers)
                
                logger.info(f"Fetching: {url}")
                
                async with self.session.get(url, headers=request_headers) as response:
                    if response.status == 200:
                        content = await response.text()
                        logger.debug(f"Successfully fetched {url} ({len(content)} chars)")
                        return content
                    elif response.status == 429:
                        logger.warning(f"Rate limited on {url}, status: {response.status}")
                        # Wait longer and retry once
                        await asyncio.sleep(random.uniform(5, 10))
                        return None
                    else:
                        logger.warning(f"Failed to fetch {url}, status: {response.status}")
                        return None
                        
            except asyncio.TimeoutError:
                logger.error(f"Timeout fetching {url}")
                return None
            except aiohttp.ClientError as e:
                logger.error(f"Client error fetching {url}: {e}")
                return None
            except Exception as e:
                logger.error(f"Unexpected error fetching {url}: {e}")
                return None
    
    async def fetch_multiple_pages(self, urls: List[str]) -> List[Optional[str]]:
        """
        Fetch multiple pages concurrently with proper rate limiting.
        
        Args:
            urls: List of URLs to fetch
            
        Returns:
            List of page contents (None for failed requests)
        """
        tasks = [self.fetch_page(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Convert exceptions to None
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Exception fetching {urls[i]}: {result}")
                processed_results.append(None)
            else:
                processed_results.append(result)
        
        return processed_results


class HTMLParser:
    """HTML parsing utilities using BeautifulSoup."""
    
    @staticmethod
    def parse_html(content: str, parser: str = 'html.parser') -> Optional[BeautifulSoup]:
        """
        Parse HTML content into BeautifulSoup object.
        
        Args:
            content: HTML content string
            parser: Parser to use ('html.parser', 'lxml', etc.)
            
        Returns:
            BeautifulSoup object or None if parsing failed
        """
        try:
            return BeautifulSoup(content, parser)
        except Exception as e:
            logger.error(f"Failed to parse HTML: {e}")
            return None
    
    @staticmethod
    def extract_text(element, strip: bool = True) -> str:
        """
        Extract text from BeautifulSoup element.
        
        Args:
            element: BeautifulSoup element
            strip: Whether to strip whitespace
            
        Returns:
            Extracted text
        """
        if element is None:
            return ""
        
        text = element.get_text()
        return text.strip() if strip else text
    
    @staticmethod
    def extract_links(soup: BeautifulSoup, base_url: str = "") -> List[str]:
        """
        Extract all links from a BeautifulSoup object.
        
        Args:
            soup: BeautifulSoup object
            base_url: Base URL for resolving relative links
            
        Returns:
            List of absolute URLs
        """
        links = []
        for link in soup.find_all('a', href=True):
            href = link['href']
            if base_url:
                href = urljoin(base_url, href)
            links.append(href)
        return links
    
    @staticmethod
    def find_job_elements(soup: BeautifulSoup, selectors: Dict[str, str]) -> List[Dict[str, Any]]:
        """
        Find job elements using CSS selectors.
        
        Args:
            soup: BeautifulSoup object
            selectors: Dictionary mapping field names to CSS selectors
            
        Returns:
            List of dictionaries with extracted job data
        """
        jobs = []
        
        # Find all job containers (assuming they have a common selector)
        job_containers = soup.select(selectors.get('container', '.job'))
        
        for container in job_containers:
            job_data = {}
            
            for field, selector in selectors.items():
                if field == 'container':
                    continue
                
                element = container.select_one(selector)
                if element:
                    if field.endswith('_link') or field == 'link':
                        # Extract href for link fields
                        job_data[field] = element.get('href', '')
                    else:
                        # Extract text for other fields
                        job_data[field] = HTMLParser.extract_text(element)
                else:
                    job_data[field] = ""
            
            if job_data:  # Only add if we found some data
                jobs.append(job_data)
        
        return jobs


def extract_domain(url: str) -> str:
    """Extract domain from URL."""
    return urlparse(url).netloc


def is_valid_url(url: str) -> bool:
    """Check if URL is valid."""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False


def normalize_url(url: str, base_url: str = "") -> str:
    """Normalize URL by making it absolute and cleaning it."""
    if not url:
        return ""
    
    # Make absolute if relative
    if base_url and not url.startswith(('http://', 'https://')):
        url = urljoin(base_url, url)
    
    return url.strip()