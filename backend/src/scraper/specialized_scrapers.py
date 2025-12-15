"""
Specialized job scrapers for pharmaceutical and medical device industry sites.

This module handles scraping from emploi.leem.org, snitem.fr, and pharmaceutical
company career pages specific to regulatory affairs positions.
"""

import asyncio
import logging
import re
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin, urlparse
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


class LeemScraper:
    """Scraper for emploi.leem.org (French pharmaceutical industry jobs)."""
    
    def __init__(self):
        self.base_url = "https://emploi.leem.org"
        self.search_url = f"{self.base_url}/offres-emploi"
    
    def _build_search_urls(self) -> List[str]:
        """Build search URLs for LEEM job board."""
        # LEEM search parameters for regulatory affairs
        search_params = [
            "?q=réglementaire",
            "?q=regulatory",
            "?q=affaires+réglementaires",
            "?q=qualité",
            "?q=compliance"
        ]
        
        urls = []
        for param in search_params:
            urls.append(f"{self.search_url}{param}")
        
        return urls
    
    def _extract_job_links_from_search(self, html_content: str, base_url: str) -> List[str]:
        """Extract job links from LEEM search results."""
        soup = HTMLParser.parse_html(html_content)
        if not soup:
            return []
        
        job_links = []
        
        # LEEM job listing selectors
        job_link_selectors = [
            '.job-item a',
            '.offre-emploi a',
            'a[href*="/offre/"]',
            '.liste-offres a'
        ]
        
        for selector in job_link_selectors:
            links = soup.select(selector)
            for link in links:
                href = link.get('href')
                if href:
                    full_url = urljoin(base_url, href)
                    if full_url not in job_links:
                        job_links.append(full_url)
        
        return job_links
    
    def _extract_job_data_from_page(self, html_content: str, job_url: str) -> Optional[Dict[str, Any]]:
        """Extract job data from LEEM job page."""
        soup = HTMLParser.parse_html(html_content)
        if not soup:
            return None
        
        try:
            job_data = {
                'link': job_url,
                'source': 'leem'
            }
            
            # Job title
            title_selectors = [
                'h1.job-title',
                '.offre-titre h1',
                'h1',
                '.job-header h1'
            ]
            
            for selector in title_selectors:
                title_elem = soup.select_one(selector)
                if title_elem:
                    job_data['job_title'] = HTMLParser.extract_text(title_elem)
                    break
            
            # Company name
            company_selectors = [
                '.company-name',
                '.entreprise',
                '.job-company',
                '.offre-entreprise'
            ]
            
            for selector in company_selectors:
                company_elem = soup.select_one(selector)
                if company_elem:
                    job_data['company_name'] = HTMLParser.extract_text(company_elem)
                    break
            
            # Location
            location_selectors = [
                '.job-location',
                '.lieu',
                '.localisation',
                '.offre-lieu'
            ]
            
            for selector in location_selectors:
                location_elem = soup.select_one(selector)
                if location_elem:
                    location_text = HTMLParser.extract_text(location_elem)
                    city = self._extract_city_from_location(location_text)
                    if city:
                        job_data['city'] = city
                        break
            
            # Job description
            description_selectors = [
                '.job-description',
                '.offre-description',
                '.description',
                '.contenu'
            ]
            
            description_text = ""
            for selector in description_selectors:
                desc_elem = soup.select_one(selector)
                if desc_elem:
                    description_text = HTMLParser.extract_text(desc_elem)
                    break
            
            # Extract experience years
            experience_years = self._extract_experience_years(description_text)
            if experience_years is not None:
                job_data['year_of_experience'] = experience_years
            
            # Publication date
            job_data['published_date'] = datetime.now().isoformat()
            
            # Validate required fields
            required_fields = ['job_title', 'company_name']
            if all(field in job_data and job_data[field] for field in required_fields):
                # If no city found, default to Paris for LEEM jobs
                if 'city' not in job_data:
                    job_data['city'] = 'Paris'
                return job_data
            
            return None
            
        except Exception as e:
            logger.error(f"Error extracting LEEM job data from {job_url}: {e}")
            return None
    
    def _extract_city_from_location(self, location_text: str) -> Optional[str]:
        """Extract city from location text."""
        if not location_text:
            return None
        
        location_lower = location_text.lower()
        
        for city in ILE_DE_FRANCE_CITIES:
            if city in location_lower:
                return city.title()
        
        if any(term in location_lower for term in ['paris', 'île-de-france']):
            return 'Paris'
        
        return None
    
    def _extract_experience_years(self, description_text: str) -> Optional[int]:
        """Extract years of experience from description."""
        if not description_text:
            return 0
        
        patterns = [
            r'(\d+)\s*(?:ans?|années?)\s*(?:d\')?(?:expérience|experience)',
            r'(?:minimum|au moins)\s*(\d+)\s*(?:ans?|années?)',
            r'(\d+)\s*(?:à|-)\s*\d+\s*(?:ans?|années?)',
        ]
        
        description_lower = description_text.lower()
        
        for pattern in patterns:
            matches = re.findall(pattern, description_lower)
            if matches:
                try:
                    return int(matches[0])
                except (ValueError, IndexError):
                    continue
        
        return 0
    
    async def scrape_jobs(self, scraper: AsyncWebScraper) -> List[Dict[str, Any]]:
        """Scrape jobs from LEEM."""
        logger.info("Starting LEEM job scraping")
        
        all_jobs = []
        search_urls = self._build_search_urls()
        
        try:
            # Fetch search pages
            search_pages = await scraper.fetch_multiple_pages(search_urls)
            
            # Extract job links
            all_job_links = []
            for page_content in search_pages:
                if page_content:
                    job_links = self._extract_job_links_from_search(page_content, self.base_url)
                    all_job_links.extend(job_links)
            
            unique_job_links = list(set(all_job_links))[:20]  # Limit to 20 jobs
            
            # Fetch job pages
            job_pages = await scraper.fetch_multiple_pages(unique_job_links)
            
            # Extract job data
            for job_url, page_content in zip(unique_job_links, job_pages):
                if page_content:
                    job_data = self._extract_job_data_from_page(page_content, job_url)
                    if job_data:
                        all_jobs.append(job_data)
            
            logger.info(f"LEEM scraping completed: {len(all_jobs)} jobs extracted")
            return all_jobs
            
        except Exception as e:
            logger.error(f"Error during LEEM scraping: {e}")
            return []


