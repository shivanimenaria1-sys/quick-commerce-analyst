import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AnalysisProvider } from './context/AnalysisContext';
import { ThemeProvider } from './context/ThemeContext';
import Login from './pages/Login';
import Upload from './pages/Upload';
import Dashboard from './pages/Dashboard';
import ExploreKPIs from './pages/ExploreKPIs';
import ExploreVisualizations from './pages/ExploreVisualizations';
import VisualizationDetailPlaceholder from './pages/VisualizationDetailPlaceholder';
import ReportCenter from './pages/ReportCenter';
import { ToastProvider } from './context/ToastContext';
import ProtectedRoute from './components/ProtectedRoute';

function App() {
  return (
    <ThemeProvider>
      <ToastProvider>
        <AnalysisProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route 
              path="/upload" 
              element={
                <ProtectedRoute>
                  <Upload />
                </ProtectedRoute>
              } 
            />
            <Route 
              path="/analysis/kpis/:sessionId" 
              element={
                <ProtectedRoute>
                  <ExploreKPIs />
                </ProtectedRoute>
              } 
            />
            <Route 
              path="/analysis/visualizations/:sessionId" 
              element={
                <ProtectedRoute>
                  <ExploreVisualizations />
                </ProtectedRoute>
              } 
            />
            <Route 
              path="/analysis/visualizations/:sessionId/:visualizationId" 
              element={
                <ProtectedRoute>
                  <VisualizationDetailPlaceholder />
                </ProtectedRoute>
              } 
            />
            <Route 
              path="/reports/:sessionId" 
              element={
                <ProtectedRoute>
                  <ReportCenter />
                </ProtectedRoute>
              } 
            />
            <Route 
              path="/dashboard" 
              element={
                <ProtectedRoute>
                  <Dashboard />
                </ProtectedRoute>
              } 
            />
            {/* Default fallback redirects to login */}
            <Route path="*" element={<Navigate to="/login" replace />} />
          </Routes>
        </BrowserRouter>
      </AnalysisProvider>
      </ToastProvider>
    </ThemeProvider>
  );
}

export default App;
