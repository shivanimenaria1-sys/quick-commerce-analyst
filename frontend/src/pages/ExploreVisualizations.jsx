import React, { useState, useEffect, useMemo } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { apiService } from '../services/api';
import { analysisSessionStorage } from '../services/storageService';
import ErrorBoundary from '../components/ErrorBoundary';
import EmptyState from '../components/EmptyState';

// Shimmer Loader for stats
const StatCardSkeleton = () => (
  <div className="p-5 rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-[#111217]/30 text-left flex flex-col justify-between min-h-[90px]">
    <div className="h-3 w-20 bg-slate-200 dark:bg-slate-800/80 rounded shimmer"></div>
    <div className="h-7 w-12 bg-slate-200 dark:bg-slate-800 rounded shimmer mt-2"></div>
  </div>
);

// Shimmer Loader for cards list
const ChartCardSkeleton = () => (
  <div className="rounded-3xl border border-slate-200 dark:border-slate-850 bg-white dark:bg-[#111217]/20 shadow-sm flex flex-col overflow-hidden min-h-[280px]">
    <div className="h-32 bg-slate-200 dark:bg-slate-800/70 rounded-t shimmer"></div>
    <div className="p-6 space-y-4 flex-1 flex flex-col justify-between">
      <div className="space-y-2.5">
        <div className="h-5 w-2/3 bg-slate-200 dark:bg-slate-800/80 rounded shimmer"></div>
        <div className="h-3 w-1/3 bg-slate-200 dark:bg-slate-800/60 rounded shimmer"></div>
        <div className="h-3 w-full bg-slate-200 dark:bg-slate-800/50 rounded shimmer mt-3"></div>
      </div>
      <div className="h-6 w-24 bg-slate-200 dark:bg-slate-800/80 rounded-xl shimmer mt-2 self-end"></div>
    </div>
  </div>
);

