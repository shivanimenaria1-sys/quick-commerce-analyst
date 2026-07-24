import io
import logging
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from app.services.data_ingestion import sessions
from app.services.orchestrator import PipelineOrchestrator
from app.services.dataset_profiler.parser import BaseParser
from app.services.dataset_profiler.profiler import profile_dataset
from app.services.semantic_mapper import map_semantics
from app.services.kpi_generator.generator import generate_candidate_kpis
from app.services.kpi_ranking import rank_candidate_kpis
from app.services.insight_generator.generator import generate_narrative_insights
from app.services.report_generator.exporter import HTMLReportExporter, PDFReportExporter

router = APIRouter()
logger = logging.getLogger("dataset_profiler")

class InsightsRequest(BaseModel):
    pipeline_result: Dict[str, Any]

class ExportRequest(BaseModel):
    pipeline_result: Dict[str, Any]
    insights: Dict[str, Any]
    format: str = "html"  # "html" or "pdf"


@router.get("/report/{session_id}")
def download_session_report(session_id: str):
    """
    Generates a professional corporate analytics report for the given session_id.
    Runs the modern schema-agnostic pipeline and returns a downloadable PDF report.
    """
    if session_id not in sessions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session with ID {session_id} not found."
        )
        
    df = sessions[session_id]
    logger.info(f"Report Route: Compiling PDF report via modern pipeline for session '{session_id}'")
    
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
        insights = insights_res.get("insights", {})
        
        # Step 5: Export to PDF
        exporter = PDFReportExporter()
        report_bytes = exporter.export(pipeline_result, insights)
        
        buffer = io.BytesIO(report_bytes)
        buffer.seek(0)
        
        filename = f"operations_insights_report_{session_id[:8]}.pdf"
        headers = {
            "Content-Disposition": f'attachment; filename="{filename}"'
        }
        
        return StreamingResponse(buffer, media_type="application/pdf", headers=headers)
        
    except Exception as e:
        logger.error(f"Error compiling session report: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error occurred during report compiling: {str(e)}"
        )


@router.post("/report/insights")
def get_report_insights(request: InsightsRequest):
    """
    Computes deterministic insights and leverages Gemini to produce
    domain-grounded, validated narrative interpretations and suggestions.
    """
    try:
        res = generate_narrative_insights(request.pipeline_result)
        return res
    except Exception as e:
        logger.error(f"Error generating narrative report insights: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/report/export")
def export_report_file(request: ExportRequest):
    """
    Exports a domain-adaptive PDF or HTML report based on the provided pipeline
    result context and narrative insights.
    """
    try:
        if request.format == "pdf":
            exporter = PDFReportExporter()
            media_type = "application/pdf"
            filename = "operations_insights_report.pdf"
        else:
            exporter = HTMLReportExporter()
            media_type = "text/html"
            filename = "operations_insights_report.html"
            
        report_bytes = exporter.export(request.pipeline_result, request.insights)
        buffer = io.BytesIO(report_bytes)
        buffer.seek(0)
        
        headers = {
            "Content-Disposition": f'attachment; filename="{filename}"'
        }
        return StreamingResponse(buffer, media_type=media_type, headers=headers)
    except Exception as e:
        logger.error(f"Error exporting report: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
