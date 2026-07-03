import { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useDropzone } from 'react-dropzone';
import { useAnalysis } from '../context/AnalysisContext';
import { REQUIRED_COLUMNS } from '../constants';
import { apiService } from '../services/api';

const Upload = () => {
  const { logout, user, setSessionId, setAnalysisResults } = useAnalysis();
  
  // Pipeline processing states
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [currentStep, setCurrentStep] = useState(''); // 'uploading', 'cleaning', 'engineering', 'kpis', 'insights'
  const [statusMessage, setStatusMessage] = useState('');
  
  const [errorMsg, setErrorMsg] = useState('');
  const [missingColumns, setMissingColumns] = useState([]);
  
  // For retries
  const [lastSessionId, setLastSessionId] = useState(null);
  
  const navigate = useNavigate();

  // Download template CSV client-side
  const handleDownloadTemplate = () => {
    const csvContent = REQUIRED_COLUMNS.join(",") + "\n";
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.setAttribute("href", url);
    link.setAttribute("download", "quick_commerce_template.csv");
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  // Run the full pipeline sequentially
  const runProcessingPipeline = async (sessionId) => {
    try {
      // Step 2: Clean Dataset
      setCurrentStep('cleaning');
      setStatusMessage('Step 1/4: Cleaning operations log (imputing fields, removing duplicates)...');
      const cleanReport = await apiService.cleanDataset(sessionId);

      // Step 3: Feature Engineering
      setCurrentStep('engineering');
      setStatusMessage('Step 2/4: Applying derived metrics (margins, delay checks, utilization)...');
      const engineeringReport = await apiService.engineerFeatures(sessionId);

      // Step 4: Calculate KPIs
      setCurrentStep('kpis');
      setStatusMessage('Step 3/4: Calculating operational and hyperlocal KPIs...');
      const kpis = await apiService.getKPIs(sessionId);

      // Step 5: Get AI Insights
      setCurrentStep('insights');
      setStatusMessage('Step 4/4: Consulting Gemini AI for diagnostics and recommendations...');
      const insights = await apiService.getInsights(sessionId);

      // Set results and navigate
      setAnalysisResults({
        cleaning_report: cleanReport,
        engineering: engineeringReport,
        kpis: kpis,
        insights: insights
      });
      
      navigate('/dashboard');
    } catch (err) {
      console.error("Pipeline failure:", err);
      setErrorMsg(err.message || 'An error occurred during pipeline calculations.');
      setCurrentStep('error');
    }
  };

  // Handle file drop
  const onDrop = useCallback(async (acceptedFiles) => {
    const selectedFile = acceptedFiles[0];
    if (!selectedFile) return;

    setFile(selectedFile);
    setUploading(true);
    setCurrentStep('uploading');
    setStatusMessage('Uploading CSV and validating headers schema...');
    setErrorMsg('');
    setMissingColumns([]);

    try {
      // Step 1: Upload CSV
      const uploadData = await apiService.uploadCSV(selectedFile);
      setSessionId(uploadData.session_id);
      setLastSessionId(uploadData.session_id);
      
      // Auto-run the rest of the pipeline
      await runProcessingPipeline(uploadData.session_id);
    } catch (err) {
      console.error("Upload error:", err);
      if (err.missingColumns) {
        setMissingColumns(err.missingColumns);
        setErrorMsg("Schema validation failed: Missing required columns.");
      } else {
        setErrorMsg(err.message || "Could not connect to the backend server. Please verify that the FastAPI server is running.");
      }
      setCurrentStep('error');
      setUploading(false);
    }
  }, [setSessionId]);

  const handleRetryPipeline = () => {
    if (lastSessionId) {
      setErrorMsg('');
      setUploading(true);
      runProcessingPipeline(lastSessionId);
    }
  };

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'text/csv': ['.csv']
    },
    multiple: false,
    disabled: uploading
  });

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-[#0d0e12] text-slate-800 dark:text-slate-100 font-sans relative transition-colors duration-200">
      {/* Background gradients */}
      <div className="absolute top-0 right-1/4 w-96 h-96 bg-indigo-500/5 rounded-full blur-[100px] pointer-events-none"></div>
      <div className="absolute bottom-0 left-1/4 w-96 h-96 bg-violet-500/5 rounded-full blur-[100px] pointer-events-none"></div>

      {/* Header */}
      <header className="sticky top-0 z-40 w-full border-b border-slate-200 dark:border-slate-800 bg-white/80 dark:bg-[#0d0e12]/80 backdrop-blur-md">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-indigo-500 to-violet-600 flex items-center justify-center">
              <svg className="w-4.5 h-4.5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            </div>
            <span className="text-lg font-bold tracking-tight">Quick Commerce Analyst</span>
          </div>

          <div className="flex items-center gap-4">
            {user && (
              <div className="flex items-center gap-3">
                <div className="hidden sm:flex flex-col text-right">
                  <span className="text-xs font-semibold">{user.displayName || "Analyst"}</span>
                  <span className="text-[10px] text-slate-500 dark:text-slate-400">{user.email}</span>
                </div>
                {user.photoURL ? (
                  <img src={user.photoURL} alt="Avatar" className="w-8 h-8 rounded-full border border-slate-350 dark:border-slate-700" />
                ) : (
                  <div className="w-8 h-8 rounded-full bg-slate-200 dark:bg-slate-800 flex items-center justify-center text-xs font-semibold border border-slate-300 dark:border-slate-700 text-slate-500">
                    {user.email?.charAt(0).toUpperCase()}
                  </div>
                )}
                <button
                  onClick={logout}
                  className="px-3 py-1.5 rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/50 dark:hover:bg-slate-800 text-xs font-medium cursor-pointer transition-all duration-200 text-slate-600 dark:text-slate-300"
                >
                  Logout
                </button>
              </div>
            )}
          </div>
        </div>
      </header>

      {/* Main content */}
      <main className="max-w-4xl mx-auto px-4 py-12 relative z-10">
        <section className="mb-8 text-center sm:text-left">
          <h2 className="text-2xl sm:text-3xl font-black tracking-tight">Upload Dataset</h2>
          <p className="text-slate-500 dark:text-slate-400 text-sm mt-1">Upload your transactional log file in CSV format to trigger the intelligence diagnostics.</p>
        </section>

        {/* Column checklist container */}
        <section className="rounded-2xl border border-slate-250 dark:border-slate-800 bg-white dark:bg-[#111217]/50 p-6 mb-8 shadow-sm">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-4">
            <div>
              <h3 className="text-sm font-bold tracking-wide">Required CSV Headers</h3>
              <p className="text-slate-500 dark:text-slate-400 text-xs mt-0.5">Your CSV dataset must contain exactly these 20 column headers (casing is ignored):</p>
            </div>
            <button
              onClick={handleDownloadTemplate}
              className="inline-flex items-center justify-center gap-1.5 px-3 py-1.5 rounded-lg bg-indigo-500/10 hover:bg-indigo-500/20 text-indigo-500 dark:text-indigo-400 font-semibold text-xs transition-all duration-200 border border-indigo-500/20 cursor-pointer"
            >
              <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
              </svg>
              Download CSV Template
            </button>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
            {REQUIRED_COLUMNS.map((col) => {
              const isMissing = missingColumns.includes(col);
              return (
                <div
                  key={col}
                  className={`px-3 py-1.5 rounded-lg border text-center text-[11px] font-semibold transition-all duration-200 ${
                    isMissing
                      ? 'bg-rose-500/10 border-rose-500/30 text-rose-500 dark:text-rose-400 shadow-sm'
                      : 'bg-slate-100 dark:bg-slate-900/80 border-slate-200 dark:border-slate-800 text-slate-600 dark:text-slate-300'
                  }`}
                >
                  {col}
                </div>
              );
            })}
          </div>
        </section>

        {/* Dropzone container / Loader */}
        <section
          {...getRootProps()}
          className={`rounded-2xl border-2 border-dashed p-10 text-center flex flex-col items-center justify-center min-h-[240px] transition-all duration-300 ${
            uploading
              ? 'border-indigo-500/40 bg-indigo-500/5 cursor-wait'
              : isDragActive
              ? 'border-indigo-500 bg-indigo-500/5 shadow-inner cursor-pointer'
              : 'border-slate-350 dark:border-slate-800 hover:border-slate-400 dark:hover:border-slate-700 bg-white dark:bg-slate-900/20 hover:bg-slate-100/50 dark:hover:bg-slate-900/40 cursor-pointer shadow-sm'
          }`}
        >
          <input {...getInputProps()} />
          
          {uploading ? (
            <div className="flex flex-col items-center gap-4">
              <div className="w-12 h-12 rounded-full border-4 border-indigo-500/20 border-t-indigo-500 animate-spin"></div>
              <div className="space-y-1">
                <p className="text-sm font-bold">{statusMessage}</p>
                <p className="text-xs text-slate-500 dark:text-slate-400">Please do not refresh the page during analysis compiling.</p>
              </div>
            </div>
          ) : (
            <>
              <div className="w-12 h-12 rounded-full bg-slate-100 dark:bg-slate-800 flex items-center justify-center mb-4 border border-slate-200 dark:border-slate-700 text-slate-500 dark:text-slate-400">
                <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                </svg>
              </div>
              
              {file ? (
                <div className="flex flex-col items-center">
                  <p className="text-sm font-bold truncate max-w-xs">{file.name}</p>
                  <p className="text-slate-500 dark:text-slate-400 text-xs mt-1">{(file.size / 1024).toFixed(1)} KB &bull; Click or drag to change file</p>
                </div>
              ) : (
                <div className="max-w-sm">
                  <p className="text-sm font-bold">Drag and drop your transaction CSV here</p>
                  <p className="text-slate-500 dark:text-slate-400 text-xs mt-1">or click to browse local files (max 10MB)</p>
                </div>
              )}
            </>
          )}
        </section>

        {/* Error notification & Retry */}
        {currentStep === 'error' && errorMsg && (
          <div className="mt-6 p-5 rounded-2xl bg-rose-500/10 border border-rose-500/20 text-rose-600 dark:text-rose-400 text-xs leading-relaxed flex flex-col sm:flex-row sm:items-start justify-between gap-4 shadow-sm">
            <div className="flex items-start gap-2.5">
              <svg className="w-4 h-4 shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
              <div>
                <p className="font-bold mb-1">Execution Pipeline Failed</p>
                <p>{errorMsg}</p>
                {missingColumns.length > 0 && (
                  <p className="mt-1 font-semibold">Please check the highlighted column headers above.</p>
                )}
              </div>
            </div>
            
            {lastSessionId && missingColumns.length === 0 && (
              <button
                onClick={handleRetryPipeline}
                className="shrink-0 inline-flex items-center justify-center px-4.5 py-2 rounded-xl bg-rose-500/25 hover:bg-rose-500/35 text-rose-700 dark:text-rose-400 font-bold border border-rose-500/30 cursor-pointer transition-colors duration-200"
              >
                Retry Pipeline
              </button>
            )}
          </div>
        )}
      </main>
    </div>
  );
};

export default Upload;
