from src.shared.models import JobModel
from typing import List
import logging
import uuid
import hashlib
from datetime import datetime, timezone

logger = logging.getLogger()

def generate_job_id(url: str) -> str:
    """Generate a unique job ID from URL using SHA-256 hash."""
    # Normalize URL by removing query parameters and fragments
    clean_url = url.split('?')[0].split('#')[0].strip().lower()
        
    # Generate hash
    hash_object = hashlib.sha256(clean_url.encode('utf-8'))
    job_id = hash_object.hexdigest()[:16]  # Use first 16 characters
        
    return job_id

class JobMapper:
    def map_adzuna_job(self, adzuna_job) -> List[JobModel]:
        job_data = adzuna_job.get('results', [])
        now = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
        jobs = []
        for job in job_data:
            job_model = JobModel(
                id=generate_job_id(job.get('redirect_url', '')),
                job_title=job.get('title'),
                company_name=job.get('company', {}).get('display_name'),
                link=job.get('redirect_url'),
                source='adzuna',
                year_of_experience=-1,
                published_date=job.get('created'),
                description=job.get('description'),
                salary_range=job.get('company', {}).get('average_salary'),
                created_at=now,
                updated_at=now
            )
            jobs.append(job_model)
        return jobs