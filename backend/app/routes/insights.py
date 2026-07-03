from fastapi import APIRouter, HTTPException, status
from app.services.data_ingestion import sessions
from app.services.data_cleaning import clean_dataset
from app.services.feature_engineering import engineer_features
from app.services.kpi_engine import calculate_kpis
from app.services.insight_generator import generate_insights, insights_cache

router = APIRouter()

@router.get("/insights/{session_id}")
def get_session_insights(session_id: str):
    """
    Returns AI-generated business insights for the given session_id.
    Uses in-memory cache to prevent duplicate LLM requests.
    """
    # 1. Check in-memory cache first
    if session_id in insights_cache:
        return insights_cache[session_id]
        
    # 2. Check if session exists in the main store
    if session_id not in sessions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session with ID {session_id} not found."
        )
        
    df = sessions[session_id]
    
    try:
        # 3. Ensure dataframe is cleaned and engineered
        is_cleaned = 'is_outlier' in df.columns
        is_engineered = 'is_delayed' in df.columns
        
        if not is_cleaned:
            df, _ = clean_dataset(df)
            sessions[session_id] = df
            
        if not is_engineered:
            df, _ = engineer_features(df)
            sessions[session_id] = df
            
        # 4. Calculate KPIs
        kpis = calculate_kpis(df)
        
        # 5. Generate AI insights
        insights = generate_insights(kpis)
        
        # 6. Cache the insights for subsequent requests
        insights_cache[session_id] = insights
        
        return insights
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error occurred during insight generation: {str(e)}"
        )
