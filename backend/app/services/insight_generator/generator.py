import os
import json
import logging
from typing import Dict, Any, List
from pydantic import BaseModel, Field
from google import genai
from google.genai import types
from app.services.insight_generator.extractor import InsightExtractionEngine

logger = logging.getLogger("dataset_profiler")

_gemini_client = None

def get_gemini_client() -> genai.Client:
    global _gemini_client
    if _gemini_client is not None:
        return _gemini_client
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return None
    try:
        _gemini_client = genai.Client(api_key=api_key)
        return _gemini_client
    except Exception as e:
        logger.error(f"Error initializing Gemini client: {e}")
        return None

class KPIInterpretation(BaseModel):
    kpi_id: str = Field(description="Must match the exact kpi_id of the analyzed KPI")
    interpretation: str = Field(description="Domain-aware evaluation (good/bad/neutral) referencing actual numbers. Max 20 words.")
    citations: List[str] = Field(description="Citations of matching kpi_id or trend_id")

class StatementWithCitations(BaseModel):
    text: str = Field(description="Narrative statement text.")
    citations: List[str] = Field(description="IDs of originating KPIs, trends, anomalies, or correlations used (e.g., 'total_revenue', 'anomaly_sales_amount')")

class DomainInsightResponse(BaseModel):
    executive_summary: str = Field(description="2-3 sentence domain-aware executive summary of operations referencing actual numbers.")
    kpi_interpretations: List[KPIInterpretation] = Field(description="Detailed evaluations for each active KPI in the input.")
    risks: List[StatementWithCitations] = Field(description="Notable operational risks. Strictly derived from flagged anomalies or high nulls in input.")
    opportunities: List[StatementWithCitations] = Field(description="Notable opportunities derived from trend percentages in input.")
    recommendations: List[StatementWithCitations] = Field(description="2-4 actionable suggestions phrased as 'Consider...', 'We suggest...'.")


def generate_narrative_insights(pipeline_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Orchestrates narrative insight generation:
    1. Extracts deterministic insights (extraction engine).
    2. Invokes Gemini exactly once to summarize using structured Pydantic schemas.
    3. Runs a Narrative Validation guardrail step (scrubbing/regenerating unreferenced numbers).
    """
    logger.info("Executing Narrative Insight Generator...")
    
    # 1. Deterministic extraction
    extracted_insights = InsightExtractionEngine.extract_insights(pipeline_result)
    
    # Check if there are active KPIs
    if not extracted_insights["kpi_metrics"]:
        logger.warning("No KPIs found in context. Skipping LLM generation.")
        return {
            "insights": {
                "executive_summary": "No operational KPIs selected for narrative analysis.",
                "kpi_interpretations": [],
                "risks": [],
                "opportunities": [],
                "recommendations": []
            }
        }

    # 2. Build prompt
    prompt = f"""
You are a senior domain analyst. Review the following deterministically compiled business operations insights:

INPUT METRICS AND STATISTICS:
{json.dumps(extracted_insights, indent=2)}

Rules:
1. You are STRICTORLY PROHIBITED from inventing context, business facts, or statistics.
2. The narrative must ONLY reference the numbers and trends present in the input. Do not perform any numerical calculations or make up numbers.
3. Every generated statement MUST include references to the originating KPI, trend, anomaly, or correlation ID in its 'citations' list.
4. Recommendations must be phrased strictly as suggestions (e.g. 'We recommend considering...', 'Consider reviewing...').
5. You must return a structured JSON response matching the schema.
"""

    client = get_gemini_client()
    if not client:
        raise ValueError("GEMINI_API_KEY is missing or not configured in environment.")

    from app.services.insight_generator.validator import NarrativeValidator
    
    # 3. LLM call with up to 2 retries (total 3 attempts)
    max_attempts = 3
    last_exception = None
    final_insights = None
    
    for attempt in range(max_attempts):
        logger.info(f"Calling Gemini API for Narrative Insights (Attempt {attempt+1}/{max_attempts})...")
        try:
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=DomainInsightResponse,
                    temperature=0.1
                )
            )
            
            parsed = json.loads(response.text)
            validated_response = DomainInsightResponse.model_validate(parsed)
            final_insights = validated_response.model_dump()
            
            # 4. Guardrail validation
            logger.info("Validating narrative grounding...")
            validation_errors = NarrativeValidator.validate(final_insights, extracted_insights)
            if not validation_errors:
                logger.info("Narrative insights passed validation check.")
                break
            else:
                logger.warning(f"Narrative validation failed on attempt {attempt+1}: {validation_errors}")
                # We can try to repair or regenerate in next loop iteration
                last_exception = Exception(f"Narrative validation error: {validation_errors}")
                final_insights = None
                
        except Exception as e:
            logger.warning(f"Narrative generation attempt {attempt+1} failed: {e}")
            last_exception = e
            continue

    if not final_insights:
        logger.error(f"Narrative generation failed. Executing fallback validation recovery...")
        # Fallback recovery: if LLM failed or validation repeatedly failed, use standard template or strip error items
        try:
            # Re-generate once with strict instruction or fallback to deterministic summaries
            if last_exception:
                logger.warning("Attempting self-correction: stripping ungrounded sentences...")
                # We will perform strict validation and auto-strip statements that do not validate
                raw_parsed = json.loads(response.text)
                final_insights = NarrativeValidator.scrub_ungrounded(raw_parsed, extracted_insights)
            else:
                raise RuntimeError("No response received from LLM.")
        except Exception as fallback_err:
            logger.error(f"Fallback recovery failed: {fallback_err}")
            # Absolute fallback
            final_insights = {
                "executive_summary": f"Completed analysis for {extracted_insights['domain_context']['domain']} operations log.",
                "kpi_interpretations": [
                    {
                        "kpi_id": k["kpi_id"],
                        "interpretation": f"Calculated value of {k['value']} via {k['aggregation']}.",
                        "citations": [k["kpi_id"]]
                    } for k in extracted_insights["kpi_metrics"]
                ],
                "risks": [],
                "opportunities": [],
                "recommendations": []
            }

    return {
        "status": "success",
        "extracted_insights": extracted_insights,
        "insights": final_insights
    }
