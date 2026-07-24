import React from 'react';
import { BaseChart, formatNumber } from './BaseChart';

export const BoxPlotRenderer = ({ visualization }) => {
  const { chart_data } = visualization || {};

  // Check if chart_data has the required stats
  let stats = null;
  if (chart_data) {
    if (Array.isArray(chart_data) && chart_data.length > 0) {
      stats = chart_data[0];
    } else if (typeof chart_data === 'object' && chart_data.min !== undefined) {
      stats = chart_data;
    }
  }

  const hasData = stats && 
    stats.min !== undefined && 
    stats.max !== undefined && 
    stats.median !== undefined && 
    stats.q1 !== undefined && 
    stats.q3 !== undefined;

  const renderBoxPlot = () => {
    const { min, max, median, q1, q3 } = stats;
    const range = max - min || 1;
    const iqr = q3 - q1;

    // Convert values to percentages for the SVG representation (horizontal scale from 10% to 90%)
    const getPct = (val) => {
      return ((val - min) / range) * 80 + 10;
    };

    const xMin = getPct(min);
    const xQ1 = getPct(q1);
    const xMedian = getPct(median);
    const xQ3 = getPct(q3);
    const xMax = getPct(max);

    return (
      <div className="w-full flex flex-col justify-between items-center p-2">
        {/* Centered Box Plot SVG */}
        <div className="w-full flex justify-center items-center py-6">
          <svg className="w-full max-w-[380px] h-20 overflow-visible" viewBox="0 0 100 100" preserveAspectRatio="none">
            {/* Whiskers line */}
            <line 
              x1={`${xMin}%`} 
              y1="50" 
              x2={`${xMax}%`} 
              y2="50" 
              stroke="#94a3b8" 
              strokeWidth="1.5"
              strokeDasharray="4 2"
            />
            
            {/* Min whisker cap */}
            <line 
              x1={`${xMin}%`} 
              y1="35" 
              x2={`${xMin}%`} 
              y2="65" 
              stroke="#94a3b8" 
              strokeWidth="2"
            />

            {/* Max whisker cap */}
            <line 
              x1={`${xMax}%`} 
              y1="35" 
              x2={`${xMax}%`} 
              y2="65" 
              stroke="#94a3b8" 
              strokeWidth="2"
            />

            {/* Interquartile Range (IQR) Box */}
            <rect 
              x={`${xQ1}%`} 
              y="25" 
              width={`${xQ3 - xQ1}%`} 
              height="50" 
              fill="#10b981" 
              fillOpacity="0.2"
              stroke="#10b981" 
              strokeWidth="1.5"
              rx="2"
            />

            {/* Median line */}
            <line 
              x1={`${xMedian}%`} 
              y1="25" 
              x2={`${xMedian}%`} 
              y2="75" 
              stroke="#10b981" 
              strokeWidth="2.5"
            />
          </svg>
        </div>

        {/* Structured Responsive Grid of Statistics Boxes */}
        <div className="w-full grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-2.5 mt-6 border-t border-slate-100 dark:border-slate-800 pt-5">
          {[
            { label: 'Minimum', value: min, style: 'text-slate-500 dark:text-slate-400' },
            { label: 'Q1', value: q1, style: 'text-indigo-400' },
            { label: 'Median', value: median, style: 'text-emerald-500 font-bold dark:text-emerald-400' },
            { label: 'Q3', value: q3, style: 'text-indigo-400' },
            { label: 'Maximum', value: max, style: 'text-slate-500 dark:text-slate-400' },
            { label: 'IQR', value: iqr, style: 'text-purple-400' }
          ].map((item, idx) => (
            <div 
              key={idx} 
              className="p-3.5 rounded-xl bg-slate-50 dark:bg-slate-900/30 border border-slate-100 dark:border-slate-800 hover:border-slate-300 dark:hover:border-slate-700 transition-all duration-150 text-center flex flex-col justify-between min-h-[64px]"
            >
              <span className="block text-[9px] uppercase font-bold text-slate-400 tracking-wider">
                {item.label}
              </span>
              <span className={`block text-xs font-mono font-bold mt-1 ${item.style}`}>
                {formatNumber(item.value)}
              </span>
            </div>
          ))}
        </div>
      </div>
    );
  };

  return (
    <BaseChart visualization={visualization} hasData={hasData}>
      {hasData ? (
        renderBoxPlot()
      ) : (
        <div className="flex flex-col items-center justify-center text-center p-6 space-y-2 select-none">
          <span className="text-xs font-semibold text-slate-400 dark:text-slate-500">
            No statistics available
          </span>
        </div>
      )}
    </BaseChart>
  );
};

export default BoxPlotRenderer;
