import logging
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Union
from app.services.dataset_profiler.cleaners import clean_numeric_string, robust_parse_dates

logger = logging.getLogger("dataset_profiler")

def safe_float(val: Any) -> Union[float, None]:
    """
    Safely converts a value to a rounded float or None if invalid.
    """
    if pd.isna(val) or val is None:
        return None
    try:
        f_val = float(val)
        if np.isnan(f_val) or np.isinf(f_val):
            return None
        return round(f_val, 4)
    except (ValueError, TypeError):
        return None


def detect_datetime_granularity(series: pd.Series) -> str:
    """
    Infers the temporal granularity of a datetime series by analyzing
    the median difference between sorted unique dates.
    """
    unique_dates = pd.Series(series.dropna().unique()).sort_values()
    if len(unique_dates) < 2:
        return "unknown"
        
    diffs = unique_dates.diff().dropna()
    median_diff = diffs.median()
    
    # Get total days difference
    days = median_diff.total_seconds() / (24 * 3600)
    
    if days < 0.04:
        return "hourly_or_sub_hourly"
    elif days < 0.5:
        return "sub_daily"
    elif 0.8 <= days <= 1.2:
        return "daily"
    elif 6.0 <= days <= 8.0:
        return "weekly"
    elif 27.0 <= days <= 32.0:
        return "monthly"
    elif 85.0 <= days <= 95.0:
        return "quarterly"
    elif 350.0 <= days <= 380.0:
        return "yearly"
    else:
        return f"irregular_{round(days, 1)}_days"


def calculate_numeric_stats(series: pd.Series) -> Dict[str, Any]:
    """
    Computes numeric-specific statistics: min, max, mean, median, std, skewness, outliers (IQR).
    """
    cleaned = clean_numeric_string(series).dropna()
    if cleaned.empty:
        return {}
        
    q1 = cleaned.quantile(0.25)
    q3 = cleaned.quantile(0.75)
    iqr = q3 - q1
    lower_bound = q1 - 1.5 * iqr
    upper_bound = q3 + 1.5 * iqr
    outliers = cleaned[(cleaned < lower_bound) | (cleaned > upper_bound)]

    return {
        "min": safe_float(cleaned.min()),
        "max": safe_float(cleaned.max()),
        "mean": safe_float(cleaned.mean()),
        "median": safe_float(cleaned.median()),
        "std": safe_float(cleaned.std()),
        "skewness": safe_float(cleaned.skew()),
        "outlier_count": int(outliers.count())
    }


def calculate_categorical_stats(series: pd.Series) -> Dict[str, Any]:
    """
    Computes top 10 frequencies for categorical columns.
    """
    non_null = series.dropna().astype(str)
    if non_null.empty:
        return {"top_frequencies": {}}
        
    freqs = non_null.value_counts().head(10).to_dict()
    # Ensure keys are strings and values are native ints
    clean_freqs = {str(k): int(v) for k, v in freqs.items()}
    return {"top_frequencies": clean_freqs}


def calculate_datetime_stats(series: pd.Series) -> Dict[str, Any]:
    """
    Computes datetime statistics: min, max, granularity.
    """
    parsed = robust_parse_dates(series).dropna()
    if parsed.empty:
        return {}
        
    min_date = parsed.min()
    max_date = parsed.max()
    granularity = detect_datetime_granularity(parsed)
    
    return {
        "min_date": min_date.strftime("%Y-%m-%d %H:%M:%S") if hasattr(min_date, 'strftime') else str(min_date),
        "max_date": max_date.strftime("%Y-%m-%d %H:%M:%S") if hasattr(max_date, 'strftime') else str(max_date),
        "detected_granularity": granularity
    }


def compute_column_stats(series: pd.Series, inferred_type: str) -> Dict[str, Any]:
    """
    Computes core stats for a column based on its inferred data type.
    """
    total = len(series)
    non_null = series.dropna()
    null_count = total - len(non_null)
    null_pct = (null_count / total) * 100.0 if total > 0 else 0.0
    
    unique_count = len(non_null.unique())
    cardinality_ratio = unique_count / len(non_null) if len(non_null) > 0 else 0.0
    
    # Extract 5 sample values
    sample_vals = non_null.head(5).tolist()
    # Clean samples to ensure JSON compatibility
    clean_samples = [str(x) for x in sample_vals]

    stats = {
        "null_percentage": safe_float(null_pct),
        "unique_value_count": int(unique_count),
        "cardinality_ratio": safe_float(cardinality_ratio),
        "sample_values": clean_samples
    }

    # Add type-specific statistics
    if inferred_type in ("integer", "float", "numeric"):
        stats.update(calculate_numeric_stats(series))
    elif inferred_type == "categorical":
        stats.update(calculate_categorical_stats(series))
    elif inferred_type == "datetime":
        stats.update(calculate_datetime_stats(series))
        
    return stats
