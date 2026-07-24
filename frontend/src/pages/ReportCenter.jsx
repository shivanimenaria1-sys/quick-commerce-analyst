import React, { useState, useEffect, useMemo } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { apiService } from '../services/api';
import { analysisSessionStorage } from '../services/storageService';
import { useToast } from '../context/ToastContext';
import ErrorBoundary from '../components/ErrorBoundary';
import EmptyState from '../components/EmptyState';
import { ChartRenderer } from '../components/charts/ChartRenderer';

// Shimmer Loader for Report Center statistics card list
const StatCardSkeleton = () => (
  <div className="p-4 rounded-xl border border-slate-205 dark:border-slate-850 bg-white dark:bg-[#111217]/25 text-left flex flex-col justify-between min-h-[70px]">
    <div className="h-2.5 w-16 bg-slate-200 dark:bg-slate-800/80 rounded shimmer"></div>
    <div className="h-5 w-12 bg-slate-200 dark:bg-slate-800 rounded shimmer mt-2"></div>
  </div>
);

// Document Preview shimmer skeleton
const PreviewSkeleton = () => (
  <div className="flex-1 flex flex-col justify-between p-6 space-y-4">
    <div className="space-y-3">
      <div className="h-7 w-2/3 bg-slate-200 dark:bg-slate-800 rounded shimmer"></div>
      <div className="h-3 w-1/3 bg-slate-200 dark:bg-slate-800/80 rounded shimmer"></div>
      <div className="h-px w-full bg-slate-250 dark:bg-slate-800 my-4"></div>
      <div className="h-4 w-full bg-slate-200 dark:bg-slate-800/60 rounded shimmer"></div>
      <div className="h-4 w-full bg-slate-200 dark:bg-slate-800/60 rounded shimmer"></div>
      <div className="h-4 w-3/4 bg-slate-200 dark:bg-slate-800/60 rounded shimmer"></div>
    </div>
    <div className="flex gap-4">
      <div className="h-24 flex-1 bg-slate-200 dark:bg-slate-800/40 rounded-xl shimmer"></div>
      <div className="h-24 flex-1 bg-slate-200 dark:bg-slate-800/40 rounded-xl shimmer"></div>
    </div>
  </div>
);

