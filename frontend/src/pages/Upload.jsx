import { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useDropzone } from 'react-dropzone';
import { useAnalysis } from '../context/AnalysisContext';
import { REQUIRED_COLUMNS } from '../constants';
import { apiService } from '../services/api';
import { analysisSessionStorage } from '../services/storageService';
import { useToast } from '../context/ToastContext';
import ErrorBoundary from '../components/ErrorBoundary';
import SemanticConfirmTable from '../components/SemanticConfirmTable';
import KPIReviewTable from '../components/KPIReviewTable';
import EvaluationDashboard from '../components/EvaluationDashboard';
import ChartRenderer from '../components/charts/ChartRenderer';

const Upload = () => {
  const { logout, user, sessionId, setSessionId, setAnalysisResults } = useAnalysis();
  const navigate = useNavigate();
  const { addToast } = useToast();
  
  // Tabs: 'profiler' (Interactive Schema Profiler) or 'dashboard' (Fixed Q-Commerce analysis)
  const [activeTab, setActiveTab] = useState('profiler');
  
  // Pipeline processing states
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [currentStep, setCurrentStep] = useState(''); // 'uploading', 'cleaning', 'engineering', 'kpis', 'insights', 'profiling', 'confirm_semantics', 'processing_derived', 'review_kpis', 'profile_complete', 'error'
  const [statusMessage, setStatusMessage] = useState('');
  
  const [errorMsg, setErrorMsg] = useState('');
  const [missingColumns, setMissingColumns] = useState([]);
  
  // Interactive Profiler specific state
  const [profileData, setProfileData] = useState(null);
  const [mappingData, setMappingData] = useState(null);
  const [domainData, setDomainData] = useState(null);
  const [pipelineContext, setPipelineContext] = useState(null);
  const [candidateKPIs, setCandidateKPIs] = useState(null);
  const [rankedKPIs, setRankedKPIs] = useState(null);
  const [finalKPIs, setFinalKPIs] = useState([]);
  const [dashboardPlan, setDashboardPlan] = useState(null);
  const [showFullProfileJSON, setShowFullProfileJSON] = useState(false);
  const [showDevDashboard, setShowDevDashboard] = useState(false);
  
  // For retries of fixed workflow
  const [lastSessionId, setLastSessionId] = useState(null);

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

  // Run the full fixed pipeline sequentially
  const runProcessingPipeline = async (sessId) => {
    try {
      // Step 2: Clean Dataset
      setCurrentStep('cleaning');
      setStatusMessage('Step 1/4: Cleaning operations log (imputing fields, removing duplicates)...');
      const cleanReport = await apiService.cleanDataset(sessId);

      // Step 3: Feature Engineering
      setCurrentStep('engineering');
      setStatusMessage('Step 2/4: Applying derived metrics (margins, delay checks, utilization)...');
      const engineeringReport = await apiService.engineerFeatures(sessId);

      // Step 4: Calculate KPIs
      setCurrentStep('kpis');
      setStatusMessage('Step 3/4: Calculating operational and hyperlocal KPIs...');
      const kpis = await apiService.getKPIs(sessId);

      // Step 5: Get AI Insights
      setCurrentStep('insights');
      setStatusMessage('Step 4/4: Consulting Gemini AI for diagnostics and recommendations...');
      const insights = await apiService.getInsights(sessId);

      // Set results and navigate
      setAnalysisResults({
        cleaning_report: cleanReport,
        engineering: engineeringReport,
        kpis: kpis,
        insights: insights
      });
      
      addToast("Hyperlocal commerce pipeline calculations completed successfully!", "success");
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
    setErrorMsg('');
    setMissingColumns([]);

    if (activeTab === 'profiler') {
      setCurrentStep('profiling');
      setStatusMessage('Profiling dataset schema and inferring semantic meanings via Gemini...');
      try {
        const res = await apiService.profileAndMapSemantics(selectedFile);
        setSessionId(res.session_id); // SAVE session id
        setProfileData(res.profile);
        setMappingData(res.mapping);
        setCurrentStep('confirm_semantics');
        setUploading(false);
      } catch (err) {
        console.error("Profiling error:", err);
        setErrorMsg(err.message || "An error occurred while profiling the dataset.");
        setCurrentStep('error');
        setUploading(false);
      }
    } else {
      setCurrentStep('uploading');
      setStatusMessage('Uploading CSV and validating headers schema...');
      try {
        // Step 1: Upload CSV
        const uploadData = await apiService.uploadCSV(selectedFile);
        setSessionId(uploadData.session_id);
        setLastSessionId(uploadData.session_id);
        
        // Auto-run the rest of the fixed pipeline
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
    }
  }, [activeTab, setSessionId]);

  const handleOverrideSemantics = async (columnName, originalRole, correctedRole) => {
    if (!mappingData) return;
    try {
      await apiService.submitSemanticCorrection(
        mappingData.schema_fingerprint,
        columnName,
        originalRole,
        correctedRole
      );
    } catch (err) {
      console.error("Failed to log correction override:", err);
    }
  };

  const handleConfirmSemantics = async (finalColumns) => {
    if (!sessionId || !mappingData || !profileData) return;
    
    setUploading(true);
    setCurrentStep('processing_derived');
    setStatusMessage('Post-processing: Engineering features, classifying domain, and compiling candidate KPIs...');
    setErrorMsg('');

    try {
      const confirmedMapping = {
        schema_fingerprint: mappingData.schema_fingerprint,
        columns: finalColumns
      };

      // 1. Classify domain
      const domainProfile = await apiService.classifyDomain(confirmedMapping, profileData);
      setDomainData(domainProfile);

      // 2. Generate candidates and pipeline context
      const genResponse = await apiService.generateKPICandidates(
        sessionId,
        confirmedMapping,
        domainProfile,
        profileData
      );
      setPipelineContext(genResponse.pipeline_context);
      setCandidateKPIs(genResponse.candidates);

      // 3. Rank candidates
      const rankResponse = await apiService.rankKPICandidates(
        genResponse.pipeline_context,
        genResponse.candidates
      );
      setRankedKPIs(rankResponse.selected_kpis);

      setCurrentStep('review_kpis');
      setUploading(false);
    } catch (err) {
      console.error("Error during post-processing features:", err);
      setErrorMsg(err.message || "An error occurred while compiling domain classifications and engineering features.");
      setCurrentStep('error');
      setUploading(false);
    }
  };

  const handleConfirmKPIs = async (selectedKPIs) => {
    setUploading(true);
    setCurrentStep('processing_derived');
    setStatusMessage('Generating narrative business insights...');
    try {
      const basicContext = {
        ...pipelineContext,
        selected_kpis: {
          selected_kpis: selectedKPIs
        }
      };
      
      // 1. Generate narrative insights from confirmed KPIs
      const insightsRes = await apiService.getReportInsights(basicContext);
      const insights = insightsRes?.insights || {};
      
      setStatusMessage('Compiling dynamic dashboard layout specifications...');
      
      const updatedContext = {
        ...basicContext,
        insights: insights
      };

      // 2. Fetch dashboard plan (which automatically saves context + insights to backend analysis_store)
      const plan = await apiService.getDashboardPlan(updatedContext);
      setDashboardPlan(plan);
      setFinalKPIs(selectedKPIs);
      
      // Save completed analysis params in local cache
      analysisSessionStorage.saveSessionData(sessionId, {
        profileData,
        mappingData,
        domainData,
        pipelineContext: updatedContext,
        finalKPIs: selectedKPIs,
        dashboardPlan: plan,
        insights: insights
      });

      addToast("Business diagnostics analysis completed successfully!", "success");
      setCurrentStep('profile_complete');
      setUploading(false);
    } catch (err) {
      console.error("Dashboard planning failed:", err);
      setErrorMsg(err.message || "Failed to generate dashboard layout plan.");
      setCurrentStep('error');
      setUploading(false);
    }
  };

  const handleResetProfiler = () => {
    setFile(null);
    setProfileData(null);
    setMappingData(null);
    setDomainData(null);
    setPipelineContext(null);
    setCandidateKPIs(null);
    setRankedKPIs(null);
    setFinalKPIs([]);
    setDashboardPlan(null);
    setCurrentStep('');
    setErrorMsg('');
  };

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
        
        {/* Navigation Tabs */}
        {currentStep !== 'confirm_semantics' && currentStep !== 'processing_derived' && currentStep !== 'review_kpis' && currentStep !== 'profile_complete' && (
          <div className="flex justify-center mb-10">
            <div className="inline-flex rounded-2xl bg-slate-200/60 dark:bg-slate-900/40 p-1.5 border border-slate-200 dark:border-slate-800/80 backdrop-blur-sm">
              <button
                onClick={() => { setActiveTab('profiler'); setErrorMsg(''); }}
                className={`px-6 py-2.5 rounded-xl text-xs font-bold transition-all duration-200 cursor-pointer ${
                  activeTab === 'profiler'
                    ? 'bg-gradient-to-tr from-indigo-500 to-violet-600 text-white shadow-md'
                    : 'text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-200'
                }`}
              >
                Interactive Schema Profiler
              </button>
              <button
                onClick={() => { setActiveTab('dashboard'); setErrorMsg(''); }}
                className={`px-6 py-2.5 rounded-xl text-xs font-bold transition-all duration-200 cursor-pointer ${
                  activeTab === 'dashboard'
                    ? 'bg-gradient-to-tr from-indigo-500 to-violet-600 text-white shadow-md'
                    : 'text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-200'
                }`}
              >
                Fixed Q-Commerce Analysis
              </button>
            </div>
          </div>
        )}

        {/* Loader states */}
        {uploading && (currentStep === 'profiling' || currentStep === 'processing_derived') && (
          <section className="rounded-3xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-[#111217]/50 p-12 text-center shadow-lg max-w-lg mx-auto flex flex-col items-center gap-6">
            <div className="w-16 h-16 rounded-full border-4 border-indigo-500/20 border-t-indigo-500 animate-spin"></div>
            <div className="space-y-2">
              <h4 className="text-sm font-bold">{statusMessage}</h4>
              <p className="text-xs text-slate-500 dark:text-slate-400">Consulting AI services and running local deterministic algorithms...</p>
            </div>
          </section>
        )}

        {/* Dynamic workflow presentation */}
        {currentStep === 'confirm_semantics' && mappingData && (
          <div className="space-y-6">
            <button
              onClick={handleResetProfiler}
              className="inline-flex items-center gap-1.5 text-xs font-bold text-slate-500 hover:text-indigo-500 transition-colors cursor-pointer"
            >
              &larr; Back to Upload
            </button>
            <ErrorBoundary message="Failed to render semantic mappings confirmation list. Please reset and retry.">
              <SemanticConfirmTable
                mapping={mappingData}
                onConfirm={handleConfirmSemantics}
                onOverride={handleOverrideSemantics}
              />
            </ErrorBoundary>
          </div>
        )}

        {currentStep === 'review_kpis' && rankedKPIs && (
          <div className="space-y-6">
            <button
              onClick={handleResetProfiler}
              className="inline-flex items-center gap-1.5 text-xs font-bold text-slate-500 hover:text-indigo-500 transition-colors cursor-pointer"
            >
              &larr; Back to Upload
            </button>
            <ErrorBoundary message="Failed to render KPI candidate review checklist. Please reset and retry.">
              <KPIReviewTable
                kpis={rankedKPIs}
                fingerprint={mappingData.schema_fingerprint}
                onConfirm={handleConfirmKPIs}
              />
            </ErrorBoundary>
          </div>
        )}
        
        {currentStep === 'profile_complete' && profileData ? (
          <div className="space-y-8 animate-fade-in">
            <div className="rounded-3xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-[#111217]/50 p-8 text-center shadow-2xl relative overflow-hidden">
              <div className="absolute top-0 right-0 w-32 h-32 bg-emerald-500/10 rounded-full blur-3xl pointer-events-none"></div>
              
              <div className="w-16 h-16 rounded-2xl bg-emerald-500/10 border border-emerald-500/25 flex items-center justify-center mx-auto mb-6 text-emerald-500">
                <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              
              <h3 className="text-2xl font-black tracking-tight text-slate-800 dark:text-slate-100">
                Profiling & Mapping Completed
              </h3>
              <p className="text-sm text-slate-500 dark:text-slate-400 mt-2 max-w-md mx-auto">
                Your dataset schema has been parsed, semantic column roles verified, and business domain classified successfully.
              </p>

              {/* Classification Results */}
              {domainData && (
                <div className="my-8 max-w-lg mx-auto p-5 rounded-2xl border border-indigo-500/20 bg-indigo-500/[0.03] text-left">
                  <div className="flex justify-between items-center mb-2">
                    <span className="text-[10px] uppercase font-bold tracking-wider text-slate-400">Classified Business Domain</span>
                    <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold bg-indigo-500/15 text-indigo-500 dark:text-indigo-400 border border-indigo-500/20">
                      {Math.round(domainData.confidence * 100)}% Confidence
                    </span>
                  </div>
                  <h4 className="text-xl font-bold text-slate-800 dark:text-slate-200">
                    {domainData.domain}
                  </h4>
                  <p className="text-xs text-slate-500 dark:text-slate-400 mt-1 italic">
                    "{domainData.reasoning}"
                  </p>
                </div>
              )}

              {/* Metrics Grid */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mt-8">
                <div className="p-4 rounded-2xl border border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-900/30">
                  <span className="block text-[10px] uppercase font-bold text-slate-400">Rows</span>
                  <span className="text-lg font-black text-slate-800 dark:text-slate-200 mt-1 block">
                    {profileData.dataset_metadata.row_count}
                  </span>
                </div>
                <div className="p-4 rounded-2xl border border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-900/30">
                  <span className="block text-[10px] uppercase font-bold text-slate-400">Original Columns</span>
                  <span className="text-lg font-black text-slate-800 dark:text-slate-200 mt-1 block">
                    {profileData.dataset_metadata.column_count}
                  </span>
                </div>
                <div className="p-4 rounded-2xl border border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-900/30">
                  <span className="block text-[10px] uppercase font-bold text-slate-400">Active KPIs</span>
                  <span className="text-lg font-black text-slate-800 dark:text-slate-200 mt-1 block text-indigo-500">
                    {finalKPIs.length}
                  </span>
                </div>
                <div className="p-4 rounded-2xl border border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-900/30">
                  <span className="block text-[10px] uppercase font-bold text-slate-400">Engineered Features</span>
                  <span className="text-lg font-black text-slate-800 dark:text-slate-200 mt-1 block text-emerald-500">
                    +{pipelineContext?.engineered_features?.length || 0}
                  </span>
                </div>
              </div>

              {/* Cache Fingerprint */}
              {mappingData && (
                <div className="mt-6 flex items-center justify-center gap-2">
                  <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Schema Fingerprint:</span>
                  <span className="font-mono text-[10px] px-2 py-0.5 rounded bg-slate-100 dark:bg-slate-900 text-slate-600 dark:text-indigo-400 border border-slate-200 dark:border-slate-800">
                    {mappingData.schema_fingerprint.substring(0, 16)}...
                  </span>
                </div>
              )}
              
              <div className="mt-8 flex flex-wrap justify-center gap-4">
                <button
                  onClick={() => setShowFullProfileJSON(!showFullProfileJSON)}
                  className="px-6 py-2.5 rounded-2xl border border-slate-200 dark:border-slate-800 bg-white hover:bg-slate-50 dark:bg-slate-900/50 dark:hover:bg-slate-800 text-xs font-bold transition-all duration-200 cursor-pointer"
                >
                  {showFullProfileJSON ? 'Hide Profile JSON' : 'View Profile JSON'}
                </button>
                
                <button
                  onClick={() => navigate(`/reports/${sessionId}`)}
                  className="px-6 py-2.5 rounded-2xl border border-indigo-500/20 bg-indigo-500/10 hover:bg-indigo-500/15 text-indigo-500 text-xs font-bold transition-all duration-200 cursor-pointer"
                >
                  View Report Center &rarr;
                </button>
                
                <button
                  onClick={handleResetProfiler}
                  className="px-6 py-2.5 rounded-2xl bg-gradient-to-tr from-indigo-500 to-violet-600 hover:from-indigo-600 hover:to-violet-700 text-white text-xs font-bold transition-all duration-200 cursor-pointer shadow-lg shadow-indigo-500/25"
                >
                  Analyze New File
                </button>
              </div>
            </div>

            {/* Analysis Explorer Section */}
            <div className="mt-10 pt-8 border-t border-slate-205 dark:border-slate-800 text-left">
              <h3 className="text-sm font-bold tracking-wider uppercase text-slate-400 mb-6">
                Analysis Explorer
              </h3>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Card 1: Selected KPIs */}
                <div 
                  onClick={() => navigate(`/analysis/kpis/${sessionId}`)}
                  className="group relative p-6 rounded-3xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-[#111217]/30 hover:border-indigo-500/30 hover:bg-slate-50 dark:hover:bg-slate-900/10 transition-all duration-200 cursor-pointer shadow-sm hover:shadow-xl hover:shadow-indigo-500/[0.02] flex flex-col justify-between min-h-[170px]"
                >
                  <div className="space-y-4">
                    <div className="w-10 h-10 rounded-2xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-500 group-hover:scale-105 transition-transform duration-200">
                      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                      </svg>
                    </div>
                    <div>
                      <h4 className="text-base font-bold text-slate-800 dark:text-slate-100 group-hover:text-indigo-500 transition-colors duration-200">
                        Selected Key Performance Indicators
                      </h4>
                      <p className="text-xs text-slate-500 dark:text-slate-400 mt-2 leading-relaxed">
                        View every KPI discovered during analysis, organized into business categories.
                      </p>
                    </div>
                  </div>
                  <div className="mt-4 flex items-center gap-1.5 text-xs font-bold text-indigo-500 group-hover:gap-2.5 transition-all duration-200">
                    <span>Explore KPIs</span>
                    <span>&rarr;</span>
                  </div>
                </div>

                {/* Card 2: Explore Visualizations */}
                <div 
                  onClick={() => navigate(`/analysis/visualizations/${sessionId}`)}
                  className="group relative p-6 rounded-3xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-[#111217]/30 hover:border-emerald-500/30 hover:bg-slate-50 dark:hover:bg-slate-900/10 transition-all duration-200 cursor-pointer shadow-sm hover:shadow-xl hover:shadow-emerald-500/[0.02] flex flex-col justify-between min-h-[170px]"
                >
                  <div className="space-y-4">
                    <div className="w-10 h-10 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-500 group-hover:scale-105 transition-transform duration-200">
                      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 8v8m-4-5v5m-4-2v2m-2 4h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                      </svg>
                    </div>
                    <div>
                      <h4 className="text-base font-bold text-slate-800 dark:text-slate-100 group-hover:text-emerald-500 transition-colors duration-200">
                        Explore Visualizations
                      </h4>
                      <p className="text-xs text-slate-500 dark:text-slate-400 mt-2 leading-relaxed">
                        Browse all recommended charts, filters, dashboard sections, and business visualizations.
                      </p>
                    </div>
                  </div>
                  <div className="mt-4 flex items-center gap-1.5 text-xs font-bold text-emerald-500 group-hover:gap-2.5 transition-all duration-200">
                    <span>Explore Visualizations</span>
                    <span>&rarr;</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Profile JSON view */}
            {showFullProfileJSON && (
              <div className="rounded-3xl border border-slate-200 dark:border-slate-800 bg-slate-950 p-6 shadow-xl text-left max-h-[400px] overflow-y-auto">
                <div className="flex justify-between items-center mb-3">
                  <span className="text-[10px] uppercase font-bold text-slate-500 tracking-wider">JSON dataset_profile Output</span>
                  <button
                    onClick={() => {
                      navigator.clipboard.writeText(JSON.stringify(profileData, null, 2));
                    }}
                    className="text-[10px] font-bold text-indigo-400 hover:text-indigo-300 cursor-pointer"
                  >
                    Copy to Clipboard
                  </button>
                </div>
                <pre className="font-mono text-xs text-emerald-400 whitespace-pre-wrap">
                  {JSON.stringify(profileData, null, 2)}
                </pre>
              </div>
            )}
          </div>
        ) : (
          <>
            <section className="mb-8 text-center sm:text-left">
              <h2 className="text-2xl sm:text-3xl font-black tracking-tight">Upload Dataset</h2>
              <p className="text-slate-500 dark:text-slate-400 text-sm mt-1">
                {activeTab === 'profiler'
                  ? 'Upload any structured CSV dataset to compute its schema profile and column semantics.'
                  : 'Upload your operational dataset log matching the fixed 20-columns schema to run operations analysis.'
                }
              </p>
            </section>

            {/* Tab-dependent checklist headers (only show for Fixed workflow) */}
            {activeTab === 'dashboard' && (
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
            )}

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
                      <p className="text-sm font-bold">Drag and drop your dataset CSV here</p>
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
                    {activeTab === 'dashboard' && missingColumns.length > 0 && (
                      <p className="mt-1 font-semibold">Please check the highlighted column headers above.</p>
                    )}
                  </div>
                </div>
                
                {activeTab === 'dashboard' && lastSessionId && missingColumns.length === 0 && (
                  <button
                    onClick={handleRetryPipeline}
                    className="shrink-0 inline-flex items-center justify-center px-4.5 py-2 rounded-xl bg-rose-500/25 hover:bg-rose-500/35 text-rose-700 dark:text-rose-400 font-bold border border-rose-500/30 cursor-pointer transition-colors duration-200"
                  >
                    Retry Pipeline
                  </button>
                )}
              </div>
            )}
          </>
        )}
        <div className="mt-12 text-center border-t border-slate-200 dark:border-slate-800 pt-6">
          <button
            onClick={() => setShowDevDashboard(true)}
            className="text-[10px] font-bold uppercase tracking-wider text-slate-400 hover:text-indigo-500 transition-colors cursor-pointer"
          >
            Developer Workspace & Calibration Metrics
          </button>
        </div>
        
        {showDevDashboard && <EvaluationDashboard onClose={() => setShowDevDashboard(false)} />}
      </main>
    </div>
  );
};

export default Upload;
