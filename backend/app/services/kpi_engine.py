import numpy as np
import pandas as pd
from typing import Dict, Any, List

def round_numeric_data(data: Any) -> Any:
    """
    Recursively traverses dictionaries, lists, and primitives to:
    1. Round all floats to 2 decimal places.
    2. Convert Pandas/NumPy types (e.g. np.float64, np.int64) to native Python types.
    3. Safely map NaNs or NaTs to None (JSON null).
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

def calculate_kpis(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Calculates structured business KPIs grouped by category from the quick commerce dataset.
    Rounds all numeric metrics to 2 decimal places.
    """
    if df.empty:
        return {
            "customer_kpis": {"total_customers": 0, "repeat_customer_rate": 0.0, "avg_orders_per_customer": 0.0},
            "order_kpis": {"total_orders": 0, "avg_order_value": 0.0, "cancellation_rate": 0.0, "return_rate": 0.0},
            "revenue_kpis": {"total_revenue": 0.0, "revenue_by_category": {}, "revenue_by_city": {}, "revenue_by_time_slot": {}, "revenue_by_day_of_week": {}},
            "delivery_kpis": {"avg_delivery_time": 0.0, "on_time_delivery_rate": 0.0, "delayed_order_rate": 0.0},
            "unit_economics_kpis": {"avg_profit_margin_per_order": 0.0, "low_margin_order_pct": 0.0, "total_estimated_profit": 0.0, "delivery_cost_as_pct_of_order_value": 0.0},
            "hyperlocal_kpis": {"orders_by_pincode": {}, "orders_per_dark_store": {}, "underserved_pincodes": []},
            "rider_kpis": {"avg_rider_utilization_pct": 0.0, "top_10_riders_by_orders": {}, "low_utilization_rider_pct": 0.0},
            "satisfaction_kpis": {"avg_customer_rating": 0.0, "rating_trend_by_month": {}, "cancellation_reason_breakdown": {}}
        }

    # 1. Customer KPIs
    total_cust = int(df['customer_id'].nunique()) if 'customer_id' in df.columns else 0
    if total_cust > 0 and 'customer_id' in df.columns:
        cust_counts = df['customer_id'].value_counts()
        repeat_cust_count = int((cust_counts > 1).sum())
        repeat_customer_rate = (repeat_cust_count / total_cust) * 100.0
        avg_orders_per_customer = len(df) / total_cust
    else:
        repeat_customer_rate = 0.0
        avg_orders_per_customer = 0.0
        
    customer_kpis = {
        "total_customers": total_cust,
        "repeat_customer_rate": repeat_customer_rate,
        "avg_orders_per_customer": avg_orders_per_customer
    }

    # 2. Order KPIs
    total_orders = len(df)
    avg_order_value = float(df['order_value'].mean()) if 'order_value' in df.columns else 0.0
    
    cancellation_rate = 0.0
    return_rate = 0.0
    if total_orders > 0 and 'order_status' in df.columns:
        statuses = df['order_status'].astype(str).str.title()
        cancelled_count = int((statuses == 'Cancelled').sum())
        returned_count = int((statuses == 'Returned').sum())
        cancellation_rate = (cancelled_count / total_orders) * 100.0
        return_rate = (returned_count / total_orders) * 100.0
        
    order_kpis = {
        "total_orders": total_orders,
        "avg_order_value": avg_order_value,
        "cancellation_rate": cancellation_rate,
        "return_rate": return_rate
    }

    # 3. Revenue KPIs
    total_revenue = float(df['order_value'].sum()) if 'order_value' in df.columns else 0.0
    revenue_by_category = df.groupby('category')['order_value'].sum().to_dict() if 'category' in df.columns and 'order_value' in df.columns else {}
    revenue_by_city = df.groupby('city')['order_value'].sum().to_dict() if 'city' in df.columns and 'order_value' in df.columns else {}
    revenue_by_time_slot = df.groupby('time_slot')['order_value'].sum().to_dict() if 'time_slot' in df.columns and 'order_value' in df.columns else {}
    revenue_by_day_of_week = df.groupby('order_day_of_week')['order_value'].sum().to_dict() if 'order_day_of_week' in df.columns and 'order_value' in df.columns else {}
    
    revenue_kpis = {
        "total_revenue": total_revenue,
        "revenue_by_category": revenue_by_category,
        "revenue_by_city": revenue_by_city,
        "revenue_by_time_slot": revenue_by_time_slot,
        "revenue_by_day_of_week": revenue_by_day_of_week
    }

    # 4. Delivery KPIs
    avg_delivery_time = float(df['delivery_time_minutes'].mean()) if 'delivery_time_minutes' in df.columns else 0.0
    
    on_time_delivery_rate = 0.0
    delayed_order_rate = 0.0
    if total_orders > 0 and 'is_delayed' in df.columns:
        delayed_count = int((df['is_delayed'] == True).sum())
        on_time_count = int((df['is_delayed'] == False).sum())
        delayed_order_rate = (delayed_count / total_orders) * 100.0
        on_time_delivery_rate = (on_time_count / total_orders) * 100.0
        
    delivery_kpis = {
        "avg_delivery_time": avg_delivery_time,
        "on_time_delivery_rate": on_time_delivery_rate,
        "delayed_order_rate": delayed_order_rate
    }

    # 5. Unit Economics KPIs
    avg_profit_margin_per_order = float(df['estimated_profit_margin'].mean()) if 'estimated_profit_margin' in df.columns else 0.0
    total_estimated_profit = float(df['estimated_profit_margin'].sum()) if 'estimated_profit_margin' in df.columns else 0.0
    
    low_margin_order_pct = 0.0
    if total_orders > 0 and 'is_low_margin_order' in df.columns:
        low_margin_count = int((df['is_low_margin_order'] == True).sum())
        low_margin_order_pct = (low_margin_count / total_orders) * 100.0
        
    delivery_cost_as_pct_of_order_value = 0.0
    if 'estimated_fulfillment_cost' in df.columns and 'order_value' in df.columns:
        total_order_val = df['order_value'].sum()
        if total_order_val > 0.0:
            total_fulfillment_cost = df['estimated_fulfillment_cost'].sum()
            delivery_cost_as_pct_of_order_value = (total_fulfillment_cost / total_order_val) * 100.0
            
    unit_economics_kpis = {
        "avg_profit_margin_per_order": avg_profit_margin_per_order,
        "low_margin_order_pct": low_margin_order_pct,
        "total_estimated_profit": total_estimated_profit,
        "delivery_cost_as_pct_of_order_value": delivery_cost_as_pct_of_order_value
    }

    # 6. Hyperlocal KPIs
    orders_by_pincode = df['pincode'].value_counts().to_dict() if 'pincode' in df.columns else {}
    orders_per_dark_store = df['dark_store_id'].value_counts().to_dict() if 'dark_store_id' in df.columns else {}
    
    underserved_pincodes: List[str] = []
    if 'pincode' in df.columns and 'delivery_time_minutes' in df.columns:
        p75 = df['delivery_time_minutes'].quantile(0.75)
        if not pd.isna(p75):
            avg_delivery_by_pincode = df.groupby('pincode')['delivery_time_minutes'].mean()
            underserved_pincodes = avg_delivery_by_pincode[avg_delivery_by_pincode > p75].index.tolist()
            
    hyperlocal_kpis = {
        "orders_by_pincode": orders_by_pincode,
        "orders_per_dark_store": orders_per_dark_store,
        "underserved_pincodes": underserved_pincodes
    }

    # 7. Rider KPIs
    avg_rider_utilization_pct = 0.0
    low_utilization_rider_pct = 0.0
    top_10_riders_by_orders = {}
    
    if 'delivery_partner_id' in df.columns:
        top_10_riders_by_orders = df['delivery_partner_id'].value_counts().head(10).to_dict()
        
        if 'rider_utilization_pct' in df.columns:
            # Aggregate utilization per unique rider
            rider_util = df.groupby('delivery_partner_id')['rider_utilization_pct'].mean()
            if not rider_util.empty:
                avg_rider_utilization_pct = float(rider_util.mean())
                low_util_count = int((rider_util < 50.0).sum())
                low_utilization_rider_pct = (low_util_count / len(rider_util)) * 100.0
                
    rider_kpis = {
        "avg_rider_utilization_pct": avg_rider_utilization_pct,
        "top_10_riders_by_orders": top_10_riders_by_orders,
        "low_utilization_rider_pct": low_utilization_rider_pct
    }

    # 8. Satisfaction KPIs
    avg_customer_rating = float(df['customer_rating'].mean()) if 'customer_rating' in df.columns else 0.0
    
    rating_trend_by_month = {}
    if 'customer_rating' in df.columns and 'order_month' in df.columns:
        rating_trend_by_month = df.groupby('order_month')['customer_rating'].mean().to_dict()
        
    cancellation_reason_breakdown = {}
    if 'cancellation_reason' in df.columns and 'order_status' in df.columns:
        cancelled_mask = df['order_status'].astype(str).str.title() == 'Cancelled'
        cancellation_reason_breakdown = df[cancelled_mask]['cancellation_reason'].value_counts().to_dict()
        
    satisfaction_kpis = {
        "avg_customer_rating": avg_customer_rating,
        "rating_trend_by_month": rating_trend_by_month,
        "cancellation_reason_breakdown": cancellation_reason_breakdown
    }

    # Construct overall KPI response
    raw_kpis = {
        "customer_kpis": customer_kpis,
        "order_kpis": order_kpis,
        "revenue_kpis": revenue_kpis,
        "delivery_kpis": delivery_kpis,
        "unit_economics_kpis": unit_economics_kpis,
        "hyperlocal_kpis": hyperlocal_kpis,
        "rider_kpis": rider_kpis,
        "satisfaction_kpis": satisfaction_kpis
    }
    
    # Recursively round all floats to 2 decimal places and return
    return round_numeric_data(raw_kpis)
