import os
import json
import datetime
from jinja2 import Environment, FileSystemLoader
from typing import Tuple, Dict, Any, List

# Try importing weasyprint. If GTK+ libraries are missing, fallback gracefully.
try:
    import weasyprint
    WEASYPRINT_AVAILABLE = True
except Exception as e:
    print(f"WeasyPrint is unconfigured or GTK+ missing: {str(e)}. Fallback mode enabled.")
    WEASYPRINT_AVAILABLE = False

from app.services.insight_generator import get_gemini_client
from google.genai import types
from pydantic import BaseModel, Field

class ExecutiveAnalysisSchema(BaseModel):
    score: int = Field(description="Operational health score from 0-100")
    classification: str = Field(description="Operational classification: Excellent, Healthy, Needs Improvement, Critical")
    explanation: str = Field(description="2-3 sentence overview of why the score was received based on KPIs.")
    conclusion_text: str = Field(description="150-250 words executive consulting summary on performance, operational risk, and growth opportunities.")
    conclusion_steps: list[str] = Field(description="A list of exactly 3 strategic next-step recommendations.")

def calculate_heuristic_health_score(kpis: dict) -> Tuple[int, str, str]:
    """
    Calculates a heuristic business health score (0-100), classification,
    and explanation based on operational KPIs as a fallback when AI is unavailable.
    """
    # Grab base parameters with safe defaults
    rating = kpis.get("satisfaction_kpis", {}).get("avg_customer_rating")
    rating = float(rating) if rating is not None else 4.0
    
    repeat = kpis.get("customer_kpis", {}).get("repeat_customer_rate")
    repeat = float(repeat) if repeat is not None else 20.0
    
    cancellation = kpis.get("order_kpis", {}).get("cancellation_rate")
    cancellation = float(cancellation) if cancellation is not None else 5.0
    
    delay = kpis.get("delivery_kpis", {}).get("delayed_order_rate")
    delay = float(delay) if delay is not None else 15.0
    
    low_margin = kpis.get("unit_economics_kpis", {}).get("low_margin_order_pct")
    low_margin = float(low_margin) if low_margin is not None else 10.0

    # Calculate score
    score = 80  # Base score
    score += (rating - 4.0) * 15.0
    score += (repeat - 20.0) * 0.4
    score -= (cancellation - 5.0) * 3.0
    score -= (delay - 15.0) * 0.5
    score -= (low_margin - 10.0) * 0.8
    
    # Cap score
    score = max(0, min(100, round(score)))

    # Determine classification
    if score >= 90:
        classification = "Excellent"
    elif score >= 75:
        classification = "Healthy"
    elif score >= 60:
        classification = "Needs Improvement"
    else:
        classification = "Critical"

    # Construct explanation
    explanation = (
        f"The business receives a score of {score} ({classification}). This diagnostic is driven by "
        f"customer satisfaction metrics (average rating: {rating:.2f}) and repeat order rates ({repeat:.2f}%). "
        f"However, addressing a {cancellation:.2f}% cancellation index and {delay:.2f}% SLA delivery delays "
        f"represent crucial paths for unlocking margin optimization."
    )
    
    return score, classification, explanation

