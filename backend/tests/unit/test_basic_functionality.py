"""
Basic functionality tests to verify core components work.
"""
import pytest
from src.shared.models import JobRecord, JobFilters, JobsResponse, ErrorResponse
from src.shared.validation import validate_ile_de_france_city, normalize_date
from src.api.job_service import JobService
from src.api.auth import CognitoAuthValidator
from datetime import datetime


def test_job_record_creation():
    """Test that JobRecord can be created with valid data."""
    job_data = {
        "job_id": "test123",
        "job_title": "Regulatory Affairs Manager",
        "company_name": "Test Company",
        "city": "Paris",
        "year_of_experience": 5,
        "published_date": "2024-01-15",
        "link": "https://example.com/job/123",
        "source": "test_source",
        "created_at": "2024-01-15T10:00:00",
        "updated_at": "2024-01-15T10:00:00"
    }
    
    job = JobRecord(**job_data)
    assert job.job_title == "Regulatory Affairs Manager"
    assert job.city == "Paris"
    assert job.year_of_experience == 5


def test_job_filters_creation():
    """Test that JobFilters can be created with valid data."""
    filters = JobFilters(
        published_after="2024-01-01",
        min_experience=2,
        max_experience=10,
        city="Paris"
    )
    
    assert filters.published_after == "2024-01-01"
    assert filters.min_experience == 2
    assert filters.max_experience == 10
    assert filters.city == "Paris"


def test_ile_de_france_city_validation():
    """Test that Île-de-France city validation works."""
    # Valid cities
    assert validate_ile_de_france_city("Paris") == True
    assert validate_ile_de_france_city("Versailles") == True
    assert validate_ile_de_france_city("Nanterre") == True
    
    # Invalid cities
    assert validate_ile_de_france_city("Lyon") == False
    assert validate_ile_de_france_city("Marseille") == False
    assert validate_ile_de_france_city("") == False
    assert validate_ile_de_france_city(None) == False


def test_date_normalization():
    """Test that date normalization works correctly."""
    # Test various date formats
    assert normalize_date("2024-01-15") == "2024-01-15"
    assert normalize_date("2024-01-15T10:30:00") == "2024-01-15T10:30:00"
    
    # Test datetime object
    dt = datetime(2024, 1, 15, 10, 30, 0)
    result = normalize_date(dt)
    assert "2024-01-15T10:30:00" in result


def test_error_response_creation():
    """Test that ErrorResponse can be created."""
    error = ErrorResponse(
        error="TEST_ERROR",
        message="This is a test error",
        timestamp="2024-01-15T10:00:00"
    )
    
    assert error.error == "TEST_ERROR"
    assert error.message == "This is a test error"


def test_job_service_initialization():
    """Test that JobService can be initialized."""
    # This should not fail even without DynamoDB connection
    service = JobService("test-table")
    assert service.table_name == "test-table"


def test_auth_validator_initialization():
    """Test that CognitoAuthValidator can be initialized."""
    # This should not fail even without Cognito configuration
    validator = CognitoAuthValidator()
    assert validator is not None