import logging
from typing import Dict, Any, List
from app.services.visualization_recommendation.recommender import recommend_visualizations, get_columns_with_role

logger = logging.getLogger("dataset_profiler")

def generate_dashboard_plan(pipeline_result: Dict[str, Any], recommendations: List[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Generates a structured, schema-agnostic Dashboard Plan containing KPI cards,
    charts, dynamic filters, and detailed fallback tables. Hides empty sections automatically.
    """
    logger.info("Executing Dashboard Planning Engine...")
    
    profile = pipeline_result.get("dataset_profile", {})
    mapping = pipeline_result.get("confirmed_semantic_mapping", {})
    selected_kpis = pipeline_result.get("selected_kpis", {}).get("selected_kpis", [])
    
    # 1. Recommendations compilation
    if recommendations is None:
        recommendations = recommend_visualizations(pipeline_result)
    
    # 2. Dynamic KPI Cards
    kpi_cards = []
    active_kpis = [k for k in selected_kpis if k.get("selected", True)]
    if not active_kpis:
        active_kpis = pipeline_result.get("candidate_kpis", {}).get("candidate_kpis", [])[:4]
        
    for kpi in active_kpis:
        kpi_cards.append({
            "card_id": f"card_{kpi['id']}",
            "kpi_id": kpi["id"],
            "display_label": kpi.get("display_name", kpi["id"]),
            "aggregation": kpi.get("aggregation", "SUM"),
            "section": "Overview"
        })

    # 3. Dynamic Filters based on semantic roles
    filters = []
    date_cols = get_columns_with_role(mapping, "date_like") + get_columns_with_role(mapping, "datetime_like")
    cat_cols = get_columns_with_role(mapping, "category_like")
    loc_cols = get_columns_with_role(mapping, "location_like")
    status_cols = get_columns_with_role(mapping, "status_like")
    bool_cols = get_columns_with_role(mapping, "boolean_flag_like")
    
    for col in date_cols:
        filters.append({
            "filter_id": f"filter_{col}",
            "column_name": col,
            "control_type": "date_picker",
            "semantic_role": "date_like"
        })
    for col in cat_cols:
        filters.append({
            "filter_id": f"filter_{col}",
            "column_name": col,
            "control_type": "dropdown",
            "semantic_role": "category_like"
        })
    for col in loc_cols:
        filters.append({
            "filter_id": f"filter_{col}",
            "column_name": col,
            "control_type": "dropdown",
            "semantic_role": "location_like"
        })
    for col in status_cols:
        filters.append({
            "filter_id": f"filter_{col}",
            "column_name": col,
            "control_type": "multi_select",
            "semantic_role": "status_like"
        })
    for col in bool_cols:
        filters.append({
            "filter_id": f"filter_{col}",
            "column_name": col,
            "control_type": "toggle",
            "semantic_role": "boolean_like"
        })

    # 4. Map Charts to target dashboard sections
    charts = []
    
    # Active sections tracking
    active_sections = set()
    if kpi_cards:
        active_sections.add("Overview")
        
    for rec in recommendations:
        c_type = rec["chart_type"]
        chart_id = rec["chart_id"]
        
        # Segment section dynamically based on type and roles
        section = "Trend Analysis"
        if "pie" in chart_id or "bar" in chart_id or "treemap" in chart_id:
            # Check if this dimension is location
            has_loc = False
            for dim in rec.get("dimensions", []):
                if dim in loc_cols:
                    has_loc = True
            
            if has_loc:
                section = "Location Analysis"
            else:
                section = "Category Analysis"
        elif c_type in ("histogram", "boxplot", "scatter", "heatmap"):
            section = "Distribution Analysis"
            
        active_sections.add(section)
        
        chart_dict = {
            "id": chart_id,
            "chart_id": chart_id,
            "chart_type": c_type,
            "display_label": rec["reason"].split(":")[0] if "reason" in rec else chart_id,
            "reason": rec.get("reason", ""),
            "required_kpis": rec.get("required_kpis", []),
            "required_roles": rec.get("required_roles", []),
            "priority": rec.get("priority", 3),
            "section": section,
            "dimensions": rec.get("dimensions", [])
        }
        if "chart_data" in rec:
            chart_dict["chart_data"] = rec["chart_data"]
            
        charts.append(chart_dict)

    # 5. Detail table / Fallback Explorable widgets
    # Every dataset has a detail table configuration
    columns_headers = list(profile.get("columns", {}).keys())
    tables = [
        {
            "table_id": "detail_explorer_table",
            "display_label": "Detailed Dataset Explorer",
            "columns": columns_headers,
            "searchable": True,
            "sortable": True,
            "section": "Detail Tables"
        }
    ]
    active_sections.add("Detail Tables")

    # Compile the final plan, tracking sections
    dashboard_plan = {
        "dashboard": {
            "kpi_cards": kpi_cards,
            "charts": charts,
            "filters": filters,
            "tables": tables,
            "metadata": {
                "active_sections": sorted(list(active_sections)),
                "total_widgets": len(kpi_cards) + len(charts) + len(filters) + len(tables)
            }
        }
    }
    
    logger.info("Dashboard planning completed successfully.")
    return dashboard_plan
