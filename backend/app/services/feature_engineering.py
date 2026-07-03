import numpy as np
import pandas as pd
from typing import Tuple, List

def engineer_features(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
    """
    Computes derived features for analytics:
    - Date/Time: day of week name, month index, weekend flag, hour, time slot.
    - Customer: customer order frequencies, customer tenure (if signup_date exists).
    - Delivery: delays, delayed flag.
    - Unit Economics: fulfillment cost, profit margin, low margin flag.
    - Rider: utilization percentage.
    
    Returns the enriched DataFrame and the list of new columns added.
    """
    engineered_df = df.copy()
    original_columns = set(df.columns)
    
    # 1. Date/time features (from order_date, order_time)
    if 'order_date' in engineered_df.columns:
        dates = pd.to_datetime(engineered_df['order_date'], errors='coerce')
        engineered_df['order_day_of_week'] = dates.dt.day_name()
        engineered_df['order_month'] = dates.dt.month
        engineered_df['is_weekend'] = dates.dt.dayofweek >= 5
    else:
        engineered_df['order_day_of_week'] = np.nan
        engineered_df['order_month'] = np.nan
        engineered_df['is_weekend'] = np.nan
        
    if 'order_time' in engineered_df.columns:
        def get_hour(t):
            if pd.isna(t):
                return np.nan
            if hasattr(t, 'hour'):
                return t.hour
            try:
                # String fallback parsing
                return pd.to_datetime(t, errors='coerce').hour
            except Exception:
                return np.nan
        engineered_df['order_hour'] = engineered_df['order_time'].apply(get_hour)
    else:
        engineered_df['order_hour'] = np.nan
        
    def get_time_slot(hour):
        if pd.isna(hour) or np.isnan(hour):
            return "Unknown"
        h = int(hour)
        if 5 <= h < 12:
            return "Morning"
        elif 12 <= h < 17:
            return "Afternoon"
        elif 17 <= h < 21:
            return "Evening"
        else:
            return "Night"
            
    engineered_df['time_slot'] = engineered_df['order_hour'].apply(get_time_slot)
    
    # 2. Customer features
    if 'customer_id' in engineered_df.columns:
        cust_counts = engineered_df['customer_id'].value_counts()
        engineered_df['customer_order_count'] = engineered_df['customer_id'].map(cust_counts)
    else:
        engineered_df['customer_order_count'] = np.nan
        
    if 'signup_date' in engineered_df.columns and 'order_date' in engineered_df.columns:
        order_dates = pd.to_datetime(engineered_df['order_date'], errors='coerce')
        signup_dates = pd.to_datetime(engineered_df['signup_date'], errors='coerce')
        engineered_df['customer_tenure_days'] = (order_dates - signup_dates).dt.days
        
    # 3. Delivery features
    if 'delivery_time_minutes' in engineered_df.columns and 'promised_delivery_time' in engineered_df.columns:
        engineered_df['delivery_delay_minutes'] = engineered_df['delivery_time_minutes'] - engineered_df['promised_delivery_time']
        engineered_df['is_delayed'] = engineered_df['delivery_delay_minutes'] > 0
    else:
        engineered_df['delivery_delay_minutes'] = np.nan
        engineered_df['is_delayed'] = np.nan
        
    # 4. Unit economics features
    order_val = engineered_df['order_value'].fillna(0.0) if 'order_value' in engineered_df.columns else 0.0
    del_charge = engineered_df['delivery_charge'].fillna(0.0) if 'delivery_charge' in engineered_df.columns else 0.0
    discount = engineered_df['discount_applied'].fillna(0.0) if 'discount_applied' in engineered_df.columns else 0.0
    del_time = engineered_df['delivery_time_minutes'].fillna(0.0) if 'delivery_time_minutes' in engineered_df.columns else 0.0
    
    # Packaging = 10, overhead = 5% of order_value, rider cost = ₹2/minute
    engineered_df['estimated_fulfillment_cost'] = (del_time * 2.0) + 10.0 + (order_val * 0.05)
    # Profit margin = revenue - cost
    engineered_df['estimated_profit_margin'] = (order_val + del_charge - discount) - engineered_df['estimated_fulfillment_cost']
    engineered_df['is_low_margin_order'] = engineered_df['estimated_profit_margin'] < 0.0
    
    # 5. Rider utilization features
    if 'rider_active_minutes' in engineered_df.columns and 'rider_shift_minutes' in engineered_df.columns:
        active = engineered_df['rider_active_minutes'].fillna(0.0)
        shift = engineered_df['rider_shift_minutes'].fillna(0.0)
        # Avoid divide by zero
        engineered_df['rider_utilization_pct'] = np.where(
            shift > 0.0,
            (active / shift) * 100.0,
            0.0
        )
    else:
        engineered_df['rider_utilization_pct'] = np.nan
        
    # Detect newly added columns
    new_columns = [col for col in engineered_df.columns if col not in original_columns]
    
    return engineered_df, new_columns
