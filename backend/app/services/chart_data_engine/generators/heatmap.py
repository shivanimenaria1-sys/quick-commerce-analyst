import pandas as pd
from typing import List, Any
from app.services.chart_data_engine.generators.base import BaseChartGenerator
from app.services.chart_data_engine.registry import chart_registry
from app.services.chart_data_engine.utils import round_numeric_data

@chart_registry.register("heatmap")
class HeatmapGenerator(BaseChartGenerator):
    def generate(self, runtime: Any, context: Any, dimensions: List[str], required_kpis: List[str]) -> Any:
        df = runtime.df
        if df is None or df.empty or not dimensions:
            return None
            
        # Filter existing columns that are numeric in df
        numeric_cols = [col for col in dimensions if col in df.columns]
        numeric_cols = [col for col in numeric_cols if pd.api.types.is_numeric_dtype(df[col])]
        
        if len(numeric_cols) < 2:
            return None
            
        # Pearson correlation matrix
        corr_matrix = df[numeric_cols].corr(method='pearson').fillna(0.0)
        return round_numeric_data(corr_matrix.to_dict())
