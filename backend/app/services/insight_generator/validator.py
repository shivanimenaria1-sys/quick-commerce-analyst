import re
import logging
from typing import Dict, Any, List

logger = logging.getLogger("dataset_profiler")

class NarrativeValidator:
    """
    Validation and guardrail layer. Verifies that every number mentioned or ID cited
    in the narrative exists inside the deterministic input insights.
    """
    
    @staticmethod
    def extract_all_numbers(text: str) -> List[float]:
        # Matches decimal numbers (e.g. 14.5, -0.85) or large integers (e.g. 250000)
        # Ignores tiny ordinal numbers (0, 1, 2, 3, 4, 5) to prevent false positives in writing
        numbers = []
        found = re.findall(r'-?\b\d+(?:\.\d+)?\b', text)
        for num_str in found:
            try:
                val = float(num_str)
                # Ignore numbers between -5 and 5 to allow normal sentence counts/plurals
                if abs(val) > 5.0 or "." in num_str:
                    numbers.append(val)
            except ValueError:
                continue
        return numbers

    @staticmethod
    def get_valid_source_numbers(extracted_insights: Dict[str, Any]) -> set:
        """
        Gathers all allowed numbers from the source insights.
        """
        valid_numbers = set()
        
        # 1. KPI values
        for kpi in extracted_insights.get("kpi_metrics", []):
            val = kpi.get("value")
            if val is not None:
                valid_numbers.add(float(val))
                
        # 2. Trend change percentages
        for trend in extracted_insights.get("trends", []):
            pct = trend.get("pct_change")
            if pct is not None:
                valid_numbers.add(float(pct))
                
        # 3. Anomaly counts & percentages
        for anomaly in extracted_insights.get("anomalies", []):
            cnt = anomaly.get("count")
            if cnt is not None:
                valid_numbers.add(float(cnt))
            pct = anomaly.get("percentage")
            if pct is not None:
                valid_numbers.add(float(pct))
                
        # 4. Correlation coefficients
        for corr in extracted_insights.get("correlations", []):
            coef = corr.get("coefficient")
            if coef is not None:
                valid_numbers.add(float(coef))
                
        # Add integer versions too to make checks robust
        integer_versions = {int(x) for x in valid_numbers if x.is_integer()}
        return valid_numbers.union(integer_versions)

    @staticmethod
    def get_valid_source_ids(extracted_insights: Dict[str, Any]) -> set:
        """
        Gathers all valid KPI and insight IDs.
        """
        valid_ids = set()
        for k in extracted_insights.get("kpi_metrics", []):
            valid_ids.add(k["kpi_id"])
        for t in extracted_insights.get("trends", []):
            valid_ids.add(t["trend_id"])
            valid_ids.add(t["metric"])
        for a in extracted_insights.get("anomalies", []):
            valid_ids.add(a["anomaly_id"])
        for c in extracted_insights.get("correlations", []):
            valid_ids.add(c["correlation_id"])
        return valid_ids

    @classmethod
    def validate(cls, insights: Dict[str, Any], extracted_insights: Dict[str, Any]) -> List[str]:
        """
        Returns a list of validation error messages. Empty list indicates clean validation.
        """
        errors = []
        valid_numbers = cls.get_valid_source_numbers(extracted_insights)
        valid_ids = cls.get_valid_source_ids(extracted_insights)
        
        # Helper to validate a statement's text and citations
        def validate_statement(text: str, citations: List[str], field_label: str) -> None:
            # A. Check numbers
            text_nums = cls.extract_all_numbers(text)
            for num in text_nums:
                # Allow minor float precision tolerance (e.g. matching 14.5 to 14.5)
                matched = False
                for source_num in valid_numbers:
                    if abs(source_num - num) < 0.01:
                        matched = True
                        break
                if not matched:
                    errors.append(f"[{field_label}] Hallucinated number '{num}' in: \"{text}\"")
            
            # B. Check citations
            for cit in citations:
                if cit not in valid_ids:
                    errors.append(f"[{field_label}] Invalid citation ID '{cit}' in: \"{text}\"")

        # 1. Validate Executive Summary
        exec_text = insights.get("executive_summary", "")
        exec_nums = cls.extract_all_numbers(exec_text)
        for num in exec_nums:
            matched = False
            for source_num in valid_numbers:
                if abs(source_num - num) < 0.01:
                    matched = True
                    break
            if not matched:
                errors.append(f"[executive_summary] Hallucinated number '{num}' in: \"{exec_text}\"")

        # 2. Validate KPI Interpretations
        for idx, kpi_interp in enumerate(insights.get("kpi_interpretations", [])):
            k_id = kpi_interp.get("kpi_id")
            if k_id not in valid_ids:
                errors.append(f"[kpi_interpretations] Citations KPI ID '{k_id}' does not exist.")
            validate_statement(kpi_interp.get("interpretation", ""), kpi_interp.get("citations", []), f"kpi_interpretations[{idx}]")

        # 3. Validate Risks, Opportunities, Recommendations
        for idx, r in enumerate(insights.get("risks", [])):
            validate_statement(r.get("text", ""), r.get("citations", []), f"risks[{idx}]")
            
        for idx, o in enumerate(insights.get("opportunities", [])):
            validate_statement(o.get("text", ""), o.get("citations", []), f"opportunities[{idx}]")
            
        for idx, rec in enumerate(insights.get("recommendations", [])):
            validate_statement(rec.get("text", ""), rec.get("citations", []), f"recommendations[{idx}]")
            
        return errors

    @classmethod
    def scrub_ungrounded(cls, insights: Dict[str, Any], extracted_insights: Dict[str, Any]) -> Dict[str, Any]:
        """
        Scrubs or filters out ungrounded elements/sentences instead of failing completely.
        """
        valid_numbers = cls.get_valid_source_numbers(extracted_insights)
        valid_ids = cls.get_valid_source_ids(extracted_insights)
        
        def statement_is_valid(text: str, citations: List[str]) -> bool:
            # Check numbers
            text_nums = cls.extract_all_numbers(text)
            for num in text_nums:
                matched = False
                for s in valid_numbers:
                    if abs(s - num) < 0.01:
                        matched = True
                        break
                if not matched:
                    return False
            # Check citations
            for cit in citations:
                if cit not in valid_ids:
                    return False
            return True

        # Scrub Executive Summary by splitting sentences and filtering ungrounded ones
        exec_sentences = re.split(r'(?<=[.!?])\s+', insights.get("executive_summary", ""))
        scrubbed_sentences = []
        for sent in exec_sentences:
            # Check if numbers inside this single sentence are valid
            sent_nums = cls.extract_all_numbers(sent)
            sent_valid = True
            for num in sent_nums:
                matched = False
                for s in valid_numbers:
                    if abs(s - num) < 0.01:
                        matched = True
                        break
                if not matched:
                    sent_valid = False
                    break
            if sent_valid:
                scrubbed_sentences.append(sent)
                
        insights["executive_summary"] = " ".join(scrubbed_sentences)
        if not insights["executive_summary"]:
            insights["executive_summary"] = f"Operations analytics summary compiled for the {extracted_insights['domain_context']['domain']} dataset."

        # Scrub KPI Interpretations
        clean_kpis = []
        for k in insights.get("kpi_interpretations", []):
            if k.get("kpi_id") in valid_ids and statement_is_valid(k.get("interpretation", ""), k.get("citations", [])):
                clean_kpis.append(k)
        insights["kpi_interpretations"] = clean_kpis

        # Scrub Risks, Opportunities, Recommendations
        insights["risks"] = [r for r in insights.get("risks", []) if statement_is_valid(r.get("text", ""), r.get("citations", []))]
        insights["opportunities"] = [o for o in insights.get("opportunities", []) if statement_is_valid(o.get("text", ""), o.get("citations", []))]
        insights["recommendations"] = [rec for rec in insights.get("recommendations", []) if statement_is_valid(rec.get("text", ""), rec.get("citations", []))]

        return insights
