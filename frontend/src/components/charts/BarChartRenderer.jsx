import React from 'react';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, LabelList } from 'recharts';
import { BaseChart, CustomTooltip, formatNumber } from './BaseChart';

export const BarChartRenderer = ({ visualization }) => {
  const { chart_data, x_axis, y_axis } = visualization || {};
  const hasData = Array.isArray(chart_data) && chart_data.length > 0;

  // Measure the longest label length
  const longestLabelLength = hasData 
    ? Math.max(...chart_data.map(d => String(d[x_axis] || '').length), 0)
    : 0;

  const shouldRotate = longestLabelLength > 8;
  const rotateAngle = shouldRotate ? -35 : 0;
  const textAnchor = shouldRotate ? "end" : "middle";
  const bottomMargin = shouldRotate ? Math.min(100, longestLabelLength * 5 + 10) : 10;

  // If there are many categories (> 10), enable scrollable horizontal view
  const isScrollable = hasData && chart_data.length > 10;
  const innerWidth = isScrollable ? `${chart_data.length * 60}px` : "100%";

  // Only render value labels above bars when there is sufficient space (12 or fewer items)
  const showLabels = hasData && chart_data.length <= 12;

  return (
    <BaseChart visualization={visualization} hasData={hasData}>
      {hasData && (
        <div className="w-full h-full overflow-x-auto scrollbar-thin scrollbar-thumb-slate-200 dark:scrollbar-thumb-slate-800 scrollbar-track-transparent">
          <div style={{ width: innerWidth, height: "100%", minHeight: "260px" }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chart_data} margin={{ top: 20, right: 10, left: -20, bottom: bottomMargin }}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(148, 163, 184, 0.1)" />
                <XAxis 
                  dataKey={x_axis} 
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
                <Tooltip 
                  content={<CustomTooltip />}
                  cursor={{ fill: 'rgba(255, 255, 255, 0.05)' }}
                />
                <Bar 
                  dataKey={y_axis} 
                  fill="#a855f7" 
                  radius={[4, 4, 0, 0]}
                  name={y_axis.replace(/_/g, ' ').toUpperCase()}
                >
                  {showLabels && (
                    <LabelList 
                      dataKey={y_axis} 
                      position="top" 
                      formatter={formatNumber} 
                      fill="currentColor"
                      className="fill-slate-500 dark:fill-slate-400 text-[9px] font-mono"
                    />
                  )}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}
    </BaseChart>
  );
};

export default BarChartRenderer;
