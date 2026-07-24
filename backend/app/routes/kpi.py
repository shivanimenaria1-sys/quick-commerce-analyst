import logging
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import Dict, Any
from app.services.data_ingestion import sessions
from app.services.orchestrator import PipelineOrchestrator
from app.services.kpi_generator import generate_candidate_kpis, PipelineContext
from app.services.kpi_ranking import rank_candidate_kpis

router = APIRouter(prefix="/kpi")
logger = logging.getLogger("dataset_profiler")

class GenerateKPIRequest(BaseModel):
    session_id: str
    semantic_mapping: dict
    domain_profile: dict
    dataset_profile: dict

class RankKPIRequest(BaseModel):
    pipeline_context: dict
    candidate_kpis: dict


@router.post("/generate")
def generate_candidates(request: GenerateKPIRequest):
    """
    Coordinates feature engineering and compiles the unified PipelineContext to
    generate rule-based KPI candidates deterministically.
    """
    if request.session_id not in sessions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session with ID {request.session_id} not found."
        )
        
    try:
        df = sessions[request.session_id]
        
        # 1. Run post process feature engineering
        domain_profile, metadata, engineered_df = PipelineOrchestrator.post_process_features(
            df=df,
            semantic_mapping=request.semantic_mapping,
            dataset_profile=request.dataset_profile
        )
        
        # Save enriched DataFrame back to session store
        sessions[request.session_id] = engineered_df
        
        # 2. Build PipelineContext
        context = PipelineOrchestrator.build_context(
            dataset_profile=request.dataset_profile,
            semantic_mapping=request.semantic_mapping,
            domain_profile=request.domain_profile,
            engineered_features=metadata,
            session_id=request.session_id
        )
        
        # 3. Generate KPI candidates
        candidates = generate_candidate_kpis(context)
        
        return {
            "status": "success",
            "candidates": candidates,
            "pipeline_context": context.model_dump()
        }
    except Exception as e:
        logger.error(f"Error in generate_candidates route: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/rank")
def rank_candidates(request: RankKPIRequest):
    """
    Calls the LLM ranking engine to sort, relabel, and prioritize generated KPI candidates.
    Never modifies KPI calculation formulas.
    """
    try:
        # Validate PipelineContext schema
        context = PipelineContext.model_validate(request.pipeline_context)
        
        # Run ranking
        rankings = rank_candidate_kpis(context, request.candidate_kpis)
        return rankings
    except Exception as e:
        logger.error(f"Error in rank_candidates route: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
