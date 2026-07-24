import json
import logging
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from google.genai import types
from app.services.insight_generator import get_gemini_client
from app.services.semantic_mapper.cache import BaseCacheProvider, JSONFileCacheProvider, generate_schema_fingerprint

logger = logging.getLogger("dataset_profiler")

DEFAULT_SEMANTIC_ROLES = [
    "revenue_like", "cost_like", "profit_like", "price_like", "quantity_like",
    "date_like", "datetime_like", "customer_id_like", "product_id_like", "employee_like",
    "category_like", "location_like", "rating_like", "duration_like", "status_like",
    "boolean_flag_like", "percentage_like", "currency_like", "text_like", "id_like",
    "unknown"
]

class AlternativeRole(BaseModel):
    role: str
    confidence: float

class ColumnMapping(BaseModel):
    column_name: str
    semantic_role: str
    confidence: float
    reasoning: str = Field(description="Maximum 15 words explaining the choice")
    alternative_roles: List[AlternativeRole]

class SemanticMappingResponse(BaseModel):
    mappings: List[ColumnMapping]


def map_semantics(
    dataset_profile: Dict[str, Any],
    allowed_roles: Optional[List[str]] = None,
    cache_provider: Optional[BaseCacheProvider] = None
) -> Dict[str, Any]:
    """
    Main mapping engine. Takes a dataset profile, infers semantic meanings for all columns
    using a single structured LLM call with up to 2 retries on failure, and manages caching.
    Never inspects or reads raw datasets directly.
    """
    if allowed_roles is None:
        allowed_roles = DEFAULT_SEMANTIC_ROLES
        
    if cache_provider is None:
        cache_provider = JSONFileCacheProvider()

    # 1. Deterministic Caching check
    fingerprint = generate_schema_fingerprint(dataset_profile)
    cached_mapping = cache_provider.get(fingerprint)
    if cached_mapping:
        logger.info(f"Cache hit! Retrieved semantic column mappings for fingerprint: {fingerprint}")
        return cached_mapping

    logger.info(f"Cache miss. Generating semantic column mappings for fingerprint: {fingerprint}")
    
    # 2. Extract column metadata from profile
    metadata = dataset_profile.get("dataset_metadata", {})
    row_count = metadata.get("row_count", 0)
    col_count = metadata.get("column_count", 0)
    
    columns_info = []
    columns_profile = dataset_profile.get("columns", {})
    for col_name, col_data in columns_profile.items():
        stats = col_data.get("statistics", {})
        col_summary = {
            "column_name": col_name,
            "inferred_dtype": col_data.get("inferred_dtype", ""),
            "dtype_confidence": col_data.get("confidence_score", 1.0),
            "sample_values": stats.get("sample_values", []),
            "cardinality_ratio": stats.get("cardinality_ratio", 0.0),
            "null_percentage": stats.get("null_percentage", 0.0),
            "basic_stats": {
                "min": stats.get("min"),
                "max": stats.get("max"),
                "mean": stats.get("mean"),
                "median": stats.get("median")
            }
        }
        columns_info.append(col_summary)

    # 3. LLM Prompt Construction
    prompt = f"""
You are a data semantics expert. Your task is to analyze the columns of a dataset and map each one to its most appropriate semantic role.

Context:
- Dataset rows: {row_count}
- Dataset columns: {col_count}

Available semantic roles you must choose from:
{json.dumps(allowed_roles, indent=2)}

Columns to analyze:
{json.dumps(columns_info, indent=2)}

For each column, you must return a mapping object matching the JSON schema:
1. "column_name": Name of the column.
2. "semantic_role": One of the allowed semantic roles.
3. "confidence": A float between 0.0 and 1.0 representing your classification confidence.
4. "reasoning": A brief explanation (maximum 15 words).
5. "alternative_roles": A list of other possible roles (each with role and confidence score).

You must map ALL columns in this list. Return the response as a JSON object with a single "mappings" key containing the array of column mapping objects.
"""

    client = get_gemini_client()
    if not client:
        raise ValueError("GEMINI_API_KEY is missing or not configured in environment (.env).")

    # 4. LLM Generation Loop (Auto-retry up to 2 times, total 3 attempts)
    max_attempts = 3
    last_exception = None
    structured_data = None
    
    for attempt in range(max_attempts):
        logger.info(f"Calling Gemini API (Attempt {attempt + 1}/{max_attempts})...")
        try:
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=SemanticMappingResponse,
                    temperature=0.2
                )
            )
            
            content = response.text
            parsed = json.loads(content)
            
            # Strict validation check of output json schema
            # Check pydantic parse correctness
            validated = SemanticMappingResponse.model_validate(parsed)
            structured_data = validated.mappings
            logger.info("Gemini returned successfully validated structured JSON mapping.")
            break
        except Exception as e:
            logger.warning(f"Attempt {attempt + 1} failed during semantic mapping: {e}")
            last_exception = e
            continue

    if not structured_data:
        raise RuntimeError(f"Semantic Column mapping failed after {max_attempts} attempts. Error: {last_exception}")

    # 5. Build final columns mapping dict and check confidence thresholds
    mapped_columns = {}
    response_map = {m.column_name: m for m in structured_data}
    
    for col_name in columns_profile.keys():
        if col_name in response_map:
            m = response_map[col_name]
            role = m.semantic_role
            conf = m.confidence
            reason = m.reasoning
            alts = [{"role": alt.role, "confidence": alt.confidence} for alt in m.alternative_roles]
        else:
            # Fallback for missing column in LLM response
            role = "unknown"
            conf = 0.0
            reason = "Failed to classify column."
            alts = []
            
        needs_confirm = conf < 0.60
        mapped_columns[col_name] = {
            "semantic_role": role,
            "confidence": conf,
            "reasoning": reason,
            "alternative_roles": alts,
            "needs_user_confirmation": needs_confirm
        }

    final_mapping = {
        "schema_fingerprint": fingerprint,
        "columns": mapped_columns
    }

    # Save to persistent cache
    cache_provider.set(fingerprint, final_mapping)
    logger.info(f"Cached semantic column mappings for fingerprint: {fingerprint}")
    
    return final_mapping
