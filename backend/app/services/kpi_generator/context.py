from pydantic import BaseModel
from typing import Dict, Any, List

class PipelineContext(BaseModel):
    """
    Standardized context payload that aggregates the metadata, profiles,
    and engineered feature definitions compiled during previous pipeline stages.
    Consumed by downstream analytical modules.
    """
    dataset_profile: Dict[str, Any]
    confirmed_semantic_mapping: Dict[str, Any]
    domain_profile: Dict[str, Any]
    engineered_features: List[Dict[str, Any]]
    session_id: str = None
