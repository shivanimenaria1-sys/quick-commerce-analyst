import logging
from typing import List, Dict, Any
from app.services.kpi_generator.context import PipelineContext
from app.services.kpi_generator.registry import register_kpi_generator

logger = logging.getLogger("dataset_profiler")

def get_columns_with_role(mapping: dict, role: str) -> List[str]:
    cols = []
    columns_mapping = mapping.get("columns", mapping)
    for col_name, col_data in columns_mapping.items():
        curr_role = col_data if isinstance(col_data, str) else col_data.get("semantic_role", "")
        if curr_role == role:
            cols.append(col_name)
    return cols

def has_role(mapping: dict, role: str) -> bool:
    return len(get_columns_with_role(mapping, role)) > 0


@register_kpi_generator("revenue_cost_plugin")
def generate_revenue_and_cost_kpis(context: PipelineContext) -> List[Dict[str, Any]]:
    """
    Generates revenue, cost, profit, and margin candidates.
    """
    candidates = []
    mapping = context.confirmed_semantic_mapping
    
    has_rev = has_role(mapping, "revenue_like")
    has_cost = has_role(mapping, "cost_like")
    has_qty = has_role(mapping, "quantity_like")
    has_date = has_role(mapping, "date_like") or has_role(mapping, "datetime_like")
    
    # 1. Revenue only
    if has_rev:
        candidates.append({
            "id": "total_revenue",
            "display_name": "Total Revenue",
            "required_semantic_roles": ["revenue_like"],
            "formula": {"operation": "SUM", "fields": ["revenue_like"]},
            "aggregation": "SUM",
            "confidence": 1.0,
            "generator_plugin": "revenue_cost_plugin",
            "explanation": "Calculates the sum of all transaction revenue fields.",
            "dependencies": []
        })
        candidates.append({
            "id": "average_revenue",
            "display_name": "Average Revenue",
            "required_semantic_roles": ["revenue_like"],
            "formula": {"operation": "AVG", "fields": ["revenue_like"]},
            "aggregation": "AVG",
            "confidence": 1.0,
            "generator_plugin": "revenue_cost_plugin",
            "explanation": "Calculates the average transaction value of revenue fields.",
            "dependencies": []
        })
        candidates.append({
            "id": "revenue_distribution",
            "display_name": "Revenue Distribution",
            "required_semantic_roles": ["revenue_like"],
            "formula": {"operation": "DISTRIBUTION", "fields": ["revenue_like"]},
            "aggregation": "DISTRIBUTION",
            "confidence": 1.0,
            "generator_plugin": "revenue_cost_plugin",
            "explanation": "Renders transaction counts across dynamic revenue brackets.",
            "dependencies": []
        })
        
    # 2. Cost only
    if has_cost:
        candidates.append({
            "id": "total_cost",
            "display_name": "Total Cost",
            "required_semantic_roles": ["cost_like"],
            "formula": {"operation": "SUM", "fields": ["cost_like"]},
            "aggregation": "SUM",
            "confidence": 1.0,
            "generator_plugin": "revenue_cost_plugin",
            "explanation": "Calculates the sum of all operational cost fields.",
            "dependencies": []
        })
        candidates.append({
            "id": "average_cost",
            "display_name": "Average Cost",
            "required_semantic_roles": ["cost_like"],
            "formula": {"operation": "AVG", "fields": ["cost_like"]},
            "aggregation": "AVG",
            "confidence": 1.0,
            "generator_plugin": "revenue_cost_plugin",
            "explanation": "Calculates the average operational cost value.",
            "dependencies": []
        })

    # 3. Revenue + Cost combined
    if has_rev and has_cost:
        candidates.append({
            "id": "gross_profit",
            "display_name": "Gross Profit",
            "required_semantic_roles": ["revenue_like", "cost_like"],
            "formula": {"operation": "SUBTRACT", "fields": ["revenue_like", "cost_like"]},
            "aggregation": "SUM",
            "confidence": 1.0,
            "generator_plugin": "revenue_cost_plugin",
            "explanation": "Derived as total revenue minus total cost.",
            "dependencies": ["total_revenue", "total_cost"]
        })
        candidates.append({
            "id": "profit_margin",
            "display_name": "Profit Margin",
            "required_semantic_roles": ["revenue_like", "cost_like"],
            "formula": {"operation": "RATIO_PERCENT", "fields": ["gross_profit", "revenue_like"]},
            "aggregation": "RATE",
            "confidence": 1.0,
            "generator_plugin": "revenue_cost_plugin",
            "explanation": "Profit margin percentage calculated from profit and revenue.",
            "dependencies": ["gross_profit", "total_revenue"]
        })
        candidates.append({
            "id": "cost_ratio",
            "display_name": "Cost Ratio",
            "required_semantic_roles": ["revenue_like", "cost_like"],
            "formula": {"operation": "RATIO", "fields": ["cost_like", "revenue_like"]},
            "aggregation": "RATIO",
            "confidence": 1.0,
            "generator_plugin": "revenue_cost_plugin",
            "explanation": "Measures total cost divided by total revenue.",
            "dependencies": ["total_cost", "total_revenue"]
        })

    # 4. Revenue + Quantity
    if has_rev and has_qty:
        candidates.append({
            "id": "average_order_value",
            "display_name": "Average Order Value",
            "required_semantic_roles": ["revenue_like", "quantity_like"],
            "formula": {"operation": "RATIO", "fields": ["revenue_like", "quantity_like"]},
            "aggregation": "RATIO",
            "confidence": 1.0,
            "generator_plugin": "revenue_cost_plugin",
            "explanation": "Measures transaction value divided by purchased units.",
            "dependencies": []
        })
        candidates.append({
            "id": "revenue_per_unit",
            "display_name": "Revenue per Unit",
            "required_semantic_roles": ["revenue_like", "quantity_like"],
            "formula": {"operation": "RATIO", "fields": ["revenue_like", "quantity_like"]},
            "aggregation": "RATIO",
            "confidence": 1.0,
            "generator_plugin": "revenue_cost_plugin",
            "explanation": "Calculates revenue generated per unit sold.",
            "dependencies": []
        })

    # 5. Revenue + Date Trend
    if has_rev and has_date:
        candidates.append({
            "id": "revenue_trend",
            "display_name": "Revenue Trend",
            "required_semantic_roles": ["revenue_like", "date_like"],
            "formula": {"operation": "GROUP_TREND", "fields": ["revenue_like", "date_like"]},
            "aggregation": "TREND",
            "confidence": 1.0,
            "generator_plugin": "revenue_cost_plugin",
            "explanation": "Monitors total revenue shifts over date records.",
            "dependencies": ["total_revenue"]
        })
        candidates.append({
            "id": "revenue_growth_rate",
            "display_name": "Revenue Growth Rate",
            "required_semantic_roles": ["revenue_like", "date_like"],
            "formula": {"operation": "PERIOD_GROWTH", "fields": ["revenue_like", "date_like"]},
            "aggregation": "RATE",
            "confidence": 1.0,
            "generator_plugin": "revenue_cost_plugin",
            "explanation": "Computes period-over-period growth rate of revenue.",
            "dependencies": ["revenue_trend"]
        })
        candidates.append({
            "id": "monthly_revenue",
            "display_name": "Monthly Revenue",
            "required_semantic_roles": ["revenue_like", "date_like"],
            "formula": {"operation": "GROUP_MONTH", "fields": ["revenue_like", "date_like"]},
            "aggregation": "SUM",
            "confidence": 1.0,
            "generator_plugin": "revenue_cost_plugin",
            "explanation": "Aggregates revenue values grouped by month.",
            "dependencies": ["total_revenue"]
        })
        candidates.append({
            "id": "weekly_revenue",
            "display_name": "Weekly Revenue",
            "required_semantic_roles": ["revenue_like", "date_like"],
            "formula": {"operation": "GROUP_WEEK", "fields": ["revenue_like", "date_like"]},
            "aggregation": "SUM",
            "confidence": 1.0,
            "generator_plugin": "revenue_cost_plugin",
            "explanation": "Aggregates revenue values grouped by ISO week.",
            "dependencies": ["total_revenue"]
        })
        candidates.append({
            "id": "rolling_revenue",
            "display_name": "Rolling Revenue",
            "required_semantic_roles": ["revenue_like", "date_like"],
            "formula": {"operation": "ROLLING_SUM", "fields": ["revenue_like", "date_like"]},
            "aggregation": "TREND",
            "confidence": 1.0,
            "generator_plugin": "revenue_cost_plugin",
            "explanation": "Calculates 7-record rolling total of sales revenue.",
            "dependencies": ["total_revenue"]
        })

    return candidates


