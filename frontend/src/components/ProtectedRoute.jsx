import { Navigate } from 'react-router-dom';
import { useAnalysis } from '../context/AnalysisContext';

const ProtectedRoute = ({ children }) => {
  const { user, loading } = useAnalysis();

  if (loading) {
    // Premium loading indicator
    return (
      <div className="min-h-screen bg-[#0d0e12] flex items-center justify-center flex-col gap-4 text-slate-100">
        <div className="w-12 h-12 rounded-full border-4 border-indigo-500/20 border-t-indigo-500 animate-spin"></div>
        <p className="text-slate-400 text-sm font-medium tracking-wide">Securing session...</p>
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  return children;
};

export default ProtectedRoute;
