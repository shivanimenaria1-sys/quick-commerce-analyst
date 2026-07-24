import React, { useState, useEffect, useMemo } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { apiService } from '../services/api';
import { analysisSessionStorage } from '../services/storageService';
import ChartRenderer from '../components/charts/ChartRenderer';
import ErrorBoundary from '../components/ErrorBoundary';
import EmptyState from '../components/EmptyState';

// Shimmer placeholders for Detail layout
const ChartAreaSkeleton = () => (
  <div className="rounded-3xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-[#111217]/30 p-6 h-[320px] flex flex-col justify-between">
    <div className="h-4 w-40 bg-slate-200 dark:bg-slate-800/80 rounded shimmer"></div>
    <div className="flex-1 flex items-end gap-3 px-6 pt-10 pb-4">
      {[40, 70, 45, 90, 60, 80, 50, 95].map((h, i) => (
        <div key={i} className="flex-1 bg-slate-200 dark:bg-slate-800/40 rounded-t shimmer" style={{ height: `${h}%` }}></div>
      ))}
    </div>
  </div>
);

const InsightsPanelSkeleton = () => (
  <div className="p-6 rounded-3xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-[#111217]/30 space-y-6">
    <div className="flex justify-between items-center pb-4 border-b border-slate-250 dark:border-slate-850">
      <div className="h-6 w-32 bg-slate-200 dark:bg-slate-800/80 rounded shimmer"></div>
      <div className="h-5 w-16 bg-slate-200 dark:bg-slate-800/80 rounded shimmer"></div>
    </div>
    <div className="space-y-3">
      <div className="h-4 w-full bg-slate-200 dark:bg-slate-800/60 rounded shimmer"></div>
      <div className="h-4 w-full bg-slate-200 dark:bg-slate-800/60 rounded shimmer"></div>
      <div className="h-4 w-2/3 bg-slate-200 dark:bg-slate-800/60 rounded shimmer"></div>
    </div>
  </div>
);

