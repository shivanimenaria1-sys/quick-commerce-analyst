from typing import List, Any
from app.services.chart_data_engine.generators.base import BaseChartGenerator
from app.services.chart_data_engine.registry import chart_registry
from app.services.chart_data_engine.utils import format_records

@chart_registry.register("scatter")
class ScatterGenerator(BaseChartGenerator):
    def generate(self, runtime: Any, context: Any, dimensions: List[str], required_kpis: List[str]) -> Any:
        df = runtime.df
        if df is None or df.empty or len(dimensions) < 2:
            return None
            
        x_axis = dimensions[0]
        y_axis = dimensions[1]
        
        if x_axis not in df.columns or y_axis not in df.columns:
            return None
            
        df_clean = df[[x_axis, y_axis]].dropna()
        if df_clean.empty:
            return None
            
        # Downsample to a maximum of 250 points to prevent browser rendering lag
        if len(df_clean) > 250:
            df_clean = df_clean.sample(n=250, random_state=42)
            
        # Sort values chronologically or by X axis for neatness (optional, but scatter is point-based)
        df_clean = df_clean.sort_values(by=x_axis)
        
        return format_records(df_clean)
