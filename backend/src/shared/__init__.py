"""
Shared utilities and models for the regulatory jobs application.
"""
from .models import JobRecord, JobFilters, JobsResponse, ErrorResponse
from .validation import (
    validate_ile_de_france_city,
    normalize_date,
    validate_job_record_completeness,
    generate_job_id,
    ILE_DE_FRANCE_CITIES
)

__all__ = [
    'JobRecord',
    'JobFilters', 
    'JobsResponse',
    'ErrorResponse',
    'validate_ile_de_france_city',
    'normalize_date',
    'validate_job_record_completeness',
    'generate_job_id',
    'ILE_DE_FRANCE_CITIES'
]