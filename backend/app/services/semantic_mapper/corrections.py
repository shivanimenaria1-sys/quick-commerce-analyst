import os
import json
import logging
import datetime
from typing import Dict, Any, List
from app.services.semantic_mapper.cache import JSONFileCacheProvider

logger = logging.getLogger("dataset_profiler")

def save_correction(fingerprint: str, column_name: str, original_role: str, corrected_role: str) -> None:
    """
    Saves a user override correction into a persistent log file,
    and updates the active schema cache with the overridden values.
    """
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    data_dir = os.path.join(base_dir, "data")
    os.makedirs(data_dir, exist_ok=True)
    corrections_file = os.path.join(data_dir, "semantic_corrections.json")
    
    # 1. Append to corrections log
    corrections: List[Dict[str, Any]] = []
    if os.path.exists(corrections_file):
        try:
            with open(corrections_file, 'r', encoding='utf-8') as f:
                corrections = json.load(f)
        except Exception as e:
            logger.error(f"Error loading semantic corrections log: {e}")
            
    correction_entry = {
        "schema_fingerprint": fingerprint,
        "column_name": column_name,
        "original_role": original_role,
        "corrected_role": corrected_role,
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z"
    }
    corrections.append(correction_entry)
    
    try:
        with open(corrections_file, 'w', encoding='utf-8') as f:
            json.dump(corrections, f, indent=2)
        logger.info(f"User correction logged: '{column_name}' mapped from '{original_role}' to '{corrected_role}'.")
    except Exception as e:
        logger.error(f"Error writing semantic corrections: {e}")
        
    # 2. Update cache immediately so subsequent calls return overridden values
    try:
        cache_provider = JSONFileCacheProvider()
        cached = cache_provider.get(fingerprint)
        if cached:
            columns_mapping = cached.get("columns", {})
            if column_name in columns_mapping:
                columns_mapping[column_name]["semantic_role"] = corrected_role
                columns_mapping[column_name]["confidence"] = 1.0
                columns_mapping[column_name]["needs_user_confirmation"] = False
                cached["columns"] = columns_mapping
                cache_provider.set(fingerprint, cached)
                logger.info(f"Schema cache updated with overridden role for column '{column_name}'.")
    except Exception as e:
        logger.error(f"Error updating cache with override: {e}")
