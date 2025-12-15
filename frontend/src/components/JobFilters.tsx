import React, { useState, useEffect } from 'react';
import type { JobFilters as JobFiltersType } from '../services/api';
import './JobFilters.css';

interface JobFiltersProps {
  filters: JobFiltersType;
  onFiltersChange: (filters: JobFiltersType) => void;
  loading?: boolean;
}

// Île-de-France cities for the dropdown
const ILE_DE_FRANCE_CITIES = [
  'Paris',
  'Boulogne-Billancourt',
  'Saint-Denis',
  'Argenteuil',
  'Montreuil',
  'Créteil',
  'Nanterre',
  'Courbevoie',
  'Versailles',
  'Rueil-Malmaison',
  'Aubervilliers',
  'Champigny-sur-Marne',
  'Saint-Maur-des-Fossés',
  'Drancy',
  'Issy-les-Moulineaux',
  'Levallois-Perret',
  'Antony',
  'Neuilly-sur-Seine',
  'Vitry-sur-Seine',
  'Clichy',
  'Sarcelles',
  'Ivry-sur-Seine',
  'Villejuif',
  'Épinay-sur-Seine',
  'Colombes',
  'Asnières-sur-Seine',
  'Aulnay-sous-Bois',
  'Garges-lès-Gonesse',
  'Bondy',
  'Maisons-Alfort',
  'Meaux',
  'Pontault-Combault',
  'Bobigny',
  'Rosny-sous-Bois',
  'Choisy-le-Roi',
  'Sartrouville',
  'Sevran',
  'Vincennes',
  'Livry-Gargan',
  'Cergy',
  'Sainte-Geneviève-des-Bois',
  'Viry-Châtillon',
  'Athis-Mons',
  'Palaiseau',
  'Conflans-Sainte-Honorine',
  'Montrouge',
  'Bagnolet',
  'Bagneux',
  'Nogent-sur-Marne',
  'Malakoff'
].sort();

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

  const handleFilterChange = (key: keyof JobFiltersType, value: string | number | undefined) => {
    const newFilters = { ...localFilters };
    
    if (value === '' || value === undefined) {
      delete newFilters[key];
    } else {
      (newFilters as Record<string, string | number>)[key] = value;
    }
    
    setLocalFilters(newFilters);
  };

  const applyFilters = () => {
    onFiltersChange(localFilters);
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
      // Convert to ISO string for API
      const date = new Date(value);
      handleFilterChange('published_after', date.toISOString());
    } else {
      handleFilterChange('published_after', undefined);
    }
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
          <label htmlFor="published-after">Date de publication</label>
          <input
            id="published-after"
            type="date"
            value={formatDateForInput(localFilters.published_after)}
            onChange={(e) => handleDateChange(e.target.value)}
            disabled={loading}
            className="filter-input"
            aria-describedby="published-after-help"
          />
          <small id="published-after-help" className="filter-help">
            Afficher les offres publiées après cette date
          </small>
        </div>

        <div className="filter-group">
          <label htmlFor="experience-min">Expérience minimum (années)</label>
          <select
            id="experience-min"
            value={localFilters.min_experience || ''}
            onChange={(e) => handleFilterChange('min_experience', e.target.value ? parseInt(e.target.value) : undefined)}
            disabled={loading}
            className="filter-select"
            aria-label="Sélectionner l'expérience minimum requise"
          >
            <option value="">Toutes</option>
            <option value="0">Débutant (0 an)</option>
            <option value="1">1 an</option>
            <option value="2">2 ans</option>
            <option value="3">3 ans</option>
            <option value="5">5 ans</option>
            <option value="7">7 ans</option>
            <option value="10">10 ans et plus</option>
          </select>
        </div>

        <div className="filter-group">
          <label htmlFor="experience-max">Expérience maximum (années)</label>
          <select
            id="experience-max"
            value={localFilters.max_experience || ''}
            onChange={(e) => handleFilterChange('max_experience', e.target.value ? parseInt(e.target.value) : undefined)}
            disabled={loading}
            className="filter-select"
            aria-label="Sélectionner l'expérience maximum requise"
          >
            <option value="">Toutes</option>
            <option value="1">1 an</option>
            <option value="2">2 ans</option>
            <option value="3">3 ans</option>
            <option value="5">5 ans</option>
            <option value="7">7 ans</option>
            <option value="10">10 ans</option>
            <option value="15">15 ans</option>
          </select>
        </div>

        <div className="filter-group">
          <label htmlFor="city-filter">Ville</label>
          <select
            id="city-filter"
            value={localFilters.city || ''}
            onChange={(e) => handleFilterChange('city', e.target.value || undefined)}
            disabled={loading}
            className="filter-select"
            aria-describedby="city-filter-help"
          >
            <option value="">Toutes les villes</option>
            {ILE_DE_FRANCE_CITIES.map((city) => (
              <option key={city} value={city}>
                {city}
              </option>
            ))}
          </select>
          <small id="city-filter-help" className="filter-help">
            Villes de la région Île-de-France
          </small>
        </div>

        <div className="filter-actions" role="group" aria-label="Actions des filtres">
          <button
            className="apply-filters-btn"
            onClick={applyFilters}
            disabled={loading}
            aria-label={loading ? 'Application des filtres en cours...' : 'Appliquer les filtres sélectionnés'}
          >
            {loading ? 'Application...' : 'Appliquer les filtres'}
          </button>
          
          {hasActiveFilters && (
            <button
              className="clear-filters-btn"
              onClick={clearFilters}
              disabled={loading}
              aria-label="Effacer tous les filtres actifs"
            >
              Effacer les filtres
            </button>
          )}
        </div>

        {hasActiveFilters && (
          <div className="active-filters" role="region" aria-label="Filtres actuellement actifs">
            <h4 id="active-filters-heading">Filtres actifs:</h4>
            <div className="filter-tags" role="list" aria-labelledby="active-filters-heading">
              {localFilters.published_after && (
                <span className="filter-tag" role="listitem">
                  Publié après: {formatDateForInput(localFilters.published_after)}
                  <button 
                    onClick={() => handleFilterChange('published_after', undefined)}
                    aria-label="Supprimer le filtre de date de publication"
                  >
                    ×
                  </button>
                </span>
              )}
              {localFilters.min_experience !== undefined && (
                <span className="filter-tag" role="listitem">
                  Min: {localFilters.min_experience} an{localFilters.min_experience > 1 ? 's' : ''}
                  <button 
                    onClick={() => handleFilterChange('min_experience', undefined)}
                    aria-label="Supprimer le filtre d'expérience minimum"
                  >
                    ×
                  </button>
                </span>
              )}
              {localFilters.max_experience !== undefined && (
                <span className="filter-tag" role="listitem">
                  Max: {localFilters.max_experience} an{localFilters.max_experience > 1 ? 's' : ''}
                  <button 
                    onClick={() => handleFilterChange('max_experience', undefined)}
                    aria-label="Supprimer le filtre d'expérience maximum"
                  >
                    ×
                  </button>
                </span>
              )}
              {localFilters.city && (
                <span className="filter-tag" role="listitem">
                  Ville: {localFilters.city}
                  <button 
                    onClick={() => handleFilterChange('city', undefined)}
                    aria-label={`Supprimer le filtre de ville: ${localFilters.city}`}
                  >
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