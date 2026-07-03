from fastapi import APIRouter, HTTPException, status
from app.services.data_ingestion import sessions
from app.services.data_cleaning import clean_dataset
from app.services.feature_engineering import engineer_features
from app.services.kpi_engine import calculate_kpis

router = APIRouter()

@router.get("/kpis/{session_id}")
def get_session_kpis(session_id: str):
    """
    Returns the KPI dictionary for the given session_id.
    Checks if the dataset has already been cleaned and engineered,
    triggers any missing pre-processing pipeline stages, and calculates
    high-level business performance metrics.
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
        
        # 3. Perform pre-processing if cached stages are missing
        if not is_cleaned:
            df, _ = clean_dataset(df)
            sessions[session_id] = df
            
        if not is_engineered:
            df, _ = engineer_features(df)
            sessions[session_id] = df
            
        # 4. Calculate final rounded KPIs
        kpis = calculate_kpis(df)
        
        from app.utils.serialization import clean_for_json
        return clean_for_json(kpis)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error occurred during KPI calculation pipeline: {str(e)}"
        )
