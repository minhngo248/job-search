"""
Glassdoor job scraper for regulatory affairs positions in Île-de-France.

This module handles scraping job postings from Glassdoor with pagination
and specific extraction logic for Glassdoor's job listing structure.
"""

import asyncio
import logging
import re
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin, quote_plus
from datetime import datetime, timedelta

from .web_utils import AsyncWebScraper, HTMLParser

logger = logging.getLogger(__name__)

# Île-de-France cities for filtering (same as LinkedIn)
ILE_DE_FRANCE_CITIES = {
    'paris', 'boulogne-billancourt', 'saint-denis', 'argenteuil', 'montreuil',
    'créteil', 'nanterre', 'courbevoie', 'versailles', 'rueil-malmaison',
    'aubervilliers', 'champigny-sur-marne', 'saint-maur-des-fossés', 'drancy',
    'issy-les-moulineaux', 'levallois-perret', 'antony', 'noisy-le-grand',
    'villejuif', 'clichy', 'ivry-sur-seine', 'maisons-alfort', 'neuilly-sur-seine',
    'clamart', 'pantin', 'bondy', 'fontenay-sous-bois', 'bobigny', 'rosny-sous-bois',
    'vincennes', 'châtillon', 'colombes', 'aulnay-sous-bois', 'sarcelles',
    'puteaux', 'gennevilliers', 'schiltigheim', 'alfortville', 'meudon',
    'saint-ouen', 'corbeil-essonnes', 'vitry-sur-seine', 'bagnolet', 'bagneux',
    'cergy', 'houilles', 'romainville', 'le-blanc-mesnil', 'châtenay-malabry',
    'fresnes', 'saint-cloud', 'sevran', 'livry-gargan', 'meaux', 'melun',
    'pontoise', 'évry', 'sartrouville', 'garges-lès-gonesse', 'franconville',
    'goussainville', 'roissy-en-brie', 'thiais', 'villeneuve-saint-georges',
    'montrouge', 'noisy-le-sec', 'malakoff', 'sucy-en-brie', 'saint-germain-en-laye',
    'massy', 'palaiseau', 'trappes', 'conflans-sainte-honorine', 'chelles',
    'bois-colombes', 'villiers-sur-marne', 'épinay-sur-seine', 'maisons-laffitte',
    'poissy', 'montigny-le-bretonneux', 'yerres', 'le-perreux-sur-marne',
    'villeparisis', 'neuilly-plaisance', 'cachan', 'saint-mandé', 'deuil-la-barre',
    'pierrefitte-sur-seine', 'villeneuve-la-garenne', 'saint-gratien', 'ermont',
    'chatou', 'le-kremlin-bicêtre', 'villiers-le-bel', 'montfermeil', 'dugny',
    'la-garenne-colombes', 'stains', 'limeil-brévannes', 'villemomble',
    'bry-sur-marne', 'nogent-sur-marne', 'gournay-sur-marne', 'le-bourget',
    'fontenay-aux-roses', 'arcueil', 'gentilly', 'le-plessis-robinson'
}


