import React, { useState, useEffect } from 'react';
import type { JobFilters as JobFiltersType } from '../services/api';
import './JobFilters.css';

interface JobFiltersProps {
  filters: JobFiltersType;
  onFiltersChange: (filters: JobFiltersType) => void;
  loading?: boolean;
}

export const JobFilters: React.FC<JobFiltersProps> = ({
  filters,
  onFiltersChange,
  loading = false
}) => {
  const [localFilters, setLocalFilters] = useState<JobFiltersType>(filters);
  const [isExpanded, setIsExpanded] = useState(false);

  // Update local filters when props change
  useEffect(() => {
    setLocalFilters(filters);
  }, [filters]);

  const handleFilterChange = (key: keyof JobFiltersType, value: string | undefined) => {
    const updatedFilters = { ...localFilters };

    if (!value) {
      delete updatedFilters[key];
    } else {
      updatedFilters[key] = value;
    }

    setLocalFilters(updatedFilters);
    onFiltersChange(updatedFilters);
  };

  const clearFilters = () => {
    const emptyFilters: JobFiltersType = {};
    setLocalFilters(emptyFilters);
    onFiltersChange(emptyFilters);
  };

  const hasActiveFilters = Object.keys(localFilters).length > 0;

  const formatDateForInput = (dateString?: string): string => {
    if (!dateString) return '';
    try {
      const date = new Date(dateString);
      return date.toISOString().split('T')[0];
    } catch {
      return '';
    }
  };

  const handleDateChange = (value: string) => {
    if (value) {
      const date = new Date(value);
      handleFilterChange('date_posted_after', date.toISOString());
    } else {
      handleFilterChange('date_posted_after', undefined);
    }
  };

  const formatSourceLabel = (value?: string) => {
    if (!value) return '';
    if (value.toLowerCase() === 'linkedin') return 'LinkedIn';
    if (value.toLowerCase() === 'adzuna') return 'Adzuna';
    return value;
  };

  return (
    <div className="job-filters">
      <div 
        className="filters-header"
        onClick={() => setIsExpanded(!isExpanded)}
        role="button"
        tabIndex={0}
        onKeyDown={(e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            setIsExpanded(!isExpanded);
          }
        }}
        aria-expanded={isExpanded}
        aria-controls="filters-content"
      >
        <h3 id="filters-heading">Filtres de recherche</h3>
        <button
          className="toggle-filters"
          onClick={(e) => {
            e.stopPropagation();
            setIsExpanded(!isExpanded);
          }}
          aria-expanded={isExpanded}
          aria-controls="filters-content"
          aria-label={isExpanded ? "Masquer les filtres" : "Afficher les filtres"}
        >
          {isExpanded ? '▲' : '▼'}
        </button>
      </div>

      <div 
        id="filters-content"
        className={`filters-content ${isExpanded ? 'expanded' : ''}`}
        aria-labelledby="filters-heading"
      >
        <div className="filter-group">
          <label htmlFor="job-title">Titre du poste</label>
          <input
            id="job-title"
            type="text"
            value={localFilters.title || ''}
            onChange={(e) => handleFilterChange('title', e.target.value)}
            disabled={loading}
            className="filter-input"
            placeholder="Ex: Responsable affaires réglementaires"
          />
        </div>

        <div className="filter-group">
          <label htmlFor="company-name">Entreprise</label>
          <input
            id="company-name"
            type="text"
            value={localFilters.company || ''}
            onChange={(e) => handleFilterChange('company', e.target.value)}
            disabled={loading}
            className="filter-input"
            placeholder="Ex: MedTech"
          />
        </div>

        <div className="filter-group">
          <label htmlFor="source-select">Source</label>
          <select
            id="source-select"
            value={localFilters.source || ''}
            onChange={(e) => handleFilterChange('source', e.target.value || undefined)}
            disabled={loading}
            className="filter-select"
          >
            <option value="">Toutes les sources</option>
            <option value="linkedin">LinkedIn</option>
            <option value="adzuna">Adzuna</option>
          </select>
        </div>

        <div className="filter-group">
          <label htmlFor="published-after">Date de publication</label>
          <input
            id="published-after"
            type="date"
            value={formatDateForInput(localFilters.date_posted_after)}
            onChange={(e) => handleDateChange(e.target.value)}
            disabled={loading}
            className="filter-input"
            aria-describedby="published-after-help"
          />
          <small id="published-after-help" className="filter-help">
            Afficher les offres publiées après cette date
          </small>
        </div>

        {hasActiveFilters && (
          <div className="filter-actions" role="group" aria-label="Actions des filtres">
            <button
              className="clear-filters-btn"
              onClick={clearFilters}
              disabled={loading}
              aria-label="Effacer tous les filtres actifs"
            >
              Effacer les filtres
            </button>
          </div>
        )}

        {hasActiveFilters && (
          <div className="active-filters" role="region" aria-label="Filtres actuellement actifs">
            <h4 id="active-filters-heading">Filtres actifs:</h4>
            <div className="filter-tags" role="list" aria-labelledby="active-filters-heading">
              {localFilters.title && (
                <span className="filter-tag" role="listitem">
                  Titre: {localFilters.title}
                  <button onClick={() => handleFilterChange('title', undefined)} aria-label="Supprimer le filtre de titre">
                    ×
                  </button>
                </span>
              )}
              {localFilters.company && (
                <span className="filter-tag" role="listitem">
                  Entreprise: {localFilters.company}
                  <button onClick={() => handleFilterChange('company', undefined)} aria-label="Supprimer le filtre d'entreprise">
                    ×
                  </button>
                </span>
              )}
              {localFilters.source && (
                <span className="filter-tag" role="listitem">
                  Source: {formatSourceLabel(localFilters.source)}
                  <button onClick={() => handleFilterChange('source', undefined)} aria-label="Supprimer le filtre de source">
                    ×
                  </button>
                </span>
              )}
              {localFilters.date_posted_after && (
                <span className="filter-tag" role="listitem">
                  Publié après: {formatDateForInput(localFilters.date_posted_after)}
                  <button onClick={() => handleFilterChange('date_posted_after', undefined)} aria-label="Supprimer le filtre de date">
                    ×
                  </button>
                </span>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};