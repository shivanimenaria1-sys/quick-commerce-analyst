import logging
from typing import Dict, List, Callable, Tuple, Any
from app.services.kpi_generator.context import PipelineContext

logger = logging.getLogger("dataset_profiler")

# Type signature of a KPI candidate generator: (context) -> list of KPI dicts
KPIGeneratorFunc = Callable[[PipelineContext], List[Dict[str, Any]]]

class KPIGeneratorRegistry:
    """
    Registry for dynamic KPI generation plugins.
    Allows registering candidate KPI generators using decorators.
    """
    def __init__(self):
        self._generators: Dict[str, KPIGeneratorFunc] = {}

    def register(self, name: str, func: KPIGeneratorFunc) -> None:
        if name in self._generators:
            logger.warning(f"Overwriting registered KPI generator: {name}")
        self._generators[name] = func
        logger.info(f"Registered KPI generator plugin: '{name}'")

    def get_generators(self) -> List[Tuple[str, KPIGeneratorFunc]]:
        return list(self._generators.items())


# Shared singleton registry instance
kpi_registry = KPIGeneratorRegistry()

def register_kpi_generator(name: str):
    """
    Decorator to register a KPI candidate generator plugin.
    """
    def decorator(func: KPIGeneratorFunc):
        kpi_registry.register(name, func)
        return func
    return decorator
