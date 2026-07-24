import os
import json
import hashlib
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

logger = logging.getLogger("dataset_profiler")

class BaseCacheProvider(ABC):
    """
    Abstract Base Class for mapping cache storage.
    Enables future extensions like SQLite, Redis, or PostgreSQL.
    """
    @abstractmethod
    def get(self, fingerprint: str) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    def set(self, fingerprint: str, mapping: Dict[str, Any]) -> None:
        pass


class JSONFileCacheProvider(BaseCacheProvider):
    """
    Concrete CacheProvider that persists data in a JSON file.
    """
    def __init__(self, file_path: str = None):
        if file_path is None:
            # Default to backend/data/semantic_cache.json
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            data_dir = os.path.join(base_dir, "data")
            os.makedirs(data_dir, exist_ok=True)
            file_path = os.path.join(data_dir, "semantic_cache.json")
        self.file_path = file_path
        self._cache = self._load_cache()

    def _load_cache(self) -> Dict[str, Any]:
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading semantic cache file: {e}")
                return {}
        return {}

    def _save_cache(self) -> None:
        try:
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump(self._cache, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving semantic cache file: {e}")

    def get(self, fingerprint: str) -> Optional[Dict[str, Any]]:
        return self._cache.get(fingerprint)

    def set(self, fingerprint: str, mapping: Dict[str, Any]) -> None:
        self._cache[fingerprint] = mapping
        self._save_cache()


def generate_schema_fingerprint(dataset_profile: Dict[str, Any]) -> str:
    """
    Generates a deterministic SHA-256 schema fingerprint based on the
    dataset's column names, types, rounded stats, and cardinality ratios.
    This ensures order-independence and minor data variation tolerance.
    """
    columns = dataset_profile.get("columns", {})
    sorted_cols = sorted(columns.keys())
    
    parts = []
    for col in sorted_cols:
        col_data = columns[col]
        dtype = col_data.get("inferred_dtype", "")
        
        # Get stats
        stats = col_data.get("statistics", {})
        cardinality = stats.get("cardinality_ratio")
        null_pct = stats.get("null_percentage")
        
        # Rounded stats
        r_card = round(float(cardinality), 4) if cardinality is not None else 0.0
        r_null = round(float(null_pct), 2) if null_pct is not None else 0.0
        
        num_min = stats.get("min")
        num_max = stats.get("max")
        num_mean = stats.get("mean")
        
        r_min = round(float(num_min), 2) if num_min is not None else None
        r_max = round(float(num_max), 2) if num_max is not None else None
        r_mean = round(float(num_mean), 2) if num_mean is not None else None
        
        part = f"{col.lower().strip()}:{dtype}:{r_card}:{r_null}:{r_min}:{r_max}:{r_mean}"
        parts.append(part)
        
    full_str = "||".join(parts)
    return hashlib.sha256(full_str.encode('utf-8')).hexdigest()
