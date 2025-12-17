"""
Data models for the regulatory jobs application.
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, validator
from .validation import validate_ile_de_france_city, normalize_date


class JobRecord(BaseModel):
    """
    Job record model representing a medical device regulatory job posting.
    
    This model defines the structure and validation rules for job postings
    stored in DynamoDB and returned by the API.
    """
    job_id: str = Field(..., description="Primary key (hash of URL)")
    job_title: str = Field(..., min_length=1, description="Job title")
    company_name: str = Field(..., min_length=1, description="Company name")
    city: str = Field(..., min_length=1, description="City within Île-de-France")
    year_of_experience: int = Field(..., ge=0, le=50, description="Required years of experience")
    published_date: str = Field(..., description="ISO 8601 date string")
    link: str = Field(..., min_length=1, description="Original job posting URL")
    source: str = Field(..., min_length=1, description="Source website")
    description: Optional[str] = Field(None, description="Job description")
    salary_range: Optional[str] = Field(None, description="Salary information if available")
    created_at: str = Field(..., description="Timestamp when record was created")
    updated_at: str = Field(..., description="Timestamp when record was last updated")

    @validator('city')
    def validate_city_in_ile_de_france(cls, v: str) -> str:
        """Validate that the city is within the Île-de-France region."""
        if not validate_ile_de_france_city(v):
            raise ValueError(f"City '{v}' is not in the Île-de-France region")
        return v

    @validator('published_date')
    def validate_and_normalize_published_date(cls, v: str) -> str:
        """Validate and normalize the published date to ISO 8601 format."""
        return normalize_date(v)

    @validator('created_at', 'updated_at')
    def validate_timestamp_format(cls, v: str) -> str:
        """Validate that timestamps are in ISO 8601 format."""
        return normalize_date(v)

    @validator('link')
    def validate_url_format(cls, v: str) -> str:
        """Basic URL validation."""
        if not (v.startswith('http://') or v.startswith('https://')):
            raise ValueError("Link must be a valid HTTP/HTTPS URL")
        return v

    class Config:
        """Pydantic configuration."""
        # Allow extra fields for future extensibility
        extra = "forbid"
        # Use enum values for serialization
        use_enum_values = True
        # Validate assignment
        validate_assignment = True


class JobFilters(BaseModel):
    """
    Model for job filtering parameters used in API queries.
    """
    published_after: Optional[str] = Field(None, description="ISO date string for minimum publication date")
    min_experience: Optional[int] = Field(None, ge=0, le=50, description="Minimum years of experience")
    max_experience: Optional[int] = Field(None, ge=0, le=50, description="Maximum years of experience")
    city: Optional[str] = Field(None, min_length=1, description="City name filter")

    @validator('published_after')
    def validate_published_after_date(cls, v: Optional[str]) -> Optional[str]:
        """Validate and normalize the published_after date."""
        if v is None:
            return v
        return normalize_date(v)

    @validator('city')
    def validate_filter_city(cls, v: Optional[str]) -> Optional[str]:
        """Validate that the filter city is within Île-de-France if provided."""
        if v is None:
            return v
        if not validate_ile_de_france_city(v):
            raise ValueError(f"City '{v}' is not in the Île-de-France region")
        return v

    @validator('max_experience')
    def validate_experience_range(cls, v: Optional[int], values: dict) -> Optional[int]:
        """Validate that max_experience is greater than or equal to min_experience."""
        if v is not None and 'min_experience' in values and values['min_experience'] is not None:
            if v < values['min_experience']:
                raise ValueError("max_experience must be greater than or equal to min_experience")
        return v


class JobsResponse(BaseModel):
    """
    Model for API response containing job listings.
    """
    jobs: list[JobRecord] = Field(..., description="List of job records")
    total_count: int = Field(..., ge=0, description="Total number of jobs matching filters")
    filters_applied: JobFilters = Field(..., description="Filters that were applied to the query")


class ErrorResponse(BaseModel):
    """
    Model for API error responses.
    """
    error: str = Field(..., min_length=1, description="Error type or code")
    message: str = Field(..., min_length=1, description="Human-readable error message")
    timestamp: str = Field(..., description="ISO 8601 timestamp when error occurred")

    @validator('timestamp')
    def validate_error_timestamp(cls, v: str) -> str:
        """Validate that error timestamp is in ISO 8601 format."""
        return normalize_date(v)