class SnitemScraper:
    """Scraper for snitem.fr (French medical device industry jobs)."""
    
    def __init__(self):
        self.base_url = "https://www.snitem.fr"
        self.jobs_url = f"{self.base_url}/emploi"
    
    def _build_search_urls(self) -> List[str]:
        """Build search URLs for SNITEM job board."""
        return [
            self.jobs_url,
            f"{self.jobs_url}?search=réglementaire",
            f"{self.jobs_url}?search=regulatory",
            f"{self.jobs_url}?search=qualité"
        ]
    
    def _extract_job_links_from_search(self, html_content: str, base_url: str) -> List[str]:
        """Extract job links from SNITEM search results."""
        soup = HTMLParser.parse_html(html_content)
        if not soup:
            return []
        
        job_links = []
        
        job_link_selectors = [
            '.job-listing a',
            '.emploi-item a',
            'a[href*="/emploi/"]',
            '.offre a'
        ]
        
        for selector in job_link_selectors:
            links = soup.select(selector)
            for link in links:
                href = link.get('href')
                if href:
                    full_url = urljoin(base_url, href)
                    if full_url not in job_links:
                        job_links.append(full_url)
        
        return job_links
    
    def _extract_job_data_from_page(self, html_content: str, job_url: str) -> Optional[Dict[str, Any]]:
        """Extract job data from SNITEM job page."""
        soup = HTMLParser.parse_html(html_content)
        if not soup:
            return None
        
        try:
            job_data = {
                'link': job_url,
                'source': 'snitem'
            }
            
            # Similar extraction logic as LEEM
            title_selectors = ['h1', '.job-title', '.titre']
            for selector in title_selectors:
                title_elem = soup.select_one(selector)
                if title_elem:
                    job_data['job_title'] = HTMLParser.extract_text(title_elem)
                    break
            
            company_selectors = ['.company', '.entreprise', '.societe']
            for selector in company_selectors:
                company_elem = soup.select_one(selector)
                if company_elem:
                    job_data['company_name'] = HTMLParser.extract_text(company_elem)
                    break
            
            # Default values for SNITEM
            job_data['city'] = 'Paris'  # Most SNITEM jobs are in Paris area
            job_data['year_of_experience'] = 0
            job_data['published_date'] = datetime.now().isoformat()
            
            if job_data.get('job_title') and job_data.get('company_name'):
                return job_data
            
            return None
            
        except Exception as e:
            logger.error(f"Error extracting SNITEM job data from {job_url}: {e}")
            return None
    
    async def scrape_jobs(self, scraper: AsyncWebScraper) -> List[Dict[str, Any]]:
        """Scrape jobs from SNITEM."""
        logger.info("Starting SNITEM job scraping")
        
        all_jobs = []
        search_urls = self._build_search_urls()
        
        try:
            search_pages = await scraper.fetch_multiple_pages(search_urls)
            
            all_job_links = []
            for page_content in search_pages:
                if page_content:
                    job_links = self._extract_job_links_from_search(page_content, self.base_url)
                    all_job_links.extend(job_links)
            
            unique_job_links = list(set(all_job_links))[:15]  # Limit to 15 jobs
            
            job_pages = await scraper.fetch_multiple_pages(unique_job_links)
            
            for job_url, page_content in zip(unique_job_links, job_pages):
                if page_content:
                    job_data = self._extract_job_data_from_page(page_content, job_url)
                    if job_data:
                        all_jobs.append(job_data)
            
            logger.info(f"SNITEM scraping completed: {len(all_jobs)} jobs extracted")
            return all_jobs
            
        except Exception as e:
            logger.error(f"Error during SNITEM scraping: {e}")
            return []


