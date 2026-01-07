import { useState, useEffect } from 'react';
import type { ChangeEvent } from 'react';
import '../App.css';
import { JobFilters, JobList } from '../components';
import { useJobs } from '../hooks';
import { useAuth } from '../hooks/useAuth';
import { signOutRedirect } from '../services/auth';

interface AppConfig {
  appName: string;
  appVersion: string;
  apiGatewayUrl: string;
}

const PAGE_SIZE_OPTIONS = [5, 10, 20, 50];

function HomePage() {
  const [config, setConfig] = useState<AppConfig | null>(null);
  const [configError, setConfigError] = useState<string | null>(null);
  const [configLoading, setConfigLoading] = useState(true);

  const auth = useAuth();

  const {
    jobs,
    loading: jobsLoading,
    error: jobsError,
    filters,
    setFilters,
    refreshJobs,
    clearError,
    pageSize,
    setPageSize,
    currentPage,
    hasNextPage,
    hasPreviousPage,
    goToNextPage,
    goToPreviousPage,
  } = useJobs();

  useEffect(() => {
    const loadConfig = async () => {
      try {
        const configModule = await import('../config');
        const loadedConfig = configModule.config;

        console.log('Configuration loaded successfully');

        setConfig(loadedConfig);
      } catch (error) {
        console.error('Configuration error:', error);
        const errorMessage =
          error instanceof Error ? error.message : 'Unknown configuration error';
        setConfigError(errorMessage);
      } finally {
        setConfigLoading(false);
      }
    };

    loadConfig();
  }, []);

  if (configLoading) {
    return (
      <div className="app-loading" role="status" aria-live="polite">
        <div className="loading-spinner" aria-hidden="true"></div>
        <h1>Chargement de l'application...</h1>
      </div>
    );
  }

  if (configError) {
    return (
      <div className="app-error" role="alert">
        <div className="error-icon" aria-hidden="true">
          ⚠️
        </div>
        <h1>Erreur de Configuration</h1>
        <p>{configError}</p>
        <p>Veuillez vérifier vos variables d'environnement et réessayer.</p>
        <button
          onClick={() => window.location.reload()}
          aria-label="Recharger la page pour réessayer"
        >
          Recharger la page
        </button>
      </div>
    );
  }

  if (!config) {
    return (
      <div className="app-error" role="alert">
        <div className="error-icon" aria-hidden="true">
          ⚠️
        </div>
        <h1>Erreur de Configuration</h1>
        <p>La configuration n'a pas pu être chargée</p>
        <button
          onClick={() => window.location.reload()}
          aria-label="Recharger la page pour réessayer"
        >
          Recharger la page
        </button>
      </div>
    );
  }

  const handleSignInClick = async () => {
    try {
      await auth.signinRedirect();
    } catch (error) {
      console.error('Unable to redirect to Cognito hosted UI', error);
    }
  };

  const isAuthenticated = auth?.isAuthenticated;

  const handlePageSizeChange = (event: ChangeEvent<HTMLSelectElement>) => {
    const value = Number(event.target.value);
    setPageSize(value);
  };

  const handleSignOutClick = async () => {
    try {
      await auth.removeUser();
    } catch (error) {
      console.error('Error clearing local auth state', error);
    }
    // Cognito expects non-standard `logout_uri` + `client_id`, so we rely on our helper
    signOutRedirect();
  };

  return (
    <div className="app">
      <a href="#main-content" className="skip-link">
        Aller au contenu principal
      </a>

      <header className="app-header" role="banner">
        <div className="header-content header-content-with-actions">
          <div>
            <h1>{config.appName}</h1>
            <p className="app-subtitle">
              Offres d'emploi en affaires réglementaires - Dispositifs médicaux
            </p>
          </div>
          <div className="header-actions">
            {!isAuthenticated && (
              <button
                type="button"
                className="header-button"
                onClick={handleSignInClick}
              >
                Sign In
              </button>
            )}
            {isAuthenticated && (
              <>
                <span className="header-hello">Hello Peoo</span>
                <button
                  type="button"
                  className="header-button"
                  onClick={handleSignOutClick}
                >
                  Sign Out
                </button>
              </>
            )}
          </div>
        </div>
      </header>

      <main className="app-main" role="main" id="main-content">
        <div className="main-content">
          <aside
            className="filters-sidebar"
            role="complementary"
            aria-label="Filtres de recherche"
          >
            <JobFilters
              filters={filters}
              onFiltersChange={setFilters}
              loading={jobsLoading}
            />
          </aside>

          <section
            className="jobs-section"
            role="region"
            aria-label="Liste des offres d'emploi"
          >
            {jobsError && (
              <div className="error-banner" role="alert" aria-live="polite">
                <span>{jobsError}</span>
                <div className="error-actions">
                  <button
                    onClick={clearError}
                    className="dismiss-error"
                    aria-label="Fermer le message d'erreur"
                  >
                    ×
                  </button>
                  <button
                    onClick={refreshJobs}
                    className="retry-error"
                    aria-label="Réessayer de charger les offres"
                  >
                    Réessayer
                  </button>
                </div>
              </div>
            )}

            <JobList
              jobs={jobs}
              loading={jobsLoading}
              error={jobsError}
            />

            <div className="pagination-controls" role="navigation" aria-label="Pagination des offres">
              <div className="page-info">
                <strong>Page</strong>
                <span>{currentPage}</span>
              </div>

              <div className="page-size-selector">
                <label htmlFor="page-size">Résultats / page</label>
                <select
                  id="page-size"
                  value={pageSize}
                  onChange={handlePageSizeChange}
                  disabled={jobsLoading}
                >
                  {PAGE_SIZE_OPTIONS.map((size) => (
                    <option key={size} value={size}>
                      {size}
                    </option>
                  ))}
                </select>
              </div>

              <div className="page-buttons">
                <button
                  type="button"
                  onClick={goToPreviousPage}
                  disabled={!hasPreviousPage || jobsLoading}
                >
                  ← Précédent
                </button>
                <button
                  type="button"
                  onClick={goToNextPage}
                  disabled={!hasNextPage || jobsLoading}
                >
                  Suivant →
                </button>
              </div>
            </div>
          </section>
        </div>
      </main>

      <footer className="app-footer" role="contentinfo">
        <p>
          Version {config.appVersion}  Données mises à jour 2 fois par jour
        </p>
      </footer>
    </div>
  );
}

export default HomePage;
