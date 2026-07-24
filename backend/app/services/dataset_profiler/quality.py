import logging
import numpy as np
import pandas as pd
from typing import Dict, Any, List

logger = logging.getLogger("dataset_profiler")

def check_constant_column(series: pd.Series) -> bool:
    """
    Returns True if the column has exactly 1 unique non-null value.
    """
    non_null = series.dropna()
    if non_null.empty:
        return False
    return len(non_null.unique()) == 1


def check_near_constant_column(series: pd.Series, threshold: float = 0.95) -> bool:
    """
    Returns True if the most frequent non-null value represents
    more than `threshold` percentage of the non-null entries.
    """
    non_null = series.dropna()
    if non_null.empty:
        return False
        
    value_counts = non_null.value_counts()
    if value_counts.empty:
        return False
        
    top_count = value_counts.iloc[0]
    ratio = top_count / len(non_null)
    return ratio >= threshold and len(value_counts) > 1


def check_mixed_types(series: pd.Series) -> bool:
    """
    Returns True if a column contains mixed fundamental types
    (e.g., mixing strings with numeric values).
    """
    non_null = series.dropna()
    if non_null.empty:
        return False
        
    # Extract native Python types
    types = {type(x) for x in non_null}
    
    # Exclude safe mixtures like numeric integer + float
    all_numeric = all(isinstance(x, (int, float, np.integer, np.floating)) for x in non_null)
    if all_numeric:
        return False
        
    # Check if we have strings mixed with anything else
    has_str = any(isinstance(x, str) for x in non_null)
    has_non_str = any(not isinstance(x, str) for x in non_null)
    
    return has_str and has_non_str


def check_high_null_column(series: pd.Series, threshold: float = 50.0) -> bool:
    """
    Returns True if the column has more than `threshold` percent missing values.
    """
    if len(series) == 0:
        return False
    null_pct = (series.isna().sum() / len(series)) * 100.0
    return null_pct >= threshold


def check_highly_imbalanced_categorical(series: pd.Series, inferred_type: str, threshold: float = 0.95) -> bool:
    """
    Returns True if a categorical column is highly imbalanced
    (one category takes up more than `threshold` of the entries).
    """
    if inferred_type != "categorical":
        return False
        
    non_null = series.dropna()
    if non_null.empty:
        return False
        
    counts = non_null.value_counts()
    if counts.empty:
        return False
        
    top_freq = counts.iloc[0]
    return (top_freq / len(non_null)) >= threshold


def detect_dataset_quality_issues(df: pd.DataFrame, inferred_types: Dict[str, str]) -> Dict[str, List[str]]:
    """
    Scans the dataset and flags column-level quality issues:
    constant_columns, near_constant_columns, high_null_columns, mixed_type_columns, highly_imbalanced_categorical.
    """
    constant_cols = []
    near_constant_cols = []
    high_null_cols = []
    mixed_type_cols = []
    imbalanced_cat_cols = []
    
    for col in df.columns:
        series = df[col]
        inferred_type = inferred_types.get(col, "categorical")
        
        if check_constant_column(series):
            constant_cols.append(col)
            
        if check_near_constant_column(series):
            near_constant_cols.append(col)
            
        if check_high_null_column(series):
            high_null_cols.append(col)
            
        if check_mixed_types(series):
            mixed_type_cols.append(col)
            
        if check_highly_imbalanced_categorical(series, inferred_type):
            imbalanced_cat_cols.append(col)
            
    return {
        "constant_columns": constant_cols,
        "near_constant_columns": near_constant_cols,
        "high_null_columns": high_null_cols,
        "mixed_type_columns": mixed_type_cols,
        "highly_imbalanced_categorical_columns": imbalanced_cat_cols
    }
