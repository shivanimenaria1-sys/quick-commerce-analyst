import logging
import numpy as np
import pandas as pd
from typing import List

logger = logging.getLogger("dataset_profiler")

def is_numeric_like(series: pd.Series) -> bool:
    """
    Heuristic to determine if a column is numeric-like (could be read as string
    due to symbols like currency, spaces, commas, or percent signs).
    """
    if pd.api.types.is_numeric_dtype(series):
        return True
    if not pd.api.types.is_object_dtype(series) and not pd.api.types.is_string_dtype(series):
        return False
        
    non_null = series.dropna()
    if non_null.empty:
        return False
        
    # Attempt cleaning
    try:
        cleaned = non_null.astype(str).str.replace(r'[$\s€£¥,%]', '', regex=True)
        cleaned = cleaned.replace('', np.nan)
        converted = pd.to_numeric(cleaned, errors='coerce')
        
        success_ratio = converted.notna().sum() / len(non_null)
        return success_ratio > 0.85
    except Exception as e:
        logger.debug(f"Error checking numeric-like for series: {e}")
        return False


def clean_numeric_string(series: pd.Series) -> pd.Series:
    """
    Cleans numeric strings by removing currency signs ($ € £ ¥),
    commas, spaces, and percent signs to convert to float.
    """
    if pd.api.types.is_numeric_dtype(series):
        return series
        
    cleaned = series.astype(str).str.replace(r'[$\s€£¥,%]', '', regex=True)
    cleaned = cleaned.replace('', np.nan)
    return pd.to_numeric(cleaned, errors='coerce')


def robust_parse_dates(series: pd.Series, formats: List[str] = None) -> pd.Series:
    """
    Robustly parses a series of string dates into pandas datetime objects using
    an explicit list of formats in order of priority.
    """
    if pd.api.types.is_datetime64_any_dtype(series):
        return series
        
    if formats is None:
        formats = [
            '%Y-%m-%d', '%d-%m-%Y', '%Y/%m/%d', '%d/%m/%Y',
            '%Y-%m-%d %H:%M:%S', '%d-%m-%Y %H:%M:%S',
            '%Y-%m-%dT%H:%M:%S', '%Y-%m-%dT%H:%M:%SZ'
        ]
        
    # Convert series elements to string, keeping NaNs
    str_series = series.astype(str)
    str_series = str_series.where(series.notna(), np.nan)
    
    result = pd.Series(pd.NaT, index=series.index, dtype='datetime64[ns]')
    remaining = str_series.copy()
    parsed_mask = pd.Series(False, index=series.index)
    
    for fmt in formats:
        unparsed_mask = (~parsed_mask) & remaining.notna()
        if not unparsed_mask.any():
            break
            
        try:
            parsed_subset = pd.to_datetime(remaining[unparsed_mask], format=fmt, errors='coerce')
            success_mask = parsed_subset.notna()
            
            success_indices = success_mask[success_mask].index
            result.loc[success_indices] = parsed_subset.loc[success_indices]
            parsed_mask.loc[success_indices] = True
        except Exception:
            continue
            
    return result


def is_datetime_like(series: pd.Series) -> bool:
    """
    Heuristic to determine if a column is datetime-like.
    """
    if pd.api.types.is_datetime64_any_dtype(series):
        return True
    if not pd.api.types.is_object_dtype(series) and not pd.api.types.is_string_dtype(series):
        return False
        
    non_null = series.dropna()
    if non_null.empty:
        return False
        
    try:
        parsed = robust_parse_dates(non_null)
        success_ratio = parsed.notna().sum() / len(non_null)
        return success_ratio > 0.85
    except Exception as e:
        logger.debug(f"Error checking datetime-like for series: {e}")
        return False
