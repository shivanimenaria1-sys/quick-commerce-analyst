import unittest
from app.services.insight_generator.validator import NarrativeValidator
from app.services.insight_generator.extractor import InsightExtractionEngine
from app.services.report_generator.exporter import HTMLReportExporter, PDFReportExporter

class TestInsightsPipeline(unittest.TestCase):
    def setUp(self):
        # Deterministic inputs setup
        self.retail_insights = {
            "domain_context": {"domain": "Retail", "confidence": 0.95, "reasoning": "Txn sales logs"},
            "kpi_metrics": [
                {"kpi_id": "total_revenue", "display_name": "Total Revenue", "value": 54200.5, "aggregation": "SUM"}
            ],
            "trends": [
                {"trend_id": "trend_total_revenue", "metric": "total_revenue", "direction": "upward", "pct_change": 12.5}
            ],
            "anomalies": [
                {"anomaly_id": "anomaly_discount", "column_name": "discount_amt", "anomaly_type": "outliers_detected", "count": 14}
            ],
            "correlations": []
        }

        # Mock LLM response containing a hallucinated number (999.0 or 1234.5)
        self.mock_llm_response = {
            "executive_summary": "We analyzed Retail sales operations showing total revenue of 54200.5. However, we also found 999.0 errors.",
            "kpi_interpretations": [
                {
                    "kpi_id": "total_revenue",
                    "interpretation": "Sales revenue shows an upward trend of 12.5% MoM, with a final value of 54200.5.",
                    "citations": ["total_revenue", "trend_total_revenue"]
                }
            ],
            "risks": [
                {
                    "text": "Detected 14 outliers in discount amounts.",
                    "citations": ["anomaly_discount"]
                },
                {
                    "text": "Critical: high null concentration of 1234.5 items.",
                    "citations": ["anomaly_discount"]
                }
            ],
            "opportunities": [
                {
                    "text": "Capitalize on the upward revenue momentum of 12.5%.",
                    "citations": ["trend_total_revenue"]
                }
            ],
            "recommendations": [
                {
                    "text": "Consider reviewing store layouts.",
                    "citations": ["total_revenue"]
                }
            ]
        }

    def test_narrative_validator_grounding(self):
        """
        Verifies that NarrativeValidator correctly flags and scrubs hallucinated numbers.
        """
        # Validate raw response (should catch 999.0 in summary and 1234.5 in risks)
        errors = NarrativeValidator.validate(self.mock_llm_response, self.retail_insights)
        self.assertTrue(len(errors) > 0, "Validation should flag hallucinated numbers")
        
        # Check specific errors
        has_summary_error = any("999" in err for err in errors)
        has_risk_error = any("1234" in err for err in errors)
        self.assertTrue(has_summary_error)
        self.assertTrue(has_risk_error)
        
        # Scrub ungrounded values
        import copy
        scrubbed = NarrativeValidator.scrub_ungrounded(copy.deepcopy(self.mock_llm_response), self.retail_insights)
        
        # Validate scrubbed response
        clean_errors = NarrativeValidator.validate(scrubbed, self.retail_insights)
        self.assertEqual(len(clean_errors), 0, "Scrubbed response should have 0 validation errors")
        
        # Verify ungrounded sentences and risk cards are removed
        self.assertNotIn("999", scrubbed["executive_summary"])
        self.assertIn("54200.5", scrubbed["executive_summary"])
        self.assertEqual(len(scrubbed["risks"]), 1, "The risk containing 1234.5 should have been scrubbed")
        self.assertEqual(scrubbed["risks"][0]["text"], "Detected 14 outliers in discount amounts.")

    def test_adaptive_report_exporters(self):
        """
        Verifies that report exporters dynamically adapt formatting and wordings
        by domain (Retail vs HR), and return valid content.
        """
        retail_pipeline = {
            "domain_profile": {"domain": "Retail", "confidence": 0.95},
            "dataset_profile": {"columns": {"sales": {}}}
        }
        
        hr_pipeline = {
            "domain_profile": {"domain": "HR", "confidence": 0.90},
            "dataset_profile": {"columns": {"dept": {}}}
        }

        # Run HTML Exporters
        html_exporter = HTMLReportExporter()
        
        retail_html = html_exporter.export(retail_pipeline, self.mock_llm_response).decode('utf-8')
        hr_html = html_exporter.export(hr_pipeline, self.mock_llm_response).decode('utf-8')
        
        # Verify distinct titles adapted to domain classification
        self.assertIn("Retail Sales Performance", retail_html)
        self.assertIn("Human Resources Roster", hr_html)
        self.assertNotIn("Retail Sales Performance", hr_html)
        
        # Run PDF Exporter (should return valid bytes, either PDF format or fallback HTML)
        pdf_exporter = PDFReportExporter()
        retail_pdf = pdf_exporter.export(retail_pipeline, self.mock_llm_response)
        
        self.assertTrue(len(retail_pdf) > 0)
        self.assertTrue(isinstance(retail_pdf, bytes))

if __name__ == "__main__":
    unittest.main()
