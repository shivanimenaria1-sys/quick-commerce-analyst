import pandas as pd
from typing import List, Any
from app.services.chart_data_engine.generators.base import BaseChartGenerator
from app.services.chart_data_engine.registry import chart_registry
from app.services.chart_data_engine.utils import resolve_kpi_column_and_agg, format_records

@chart_registry.register("line")
class LineGenerator(BaseChartGenerator):
    def generate(self, runtime: Any, context: Any, dimensions: List[str], required_kpis: List[str]) -> Any:
        df = runtime.df
        if df is None or df.empty or not dimensions:
            return None
            
        x_axis = dimensions[0]
        if x_axis not in df.columns:
            return None
            
        semantic_mapping = context.confirmed_semantic_mapping
        
        # Default metric is order count
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
            
        # Clone df section to safely modify x_axis values
        df_clean = df_clean.copy()
        
        # Group temporal column to YYYY-MM or YYYY-MM-DD to keep data points readable
        try:
            dates = pd.to_datetime(df_clean[x_axis], errors='coerce')
            non_na_dates = dates.dropna()
            if not non_na_dates.empty:
                unique_months = non_na_dates.dt.to_period('M').nunique()
                if unique_months > 12:
                    df_clean[x_axis] = dates.dt.strftime('%Y-%m')
                else:
                    df_clean[x_axis] = dates.dt.strftime('%Y-%m-%d')
            else:
                # Fallback to standard string representation
                df_clean[x_axis] = df_clean[x_axis].astype(str)
        except Exception:
            df_clean[x_axis] = df_clean[x_axis].astype(str)
            
        # Perform group aggregation
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
            agg_df = df_clean.groupby(x_axis)[metric_col].sum().reset_index(name=y_axis)
            
        # Sort chronologically by x_axis
        agg_df = agg_df.sort_values(by=x_axis)
        return format_records(agg_df)
