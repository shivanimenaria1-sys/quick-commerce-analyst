import logging
from typing import Dict, List, Callable, Tuple, Any
import pandas as pd

logger = logging.getLogger("dataset_profiler")

# Type alias for generator function: (df, mapping) -> (new_df_cols, metadata_list)
FeatureGeneratorFunc = Callable[[pd.DataFrame, Dict[str, Any]], Tuple[pd.DataFrame, List[Dict[str, Any]]]]

class FeatureGeneratorRegistry:
    """
    Central registry for Feature Generator plugins.
    Allows dynamic registration of new feature computation rules.
    """
    def __init__(self):
        self._generators: Dict[str, FeatureGeneratorFunc] = {}

    def register(self, name: str, func: FeatureGeneratorFunc) -> None:
        """
        Registers a new generator function.
        """
        if name in self._generators:
            logger.warning(f"Overwriting registered feature generator: {name}")
        self._generators[name] = func
        logger.info(f"Registered feature generator plugin: '{name}'")

    def get_generators(self) -> List[Tuple[str, FeatureGeneratorFunc]]:
        """
        Returns all registered generator plugins.
        """
        return list(self._generators.items())


# Shared singleton registry instance
registry = FeatureGeneratorRegistry()

def register_generator(name: str):
    """
    Decorator to register a feature generator function.
    """
    def decorator(func: FeatureGeneratorFunc):
        registry.register(name, func)
        return func
    return decorator
