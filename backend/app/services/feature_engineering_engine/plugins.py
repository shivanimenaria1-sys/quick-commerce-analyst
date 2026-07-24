import logging
import numpy as np
import pandas as pd
from typing import Tuple, List, Dict, Any
from app.services.feature_engineering_engine.registry import register_generator
from app.services.dataset_profiler.cleaners import clean_numeric_string, robust_parse_dates

logger = logging.getLogger("dataset_profiler")

def get_columns_by_role(semantic_mapping: dict, role: str) -> List[str]:
    """
    Finds all columns mapped to a specific semantic role.
    Supports both direct flat dictionaries and nested json structures.
    """
    cols = []
    columns_mapping = semantic_mapping
    if "columns" in semantic_mapping:
        columns_mapping = semantic_mapping["columns"]
        
    for col_name, col_data in columns_mapping.items():
        curr_role = col_data if isinstance(col_data, str) else col_data.get("semantic_role", "unknown")
        if curr_role == role:
            cols.append(col_name)
    return cols


@register_generator("date_extractor")
def extract_date_features(df: pd.DataFrame, semantic_mapping: dict) -> Tuple[pd.DataFrame, List[Dict[str, Any]]]:
    """
    Extracts chronological features from any column mapped to date_like or datetime_like.
    """
    new_cols = pd.DataFrame(index=df.index)
    metadata = []
    
    date_cols = get_columns_by_role(semantic_mapping, "date_like") + get_columns_by_role(semantic_mapping, "datetime_like")
    
    for col in date_cols:
        if col not in df.columns:
            continue
            
        try:
            # Parse robustly
            parsed_dates = robust_parse_dates(df[col])
            
            # 1. Day of Week
            day_col = f"{col}_day_of_week"
            new_cols[day_col] = parsed_dates.dt.day_name()
            # If all are NaT, day_name returns NaN
            new_cols[day_col] = new_cols[day_col].fillna("Unknown")
            metadata.append({
                "feature_name": day_col,
                "source_semantic_roles": [semantic_mapping.get("columns", {}).get(col, {}).get("semantic_role") if "columns" in semantic_mapping else "date_like"],
                "generation_rule": f"Extract day of week name from {col}",
                "output_type": "categorical"
            })
            
            # 2. Week of Year
            week_col = f"{col}_week"
            new_cols[week_col] = parsed_dates.dt.isocalendar().week.astype(float)
            metadata.append({
                "feature_name": week_col,
                "source_semantic_roles": ["date_like"],
                "generation_rule": f"Extract ISO week index from {col}",
                "output_type": "integer"
            })
            
            # 3. Month
            month_col = f"{col}_month"
            new_cols[month_col] = parsed_dates.dt.month.astype(float)
            metadata.append({
                "feature_name": month_col,
                "source_semantic_roles": ["date_like"],
                "generation_rule": f"Extract month index (1-12) from {col}",
                "output_type": "integer"
            })
            
            # 4. Quarter
            quarter_col = f"{col}_quarter"
            new_cols[quarter_col] = parsed_dates.dt.quarter.astype(float)
            metadata.append({
                "feature_name": quarter_col,
                "source_semantic_roles": ["date_like"],
                "generation_rule": f"Extract quarter index (1-4) from {col}",
                "output_type": "integer"
            })
            
            # 5. Year
            year_col = f"{col}_year"
            new_cols[year_col] = parsed_dates.dt.year.astype(float)
            metadata.append({
                "feature_name": year_col,
                "source_semantic_roles": ["date_like"],
                "generation_rule": f"Extract calendar year from {col}",
                "output_type": "integer"
            })
            
            # 6. Is Weekend
            weekend_col = f"{col}_is_weekend"
            new_cols[weekend_col] = (parsed_dates.dt.dayofweek >= 5).astype(bool)
            metadata.append({
                "feature_name": weekend_col,
                "source_semantic_roles": ["date_like"],
                "generation_rule": f"Flag weekend status (Saturday/Sunday) from {col}",
                "output_type": "boolean"
            })
            
            # 7. Season
            season_col = f"{col}_season"
            # Map month to season
            def get_season(month_val):
                if pd.isna(month_val):
                    return "Unknown"
                m = int(month_val)
                if m in (12, 1, 2):
                    return "Winter"
                elif m in (3, 4, 5):
                    return "Spring"
                elif m in (6, 7, 8):
                    return "Summer"
                else:
                    return "Autumn"
            new_cols[season_col] = new_cols[month_col].apply(get_season)
            metadata.append({
                "feature_name": season_col,
                "source_semantic_roles": ["date_like"],
                "generation_rule": f"Map calendar month of {col} to meteorological season",
                "output_type": "categorical"
            })
        except Exception as e:
            logger.error(f"Error extracting date features for '{col}': {e}")
            
    return new_cols, metadata


