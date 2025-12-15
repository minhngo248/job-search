import React from 'react';
import type { JobRecord } from '../services/api';
import { JobCard } from './JobCard';
import './JobList.css';

interface JobListProps {
  jobs: JobRecord[];
  loading: boolean;
  error: string | null;
  totalCount: number;
  onLoadMore?: () => void;
  hasMore?: boolean;
  loadingMore?: boolean;
}

export const JobList: React.FC<JobListProps> = ({
  jobs,
  loading,
  error,
  totalCount,
  onLoadMore,
  hasMore = false,
  loadingMore = false
}) => {
  if (loading && jobs.length === 0) {
    return (
      <div className="job-list-container">
        <div className="loading-state" role="status" aria-live="polite">
          <div className="loading-spinner" aria-hidden="true"></div>
          <p>Chargement des offres d'emploi...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="job-list-container">
        <div className="error-state" role="alert">
          <div className="error-icon" aria-hidden="true">⚠️</div>
          <h3>Erreur lors du chargement</h3>
          <p>{error}</p>
          <button 
            className="retry-button"
            onClick={() => window.location.reload()}
            aria-label="Réessayer de charger les offres d'emploi"
          >
            Réessayer
          </button>
        </div>
      </div>
    );
  }

  if (jobs.length === 0) {
    return (
      <div className="job-list-container">
        <div className="empty-state" role="status">
          <div className="empty-icon" aria-hidden="true">🔍</div>
          <h3>Aucune offre trouvée</h3>
          <p>Aucune offre d'emploi ne correspond à vos critères de recherche.</p>
          <p>Essayez de modifier vos filtres pour voir plus de résultats.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="job-list-container">
      <div className="job-list-header">
        <h2 id="job-count-heading">
          {totalCount} offre{totalCount > 1 ? 's' : ''} d'emploi trouvée{totalCount > 1 ? 's' : ''}
        </h2>
        {jobs.length < totalCount && (
          <p className="showing-count" aria-describedby="job-count-heading">
            Affichage de {jobs.length} sur {totalCount} offres
          </p>
        )}
      </div>

      <div 
        className="job-list" 
        role="list" 
        aria-label={`Liste de ${jobs.length} offres d'emploi`}
        aria-describedby="job-count-heading"
      >
        {jobs.map((job) => (
          <div key={job.job_id} role="listitem">
            <JobCard job={job} />
          </div>
        ))}
      </div>

      {hasMore && onLoadMore && (
        <div className="load-more-section">
          <button
            className="load-more-button"
            onClick={onLoadMore}
            disabled={loadingMore}
            aria-label={loadingMore ? "Chargement en cours..." : "Charger plus d'offres d'emploi"}
          >
            {loadingMore ? (
              <>
                <div className="loading-spinner small" aria-hidden="true"></div>
                Chargement...
              </>
            ) : (
              'Charger plus d\'offres'
            )}
          </button>
        </div>
      )}
    </div>
  );
};