class PharmaCompanyScraper:
    """Scraper for major pharmaceutical company career pages."""
    
    def __init__(self):
        self.company_urls = {
            'sanofi': 'https://careers.sanofi.com/en/search-jobs',
            'novartis': 'https://www.novartis.com/careers/career-search',
            'roche': 'https://careers.roche.com/global/en/search-results',
            'pfizer': 'https://www.pfizer.com/about/careers/job-search',
            'abbvie': 'https://careers.abbvie.com/search-jobs'
        }
    
    def _build_search_urls(self) -> List[str]:
        """Build search URLs for pharmaceutical company career pages."""
        urls = []
        
        for company, base_url in self.company_urls.items():
            # Add search parameters for regulatory affairs and France location
            search_params = [
                f"{base_url}?q=regulatory&location=france",
                f"{base_url}?q=regulatory+affairs&location=paris",
                f"{base_url}?keywords=regulatory&country=france"
            ]
            urls.extend(search_params)
        
        return urls
    
    def _extract_job_data_from_search(self, html_content: str, company_name: str, base_url: str) -> List[Dict[str, Any]]:
        """Extract job data directly from search results page."""
        soup = HTMLParser.parse_html(html_content)
        if not soup:
            return []
        
        jobs = []
        
        # Generic selectors for job listings
        job_selectors = [
            '.job-item',
            '.search-result',
            '.job-listing',
            '.career-opportunity'
        ]
        
        for selector in job_selectors:
            job_elements = soup.select(selector)
            
            for job_elem in job_elements:
                try:
                    job_data = {
                        'source': 'pharma_company',
                        'company_name': company_name
                    }
                    
                    # Extract title
                    title_elem = job_elem.select_one('h2, h3, .job-title, .title')
                    if title_elem:
                        title = HTMLParser.extract_text(title_elem)
                        # Filter for regulatory-related jobs
                        if any(keyword in title.lower() for keyword in ['regulatory', 'réglementaire', 'compliance', 'quality']):
                            job_data['job_title'] = title
                        else:
                            continue
                    
                    # Extract location
                    location_elem = job_elem.select_one('.location, .job-location, .lieu')
                    if location_elem:
                        location_text = HTMLParser.extract_text(location_elem)
                        city = self._extract_city_from_location(location_text)
                        if city:
                            job_data['city'] = city
                        else:
                            continue  # Skip if not in Île-de-France
                    
                    # Extract link
                    link_elem = job_elem.select_one('a')
                    if link_elem:
                        href = link_elem.get('href')
                        if href:
                            job_data['link'] = urljoin(base_url, href)
                    
                    # Default values
                    job_data['year_of_experience'] = 2  # Assume mid-level for pharma
                    job_data['published_date'] = datetime.now().isoformat()
                    
                    if job_data.get('job_title') and job_data.get('city'):
                        jobs.append(job_data)
                
                except Exception as e:
                    logger.debug(f"Error extracting pharma job data: {e}")
                    continue
        
        return jobs
    
    def _extract_city_from_location(self, location_text: str) -> Optional[str]:
        """Extract city from location text."""
        if not location_text:
            return None
        
        location_lower = location_text.lower()
        
        for city in ILE_DE_FRANCE_CITIES:
            if city in location_lower:
                return city.title()
        
        if any(term in location_lower for term in ['paris', 'île-de-france', 'france']):
            return 'Paris'
        
        return None
    
    async def scrape_jobs(self, scraper: AsyncWebScraper) -> List[Dict[str, Any]]:
        """Scrape jobs from pharmaceutical company career pages."""
        logger.info("Starting pharmaceutical company job scraping")
        
        all_jobs = []
        search_urls = self._build_search_urls()
        
        try:
            # Limit to avoid overwhelming company sites
            limited_urls = search_urls[:10]
            search_pages = await scraper.fetch_multiple_pages(limited_urls)
            
            for i, page_content in enumerate(search_pages):
                if page_content:
                    # Determine company name from URL
                    url = limited_urls[i]
                    company_name = 'Unknown'
                    for company, company_url in self.company_urls.items():
                        if company_url in url:
                            company_name = company.title()
                            break
                    
                    jobs = self._extract_job_data_from_search(page_content, company_name, url)
                    all_jobs.extend(jobs)
            
            logger.info(f"Pharmaceutical company scraping completed: {len(all_jobs)} jobs extracted")
            return all_jobs
            
        except Exception as e:
            logger.error(f"Error during pharmaceutical company scraping: {e}")
            return []


class SpecializedScrapersManager:
    """Manager for all specialized scrapers."""
    
    def __init__(self):
        self.leem_scraper = LeemScraper()
        self.snitem_scraper = SnitemScraper()
        self.pharma_scraper = PharmaCompanyScraper()
    
    async def scrape_all_specialized_sites(self, scraper: AsyncWebScraper) -> List[Dict[str, Any]]:
        """Scrape all specialized sites concurrently."""
        logger.info("Starting specialized sites scraping")
        
        # Run all scrapers concurrently
        tasks = [
            self.leem_scraper.scrape_jobs(scraper),
            self.snitem_scraper.scrape_jobs(scraper),
            self.pharma_scraper.scrape_jobs(scraper)
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        all_jobs = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Specialized scraper {i} failed: {result}")
            elif isinstance(result, list):
                all_jobs.extend(result)
        
        logger.info(f"Specialized sites scraping completed: {len(all_jobs)} total jobs")
        return all_jobs