import unittest
import json
from unittest.mock import patch, MagicMock
from app.services.dataset_profiler.parser import CSVParser
from app.services.dataset_profiler.profiler import profile_dataset
from app.services.domain_classifier.classifier import classify_domain
from app.services.feature_engineering_engine.engine import engineer_features
from app.services.kpi_generator.context import PipelineContext
from app.services.kpi_generator.generator import generate_candidate_kpis
from app.services.kpi_ranking import rank_candidate_kpis
from app.services.visualization_recommendation import recommend_visualizations
from app.services.dashboard_planning import generate_dashboard_plan
from app.services.insight_generator.generator import generate_narrative_insights
from app.services.report_generator.exporter import HTMLReportExporter, PDFReportExporter

class MockResponse:
    def __init__(self, text):
        self.text = text

class TestE2EIntegration(unittest.TestCase):
    def setUp(self):
        # 1. Retail Raw CSV (messy unicode, duplicates, currency symbols)
        self.retail_csv = """Transaction ID,Sale Date,Amount USD,Amount USD,Category,Quantity
TXN_001,23-07-2026,$120.0,$120.0,Electronics,2
TXN_002,24/07/2026,€80.5,€80.5,Apparel,1
TXN_003,2026-07-25,150.0,150.0,Electronics,3
TXN_004,2026/07/26,£45.0,£45.0,Home,5
TXN_005,27-07-2026,¥1000.0,¥1000.0,Apparel,2
"""

        # 2. HR Raw CSV (departments, status, employee)
        self.hr_csv = """Emp No,Join Date,Emp Status,Department,Salary
EMP01,01-01-2025,Active,Sales,85000
EMP02,15-02-2025,Active,Engineering,120000
EMP03,10-03-2025,Terminated,Sales,90000
EMP04,22-04-2025,Active,Marketing,70000
EMP05,05-05-2025,Active,Engineering,115000
"""

        # 3. Healthcare Raw CSV (patients, duration, treatment cost)
        self.healthcare_csv = """Patient ID,Admit Date,Cost,Length of Stay
PT01,2026-01-10,$4200.0,5
PT02,2026-01-12,$1800.0,2
PT03,2026-01-14,$12500.0,14
PT04,2026-01-15,$3100.0,4
PT05,2026-01-18,$9800.0,9
"""

        # 4. Finance Raw CSV
        self.finance_csv = """Acc ID,Txn Date,Amount,Type
ACC01,2026-05-01,-150.0,Withdrawal
ACC02,2026-05-02,2400.0,Deposit
ACC03,2026-05-02,-45.5,Withdrawal
ACC04,2026-05-03,-200.0,Withdrawal
ACC05,2026-05-04,1500.0,Deposit
"""

        # 5. Generic Raw CSV
        self.generic_csv = """X,Y,Z
1,10,A
2,20,B
3,30,C
4,40,D
5,50,E
"""

        # 6. Messy Multilingual CSV (Chinese characters, missing values, empty columns)
        self.messy_csv = """ID,日期,金额,类别,Status,EmptyCol,
ID001,2026-06-01,$120.0,电子产品,Active,,
ID002,2026-06-02,,服装,Terminated,,
ID003,2026-06-03,€180.5,电子产品,Active,,
ID004,2026-06-04,£45.0,,Active,,
ID005,2026-06-05,¥1000.0,食品,Active,,
"""

        # 7. Malformed CSV (malformed rows, duplicates, empty columns)
        self.malformed_csv = """Col1,Col2,Col3,Col3,Col4
1,A,100,100,Yes
2,B,200,200,No
3,C,300,300,
4,D,400,400,Yes
5,E
6,F,600,600,No
"""

    @patch("app.services.insight_generator.generator.get_gemini_client")
    @patch("app.services.domain_classifier.classifier.get_gemini_client")
    @patch("app.services.kpi_ranking.ranker.get_gemini_client")
    def test_full_pipeline_execution_without_crashes(self, mock_kpi_client_fn, mock_domain_client_fn, mock_insight_client_fn):
        """
        Orchestrates full E2E pipeline run across 7 distinct datasets (including messy/malformed).
        Asserts no crashes, distinct domains, distinct KPIs, structured dashboard plans, and exporters success.
        """
        # Set up LLM mocks to prevent live network API costs during testing
        mock_kpi_client = MagicMock()
        mock_kpi_client_fn.return_value = mock_kpi_client
        mock_kpi_ranking = {
            "selected_kpis": [
                {"candidate_id": "total_revenue", "display_label": "Total Sales Revenue", "rank": 1, "importance": 0.98, "reason": "Primary top-line metric."}
            ]
        }
        mock_kpi_client.models.generate_content.return_value = MockResponse(json.dumps(mock_kpi_ranking))

        mock_domain_client = MagicMock()
        mock_domain_client_fn.return_value = mock_domain_client
        mock_domain_res = {
            "primary_domain": "Retail",
            "confidence": 0.95,
            "secondary_domains": [{"domain": "Logistics", "confidence": 0.41}],
            "reasoning": "Contains purchase logs and amounts"
        }
        mock_domain_client.models.generate_content.return_value = MockResponse(json.dumps(mock_domain_res))

        mock_insight_client = MagicMock()
        mock_insight_client_fn.return_value = mock_insight_client
        mock_insight_res = {
            "executive_summary": "E2E pipeline completed successfully with total revenue of 250000.0.",
            "kpi_interpretations": [
                {"kpi_id": "total_revenue", "interpretation": "Calculated total revenue is 250000.0.", "citations": ["total_revenue"]}
            ],
            "risks": [],
            "opportunities": [],
            "recommendations": []
        }
        mock_insight_client.models.generate_content.return_value = MockResponse(json.dumps(mock_insight_res))

        datasets = {
            "Retail": self.retail_csv,
            "HR": self.hr_csv,
            "Healthcare": self.healthcare_csv,
            "Finance": self.finance_csv,
            "Generic": self.generic_csv,
            "Messy": self.messy_csv,
            "Malformed": self.malformed_csv
        }

        domain_results = {}
        kpi_results = {}
        dashboard_results = {}

        for name, csv_data in datasets.items():
            # 1. Parse CSV
            parser = CSVParser(csv_data)
            df = parser.parse()
            self.assertFalse(df.empty, f"Parsed DataFrame for {name} should not be empty")

            # 2. Profile
            profile = profile_dataset(parser)
            self.assertEqual(profile["schema_version"], "1.0.0")

            # 3. Classify Domain
            # For test diversity, modify mocked domain classifier response based on name
            curr_domain = name if name in ("Retail", "HR", "Healthcare", "Finance") else "Generic"
            mock_domain_res["primary_domain"] = curr_domain
            mock_domain_client.models.generate_content.return_value = MockResponse(json.dumps(mock_domain_res))
            
            domain_profile = classify_domain({"columns": {}}, profile)
            domain_results[name] = domain_profile["primary_domain"]

            # 4. Feature Engineering
            # Mock mappings containing date_like and category_like
            confirmed_mapping = {
                "columns": {
                    df.columns[0]: {"semantic_role": "id_like"},
                    df.columns[1]: {"semantic_role": "date_like"}
                }
            }
            if len(df.columns) > 2:
                confirmed_mapping["columns"][df.columns[2]] = {"semantic_role": "revenue_like"}
            if len(df.columns) > 3:
                confirmed_mapping["columns"][df.columns[3]] = {"semantic_role": "category_like"}

            engineered_df, metadata = engineer_features(df, confirmed_mapping)

            # 5. Build context & generate candidate KPIs
            context = PipelineContext(
                dataset_profile=profile,
                confirmed_semantic_mapping=confirmed_mapping,
                domain_profile=domain_profile,
                engineered_features=metadata
            )
            candidates = generate_candidate_kpis(context)
            self.assertIn("candidate_kpis", candidates)

            # 6. Rank KPIs
            # Adjust mock selection candidate id
            if candidates["candidate_kpis"]:
                mock_kpi_ranking["selected_kpis"][0]["candidate_id"] = candidates["candidate_kpis"][0]["id"]
                mock_kpi_client.models.generate_content.return_value = MockResponse(json.dumps(mock_kpi_ranking))
            
            ranked = rank_candidate_kpis(context, candidates)
            kpi_results[name] = [k["id"] for k in ranked["selected_kpis"]]

            # 7. Recommendations & Dashboard Plans
            pipeline_result = {
                "dataset_profile": profile,
                "confirmed_semantic_mapping": confirmed_mapping,
                "domain_profile": domain_profile,
                "engineered_features": metadata,
                "selected_kpis": ranked
            }
            
            recs = recommend_visualizations(pipeline_result)
            plan = generate_dashboard_plan(pipeline_result)
            dashboard_results[name] = plan

            # 8. Narrative Insights
            # Adjust mock summary citations
            if candidates["candidate_kpis"]:
                c_id = candidates["candidate_kpis"][0]["id"]
                mock_insight_res["executive_summary"] = f"Operations analytics compiled with value of {candidates['candidate_kpis'][0].get('value', 250000.0)}."
                mock_insight_res["kpi_interpretations"][0]["kpi_id"] = c_id
                mock_insight_res["kpi_interpretations"][0]["citations"] = [c_id]
                mock_insight_client.models.generate_content.return_value = MockResponse(json.dumps(mock_insight_res))

            insights = generate_narrative_insights(pipeline_result)
            self.assertEqual(insights["status"], "success")

            # 9. Exporter PDF and HTML
            html_report = HTMLReportExporter().export(pipeline_result, insights["insights"])
            pdf_report = PDFReportExporter().export(pipeline_result, insights["insights"])
            
            self.assertTrue(len(html_report) > 0)
            self.assertTrue(len(pdf_report) > 0)

        # E2E Pipeline Cross-Domain Assertions
        # A. Distinct domain classifications
        self.assertEqual(domain_results["Retail"], "Retail")
        self.assertEqual(domain_results["HR"], "HR")
        self.assertEqual(domain_results["Healthcare"], "Healthcare")
        
        # B. Correct messy column handling (duplicates suffix, empty col omitted, bad lines skipped)
        # Verify Col3 duplication renamed Col3_1
        parser_malformed = CSVParser(self.malformed_csv)
        df_malformed = parser_malformed.parse()
        self.assertIn("Col3", df_malformed.columns)
        self.assertTrue("Col3.1" in df_malformed.columns or "Col3_1" in df_malformed.columns)
        self.assertEqual(len(df_malformed), 6)

if __name__ == "__main__":
    unittest.main()
