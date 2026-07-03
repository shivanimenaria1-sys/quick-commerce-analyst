from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse
import io
from app.services.data_ingestion import sessions
from app.services.data_cleaning import clean_dataset
from app.services.feature_engineering import engineer_features
from app.services.kpi_engine import calculate_kpis
from app.services.insight_generator import generate_insights, insights_cache
from app.services.report_generator import generate_pdf_report

router = APIRouter()

@router.get("/report/{session_id}")
def download_session_report(session_id: str):
    """
    Generates a professional corporate analytics report for the given session_id.
    Runs any missing pipeline preprocessing, executes AI consulting analysis,
    and returns a downloadable file (PDF, or HTML fallback).
    """
    # 1. Retrieve the session DataFrame
    if session_id not in sessions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session with ID {session_id} not found."
        )
        
    df = sessions[session_id]
    
    try:
        # 2. Check if clean/engineer pipelines have been executed
        is_cleaned = 'is_outlier' in df.columns
        is_engineered = 'is_delayed' in df.columns
        
        if not is_cleaned:
            df, _ = clean_dataset(df)
            sessions[session_id] = df
            
        if not is_engineered:
            df, _ = engineer_features(df)
            sessions[session_id] = df
            
        # 3. Calculate KPIs
        kpis = calculate_kpis(df)
        
        # 4. Fetch or generate AI insights
        if session_id in insights_cache:
            insights = insights_cache[session_id]
        else:
            insights = generate_insights(kpis)
            insights_cache[session_id] = insights
            
        # 5. Compile report bytes and content type
        report_bytes, content_type = generate_pdf_report(kpis, insights)
        
        # 6. Set appropriate file attachment headers based on file type
        extension = "pdf" if content_type == "application/pdf" else "html"
        filename = f"diagnostic_report_{session_id[:8]}.{extension}"
        
        # 7. Write to BytesIO buffer and rewind
        buffer = io.BytesIO(report_bytes)
        buffer.seek(0)
        
        # 8. Log validation checks
        pdf_size = len(report_bytes)
        first_bytes_preview = report_bytes[:15]
        print(f"[REPORT DOWNLOAD LOG] Session: {session_id}")
        print(f"[REPORT DOWNLOAD LOG] Response Content-Type: {content_type}")
        print(f"[REPORT DOWNLOAD LOG] Generated Report Size: {pdf_size} bytes")
        print(f"[REPORT DOWNLOAD LOG] First few bytes: {first_bytes_preview}")
        
        headers = {
            "Content-Disposition": f'attachment; filename="{filename}"'
        }
        
        return StreamingResponse(buffer, media_type=content_type, headers=headers)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error occurred during report compiling: {str(e)}"
        )
