import logging
from fastapi import APIRouter, HTTPException, status
from app.services.data_ingestion import sessions
from app.services.orchestrator import PipelineOrchestrator
from app.services.dataset_profiler.parser import BaseParser
from app.services.dataset_profiler.profiler import profile_dataset
from app.services.semantic_mapper import map_semantics
from app.services.kpi_generator.generator import generate_candidate_kpis
from app.services.kpi_ranking import rank_candidate_kpis
from app.services.insight_generator.generator import generate_narrative_insights
from app.utils.serialization import clean_for_json

router = APIRouter()
logger = logging.getLogger("dataset_profiler")

@router.post("/analyze/{session_id}")
def analyze_session(session_id: str):
    """
    Orchestrates the schema-agnostic modular AI pipeline in sequence:
    1. Parsing and statistics profiling
    2. Semantic Column Mapping
    3. Domain Classification & Feature Engineering
    4. Candidate KPI Generation & LLM Ranking
    5. Insight Extraction & Gemini Narrative Generation (validated)
    Returns a combined structured JSON result payload.
    """
    if session_id not in sessions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session with ID {session_id} not found."
        )
        
    df = sessions[session_id]
    logger.info(f"Orchestrated Analysis: Initiating pipeline sequence for session '{session_id}'")
    
    try:
        # Step 1: Profile & Map
        class PreparsedParser(BaseParser):
            def __init__(self, parsed_df):
                self.parsed_df = parsed_df
            def parse(self):
                return self.parsed_df
                
        profile = profile_dataset(PreparsedParser(df))
        mapping = map_semantics(profile)
        
        # Step 2: Post-process (Domain Classification & Feature Engineering)
        domain_profile, metadata, engineered_df = PipelineOrchestrator.post_process_features(df, mapping, profile)
        sessions[session_id] = engineered_df
        
        # Step 3: Context & KPIs
        context = PipelineOrchestrator.build_context(profile, mapping, domain_profile, metadata)
        candidates = generate_candidate_kpis(context)
        ranked = rank_candidate_kpis(context, candidates)
        
        # Step 4: Insights
        pipeline_result = {
            "dataset_profile": profile,
            "confirmed_semantic_mapping": mapping,
            "domain_profile": domain_profile,
            "engineered_features": metadata,
            "selected_kpis": ranked
        }
        insights_res = generate_narrative_insights(pipeline_result)
        
        payload = {
            "status": "success",
            "dataset_profile": profile,
            "confirmed_semantic_mapping": mapping,
            "domain_profile": domain_profile,
            "selected_kpis": ranked,
            "insights": insights_res.get("insights", {})
        }
        
        return clean_for_json(payload)
        
    except Exception as e:
        logger.error(f"Orchestrated pipeline failed for session '{session_id}': {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Pipeline execution failed: {str(e)}"
        )


@router.get("/analysis/{session_id}")
def get_completed_analysis(session_id: str):
    """
    Exposes completed analysis (profile, semantic map, domain classification, and layout plans).
    """
    from app.services.session_store.analysis_store import analysis_store
    result = analysis_store.get(session_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Analysis session {session_id} not found."
        )
    return clean_for_json(result)


@router.get("/analysis/{session_id}/kpis")
def get_completed_analysis_kpis(session_id: str):
    """
    Exposes the KPIs computed for the completed session.
    """
    from app.services.session_store.analysis_store import analysis_store
    result = analysis_store.get(session_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Analysis session {session_id} not found."
        )
    return clean_for_json(result.get("selected_kpis", []))


@router.get("/analysis/{session_id}/visualizations")
def get_completed_analysis_visualizations(session_id: str):
    """
    Exposes layout visualization specs generated for the completed session.
    """
    from app.services.session_store.analysis_store import analysis_store
    result = analysis_store.get(session_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Analysis session {session_id} not found."
        )
    return clean_for_json(result.get("dashboard_plan", {}))