@register_generator("profit_margin_calculator")
def calculate_profit_and_margins(df: pd.DataFrame, semantic_mapping: dict) -> Tuple[pd.DataFrame, List[Dict[str, Any]]]:
    """
    Computes profit, profit margin, and margin risk buckets from revenue_like and cost_like columns.
    """
    new_cols = pd.DataFrame(index=df.index)
    metadata = []
    
    rev_cols = get_columns_by_role(semantic_mapping, "revenue_like")
    cost_cols = get_columns_by_role(semantic_mapping, "cost_like")
    
    if rev_cols and cost_cols:
        rev_col = rev_cols[0]
        cost_col = cost_cols[0]
        
        if rev_col in df.columns and cost_col in df.columns:
            try:
                # Clean numeric values
                rev = clean_numeric_string(df[rev_col])
                cost = clean_numeric_string(df[cost_col])
                
                # 1. Net Profit
                profit_col = "calculated_net_profit"
                new_cols[profit_col] = rev - cost
                metadata.append({
                    "feature_name": profit_col,
                    "source_semantic_roles": ["revenue_like", "cost_like"],
                    "generation_rule": f"Compute net profit as ({rev_col} - {cost_col})",
                    "output_type": "float"
                })
                
                # 2. Profit Margin percentage
                margin_col = "calculated_profit_margin_pct"
                # Handle division by zero
                margin = (new_cols[profit_col] / rev).replace([np.inf, -np.inf], np.nan).fillna(0.0)
                new_cols[margin_col] = margin * 100.0
                metadata.append({
                    "feature_name": margin_col,
                    "source_semantic_roles": ["revenue_like", "cost_like"],
                    "generation_rule": f"Compute profit margin as (({rev_col} - {cost_col}) / {rev_col}) * 100",
                    "output_type": "float"
                })
                
                # 3. Profit Margin buckets
                bucket_col = "calculated_profit_margin_bucket"
                def get_margin_bucket(m_pct):
                    if pd.isna(m_pct):
                        return "Unknown"
                    val = float(m_pct)
                    if val < 10.0:
                        return "Low Margin"
                    elif val <= 30.0:
                        return "Medium Margin"
                    else:
                        return "High Margin"
                new_cols[bucket_col] = new_cols[margin_col].apply(get_margin_bucket)
                metadata.append({
                    "feature_name": bucket_col,
                    "source_semantic_roles": ["revenue_like", "cost_like"],
                    "generation_rule": f"Bin profit margins into Low (<10%), Medium (10%-30%), or High (>30%)",
                    "output_type": "categorical"
                })
            except Exception as e:
                logger.error(f"Error computing profit/margin features: {e}")
                
    return new_cols, metadata


@register_generator("loyalty_metrics_calculator")
def calculate_loyalty_metrics(df: pd.DataFrame, semantic_mapping: dict) -> Tuple[pd.DataFrame, List[Dict[str, Any]]]:
    """
    Computes transaction frequencies and repeat flags based on customer identifiers.
    """
    new_cols = pd.DataFrame(index=df.index)
    metadata = []
    
    cust_cols = get_columns_by_role(semantic_mapping, "customer_id_like")
    for col in cust_cols:
        if col not in df.columns:
            continue
            
        try:
            # 1. Purchase frequency
            freq_col = f"{col}_frequency"
            freq_counts = df[col].value_counts()
            new_cols[freq_col] = df[col].map(freq_counts).astype(float)
            metadata.append({
                "feature_name": freq_col,
                "source_semantic_roles": ["customer_id_like"],
                "generation_rule": f"Calculate the total number of transactions matching {col}",
                "output_type": "integer"
            })
            
            # 2. Repeat Customer Flag
            repeat_col = f"{col}_is_repeat_customer"
            new_cols[repeat_col] = (new_cols[freq_col] > 1).astype(bool)
            metadata.append({
                "feature_name": repeat_col,
                "source_semantic_roles": ["customer_id_like"],
                "generation_rule": f"Flag customer as a repeat user if purchase frequency is > 1",
                "output_type": "boolean"
            })
        except Exception as e:
            logger.error(f"Error computing loyalty metrics for '{col}': {e}")
            
    return new_cols, metadata


