import React from 'react';
import './JobCardSkeleton.css';

export const JobCardSkeleton: React.FC = () => {
  return (
    <div className="job-card-skeleton" aria-hidden="true">
      <div className="skeleton-header">
        <div className="skeleton-title-section">
          <div className="skeleton-title"></div>
          <div className="skeleton-salary"></div>
        </div>
        <div className="skeleton-source"></div>
      </div>
      
      <div className="skeleton-body">
        <div className="skeleton-company-section">
          <div className="skeleton-logo"></div>
          <div className="skeleton-company-details">
            <div className="skeleton-company-name"></div>
            <div className="skeleton-location"></div>
          </div>
        </div>
        
        <div className="skeleton-job-details">
          <div className="skeleton-experience"></div>
          <div className="skeleton-date"></div>
        </div>
        
        <div className="skeleton-description">
          <div className="skeleton-text-line"></div>
          <div className="skeleton-text-line"></div>
          <div className="skeleton-text-line short"></div>
        </div>
      </div>
    </div>
  );
};