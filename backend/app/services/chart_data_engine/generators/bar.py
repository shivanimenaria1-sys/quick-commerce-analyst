import pandas as pd
from typing import List, Any
from app.services.chart_data_engine.generators.base import BaseChartGenerator
from app.services.chart_data_engine.registry import chart_registry
from app.services.chart_data_engine.utils import resolve_kpi_column_and_agg, format_records

@chart_registry.register("bar")
class BarGenerator(BaseChartGenerator):
    def generate(self, runtime: Any, context: Any, dimensions: List[str], required_kpis: List[str]) -> Any:
        df = runtime.df
        if df is None or df.empty or not dimensions:
            return None
            
        x_axis = dimensions[0]
        if x_axis not in df.columns:
            return None
            
        semantic_mapping = context.confirmed_semantic_mapping
        
        # Default aggregation is count
        metric_col = "order_id"
        agg_type = "count"
        y_axis = "count"
        
        if required_kpis:
            y_axis = required_kpis[0]
            col_y, agg_y = resolve_kpi_column_and_agg(y_axis, semantic_mapping)
            if col_y and col_y in df.columns:
                metric_col = col_y
                agg_type = agg_y
            elif y_axis in df.columns:
                metric_col = y_axis
                agg_type = "mean" if pd.api.types.is_numeric_dtype(df[y_axis]) else "count"
                
        df_clean = df.dropna(subset=[x_axis])
        if df_clean.empty:
            return None
            
        # Group and aggregate
        if agg_type == "count":
            agg_df = df_clean.groupby(x_axis)[metric_col].count().reset_index(name=y_axis)
        elif agg_type == "sum":
            agg_df = df_clean.groupby(x_axis)[metric_col].sum().reset_index(name=y_axis)
        elif agg_type == "mean":
            agg_df = df_clean.groupby(x_axis)[metric_col].mean().reset_index(name=y_axis)
        elif agg_type == "cancellation_rate":
            agg_df = df_clean.groupby(x_axis)[metric_col].apply(
                lambda x: (x.astype(str).str.lower() == 'cancelled').mean() * 100.0
            ).reset_index(name=y_axis)
        elif agg_type == "return_rate":
            agg_df = df_clean.groupby(x_axis)[metric_col].apply(
                lambda x: (x.astype(str).str.lower() == 'returned').mean() * 100.0
            ).reset_index(name=y_axis)
        else:
            agg_df = df_clean.groupby(x_axis)[metric_col].mean().reset_index(name=y_axis)
            
        # Sort descending by the aggregated metric value
        agg_df = agg_df.sort_values(by=y_axis, ascending=False)
        
        # Cap to top 15 categories to prevent visual clutter
        if len(agg_df) > 15:
            agg_df = agg_df.head(15)
            
        return format_records(agg_df)
