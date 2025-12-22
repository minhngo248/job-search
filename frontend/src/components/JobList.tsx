import React, { useMemo } from 'react';
import type { JobRecord } from '../services/api';
import { JobCard } from './JobCard';
import { JobCardSkeleton } from './JobCardSkeleton';
import { JobListHeader, type SortOption } from './JobListHeader';
import { useKeyboardNavigation } from '../hooks/useKeyboardNavigation';
import './JobList.css';

interface JobListProps {
  jobs?: JobRecord[];
  loading: boolean;
  error: string | null;
  totalCount: number;
  onLoadMore?: () => void;
  hasMore?: boolean;
  loadingMore?: boolean;
  enableVirtualScrolling?: boolean; // New prop for virtual scrolling
  sortBy?: SortOption;
  onSortChange?: (sortBy: SortOption) => void;
  enableKeyboardNavigation?: boolean;
}

export const JobList: React.FC<JobListProps> = ({
  jobs = [],
  loading,
  error,
  totalCount,
  onLoadMore,
  hasMore = false,
  loadingMore = false,
  enableVirtualScrolling = false,
  sortBy = 'date_desc',
  onSortChange,
  enableKeyboardNavigation = true
}) => {
  // Ensure jobs is always an array
  const safeJobs = jobs || [];
  
  // Determine if we should use virtual scrolling (for 1000+ jobs)
  const shouldUseVirtualScrolling = enableVirtualScrolling && safeJobs.length >= 1000;
  
  // Calculate grid columns based on viewport (simplified for now)
  const gridColumns = useMemo(() => {
    if (typeof window === 'undefined') return 1;
    const width = window.innerWidth;
    if (width >= 1920) return 5;
    if (width >= 1440) return 4;
    if (width >= 1024) return 3;
    if (width >= 768) return 2;
    return 1;
  }, []);
  
  // Keyboard navigation
  const { containerRef, currentIndex } = useKeyboardNavigation({
    itemCount: safeJobs.length,
    enabled: enableKeyboardNavigation && safeJobs.length > 0,
    gridColumns,
    onItemActivate: (index) => {
      // Open job link when Enter or Space is pressed
      const job = safeJobs[index];
      if (job) {
        window.open(job.link, '_blank', 'noopener,noreferrer');
      }
    }
  });
  
  // Generate skeleton items for loading state
  const skeletonItems = useMemo(() => {
    const count = loading && safeJobs.length === 0 ? 6 : 3; // Show 6 skeletons on initial load, 3 for load more
    return Array.from({ length: count }, (_, index) => (
      <div key={`skeleton-${index}`} role="listitem">
        <JobCardSkeleton />
      </div>
    ));
  }, [loading, safeJobs.length]);

  if (loading && safeJobs.length === 0) {
    return (
      <div className="job-list-container">
        <JobListHeader
          totalCount={0}
          displayedCount={0}
          sortBy={sortBy}
          onSortChange={onSortChange || (() => {})}
          loading={true}
        />
        <div 
          className="job-list skeleton-loading" 
          role="list" 
          aria-label="Chargement des offres d'emploi"
        >
          {skeletonItems}
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

  if (safeJobs.length === 0) {
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
      <JobListHeader
        totalCount={totalCount}
        displayedCount={safeJobs.length}
        sortBy={sortBy}
        onSortChange={onSortChange || (() => {})}
        loading={loading}
      />

      <div 
        ref={containerRef}
        className={`job-list ${shouldUseVirtualScrolling ? 'virtual-scrolling' : ''} ${enableKeyboardNavigation ? 'keyboard-navigation' : ''}`}
        role="list" 
        aria-label={`Liste de ${safeJobs.length} offres d'emploi`}
        aria-describedby="job-count-heading"
        tabIndex={enableKeyboardNavigation ? 0 : -1}
      >
        {safeJobs.map((job, index) => (
          <div 
            key={job.id} 
            role="listitem"
            className={enableKeyboardNavigation && index === currentIndex ? 'keyboard-focused' : ''}
          >
            <JobCard job={job} />
          </div>
        ))}
        
        {/* Show skeleton loading items while loading more */}
        {loadingMore && skeletonItems}
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
      
      {/* Performance indicator for large datasets */}
      {shouldUseVirtualScrolling && (
        <div className="performance-indicator" role="status" aria-live="polite">
          <small>Mode haute performance activé pour {safeJobs.length} offres</small>
        </div>
      )}
      
      {/* Keyboard navigation help */}
      {enableKeyboardNavigation && safeJobs.length > 0 && (
        <div className="keyboard-help" role="region" aria-label="Aide navigation clavier">
          <small>
            Navigation: ↑↓ pour naviguer, Entrée pour ouvrir, Home/End pour aller au début/fin
            {gridColumns > 1 && ', ←→ pour naviguer horizontalement'}
          </small>
        </div>
      )}
    </div>
  );
};