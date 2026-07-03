from fastapi import APIRouter, HTTPException, status
from fastapi.encoders import jsonable_encoder
from app.services.data_ingestion import sessions
from app.services.feature_engineering import engineer_features
from app.utils.serialization import clean_for_json

router = APIRouter()

@router.post("/engineer/{session_id}")
def engineer_data_features(session_id: str):
    """
    Retrieves the DataFrame for the given session_id, runs feature engineering
    calculations to add derived analytical columns, updates the in-memory store,
    and returns a preview (first 10 rows) along with the list of new columns added.
    """
    # 1. Check if session exists
    if session_id not in sessions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session with ID {session_id} not found."
        )
        
    df = sessions[session_id]
    
    try:
        # 2. Compute engineered features
        engineered_df, new_columns = engineer_features(df)
        
        # 3. Update the session store with the enriched DataFrame
        sessions[session_id] = engineered_df
        
        # 4. Generate preview (first 10 rows) and serialize safely
        preview_df = engineered_df.head(10)
        preview_records = preview_df.to_dict(orient="records")
        cleaned_preview = clean_for_json(preview_records)
        serializable_preview = jsonable_encoder(cleaned_preview)
        
        return {
            "new_columns": new_columns,
            "preview": serializable_preview
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error occurred during feature engineering: {str(e)}"
        )
