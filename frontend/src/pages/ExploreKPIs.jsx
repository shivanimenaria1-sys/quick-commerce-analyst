import React, { useState, useEffect, useMemo } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { apiService } from '../services/api';
import { analysisSessionStorage } from '../services/storageService';
import EmptyState from '../components/EmptyState';

// Shimmer Loader for statistics cards
const StatCardSkeleton = () => (
  <div className="p-5 rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-[#111217]/30 text-left flex flex-col justify-between min-h-[90px]">
    <div className="h-3 w-20 bg-slate-200 dark:bg-slate-800/80 rounded shimmer"></div>
    <div className="h-7 w-12 bg-slate-200 dark:bg-slate-800 rounded shimmer mt-2"></div>
  </div>
);

// Shimmer Loader for KPI Accordion card list
const KPIListSkeleton = () => (
  <div className="space-y-4">
    <div className="h-4 w-36 bg-slate-200 dark:bg-slate-800/80 rounded shimmer mb-4"></div>
    <div className="space-y-3">
      {[1, 2, 3].map(idx => (
        <div key={idx} className="p-5 rounded-2xl border border-slate-200 dark:border-slate-800/60 bg-white dark:bg-[#111217]/25 flex flex-col gap-2">
          <div className="flex justify-between items-start gap-4">
            <div className="h-5 w-48 bg-slate-200 dark:bg-slate-800/80 rounded shimmer"></div>
            <div className="h-4 w-12 bg-slate-200 dark:bg-slate-800/80 rounded shimmer"></div>
          </div>
          <div className="h-3 w-full bg-slate-200 dark:bg-slate-800/50 rounded shimmer mt-1"></div>
          <div className="h-3 w-2/3 bg-slate-200 dark:bg-slate-800/50 rounded shimmer"></div>
        </div>
      ))}
    </div>
  </div>
);

