import numpy as np
import pandas as pd
from typing import Dict, Any, Tuple, List

def get_columns_with_role(mapping: dict, role: str) -> List[str]:
    cols = []
    columns_mapping = mapping.get("columns", mapping)
    for col_name, col_data in columns_mapping.items():
        curr_role = col_data if isinstance(col_data, str) else col_data.get("semantic_role", "")
        if curr_role == role:
            cols.append(col_name)
    return cols

def get_column_by_role(semantic_mapping: dict, role: str) -> str:
    cols = get_columns_with_role(semantic_mapping, role)
    return cols[0] if cols else None

def resolve_kpi_column_and_agg(kpi_id: str, semantic_mapping: dict) -> Tuple[str, str]:
    """
    Resolves the semantic role/column name and aggregation function based on KPI ID.
    Returns:
        Tuple of (column_name, aggregation_type)
    """
    ROLE_AGG_MAP = {
        "total_revenue": ("revenue_like", "sum"),
        "average_revenue": ("revenue_like", "mean"),
        "total_cost": ("cost_like", "sum"),
        "average_cost": ("cost_like", "mean"),
        "gross_profit": ("profit_margin", "sum"),
        "avg_profit_margin_per_order": ("profit_margin", "mean"),
        "profit_margin": ("profit_margin", "mean"),
        "total_orders": ("order_id", "count"),
        "average_order_value": ("order_value", "mean"),
        "avg_delivery_time": ("duration_like", "mean"),
        "avg_customer_rating": ("rating_like", "mean"),
        "avg_rider_utilization_pct": ("utilization_like", "mean"),
        "cancellation_rate": ("status_like", "cancellation_rate"),
        "return_rate": ("status_like", "return_rate"),
        "repeat_customer_rate": ("customer_id", "repeat_customer_rate"),
    }
    
    if kpi_id in ROLE_AGG_MAP:
        role, agg = ROLE_AGG_MAP[kpi_id]
        
        # Special case: total_orders and repeat_customer_rate can use customer_id or other fields
        if role == "order_id":
            # Find order_id or fallback to any column
            col = get_column_by_role(semantic_mapping, "id_like") or "order_id"
            return col, agg
            
        col = get_column_by_role(semantic_mapping, role)
        if col:
            return col, agg
            
    # Fallbacks: check if KPI ID matches any semantic role directly
    col = get_column_by_role(semantic_mapping, kpi_id)
    if col:
        return col, "mean"
        
    return None, None

def round_numeric_data(data: Any) -> Any:
    """
    Recursively rounds floats and cleans Pandas/NumPy types for JSON serialization.
    """
    if isinstance(data, dict):
        return {str(k): round_numeric_data(v) for k, v in data.items()}
    elif isinstance(data, (list, tuple, set)):
        return [round_numeric_data(x) for x in data]
    elif isinstance(data, (float, np.float64, np.float32)):
        if pd.isna(data) or np.isnan(data) or np.isinf(data):
            return None
        return round(float(data), 2)
    elif isinstance(data, (int, np.integer)):
        return int(data)
    elif isinstance(data, (bool, np.bool_)):
        return bool(data)
    elif pd.isna(data):
        return None
    else:
        return data

def format_records(df: pd.DataFrame) -> list:
    """
    Safely converts a DataFrame to a list of dict records with clean JSON-safe types.
    """
    records = df.to_dict(orient='records')
    return [round_numeric_data(r) for r in records]