class GlassdoorScraper:
    """Glassdoor job scraper with pagination support."""
    
    def __init__(self):
        self.base_url = "https://www.glassdoor.com"
        self.search_keywords = [
            "regulatory affairs medical device",
            "affaires réglementaires dispositif médical",
            "regulatory medical device",
            "quality assurance medical device",
            "medical device compliance"
        ]
    
    def _build_search_urls(self, max_pages: int = 3) -> List[str]:
        """Build Glassdoor job search URLs for regulatory positions."""
        urls = []
        
        for keyword in self.search_keywords:
            # Encode the keyword for URL
            encoded_keyword = quote_plus(keyword)
            
            # Build search URLs with pagination
            for page in range(1, max_pages + 1):
                search_params = [
                    f"sc.keyword={encoded_keyword}",
                    "locT=C",
                    "locId=2988507",  # Paris, France location ID
                    "locKeyword=Paris%2C%20France",
                    f"p={page}",
                    "fromAge=1",  # Jobs posted in last day
                    "jobType=fulltime"
                ]
                
                url = f"{self.base_url}/Job/jobs.htm?{'&'.join(search_params)}"
                urls.append(url)
        
        return urls
    
    def _extract_job_links_from_search(self, html_content: str, base_url: str) -> List[str]:
        """Extract individual job posting URLs from Glassdoor search results."""
        soup = HTMLParser.parse_html(html_content)
        if not soup:
            return []
        
        job_links = []
        
        # Glassdoor job search results selectors
        job_link_selectors = [
            'a[data-test="job-link"]',
            '.jobLink',
            'a[href*="/job-listing/"]',
            '.react-job-listing a',
            'a[data-id][href*="/job/"]'
        ]
        
        for selector in job_link_selectors:
            links = soup.select(selector)
            for link in links:
                href = link.get('href')
                if href:
                    full_url = urljoin(base_url, href)
                    # Clean up the URL
                    clean_url = full_url.split('?')[0]
                    if clean_url not in job_links:
                        job_links.append(clean_url)
        
        logger.info(f"Found {len(job_links)} job links in Glassdoor search results")
        return job_links
    
    def _extract_job_data_from_page(self, html_content: str, job_url: str) -> Optional[Dict[str, Any]]:
        """Extract job data from individual Glassdoor job page."""
        soup = HTMLParser.parse_html(html_content)
        if not soup:
            return None
        
        try:
            job_data = {
                'link': job_url,
                'source': 'glassdoor'
            }
            
            # Job title
            title_selectors = [
                '[data-test="job-title"]',
                '.jobsearch-JobInfoHeader-title',
                'h1.e1tk4kwz4',
                '.css-17x2pwl h1'
            ]
            
            for selector in title_selectors:
                title_elem = soup.select_one(selector)
                if title_elem:
                    job_data['job_title'] = HTMLParser.extract_text(title_elem)
                    break
            
            # Company name
            company_selectors = [
                '[data-test="employer-name"]',
                '.css-16nw49e',
                '.employerName',
                'div[data-test="employer-name"] span'
            ]
            
            for selector in company_selectors:
                company_elem = soup.select_one(selector)
                if company_elem:
                    job_data['company_name'] = HTMLParser.extract_text(company_elem)
                    break
            
            # Location
            location_selectors = [
                '[data-test="job-location"]',
                '.css-1buaf54',
                '.locationsContainer',
                'div[data-test="job-location"]'
            ]
            
            for selector in location_selectors:
                location_elem = soup.select_one(selector)
                if location_elem:
                    location_text = HTMLParser.extract_text(location_elem)
                    city = self._extract_city_from_location(location_text)
                    if city:
                        job_data['city'] = city
                        break
            
            # Job description for experience extraction
            description_selectors = [
                '[data-test="jobDescriptionText"]',
                '.jobDescriptionContent',
                '.css-1uobp1k',
                '.desc'
            ]
            
            description_text = ""
            for selector in description_selectors:
                desc_elem = soup.select_one(selector)
                if desc_elem:
                    description_text = HTMLParser.extract_text(desc_elem)
                    break
            
            # Extract years of experience from description
            experience_years = self._extract_experience_years(description_text)
            if experience_years is not None:
                job_data['year_of_experience'] = experience_years
            
            # Try to extract publication date
            pub_date = self._extract_publication_date(soup)
            if pub_date:
                job_data['published_date'] = pub_date
            
            # Validate required fields
            required_fields = ['job_title', 'company_name', 'city']
            if all(field in job_data and job_data[field] for field in required_fields):
                return job_data
            else:
                logger.warning(f"Missing required fields in Glassdoor job data: {job_data}")
                return None
                
        except Exception as e:
            logger.error(f"Error extracting job data from {job_url}: {e}")
            return None
    
    def _extract_city_from_location(self, location_text: str) -> Optional[str]:
        """Extract city name from location text and validate it's in Île-de-France."""
        if not location_text:
            return None
        
        location_lower = location_text.lower()
        
        # Check if any Île-de-France city is mentioned
        for city in ILE_DE_FRANCE_CITIES:
            if city in location_lower:
                return city.title()
        
        # Check for Paris variations
        if any(term in location_lower for term in ['paris', 'île-de-france', 'ile-de-france']):
            return 'Paris'
        
        return None
    
    def _extract_experience_years(self, description_text: str) -> Optional[int]:
        """Extract years of experience from job description."""
        if not description_text:
            return None
        
        # Common patterns for experience requirements
        patterns = [
            r'(\d+)\+?\s*(?:years?|ans?)\s*(?:of\s*)?(?:experience|expérience)',
            r'(?:minimum|minimum de|au moins)\s*(\d+)\s*(?:years?|ans?)',
            r'(\d+)\s*(?:to|-|à)\s*\d+\s*(?:years?|ans?)',
            r'(\d+)\s*(?:years?|ans?)\s*(?:minimum|min)',
            r'(?:experience|expérience).*?(\d+)\s*(?:years?|ans?)',
        ]
        
        description_lower = description_text.lower()
        
        for pattern in patterns:
            matches = re.findall(pattern, description_lower)
            if matches:
                try:
                    return int(matches[0])
                except (ValueError, IndexError):
                    continue
        
        # Default to 0 if no experience mentioned
        return 0
    
    def _extract_publication_date(self, soup) -> Optional[str]:
        """Extract publication date from Glassdoor job page."""
        # Glassdoor often shows relative dates
        date_selectors = [
            '[data-test="job-age"]',
            '.css-1cnx1r9',
            '.jobAge',
            'div[data-test="job-age"]'
        ]
        
        for selector in date_selectors:
            date_elem = soup.select_one(selector)
            if date_elem:
                date_text = HTMLParser.extract_text(date_elem)
                return self._parse_relative_date(date_text)
        
        # Default to current date if not found
        return datetime.now().isoformat()
    
    def _parse_relative_date(self, date_text: str) -> str:
        """Parse relative date text like '2d' or '1 day ago' to ISO format."""
        if not date_text:
            return datetime.now().isoformat()
        
        date_text_lower = date_text.lower()
        now = datetime.now()
        
        # Parse patterns like "2d", "1 day ago", "3h", etc.
        if 'd' in date_text_lower or 'day' in date_text_lower:
            match = re.search(r'(\d+)\s*d(?:ay)?', date_text_lower)
            if match:
                days = int(match.group(1))
                pub_date = now - timedelta(days=days)
                return pub_date.isoformat()
        
        elif 'h' in date_text_lower or 'hour' in date_text_lower:
            match = re.search(r'(\d+)\s*h(?:our)?', date_text_lower)
            if match:
                hours = int(match.group(1))
                pub_date = now - timedelta(hours=hours)
                return pub_date.isoformat()
        
        elif 'w' in date_text_lower or 'week' in date_text_lower:
            match = re.search(r'(\d+)\s*w(?:eek)?', date_text_lower)
            if match:
                weeks = int(match.group(1))
                pub_date = now - timedelta(weeks=weeks)
                return pub_date.isoformat()
        
        elif 'm' in date_text_lower or 'month' in date_text_lower:
            match = re.search(r'(\d+)\s*m(?:onth)?', date_text_lower)
            if match:
                months = int(match.group(1))
                pub_date = now - timedelta(days=months * 30)  # Approximate
                return pub_date.isoformat()
        
        # Default to current date
        return now.isoformat()
    
    async def scrape_jobs(self, scraper: AsyncWebScraper) -> List[Dict[str, Any]]:
        """
        Scrape regulatory jobs from Glassdoor.
        
        Args:
            scraper: AsyncWebScraper instance
            
        Returns:
            List of job dictionaries
        """
        logger.info("Starting Glassdoor job scraping")
        
        all_jobs = []
        search_urls = self._build_search_urls(max_pages=2)  # Limit to 2 pages per keyword
        
        try:
            # Fetch search result pages
            search_pages = await scraper.fetch_multiple_pages(search_urls)
            
            # Extract job links from all search pages
            all_job_links = []
            for i, page_content in enumerate(search_pages):
                if page_content:
                    job_links = self._extract_job_links_from_search(page_content, self.base_url)
                    all_job_links.extend(job_links)
                    logger.info(f"Glassdoor search page {i+1}: found {len(job_links)} job links")
            
            # Remove duplicates
            unique_job_links = list(set(all_job_links))
            logger.info(f"Total unique Glassdoor job links found: {len(unique_job_links)}")
            
            # Limit to avoid overwhelming Glassdoor (take first 30)
            limited_job_links = unique_job_links[:30]
            
            # Fetch individual job pages
            job_pages = await scraper.fetch_multiple_pages(limited_job_links)
            
            # Extract job data from each page
            for i, (job_url, page_content) in enumerate(zip(limited_job_links, job_pages)):
                if page_content:
                    job_data = self._extract_job_data_from_page(page_content, job_url)
                    if job_data:
                        all_jobs.append(job_data)
                        logger.debug(f"Extracted Glassdoor job {i+1}: {job_data.get('job_title', 'Unknown')}")
            
            logger.info(f"Glassdoor scraping completed: {len(all_jobs)} jobs extracted")
            return all_jobs
            
        except Exception as e:
            logger.error(f"Error during Glassdoor scraping: {e}")
            return []