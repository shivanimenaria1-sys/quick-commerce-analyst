import unittest
import os
import json
import tempfile
from unittest.mock import patch, MagicMock
from app.services.kpi_generator import PipelineContext, generate_candidate_kpis
from app.services.kpi_ranking import rank_candidate_kpis
from app.services.kpi_ranking.ranker import KPIRankingsCache

class MockResponse:
    def __init__(self, text):
        self.text = text

class TestKPIPipeline(unittest.TestCase):
    def setUp(self):
        # 1. Retail context setup
        self.retail_context = PipelineContext(
            dataset_profile={
                "dataset_metadata": {"row_count": 100, "column_count": 3},
                "columns": {
                    "sales_amt": {"inferred_dtype": "float", "statistics": {"cardinality_ratio": 0.9, "null_percentage": 0.0}},
                    "cost_amt": {"inferred_dtype": "float", "statistics": {"cardinality_ratio": 0.8, "null_percentage": 0.0}}
                }
            },
            confirmed_semantic_mapping={
                "columns": {
                    "sales_amt": {"semantic_role": "revenue_like"},
                    "cost_amt": {"semantic_role": "cost_like"}
                }
            },
            domain_profile={"domain": "Retail", "confidence": 0.90, "reasoning": "Standard sales context"},
            engineered_features=[]
        )

        # 2. HR context setup
        self.hr_context = PipelineContext(
            dataset_profile={
                "dataset_metadata": {"row_count": 50, "column_count": 2},
                "columns": {
                    "emp_no": {"inferred_dtype": "id_like", "statistics": {"cardinality_ratio": 1.0, "null_percentage": 0.0}},
                    "emp_status": {"inferred_dtype": "categorical", "statistics": {"cardinality_ratio": 0.04, "null_percentage": 0.0}}
                }
            },
            confirmed_semantic_mapping={
                "columns": {
                    "emp_no": {"semantic_role": "employee_like"},
                    "emp_status": {"semantic_role": "status_like"}
                }
            },
            domain_profile={"domain": "HR", "confidence": 0.95, "reasoning": "Standard employee roster"},
            engineered_features=[]
        )

        # 3. Temp file for testing kpi rankings cache isolation
        self.temp_cache_file = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
        self.temp_cache_file.close()

    def tearDown(self):
        if os.path.exists(self.temp_cache_file.name):
            os.remove(self.temp_cache_file.name)

    def test_kpi_candidate_generator_distinct_domains(self):
        """
        Verifies that rule-based KPI Candidate Generator yields distinct,
        correct KPIs for HR versus Retail datasets.
        """
        # Run Retail candidate generation
        retail_res = generate_candidate_kpis(self.retail_context)
        retail_ids = [k["id"] for k in retail_res["candidate_kpis"]]
        
        # Verify retail specific candidates
        self.assertIn("total_revenue", retail_ids)
        self.assertIn("total_cost", retail_ids)
        self.assertIn("gross_profit", retail_ids)
        self.assertIn("profit_margin", retail_ids)
        self.assertNotIn("headcount", retail_ids)
        
        # Verify schema elements: formula, aggregation, roles, generator_plugin, explanation, dependencies
        profit_kpi = [k for k in retail_res["candidate_kpis"] if k["id"] == "gross_profit"][0]
        self.assertEqual(profit_kpi["aggregation"], "SUM")
        self.assertEqual(profit_kpi["generator_plugin"], "revenue_cost_plugin")
        self.assertEqual(profit_kpi["required_semantic_roles"], ["revenue_like", "cost_like"])
        self.assertIn("total_revenue", profit_kpi["dependencies"])
        self.assertIn("total_cost", profit_kpi["dependencies"])
        
        # Verify structured formula metadata
        self.assertEqual(profit_kpi["formula"]["operation"], "SUBTRACT")
        self.assertEqual(profit_kpi["formula"]["fields"], ["revenue_like", "cost_like"])

        # Run HR candidate generation
        hr_res = generate_candidate_kpis(self.hr_context)
        hr_ids = [k["id"] for k in hr_res["candidate_kpis"]]
        
        # Verify HR specific candidates
        self.assertIn("headcount", hr_ids)
        self.assertIn("active_employees", hr_ids)
        self.assertIn("attrition_rate", hr_ids)
        self.assertNotIn("total_revenue", hr_ids)

    @patch("app.services.kpi_ranking.ranker.get_gemini_client")
    @patch("app.services.kpi_ranking.ranker.KPIRankingsCache")
    def test_kpi_ranking_and_fingerprint_caching(self, mock_cache_cls, mock_get_client):
        """
        Verifies LLM ranks precomputed candidate list, respects constraints
        (cannot change calculation formulas), and is cached correctly.
        """
        # Set up mock cache provider
        mock_cache = MagicMock()
        mock_cache_cls.return_value = mock_cache
        mock_cache.get.return_value = None  # Cache miss initially
        
        # Mock Gemini ranker client
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        
        mock_ranking_json = {
            "selected_kpis": [
                {
                    "candidate_id": "total_revenue",
                    "display_label": "Gross Sales Revenue",
                    "rank": 1,
                    "importance": 0.98,
                    "reason": "Indicates direct top-line retail sales."
                },
                {
                    "candidate_id": "gross_profit",
                    "display_label": "Net Profit Margin",
                    "rank": 2,
                    "importance": 0.95,
                    "reason": "Direct operational profit indicator."
                }
            ]
        }
        mock_client.models.generate_content.return_value = MockResponse(json.dumps(mock_ranking_json))

        candidates = {
            "candidate_kpis": [
                {
                    "id": "total_revenue",
                    "display_name": "Total Revenue",
                    "formula": {"operation": "SUM", "fields": ["revenue_like"]},
                    "aggregation": "SUM",
                    "required_semantic_roles": ["revenue_like"],
                    "generator_plugin": "revenue_cost_plugin",
                    "explanation": "Calculates the sum of all transaction revenue fields.",
                    "dependencies": []
                },
                {
                    "id": "gross_profit",
                    "display_name": "Gross Profit",
                    "formula": {"operation": "SUBTRACT", "fields": ["revenue_like", "cost_like"]},
                    "aggregation": "SUM",
                    "required_semantic_roles": ["revenue_like", "cost_like"],
                    "generator_plugin": "revenue_cost_plugin",
                    "explanation": "Calculates profit.",
                    "dependencies": []
                }
            ]
        }

        # Run ranking
        rankings = rank_candidate_kpis(self.retail_context, candidates)
        
        # Verify ranking results
        self.assertIsNotNone(rankings)
        self.assertEqual(len(rankings["selected_kpis"]), 2)
        
        # Check display labels are overridden by LLM
        first_kpi = rankings["selected_kpis"][0]
        self.assertEqual(first_kpi["id"], "total_revenue")
        self.assertEqual(first_kpi["display_name"], "Gross Sales Revenue")
        self.assertEqual(first_kpi["rank"], 1)
        self.assertEqual(first_kpi["importance"], 0.98)
        
        # Check that core formulas remain untouched by ranking engine
        self.assertEqual(first_kpi["formula"]["operation"], "SUM")
        self.assertEqual(first_kpi["formula"]["fields"], ["revenue_like"])
        
        # Verify Gemini called exactly once
        self.assertEqual(mock_client.models.generate_content.call_count, 1)
        # Verify cached
        mock_cache.set.assert_called_once()

if __name__ == "__main__":
    unittest.main()
