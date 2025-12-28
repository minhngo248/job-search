from typing import Optional
from pydantic import BaseModel

class JobModel(BaseModel):
    """
    Job record model representing a medical device regulatory job posting.
    
    This model defines the structure and validation rules for job postings
    stored in DynamoDB and returned by the API.
    """
    id: str
    job_title: str
    company_name: str
    link: str
    source: str
    year_of_experience: int
    published_date: str
    description: Optional[str] = None
    salary_range: Optional[float] = None,
    created_at: Optional[str] = None,
    updated_at: Optional[str] = None