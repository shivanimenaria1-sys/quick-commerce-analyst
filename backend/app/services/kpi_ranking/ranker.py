import os
import json
import hashlib
import logging
from typing import Dict, Any, List
from pydantic import BaseModel, Field
from google.genai import types
from app.services.insight_generator import get_gemini_client
from app.services.kpi_generator.context import PipelineContext
from app.services.semantic_mapper.cache import generate_schema_fingerprint

logger = logging.getLogger("dataset_profiler")

class SelectedKPISchema(BaseModel):
    candidate_id: str = Field(description="The unique id matching the candidate KPI")
    display_label: str = Field(description="Visual name/label of the KPI refined for business clarity")
    rank: int = Field(description="Numerical rank order starting from 1 (highest priority)")
    importance: float = Field(description="Weight importance score between 0.0 and 1.0")
    reason: str = Field(description="Brief explanation of why this KPI is important for the classified business domain")

class KPIRankingResponse(BaseModel):
    selected_kpis: List[SelectedKPISchema]


class KPIRankingsCache:
    """
    Handles loading and storing ranked KPI results using a compound hash of the
    dataset's column schema, semantic mapping, and business domain.
    """
    def __init__(self):
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        data_dir = os.path.join(base_dir, "data")
        os.makedirs(data_dir, exist_ok=True)
        self.file_path = os.path.join(data_dir, "kpi_rankings_cache.json")
        self._cache = self._load()

    def _load(self) -> dict:
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading KPI rankings cache: {e}")
                return {}
        return {}

    def _save(self) -> None:
        try:
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump(self._cache, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving KPI rankings cache: {e}")

    def get(self, schema_fp: str, mapping_fp: str, domain: str) -> Any:
        compound_key = hashlib.sha256(f"{schema_fp}||{mapping_fp}||{domain}".encode('utf-8')).hexdigest()
        return self._cache.get(compound_key)

    def set(self, schema_fp: str, mapping_fp: str, domain: str, data: Any) -> None:
        compound_key = hashlib.sha256(f"{schema_fp}||{mapping_fp}||{domain}".encode('utf-8')).hexdigest()
        self._cache[compound_key] = data
        self._save()


def rank_candidate_kpis(context: PipelineContext, candidate_kpis: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calls Gemini exactly once to rank, filter, and relabel rule-based KPI candidates.
    Isolated from changing formulas or aggregations. Caches results using compound hashes.
    """
    # 1. Cache lookup
    schema_fp = generate_schema_fingerprint(context.dataset_profile)
    mapping_fp = generate_schema_fingerprint(context.confirmed_semantic_mapping)
    domain_data = context.domain_profile.get("domain", "Generic")
    
    cache = KPIRankingsCache()
    cached = cache.get(schema_fp, mapping_fp, domain_data)
    if cached:
        logger.info("Cache hit! Retrieved ranked KPIs from cache.")
        return cached

    logger.info("Cache miss. Calling Gemini to rank KPI candidates...")
    
    # 2. Extract context parameters (never send raw rows)
    row_count = context.dataset_profile.get("dataset_metadata", {}).get("row_count", 0)
    col_count = context.dataset_profile.get("dataset_metadata", {}).get("column_count", 0)
    
    # Compact candidates list for LLM context
    candidates_list = []
    candidates_dict = {}
    for cand in candidate_kpis.get("candidate_kpis", []):
        candidates_list.append({
            "id": cand["id"],
            "suggested_display_name": cand["display_name"],
            "required_semantic_roles": cand["required_semantic_roles"],
            "explanation": cand["explanation"]
        })
        candidates_dict[cand["id"]] = cand

    if not candidates_list:
        logger.warning("No KPI candidates generated to rank.")
        return {"selected_kpis": []}

    prompt = f"""
You are a senior business intelligence ranker. Your task is to review a list of precomputed KPI candidates and rank them for a specific business domain.

Dataset Context:
- Domain: {domain_data}
- Total Rows: {row_count}
- Total Columns: {col_count}

Candidate KPIs to Rank:
{json.dumps(candidates_list, indent=2)}

Rules:
1. You are STRICTORLY PROHIBITED from inventing new KPI candidates, and you must never change their formulas, aggregations, semantic roles, or calculation logic.
2. You should:
   - Rank the candidates numerically starting from 1 (highest priority).
   - Filter out candidates that are irrelevant to the business domain (e.g. attrition KPIs for a retail transaction dataset).
   - Improve the display labels for business clarity if needed (e.g. rename 'average_revenue' to 'Average Sale Size').
   - Provide a concise business explanation why each KPI matters.
3. Return the response matching the JSON schema.
"""

    client = get_gemini_client()
    if not client:
        raise ValueError("GEMINI_API_KEY is missing or not configured in environment (.env).")

    # 3. LLM call with up to 2 retries (total 3 attempts)
    max_attempts = 3
    last_exception = None
    structured_rankings = None
    
    for attempt in range(max_attempts):
        logger.info(f"Calling Gemini API for KPI ranking (Attempt {attempt+1}/{max_attempts})...")
        try:
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=KPIRankingResponse,
                    temperature=0.2
                )
            )
            
            parsed = json.loads(response.text)
            validated = KPIRankingResponse.model_validate(parsed)
            structured_rankings = validated.selected_kpis
            logger.info("Gemini successfully returned validated KPI rankings.")
            break
        except Exception as e:
            logger.warning(f"KPI ranking attempt {attempt+1} failed: {e}")
            last_exception = e
            continue

    if not structured_rankings:
        raise RuntimeError(f"KPI ranking failed after {max_attempts} attempts. Error: {last_exception}")

    # 4. Reconstruct selected KPIs while strictly preserving formula logic
    ranked_kpis = []
    ranked_ids = set()
    
    for item in structured_rankings:
        cand_id = item.candidate_id
        if cand_id in candidates_dict:
            original_cand = candidates_dict[cand_id]
            ranked_ids.add(cand_id)
            
            # Reconstruct KPI: copy original properties, append rank/reason/label
            kpi_entry = {
                **original_cand,
                "display_name": item.display_label,
                "rank": item.rank,
                "importance": item.importance,
                "reason": item.reason,
                "selected": True
            }
            ranked_kpis.append(kpi_entry)
            
    # Include unselected candidates at the bottom for review table completeness
    for cand_id, original_cand in candidates_dict.items():
        if cand_id not in ranked_ids:
            kpi_entry = {
                **original_cand,
                "rank": len(ranked_kpis) + 1,
                "importance": 0.10,
                "reason": "Not prioritized for this business domain.",
                "selected": False
            }
            ranked_kpis.append(kpi_entry)

    # Sort primarily by rank
    ranked_kpis.sort(key=lambda x: (not x["selected"], x["rank"]))
    
    final_output = {
        "selected_kpis": ranked_kpis
    }

    # Save to persistent cache
    cache.set(schema_fp, mapping_fp, domain_data, final_output)
    
    return final_output