export const VisualizationDetail = () => {
  const { sessionId, visualizationId } = useParams();
  const navigate = useNavigate();
  
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [sessionInfo, setSessionInfo] = useState(null);

  useEffect(() => {
    let active = true;

    const fetchAnalysisData = async () => {
      // 1. Serve from cache immediately so the page isn't blank on navigation
      const cached = analysisSessionStorage.getSessionData(sessionId);
      if (cached) {
        setSessionInfo(cached);
        setLoading(false);
      }

      try {
        const fresh = await apiService.getAnalysis(sessionId);
        if (!active) return;

        // 2. Deep-merge fresh data into the existing cache via the canonical
        //    helper, so that insights and other cached fields are preserved.
        const merged = analysisSessionStorage.updateFromAnalysis(sessionId, fresh);

        // DEBUG LOG – remove after verification
        console.debug('[SESSION_DEBUG] VisualizationDetail after updateFromAnalysis:', {
          sessionId: sessionId?.substring(0, 8),
          visualizationId,
          insightKeys: Object.keys(merged?.insights || {}),
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

  const chartObject = useMemo(() => {
    const charts = sessionInfo?.dashboardPlan?.dashboard?.charts || [];
    const matched = charts.find(c => String(c.id || c.chart_id) === String(visualizationId));
    
    // Debug logging for tracing visualization lookup parameters
    console.log("Visualization Lookup Debug Info:", {
      routeVisualizationId: visualizationId,
      totalCharts: charts.length,
      availableIds: charts.map(c => ({ id: c.id, chart_id: c.chart_id })),
      matchedId: matched?.id || matched?.chart_id
    });
    
    return matched;
  }, [sessionInfo, visualizationId]);

  const details = useMemo(() => {
    if (!chartObject || !sessionInfo) return null;

    const profile = sessionInfo.profileData;
    const mapping = sessionInfo.mappingData;
    const finalKPIs = sessionInfo.finalKPIs;

    // Scan values helper
    const scanChartData = (data, xAxis, yAxis) => {
      if (!Array.isArray(data) || data.length === 0 || !xAxis || !yAxis) {
        return { maxVal: 0, maxLabel: 'N/A', minVal: 0, minLabel: 'N/A', avgVal: 0 };
      }
      let maxVal = -Infinity;
      let maxLabel = 'N/A';
      let minVal = Infinity;
      let minLabel = 'N/A';
      let sum = 0;
      let count = 0;

      data.forEach(item => {
        const val = Number(item[yAxis]);
        if (!isNaN(val)) {
          sum += val;
          count++;
          if (val > maxVal) {
            maxVal = val;
            maxLabel = String(item[xAxis] || 'N/A');
          }
          if (val < minVal) {
            minVal = val;
            minLabel = String(item[xAxis] || 'N/A');
          }
        }
      });

      return {
        maxVal: maxVal === -Infinity ? 0 : maxVal,
        maxLabel,
        minVal: minVal === Infinity ? 0 : minVal,
        minLabel,
        avgVal: count > 0 ? sum / count : 0
      };
    };

    const scanned = scanChartData(chartObject.chart_data, chartObject.x_axis, chartObject.y_axis);

    const getBusinessCategory = (kpi) => {
      if (!kpi) return 'General';
      const plugin = kpi.generator_plugin || '';
      const id = kpi.id || '';
      if (plugin.includes('revenue') || plugin.includes('cost') || id.includes('revenue') || id.includes('cost') || id.includes('profit') || id.includes('margin')) {
        return 'Financial Operations';
      }
      if (plugin.includes('loyalty') || plugin.includes('customer') || id.includes('customer') || id.includes('loyalty') || id.includes('repeat')) {
        return 'Customer Analytics';
      }
      if (plugin.includes('duration') || id.includes('delivery') || id.includes('time') || id.includes('delay') || id.includes('rider')) {
        return 'Delivery Logistics';
      }
      if (plugin.includes('location') || id.includes('pincode') || id.includes('store') || id.includes('region')) {
        return 'Geographical Coverage';
      }
      return 'Operational Management';
    };

    const resolveSourceColumn = (columnOrRole) => {
      if (!columnOrRole || !mapping) return columnOrRole;
      const columnsMap = mapping.columns || mapping;
      for (const [colName, colData] of Object.entries(columnsMap)) {
        const currRole = typeof colData === 'string' ? colData : colData.semantic_role;
        if (currRole === columnOrRole) {
          return colName;
        }
      }
      return columnOrRole;
    };

    const getMissingValuesCount = (columnName, prof) => {
      if (!columnName || !prof) return 0;
      const metrics = prof.quality_metrics?.[columnName] || prof.quality_profiles?.[columnName];
      if (metrics) {
        return metrics.missing_count || metrics.null_count || 0;
      }
      return 0;
    };

    const getTimeGranularity = (dimName) => {
      const dim = (dimName || '').toLowerCase();
      if (dim.includes('date') || dim.includes('time') || dim.includes('timestamp')) {
        if (dim.includes('hour') || dim.includes('time_of_day')) return 'Hourly';
        if (dim.includes('month')) return 'Monthly';
        if (dim.includes('day_of_week') || dim.includes('weekday')) return 'Weekly Day Pacing';
        return 'Daily Trend';
      }
      return 'Categorical distribution';
    };
    // Trend evaluator heuristic
    const analyzeTrend = (scannedInfo, chartType) => {
      const type = (chartType || '').toLowerCase();
      if (!type.includes('line') && !type.includes('scatter')) {
        return 'Not applicable (Non-temporal category grouping)';
      }
      const data = chartObject.chart_data || [];
      if (data.length < 4) return 'Stable pacing (Insufficient observations)';

      const half = Math.floor(data.length / 2);
      const yAxis = chartObject.y_axis;
      
      let firstHalfSum = 0;
      let firstHalfCount = 0;
      for (let i = 0; i < half; i++) {
        const val = Number(data[i][yAxis]);
        if (!isNaN(val)) {
          firstHalfSum += val;
          firstHalfCount++;
        }
      }

      let secondHalfSum = 0;
      let secondHalfCount = 0;
      for (let i = half; i < data.length; i++) {
        const val = Number(data[i][yAxis]);
        if (!isNaN(val)) {
          secondHalfSum += val;
          secondHalfCount++;
        }
      }

      const avg1 = firstHalfCount > 0 ? firstHalfSum / firstHalfCount : 0;
      const avg2 = secondHalfCount > 0 ? secondHalfSum / secondHalfCount : 0;

      if (avg1 === 0) return 'Stable pacing';
      const pctDiff = ((avg2 - avg1) / avg1) * 100;

      if (pctDiff > 5) return `Increasing trend (+${pctDiff.toFixed(1)}% pacing shift)`;
      if (pctDiff < -5) return `Decreasing trend (${pctDiff.toFixed(1)}% pacing shift)`;
      return 'Stable pacing (pacing deviation within ±5%)';
    };

    // Contextual recommendations mappings
    const getRecommendedActions = (chart, kpiName, dimName) => {
      const category = getBusinessCategory(finalKPIs.find(k => k.id === chart.required_kpis?.[0]));
      const dim = (dimName || '').toLowerCase();
      
      if (category.includes('Financial')) {
        return [
          `Review outlier values under ${dimName} for potential margin leakage.`,
          `Analyze cost components during maximum peaks (${scanned ? scanned.maxLabel : 'N/A'}) to identify savings opportunities.`,
          `Set up alerts for when the metric drops below minimum thresholds.`
        ];
      }
      if (category.includes('Delivery')) {
        return [
          `Optimize rider zoning parameters for regions showcasing delay patterns.`,
          `Evaluate dispatch delays during maximum latency peaks to coordinate grid schedules.`,
          `Formulate SLA buffers during high-congestion periods.`
        ];
      }
      if (category.includes('Customer')) {
        return [
          `Target segments under ${dimName} reporting below-average retention levels.`,
          `Incentivize top performing segments showing optimal metrics.`,
          `Conduct customer surveys around low periods to address drop-offs.`
        ];
      }
      return [
        `Monitor metrics periodically to capture seasonal patterns under ${dimName}.`,
        `Investigate operational bottlenecks contributing to maximum deviations.`,
        `Examine data points adjacent to outliers for surrounding context.`
      ];
    };

    const primaryKpiId = chartObject.required_kpis?.[0];
    const kpiObject = finalKPIs.find(k => k.id === primaryKpiId);
    const kpiDisplayName = kpiObject ? kpiObject.display_name : (primaryKpiId || 'N/A');
    const resolvedDimension = resolveSourceColumn(chartObject.x_axis || chartObject.y_axis);
    
    // Resolve formula string
    const formula = kpiObject?.formula || 'N/A';
    let formulaStr = 'N/A';
    if (typeof formula === 'string') formulaStr = formula;
    else if (formula && formula.operation) {
      formulaStr = `${formula.operation}(${(formula.fields || []).join(', ')})`;
    }

    // Resolve source columns
    const sourceCols = [];
    if (kpiObject?.required_semantic_roles) {
      kpiObject.required_semantic_roles.forEach(role => {
        const col = resolveSourceColumn(role);
        if (col && !sourceCols.includes(col)) sourceCols.push(col);
      });
    }
    if (sourceCols.length === 0) sourceCols.push(resolvedDimension);

    const categoryName = getBusinessCategory(kpiObject);
    const granularity = getTimeGranularity(resolvedDimension);
    const dataPoints = chartObject.chart_data?.length || 0;
    
    let nullCountSum = 0;
    sourceCols.forEach(col => {
      nullCountSum += getMissingValuesCount(col, profile);
    });
    nullCountSum += getMissingValuesCount(resolvedDimension, profile);

    const trendType = analyzeTrend(scanned, chartObject.chart_type);
    
    const totalRows = profile?.dataset_metadata?.row_count || 100;
    const nullRatio = nullCountSum / (totalRows * (sourceCols.length + 1) || 1);
    let confidenceRating = 'High';
    if (nullRatio > 0.1) confidenceRating = 'Low';
    else if (nullRatio > 0.01) confidenceRating = 'Medium';

    const recommendationCards = getRecommendedActions(chartObject, kpiDisplayName, resolvedDimension);

    return {
      primaryKpiId,
      kpiObject,
      kpiDisplayName,
      resolvedDimension,
      formulaStr,
      sourceCols,
      categoryName,
      granularity,
      dataPoints,
      nullCountSum,
      scanned,
      trendType,
      confidenceRating,
      recommendationCards
    };
  }, [chartObject, sessionInfo]);

  const formatCompact = (val) => {
    if (typeof val !== 'number') return val;
    if (val >= 1000000) return `${(val / 1000000).toFixed(1)}M`;
    if (val >= 1000) return `${(val / 1000).toFixed(1)}k`;
    return val.toFixed(1);
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

  if (!chartObject && !loading) {
    return (
      <div className="min-h-screen bg-slate-50 dark:bg-[#0d0e12] flex items-center justify-center text-slate-800 dark:text-slate-100 font-sans p-4">
        <EmptyState 
          title="Visualization Not Found"
          description="The visualization ID you requested is no longer available in this session plan."
          actionText="Back to Explorer"
          onAction={() => navigate(`/analysis/visualizations/${sessionId}`)}
          iconType="default"
        />
      </div>
    );
  }

  return (
    <ErrorBoundary message="Failed to load visualization detail workspace. Please return to Explorer.">
      <div className="min-h-screen bg-slate-50 dark:bg-[#0d0e12] text-slate-800 dark:text-slate-100 font-sans relative pb-16 transition-colors duration-200">
      <div className="absolute top-0 right-1/4 w-96 h-96 bg-indigo-500/5 rounded-full blur-[100px] pointer-events-none"></div>

      <header className="sticky top-0 z-40 w-full border-b border-slate-200 dark:border-slate-800 bg-white/80 dark:bg-[#0d0e12]/80 backdrop-blur-md">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <button 
              onClick={() => navigate(`/analysis/visualizations/${sessionId}`)}
              className="p-1.5 rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/50 dark:hover:bg-slate-800 text-xs font-bold cursor-pointer transition-colors text-slate-600 dark:text-slate-300"
              aria-label="Back to Visualization Explorer"
            >
              &larr; Explorer
            </button>
            <span className="text-xs font-bold text-slate-450 dark:text-slate-500 font-mono">ID: {visualizationId?.substring(0, 8)}...</span>
          </div>
          {chartObject?.chart_type && (
            <span className="px-2 py-0.5 rounded bg-indigo-500/10 text-indigo-500 border border-indigo-500/20 text-[10px] uppercase font-bold font-mono">
              {chartObject.chart_type}
            </span>
          )}
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-10 relative z-10 space-y-8">
        
        {/* Breadcrumb Navigation */}
        <div className="flex items-center gap-1.5 text-xs text-slate-450 dark:text-slate-500 select-none text-left">
          <span className="cursor-pointer hover:text-indigo-500 transition-colors" onClick={() => navigate('/upload')}>Analysis Workspace</span>
          <span>&gt;</span>
          <span className="cursor-pointer hover:text-indigo-500 transition-colors" onClick={() => navigate(`/analysis/visualizations/${sessionId}`)}>Visualization Explorer</span>
          <span>&gt;</span>
          <span className="text-slate-700 dark:text-slate-300 font-bold truncate max-w-[200px]">{chartObject?.title || 'Chart Details'}</span>
        </div>

        {/* Header Metadata Title block */}
        <div className="text-left space-y-2">
          <h1 className="text-2xl sm:text-3xl font-black tracking-tight text-slate-900 dark:text-slate-100">
            {chartObject?.title || 'Metric Analysis Detail'}
          </h1>
          <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-slate-550 dark:text-slate-400">
            <span>Dataset: <strong className="font-semibold text-slate-700 dark:text-slate-300">{sessionInfo?.mappingData?.dataset_name || 'Commerce Log'}</strong></span>
            <span>•</span>
            <span>Domain: <strong className="font-semibold text-slate-700 dark:text-slate-300">{sessionInfo?.domainData?.domain || 'Retail'}</strong></span>
          </div>
        </div>

        {loading ? (
          <div className="space-y-6">
            <ChartAreaSkeleton />
            <InsightsPanelSkeleton />
          </div>
        ) : (
          <>
            {/* Live Interactive Chart Panel */}
            <div className="rounded-3xl border border-slate-200 dark:border-slate-850 bg-white dark:bg-[#111217]/35 p-6 flex flex-col items-center justify-center min-h-[300px] shadow-sm relative overflow-hidden">
              <div className="w-full h-[360px] relative z-10">
                <ErrorBoundary message="Failed to render interactive chart. The dataset may contain unsupported coordinates or data types.">
                  <ChartRenderer visualization={chartObject} />
                </ErrorBoundary>
              </div>
            </div>

            {/* Dynamic AI Business Insights Panel */}
            <div className="rounded-3xl border border-slate-200 dark:border-slate-850 bg-white dark:bg-[#111217]/35 p-6 sm:p-8 space-y-8 text-left shadow-lg">
              <div className="flex items-center justify-between gap-4 pb-4 border-b border-slate-150 dark:border-slate-850/60">
                <div className="flex items-center gap-3">
                  <div className="w-9 h-9 rounded-xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-500 animate-pulse">
                    <svg className="w-4.5 h-4.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                    </svg>
                  </div>
                  <div>
                    <h3 className="text-base font-bold text-slate-800 dark:text-slate-100">AI Business Insights</h3>
                    <p className="text-[10px] text-slate-400">Contextual evaluation generated from verified dataset metrics</p>
                  </div>
                </div>
                
                {/* Confidence Badge */}
                <div className="flex items-center gap-2">
                  <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider">Confidence:</span>
                  <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold border ${
                    details?.confidenceRating === 'High' 
                      ? 'bg-emerald-500/10 text-emerald-500 border-emerald-500/20' 
                      : details?.confidenceRating === 'Medium'
                      ? 'bg-amber-500/10 text-amber-500 border-amber-500/20'
                      : 'bg-red-500/10 text-red-500 border-red-500/20'
                  }`}>
                    {details?.confidenceRating}
                  </span>
                </div>
              </div>

              {/* Insights content layout split */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                
                {/* Section A: Executive Summary & Interpretation */}
                <div className="space-y-6">
                  <div className="p-5 rounded-2xl border border-slate-200 dark:border-slate-850 bg-slate-50/50 dark:bg-slate-900/10 space-y-2">
                    <h5 className="text-[10px] uppercase font-bold text-slate-400 tracking-wider">Executive Summary</h5>
                    <p className="text-xs text-slate-650 dark:text-slate-300 leading-relaxed">
                      This {chartObject?.chart_type} analyzes the pacing of <strong className="font-semibold text-slate-800 dark:text-slate-150">{details?.kpiDisplayName}</strong> distributed across {details?.dataPoints} discrete coordinates of <strong className="font-semibold text-slate-800 dark:text-slate-150">{details?.resolvedDimension}</strong>. The model reveals key anomalies that are crucial for operational scheduling and resource balancing.
                    </p>
                  </div>

                  <div className="p-5 rounded-2xl border border-slate-200 dark:border-slate-850 bg-slate-50/50 dark:bg-slate-900/10 space-y-2">
                    <h5 className="text-[10px] uppercase font-bold text-slate-400 tracking-wider">Business Interpretation</h5>
                    <p className="text-xs text-slate-650 dark:text-slate-350 leading-relaxed italic">
                      "Understanding fluctuations in {details?.kpiDisplayName} by {details?.resolvedDimension} enables managers to align shifts, optimize zoning targets, and adjust procurement paces. Peaks suggest periods of maximum stress, while valleys indicate under-utilized capacities."
                    </p>
                  </div>
                </div>

                {/* Section B: Key Findings & Data Quality */}
                <div className="space-y-6">
                  
                  {/* Scan results Card */}
                  <div className="p-5 rounded-2xl border border-slate-200 dark:border-slate-850 bg-slate-50/50 dark:bg-slate-900/10 space-y-3">
                    <h5 className="text-[10px] uppercase font-bold text-slate-400 tracking-wider">Key Findings</h5>
                    <ul className="space-y-2.5 text-xs text-slate-600 dark:text-slate-300">
                      <li className="flex justify-between items-center gap-4">
                        <span>Maximum Coordinate Peak:</span>
                        <strong className="font-mono font-bold text-slate-800 dark:text-slate-100">
                          {details?.scanned ? formatCompact(details.scanned.maxVal) : 'N/A'}{' '}
                          <span className="text-[9px] text-slate-400 font-normal">({details?.scanned?.maxLabel})</span>
                        </strong>
                      </li>
                      <li className="flex justify-between items-center gap-4">
                        <span>Minimum Coordinate Valley:</span>
                        <strong className="font-mono font-bold text-slate-800 dark:text-slate-100">
                          {details?.scanned ? formatCompact(details.scanned.minVal) : 'N/A'}{' '}
                          <span className="text-[9px] text-slate-400 font-normal">({details?.scanned?.minLabel})</span>
                        </strong>
                      </li>
                      <li className="flex justify-between items-center gap-4">
                        <span>Observed Categories/Periods:</span>
                        <strong className="font-mono font-bold text-slate-800 dark:text-slate-100">{details?.dataPoints}</strong>
                      </li>
                      <li className="flex justify-between items-center gap-4">
                        <span>Trend Classification:</span>
                        <span className="font-mono font-bold text-indigo-500 dark:text-indigo-405">{details?.trendType}</span>
                      </li>
                    </ul>
                  </div>

                  {/* Data Quality Card */}
                  <div className="p-5 rounded-2xl border border-slate-200 dark:border-slate-850 bg-slate-50/50 dark:bg-slate-900/10 space-y-3">
                    <h5 className="text-[10px] uppercase font-bold text-slate-450 tracking-wider">Data Quality Notes</h5>
                    <ul className="space-y-2 text-xs text-slate-600 dark:text-slate-300">
                      <li className="flex justify-between items-center gap-4">
                        <span>Total Observations:</span>
                        <strong className="font-mono font-bold text-slate-800 dark:text-slate-100">{details?.dataPoints} points</strong>
                      </li>
                      <li className="flex justify-between items-center gap-4">
                        <span>Missing Values (Source & X-Axis):</span>
                        <strong className={`font-mono font-bold ${details?.nullCountSum > 0 ? 'text-amber-500' : 'text-slate-800 dark:text-slate-100'}`}>
                          {details?.nullCountSum} nulls
                        </strong>
                      </li>
                      <li className="flex justify-between items-center gap-4">
                        <span>Analysis Quality Index:</span>
                        <span className="font-bold text-slate-800 dark:text-slate-100">
                          {details?.nullCountSum === 0 ? 'Optimal (100% Grounded)' : 'Sufficient (Grounded)'}
                        </span>
                      </li>
                    </ul>
                  </div>

                </div>
              </div>

              {/* Recommended Actions cards row */}
              <div className="space-y-3.5 pt-6 border-t border-slate-150 dark:border-slate-850/60">
                <h5 className="text-[10px] uppercase font-bold text-slate-400 tracking-wider">Recommended Business Actions</h5>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  {details?.recommendationCards.map((action, i) => (
                    <div key={i} className="p-4 rounded-xl border border-slate-205 dark:border-slate-850 bg-slate-50/20 dark:bg-[#111217]/10 flex gap-3 items-start hover:border-indigo-500/25 hover:bg-slate-50/50 dark:hover:bg-slate-900/5 transition-colors">
                      <span className="text-indigo-500 font-bold mt-0.5">&#8226;</span>
                      <p className="text-xs text-slate-550 dark:text-slate-350 leading-relaxed">
                        {action}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Desktop Responsive Sections layout */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 text-left">
              
              {/* Col 1 & 2: Metadata, KPI Lineage, and Config */}
              <div className="lg:col-span-2 space-y-6">
                
                {/* Metadata Card Panel */}
                <div className="p-6 rounded-3xl border border-slate-200 dark:border-slate-850 bg-white dark:bg-[#111217]/25 space-y-4">
                  <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400">Visualization Metadata</h4>
                  <div className="grid grid-cols-2 gap-4 text-xs">
                    <div>
                      <span className="block text-[9px] uppercase font-bold text-slate-450 dark:text-slate-500">Primary KPI</span>
                      <span className="block mt-1 font-bold text-slate-800 dark:text-slate-100">{details?.kpiDisplayName}</span>
                    </div>
                    <div>
                      <span className="block text-[9px] uppercase font-bold text-slate-455 dark:text-slate-500">Primary Dimension</span>
                      <span className="block mt-1 font-bold text-slate-800 dark:text-slate-100">{details?.resolvedDimension}</span>
                    </div>
                    <div>
                      <span className="block text-[9px] uppercase font-bold text-slate-455 dark:text-slate-500">Source Columns</span>
                      <div className="flex flex-wrap gap-1 mt-1">
                        {details?.sourceCols.map((c, i) => (
                          <span key={i} className="px-1.5 py-0.2 rounded font-mono text-[9px] bg-slate-100 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-slate-600 dark:text-slate-350">{c}</span>
                        ))}
                      </div>
                    </div>
                    <div>
                      <span className="block text-[9px] uppercase font-bold text-slate-455 dark:text-slate-500">Aggregation Method</span>
                      <span className="block mt-1 font-mono font-bold text-indigo-500 dark:text-indigo-400 uppercase">{chartObject?.aggregation_method || details?.aggregation}</span>
                    </div>
                  </div>
                  <div className="pt-2.5 border-t border-slate-150 dark:border-slate-850/60">
                    <span className="block text-[9px] uppercase font-bold text-slate-450 dark:text-slate-500">Business Purpose</span>
                    <p className="mt-1 text-xs text-slate-500 dark:text-slate-400 leading-relaxed italic">
                      "{chartObject?.business_purpose || details?.kpiObject?.explanation || 'Aggregated metrics distribution analysis'}"
                    </p>
                  </div>
                </div>

                {/* KPI Lineage Panel */}
                <div className="p-6 rounded-3xl border border-slate-200 dark:border-slate-850 bg-white dark:bg-[#111217]/25 space-y-4">
                  <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400">KPI Generation Lineage</h4>
                  
                  <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 text-xs bg-slate-50/50 dark:bg-slate-900/10 p-4 rounded-2xl border border-slate-200 dark:border-slate-850/50">
                    {/* Node 1: Raw Columns */}
                    <div className="space-y-1">
                      <span className="block text-[9px] font-bold text-slate-400 uppercase tracking-wide">Raw Columns</span>
                      <div className="flex flex-col gap-0.5">
                        {details?.sourceCols.map((c, i) => (
                          <span key={i} className="font-mono text-[10px] font-bold text-slate-700 dark:text-slate-300">{c}</span>
                        ))}
                      </div>
                    </div>

                    <span className="hidden sm:inline text-indigo-500/40 text-lg font-bold">&rarr;</span>

                    {/* Node 2: Semantic Roles */}
                    <div className="space-y-1">
                      <span className="block text-[9px] font-bold text-slate-400 uppercase tracking-wide">Semantic Roles</span>
                      <div className="flex flex-col gap-0.5">
                        {details?.kpiObject?.required_semantic_roles?.map((role, i) => (
                          <span key={i} className="font-mono text-[10px] font-bold text-indigo-400">{role}</span>
                        ))}
                      </div>
                    </div>

                    <span className="hidden sm:inline text-indigo-500/40 text-lg font-bold">&rarr;</span>

                    {/* Node 3: Aggregation */}
                    <div className="space-y-1">
                      <span className="block text-[9px] font-bold text-slate-400 uppercase tracking-wide">Aggregation</span>
                      <span className="font-mono font-bold text-emerald-500 text-[10px]">{details?.aggregation}</span>
                    </div>

                    <span className="hidden sm:inline text-indigo-500/40 text-lg font-bold">&rarr;</span>

                    {/* Node 4: final KPI */}
                    <div className="space-y-1">
                      <span className="block text-[9px] font-bold text-slate-400 uppercase tracking-wide">Generated KPI</span>
                      <span className="font-bold text-slate-800 dark:text-slate-100 text-[10px]">{details?.kpiDisplayName}</span>
                    </div>
                  </div>
                </div>

                {/* Configuration Details */}
                <div className="p-6 rounded-3xl border border-slate-200 dark:border-slate-850 bg-white dark:bg-[#111217]/25 space-y-4">
                  <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400">Chart Configuration parameters</h4>
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs">
                    <div>
                      <span className="block text-[9px] uppercase font-bold text-slate-450 dark:text-slate-500">X-Axis Variable</span>
                      <span className="block mt-1 font-mono text-slate-700 dark:text-slate-355">{chartObject?.x_axis || 'N/A'}</span>
                    </div>
                    <div>
                      <span className="block text-[9px] uppercase font-bold text-slate-455 dark:text-slate-500">Y-Axis Variable</span>
                      <span className="block mt-1 font-mono text-slate-700 dark:text-slate-355">{chartObject?.y_axis || 'N/A'}</span>
                    </div>
                    <div>
                      <span className="block text-[9px] uppercase font-bold text-slate-455 dark:text-slate-500">Group By Field</span>
                      <span className="block mt-1 font-mono text-slate-700 dark:text-slate-355">{chartObject?.config?.grouped ? 'Active' : 'None'}</span>
                    </div>
                    <div>
                      <span className="block text-[9px] uppercase font-bold text-slate-455 dark:text-slate-500">Dashboard Section</span>
                      <span className="block mt-1 text-slate-700 dark:text-slate-355">{chartObject?.section || 'General'}</span>
                    </div>
                  </div>
                </div>

              </div>

              {/* Col 3: Insights Summary, Data Summary and Related KPIs */}
              <div className="space-y-6">
                
                {/* Insights Summary Section */}
                <div className="p-6 rounded-3xl border border-slate-200 dark:border-slate-850 bg-white dark:bg-[#111217]/25 space-y-4">
                  <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400">Insights Summary</h4>
                  <div className="divide-y divide-slate-150 dark:divide-slate-850/60 text-xs">
                    <div className="py-2.5 flex justify-between items-center gap-4">
                      <span className="text-slate-500 dark:text-slate-400 flex items-center gap-1.5">
                        <span className="text-emerald-500 font-bold">&#10003;</span> Chart Type
                      </span>
                      <span className="font-bold text-slate-800 dark:text-slate-100">{chartObject?.chart_type?.toUpperCase()}</span>
                    </div>
                    <div className="py-2.5 flex justify-between items-center gap-4">
                      <span className="text-slate-500 dark:text-slate-400 flex items-center gap-1.5">
                        <span className="text-emerald-500 font-bold">&#10003;</span> KPI
                      </span>
                      <span className="font-bold text-slate-800 dark:text-slate-100">{details?.kpiDisplayName}</span>
                    </div>
                    <div className="py-2.5 flex justify-between items-center gap-4">
                      <span className="text-slate-500 dark:text-slate-400 flex items-center gap-1.5">
                        <span className="text-emerald-500 font-bold">&#10003;</span> Dimension
                      </span>
                      <span className="font-bold text-slate-800 dark:text-slate-100">{details?.resolvedDimension}</span>
                    </div>
                    <div className="py-2.5 flex justify-between items-center gap-4">
                      <span className="text-slate-500 dark:text-slate-400 flex items-center gap-1.5">
                        <span className="text-emerald-500 font-bold">&#10003;</span> Time Granularity
                      </span>
                      <span className="font-bold text-slate-800 dark:text-slate-100">{details?.granularity}</span>
                    </div>
                    <div className="py-2.5 flex justify-between items-center gap-4">
                      <span className="text-slate-500 dark:text-slate-400 flex items-center gap-1.5">
                        <span className="text-emerald-500 font-bold">&#10003;</span> Data Points
                      </span>
                      <span className="font-mono font-bold text-slate-800 dark:text-slate-100">{details?.dataPoints}</span>
                    </div>
                    <div className="py-2.5 flex justify-between items-center gap-4">
                      <span className="text-slate-500 dark:text-slate-400 flex items-center gap-1.5">
                        <span className="text-emerald-500 font-bold">&#10003;</span> Missing Values
                      </span>
                      <span className="font-mono font-bold text-slate-800 dark:text-slate-100">{details?.nullCountSum}</span>
                    </div>
                    <div className="py-2.5 flex justify-between items-center gap-4">
                      <span className="text-slate-500 dark:text-slate-400 flex items-center gap-1.5">
                        <span className="text-emerald-500 font-bold">&#10003;</span> Numeric Measures
                      </span>
                      <span className="font-mono font-bold text-slate-800 dark:text-slate-100">1</span>
                    </div>
                  </div>
                </div>

                {/* Data Summary Card */}
                <div className="p-6 rounded-3xl border border-slate-200 dark:border-slate-850 bg-white dark:bg-[#111217]/25 space-y-4">
                  <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400">Dataset Diagnostics</h4>
                  <div className="grid grid-cols-2 gap-4 text-xs">
                    <div className="p-3 bg-slate-50/50 dark:bg-slate-900/10 rounded-xl border border-slate-200 dark:border-slate-855/50">
                      <span className="block text-[8px] uppercase font-bold text-slate-400">Total Rows</span>
                      <span className="block mt-1 font-mono font-bold text-slate-800 dark:text-slate-100">{sessionInfo?.profileData?.dataset_metadata?.row_count || 'N/A'}</span>
                    </div>
                    <div className="p-3 bg-slate-50/50 dark:bg-slate-900/10 rounded-xl border border-slate-200 dark:border-slate-855/50">
                      <span className="block text-[8px] uppercase font-bold text-slate-400">Total Columns</span>
                      <span className="block mt-1 font-mono font-bold text-slate-800 dark:text-slate-100">{sessionInfo?.profileData?.dataset_metadata?.column_count || 'N/A'}</span>
                    </div>
                  </div>
                </div>

                {/* Related KPIs Chips */}
                <div className="p-6 rounded-3xl border border-slate-200 dark:border-slate-850 bg-white dark:bg-[#111217]/25 space-y-4">
                  <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400">Related KPI References</h4>
                  <div className="flex flex-wrap gap-1.5">
                    {chartObject?.required_kpis?.map((kpiId) => {
                      const kObject = sessionInfo?.finalKPIs?.find(k => k.id === kpiId);
                      return (
                        <span 
                          key={kpiId} 
                          className="px-2.5 py-1 rounded-xl bg-slate-100 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-[10px] font-semibold text-slate-450 cursor-not-allowed opacity-75 select-none"
                        >
                          {kObject ? kObject.display_name : kpiId}
                        </span>
                      );
                    })}
                  </div>
                </div>

              </div>

            </div>
          </>
        )}

      </main>
    </div>
    </ErrorBoundary>
  );
};

export default VisualizationDetail;