// Inline Mini SVG Preview Component
const MiniChartPreview = ({ type }) => {
  const chartType = (type || '').toLowerCase();
  
  if (chartType.includes('line')) {
    return (
      <svg className="w-full h-20 text-indigo-500/30" viewBox="0 0 100 40" fill="none" stroke="currentColor">
        <path d="M5 35 H95 M5 35 L20 18 L40 28 L60 10 L80 20 L95 5" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
        <path d="M5 35 L20 18 L40 28 L60 10 L80 20 L95 5 L95 35 Z" fill="url(#lineGrad)" opacity="0.1" />
        <defs>
          <linearGradient id="lineGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="rgb(99, 102, 241)" />
            <stop offset="100%" stopColor="transparent" />
          </linearGradient>
        </defs>
      </svg>
    );
  }
  if (chartType.includes('bar') || chartType.includes('histogram')) {
    return (
      <svg className="w-full h-20 text-indigo-500/30" viewBox="0 0 100 40" fill="none" stroke="currentColor">
        <line x1="5" y1="35" x2="95" y2="35" strokeWidth="1" />
        <rect x="12" y="15" width="10" height="20" rx="1" fill="currentColor" opacity="0.8" />
        <rect x="28" y="8" width="10" height="27" rx="1" fill="currentColor" opacity="0.6" />
        <rect x="44" y="20" width="10" height="15" rx="1" fill="currentColor" opacity="0.8" />
        <rect x="60" y="5" width="10" height="30" rx="1" fill="currentColor" opacity="0.5" />
        <rect x="76" y="18" width="10" height="17" rx="1" fill="currentColor" opacity="0.7" />
      </svg>
    );
  }
  if (chartType.includes('pie') || chartType.includes('donut') || chartType.includes('ring')) {
    return (
      <svg className="w-full h-20 text-indigo-500/30" viewBox="0 0 100 40" fill="none">
        <circle cx="50" cy="20" r="16" stroke="currentColor" strokeWidth="6" strokeDasharray="30 70" fill="none" transform="rotate(-90 50 20)" opacity="0.7" />
        <circle cx="50" cy="20" r="16" stroke="currentColor" strokeWidth="6" strokeDasharray="45 55" fill="none" transform="rotate(20 50 20)" opacity="0.5" />
        <circle cx="50" cy="20" r="16" stroke="currentColor" strokeWidth="6" strokeDasharray="25 75" fill="none" transform="rotate(180 50 20)" opacity="0.8" />
      </svg>
    );
  }
  if (chartType.includes('scatter')) {
    return (
      <svg className="w-full h-20 text-indigo-500/30" viewBox="0 0 100 40" fill="currentColor">
        <circle cx="15" cy="25" r="2.5" opacity="0.6" />
        <circle cx="30" cy="15" r="2" opacity="0.8" />
        <circle cx="45" cy="28" r="2.5" opacity="0.5" />
        <circle cx="55" cy="12" r="2" opacity="0.7" />
        <circle cx="70" cy="22" r="3" opacity="0.6" />
        <circle cx="85" cy="8" r="2" opacity="0.9" />
        <line x1="5" y1="35" x2="95" y2="35" stroke="currentColor" strokeWidth="1" opacity="0.3" />
      </svg>
    );
  }
  if (chartType.includes('box')) {
    return (
      <svg className="w-full h-20 text-indigo-500/30" viewBox="0 0 100 40" fill="none" stroke="currentColor" strokeWidth="1.5">
        <line x1="10" y1="20" x2="90" y2="20" strokeDasharray="3 3" />
        <line x1="10" y1="12" x2="10" y2="28" />
        <line x1="90" y1="12" x2="90" y2="28" />
        <rect x="30" y="8" width="40" height="24" fill="currentColor" opacity="0.15" />
        <line x1="55" y1="8" x2="55" y2="32" strokeWidth="2.5" />
      </svg>
    );
  }
  if (chartType.includes('heatmap')) {
    return (
      <svg className="w-full h-20 text-indigo-500/30" viewBox="0 0 100 40" fill="currentColor">
        <rect x="5" y="4" width="26" height="14" rx="1.5" opacity="0.3" />
        <rect x="37" y="4" width="26" height="14" rx="1.5" opacity="0.8" />
        <rect x="69" y="4" width="26" height="14" rx="1.5" opacity="0.5" />
        <rect x="5" y="22" width="26" height="14" rx="1.5" opacity="0.7" />
        <rect x="37" y="22" width="26" height="14" rx="1.5" opacity="0.4" />
        <rect x="69" y="22" width="26" height="14" rx="1.5" opacity="0.9" />
      </svg>
    );
  }
  return (
    <svg className="w-full h-20 text-indigo-500/30" viewBox="0 0 100 40" fill="none" stroke="currentColor">
      <rect x="10" y="5" width="80" height="30" rx="2" strokeDasharray="3 3" />
      <path d="M20 20 H80" opacity="0.4" />
    </svg>
  );
};

