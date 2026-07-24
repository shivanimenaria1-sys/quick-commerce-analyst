import React from 'react';
import { ResponsiveContainer, PieChart, Pie, Cell, Tooltip } from 'recharts';
import { BaseChart, CustomTooltip, formatNumber } from './BaseChart';

const COLORS = ['#6366f1', '#a855f7', '#ec4899', '#f43f5e', '#eab308', '#06b6d4', '#10b981'];

export const PieChartRenderer = ({ visualization }) => {
  const { chart_data, x_axis, y_axis } = visualization || {};
  const hasData = Array.isArray(chart_data) && chart_data.length > 0;

  // Calculate sum of all values to compute percentages
  const total = hasData 
    ? chart_data.reduce((sum, item) => sum + Number(item[y_axis] || 0), 0)
    : 1;

  // Custom label renderer to draw slice percentages directly on donut slices (only if slice >= 5%)
  const renderCustomizedLabel = ({ cx, cy, midAngle, innerRadius, outerRadius, percent }) => {
    if (percent < 0.05) return null;
    
    const RADIAN = Math.PI / 180;
    const radius = innerRadius + (outerRadius - innerRadius) * 0.5;
    const x = cx + radius * Math.cos(-midAngle * RADIAN);
    const y = cy + radius * Math.sin(-midAngle * RADIAN);

    return (
      <text 
        x={x} 
        y={y} 
        fill="white" 
        textAnchor="middle" 
        dominantBaseline="central" 
        className="text-[10px] font-mono font-bold fill-white"
      >
        {`${(percent * 100).toFixed(0)}%`}
      </text>
    );
  };

  return (
    <BaseChart visualization={visualization} hasData={hasData}>
      {hasData && (
        <div className="w-full h-full flex flex-col lg:flex-row items-center justify-center gap-6 lg:gap-8">
          {/* Donut Chart Container */}
          <div className="w-full max-w-[200px] h-[200px] shrink-0">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={chart_data}
                  cx="50%"
                  cy="50%"
                  innerRadius={55}
                  outerRadius={80}
                  paddingAngle={3}
                  dataKey={y_axis}
                  nameKey={x_axis}
                  labelLine={false}
                  label={renderCustomizedLabel}
                >
                  {chart_data.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip content={<CustomTooltip isPie={true} total={total} />} />
              </PieChart>
            </ResponsiveContainer>
          </div>

          {/* Custom Responsive Legend Column */}
          <div className="flex-1 w-full max-h-[180px] overflow-y-auto pr-1 space-y-1.5 scrollbar-thin scrollbar-thumb-slate-200 dark:scrollbar-thumb-slate-800 scrollbar-track-transparent">
            {chart_data.map((item, idx) => {
              const val = Number(item[y_axis] || 0);
              const pct = Math.round((val / total) * 100);
              const markerColor = COLORS[idx % COLORS.length];

              return (
                <div 
                  key={idx} 
                  className="flex items-center justify-between text-xs py-1.5 px-3 hover:bg-slate-100/5 dark:hover:bg-white/5 rounded-xl transition-all duration-150 border border-transparent hover:border-slate-200/5"
                >
                  <div className="flex items-center truncate mr-3">
                    <span 
                      className="w-2.5 h-2.5 rounded-full shrink-0 mr-2 shadow-sm" 
                      style={{ backgroundColor: markerColor }} 
                    />
                    <span className="truncate font-semibold text-slate-700 dark:text-slate-350">
                      {item[x_axis]}
                    </span>
                  </div>
                  <div className="font-mono text-slate-500 dark:text-slate-450 font-bold shrink-0 text-[11px]">
                    {formatNumber(val)} 
                    <span className="text-[10px] text-slate-450 dark:text-slate-500 font-medium ml-1">
                      ({pct}%)
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </BaseChart>
  );
};

export default PieChartRenderer;
