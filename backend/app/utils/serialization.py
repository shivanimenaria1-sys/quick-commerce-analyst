import math
import datetime
import numpy as np
import pandas as pd

def clean_for_json(val):
    """
    Recursively cleans values inside dictionaries, lists, or scalars to make them JSON serializable.
    - Replaces float NaN and +/- Infinity with None.
    - Replaces pandas NaT, pd.NA, and np.nan with None.
    - Converts numpy scalars (np.int64, np.float64, np.bool_) to standard Python types.
    - Converts datetime, date, time, and Timestamp objects to ISO strings.
    - Converts Timedelta objects to string representation.
    """
    if isinstance(val, dict):
        return {k: clean_for_json(v) for k, v in val.items()}
    elif isinstance(val, (list, tuple)):
        return [clean_for_json(v) for v in val]
        
    # Check for pandas/numpy nulls (like pd.NaT, pd.NA, np.nan, None)
    if pd.isna(val):
        return None
        
    # Check numpy types
    if isinstance(val, (np.integer, np.floating)):
        as_py = val.item()
        if isinstance(as_py, float) and (math.isnan(as_py) or math.isinf(as_py)):
            return None
        return as_py
    elif isinstance(val, np.bool_):
        return bool(val)
    elif isinstance(val, np.ndarray):
        return [clean_for_json(item) for item in val.tolist()]
        
    # Check standard floats for nan/inf
    if isinstance(val, float):
        if math.isnan(val) or math.isinf(val):
            return None
        return val
        
    # Check datetimes and timestamps
    if isinstance(val, (pd.Timestamp, datetime.datetime, datetime.date, datetime.time)):
        return val.isoformat()
    elif isinstance(val, (pd.Timedelta, datetime.timedelta)):
        return str(val)
        
    return val
