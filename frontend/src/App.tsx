import { Routes, Route } from 'react-router-dom';
import HomePage from './pages/HomePage';

// Import test utilities for development
if (import.meta.env.DEV) {
  import('./utils/responsiveTest');
  import('./utils/touchTest');
  import('./utils/performanceMonitor');
}

function App() {
  return (
    <Routes>
      <Route path="/" element={<HomePage />} />
    </Routes>
  );
}

export default App;
