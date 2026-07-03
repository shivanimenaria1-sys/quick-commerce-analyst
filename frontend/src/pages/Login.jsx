import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAnalysis } from '../context/AnalysisContext';
import { auth, GoogleAuthProvider, signInWithPopup } from '../firebase';

const Login = () => {
  const { user, setUser } = useAnalysis();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  // If already logged in, redirect to upload immediately
  useEffect(() => {
    if (user) {
      navigate('/upload');
    }
  }, [user, navigate]);

  const handleGoogleSignIn = async () => {
    setError('');
    setLoading(true);
    try {
      const provider = new GoogleAuthProvider();
      const result = await signInWithPopup(auth, provider);
      setUser(result.user);
      navigate('/upload');
    } catch (err) {
      console.error("Authentication error:", err);
      // Map common errors to friendly descriptions
      if (err.code === 'auth/popup-closed-by-user') {
        setError('Login cancelled. Please keep the Google popup window open to log in.');
      } else if (err.code === 'auth/network-request-failed') {
        setError('Network error. Please check your internet connection.');
      } else {
        setError(err.message || 'An error occurred during Google sign-in.');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#0d0e12] text-slate-100 flex items-center justify-center p-4 relative font-sans overflow-hidden">
      {/* Decorative gradient glow */}
      <div className="absolute top-0 left-1/4 w-96 h-96 bg-indigo-500/10 rounded-full blur-[100px] pointer-events-none"></div>
      <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-violet-600/10 rounded-full blur-[100px] pointer-events-none"></div>

      <div className="w-full max-w-md relative z-10 animate-fade-in">
        {/* Logo and Brand Title Header */}
        <div className="flex flex-col items-center mb-8">
          <div className="w-14 h-14 rounded-2xl bg-gradient-to-tr from-indigo-500 to-violet-600 flex items-center justify-center shadow-lg shadow-indigo-500/20 mb-4 animate-pulse">
            <svg className="w-8 h-8 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
          </div>
          <h1 className="text-3xl font-black bg-gradient-to-r from-white via-slate-100 to-slate-400 bg-clip-text text-transparent tracking-tight text-center">
            Quick Commerce Analyst
          </h1>
          <p className="text-slate-400 text-sm mt-2 text-center max-w-xs leading-relaxed">
            AI-driven fulfillment diagnostic, cost analytics, and profit margin analysis.
          </p>
        </div>

        {/* Card */}
        <div className="rounded-3xl border border-slate-800 bg-slate-900/40 p-8 backdrop-blur-md shadow-2xl">
          <h2 className="text-xl font-bold text-white mb-2 text-center">Welcome back</h2>
          <p className="text-slate-400 text-xs text-center mb-6">Sign in using your Google account to access your workspace.</p>

          {error && (
            <div className="mb-4 p-3.5 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-400 text-xs leading-relaxed">
              {error}
            </div>
          )}

          <button
            onClick={handleGoogleSignIn}
            disabled={loading}
            className="w-full flex items-center justify-center gap-3 px-5 py-3.5 rounded-xl border border-slate-700 bg-slate-800/40 hover:bg-slate-800/80 active:scale-[0.98] transition-all duration-200 cursor-pointer disabled:opacity-50 disabled:pointer-events-none font-medium text-sm text-white"
          >
            {loading ? (
              <div className="w-5 h-5 rounded-full border-2 border-indigo-400/20 border-t-indigo-400 animate-spin"></div>
            ) : (
              <svg className="w-5 h-5" viewBox="0 0 24 24">
                <path
                  fill="#EA4335"
                  d="M5.26620003,9.764517 C6.19875003,6.938637 8.85468754,4.90909091 12,4.90909091 C13.6909091,4.90909091 15.2181818,5.50909091 16.4181818,6.49090909 L19.9090909,3 C17.7818182,1.14545455 15.0545455,0 12,0 C7.31818182,0 3.27272727,2.69090909 1.28181818,6.62727273 L5.26620003,9.764517 Z"
                />
                <path
                  fill="#4285F4"
                  d="M16.0409091,14.0136364 C15.5454545,15.6181818 13.9363636,16.7272727 12,16.7272727 C8.97272727,16.7272727 6.42272727,14.8818182,5.38181818,12.2454545 L1.33636364,15.3545455 C3.36363636,19.3818182 7.5,22.0909091 12,22.0909091 C14.9454545,22.0909091 17.7,21.0545455 19.7454545,19.3272727 L16.0409091,14.0136364 Z"
                />
                <path
                  fill="#34A853"
                  d="M23.5227273,12 C23.5227273,11.2363636 23.4545455,10.5181818 23.3272727,9.81818182 L12,9.81818182 L12,14.1818182 L18.5,14.1818182 C18.2181818,15.6272727 17.3727273,16.8545455 16.0454545,17.7272727 L19.75,23.0545455 C21.9090909,21.0636364 23.5227273,17.8272727 23.5227273,12 Z"
                />
                <path
                  fill="#FBBC05"
                  d="M5.38181818,12.2454545 C5.11818182,11.4545455 4.97272727,10.6181818 4.97272727,9.75 C4.97272727,8.91818182 5.10909091,8.11818182 5.35454545,7.35454545 L1.37272727,4.21818182 C0.5,5.97272727 0,7.91818182 0,9.75 C0,11.6272727 0.522727273,13.5272727 1.43636364,15.2545455 L5.38181818,12.2454545 Z"
                />
              </svg>
            )}
            Sign in with Google
          </button>
        </div>
      </div>
    </div>
  );
};

export default Login;
