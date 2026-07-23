import os
import json
from google import genai
from google.genai import types
from typing import Dict, Any
from pydantic import BaseModel, Field

# Simple in-memory cache to store insights for each session
insights_cache: Dict[str, dict] = {}

class InsightsSchema(BaseModel):
    strengths: list[str] = Field(description="A list identifying what parts of the operations, sales, or customer satisfaction are working well.")
    bottlenecks: list[str] = Field(description="A list describing risks or issues hurting the business (e.g. delivery delays, low margin segments, high cancel rates).")
    opportunities: list[str] = Field(description="A list mapping potential growth areas or adjustments (e.g. optimizing underserved pincodes, rider shift adjustments).")
    recommendations: list[str] = Field(description="A list presenting specific, numbered actionable items to improve profitability and delivery times.")

# Shared singleton Gemini client
_gemini_client = None

def get_gemini_client() -> genai.Client:
    """
    Safely initializes and returns the shared Gemini client if the GEMINI_API_KEY is configured.
    """
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
        print(f"Error initializing Gemini client: {e}")
        return None

def generate_insights(kpis: dict) -> dict:
    """
    Sends the numeric KPI summary to gemini-2.5-flash and requests a structured analysis.
    Raises ValueError or RuntimeError on configuration missing or API call failure.
    """
    client = get_gemini_client()
    if not client:
        raise ValueError("GEMINI_API_KEY is missing or not configured in environment (.env).")
        
    prompt = f"""
You are a senior business analyst for a quick commerce (q-commerce) company.
Your task is to analyze the following summary of key performance indicators (KPIs) of the business and provide structured, high-value insights.

Here is the KPI report:
{json.dumps(kpis, indent=2)}

You must analyze this data and return a JSON object containing precisely four keys:
1. "strengths": A list of strings identifying what parts of the operations, sales, or customer satisfaction are working well.
2. "bottlenecks": A list of strings describing risks or issues hurting the business (e.g. delivery delays, low margin segments, high cancel rates).
3. "opportunities": A list of strings mapping potential growth areas or adjustments (e.g. optimizing underserved pincodes, rider shift adjustments).
4. "recommendations": A list of strings presenting specific, numbered actionable items to improve profitability and delivery times.

Rules:
- Do not mention raw rows, only refer to the aggregated statistics.
- Ensure all values in the lists are clear, concise, and business-focused.
"""

    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=InsightsSchema,
                temperature=0.7
            )
        )
        
        content = response.text
        parsed = json.loads(content)
        
        # Verify required keys are present and are lists
        required_keys = ["strengths", "bottlenecks", "opportunities", "recommendations"]
        validated_insights = {}
        for key in required_keys:
            if key in parsed and isinstance(parsed[key], list):
                validated_insights[key] = [str(item) for item in parsed[key]]
            else:
                validated_insights[key] = [f"Default {key} summary based on KPI trends."]
                
        return validated_insights
        
    except Exception as e:
        raise RuntimeError(f"Error calling Gemini API: {str(e)}")
