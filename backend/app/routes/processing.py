import logging
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from app.services.data_ingestion import sessions
from app.services.feature_engineering_engine import engineer_features
from app.services.domain_classifier import classify_domain

router = APIRouter(prefix="/process")
logger = logging.getLogger("dataset_profiler")

class EngineeringRequest(BaseModel):
    session_id: str
    semantic_mapping: dict

class ClassificationRequest(BaseModel):
    semantic_mapping: dict
    dataset_profile: dict

@router.post("/engineer")
def run_schema_agnostic_feature_engineering(request: EngineeringRequest):
    """
    Runs the rule-based, deterministic feature engineering engine on the active session's DataFrame
    based on the confirmed semantic column roles mapping.
    """
    if request.session_id not in sessions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session with ID {request.session_id} not found."
        )
        
    try:
        df = sessions[request.session_id]
        
        # Run feature engineering
        engineered_df, metadata = engineer_features(df, request.semantic_mapping)
        
        # Save enriched dataframe back to session
        sessions[request.session_id] = engineered_df
        
        # Determine newly created columns
        new_cols = list(set(engineered_df.columns) - set(df.columns))
        
        return {
            "status": "success",
            "new_columns_count": len(new_cols),
            "engineered_columns": new_cols,
            "metadata": metadata
        }
    except Exception as e:
        logger.error(f"Error running feature engineering endpoint: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/classify")
def run_llm_domain_classification(request: ClassificationRequest):
    """
    Infers the overall business domain of the dataset profile and semantic mappings.
    """
    try:
        domain_profile = classify_domain(request.semantic_mapping, request.dataset_profile)
        return domain_profile
    except Exception as e:
        logger.error(f"Error running domain classification endpoint: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
