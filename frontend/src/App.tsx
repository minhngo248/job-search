import { useState, useEffect } from 'react'
import './App.css'
import { JobFilters, JobList } from './components'
import { useJobs } from './hooks'

interface AppConfig {
  appName: string;
  appVersion: string;
  apiGatewayUrl: string;
  apiKey: string;
}

function App() {
  const [config, setConfig] = useState<AppConfig | null>(null)
  const [configError, setConfigError] = useState<string | null>(null)
  const [configLoading, setConfigLoading] = useState(true)

  const {
    jobs,
    loading: jobsLoading,
    error: jobsError,
    totalCount,
    filters,
    setFilters,
    refreshJobs,
    clearError
  } = useJobs();

  useEffect(() => {
    const loadConfig = async () => {
      try {
        const configModule = await import('./config');
        const loadedConfig = configModule.config;
        
        console.log('Configuration loaded successfully:', {
          appName: loadedConfig.appName,
          appVersion: loadedConfig.appVersion,
          apiUrl: loadedConfig.apiGatewayUrl,
          hasApiKey: !!loadedConfig.apiKey,
        });
        
        setConfig(loadedConfig);
      } catch (error) {
        console.error('Configuration error:', error);
        const errorMessage = error instanceof Error ? error.message : 'Unknown configuration error';
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
    )
  }

  if (configError) {
    return (
      <div className="app-error" role="alert">
        <div className="error-icon" aria-hidden="true">⚠️</div>
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
    )
  }

  if (!config) {
    return (
      <div className="app-error" role="alert">
        <div className="error-icon" aria-hidden="true">⚠️</div>
        <h1>Erreur de Configuration</h1>
        <p>La configuration n'a pas pu être chargée</p>
        <button 
          onClick={() => window.location.reload()}
          aria-label="Recharger la page pour réessayer"
        >
          Recharger la page
        </button>
      </div>
    )
  }

  return (
    <div className="app">
      <a href="#main-content" className="skip-link">
        Aller au contenu principal
      </a>
      
      <header className="app-header" role="banner">
        <div className="header-content">
          <h1>{config.appName}</h1>
          <p className="app-subtitle">
            Offres d'emploi en affaires réglementaires - Dispositifs médicaux
          </p>
        </div>
      </header>
      
      <main className="app-main" role="main" id="main-content">
        <div className="main-content">
          <aside className="filters-sidebar" role="complementary" aria-label="Filtres de recherche">
            <JobFilters
              filters={filters}
              onFiltersChange={setFilters}
              loading={jobsLoading}
            />
          </aside>
          
          <section className="jobs-section" role="region" aria-label="Liste des offres d'emploi">
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
              totalCount={totalCount}
            />
          </section>
        </div>
      </main>
      
      <footer className="app-footer" role="contentinfo">
        <p>Version {config.appVersion} • Données mises à jour 3 fois par jour</p>
      </footer>
    </div>
  )
}

export default App
