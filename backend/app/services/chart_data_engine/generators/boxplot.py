import pandas as pd
from typing import List, Any
from app.services.chart_data_engine.generators.base import BaseChartGenerator
from app.services.chart_data_engine.registry import chart_registry
from app.services.chart_data_engine.utils import round_numeric_data

@chart_registry.register("boxplot")
class BoxPlotGenerator(BaseChartGenerator):
    def generate(self, runtime: Any, context: Any, dimensions: List[str], required_kpis: List[str]) -> Any:
        df = runtime.df
        if df is None or df.empty or not dimensions:
            return None
            
        x_axis = dimensions[0]
        if x_axis not in df.columns:
            return None
            
        series = pd.to_numeric(df[x_axis], errors='coerce').dropna()
        if series.empty:
            return None
            
        q1 = float(series.quantile(0.25))
        median = float(series.median())
        q3 = float(series.quantile(0.75))
        iqr = q3 - q1
        
        lower_limit = q1 - 1.5 * iqr
        upper_limit = q3 + 1.5 * iqr
        
        # Whiskers represent actual min and max data points within limits (non-outliers)
        non_outliers = series[(series >= lower_limit) & (series <= upper_limit)]
        minimum = float(non_outliers.min()) if not non_outliers.empty else float(series.min())
        maximum = float(non_outliers.max()) if not non_outliers.empty else float(series.max())
        
        return [round_numeric_data({
            "min": minimum,
            "q1": q1,
            "median": median,
            "q3": q3,
            "max": maximum,
            "iqr": iqr,
            "lower_limit": lower_limit,
            "upper_limit": upper_limit
        })]