export const ExploreVisualizations = () => {
  const { sessionId } = useParams();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  const [sessionInfo, setSessionInfo] = useState(null);
  const [expandedChartId, setExpandedChartId] = useState(null);
  
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedChartType, setSelectedChartType] = useState('all');
  const [selectedKpi, setSelectedKpi] = useState('all');
  const [selectedDimension, setSelectedDimension] = useState('all');
  const [sortBy, setSortBy] = useState('alphabetical'); // 'alphabetical', 'type', 'kpi'

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
        console.debug('[SESSION_DEBUG] ExploreVisualizations after updateFromAnalysis:', {
          sessionId: sessionId?.substring(0, 8),
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

  const charts = useMemo(() => {
    const rawCharts = sessionInfo?.dashboardPlan?.dashboard?.charts || [];
    return rawCharts.map(c => ({
      ...c,
      id: c.id || c.chart_id
    }));
  }, [sessionInfo]);

  const stats = useMemo(() => {
    if (charts.length === 0) {
      return { total: 0, uniqueTypes: 0, mostUsedKpi: 'N/A', totalDimensions: 0 };
    }
    
    const uniqueTypes = new Set(charts.map(c => c.chart_type)).size;
    
    const kpiCounts = {};
    charts.forEach(c => {
      const kpis = c.required_kpis || [];
      kpis.forEach(id => {
        kpiCounts[id] = (kpiCounts[id] || 0) + 1;
      });
    });
    
    let maxCount = -1;
    let mostUsedKpiId = 'N/A';
    Object.entries(kpiCounts).forEach(([kpiId, count]) => {
      if (count > maxCount) {
        maxCount = count;
        mostUsedKpiId = kpiId;
      }
    });

    const kpiObject = sessionInfo?.finalKPIs?.find(k => k.id === mostUsedKpiId);
    const mostUsedKpiName = kpiObject ? kpiObject.display_name : mostUsedKpiId;

    const dimensions = new Set();
    charts.forEach(c => {
      if (c.x_axis) dimensions.add(c.x_axis);
      if (c.y_axis) dimensions.add(c.y_axis);
    });
    
    const kpiIds = new Set(sessionInfo?.finalKPIs?.map(k => k.id) || []);
    const cleanDimensions = Array.from(dimensions).filter(d => !kpiIds.has(d));

    return {
      total: charts.length,
      uniqueTypes,
      mostUsedKpi: mostUsedKpiName,
      totalDimensions: cleanDimensions.length
    };
  }, [charts, sessionInfo]);

  const filterOptions = useMemo(() => {
    const types = new Set();
    const kpis = new Set();
    const dims = new Set();
    
    const kpiIds = new Set(sessionInfo?.finalKPIs?.map(k => k.id) || []);

    charts.forEach(c => {
      if (c.chart_type) types.add(c.chart_type);
      if (c.required_kpis) {
        c.required_kpis.forEach(k => kpis.add(k));
      }
      if (c.x_axis && !kpiIds.has(c.x_axis)) dims.add(c.x_axis);
      if (c.y_axis && !kpiIds.has(c.y_axis)) dims.add(c.y_axis);
    });

    return {
      types: Array.from(types).sort(),
      kpis: Array.from(kpis).map(id => {
        const found = sessionInfo?.finalKPIs?.find(k => k.id === id);
        return { id, name: found ? found.display_name : id };
      }).sort((a, b) => a.name.localeCompare(b.name)),
      dimensions: Array.from(dims).sort()
    };
  }, [charts, sessionInfo]);

  const filteredAndSortedCharts = useMemo(() => {
    let result = [...charts];

    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      result = result.filter(c => 
        c.title?.toLowerCase().includes(q) ||
        c.chart_type?.toLowerCase().includes(q) ||
        c.x_axis?.toLowerCase().includes(q) ||
        c.y_axis?.toLowerCase().includes(q)
      );
    }

    if (selectedChartType !== 'all') {
      result = result.filter(c => c.chart_type === selectedChartType);
    }

    if (selectedKpi !== 'all') {
      result = result.filter(c => Array.isArray(c.required_kpis) && c.required_kpis.includes(selectedKpi));
    }

    if (selectedDimension !== 'all') {
      result = result.filter(c => c.x_axis === selectedDimension || c.y_axis === selectedDimension);
    }

    if (sortBy === 'alphabetical') {
      result.sort((a, b) => (a.title || '').localeCompare(b.title || ''));
    } else if (sortBy === 'type') {
      result.sort((a, b) => (a.chart_type || '').localeCompare(b.chart_type || ''));
    } else if (sortBy === 'kpi') {
      result.sort((a, b) => {
        const kpiA = a.required_kpis?.[0] || '';
        const kpiB = b.required_kpis?.[0] || '';
        return kpiA.localeCompare(kpiB);
      });
    }

    return result;
  }, [charts, searchQuery, selectedChartType, selectedKpi, selectedDimension, sortBy]);

  const groupedCharts = useMemo(() => {
    const groups = {};
    filteredAndSortedCharts.forEach(c => {
      let groupName = 'Fallback Charts';
      const type = (c.chart_type || '').toLowerCase();
      if (type.includes('line')) groupName = 'Line Charts';
      else if (type.includes('bar')) groupName = 'Bar Charts';
      else if (type.includes('pie') || type.includes('donut')) groupName = 'Pie & Donut Charts';
      else if (type.includes('scatter')) groupName = 'Scatter Plots';
      else if (type.includes('histogram')) groupName = 'Histograms';
      else if (type.includes('boxplot')) groupName = 'Box Plots';
      else if (type.includes('heatmap')) groupName = 'Heatmaps';
      
      if (!groups[groupName]) {
        groups[groupName] = [];
      }
      groups[groupName].push(c);
    });
    return groups;
  }, [filteredAndSortedCharts]);

  const toggleExpand = (id) => {
    setExpandedChartId(expandedChartId === id ? null : id);
  };

  const resolveSourceColumn = (columnOrRole, mapping) => {
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
              aria-label="Back to Upload Summary"
            >
              &larr; Summary
            </button>
            <span className="text-sm font-bold tracking-tight text-slate-700 dark:text-slate-200">Visualizations</span>
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
        <div className="flex items-center gap-1.5 text-xs text-slate-450 dark:text-slate-500 select-none text-left">
          <span className="cursor-pointer hover:text-indigo-500 transition-colors" onClick={() => navigate('/upload')}>Analysis Workspace</span>
          <span>&gt;</span>
          <span className="text-slate-700 dark:text-slate-300 font-bold">Visualization Explorer</span>
        </div>

        {/* Header Title Section */}
        <div className="text-left space-y-2">
          <h1 className="text-2xl sm:text-3xl font-black tracking-tight text-slate-900 dark:text-slate-100">
            Visualization Explorer
          </h1>
          <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-slate-550 dark:text-slate-400">
            <span>Dataset: <strong className="font-semibold text-slate-700 dark:text-slate-300">{sessionInfo?.mappingData?.dataset_name || 'Quick Commerce Log'}</strong></span>
            <span className="hidden sm:inline text-slate-300 dark:text-slate-800">•</span>
            <span>Fingerprint: <strong className="font-mono text-indigo-500">{sessionInfo?.mappingData?.schema_fingerprint?.substring(0, 12)}</strong></span>
          </div>
        </div>

        {/* Dynamic Statistics cards */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {loading ? (
            [1, 2, 3, 4].map(idx => <StatCardSkeleton key={idx} />)
          ) : (
            <>
              <div className="p-5 rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-[#111217]/30 text-left flex flex-col justify-between min-h-[90px]">
                <span className="block text-[10px] uppercase font-bold text-slate-450 tracking-wider">Total Recommended</span>
                <span className="text-2xl font-black text-slate-800 dark:text-slate-100 mt-2">{stats.total}</span>
              </div>
              <div className="p-5 rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-[#111217]/30 text-left flex flex-col justify-between min-h-[90px]">
                <span className="block text-[10px] uppercase font-bold text-slate-450 tracking-wider">Unique Chart Types</span>
                <span className="text-2xl font-black text-slate-800 dark:text-slate-100 mt-2">{stats.uniqueTypes}</span>
              </div>
              <div className="p-5 rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-[#111217]/30 text-left flex flex-col justify-between min-h-[90px]">
                <span className="block text-[10px] uppercase font-bold text-slate-450 tracking-wider">Most Referenced KPI</span>
                <span className="text-xs font-bold text-indigo-500 dark:text-indigo-400 mt-2 truncate" title={stats.mostUsedKpi}>
                  {stats.mostUsedKpi}
                </span>
              </div>
              <div className="p-5 rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-[#111217]/30 text-left flex flex-col justify-between min-h-[90px]">
                <span className="block text-[10px] uppercase font-bold text-slate-450 tracking-wider">Dimensions Tracked</span>
                <span className="text-2xl font-black text-slate-800 dark:text-slate-100 mt-2">{stats.totalDimensions}</span>
              </div>
            </>
          )}
        </div>

        {/* Filter and Sort Toolbar */}
        <div className="space-y-4 bg-white dark:bg-[#111217]/25 border border-slate-200 dark:border-slate-800 p-5 rounded-3xl backdrop-blur-sm text-left">
          <div className="flex flex-col md:flex-row gap-4 justify-between items-center">
            {/* Search Box */}
            <div className="w-full md:max-w-md relative">
              <input 
                type="text" 
                placeholder="Search by title, category, dimensions..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-10 pr-4 py-2 text-xs rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-900/60 focus:outline-none focus:border-indigo-500 text-slate-800 dark:text-slate-150 transition-colors"
                aria-label="Search recommended charts"
              />
              <svg className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            </div>

            {/* Sort Dropdown */}
            <div className="w-full md:w-auto flex items-center justify-end gap-2 shrink-0">
              <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Sort:</span>
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value)}
                className="px-3 py-2 text-xs rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-900/60 focus:outline-none focus:border-indigo-500 text-slate-700 dark:text-slate-350 cursor-pointer"
                aria-label="Sort charts by"
              >
                <option value="alphabetical">Alphabetical</option>
                <option value="type">Chart Type</option>
                <option value="kpi">KPI Dependency</option>
              </select>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-3 border-t border-slate-150 dark:border-slate-850/60">
            <div>
              <label className="block text-[9px] uppercase font-bold text-slate-450 dark:text-slate-500 tracking-wider mb-1.5">Chart Type</label>
              <select
                value={selectedChartType}
                onChange={(e) => setSelectedChartType(e.target.value)}
                className="w-full px-2.5 py-1.5 text-xs rounded-lg border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-900/60 focus:outline-none text-slate-700 dark:text-slate-350 cursor-pointer"
                aria-label="Filter by chart type"
              >
                <option value="all">All Types</option>
                {filterOptions.types.map(t => (
                  <option key={t} value={t}>{t.toUpperCase()}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-[9px] uppercase font-bold text-slate-450 dark:text-slate-500 tracking-wider mb-1.5">KPI Dependency</label>
              <select
                value={selectedKpi}
                onChange={(e) => setSelectedKpi(e.target.value)}
                className="w-full px-2.5 py-1.5 text-xs rounded-lg border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-900/60 focus:outline-none text-slate-700 dark:text-slate-350 cursor-pointer"
                aria-label="Filter by KPI dependency"
              >
                <option value="all">All KPIs</option>
                {filterOptions.kpis.map(k => (
                  <option key={k.id} value={k.id}>{k.name}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-[9px] uppercase font-bold text-slate-450 dark:text-slate-500 tracking-wider mb-1.5">Dimension Field</label>
              <select
                value={selectedDimension}
                onChange={(e) => setSelectedDimension(e.target.value)}
                className="w-full px-2.5 py-1.5 text-xs rounded-lg border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-900/60 focus:outline-none text-slate-700 dark:text-slate-350 cursor-pointer"
                aria-label="Filter by dimension column"
              >
                <option value="all">All Dimensions</option>
                {filterOptions.dimensions.map(d => (
                  <option key={d} value={d}>{d}</option>
                ))}
              </select>
            </div>
          </div>
        </div>

        {/* Grouped Visualizations catalog */}
        <div className="space-y-10 text-left">
          {loading ? (
            <div className="space-y-4">
              <div className="h-4 w-36 bg-slate-200 dark:bg-slate-800/80 rounded shimmer mb-4"></div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {[1, 2].map(idx => <ChartCardSkeleton key={idx} />)}
              </div>
            </div>
          ) : Object.keys(groupedCharts).length > 0 ? (
            Object.entries(groupedCharts).map(([groupName, chartList]) => (
              <div key={groupName} className="space-y-4">
                <h3 className="text-[11px] font-black uppercase text-slate-450 dark:text-slate-500 tracking-wider flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-indigo-500/60" />
                  {groupName} ({chartList.length})
                </h3>

                <ErrorBoundary message="An error occurred while compiling the recommendations catalog cards. Please reload the dashboard.">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {chartList.map((c) => {
                      const isExpanded = expandedChartId === c.id;
                      const primaryKpiId = c.required_kpis?.[0];
                      const kpiObject = sessionInfo?.finalKPIs?.find(k => k.id === primaryKpiId);
                      const kpiDisplayName = kpiObject ? kpiObject.display_name : (primaryKpiId || 'N/A');
                      const resolvedDimension = resolveSourceColumn(c.x_axis || c.y_axis, sessionInfo?.mappingData);

                      return (
                        <div 
                          key={c.id}
                          className={`rounded-3xl border border-slate-200 dark:border-slate-855 bg-white dark:bg-[#111217]/20 shadow-sm flex flex-col justify-between overflow-hidden transition-all duration-200 ${
                            isExpanded ? 'border-indigo-500/35 ring-1 ring-indigo-500/10' : 'hover:border-slate-350 dark:hover:border-slate-800'
                          }`}
                        >
                          <div className="p-6 bg-slate-50/50 dark:bg-slate-900/[0.08] border-b border-slate-150 dark:border-slate-850/60 relative flex flex-col justify-center min-h-[140px]">
                            <MiniChartPreview type={c.chart_type} />
                            <div className="absolute bottom-4 left-6 flex items-center gap-2">
                              <span className="px-2 py-0.5 rounded bg-indigo-500/15 border border-indigo-500/20 text-indigo-500 font-mono text-[9px] uppercase font-bold tracking-wider">
                                {c.chart_type}
                              </span>
                            </div>
                          </div>

                          <div className="p-6 space-y-4 flex-1 flex flex-col justify-between">
                            <div className="space-y-2">
                              <div className="flex justify-between items-start gap-4">
                                <h4 className="text-base font-bold text-slate-800 dark:text-slate-100 line-clamp-1">
                                  {c.title}
                                </h4>
                                <button 
                                  onClick={() => toggleExpand(c.id)}
                                  className="text-slate-400 p-1 hover:text-slate-650 dark:hover:text-slate-300 cursor-pointer"
                                  aria-expanded={isExpanded}
                                  aria-label="Toggle details view"
                                >
                                  {isExpanded ? (
                                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 15l7-7 7 7" />
                                    </svg>
                                  ) : (
                                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                                    </svg>
                                  )}
                                </button>
                              </div>
                              
                              <div className="flex flex-wrap items-center gap-x-3 gap-y-1.5 text-[11px] text-slate-550 dark:text-slate-400">
                                <span>KPI: <strong className="font-semibold text-indigo-500 dark:text-indigo-400">{kpiDisplayName}</strong></span>
                                <span className="text-slate-300 dark:text-slate-800">•</span>
                                <span>Dimension: <strong className="font-semibold text-slate-700 dark:text-slate-300">{resolvedDimension || 'N/A'}</strong></span>
                              </div>

                              <p className="text-xs text-slate-500 dark:text-slate-400 mt-2 italic leading-relaxed line-clamp-2">
                                "{c.business_purpose || `Analyzes ${kpiDisplayName} metrics against ${resolvedDimension} segment distributions.`}"
                              </p>
                            </div>

                            {isExpanded && (
                              <div className="pt-4 mt-4 border-t border-slate-150 dark:border-slate-850/60 space-y-3.5 text-xs text-slate-650 dark:text-slate-350 bg-slate-50/[0.15] dark:bg-slate-900/[0.04] p-4 rounded-2xl animate-fade-in">
                                <div className="grid grid-cols-2 gap-4">
                                  <div>
                                    <span className="block text-[9px] uppercase font-bold text-slate-450 dark:text-slate-500 tracking-wider">Metric Context</span>
                                    <span className="block mt-1 font-mono font-bold text-slate-700 dark:text-slate-300">{kpiDisplayName}</span>
                                  </div>
                                  <div>
                                    <span className="block text-[9px] uppercase font-bold text-slate-450 dark:text-slate-500 tracking-wider">Source Column</span>
                                    <span className="block mt-1 font-mono font-bold text-slate-700 dark:text-slate-300">{resolvedDimension || 'N/A'}</span>
                                  </div>
                                  <div>
                                    <span className="block text-[9px] uppercase font-bold text-slate-450 dark:text-slate-500 tracking-wider">Aggregation</span>
                                    <span className="block mt-1 font-mono font-bold text-indigo-500 dark:text-indigo-400 uppercase">{c.aggregation_method || 'DYNAMIC'}</span>
                                  </div>
                                  <div>
                                    <span className="block text-[9px] uppercase font-bold text-slate-450 dark:text-slate-500 tracking-wider">Section Location</span>
                                    <span className="block mt-1 font-mono font-bold text-slate-700 dark:text-slate-300">{c.section || 'General'}</span>
                                  </div>
                                </div>
                              </div>
                            )}

                            <div className="pt-4 border-t border-slate-150 dark:border-slate-850/60 flex items-center justify-between">
                              <button
                                disabled
                                className="inline-flex items-center gap-1 text-[10px] font-bold text-slate-400 cursor-not-allowed opacity-50 select-none"
                              >
                                View Related KPIs
                              </button>
                              <button 
                                onClick={() => navigate(`/analysis/visualizations/${sessionId}/${c.id}`)}
                                className="inline-flex items-center gap-1 text-xs font-bold text-indigo-500 dark:text-indigo-405 hover:gap-2 transition-all cursor-pointer"
                              >
                                Open Visualization &rarr;
                              </button>
                            </div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </ErrorBoundary>
              </div>
            ))
          ) : (
            <EmptyState 
              title="No Visualizations Match Filters"
              description="We couldn't find any recommended visualizations matching your selected filters. Adjust your search or clear checkboxes."
              actionText="Reset Filters"
              onAction={() => {
                setSearchQuery('');
                setSelectedChartType('all');
                setSelectedKpi('all');
                setSelectedDimension('all');
              }}
              iconType="search"
            />
          )}
        </div>
      </main>
    </div>
  );
};

export default ExploreVisualizations;
