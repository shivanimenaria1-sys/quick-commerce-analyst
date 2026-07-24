import logging
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import Dict, Any
from app.services.insight_generator.generator import generate_narrative_insights

router = APIRouter(prefix="/insights")
logger = logging.getLogger("dataset_profiler")

class InsightsRequest(BaseModel):
    pipeline_result: Dict[str, Any]

@router.post("")
@router.post("/")
def get_narrative_report_insights(request: InsightsRequest):
    """
    Consumes a PipelineResult containing profiles, semantic mapping, domain classification,
    and ranked KPIs, and generates domain-grounded narrative insights.
    """
    try:
        logger.info("Insights Route: Generating narrative insights from pipeline results.")
        res = generate_narrative_insights(request.pipeline_result)
        return res
    except Exception as e:
        logger.error(f"Error generating narrative insights: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