@register_kpi_generator("customer_loyalty_plugin")
def generate_customer_loyalty_kpis(context: PipelineContext) -> List[Dict[str, Any]]:
    """
    Generates customer count and loyalty repeat metrics.
    """
    candidates = []
    mapping = context.confirmed_semantic_mapping
    
    if has_role(mapping, "customer_id_like"):
        candidates.append({
            "id": "customer_count",
            "display_name": "Customer Count",
            "required_semantic_roles": ["customer_id_like"],
            "formula": {"operation": "DISTINCT_COUNT", "fields": ["customer_id_like"]},
            "aggregation": "COUNT",
            "confidence": 1.0,
            "generator_plugin": "customer_loyalty_plugin",
            "explanation": "Counts unique customer identifiers.",
            "dependencies": []
        })
        candidates.append({
            "id": "repeat_customer_rate",
            "display_name": "Repeat Customer Rate",
            "required_semantic_roles": ["customer_id_like"],
            "formula": {"operation": "RATIO_PERCENT", "fields": ["repeat_customers", "total_customers"]},
            "aggregation": "RATE",
            "confidence": 1.0,
            "generator_plugin": "customer_loyalty_plugin",
            "explanation": "Percentage of unique customers with multiple transaction occurrences.",
            "dependencies": ["customer_count"]
        })
        candidates.append({
            "id": "customer_frequency",
            "display_name": "Customer Frequency",
            "required_semantic_roles": ["customer_id_like"],
            "formula": {"operation": "AVG_COUNT", "fields": ["customer_id_like"]},
            "aggregation": "AVG",
            "confidence": 1.0,
            "generator_plugin": "customer_loyalty_plugin",
            "explanation": "Measures the average number of transaction records per customer.",
            "dependencies": []
        })
        
    return candidates


