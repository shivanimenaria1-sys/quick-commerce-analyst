import logging
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Callable, Tuple

logger = logging.getLogger("dataset_profiler")

# --- Mathematical Relationship Plugins ---
RELATIONSHIP_DETECTORS: Dict[str, Callable[[pd.Series, pd.Series, pd.Series, float], bool]] = {}

def register_relationship(name: str):
    """
    Decorator to register a new mathematical relationship detector plugin.
    """
    def decorator(func: Callable[[pd.Series, pd.Series, pd.Series, float], bool]):
        RELATIONSHIP_DETECTORS[name] = func
        return func
    return decorator


@register_relationship("addition")
def check_addition(a: pd.Series, b: pd.Series, c: pd.Series, tolerance: float) -> bool:
    # C ≈ A + B
    diff = (c - (a + b)).abs()
    return float(diff.max()) < tolerance if not diff.empty else False


@register_relationship("subtraction")
def check_subtraction(a: pd.Series, b: pd.Series, c: pd.Series, tolerance: float) -> bool:
    # C ≈ A - B
    diff = (c - (a - b)).abs()
    return float(diff.max()) < tolerance if not diff.empty else False


@register_relationship("multiplication")
def check_multiplication(a: pd.Series, b: pd.Series, c: pd.Series, tolerance: float) -> bool:
    # C ≈ A * B
    diff = (c - (a * b)).abs()
    return float(diff.max()) < tolerance if not diff.empty else False


@register_relationship("division")
def check_division(a: pd.Series, b: pd.Series, c: pd.Series, tolerance: float) -> bool:
    # C ≈ A / B
    # Handle division by zero
    if (b == 0).any():
        return False
    diff = (c - (a / b)).abs()
    return float(diff.max()) < tolerance if not diff.empty else False


def detect_derived_columns(df: pd.DataFrame, numeric_cols: List[str], tolerance: float = 1e-4) -> List[Dict[str, Any]]:
    """
    Scans all numeric triplets (A, B, C) in the dataframe and uses registered
    relationship detectors to find columns derived from others.
    """
    derived = []
    n = len(numeric_cols)
    if n < 3:
        return derived

    # Clean numeric columns to make sure they are floats
    cleaned_df = pd.DataFrame()
    for col in numeric_cols:
        from app.services.dataset_profiler.cleaners import clean_numeric_string
        cleaned_df[col] = clean_numeric_string(df[col]).dropna()

    # Align indices after dropping NaNs across triplets
    for i in range(n):
        for j in range(n):
            if i == j:
                continue
            for k in range(n):
                if k == i or k == j:
                    continue
                
                col_a = numeric_cols[i]
                col_b = numeric_cols[j]
                col_c = numeric_cols[k]
                
                # Check subset of aligned non-null indices
                common_idx = cleaned_df[col_a].index.intersection(cleaned_df[col_b].index).intersection(cleaned_df[col_c].index)
                if len(common_idx) < 5:  # Require at least 5 common rows to verify relationship
                    continue
                    
                a_series = cleaned_df.loc[common_idx, col_a]
                b_series = cleaned_df.loc[common_idx, col_b]
                c_series = cleaned_df.loc[common_idx, col_c]
                
                for rel_name, detector in RELATIONSHIP_DETECTORS.items():
                    try:
                        # Avoid duplicates like addition of A+B and B+A
                        if rel_name == "addition" and col_a > col_b:
                            continue
                        if rel_name == "multiplication" and col_a > col_b:
                            continue
                            
                        if detector(a_series, b_series, c_series, tolerance):
                            derived.append({
                                "target_column": col_c,
                                "source_column_a": col_a,
                                "source_column_b": col_b,
                                "relationship_type": rel_name,
                                "formula": f"{col_c} = {col_a} {get_operator_symbol(rel_name)} {col_b}"
                            })
                            break
                    except Exception as e:
                        logger.debug(f"Error checking relationship {rel_name} for ({col_a}, {col_b}, {col_c}): {e}")
                        continue
    return derived


def get_operator_symbol(rel_name: str) -> str:
    symbols = {
        "addition": "+",
        "subtraction": "-",
        "multiplication": "*",
        "division": "/"
    }
    return symbols.get(rel_name, "?")


# --- Correlation Calculators ---
CORRELATION_METHODS: Dict[str, Callable[[pd.DataFrame, List[str]], pd.DataFrame]] = {
    "pearson": lambda df, cols: df[cols].corr(method="pearson"),
    "spearman": lambda df, cols: df[cols].corr(method="spearman"),
    "kendall": lambda df, cols: df[cols].corr(method="kendall")
}

def register_correlation_method(name: str, func: Callable[[pd.DataFrame, List[str]], pd.DataFrame]):
    """
    Registers a new correlation calculator algorithm method.
    """
    CORRELATION_METHODS[name] = func


def compute_correlations(df: pd.DataFrame, numeric_cols: List[str], method: str = "pearson") -> Dict[str, Dict[str, float]]:
    """
    Calculates the correlation matrix using the registered correlation method.
    Returns a nested dictionary compatible with JSON serialization.
    """
    if len(numeric_cols) < 2:
        return {}
        
    if method not in CORRELATION_METHODS:
        logger.warning(f"Correlation method '{method}' not found. Falling back to Pearson.")
        method = "pearson"
        
    try:
        # Pre-clean string columns to numeric values
        cleaned_df = pd.DataFrame()
        for col in numeric_cols:
            from app.services.dataset_profiler.cleaners import clean_numeric_string
            cleaned_df[col] = clean_numeric_string(df[col])
            
        corr_matrix = CORRELATION_METHODS[method](cleaned_df, numeric_cols)
        
        # Round and clean for JSON compatibility
        from app.services.dataset_profiler.statistics import safe_float
        result = {}
        for c1 in corr_matrix.columns:
            result[str(c1)] = {}
            for c2 in corr_matrix.columns:
                result[str(c1)][str(c2)] = safe_float(corr_matrix.loc[c1, c2])
        return result
    except Exception as e:
        logger.error(f"Error computing correlation matrix: {e}")
        return {}


# --- Primary Key / Identifier Detection ---
def detect_primary_keys(df: pd.DataFrame, inferred_types: Dict[str, str]) -> List[str]:
    """
    Identifies likely primary key / identifier columns using pure heuristics
    (100% uniqueness, no null values, is id_like or integer/string patterns).
    """
    pk_candidates = []
    total_rows = len(df)
    
    if total_rows == 0:
        return pk_candidates
        
    for col in df.columns:
        series = df[col]
        non_null = series.dropna()
        
        # Heuristics:
        # 1. No null values
        if len(non_null) != total_rows:
            continue
            
        # 2. 100% unique
        unique_count = len(non_null.unique())
        if unique_count != total_rows:
            continue
            
        # 3. Candidate type check (prefer id_like or integer keys)
        inferred_type = inferred_types.get(col)
        score = 0.0
        
        if inferred_type == "id_like":
            score += 0.95
        elif inferred_type == "integer":
            score += 0.80
        elif inferred_type == "free_text":
            # Free text with 100% uniqueness is rarely a primary key
            score += 0.10
        else:
            score += 0.40
            
        # Simple name pattern booster (independent of domain context)
        col_lower = str(col).lower()
        if any(pat in col_lower for pat in ["id", "code", "no", "key", "pk"]):
            score += 0.15
            
        if score >= 0.70:
            pk_candidates.append(col)
            
    return pk_candidates
