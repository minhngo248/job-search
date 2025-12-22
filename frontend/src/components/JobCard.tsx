import React, { useState } from 'react';
import type { JobRecord } from '../services/api';
import './JobCard.css';

interface JobCardProps {
  job: JobRecord;
}

export const JobCard: React.FC<JobCardProps> = ({ job }) => {
  const [isDescriptionExpanded, setIsDescriptionExpanded] = useState(false);
  
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

  const formatSalary = (salaryRange?: string): string | null => {
    if (!salaryRange) return null;
    // Clean up salary display format
    return salaryRange.replace(/\s+/g, ' ').trim();
  };

  const getDescriptionPreview = (description?: string): { preview: string; hasMore: boolean } => {
    if (!description) return { preview: '', hasMore: false };
    
    const maxLength = 200;
    const cleanDescription = description.replace(/\s+/g, ' ').trim();
    
    if (cleanDescription.length <= maxLength) {
      return { preview: cleanDescription, hasMore: false };
    }
    
    // Find the last complete word within the limit
    const truncated = cleanDescription.substring(0, maxLength);
    const lastSpaceIndex = truncated.lastIndexOf(' ');
    const preview = lastSpaceIndex > 0 ? truncated.substring(0, lastSpaceIndex) : truncated;
    
    return { preview, hasMore: true };
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

  const handleDescriptionToggle = (event: React.MouseEvent) => {
    event.stopPropagation(); // Prevent card click when toggling description
    setIsDescriptionExpanded(!isDescriptionExpanded);
  };

  const { preview, hasMore } = getDescriptionPreview(job.description);
  const formattedSalary = formatSalary(job.salary_range);

  return (
    <article 
      className={`job-card ${job.is_featured ? 'featured' : ''}`}
      onClick={handleJobClick} 
      onKeyDown={handleKeyDown}
      role="button" 
      tabIndex={0}
      aria-label={`Offre d'emploi: ${job.job_title} chez ${job.company_name} à ${job.city}${job.is_featured ? ' (Offre mise en avant)' : ''}`}
    >
      {job.is_featured && (
        <div className="featured-badge" aria-label="Offre mise en avant">
          ⭐ Mise en avant
        </div>
      )}
      
      <div className="job-card-header">
        <div className="job-title-section">
          <h3 className="job-title">{job.job_title}</h3>
          {formattedSalary && (
            <div className="salary-info-header">
              <span 
                className="salary-range prominent"
                aria-label={`Salaire: ${formattedSalary}`}
              >
                {formattedSalary}
              </span>
            </div>
          )}
        </div>
        <span className="job-source" aria-label={`Source: ${job.source}`}>{job.source}</span>
      </div>
      
      <div className="job-card-body">
        <div className="company-info">
          <div className="company-section">
            {/* Company logo with fallback to placeholder */}
            <div className="company-logo-container">
              {job.company_logo_url ? (
                <img 
                  src={job.company_logo_url} 
                  alt={`Logo de ${job.company_name}`}
                  className="company-logo"
                  onError={(e) => {
                    // Fallback to placeholder if image fails to load
                    const target = e.target as HTMLImageElement;
                    target.style.display = 'none';
                    const placeholder = target.nextElementSibling as HTMLElement;
                    if (placeholder) placeholder.style.display = 'flex';
                  }}
                />
              ) : null}
              <div 
                className={`company-logo-placeholder ${job.company_logo_url ? 'fallback' : ''}`}
                style={{ display: job.company_logo_url ? 'none' : 'flex' }}
                aria-hidden="true"
              >
                <span className="company-initial">
                  {job.company_name.charAt(0).toUpperCase()}
                </span>
              </div>
            </div>
            <div className="company-details">
              <span className="company-name" aria-label={`Entreprise: ${job.company_name}`}>
                {job.company_name}
              </span>
              <span className="job-location" aria-label={`Localisation: ${job.city}`}>
                {job.city}
              </span>
            </div>
          </div>
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
        
        {/* Mobile salary display (hidden on desktop where it's in header) */}
        {formattedSalary && (
          <div className="salary-info-mobile">
            <span 
              className="salary-range"
              aria-label={`Salaire: ${formattedSalary}`}
            >
              {formattedSalary}
            </span>
          </div>
        )}
        
        {/* Enhanced description with truncation and expansion */}
        {preview && (
          <div className="job-description">
            <p aria-label="Description du poste">
              {isDescriptionExpanded ? job.description : preview}
              {hasMore && !isDescriptionExpanded && '...'}
            </p>
            {hasMore && (
              <button
                className="description-toggle"
                onClick={handleDescriptionToggle}
                aria-label={isDescriptionExpanded ? 'Réduire la description' : 'Voir plus de détails'}
                type="button"
              >
                {isDescriptionExpanded ? 'Voir moins' : 'Lire plus'}
              </button>
            )}
          </div>
        )}
        
        {/* Job tags */}
        {job.tags && job.tags.length > 0 && (
          <div className="job-tags" role="list" aria-label="Tags de l'offre">
            {job.tags.map((tag, index) => (
              <span key={index} className="job-tag" role="listitem">
                {tag}
              </span>
            ))}
          </div>
        )}
      </div>
    </article>
  );
};