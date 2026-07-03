from fastapi import APIRouter, HTTPException, status
from app.services.data_ingestion import sessions
from app.services.data_cleaning import clean_dataset

router = APIRouter()

@router.post("/clean/{session_id}")
def clean_data(session_id: str):
    """
    Retrieves the DataFrame for the given session_id, runs the data cleaning process,
    updates the in-memory DataFrame session with the clean version, and returns
    the generated cleaning summary report.
    """
    # 1. Check if session exists
    if session_id not in sessions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session with ID {session_id} not found."
        )
    
    # 2. Retrieve the active DataFrame
    df = sessions[session_id]
    
    try:
        # 3. Clean the dataset
        cleaned_df, report = clean_dataset(df)
        
        # 4. Save the cleaned DataFrame back to the session store
        sessions[session_id] = cleaned_df
        
        # 5. Return the report
        return report
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error occurred during data cleaning: {str(e)}"
        )
