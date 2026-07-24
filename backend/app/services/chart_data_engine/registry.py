from typing import Dict, Any, Type

class ChartGeneratorRegistry:
    def __init__(self):
        self._generators: Dict[str, Any] = {}
        
    def register(self, chart_type: str):
        """
        Decorator to register a generator class for a specific chart type.
        Instantiates the class on registration.
        """
        def decorator(cls: Type[Any]):
            self._generators[chart_type.lower()] = cls()
            return cls
        return decorator
        
    def get_generator(self, chart_type: str) -> Any:
        return self._generators.get(chart_type.lower())

chart_registry = ChartGeneratorRegistry()
