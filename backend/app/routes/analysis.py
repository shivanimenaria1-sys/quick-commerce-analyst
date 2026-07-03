from fastapi import APIRouter, HTTPException, status
from app.services.data_ingestion import sessions
from app.services.data_cleaning import clean_dataset
from app.services.feature_engineering import engineer_features
from app.services.kpi_engine import calculate_kpis
from app.services.insight_generator import generate_insights, insights_cache

router = APIRouter()

@router.post("/analyze/{session_id}")
def analyze_session(session_id: str):
    """
    Orchestrates the full data analysis pipeline in sequence:
    1. clean_dataset
    2. engineer_features
    3. calculate_kpis
    4. generate_insights
    Updates the in-memory session DataFrame and cache, and returns
    one combined JSON payload.
    """
    # 1. Retrieve the session DataFrame
    if session_id not in sessions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session with ID {session_id} not found."
        )
        
    df = sessions[session_id]
    
    print(f"\n[*] Starting full analysis pipeline for session: {session_id}")
    
    try:
        # Stage 1: Data Cleaning
        print("[*] Stage 1/4: Cleaning dataset...")
        cleaned_df, cleaning_report = clean_dataset(df)
        sessions[session_id] = cleaned_df
        print(f"[+] Stage 1/4 Complete. Rows after cleaning: {len(cleaned_df)}")
        
        # Stage 2: Feature Engineering
        print("[*] Stage 2/4: Engineering features...")
        engineered_df, new_columns = engineer_features(cleaned_df)
        sessions[session_id] = engineered_df
        print(f"[+] Stage 2/4 Complete. Added {len(new_columns)} derived columns.")
        
        # Stage 3: KPI Calculation
        print("[*] Stage 3/4: Calculating business KPIs...")
        kpis = calculate_kpis(engineered_df)
        print("[+] Stage 3/4 Complete.")
        
        # Stage 4: AI Insights
        print("[*] Stage 4/4: Generating AI insights...")
        insights = generate_insights(kpis)
        # Keep caches synced
        insights_cache[session_id] = insights
        print("[+] Stage 4/4 Complete.")
        
        from app.utils.serialization import clean_for_json
        
        print(f"[+] Full analysis pipeline completed successfully for session: {session_id}\n")
        
        payload = {
            "cleaning_report": cleaning_report,
            "kpis": kpis,
            "insights": insights
        }
        return clean_for_json(payload)
    except Exception as e:
        print(f"[-] Pipeline execution failed for session {session_id}: {str(e)}\n")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Pipeline execution failed: {str(e)}"
        )