@register_kpi_generator("hr_plugin")
def generate_hr_kpis(context: PipelineContext) -> List[Dict[str, Any]]:
    """
    Generates HR employee headcount and attrition metrics.
    """
    candidates = []
    mapping = context.confirmed_semantic_mapping
    
    has_emp = has_role(mapping, "employee_like")
    has_status = has_role(mapping, "status_like")
    
    if has_emp:
        candidates.append({
            "id": "headcount",
            "display_name": "Headcount",
            "required_semantic_roles": ["employee_like"],
            "formula": {"operation": "DISTINCT_COUNT", "fields": ["employee_like"]},
            "aggregation": "COUNT",
            "confidence": 1.0,
            "generator_plugin": "hr_plugin",
            "explanation": "Calculates total unique employee count.",
            "dependencies": []
        })
        
        if has_status:
            candidates.append({
                "id": "active_employees",
                "display_name": "Active Employees",
                "required_semantic_roles": ["employee_like", "status_like"],
                "formula": {"operation": "COUNT_FILTER", "fields": ["employee_like"], "filter": {"status_like": "active"}},
                "aggregation": "COUNT",
                "confidence": 1.0,
                "generator_plugin": "hr_plugin",
                "explanation": "Counts unique employees currently marked as active.",
                "dependencies": ["headcount"]
            })
            candidates.append({
                "id": "attrition_rate",
                "display_name": "Attrition Rate",
                "required_semantic_roles": ["employee_like", "status_like"],
                "formula": {"operation": "RATIO_PERCENT", "fields": ["terminated_employees", "headcount"]},
                "aggregation": "RATE",
                "confidence": 1.0,
                "generator_plugin": "hr_plugin",
                "explanation": "Percentage of employees who left the organization.",
                "dependencies": ["headcount"]
            })
            
    return candidates