def generate_executive_analysis(kpis: dict, insights: dict) -> dict:
    """
    Calls Gemini model gemini-2.5-flash to compile the Business Health Score and a McKinsey/BCG consulting-style conclusion.
    Falls back to a heuristic calculator and static professional paragraphs if the API call fails or is unconfigured.
    """
    client = get_gemini_client()
    
    # Fallback default values
    fallback_score, fallback_class, fallback_explanation = calculate_heuristic_health_score(kpis)
    fallback_conclusion_text = (
        "The business demonstrates robust top-line performance with significant revenue velocity and solid repeat "
        "loyalty across core geographies. However, operational pressures are beginning to manifest in delivery speed "
        "constraints and volatile margins. To protect terminal profitability and customer lifetime value, leadership "
        "must rapidly address dispatch bottlenecks in high-frequency dark stores while adjusting rider shift capacity."
    )
    fallback_conclusion_steps = [
        "Re-align rider staffing shift hours to correspond precisely with peak checkout time slots to lower transit times.",
        "Expand dark store inventory storage in high-volume underserved pincodes to lower logistics distance.",
        "Implement automated batch sorting systems to optimize the picking and packaging overhead buffer."
    ]

    if not client:
        return {
            "score": fallback_score,
            "classification": fallback_class,
            "explanation": fallback_explanation,
            "conclusion_text": fallback_conclusion_text,
            "conclusion_steps": fallback_conclusion_steps
        }

    prompt = f"""
You are a senior McKinsey or BCG consulting partner writing an Executive Business Report for a quick commerce (q-commerce) company.
Analyze the following KPIs and AI insights:

KPIs:
{json.dumps(kpis, indent=2)}

Insights:
{json.dumps(insights, indent=2)}

Rules:
- Score must be integer 0-100.
- Classification must be one of: Excellent (90-100), Healthy (75-89), Needs Improvement (60-74), Critical (<60).
- The conclusion_text must be 150-250 words, consulting style.
"""

    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=ExecutiveAnalysisSchema,
                temperature=0.7
            )
        )
        
        content = response.text
        parsed = json.loads(content)
        
        # Verify schema elements
        score = int(parsed.get("score", fallback_score))
        classification = str(parsed.get("classification", fallback_class))
        explanation = str(parsed.get("explanation", fallback_explanation))
        conclusion_text = str(parsed.get("conclusion_text", fallback_conclusion_text))
        conclusion_steps = parsed.get("conclusion_steps", fallback_conclusion_steps)
        if not isinstance(conclusion_steps, list) or len(conclusion_steps) < 3:
            conclusion_steps = fallback_conclusion_steps
            
        return {
            "score": score,
            "classification": classification,
            "explanation": explanation,
            "conclusion_text": conclusion_text,
            "conclusion_steps": conclusion_steps[:3]
        }
    except Exception as e:
        print(f"Failed to generate AI executive conclusion: {str(e)}. Using local fallback.")
        return {
            "score": fallback_score,
            "classification": fallback_class,
            "explanation": fallback_explanation,
            "conclusion_text": fallback_conclusion_text,
            "conclusion_steps": fallback_conclusion_steps
        }

def generate_pdf_report(kpis: dict, insights: dict, client_name: str = "Demo Q-Commerce Client") -> Tuple[bytes, str]:
    """
    Compiles the executive report by rendering a Jinja2 template and compiling to PDF via WeasyPrint.
    If WeasyPrint/GTK is unconfigured, returns raw HTML bytes instead.
    """
    # 1. Fetch executive analysis and health score
    analysis = generate_executive_analysis(kpis, insights)
    
    # 2. Set up Jinja2 environment and render template
    template_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "templates"))
    env = Environment(loader=FileSystemLoader(template_dir))
    template = env.get_template("report_template.html")
    
    date_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    rendered_html = template.render(
      client_name=client_name,
      date_str=date_str,
      kpis=kpis,
      insights=insights,
      health_score=analysis["score"],
      health_class=analysis["classification"],
      health_explanation=analysis["explanation"],
      conclusion_text=analysis["conclusion_text"],
      conclusion_steps=analysis["conclusion_steps"]
    )
    
    # 3. Compile using WeasyPrint if available
    if WEASYPRINT_AVAILABLE:
        try:
            pdf_bytes = weasyprint.HTML(string=rendered_html).write_pdf()
            return pdf_bytes, "application/pdf"
        except Exception as e:
            print(f"WeasyPrint conversion failed: {str(e)}. Swapping to raw HTML download.")
            
    # Default fallback: return raw HTML bytes
    return rendered_html.encode("utf-8"), "text/html"
