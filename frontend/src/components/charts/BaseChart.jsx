import React from 'react';

// Format large numbers nicely (e.g. 1.26K, 1.84M, 1.52B)
export const formatNumber = (num) => {
  if (num === null || num === undefined) return '';
  const n = Number(num);
  if (isNaN(n)) return String(num);
  const absN = Math.abs(n);
  const sign = n < 0 ? '-' : '';
  
  if (absN >= 1e9) {
    const val = absN / 1e9;
    return sign + (val % 1 === 0 ? val.toFixed(0) : val.toFixed(2)) + 'B';
  }
  if (absN >= 1e6) {
    const val = absN / 1e6;
    return sign + (val % 1 === 0 ? val.toFixed(0) : val.toFixed(2)) + 'M';
  }
  if (absN >= 1e3) {
    const val = absN / 1e3;
    return sign + (val % 1 === 0 ? val.toFixed(0) : val.toFixed(2)) + 'K';
  }
  return sign + (absN % 1 === 0 ? absN.toFixed(0) : absN.toFixed(2));
};

// Premium shared custom tooltip
export const CustomTooltip = ({ active, payload, label, isPie = false, total = 1 }) => {
  if (active && payload && payload.length) {
    const activeItem = payload[0];
    const headerLabel = label || activeItem.payload[activeItem.name] || '';
    
    return (
      <div className="bg-slate-950/95 border border-slate-800 p-3 rounded-xl shadow-2xl text-left text-xs font-sans text-slate-200 backdrop-blur-md">
        {headerLabel && (
          <p className="font-bold text-slate-400 mb-1.5 uppercase text-[9px] tracking-wider">
            {String(headerLabel)}
          </p>
        )}
        <div className="space-y-1.5">
          {payload.map((item, idx) => {
            const val = Number(item.value);
            const displayVal = isNaN(val) ? item.value : val.toLocaleString();
            
            let pctText = '';
            if (isPie && !isNaN(val) && total > 0) {
              const pct = Math.round((val / total) * 100);
              pctText = ` (${pct}%)`;
            }
            
            return (
              <div key={idx} className="flex items-center gap-3">
                <span 
                  className="w-2 h-2 rounded-full shrink-0" 
                  style={{ backgroundColor: item.color || item.payload.fill || '#6366f1' }} 
                />
                <span className="text-slate-405 dark:text-slate-400 font-medium">
                  {item.name}:
                </span>
                <span className="font-mono font-bold text-indigo-400">
                  {displayVal}{pctText}
                </span>
              </div>
            );
          })}
        </div>
      </div>
    );
  }
  return null;
};

export const BaseChart = ({ visualization, hasData, children }) => {
  const { title, subtitle, chart_type } = visualization || {};

  return (
    <div className="rounded-2xl border border-slate-250 dark:border-slate-800 bg-white dark:bg-[#12131a]/40 p-5 backdrop-blur-sm shadow-sm transition-all duration-205 hover:border-slate-350 dark:hover:border-slate-700 flex flex-col h-full min-h-[350px] w-full text-slate-850 dark:text-slate-200">
      {/* Title & Header */}
      <div className="mb-4 text-left">
        {title && (
          <h4 className="text-sm font-bold tracking-tight leading-snug">
            {title}
          </h4>
        )}
        {subtitle && (
          <p className="text-[11px] text-slate-500 dark:text-slate-450 mt-0.5">
            {subtitle}
          </p>
        )}
      </div>

      {/* Chart Canvas or Empty State */}
      <div className="flex-1 w-full relative min-h-[260px]">
        {hasData ? (
          <div className="absolute inset-0 w-full h-full">
            {children}
          </div>
        ) : (
          <div className="absolute inset-0 w-full h-full flex flex-col items-center justify-center text-center p-6 space-y-2 select-none">
            {/* Clean minimalist chart placeholder icon */}
            <svg
              className="w-10 h-10 text-slate-300 dark:text-slate-705 animate-pulse"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1.5}
                d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
              />
            </svg>
            <span className="text-xs font-semibold text-slate-400 dark:text-slate-500">
              No data available
            </span>
            <p className="text-[10px] text-slate-450 dark:text-slate-600 max-w-[200px]">
              Waiting for backend to compute real aggregated datasets for {chart_type || 'chart'}.
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default BaseChart;
