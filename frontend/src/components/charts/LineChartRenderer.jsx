import React from 'react';
import { ResponsiveContainer, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip } from 'recharts';
import { BaseChart, CustomTooltip, formatNumber } from './BaseChart';

export const LineChartRenderer = ({ visualization }) => {
  const { chart_data, x_axis, y_axis } = visualization || {};
  const hasData = Array.isArray(chart_data) && chart_data.length > 0;

  return (
    <BaseChart visualization={visualization} hasData={hasData}>
      {hasData && (
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={chart_data} margin={{ top: 10, right: 10, left: -20, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(148, 163, 184, 0.1)" />
            <XAxis 
              dataKey={x_axis} 
              stroke="rgba(148, 163, 184, 0.5)" 
              fontSize={10}
              tickLine={false} 
            />
            <YAxis 
              stroke="rgba(148, 163, 184, 0.5)" 
              fontSize={10}
              tickLine={false}
              tickFormatter={formatNumber}
            />
            <Tooltip content={<CustomTooltip />} />
            <Line 
              type="monotone" 
              dataKey={y_axis} 
              stroke="#6366f1" 
              strokeWidth={2}
              dot={{ r: 3, strokeWidth: 1 }}
              activeDot={{ r: 5 }}
              name={y_axis.replace(/_/g, ' ').toUpperCase()}
            />
          </LineChart>
        </ResponsiveContainer>
      )}
    </BaseChart>
  );
};

export default LineChartRenderer;
