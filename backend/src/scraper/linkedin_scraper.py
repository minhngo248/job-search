"""
LinkedIn job scraper for regulatory affairs positions in Île-de-France.

This module handles scraping job postings from LinkedIn with anti-bot measures
and specific extraction logic for LinkedIn's job page structure.
"""

import asyncio
import logging
import re
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin, quote_plus
from datetime import datetime, timedelta

from .web_utils import AsyncWebScraper, HTMLParser

logger = logging.getLogger(__name__)

# Île-de-France cities for filtering
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


class LinkedInScraper:
    """LinkedIn job scraper with anti-bot measures."""
    
    def __init__(self):
        self.base_url = "https://www.linkedin.com"
        self.search_keywords = [
            "regulatory affairs medical device",
            "affaires réglementaires dispositif médical",
            "regulatory medical device",
            "réglementaire médical",
            "quality assurance medical device",
            "assurance qualité dispositif médical"
        ]
    
    def _build_search_urls(self) -> List[str]:
        """Build LinkedIn job search URLs for regulatory positions."""
        urls = []
        
        # LinkedIn job search URL pattern
        base_search_url = "https://www.linkedin.com/jobs/search"
        
        for keyword in self.search_keywords:
            # Encode the keyword for URL
            encoded_keyword = quote_plus(keyword)
            
            # Build search URL with location filter for Île-de-France
            search_params = [
                f"keywords={encoded_keyword}",
                "location=Île-de-France%2C%20France",
                "locationId=105015875",  # LinkedIn location ID for Île-de-France
                "geoId=105015875",
                "sortBy=DD",  # Sort by date (most recent first)
                "f_TPR=r86400",  # Posted in last 24 hours
                "f_JT=F",  # Full-time jobs
                "start=0"
            ]
            
            url = f"{base_search_url}?{'&'.join(search_params)}"
            urls.append(url)
        
        return urls
    
    def _extract_job_links_from_search(self, html_content: str, base_url: str) -> List[str]:
        """Extract individual job posting URLs from LinkedIn search results."""
        soup = HTMLParser.parse_html(html_content)
        if not soup:
            return []
        
        job_links = []
        
        # LinkedIn job search results selectors (these may change)
        job_link_selectors = [
            'a[data-tracking-control-name="public_jobs_jserp-result_search-card"]',
            '.job-search-card a',
            '.jobs-search__results-list a[href*="/jobs/view/"]',
            'a[href*="/jobs/view/"]'
        ]
        
        for selector in job_link_selectors:
            links = soup.select(selector)
            for link in links:
                href = link.get('href')
                if href and '/jobs/view/' in href:
                    full_url = urljoin(base_url, href)
                    # Clean up the URL (remove tracking parameters)
                    clean_url = full_url.split('?')[0]
                    if clean_url not in job_links:
                        job_links.append(clean_url)
        
        logger.info(f"Found {len(job_links)} job links in search results")
        return job_links
    
    def _extract_job_data_from_page(self, html_content: str, job_url: str) -> Optional[Dict[str, Any]]:
        """Extract job data from individual LinkedIn job page."""
        soup = HTMLParser.parse_html(html_content)
        if not soup:
            return None
        
        try:
            job_data = {
                'link': job_url,
                'source': 'linkedin'
            }
            
            # Job title - multiple possible selectors
            title_selectors = [
                'h1.top-card-layout__title',
                '.topcard__title',
                'h1[data-test="job-title"]',
                '.job-details-jobs-unified-top-card__job-title h1'
            ]
            
            for selector in title_selectors:
                title_elem = soup.select_one(selector)
                if title_elem:
                    job_data['job_title'] = HTMLParser.extract_text(title_elem)
                    break
            
            # Company name
            company_selectors = [
                'a.topcard__org-name-link',
                '.topcard__flavor--black-link',
                'a[data-test="job-company-name"]',
                '.job-details-jobs-unified-top-card__company-name a'
            ]
            
            for selector in company_selectors:
                company_elem = soup.select_one(selector)
                if company_elem:
                    job_data['company_name'] = HTMLParser.extract_text(company_elem)
                    break
            
            # Location
            location_selectors = [
                '.topcard__flavor--bullet',
                '.job-details-jobs-unified-top-card__bullet',
                '[data-test="job-location"]'
            ]
            
            for selector in location_selectors:
                location_elem = soup.select_one(selector)
                if location_elem:
                    location_text = HTMLParser.extract_text(location_elem)
                    # Extract city from location text
                    city = self._extract_city_from_location(location_text)
                    if city:
                        job_data['city'] = city
                        break
            
            # Job description for experience extraction
            description_selectors = [
                '.show-more-less-html__markup',
                '.job-details-jobs-unified-top-card__job-description',
                '.description__text'
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
                logger.warning(f"Missing required fields in job data: {job_data}")
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
        """Extract publication date from LinkedIn job page."""
        # LinkedIn often shows relative dates like "2 days ago"
        date_selectors = [
            '.posted-time-ago__text',
            '.job-details-jobs-unified-top-card__posted-date',
            '[data-test="job-posted-date"]'
        ]
        
        for selector in date_selectors:
            date_elem = soup.select_one(selector)
            if date_elem:
                date_text = HTMLParser.extract_text(date_elem)
                return self._parse_relative_date(date_text)
        
        # Default to current date if not found
        return datetime.now().isoformat()
    
    def _parse_relative_date(self, date_text: str) -> str:
        """Parse relative date text like '2 days ago' to ISO format."""
        if not date_text:
            return datetime.now().isoformat()
        
        date_text_lower = date_text.lower()
        now = datetime.now()
        
        # Parse patterns like "X days ago", "X hours ago", etc.
        if 'day' in date_text_lower:
            match = re.search(r'(\d+)\s*day', date_text_lower)
            if match:
                days = int(match.group(1))
                pub_date = now - timedelta(days=days)
                return pub_date.isoformat()
        
        elif 'hour' in date_text_lower:
            match = re.search(r'(\d+)\s*hour', date_text_lower)
            if match:
                hours = int(match.group(1))
                pub_date = now - timedelta(hours=hours)
                return pub_date.isoformat()
        
        elif 'week' in date_text_lower:
            match = re.search(r'(\d+)\s*week', date_text_lower)
            if match:
                weeks = int(match.group(1))
                pub_date = now - timedelta(weeks=weeks)
                return pub_date.isoformat()
        
        # Default to current date
        return now.isoformat()
    
    async def scrape_jobs(self, scraper: AsyncWebScraper) -> List[Dict[str, Any]]:
        """
        Scrape regulatory jobs from LinkedIn.
        
        Args:
            scraper: AsyncWebScraper instance
            
        Returns:
            List of job dictionaries
        """
        logger.info("Starting LinkedIn job scraping")
        
        all_jobs = []
        search_urls = self._build_search_urls()
        
        try:
            # Fetch search result pages
            search_pages = await scraper.fetch_multiple_pages(search_urls)
            
            # Extract job links from all search pages
            all_job_links = []
            for i, page_content in enumerate(search_pages):
                if page_content:
                    job_links = self._extract_job_links_from_search(page_content, self.base_url)
                    all_job_links.extend(job_links)
                    logger.info(f"Search page {i+1}: found {len(job_links)} job links")
            
            # Remove duplicates
            unique_job_links = list(set(all_job_links))
            logger.info(f"Total unique job links found: {len(unique_job_links)}")
            
            # Limit to avoid overwhelming LinkedIn (take first 50)
            limited_job_links = unique_job_links[:50]
            
            # Fetch individual job pages
            job_pages = await scraper.fetch_multiple_pages(limited_job_links)
            
            # Extract job data from each page
            for i, (job_url, page_content) in enumerate(zip(limited_job_links, job_pages)):
                if page_content:
                    job_data = self._extract_job_data_from_page(page_content, job_url)
                    if job_data:
                        all_jobs.append(job_data)
                        logger.debug(f"Extracted job {i+1}: {job_data.get('job_title', 'Unknown')}")
            
            logger.info(f"LinkedIn scraping completed: {len(all_jobs)} jobs extracted")
            return all_jobs
            
        except Exception as e:
            logger.error(f"Error during LinkedIn scraping: {e}")
            return []