export const ReportCenter = () => {
  const { sessionId } = useParams();
  const navigate = useNavigate();
  const { addToast } = useToast();
  
  const [loading, setLoading] = useState(true);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [error, setError] = useState(null);
  
  // Stored analysis session state
  const [sessionInfo, setSessionInfo] = useState(null);
  const [htmlPreviewUrl, setHtmlPreviewUrl] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  
  // Progress modal and hidden rendering capture state
  const [exportProgress, setExportProgress] = useState(null);
  const [showProgressModal, setShowProgressModal] = useState(false);
  const [renderChartsForCapture, setRenderChartsForCapture] = useState(false);
  
  // Available report types list (dynamic catalog)
  const reportCatalog = [
    {
      id: 'exec_business_analysis',
      name: 'Executive Business Analysis Report',
      description: 'Comprehensive business diagnostics report including data profiles, semantic maps, classified operational domain characteristics, Selected KPIs catalog, and visual chart plans.',
      type: 'PDF / HTML',
      status: 'Ready'
    }
  ];

  useEffect(() => {
    let active = true;

    const fetchAnalysisData = async () => {
      // 1. Serve from cache immediately so the page isn't blank on navigation
      const cached = analysisSessionStorage.getSessionData(sessionId);
      if (cached) {
        setSessionInfo(cached);
        setLoading(false);
      }

      // 2. Fetch fresh from backend GET /api/analysis/{sessionId}
      try {
        const fresh = await apiService.getAnalysis(sessionId);
        if (!active) return;

        // Deep-merge fresh data into the existing cache via the canonical
        // helper. Preserves insights even if the API returns an empty object
        // (the cache value takes precedence in that case).
        const merged = analysisSessionStorage.updateFromAnalysis(sessionId, fresh);

        // DEBUG LOG – remove after verification
        console.debug('[SESSION_DEBUG] ReportCenter after updateFromAnalysis:', {
          sessionId: sessionId?.substring(0, 8),
          insightKeys: Object.keys(merged?.insights || {}),
          kpisCount: merged?.finalKPIs?.length ?? 0,
          chartsCount: merged?.dashboardPlan?.dashboard?.charts?.length ?? 0,
        });

        setSessionInfo(merged);
        setError(null);
      } catch (err) {
        console.error('Backend retrieval failed:', err);
        if (!cached) {
          if (active) {
            setError('Analysis session is no longer available. Please upload your dataset again.');
            setTimeout(() => {
              navigate('/upload', { state: { error: 'Analysis session is no longer available. Please upload your dataset again.' } });
            }, 3500);
          }
        }
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    };

    fetchAnalysisData();

    return () => {
      active = false;
    };
  }, [sessionId, navigate]);

  // Load HTML Preview URL dynamically on load once sessionInfo is resolved
  useEffect(() => {
    if (!sessionInfo) return;
    
    let active = true;
    const loadPreview = async () => {
      setPreviewLoading(true);
      try {
        // Compile context pipeline result payload for exporter
        const pipelineResult = {
          dataset_profile: sessionInfo.profileData,
          confirmed_semantic_mapping: sessionInfo.mappingData,
          domain_profile: sessionInfo.domainData,
          selected_kpis: { selected_kpis: sessionInfo.finalKPIs }
        };
        
        const htmlBlob = await apiService.exportReport(pipelineResult, sessionInfo.insights, 'html');
        if (!active) return;
        
        const previewUrl = URL.createObjectURL(htmlBlob);
        setHtmlPreviewUrl(previewUrl);
      } catch (err) {
        console.error("Failed to generate HTML preview:", err);
      } finally {
        if (active) {
          setPreviewLoading(false);
        }
      }
    };

    loadPreview();

    return () => {
      active = false;
      if (htmlPreviewUrl) {
        URL.revokeObjectURL(htmlPreviewUrl);
      }
    };
  }, [sessionInfo]);

  // Search filter matching
  const filteredReports = useMemo(() => {
    const q = searchQuery.toLowerCase().trim();
    if (!q) return reportCatalog;
    
    return reportCatalog.filter(r => 
      r.name.toLowerCase().includes(q) ||
      sessionInfo?.mappingData?.dataset_name?.toLowerCase().includes(q) ||
      sessionInfo?.domainData?.domain?.toLowerCase().includes(q)
    );
  }, [searchQuery, sessionInfo]);

  // Trigger file download helper
  const triggerDownload = (blob, filename) => {
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  // Export handlers
  const handleExport = async (format) => {
    if (!sessionInfo) return;
    addToast(`Compiling report as ${format.toUpperCase()}...`, 'info');
    try {
      const pipelineResult = {
        dataset_profile: sessionInfo.profileData,
        confirmed_semantic_mapping: sessionInfo.mappingData,
        domain_profile: sessionInfo.domainData,
        selected_kpis: { selected_kpis: sessionInfo.finalKPIs }
      };

      const filename = `operations_report_${sessionId.substring(0, 8)}.${format}`;
      const blob = await apiService.exportReport(pipelineResult, sessionInfo.insights, format);
      triggerDownload(blob, filename);
      addToast(`${format.toUpperCase()} report downloaded successfully!`, 'success');
    } catch (err) {
      addToast(`Export failed: ${err.message}`, 'error');
    }
  };

  const handleExportJSON = () => {
    if (!sessionInfo) return;
    addToast("Exporting JSON analysis details...", "info");
    try {
      const jsonStr = JSON.stringify(sessionInfo, null, 2);
      const blob = new Blob([jsonStr], { type: 'application/json' });
      triggerDownload(blob, `analysis_summary_${sessionId.substring(0, 8)}.json`);
      addToast("JSON summary downloaded successfully!", "success");
    } catch (err) {
      addToast(`JSON export failed: ${err.message}`, "error");
    }
  };

  const handleExportCompletePDF = async () => {
    if (!sessionInfo) return;
    
    setShowProgressModal(true);
    setExportProgress({
      collectKPIs: 'loading',
      collectCharts: 'waiting',
      embedVisualizations: 'waiting',
      buildPDF: 'waiting',
      downloading: 'waiting'
    });

    try {
      // Step 1: Collecting KPIs
      await new Promise(r => setTimeout(r, 600));
      setExportProgress(prev => ({ ...prev, collectKPIs: 'done', collectCharts: 'loading' }));

      // Step 2: Render charts in hidden container to capture SVG
      setRenderChartsForCapture(true);
      // Wait for Recharts to render completely
      await new Promise(r => setTimeout(r, 1800));

      const container = document.getElementById('capture-charts-container');
      const items = container ? container.querySelectorAll('.capture-chart-item') : [];
      const chartImages = {};

      for (const item of Array.from(items)) {
        const chartId = item.getAttribute('data-chart-id');
        const svgEl = item.querySelector('svg');
        if (svgEl && chartId) {
          try {
            const svgString = new XMLSerializer().serializeToString(svgEl);
            const svgBlob = new Blob([svgString], { type: 'image/svg+xml;charset=utf-8' });
            const url = URL.createObjectURL(svgBlob);
            
            await new Promise((resolve) => {
              const img = new Image();
              img.onload = () => {
                const canvas = document.createElement('canvas');
                // Use standard double-resolution landscape aspect ratio for ReportLab PDF page width
                canvas.width = 600;
                canvas.height = 360;
                const ctx = canvas.getContext('2d');
                ctx.fillStyle = '#ffffff';
                ctx.fillRect(0, 0, canvas.width, canvas.height);
                ctx.drawImage(img, 0, 0, 600, 360);
                const pngData = canvas.toDataURL('image/png');
                chartImages[chartId] = pngData;
                URL.revokeObjectURL(url);
                resolve();
              };
              img.onerror = () => {
                URL.revokeObjectURL(url);
                resolve();
              };
              img.src = url;
            });
          } catch (err) {
            console.error(`Failed to capture chart ${chartId}:`, err);
          }
        }
      }

      setRenderChartsForCapture(false); // Clean up hidden rendering
      setExportProgress(prev => ({ ...prev, collectCharts: 'done', embedVisualizations: 'loading' }));
      await new Promise(r => setTimeout(r, 600));

      // Step 3: Embedding Visualizations
      setExportProgress(prev => ({ ...prev, embedVisualizations: 'done', buildPDF: 'loading' }));
      
      // DEBUG LOG – remove after verification
      console.debug('[SESSION_DEBUG] ReportCenter: before exportCompleteReport:', {
        sessionId: sessionId?.substring(0, 8),
        insightKeys: Object.keys(sessionInfo?.insights || {}),
        kpisCount: sessionInfo?.finalKPIs?.length ?? 0,
        chartsCount: sessionInfo?.dashboardPlan?.dashboard?.charts?.length ?? 0,
        capturedChartImages: Object.keys(chartImages).length,
      });

      // Step 4: Build PDF on the backend
      const response = await apiService.exportCompleteReport(sessionId, chartImages);
      setExportProgress(prev => ({ ...prev, buildPDF: 'done', downloading: 'loading' }));
      await new Promise(r => setTimeout(r, 600));

      // Step 5: Downloading...
      const filename = `executive_complete_report_${sessionId.substring(0, 8)}.pdf`;
      triggerDownload(response, filename);
      
      setExportProgress(prev => ({ ...prev, downloading: 'done' }));
      addToast('Complete analysis PDF report downloaded successfully!', 'success');
      
      // Close modal after successful download
      setTimeout(() => {
        setShowProgressModal(false);
        setExportProgress(null);
      }, 1000);
      
    } catch (err) {
      console.error(err);
      addToast(`Complete PDF export failed: ${err.message || err}`, 'error');
      setShowProgressModal(false);
      setExportProgress(null);
      setRenderChartsForCapture(false);
    }
  };

  if (error && !sessionInfo) {
    return (
      <div className="min-h-screen bg-slate-50 dark:bg-[#0d0e12] flex items-center justify-center text-slate-800 dark:text-slate-100 font-sans p-4">
        <EmptyState 
          title="Analysis Session Expired"
          description={error}
          actionText="Back to Upload"
          onAction={() => navigate('/upload')}
          iconType="session"
        />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-[#0d0e12] text-slate-800 dark:text-slate-100 font-sans relative pb-16 transition-colors duration-200">
      <div className="absolute top-0 right-1/4 w-96 h-96 bg-indigo-500/5 rounded-full blur-[100px] pointer-events-none"></div>

      <header className="sticky top-0 z-40 w-full border-b border-slate-200 dark:border-slate-800 bg-white/80 dark:bg-[#0d0e12]/80 backdrop-blur-md">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <button 
              onClick={() => navigate('/upload')}
              className="p-1.5 rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/50 dark:hover:bg-slate-800 text-xs font-bold cursor-pointer transition-colors text-slate-600 dark:text-slate-300"
            >
              &larr; Summary
            </button>
            
            {/* Breadcrumbs */}
            <div className="hidden sm:flex items-center gap-1.5 text-xs text-slate-450 dark:text-slate-500">
              <span className="cursor-pointer hover:text-indigo-500 transition-colors" onClick={() => navigate('/upload')}>Analysis Workspace</span>
              <span>&gt;</span>
              <span className="text-slate-700 dark:text-slate-305 font-bold">Report Center</span>
            </div>
          </div>
          {sessionInfo?.domainData && (
            <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-indigo-500/10 text-indigo-500 border border-indigo-500/20 max-w-[140px] truncate sm:max-w-none">
              {sessionInfo.domainData.domain}
            </span>
          )}
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-10 relative z-10 space-y-8">
        
        {/* Breadcrumb Navigation */}
        <div className="flex items-center gap-1.5 text-xs text-slate-455 dark:text-slate-500 select-none text-left">
          <span className="cursor-pointer hover:text-indigo-500 transition-colors" onClick={() => navigate('/upload')}>Analysis Workspace</span>
          <span>&gt;</span>
          <span className="text-slate-700 dark:text-slate-350 font-bold">Report Center</span>
        </div>

        {/* Title and details block */}
        <div className="text-left space-y-2">
          <h1 className="text-2xl sm:text-3xl font-black tracking-tight text-slate-900 dark:text-slate-100">
            Report Center
          </h1>
          <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-slate-550 dark:text-slate-400">
            <span>Dataset: <strong className="font-semibold text-slate-700 dark:text-slate-300">{sessionInfo?.mappingData?.dataset_name || 'Quick Commerce Log'}</strong></span>
            <span>•</span>
            <span>Fingerprint: <strong className="font-mono text-indigo-550 dark:text-indigo-400">{sessionInfo?.mappingData?.schema_fingerprint?.substring(0, 12)}</strong></span>
          </div>
        </div>

        {/* Diagnostic Metrics summary grid */}
        <div className="grid grid-cols-2 sm:grid-cols-5 gap-4 text-left">
          {loading ? (
            [1, 2, 3, 4, 5].map(idx => <StatCardSkeleton key={idx} />)
          ) : (
            <>
              <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-855 bg-white dark:bg-[#111217]/25">
                <span className="block text-[8px] uppercase font-bold text-slate-400">Total KPIs</span>
                <span className="block mt-1.5 font-mono text-lg font-black text-slate-800 dark:text-slate-150">
                  {sessionInfo?.finalKPIs?.length || 0}
                </span>
              </div>
              <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-855 bg-white dark:bg-[#111217]/25">
                <span className="block text-[8px] uppercase font-bold text-slate-400">Visualizations</span>
                <span className="block mt-1.5 font-mono text-lg font-black text-slate-800 dark:text-slate-150">
                  {sessionInfo?.dashboardPlan?.dashboard?.charts?.length || 0}
                </span>
              </div>
              <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-855 bg-white dark:bg-[#111217]/25">
                <span className="block text-[8px] uppercase font-bold text-slate-400">Domain Classification</span>
                <span className="block mt-1.5 text-xs font-bold text-indigo-500 truncate" title={sessionInfo?.domainData?.domain}>
                  {sessionInfo?.domainData?.domain || 'Retail'}
                </span>
              </div>
              <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-855 bg-white dark:bg-[#111217]/25">
                <span className="block text-[8px] uppercase font-bold text-slate-400">Dataset Rows</span>
                <span className="block mt-1.5 font-mono text-lg font-black text-slate-800 dark:text-slate-150 text-ellipsis overflow-hidden">
                  {sessionInfo?.profileData?.dataset_metadata?.row_count?.toLocaleString() || 'N/A'}
                </span>
              </div>
              <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-855 bg-white dark:bg-[#111217]/25">
                <span className="block text-[8px] uppercase font-bold text-slate-400">Dataset Columns</span>
                <span className="block mt-1.5 font-mono text-lg font-black text-slate-800 dark:text-slate-150">
                  {sessionInfo?.profileData?.dataset_metadata?.column_count || 'N/A'}
                </span>
              </div>
            </>
          )}
        </div>

        {/* Toolbar: search available reports */}
        <div className="flex flex-col sm:flex-row gap-4 justify-between items-center bg-white dark:bg-[#111217]/25 border border-slate-200 dark:border-slate-800 p-4 rounded-3xl backdrop-blur-sm text-left">
          <div className="w-full sm:max-w-md relative">
            <input 
              type="text" 
              placeholder="Search reports by catalog name, dataset name, or domain..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2 text-xs rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-900/60 focus:outline-none focus:border-indigo-500 text-slate-800 dark:text-slate-150 transition-colors"
              aria-label="Search reports catalog"
            />
            <svg className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          </div>
        </div>

        {/* Double-column layout: Left Reports list, Right HTML independent preview */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 text-left items-start">
          
          {/* Left available reports list catalog */}
          <div className="lg:col-span-5 space-y-6">
            <h3 className="text-[11px] font-black uppercase text-slate-450 dark:text-slate-500 tracking-wider">
              Available Reports ({filteredReports.length})
            </h3>
            
            {filteredReports.length > 0 ? (
              filteredReports.map((report) => (
                <div key={report.id} className="p-6 rounded-3xl border border-slate-200 dark:border-slate-855 bg-white dark:bg-[#111217]/20 shadow-sm space-y-4">
                  <div>
                    <span className="px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-500 border border-emerald-500/20 font-mono text-[9px] uppercase font-bold tracking-wider">
                      {report.status}
                    </span>
                    <h4 className="text-base font-bold text-slate-800 dark:text-slate-100 mt-2">
                      {report.name}
                    </h4>
                    <p className="text-xs text-slate-550 dark:text-slate-400 mt-1.5 leading-relaxed">
                      {report.description}
                    </p>
                  </div>
                  
                  {/* Export Options buttons */}
                  <div className="grid grid-cols-2 gap-2 pt-4 border-t border-slate-150 dark:border-slate-850/60 font-sans">
                    <button
                      onClick={handleExportCompletePDF}
                      className="col-span-2 px-3.5 py-2.5 rounded-xl border border-emerald-500/30 bg-emerald-500/10 hover:bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 text-xs font-bold transition-all cursor-pointer flex items-center justify-center gap-2 shadow-sm"
                    >
                      <svg className="w-4 h-4 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                      </svg>
                      Export Complete Analysis Report (PDF)
                    </button>
                    <button
                      onClick={() => handleExport('pdf')}
                      className="px-3 py-2 rounded-xl bg-slate-100 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-[11px] font-bold transition-all hover:bg-slate-200 dark:hover:bg-slate-800 cursor-pointer text-slate-700 dark:text-slate-300"
                    >
                      Download Brief PDF
                    </button>
                    <button
                      onClick={() => handleExport('html')}
                      className="px-3 py-2 rounded-xl bg-slate-100 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-[11px] font-bold transition-all hover:bg-slate-200 dark:hover:bg-slate-800 cursor-pointer text-slate-700 dark:text-slate-300"
                    >
                      Download Brief HTML
                    </button>
                    <button
                      onClick={handleExportJSON}
                      className="col-span-2 px-3 py-2 rounded-xl border border-indigo-500/20 bg-indigo-500/5 text-indigo-550 text-[11px] font-bold transition-all hover:bg-indigo-500/10 cursor-pointer"
                    >
                      Download JSON Summary
                    </button>
                  </div>
                </div>
              ))
            ) : (
              <EmptyState 
                title="No Reports Match Search"
                description="We couldn't find any generated reports matching your search parameters. Try entering another keyword."
                actionText="Reset Search"
                onAction={() => setSearchQuery('')}
                iconType="search"
              />
            )}
          </div>

          {/* Right HTML embedded iframe preview panel */}
          <div className="lg:col-span-7 space-y-6 w-full">
            <h3 className="text-[11px] font-black uppercase text-slate-455 dark:text-slate-500 tracking-wider">
              Interactive HTML Preview
            </h3>
            
            <div className="rounded-3xl border border-slate-205 dark:border-slate-855 bg-white dark:bg-[#111217]/20 shadow-md p-6 h-[550px] flex flex-col justify-between overflow-hidden relative">
              {previewLoading ? (
                <PreviewSkeleton />
              ) : htmlPreviewUrl ? (
                <ErrorBoundary message="Failed to render report layout inside sandbox. You can still download the PDF or HTML using action buttons.">
                  <iframe
                    src={htmlPreviewUrl}
                    title="Analysis Report Preview"
                    className="w-full flex-1 border-0 rounded-2xl bg-white"
                    sandbox="allow-scripts"
                  />
                </ErrorBoundary>
              ) : (
                <div className="flex-1 flex flex-col items-center justify-center text-xs text-slate-450 dark:text-slate-500 space-y-2 select-none">
                  <svg className="w-12 h-12 text-slate-300 dark:text-slate-700 mx-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                  <p className="font-bold">No Preview Available</p>
                  <p className="text-[10px] text-slate-400">Failed to render report HTML bytes.</p>
                </div>
              )}
            </div>
          </div>

        </div>

      </main>

      {/* Dynamic Export Progress Modal */}
      {showProgressModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-sm p-4 font-sans select-none animate-fadeIn">
          <div className="bg-white dark:bg-[#12131a] border border-slate-200 dark:border-slate-800 rounded-3xl p-6 max-w-sm w-full shadow-2xl space-y-6 text-left">
            <div>
              <h3 className="text-base font-bold text-slate-800 dark:text-slate-100 flex items-center gap-2">
                <svg className="w-5 h-5 text-emerald-500 animate-spin" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Preparing Report...
              </h3>
              <p className="text-xs text-slate-500 mt-1">Please wait while the platform compiles the document.</p>
            </div>

            <div className="space-y-3">
              {[
                { key: 'collectKPIs', label: 'Collecting KPIs and Metadata' },
                { key: 'collectCharts', label: 'Rendering and Capturing Visualizations' },
                { key: 'embedVisualizations', label: 'Embedding Vector Charts' },
                { key: 'buildPDF', label: 'Compiling ReportLab PDF layout' },
                { key: 'downloading', label: 'Downloading Document' }
              ].map(step => {
                const status = exportProgress?.[step.key];
                return (
                  <div key={step.key} className="flex items-center gap-3 text-xs">
                    {status === 'done' ? (
                      <span className="w-4 h-4 rounded-full bg-emerald-500/10 border border-emerald-500 text-emerald-500 flex items-center justify-center font-bold text-[10px]">&#10003;</span>
                    ) : status === 'loading' ? (
                      <span className="w-4 h-4 rounded-full bg-indigo-500/10 border border-indigo-500 text-indigo-500 flex items-center justify-center animate-pulse text-[9px]">&#8226;</span>
                    ) : (
                      <span className="w-4 h-4 rounded-full bg-slate-100 dark:bg-slate-900 border border-slate-200 dark:border-slate-800" />
                    )}
                    <span className={`font-semibold ${status === 'done' ? 'text-slate-500 line-through' : status === 'loading' ? 'text-indigo-500 font-bold' : 'text-slate-400'}`}>
                      {step.label}
                    </span>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}

      {/* Hidden container for rendering charts temporarily to capture SVG */}
      {renderChartsForCapture && (
        <div 
          id="capture-charts-container" 
          style={{ position: 'absolute', left: '-9999px', top: '-9999px', width: '800px', opacity: 0 }}
        >
          {sessionInfo?.dashboardPlan?.dashboard?.charts?.map((c) => (
            <div 
              key={c.id || c.chart_id} 
              className="capture-chart-item" 
              data-chart-id={c.id || c.chart_id} 
              style={{ height: '360px', width: '600px', marginBottom: '20px' }}
            >
              <ChartRenderer visualization={{ ...c, id: c.id || c.chart_id }} />
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default ReportCenter;
