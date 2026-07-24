from abc import ABC, abstractmethod
from typing import List, Any

class BaseChartGenerator(ABC):
    """
    Abstract Base Class for all chart data generators.
    """
    @abstractmethod
    def generate(self, runtime: Any, context: Any, dimensions: List[str], required_kpis: List[str]) -> Any:
        """
        Processes the active DataFrame inside PipelineRuntime and compiles
        the chart data list/dict conforming to standard formats.
        """
        pass