@register_kpi_generator("duration_plugin")
def generate_duration_kpis(context: PipelineContext) -> List[Dict[str, Any]]:
    """
    Generates duration and SLA compliance metrics.
    """
    candidates = []
    mapping = context.confirmed_semantic_mapping
    
    if has_role(mapping, "duration_like"):
        candidates.append({
            "id": "average_duration",
            "display_name": "Average Duration",
            "required_semantic_roles": ["duration_like"],
            "formula": {"operation": "AVG", "fields": ["duration_like"]},
            "aggregation": "AVG",
            "confidence": 1.0,
            "generator_plugin": "duration_plugin",
            "explanation": "Measures average operation time duration.",
            "dependencies": []
        })
        candidates.append({
            "id": "duration_distribution",
            "display_name": "Duration Distribution",
            "required_semantic_roles": ["duration_like"],
            "formula": {"operation": "DISTRIBUTION", "fields": ["duration_like"]},
            "aggregation": "DISTRIBUTION",
            "confidence": 1.0,
            "generator_plugin": "duration_plugin",
            "explanation": "Renders transaction volumes mapped to dynamic time bins.",
            "dependencies": []
        })
        candidates.append({
            "id": "sla_compliance",
            "display_name": "SLA Compliance Candidates",
            "required_semantic_roles": ["duration_like"],
            "formula": {"operation": "PERCENT_BELOW", "fields": ["duration_like"], "threshold": 30.0},
            "aggregation": "RATE",
            "confidence": 1.0,
            "generator_plugin": "duration_plugin",
            "explanation": "Computes proportion of transactions satisfying target SLA duration (30 mins).",
            "dependencies": []
        })
        
    return candidates


@register_kpi_generator("location_plugin")
def generate_location_kpis(context: PipelineContext) -> List[Dict[str, Any]]:
    """
    Generates geographic metrics.
    """
    candidates = []
    mapping = context.confirmed_semantic_mapping
    
    if has_role(mapping, "location_like"):
        candidates.append({
            "id": "regional_performance",
            "display_name": "Regional Performance",
            "required_semantic_roles": ["location_like"],
            "formula": {"operation": "GROUP_COUNT", "fields": ["location_like"]},
            "aggregation": "DISTRIBUTION",
            "confidence": 1.0,
            "generator_plugin": "location_plugin",
            "explanation": "Segments transaction volumes by locations.",
            "dependencies": []
        })
        candidates.append({
            "id": "top_locations",
            "display_name": "Top Locations",
            "required_semantic_roles": ["location_like"],
            "formula": {"operation": "GROUP_SORT_LIMIT", "fields": ["location_like"]},
            "aggregation": "DISTRIBUTION",
            "confidence": 1.0,
            "generator_plugin": "location_plugin",
            "explanation": "Sorts and lists the highest volume locations.",
            "dependencies": ["regional_performance"]
        })
        
    return candidates


@register_kpi_generator("category_plugin")
def generate_category_kpis(context: PipelineContext) -> List[Dict[str, Any]]:
    """
    Generates category-level metrics.
    """
    candidates = []
    mapping = context.confirmed_semantic_mapping
    
    if has_role(mapping, "category_like"):
        candidates.append({
            "id": "category_performance",
            "display_name": "Category Performance",
            "required_semantic_roles": ["category_like"],
            "formula": {"operation": "GROUP_COUNT", "fields": ["category_like"]},
            "aggregation": "DISTRIBUTION",
            "confidence": 1.0,
            "generator_plugin": "category_plugin",
            "explanation": "Groups transaction volumes by category headers.",
            "dependencies": []
        })
        candidates.append({
            "id": "category_share",
            "display_name": "Category Share",
            "required_semantic_roles": ["category_like"],
            "formula": {"operation": "GROUP_PERCENT", "fields": ["category_like"]},
            "aggregation": "RATIO",
            "confidence": 1.0,
            "generator_plugin": "category_plugin",
            "explanation": "Computes proportion percentage of total count per category label.",
            "dependencies": ["category_performance"]
        })
        
    return candidates
