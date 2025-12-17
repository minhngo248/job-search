"""
Job scraper module for regulatory affairs positions.

This module provides web scraping capabilities for collecting medical device
regulatory job postings from multiple sources including LinkedIn, Glassdoor,
and specialized pharmaceutical industry job boards.
"""

from .lambda_handler import lambda_handler
from .job_processor import JobProcessor
from .web_utils import AsyncWebScraper
from .linkedin_scraper import LinkedInScraper
from .glassdoor_scraper import GlassdoorScraper
from .specialized_scrapers import SpecializedScrapersManager

__all__ = [
    'lambda_handler',
    'JobProcessor',
    'AsyncWebScraper',
    'LinkedInScraper',
    'GlassdoorScraper',
    'SpecializedScrapersManager'
]