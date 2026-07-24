import React from 'react';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip } from 'recharts';
import { BaseChart, CustomTooltip, formatNumber } from './BaseChart';

export const HistogramRenderer = ({ visualization }) => {
  const { chart_data } = visualization || {};
  
  // Log the raw histogram data to trace the full flow
  console.log("Histogram Data", chart_data);

  // Normalize variable formats:
  // Format A: bin & count
  // Format B: label & frequency
  // Format C: name & value
  // Backend default: name & count
  const normalizeData = (data) => {
    if (!Array.isArray(data) || data.length === 0) return [];
    
    return data.map(item => {
      // 1. Detect label key (e.g., 'label', 'bin', 'name')
      let labelKey = ['label', 'bin', 'name'].find(k => k in item);
      if (!labelKey) {
        labelKey = Object.keys(item)[0] || 'label';
      }
      
      // 2. Detect value key (e.g., 'value', 'count', 'frequency')
      let valueKey = ['value', 'count', 'frequency'].find(k => k !== labelKey && k in item);
      if (!valueKey) {
        valueKey = Object.keys(item).find(k => k !== labelKey) || 'value';
      }
      
      const rawLabel = item[labelKey];
      const rawValue = item[valueKey];
      
      const label = rawLabel !== undefined && rawLabel !== null ? String(rawLabel) : 'Unknown';
      const value = rawValue !== undefined && rawValue !== null && !isNaN(Number(rawValue)) 
        ? Number(rawValue) 
        : 0; // Preserve 0 value for zero-frequency bins
      
      return {
        label,
        value
      };
    });
  };

  const normalizedData = normalizeData(chart_data);
  const hasData = normalizedData.length > 0;

  const longestLabelLength = hasData 
    ? Math.max(...normalizedData.map(d => String(d.label || '').length), 0)
    : 0;

  const shouldRotate = longestLabelLength > 6;
  const rotateAngle = shouldRotate ? -35 : 0;
  const textAnchor = shouldRotate ? "end" : "middle";
  const bottomMargin = shouldRotate ? Math.min(100, longestLabelLength * 5 + 10) : 10;

  return (
    <BaseChart visualization={visualization} hasData={hasData}>
      {hasData ? (
        <ResponsiveContainer width="100%" height="100%">
          <BarChart 
            data={normalizedData} 
            margin={{ top: 15, right: 10, left: -20, bottom: bottomMargin }} 
            barCategoryGap={2}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(148, 163, 184, 0.1)" />
            <XAxis 
              dataKey="label" 
              stroke="rgba(148, 163, 184, 0.5)" 
              fontSize={10}
              tickLine={false}
              interval={0}
              angle={rotateAngle}
              textAnchor={textAnchor}
              dy={shouldRotate ? 5 : 0}
            />
            <YAxis 
              stroke="rgba(148, 163, 184, 0.5)" 
              fontSize={10}
              tickLine={false}
              tickFormatter={formatNumber}
            />
            <Tooltip content={<CustomTooltip />} />
            <Bar 
              dataKey="value" 
              fill="#06b6d4" 
              name="Frequency"
              radius={[2, 2, 0, 0]}
              className="hover:fill-cyan-400 transition-all duration-150 cursor-pointer"
            />
          </BarChart>
        </ResponsiveContainer>
      ) : (
        <div className="flex flex-col items-center justify-center text-center p-6 space-y-2 select-none">
          <span className="text-xs font-semibold text-slate-400 dark:text-slate-500">
            No histogram data available
          </span>
        </div>
      )}
    </BaseChart>
  );
};

export default HistogramRenderer;
