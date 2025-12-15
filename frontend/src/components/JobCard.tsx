import React from 'react';
import type { JobRecord } from '../services/api';
import './JobCard.css';

interface JobCardProps {
  job: JobRecord;
}

export const JobCard: React.FC<JobCardProps> = ({ job }) => {
  const formatDate = (dateString: string): string => {
    try {
      const date = new Date(dateString);
      return date.toLocaleDateString('fr-FR', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
      });
    } catch {
      return dateString;
    }
  };

  const formatExperience = (years: number): string => {
    if (years === 0) return 'Débutant';
    if (years === 1) return '1 an d\'expérience';
    return `${years} ans d'expérience`;
  };

  const handleJobClick = () => {
    window.open(job.link, '_blank', 'noopener,noreferrer');
  };

  const handleKeyDown = (event: React.KeyboardEvent) => {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      handleJobClick();
    }
  };

  return (
    <article 
      className="job-card" 
      onClick={handleJobClick} 
      onKeyDown={handleKeyDown}
      role="button" 
      tabIndex={0}
      aria-label={`Offre d'emploi: ${job.job_title} chez ${job.company_name} à ${job.city}`}
    >
      <div className="job-card-header">
        <h3 className="job-title">{job.job_title}</h3>
        <span className="job-source" aria-label={`Source: ${job.source}`}>{job.source}</span>
      </div>
      
      <div className="job-card-body">
        <div className="company-info">
          <span className="company-name" aria-label={`Entreprise: ${job.company_name}`}>
            {job.company_name}
          </span>
          <span className="job-location" aria-label={`Localisation: ${job.city}`}>
            {job.city}
          </span>
        </div>
        
        <div className="job-details">
          <span 
            className="experience-level"
            aria-label={`Expérience requise: ${formatExperience(job.year_of_experience)}`}
          >
            {formatExperience(job.year_of_experience)}
          </span>
          <time 
            className="published-date"
            dateTime={job.published_date}
            aria-label={`Date de publication: ${formatDate(job.published_date)}`}
          >
            Publié le {formatDate(job.published_date)}
          </time>
        </div>
        
        {job.salary_range && (
          <div className="salary-info">
            <span 
              className="salary-range"
              aria-label={`Salaire: ${job.salary_range}`}
            >
              {job.salary_range}
            </span>
          </div>
        )}
        
        {job.description && (
          <div className="job-description">
            <p aria-label="Description du poste">
              {job.description.substring(0, 150)}...
            </p>
          </div>
        )}
      </div>
    </article>
  );
};