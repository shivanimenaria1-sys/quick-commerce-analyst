import re
import uuid
import pandas as pd
from typing import Dict, List, Tuple

# Required columns normalized to standard format (lowercase, no leading/trailing spaces/underscores, internal spaces replaced by single underscore)
REQUIRED_COLUMNS = [
    "order_id",
    "customer_id",
    "order_date",
    "order_time",
    "city",
    "category",
    "order_value",
    "quantity",
    "payment_mode",
    "delivery_time_minutes",
    "promised_delivery_time",
    "order_status",
    "customer_rating",
    "pincode",
    "dark_store_id",
    "delivery_partner_id",
    "rider_shift_minutes",
    "rider_active_minutes",
    "discount_applied",
    "delivery_charge"
]

# Simple in-memory session store mapping session_id -> pd.DataFrame
sessions: Dict[str, pd.DataFrame] = {}

class ColumnValidationError(Exception):
    """Exception raised when required columns are missing."""
    def __init__(self, missing_columns: List[str]):
        self.missing_columns = missing_columns
        super().__init__(f"Missing required columns: {', '.join(missing_columns)}")

def normalize_column_name(name: str) -> str:
    """
    Normalizes a column name by:
    1. Converting to lowercase.
    2. Trimming leading/trailing whitespace and underscores.
    3. Replacing any sequence of internal spaces and underscores with a single underscore.
    """
    if not isinstance(name, str):
        name = str(name)
    normalized = name.lower().strip()
    # Strip leading/trailing underscores
    normalized = normalized.strip('_').strip()
    # Replace whitespace and multiple underscores with a single underscore
    normalized = re.sub(r'[\s_]+', '_', normalized)
    return normalized

def ingest_and_validate_dataframe(df: pd.DataFrame) -> Tuple[str, int, List[str]]:
    """
    Normalizes DataFrame columns, checks for required columns,
    and stores the DataFrame in-memory if valid.
    
    Returns:
        Tuple containing (session_id, number_of_rows, list_of_normalized_columns)
    
    Raises:
        ColumnValidationError: If any required columns are missing.
    """
    # Create mapping of original columns to normalized names
    column_mapping = {col: normalize_column_name(col) for col in df.columns}
    
    # Rename columns in the dataframe for consistency downstream
    df_normalized = df.rename(columns=column_mapping)
    
    # Check for missing required columns
    normalized_cols_set = set(df_normalized.columns)
    missing_cols = [col for col in REQUIRED_COLUMNS if col not in normalized_cols_set]
    
    if missing_cols:
        raise ColumnValidationError(missing_cols)
        
    # Generate unique session ID
    session_id = str(uuid.uuid4())
    
    # Save to in-memory store
    sessions[session_id] = df_normalized
    
    return session_id, len(df_normalized), list(df_normalized.columns)

def get_session_data(session_id: str) -> pd.DataFrame:
    """
    Retrieves the DataFrame for a given session ID.
    Returns None if the session does not exist.
    """
    return sessions.get(session_id)
