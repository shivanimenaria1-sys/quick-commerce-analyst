import logging
from typing import List, Dict, Any

logger = logging.getLogger("dataset_profiler")

def get_columns_with_role(mapping: dict, role: str) -> List[str]:
    cols = []
    columns_mapping = mapping.get("columns", mapping)
    for col_name, col_data in columns_mapping.items():
        curr_role = col_data if isinstance(col_data, str) else col_data.get("semantic_role", "")
        if curr_role == role:
            cols.append(col_name)
    return cols

def get_column_cardinality(profile: dict, col_name: str) -> int:
    col_data = profile.get("columns", {}).get(col_name, {})
    stats = col_data.get("statistics", {})
    
    # Check unique value count
    val_count = stats.get("unique_value_count")
    if val_count is not None:
        return int(val_count)
        
    # Check top frequencies size
    top_freqs = stats.get("top_frequencies", {})
    if top_freqs:
        return len(top_freqs)
        
    return 10  # Reasonable fallback

def recommend_visualizations(pipeline_result: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Completely deterministic, rule-based visualization recommendation engine.
    Derived ONLY from semantic roles, cardinality stats, and KPI selections.
    """
    logger.info("Executing Visualization Recommendation Engine...")
    
    profile = pipeline_result.get("dataset_profile", {})
    mapping = pipeline_result.get("confirmed_semantic_mapping", {})
    selected_kpis = pipeline_result.get("selected_kpis", {}).get("selected_kpis", [])
    
    # Get active/selected KPI IDs
    kpi_ids = [k["id"] for k in selected_kpis if k.get("selected", True)]
    if not kpi_ids:
        # Fallback if no specific KPIs are active, inspect candidate KPIs
        kpi_ids = [k["id"] for k in pipeline_result.get("candidate_kpis", {}).get("candidate_kpis", [])]
        
    recommendations = []
    
    # Extract roles
    date_cols = get_columns_with_role(mapping, "date_like") + get_columns_with_role(mapping, "datetime_like")
    rev_cols = get_columns_with_role(mapping, "revenue_like")
    cost_cols = get_columns_with_role(mapping, "cost_like")
    cat_cols = get_columns_with_role(mapping, "category_like")
    loc_cols = get_columns_with_role(mapping, "location_like")
    status_cols = get_columns_with_role(mapping, "status_like")
    
    # 1. Trend Analysis: date_like + numeric KPIs
    if date_cols and kpi_ids:
        date_col = date_cols[0]
        for kpi in kpi_ids:
            recommendations.append({
                "chart_id": f"trend_{date_col}_{kpi}",
                "chart_type": "line",
                "reason": f"Trend Analysis: Detected '{date_col}' (date_like) and KPI metric '{kpi}'.",
                "required_roles": ["date_like"],
                "required_kpis": [kpi],
                "priority": 1,
                "drilldown_supported": True,
                "dimensions": [date_col]
            })

    # 2. Categorical Analysis: categorical + numeric KPIs
    # Check both category_like and status_like
    all_categorical_cols = cat_cols + status_cols
    for col in all_categorical_cols:
        cardinality = get_column_cardinality(profile, col)
        
        for kpi in kpi_ids:
            if cardinality <= 7:
                # Cardinality <= 7 -> Pie chart is suitable
                recommendations.append({
                    "chart_id": f"pie_{col}_{kpi}",
                    "chart_type": "pie",
                    "reason": f"Category Share: Detected low-cardinality category '{col}' ({cardinality} values) and KPI '{kpi}'.",
                    "required_roles": ["category_like"],
                    "required_kpis": [kpi],
                    "priority": 2,
                    "dimensions": [col]
                })
            elif cardinality <= 15:
                # Cardinality <= 15 -> Standard Bar chart
                recommendations.append({
                    "chart_id": f"bar_{col}_{kpi}",
                    "chart_type": "bar",
                    "reason": f"Category Distribution: Detected category '{col}' ({cardinality} values) and KPI '{kpi}'.",
                    "required_roles": ["category_like"],
                    "required_kpis": [kpi],
                    "priority": 2,
                    "dimensions": [col]
                })
            else:
                # Cardinality > 15 -> Top-N Bar Chart / Treemap (Strictly NO pie chart!)
                recommendations.append({
                    "chart_id": f"treemap_{col}_{kpi}",
                    "chart_type": "treemap",
                    "reason": f"High Cardinality Category: Detected high-cardinality category '{col}' ({cardinality} values; Pie Chart forbidden) and KPI '{kpi}'. Recommending Treemap visualization.",
                    "required_roles": ["category_like"],
                    "required_kpis": [kpi],
                    "priority": 3,
                    "dimensions": [col]
                })

    # 3. Location Performance: location_like + numeric KPIs
    for col in loc_cols:
        cardinality = get_column_cardinality(profile, col)
        
        # Check geographical metadata flag (default: False for mock data)
        has_geo_metadata = False
        
        for kpi in kpi_ids:
            if has_geo_metadata:
                recommendations.append({
                    "chart_id": f"choropleth_{col}_{kpi}",
                    "chart_type": "choropleth",
                    "reason": f"Geographic Distribution: Geographic metadata found for location '{col}'. Recommending Choropleth.",
                    "required_roles": ["location_like"],
                    "required_kpis": [kpi],
                    "priority": 2,
                    "dimensions": [col]
                })
            else:
                recommendations.append({
                    "chart_id": f"bar_grouped_{col}_{kpi}",
                    "chart_type": "bar",
                    "reason": f"Location Performance: Detected location '{col}' ({cardinality} values) and KPI '{kpi}'. Recommending grouped bar chart.",
                    "required_roles": ["location_like"],
                    "required_kpis": [kpi],
                    "priority": 2,
                    "dimensions": [col]
                })

    # 4. Numeric Distributions: numeric column properties
    numeric_cols = get_columns_with_role(mapping, "revenue_like") + get_columns_with_role(mapping, "cost_like") + get_columns_with_role(mapping, "duration_like")
    for col in numeric_cols:
        # Histogram
        recommendations.append({
            "chart_id": f"histogram_{col}",
            "chart_type": "histogram",
            "reason": f"Numeric distribution histogram for value dispersion analysis of '{col}'.",
            "required_roles": ["revenue_like"],
            "required_kpis": [],
            "priority": 3,
            "dimensions": [col]
        })
        
        # Boxplot (if quartiles exist in profile stats)
        col_data = profile.get("columns", {}).get(col, {})
        stats = col_data.get("statistics", {})
        if stats.get("median") is not None:
            recommendations.append({
                "chart_id": f"boxplot_{col}",
                "chart_type": "boxplot",
                "reason": f"Box Plot analysis for outlier detection and quartile distribution of '{col}'.",
                "required_roles": ["revenue_like"],
                "required_kpis": [],
                "priority": 3,
                "dimensions": [col]
            })

    # Two Numeric columns -> Scatter Plot
    if len(numeric_cols) >= 2:
        recommendations.append({
            "chart_id": f"scatter_{numeric_cols[0]}_{numeric_cols[1]}",
            "chart_type": "scatter",
            "reason": f"Scatter Plot: Investigating distribution correlation between '{numeric_cols[0]}' and '{numeric_cols[1]}'.",
            "required_roles": ["revenue_like", "cost_like"],
            "required_kpis": [],
            "priority": 3,
            "dimensions": [numeric_cols[0], numeric_cols[1]]
        })

    # Correlation Heatmap if >= 3 numeric columns
    if len(numeric_cols) >= 3:
        recommendations.append({
            "chart_id": "correlation_heatmap",
            "chart_type": "heatmap",
            "reason": f"Correlation Heatmap: Plotting multivariable dependency correlations across {len(numeric_cols)} numeric fields.",
            "required_roles": ["revenue_like"],
            "required_kpis": [],
            "priority": 3,
            "dimensions": numeric_cols
        })
        
    logger.info(f"Visualization recommendation complete. Total recommendations: {len(recommendations)}.")
    return recommendations
