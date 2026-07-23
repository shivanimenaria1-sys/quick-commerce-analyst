import datetime
import numpy as np
import pandas as pd
from typing import Tuple, Dict, Any, List

def robust_to_datetime(series: pd.Series, formats: List[str] = None) -> pd.Series:
    """
    Robustly parses a series of string dates into pandas datetime objects using
    an explicit list of formats in order of priority.
    """
    if formats is None:
        formats = ['%d-%m-%Y', '%d/%m/%Y', '%Y-%m-%d', '%Y/%m/%d']
        
    result = pd.Series(pd.NaT, index=series.index, dtype='datetime64[ns]')
    remaining = series.copy()
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

def clean_dataset(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Performs standard preprocessing and data cleaning tasks on the quick commerce dataset.
    Returns the cleaned DataFrame and a dictionary report summarizing the actions.
    """
    # Create a copy to avoid in-place side effects during intermediate steps
    cleaned_df = df.copy()
    
    # Store initial stats
    initial_rows = len(cleaned_df)
    
    # 1. Trim leading/trailing whitespace in all string/object columns
    for col in cleaned_df.columns:
        if pd.api.types.is_object_dtype(cleaned_df[col]) or pd.api.types.is_string_dtype(cleaned_df[col]):
            cleaned_df[col] = cleaned_df[col].apply(lambda x: x.strip() if isinstance(x, str) else x)
            
    # 2. Standardize category-like text columns to consistent casing (Title Case)
    category_like_cols = ["payment_mode", "order_status", "city"]
    for col in category_like_cols:
        if col in cleaned_df.columns:
            cleaned_df[col] = cleaned_df[col].apply(lambda x: x.title() if isinstance(x, str) else x)
            
    # 3. Detect and handle missing values
    missing_imputed = {}
    
    # Identify numeric and categorical columns
    numeric_cols = cleaned_df.select_dtypes(include=[np.number]).columns
    categorical_cols = cleaned_df.select_dtypes(exclude=[np.number, 'datetime', 'datetimetz']).columns
    
    # Numeric imputation: Median
    for col in numeric_cols:
        na_count = int(cleaned_df[col].isna().sum())
        if na_count > 0:
            median_val = cleaned_df[col].median()
            if pd.isna(median_val):
                median_val = 0
            cleaned_df[col] = cleaned_df[col].fillna(median_val)
            missing_imputed[col] = na_count
            
    # Categorical imputation: Mode
    for col in categorical_cols:
        na_count = int(cleaned_df[col].isna().sum())
        if na_count > 0:
            mode_series = cleaned_df[col].mode()
            if not mode_series.empty:
                mode_val = mode_series.iloc[0]
            else:
                mode_val = "Unknown"
            cleaned_df[col] = cleaned_df[col].fillna(mode_val)
            missing_imputed[col] = na_count

    # 4. Detect and remove exact duplicate rows, log count removed
    cleaned_df = cleaned_df.drop_duplicates().reset_index(drop=True)
    rows_after_duplicates = len(cleaned_df)
    duplicates_removed = initial_rows - rows_after_duplicates
    
    # 5. Convert order_date to datetime, order_time to time type. Log failed rows.
    failed_dates: List[Dict[str, Any]] = []
    if 'order_date' in cleaned_df.columns:
        original_dates = cleaned_df['order_date']
        # Call robust date parser
        attempted_formats = ['%d-%m-%Y', '%d/%m/%Y', '%Y-%m-%d', '%Y/%m/%d']
        converted_dates = robust_to_datetime(original_dates, attempted_formats)
        
        # Identify rows that were not null originally, but are null after conversion (failed)
        failed_mask = original_dates.notna() & converted_dates.isna()
        failed_indices = cleaned_df[failed_mask].index.tolist()
        
        if failed_indices:
            print(f"\n[DATE PARSING FAILURE REPORT] Total invalid dates: {len(failed_indices)}")
            for idx in failed_indices:
                order_id = cleaned_df.loc[idx, 'order_id'] if 'order_id' in cleaned_df.columns else "Unknown"
                orig_val = original_dates.loc[idx]
                failure_reason = f"Value '{orig_val}' did not match any of the attempted formats."
                print(f"  - Row Index: {idx}")
                print(f"    Order ID: {order_id}")
                print(f"    Original order_date: {orig_val}")
                print(f"    Attempted formats: {', '.join(attempted_formats)}")
                print(f"    Failure reason: {failure_reason}")
                
                failed_dates.append({
                    "row_index": idx,
                    "order_id": order_id,
                    "original_value": str(orig_val),
                    "attempted_formats": attempted_formats,
                    "failure_reason": failure_reason
                })
        cleaned_df['order_date'] = converted_dates

    failed_times: List[Dict[str, Any]] = []
    if 'order_time' in cleaned_df.columns:
        original_times = cleaned_df['order_time']
        
        # Helper to parse time strings flexibly
        def parse_time(val):
            if pd.isna(val):
                return None
            if isinstance(val, datetime.time):
                return val
            if isinstance(val, (pd.Timestamp, datetime.datetime)):
                return val.time()
            
            # String parsing
            val_str = str(val).strip()
            for fmt in ('%H:%M:%S', '%H:%M', '%I:%M:%S %p', '%I:%M %p'):
                try:
                    return datetime.datetime.strptime(val_str, fmt).time()
                except ValueError:
                    continue
            
            # General fallback using pandas
            try:
                return pd.to_datetime(val_str, errors='raise').time()
            except Exception:
                return None
                
        converted_times = original_times.apply(parse_time)
        failed_mask = original_times.notna() & converted_times.isna()
        failed_indices = cleaned_df[failed_mask].index.tolist()
        
        for idx in failed_indices:
            failed_times.append({
                "row_index": idx,
                "original_value": str(cleaned_df.loc[idx, 'order_time'])
            })
        cleaned_df['order_time'] = converted_times
        
    # 6. Detect impossible values: negative order_value, quantity, delivery_time_minutes. Cap at 0.
    impossible_capped = {}
    cap_columns = ["order_value", "quantity", "delivery_time_minutes"]
    for col in cap_columns:
        if col in cleaned_df.columns:
            if pd.api.types.is_numeric_dtype(cleaned_df[col]):
                neg_mask = cleaned_df[col] < 0
                neg_count = int(neg_mask.sum())
                if neg_count > 0:
                    cleaned_df.loc[neg_mask, col] = 0
                impossible_capped[col] = neg_count
            else:
                impossible_capped[col] = 0

    # 7. Outlier detection on order_value and delivery_time_minutes using IQR.
    cleaned_df['is_outlier'] = False
    outlier_stats = {
        "order_value": 0,
        "delivery_time_minutes": 0,
        "total": 0
    }
    
    outlier_cols = ["order_value", "delivery_time_minutes"]
    for col in outlier_cols:
        if col in cleaned_df.columns and pd.api.types.is_numeric_dtype(cleaned_df[col]):
            q1 = cleaned_df[col].quantile(0.25)
            q3 = cleaned_df[col].quantile(0.75)
            iqr = q3 - q1
            lower_bound = q1 - 1.5 * iqr
            upper_bound = q3 + 1.5 * iqr
            
            outlier_mask = (cleaned_df[col] < lower_bound) | (cleaned_df[col] > upper_bound)
            outlier_stats[col] = int(outlier_mask.sum())
            cleaned_df['is_outlier'] = cleaned_df['is_outlier'] | outlier_mask
            
    outlier_stats["total"] = int(cleaned_df['is_outlier'].sum())
    
    # Construct final report dictionary
    cleaning_report = {
        "initial_rows": initial_rows,
        "cleaned_rows": len(cleaned_df),
        "duplicates_removed": duplicates_removed,
        "missing_values_imputed": missing_imputed,
        "failed_conversions": {
            "order_date": failed_dates,
            "order_time": failed_times
        },
        "impossible_values_capped": impossible_capped,
        "outliers_detected": outlier_stats
    }
    
    return cleaned_df, cleaning_report
