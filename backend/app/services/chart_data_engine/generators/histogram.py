import numpy as np
import pandas as pd
from typing import List, Any
from app.services.chart_data_engine.generators.base import BaseChartGenerator
from app.services.chart_data_engine.registry import chart_registry
from app.services.chart_data_engine.utils import round_numeric_data

@chart_registry.register("histogram")
class HistogramGenerator(BaseChartGenerator):
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
            
        # Calculate 10 bins using numpy
        counts, bin_edges = np.histogram(series, bins=10)
        chart_data = []
        for i in range(len(counts)):
            bin_min = bin_edges[i]
            bin_max = bin_edges[i+1]
            bin_name = f"{round(bin_min, 1)}-{round(bin_max, 1)}"
            chart_data.append({
                "name": bin_name,
                "count": int(counts[i]),
                "bin_min": float(bin_min),
                "bin_max": float(bin_max)
            })
            
        return round_numeric_data(chart_data)
