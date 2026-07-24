from typing import List, Any
from app.services.chart_data_engine.generators.bar import BarGenerator
from app.services.chart_data_engine.registry import chart_registry

@chart_registry.register("pie")
class PieGenerator(BarGenerator):
    """
    Renders pie/donut segment share data by inheriting aggregation logic from BarGenerator
    but capping segment slices to a maximum of top 7 categories.
    """
    def generate(self, runtime: Any, context: Any, dimensions: List[str], required_kpis: List[str]) -> Any:
        data = super().generate(runtime, context, dimensions, required_kpis)
        if data and len(data) > 7:
            return data[:7]
        return data
