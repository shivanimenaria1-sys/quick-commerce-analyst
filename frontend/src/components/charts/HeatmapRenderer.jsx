import React from 'react';
import { BaseChart } from './BaseChart';

export const HeatmapRenderer = ({ visualization }) => {
  const { chart_data, dimensions } = visualization || {};

  // Resolve dimensions/features to show in the heatmap
  const columns = dimensions || (chart_data ? Object.keys(chart_data) : []);
  const hasData = chart_data && typeof chart_data === 'object' && columns.length > 0;

  // Get color for correlation value between -1 and +1
  const getCellColor = (val) => {
    if (val === undefined || val === null) return 'rgba(148, 163, 184, 0.1)';
    // Scale color: negative = red tones, positive = indigo tones
    if (val > 0) {
      return `rgba(99, 102, 241, ${val})`; // Indigo tint
    } else {
      return `rgba(244, 63, 94, ${Math.abs(val)})`; // Rose tint
    }
  };

  const renderHeatmap = () => {
    return (
      <div className="w-full h-full flex flex-col justify-center p-2 overflow-x-auto text-slate-800 dark:text-slate-200">
        <div className="min-w-[280px] max-w-[450px] mx-auto w-full">
          <div className="grid gap-1" style={{ gridTemplateColumns: `repeat(${columns.length + 1}, minmax(0, 1fr))` }}>
            {/* Corner header */}
            <div className="p-1"></div>
            {/* Column labels */}
            {columns.map((col) => (
              <div key={col} className="p-1 text-[9px] font-bold text-slate-500 dark:text-slate-400 truncate uppercase tracking-wider text-center flex items-center justify-center h-8" title={col}>
                <span className="truncate">{col.replace(/_like|_kpi/g, '').substring(0, 8)}</span>
              </div>
            ))}

            {/* Matrix rows */}
            {columns.map((rowCol) => (
              <React.Fragment key={rowCol}>
                {/* Row label */}
                <div className="p-1 text-[9px] font-bold text-slate-500 dark:text-slate-400 truncate uppercase tracking-wider flex items-center pr-2 h-8" title={rowCol}>
                  <span className="truncate">{rowCol.replace(/_like|_kpi/g, '').substring(0, 8)}</span>
                </div>
                {/* Cells */}
                {columns.map((colCol) => {
                  const val = chart_data[rowCol]?.[colCol] ?? chart_data[colCol]?.[rowCol] ?? (rowCol === colCol ? 1.0 : 0.0);
                  return (
                    <div 
                      key={colCol} 
                      className="aspect-square rounded flex items-center justify-center text-[10px] font-mono font-bold text-white shadow-sm cursor-pointer transition-transform hover:scale-105"
                      style={{ backgroundColor: getCellColor(val) }}
                      title={`${rowCol} vs ${colCol}: ${val.toFixed(2)}`}
                    >
                      {val.toFixed(1)}
                    </div>
                  );
                })}
              </React.Fragment>
            ))}
          </div>
          {/* Legend */}
          <div className="flex justify-between items-center mt-4 px-2 text-[8px] uppercase tracking-wider font-bold text-slate-450 dark:text-slate-500">
            <span className="flex items-center gap-1"><span className="w-2.5 h-2.5 rounded bg-rose-500 inline-block"></span> Neg (-1.0)</span>
            <span>No Correlation (0.0)</span>
            <span className="flex items-center gap-1"><span className="w-2.5 h-2.5 rounded bg-indigo-500 inline-block"></span> Pos (+1.0)</span>
          </div>
        </div>
      </div>
    );
  };

  return (
    <BaseChart visualization={visualization} hasData={hasData}>
      {hasData && renderHeatmap()}
    </BaseChart>
  );
};

export default HeatmapRenderer;
