import logging
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import Dict, Any
from app.services.visualization_recommendation import recommend_visualizations
from app.services.dashboard_planning import generate_dashboard_plan

router = APIRouter(prefix="/visualizations")
logger = logging.getLogger("dataset_profiler")

class VisualizationRequest(BaseModel):
    pipeline_result: Dict[str, Any]


@router.post("/recommend")
def get_recommendations(request: VisualizationRequest):
    """
    Returns deterministic, rule-based chart recommendations
    based exclusively on columns, datatypes, cardinalities, and selected KPIs.
    """
    try:
        recommendations = recommend_visualizations(request.pipeline_result)
        return {"recommendations": recommendations}
    except Exception as e:
        logger.error(f"Error in get_recommendations route: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/plan")
def get_dashboard_plan(request: VisualizationRequest):
    """
    Generates a structured, schema-agnostic Dashboard Plan containing card grids,
    chart panels, interactive filters, and fallback table definitions.
    """
    try:
        from app.services.orchestrator import PipelineOrchestrator
        plan = PipelineOrchestrator.generate_dashboard_plan_with_data(request.pipeline_result)
        
        # Save completed analysis result to session_store
        session_id = request.pipeline_result.get("session_id")
        if session_id:
            from app.services.data_ingestion import get_session_data
            df = get_session_data(session_id)
            dataset_name = df.attrs.get("dataset_name", "Unknown Dataset") if df is not None else "Unknown Dataset"
            
            from app.services.session_store.analysis_store import analysis_store
            analysis_store.save(session_id, {
                "dataset_name": dataset_name,
                "dataset_profile": request.pipeline_result.get("dataset_profile"),
                "confirmed_semantic_mapping": request.pipeline_result.get("confirmed_semantic_mapping"),
                "domain_profile": request.pipeline_result.get("domain_profile"),
                "selected_kpis": request.pipeline_result.get("selected_kpis", {}).get("selected_kpis", []),
                "dashboard_plan": plan["dashboard"],
                "visualization_recommendations": request.pipeline_result.get("visualization_recommendations", []),
                "insights": request.pipeline_result.get("insights", {})
            })
            
        return plan
    except Exception as e:
        logger.error(f"Error in get_dashboard_plan route: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
