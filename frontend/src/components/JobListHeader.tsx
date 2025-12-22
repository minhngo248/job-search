import React, { useState } from 'react';
import './JobListHeader.css';

export type SortOption = 'date_desc' | 'date_asc' | 'experience_desc' | 'experience_asc' | 'company_asc' | 'company_desc';
export type ViewMode = 'grid' | 'list';

interface JobListHeaderProps {
  totalCount: number;
  displayedCount: number;
  sortBy: SortOption;
  onSortChange: (sortBy: SortOption) => void;
  viewMode?: ViewMode;
  onViewModeChange?: (viewMode: ViewMode) => void;
  searchQuery?: string;
  onSearchChange?: (query: string) => void;
  loading?: boolean;
}

const SORT_OPTIONS: { value: SortOption; label: string }[] = [
  { value: 'date_desc', label: 'Plus récentes' },
  { value: 'date_asc', label: 'Plus anciennes' },
  { value: 'experience_desc', label: 'Expérience décroissante' },
  { value: 'experience_asc', label: 'Expérience croissante' },
  { value: 'company_asc', label: 'Entreprise A-Z' },
  { value: 'company_desc', label: 'Entreprise Z-A' },
];

export const JobListHeader: React.FC<JobListHeaderProps> = ({
  totalCount,
  displayedCount,
  sortBy,
  onSortChange,
  viewMode = 'grid',
  onViewModeChange,
  searchQuery = '',
  onSearchChange,
  loading = false
}) => {
  const [localSearchQuery, setLocalSearchQuery] = useState(searchQuery);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSearchChange?.(localSearchQuery);
  };

  const handleSearchClear = () => {
    setLocalSearchQuery('');
    onSearchChange?.('');
  };
  return (
    <div className="job-list-header-enhanced">
      {/* Search bar */}
      {onSearchChange && (
        <form className="search-bar" onSubmit={handleSearchSubmit}>
          <div className="search-input-wrapper">
            <input
              type="text"
              value={localSearchQuery}
              onChange={(e) => setLocalSearchQuery(e.target.value)}
              placeholder="Rechercher par titre, entreprise..."
              className="search-input"
              disabled={loading}
              aria-label="Rechercher des offres d'emploi"
            />
            {localSearchQuery && (
              <button
                type="button"
                onClick={handleSearchClear}
                className="search-clear"
                aria-label="Effacer la recherche"
              >
                ×
              </button>
            )}
          </div>
          <button
            type="submit"
            className="search-button"
            disabled={loading}
            aria-label="Lancer la recherche"
          >
            🔍 Rechercher
          </button>
        </form>
      )}
      
      <div className="header-main">
        <div className="job-count-section">
          <h2 id="job-count-heading">
            {totalCount} offre{totalCount > 1 ? 's' : ''} d'emploi trouvée{totalCount > 1 ? 's' : ''}
          </h2>
          {displayedCount < totalCount && (
            <p className="showing-count" aria-describedby="job-count-heading">
              Affichage de {displayedCount} sur {totalCount} offres
            </p>
          )}
        </div>
        
        <div className="header-controls">
          {/* View mode toggle */}
          {onViewModeChange && (
            <div className="view-toggle" role="group" aria-label="Mode d'affichage">
              <button
                className={`view-button ${viewMode === 'grid' ? 'active' : ''}`}
                onClick={() => onViewModeChange('grid')}
                disabled={loading}
                aria-label="Affichage en grille"
                aria-pressed={viewMode === 'grid'}
              >
                ⊞ Grille
              </button>
              <button
                className={`view-button ${viewMode === 'list' ? 'active' : ''}`}
                onClick={() => onViewModeChange('list')}
                disabled={loading}
                aria-label="Affichage en liste"
                aria-pressed={viewMode === 'list'}
              >
                ☰ Liste
              </button>
            </div>
          )}
          
          {/* Sort dropdown */}
          <div className="sort-control">
            <label htmlFor="sort-select" className="sort-label">
              Trier par:
            </label>
            <select
              id="sort-select"
              value={sortBy}
              onChange={(e) => onSortChange(e.target.value as SortOption)}
              disabled={loading}
              className="sort-select"
              aria-label="Sélectionner l'ordre de tri des offres d'emploi"
            >
              {SORT_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>
      
      {loading && (
        <div className="header-loading" role="status" aria-live="polite">
          <div className="loading-spinner small" aria-hidden="true"></div>
          <span>Mise à jour en cours...</span>
        </div>
      )}
    </div>
  );
};