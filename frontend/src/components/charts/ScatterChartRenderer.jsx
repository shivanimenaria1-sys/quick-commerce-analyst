import React from 'react';
import { ResponsiveContainer, ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip } from 'recharts';
import { BaseChart, CustomTooltip, formatNumber } from './BaseChart';

export const ScatterChartRenderer = ({ visualization }) => {
  const { chart_data, x_axis, y_axis } = visualization || {};
  const hasData = Array.isArray(chart_data) && chart_data.length > 0;

  return (
    <BaseChart visualization={visualization} hasData={hasData}>
      {hasData && (
        <ResponsiveContainer width="100%" height="100%">
          <ScatterChart margin={{ top: 10, right: 10, left: -20, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(148, 163, 184, 0.1)" />
            <XAxis 
              type="number" 
              dataKey={x_axis} 
              name={x_axis} 
              stroke="rgba(148, 163, 184, 0.5)" 
              fontSize={10}
              tickLine={false}
              tickFormatter={formatNumber}
            />
            <YAxis 
              type="number" 
              dataKey={y_axis} 
              name={y_axis} 
              stroke="rgba(148, 163, 184, 0.5)" 
              fontSize={10}
              tickLine={false}
              tickFormatter={formatNumber}
            />
            <Tooltip 
              cursor={{ strokeDasharray: '3 3' }}
              content={<CustomTooltip />}
            />
            <Scatter 
              name={`${x_axis} vs ${y_axis}`} 
              data={chart_data} 
              fill="#ec4899" 
            />
          </ScatterChart>
        </ResponsiveContainer>
      )}
    </BaseChart>
  );
};

export default ScatterChartRenderer;
