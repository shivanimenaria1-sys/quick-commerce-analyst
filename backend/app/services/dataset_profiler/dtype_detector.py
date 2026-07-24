import logging
import re
import numpy as np
import pandas as pd
from typing import Tuple, Dict, Any
from app.services.dataset_profiler.cleaners import is_numeric_like, clean_numeric_string, is_datetime_like, robust_parse_dates

logger = logging.getLogger("dataset_profiler")

def detect_column_type(series: pd.Series) -> Tuple[str, float]:
    """
    Analyzes a column and returns the inferred data type and a confidence score (0.0 to 1.0).
    Inferred types: numeric (with sub-type integer/float), categorical, datetime, boolean, id_like, free_text.
    """
    total = len(series)
    non_null = series.dropna()
    
    if total == 0 or non_null.empty:
        # Defaults for empty column
        return "categorical", 0.0

    unique_vals = non_null.unique()
    unique_count = len(unique_vals)
    cardinality_ratio = unique_count / len(non_null)
    
    # 1. Check Boolean
    # Boolean-like values
    bool_patterns = {
        (True, False), (0, 1), ('1', '0'), ('yes', 'no'), ('y', 'n'), ('t', 'f'),
        ('true', 'false'), ('active', 'inactive'), ('delivered', 'cancelled')
    }
    unique_set_lower = {str(x).lower().strip() for x in unique_vals}
    
    if unique_count <= 2:
        # Check if matches standard boolean sets
        for pattern in bool_patterns:
            pattern_set = {str(x).lower().strip() for x in pattern}
            if unique_set_lower.issubset(pattern_set):
                return "boolean", 0.95
        if pd.api.types.is_bool_dtype(series):
            return "boolean", 1.0

    # 2. Check Datetime
    if is_datetime_like(series):
        parsed = robust_parse_dates(non_null)
        success_ratio = parsed.notna().sum() / len(non_null)
        if success_ratio > 0.85:
            return "datetime", float(success_ratio)

    # 3. Check ID-like
    # ID-like columns typically have high cardinality, unique values, and are usually strings or integers
    if unique_count == len(non_null) and unique_count > 1:
        # Check if float
        is_float = False
        if is_numeric_like(series):
            cleaned = clean_numeric_string(series)
            valid_cleaned = cleaned.dropna()
            is_int = np.all(valid_cleaned % 1 == 0) if not valid_cleaned.empty else False
            if not is_int:
                is_float = True
                
        if not is_float:
            # Check if they are integers or codes
            if pd.api.types.is_integer_dtype(series) or is_numeric_like(series):
                if pd.api.types.is_integer_dtype(series):
                    num_vals = unique_vals
                else:
                    num_vals = clean_numeric_string(pd.Series(unique_vals)).dropna().values
                
                try:
                    sorted_vals = np.sort(num_vals)
                    diffs = np.diff(sorted_vals)
                    is_consecutive = np.all(diffs == 1) or len(diffs) == 0
                except Exception:
                    is_consecutive = False
                
                col_lower = str(series.name).lower()
                has_id_name = any(pat in col_lower for pat in ["id", "code", "no", "key", "num", "pk"])
                
                max_val = max(num_vals) if len(num_vals) > 0 else 0
                if is_consecutive and (has_id_name or max_val > 1000):
                    return "id_like", 0.95
                elif has_id_name:
                    return "id_like", 0.90
            else:
                # String columns with 100% uniqueness and relatively short strings
                avg_len = non_null.astype(str).str.len().mean()
                if avg_len < 15:
                    col_lower = str(series.name).lower()
                    has_id_name = any(pat in col_lower for pat in ["id", "code", "no", "key", "num", "pk"])
                    has_alpha = non_null.astype(str).str.contains(r'[a-zA-Z]').any()
                    has_digit = non_null.astype(str).str.contains(r'\d').any()
                    if has_id_name or (has_alpha and has_digit):
                        return "id_like", 0.95

    # 4. Check Numeric (integer or float)
    if is_numeric_like(series):
        cleaned = clean_numeric_string(series)
        success_ratio = cleaned.notna().sum() / len(non_null)
        if success_ratio > 0.85:
            valid_cleaned = cleaned.dropna()
            
            # If the original series dtype is float, preserve it as float
            # Otherwise, check if all cleaned values are integers
            if pd.api.types.is_float_dtype(series):
                is_int = False
            else:
                is_int = np.all(valid_cleaned % 1 == 0)
                
            if is_int:
                return "integer", float(success_ratio * 0.98)
            else:
                return "float", float(success_ratio * 0.98)

    # 5. Check Free Text
    # Long strings with high cardinality
    if pd.api.types.is_object_dtype(series) or pd.api.types.is_string_dtype(series):
        avg_len = non_null.astype(str).str.len().mean()
        if avg_len > 20 and cardinality_ratio > 0.2:
            confidence = min(1.0, cardinality_ratio * (avg_len / 25.0))
            return "free_text", float(confidence)

    # 6. Default to Categorical
    # Low cardinality columns typically fall here
    confidence = min(1.0, 1.0 - cardinality_ratio + 0.1)
    return "categorical", float(confidence)
