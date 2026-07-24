import React from 'react';
import { LineChartRenderer } from './LineChartRenderer';
import { BarChartRenderer } from './BarChartRenderer';
import { PieChartRenderer } from './PieChartRenderer';
import { ScatterChartRenderer } from './ScatterChartRenderer';
import { HistogramRenderer } from './HistogramRenderer';
import { BoxPlotRenderer } from './BoxPlotRenderer';
import { HeatmapRenderer } from './HeatmapRenderer';

const RENDERER_REGISTRY = {
  line: LineChartRenderer,
  bar: BarChartRenderer,
  pie: PieChartRenderer,
  scatter: ScatterChartRenderer,
  histogram: HistogramRenderer,
  boxplot: BoxPlotRenderer,
  heatmap: HeatmapRenderer,
  treemap: BarChartRenderer, // Fallback high cardinality category to bar chart
};

export const ChartRenderer = ({ visualization }) => {
  if (!visualization) return null;

  // Normalize incoming fields
  const chart_type = (visualization.chart_type || visualization.chartType || '').toLowerCase();
  
  // Extract title and subtitle
  let title = visualization.title || visualization.display_label || '';
  if (!title && visualization.reason) {
    title = visualization.reason.split(':')[0]; // Use prefix of reason
  }
  if (!title) {
    title = `${chart_type.charAt(0).toUpperCase() + chart_type.slice(1)} Chart`;
  }

  const subtitle = visualization.subtitle || 
    (visualization.reason && visualization.reason.includes(':') 
      ? visualization.reason.split(':').slice(1).join(':').trim() 
      : visualization.reason) || '';

  // Extract axes with fallbacks for dimensions/required_kpis
  const x_axis = visualization.x_axis || visualization.dimensions?.[0] || '';
  let y_axis = visualization.y_axis;
  if (!y_axis) {
    if (visualization.required_kpis && visualization.required_kpis.length > 0) {
      y_axis = visualization.required_kpis[0];
    } else if (visualization.dimensions && visualization.dimensions.length > 1) {
      y_axis = visualization.dimensions[1];
    }
  }

  const chart_data = visualization.chart_data || null;
  const config = visualization.config || {};

  // Temporary console logging to verify normalization parameter matches
  console.log("ChartRenderer Normalization Params:", {
    chartType: chart_type,
    chartData: chart_data,
    dataLength: chart_data?.length || 0,
    xAxis: x_axis,
    yAxis: y_axis,
    config: config
  });

  // Form normalized visualization object matching standard format
  const normalizedVisualization = {
    chart_type,
    title,
    subtitle,
    chart_data,
    x_axis,
    y_axis,
    config,
    // Keep other fields for sub-renderers (e.g. dimensions for heatmap)
    dimensions: visualization.dimensions || [],
    required_kpis: visualization.required_kpis || []
  };

  // Find sub-renderer
  const Renderer = RENDERER_REGISTRY[chart_type];

  if (!Renderer) {
    return (
      <div className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-[#12131a]/40 p-5 text-center text-xs text-slate-500 min-h-[150px] flex items-center justify-center">
        Unsupported chart type: <strong className="font-mono text-indigo-500 ml-1">{chart_type}</strong>
      </div>
    );
  }

  return <Renderer visualization={normalizedVisualization} />;
};

export default ChartRenderer;