@register_generator("rolling_operations_calculator")
def calculate_rolling_metrics(df: pd.DataFrame, semantic_mapping: dict) -> Tuple[pd.DataFrame, List[Dict[str, Any]]]:
    """
    Computes moving averages and rolling totals based on chronological date sequences.
    """
    new_cols = pd.DataFrame(index=df.index)
    metadata = []
    
    date_cols = get_columns_by_role(semantic_mapping, "date_like") + get_columns_by_role(semantic_mapping, "datetime_like")
    rev_cols = get_columns_by_role(semantic_mapping, "revenue_like")
    
    if date_cols and rev_cols:
        date_col = date_cols[0]
        rev_col = rev_cols[0]
        
        if date_col in df.columns and rev_col in df.columns:
            try:
                # We need sorted index order for correct rolling metrics
                parsed_dates = robust_parse_dates(df[date_col])
                sorted_indices = parsed_dates.sort_values().index
                
                rev_series = clean_numeric_string(df[rev_col])
                sorted_rev = rev_series.loc[sorted_indices]
                
                # 1. 7-Period Moving Average
                rolling_avg = sorted_rev.rolling(window=7, min_periods=1).mean()
                # Map back to original index
                ma_col = "calculated_revenue_moving_avg_7d"
                new_cols[ma_col] = rolling_avg.loc[df.index]
                metadata.append({
                    "feature_name": ma_col,
                    "source_semantic_roles": ["date_like", "revenue_like"],
                    "generation_rule": f"Compute 7-record moving average of {rev_col} sorted chronologically by {date_col}",
                    "output_type": "float"
                })
                
                # 2. 7-Period Rolling Total
                rolling_sum = sorted_rev.rolling(window=7, min_periods=1).sum()
                sum_col = "calculated_revenue_rolling_total_7d"
                new_cols[sum_col] = rolling_sum.loc[df.index]
                metadata.append({
                    "feature_name": sum_col,
                    "source_semantic_roles": ["date_like", "revenue_like"],
                    "generation_rule": f"Compute 7-record rolling total of {rev_col} sorted chronologically by {date_col}",
                    "output_type": "float"
                })
            except Exception as e:
                logger.error(f"Error computing rolling metrics: {e}")
                
    return new_cols, metadata


@register_generator("categorical_aggregator")
def aggregate_categorical_proportions(df: pd.DataFrame, semantic_mapping: dict) -> Tuple[pd.DataFrame, List[Dict[str, Any]]]:
    """
    Computes the statistical frequency proportion of categories or location values.
    """
    new_cols = pd.DataFrame(index=df.index)
    metadata = []
    
    cat_cols = get_columns_by_role(semantic_mapping, "category_like") + get_columns_by_role(semantic_mapping, "location_like")
    
    for col in cat_cols:
        if col not in df.columns:
            continue
            
        try:
            prop_col = f"{col}_proportion"
            val_ratios = df[col].value_counts(normalize=True).to_dict()
            new_cols[prop_col] = df[col].map(val_ratios).astype(float)
            
            metadata.append({
                "feature_name": prop_col,
                "source_semantic_roles": [semantic_mapping.get("columns", {}).get(col, {}).get("semantic_role") if "columns" in semantic_mapping else "category_like"],
                "generation_rule": f"Calculate the proportion frequency ratio of each category label in {col}",
                "output_type": "float"
            })
        except Exception as e:
            logger.error(f"Error computing categorical aggregations for '{col}': {e}")
            
    return new_cols, metadata


@register_generator("duration_bucket_generator")
def categorize_durations(df: pd.DataFrame, semantic_mapping: dict) -> Tuple[pd.DataFrame, List[Dict[str, Any]]]:
    """
    Bins duration metrics into speed buckets and maps them relative to the median.
    """
    new_cols = pd.DataFrame(index=df.index)
    metadata = []
    
    dur_cols = get_columns_by_role(semantic_mapping, "duration_like")
    for col in dur_cols:
        if col not in df.columns:
            continue
            
        try:
            cleaned_dur = clean_numeric_string(df[col]).dropna()
            if cleaned_dur.empty:
                continue
                
            median_val = cleaned_dur.median()
            
            # 1. Bins
            bucket_col = f"{col}_bucket"
            def get_duration_bucket(val):
                if pd.isna(val):
                    return "Unknown"
                v = float(val)
                if v < 15.0:
                    return "Fast (<15m)"
                elif v <= 30.0:
                    return "Standard (15m-30m)"
                else:
                    return "Delayed (>30m)"
                    
            dur_series = clean_numeric_string(df[col])
            new_cols[bucket_col] = dur_series.apply(get_duration_bucket)
            metadata.append({
                "feature_name": bucket_col,
                "source_semantic_roles": ["duration_like"],
                "generation_rule": f"Bin duration values in {col} into Fast (<15m), Standard (15m-30m), or Delayed (>30m) buckets",
                "output_type": "categorical"
            })
            
            # 2. Exceeds Median flag
            exceed_col = f"{col}_exceeds_median"
            new_cols[exceed_col] = (dur_series > median_val).astype(bool)
            metadata.append({
                "feature_name": exceed_col,
                "source_semantic_roles": ["duration_like"],
                "generation_rule": f"Flag true if the duration in {col} exceeds the dataset median ({median_val})",
                "output_type": "boolean"
            })
        except Exception as e:
            logger.error(f"Error binning durations for '{col}': {e}")
            
    return new_cols, metadata
