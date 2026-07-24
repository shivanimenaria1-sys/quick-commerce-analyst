import json
import logging
from typing import Dict, Any, List
from pydantic import BaseModel, Field
from google.genai import types
from app.services.insight_generator import get_gemini_client

logger = logging.getLogger("dataset_profiler")

class SecondaryDomain(BaseModel):
    domain: str = Field(description="Restricted to: Retail, Quick Commerce, Sales, Finance, HR, Healthcare, Education, Manufacturing, Marketing, Logistics, Generic")
    confidence: float = Field(description="Confidence of secondary domain association between 0.0 and 1.0")

class HybridDomainProfileResponse(BaseModel):
    primary_domain: str = Field(description="The primary business domain. Restricted to Retail, Quick Commerce, Sales, Finance, HR, Healthcare, Education, Manufacturing, Marketing, Logistics, Generic")
    confidence: float = Field(description="Confidence score of primary domain classification between 0.0 and 1.0")
    secondary_domains: List[SecondaryDomain] = Field(description="List of secondary business domains if overlap is detected, empty list if none.")
    reasoning: str = Field(description="Brief explanation of the classification, maximum 25 words")


def classify_domain(confirmed_semantic_mapping: dict, dataset_profile: dict) -> dict:
    """
    Infers the business domain of a dataset using LLM structured generation.
    Supports primary, secondary, and Hybrid domain classification based on confidence scores.
    """
    metadata = dataset_profile.get("dataset_metadata", {})
    row_count = metadata.get("row_count", 0)
    col_count = metadata.get("column_count", 0)
    
    # Standardize semantic mapping structure
    columns_mapping = confirmed_semantic_mapping
    if "columns" in confirmed_semantic_mapping:
        columns_mapping = confirmed_semantic_mapping["columns"]
        
    role_pairs = []
    top_categories = {}
    
    for col_name, col_data in columns_mapping.items():
        role = col_data if isinstance(col_data, str) else col_data.get("semantic_role", "unknown")
        role_pairs.append((role, col_name))
        
        # Extract top category details for contextual boosting
        if role in ("category_like", "location_like", "status_like"):
            profile_col = dataset_profile.get("columns", {}).get(col_name, {})
            stats = profile_col.get("statistics", {})
            top_freqs = stats.get("top_frequencies", {})
            if top_freqs:
                top_categories[col_name] = list(top_freqs.keys())[:5]

    # Formulate Prompt
    prompt = f"""
You are a data domain classifier. Your task is to analyze the semantic metadata of a dataset and determine its business domain.

Dataset Context:
- Rows: {row_count}
- Columns: {col_count}

Semantic Roles & Column Names:
{json.dumps(role_pairs, indent=2)}

Top Categorical Column Values:
{json.dumps(top_categories, indent=2)}

You must classify the dataset into a primary domain and optionally list any secondary overlapping domains.
Domains are restricted to: Retail, Quick Commerce, Sales, Finance, HR, Healthcare, Education, Manufacturing, Marketing, Logistics, Generic.

Return the classification as a JSON object matching the schema.
"""

    client = get_gemini_client()
    if not client:
        raise ValueError("GEMINI_API_KEY is missing or not configured in environment (.env).")

    try:
        logger.info("Calling Gemini to classify business domain...")
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=HybridDomainProfileResponse,
                temperature=0.1
            )
        )
        
        parsed = json.loads(response.text)
        validated = HybridDomainProfileResponse.model_validate(parsed)
        
        primary_domain = validated.primary_domain
        confidence = validated.confidence
        reasoning = validated.reasoning
        
        # Apply strict confidence threshold constraint
        if confidence < 0.50:
            logger.info(f"Domain classifier confidence ({confidence}) below 0.50 threshold. Defaulting to 'Generic'.")
            primary_domain = "Generic"
            confidence = 0.50
            reasoning = "Confidence below threshold; defaulted to Generic."
            
        allowed_domains = ["Retail", "Quick Commerce", "Sales", "Finance", "HR", "Healthcare", "Education", "Manufacturing", "Marketing", "Logistics", "Generic"]
        if primary_domain not in allowed_domains:
            primary_domain = "Generic"

        # Check for Hybrid domains (secondary domains with confidence >= 0.35)
        valid_secondaries = []
        for sec in validated.secondary_domains:
            if sec.domain in allowed_domains and sec.confidence >= 0.35:
                valid_secondaries.append({
                    "domain": sec.domain,
                    "confidence": round(sec.confidence, 2)
                })
                
        classification_type = "Single"
        if valid_secondaries:
            classification_type = "Hybrid"
            
        logger.info(f"Classified domain: {primary_domain} ({classification_type})")
        
        return {
            "primary_domain": primary_domain,
            "secondary_domains": valid_secondaries,
            "classification": classification_type,
            "confidence": confidence,
            "reasoning": reasoning,
            # Backwards compatibility key
            "domain": primary_domain
        }
        
    except Exception as e:
        logger.error(f"Error classifying business domain: {e}")
        return {
            "primary_domain": "Generic",
            "secondary_domains": [],
            "classification": "Single",
            "confidence": 0.50,
            "reasoning": f"Failed to infer domain: {str(e)}",
            "domain": "Generic"
        }