export const ExploreKPIs = () => {
  const { sessionId } = useParams();
  const navigate = useNavigate();
  
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  const [sessionInfo, setSessionInfo] = useState(null);
  const [expandedKpiId, setExpandedKpiId] = useState(null);
  
  const [searchQuery, setSearchQuery] = useState('');
  const [sortBy, setSortBy] = useState('alphabetical'); // 'alphabetical', 'category', 'usage'

  useEffect(() => {
    let active = true;

    const fetchAnalysisData = async () => {
      const cached = analysisSessionStorage.getSessionData(sessionId);
      if (cached) {
        setSessionInfo(cached);
        setLoading(false);
      }

      try {
        const fresh = await apiService.getAnalysis(sessionId);
        if (!active) return;
        
        const sessionPayload = {
          profileData: fresh.dataset_profile,
          mappingData: fresh.confirmed_semantic_mapping,
          domainData: fresh.domain_profile,
          finalKPIs: fresh.selected_kpis || [],
          dashboardPlan: { dashboard: fresh.dashboard_plan }
        };
        
        analysisSessionStorage.saveSessionData(sessionId, sessionPayload);
        setSessionInfo(sessionPayload);
        setError(null);
      } catch (err) {
        console.error("Backend retrieval failed:", err);
        if (!cached) {
          if (active) {
            setError("Analysis session is no longer available. Please upload your dataset again.");
            setTimeout(() => {
              navigate('/upload', { state: { error: "Analysis session is no longer available. Please upload your dataset again." } });
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

  const getBusinessCategory = (kpi) => {
    const plugin = kpi.generator_plugin || '';
    const id = kpi.id || '';
    if (plugin.includes('revenue') || plugin.includes('cost') || id.includes('revenue') || id.includes('cost') || id.includes('profit') || id.includes('margin')) {
      return 'Financial KPIs';
    }
    if (plugin.includes('loyalty') || plugin.includes('customer') || id.includes('customer') || id.includes('loyalty') || id.includes('repeat')) {
      return 'Customer KPIs';
    }
    if (plugin.includes('duration') || id.includes('delivery') || id.includes('time') || id.includes('delay') || id.includes('rider')) {
      return 'Delivery KPIs';
    }
    if (plugin.includes('location') || id.includes('pincode') || id.includes('store') || id.includes('region')) {
      return 'Operational KPIs';
    }
    if (plugin.includes('category') || id.includes('item') || id.includes('product') || id.includes('sales_category')) {
      return 'Inventory KPIs';
    }
    if (plugin.includes('hr') || id.includes('shift') || id.includes('active') || id.includes('utilization')) {
      return 'Operational KPIs';
    }
    return 'General KPIs';
  };

  const getSourceColumns = (kpi, mapping) => {
    if (!kpi.required_semantic_roles || !mapping) return ['N/A'];
    const columnsMap = mapping.columns || mapping;
    const resolved = [];
    kpi.required_semantic_roles.forEach(role => {
      for (const [colName, colData] of Object.entries(columnsMap)) {
        const currRole = typeof colData === 'string' ? colData : colData.semantic_role;
        if (currRole === role) {
          resolved.push(colName);
        }
      }
    });
    return resolved.length ? resolved : kpi.required_semantic_roles;
  };

  const formatFormula = (kpi, mapping) => {
    const formula = kpi.formula;
    if (!formula) return 'N/A';
    if (typeof formula === 'string') return formula;
    
    const operation = formula.operation || 'AGG';
    const fields = formula.fields || [];
    
    const resolvedFields = fields.map(f => {
      if (mapping) {
        const columnsMap = mapping.columns || mapping;
        for (const [colName, colData] of Object.entries(columnsMap)) {
          const currRole = typeof colData === 'string' ? colData : colData.semantic_role;
          if (currRole === f) {
            return colName;
          }
        }
      }
      return f;
    });
    
    return `${operation}(${resolvedFields.join(', ')})`;
  };

  const getChartUsages = (kpiId, charts) => {
    if (!Array.isArray(charts)) return 0;
    return charts.filter(c => Array.isArray(c.required_kpis) && c.required_kpis.includes(kpiId)).length;
  };

  const enrichedKPIs = useMemo(() => {
    if (!sessionInfo || !sessionInfo.finalKPIs) return [];
    const mapping = sessionInfo.mappingData;
    const charts = sessionInfo.dashboardPlan?.dashboard?.charts || [];

    return sessionInfo.finalKPIs.map(kpi => {
      const category = getBusinessCategory(kpi);
      const sourceCols = getSourceColumns(kpi, mapping);
      const formulaStr = formatFormula(kpi, mapping);
      const usageCount = getChartUsages(kpi.id, charts);
      return {
        ...kpi,
        category,
        sourceCols,
        formulaStr,
        usageCount
      };
    });
  }, [sessionInfo]);

  const stats = useMemo(() => {
    if (enrichedKPIs.length === 0) {
      return { total: 0, categories: 0, mostUsed: 'N/A', avgUsages: 0 };
    }
    const categoriesSet = new Set(enrichedKPIs.map(k => k.category));
    
    let maxUsage = -1;
    let mostUsedKpi = 'N/A';
    let totalUsages = 0;
    
    enrichedKPIs.forEach(k => {
      totalUsages += k.usageCount;
      if (k.usageCount > maxUsage) {
        maxUsage = k.usageCount;
        mostUsedKpi = k.display_name;
      }
    });

    return {
      total: enrichedKPIs.length,
      categories: categoriesSet.size,
      mostUsed: mostUsedKpi,
      avgUsages: (totalUsages / enrichedKPIs.length).toFixed(1)
    };
  }, [enrichedKPIs]);

  const filteredAndSortedKPIs = useMemo(() => {
    let result = [...enrichedKPIs];

    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      result = result.filter(k => 
        k.display_name?.toLowerCase().includes(q) ||
        k.category?.toLowerCase().includes(q) ||
        (k.reason || k.explanation)?.toLowerCase().includes(q) ||
        k.formulaStr?.toLowerCase().includes(q)
      );
    }

    if (sortBy === 'alphabetical') {
      result.sort((a, b) => (a.display_name || '').localeCompare(b.display_name || ''));
    } else if (sortBy === 'category') {
      result.sort((a, b) => a.category.localeCompare(b.category));
    } else if (sortBy === 'usage') {
      result.sort((a, b) => b.usageCount - a.usageCount);
    }

    return result;
  }, [enrichedKPIs, searchQuery, sortBy]);

  const groupedKPIs = useMemo(() => {
    const groups = {};
    filteredAndSortedKPIs.forEach(kpi => {
      if (!groups[kpi.category]) {
        groups[kpi.category] = [];
      }
      groups[kpi.category].push(kpi);
    });
    return groups;
  }, [filteredAndSortedKPIs]);

  const toggleExpand = (id) => {
    setExpandedKpiId(expandedKpiId === id ? null : id);
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
            <span className="text-sm font-bold tracking-tight text-slate-700 dark:text-slate-200">KPI Explorer</span>
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
          <span className="text-slate-700 dark:text-slate-350 font-bold">KPI Explorer</span>
        </div>

        {/* Header Title Section */}
        <div className="text-left space-y-2">
          <h1 className="text-2xl sm:text-3xl font-black tracking-tight text-slate-900 dark:text-slate-100">
            Selected Key Performance Indicators
          </h1>
          <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-slate-500 dark:text-slate-400">
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
                <span className="block text-[10px] uppercase font-bold text-slate-450 tracking-wider">Total Active KPIs</span>
                <span className="text-2xl font-black text-slate-800 dark:text-slate-100 mt-2">{stats.total}</span>
              </div>
              <div className="p-5 rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-[#111217]/30 text-left flex flex-col justify-between min-h-[90px]">
                <span className="block text-[10px] uppercase font-bold text-slate-450 tracking-wider">Business Categories</span>
                <span className="text-2xl font-black text-slate-800 dark:text-slate-100 mt-2">{stats.categories}</span>
              </div>
              <div className="p-5 rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-[#111217]/30 text-left flex flex-col justify-between min-h-[90px]">
                <span className="block text-[10px] uppercase font-bold text-slate-450 tracking-wider">Most Used KPI</span>
                <span className="text-xs font-bold text-indigo-500 dark:text-indigo-400 mt-2 truncate" title={stats.mostUsed}>
                  {stats.mostUsed}
                </span>
              </div>
              <div className="p-5 rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-[#111217]/30 text-left flex flex-col justify-between min-h-[90px]">
                <span className="block text-[10px] uppercase font-bold text-slate-450 tracking-wider">Avg Visualizations</span>
                <span className="text-2xl font-black text-slate-800 dark:text-slate-100 mt-2">{stats.avgUsages} <span className="text-[10px] text-slate-400 font-normal">/ KPI</span></span>
              </div>
            </>
          )}
        </div>

        {/* Filter and Sort Toolbar */}
        <div className="flex flex-col sm:flex-row gap-4 justify-between items-center bg-white dark:bg-[#111217]/20 border border-slate-200 dark:border-slate-800 p-4 rounded-3xl backdrop-blur-sm">
          {/* Search Box */}
          <div className="w-full sm:max-w-md relative">
            <input 
              type="text" 
              placeholder="Search by name, description, category, formula..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2 text-xs rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-900/60 focus:outline-none focus:border-indigo-500 text-slate-800 dark:text-slate-155 transition-colors"
              aria-label="Search KPIs"
            />
            <svg className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          </div>

          {/* Sort By Dropdown */}
          <div className="w-full sm:w-auto flex items-center justify-end gap-2 shrink-0">
            <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Sort:</span>
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              className="px-3 py-2 text-xs rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-900/60 focus:outline-none focus:border-indigo-500 text-slate-700 dark:text-slate-300 transition-colors cursor-pointer animate-fade-in"
              aria-label="Sort KPIs by"
            >
              <option value="alphabetical">Alphabetical</option>
              <option value="category">Category</option>
              <option value="usage">Visualization Usages</option>
            </select>
          </div>
        </div>

        {/* Grouped Category Sections */}
        <div className="space-y-10 text-left">
          {loading ? (
            <KPIListSkeleton />
          ) : Object.keys(groupedKPIs).length > 0 ? (
            Object.entries(groupedKPIs).map(([category, kpis]) => (
              <div key={category} className="space-y-4">
                <h3 className="text-[11px] font-black uppercase text-slate-450 dark:text-slate-500 tracking-wider flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-indigo-500/60" />
                  {category} ({kpis.length})
                </h3>
                
                <div className="space-y-3">
                  {kpis.map((kpi) => {
                    const isExpanded = expandedKpiId === kpi.id;
                    return (
                      <div 
                        key={kpi.id}
                        className={`rounded-2xl border border-slate-200 dark:border-slate-850 bg-white dark:bg-[#111217]/20 shadow-sm transition-all duration-200 ${
                          isExpanded 
                            ? 'border-indigo-500/35 ring-1 ring-indigo-500/10' 
                            : 'hover:border-slate-350 dark:hover:border-slate-800'
                        }`}
                      >
                        <div 
                          onClick={() => toggleExpand(kpi.id)}
                          className="p-5 flex items-start sm:items-center justify-between gap-4 cursor-pointer select-none"
                          role="button"
                          aria-expanded={isExpanded}
                        >
                          <div className="space-y-1.5 flex-1 min-w-0">
                            <div className="flex flex-wrap items-center gap-x-2 gap-y-1">
                              <h4 className="text-sm font-bold text-slate-800 dark:text-slate-100 truncate">
                                {kpi.display_name}
                              </h4>
                              <span className="text-[9px] px-1.5 rounded-md font-mono bg-slate-100 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-slate-550 dark:text-slate-400 font-bold uppercase tracking-wider">
                                {kpi.aggregation}
                              </span>
                            </div>
                            <p className="text-xs text-slate-500 dark:text-slate-400 line-clamp-1">
                              {kpi.explanation || kpi.reason}
                            </p>
                          </div>
                          
                          <div className="flex items-center gap-4 shrink-0 mt-1 sm:mt-0">
                            {kpi.usageCount > 0 && (
                              <span className="px-2 py-0.5 rounded-full text-[9px] font-bold font-mono bg-emerald-500/10 text-emerald-500 border border-emerald-500/20">
                                {kpi.usageCount} {kpi.usageCount === 1 ? 'chart' : 'charts'}
                              </span>
                            )}
                            <span className="text-slate-400 text-xs">
                              {isExpanded ? (
                                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 15l7-7 7 7" />
                                </svg>
                              ) : (
                                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                                </svg>
                              )}
                            </span>
                          </div>
                        </div>

                        {isExpanded && (
                          <div className="px-5 pb-5 pt-3 border-t border-slate-100 dark:border-slate-850/60 bg-slate-50/[0.15] dark:bg-slate-900/[0.04] rounded-b-2xl space-y-5 text-left text-xs animate-fade-in">
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                              <div className="space-y-3.5">
                                <div>
                                  <span className="block text-[9px] uppercase font-bold text-slate-400 tracking-wider">Formula Specification</span>
                                  <code className="block mt-1 font-mono text-[11px] p-2 bg-slate-100 dark:bg-slate-950/80 rounded-lg border border-slate-205 dark:border-slate-850 text-indigo-500 dark:text-indigo-400 font-bold overflow-x-auto whitespace-nowrap">
                                    {kpi.formulaStr}
                                  </code>
                                </div>
                                <div>
                                  <span className="block text-[9px] uppercase font-bold text-slate-400 tracking-wider">Source Columns Resolved</span>
                                  <div className="flex flex-wrap gap-1.5 mt-1.5">
                                    {kpi.sourceCols.map((col, cIdx) => (
                                      <span key={cIdx} className="px-2 py-0.5 rounded font-mono text-[10px] bg-slate-150 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-slate-700 dark:text-slate-300">
                                        {col}
                                      </span>
                                    ))}
                                  </div>
                                </div>
                              </div>

                              <div className="space-y-3.5">
                                <div>
                                  <span className="block text-[9px] uppercase font-bold text-slate-400 tracking-wider">Business Meaning & Objective</span>
                                  <p className="mt-1 text-slate-600 dark:text-slate-350 leading-relaxed italic">
                                    "{kpi.explanation || kpi.reason}"
                                  </p>
                                </div>
                                <div className="grid grid-cols-2 gap-4">
                                  <div>
                                    <span className="block text-[9px] uppercase font-bold text-slate-400 tracking-wider">Method</span>
                                    <span className="block mt-1 font-mono font-bold text-slate-700 dark:text-slate-300">
                                      {kpi.aggregation}
                                    </span>
                                  </div>
                                  <div>
                                    <span className="block text-[9px] uppercase font-bold text-slate-400 tracking-wider">Chart Usages</span>
                                    <span className="block mt-1 font-mono font-bold text-slate-700 dark:text-slate-300">
                                      {kpi.usageCount} recommended
                                    </span>
                                  </div>
                                </div>
                              </div>
                            </div>

                            <div className="pt-3 border-t border-slate-100 dark:border-slate-850/60 flex items-center justify-between">
                              <span className="text-[10px] text-slate-450 dark:text-slate-500">
                                KPI ID: <span className="font-mono">{kpi.id}</span>
                              </span>
                              <button 
                                disabled
                                className="inline-flex items-center gap-1 text-[10px] font-bold text-slate-400 cursor-not-allowed opacity-50 select-none"
                              >
                                View Related Visualizations &rarr;
                              </button>
                            </div>
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            ))
          ) : (
            <EmptyState 
              title="No KPIs Match Your Query"
              description="We couldn't find any indicators matching your search criteria. Check your spelling or try another keyword."
              actionText="Reset Search"
              onAction={() => setSearchQuery('')}
              iconType="search"
            />
          )}
        </div>
      </main>
    </div>
  );
};

export default ExploreKPIs;
