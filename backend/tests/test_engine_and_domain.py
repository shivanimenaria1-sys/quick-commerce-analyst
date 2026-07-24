import unittest
import json
import pandas as pd
from unittest.mock import patch, MagicMock
from app.services.domain_classifier.classifier import classify_domain
from app.services.feature_engineering_engine import engineer_features

class MockResponse:
    def __init__(self, text):
        self.text = text

class TestEngineAndDomain(unittest.TestCase):
    def setUp(self):
        # 1. Mock dataset profile for Domain Classifier
        self.mock_dataset_profile = {
            "dataset_metadata": {"row_count": 100, "column_count": 5},
            "columns": {
                "Order_Category": {
                    "inferred_dtype": "categorical",
                    "statistics": {
                        "top_frequencies": {"Groceries": 45, "Electronics": 30, "Apparel": 25}
                    }
                }
            }
        }
        
        # 2. Test DataFrame for Feature Engineering Engine
        self.df = pd.DataFrame({
            "order_date": ["02-06-2026", "03-06-2026", "04-06-2026", "05-06-2026", "06-06-2026", "07-06-2026", "08-06-2026"],
            "sales_amt": [100.0, 200.0, 150.0, 300.0, 400.0, 250.0, 500.0],
            "expense_amt": [80.0, 150.0, 120.0, 270.0, 320.0, 200.0, 410.0],
            "uid": ["CUST1", "CUST2", "CUST1", "CUST3", "CUST2", "CUST1", "CUST4"],
            "dept_group": ["Sales", "HR", "Sales", "Engineering", "HR", "Sales", "Engineering"],
            "handling_time": [10.5, 25.0, 14.0, 32.5, 8.0, 19.5, 45.0]
        })
        
        self.semantic_mapping = {
            "columns": {
                "order_date": {"semantic_role": "date_like"},
                "sales_amt": {"semantic_role": "revenue_like"},
                "expense_amt": {"semantic_role": "cost_like"},
                "uid": {"semantic_role": "customer_id_like"},
                "dept_group": {"semantic_role": "category_like"},
                "handling_time": {"semantic_role": "duration_like"}
            }
        }

    @patch("app.services.domain_classifier.classifier.get_gemini_client")
    def test_domain_classifier_success(self, mock_get_client):
        """
        Validates that domain classifier queries LLM and outputs correct classification,
        respecting allowed options and defaultings.
        """
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        
        # Scenario A: High confidence Retail classification
        mock_json_retail = {
            "primary_domain": "Retail",
            "confidence": 0.95,
            "secondary_domains": [{"domain": "Logistics", "confidence": 0.41}],
            "reasoning": "Contains transaction sales data."
        }
        mock_client.models.generate_content.return_value = MockResponse(json.dumps(mock_json_retail))
        
        mapping = {"columns": {"sales_amt": "revenue_like"}}
        res = classify_domain(mapping, self.mock_dataset_profile)
        self.assertEqual(res["domain"], "Retail")
        self.assertEqual(res["confidence"], 0.95)
        
        # Scenario B: Low confidence classification (< 0.50) falls back to Generic
        mock_json_low_conf = {
            "primary_domain": "Healthcare",
            "confidence": 0.35,
            "secondary_domains": [],
            "reasoning": "Unclear terms present."
        }
        mock_client.models.generate_content.return_value = MockResponse(json.dumps(mock_json_low_conf))
        res_low = classify_domain(mapping, self.mock_dataset_profile)
        self.assertEqual(res_low["domain"], "Generic")
        self.assertEqual(res_low["confidence"], 0.50)

    def test_feature_engineering_engine_derivation(self):
        """
        Verifies that feature engineering engine successfully derives all features
        based exclusively on the semantic roles list, with no hardcoded column names.
        """
        enriched_df, metadata = engineer_features(self.df, self.semantic_mapping)
        
        self.assertFalse(enriched_df.empty)
        
        # 1. Assert Date extraction features
        self.assertIn("order_date_day_of_week", enriched_df.columns)
        self.assertIn("order_date_is_weekend", enriched_df.columns)
        self.assertIn("order_date_season", enriched_df.columns)
        self.assertEqual(enriched_df.loc[0, "order_date_day_of_week"], "Tuesday")
        self.assertEqual(enriched_df.loc[4, "order_date_is_weekend"], True) # June 6 2026 is Saturday
        
        # 2. Assert Profit Margin calculations
        self.assertIn("calculated_net_profit", enriched_df.columns)
        self.assertIn("calculated_profit_margin_pct", enriched_df.columns)
        self.assertIn("calculated_profit_margin_bucket", enriched_df.columns)
        self.assertAlmostEqual(enriched_df.loc[0, "calculated_net_profit"], 20.0)
        self.assertAlmostEqual(enriched_df.loc[0, "calculated_profit_margin_pct"], 20.0)
        self.assertEqual(enriched_df.loc[0, "calculated_profit_margin_bucket"], "Medium Margin")
        
        # 3. Assert Loyalty/Frequency indicators
        self.assertIn("uid_frequency", enriched_df.columns)
        self.assertIn("uid_is_repeat_customer", enriched_df.columns)
        # uid "CUST1" occurs 3 times
        self.assertEqual(enriched_df.loc[0, "uid_frequency"], 3.0)
        self.assertEqual(enriched_df.loc[0, "uid_is_repeat_customer"], True)
        # uid "CUST4" occurs 1 time
        self.assertEqual(enriched_df.loc[6, "uid_frequency"], 1.0)
        self.assertEqual(enriched_df.loc[6, "uid_is_repeat_customer"], False)
        
        # 4. Assert Rolling metrics
        self.assertIn("calculated_revenue_moving_avg_7d", enriched_df.columns)
        self.assertIn("calculated_revenue_rolling_total_7d", enriched_df.columns)
        # Total sum of sales_amt should match final rolling total on day 7
        self.assertAlmostEqual(enriched_df.loc[6, "calculated_revenue_rolling_total_7d"], sum(self.df["sales_amt"]))
        
        # 5. Assert Categorical aggregates
        self.assertIn("dept_group_proportion", enriched_df.columns)
        # "Sales" occurs 3 out of 7 times -> ~0.4285
        self.assertAlmostEqual(enriched_df.loc[0, "dept_group_proportion"], 3/7)
        
        # 6. Assert Duration bucketing
        self.assertIn("handling_time_bucket", enriched_df.columns)
        self.assertIn("handling_time_exceeds_median", enriched_df.columns)
        self.assertEqual(enriched_df.loc[0, "handling_time_bucket"], "Fast (<15m)")
        self.assertEqual(enriched_df.loc[6, "handling_time_bucket"], "Delayed (>30m)")
        # Median is 19.5, 45.0 > 19.5 -> True
        self.assertEqual(enriched_df.loc[6, "handling_time_exceeds_median"], True)
        
        # 7. Check metadata compilation
        self.assertTrue(len(metadata) > 0)
        for meta in metadata:
            self.assertIn("feature_name", meta)
            self.assertIn("source_semantic_roles", meta)
            self.assertIn("generation_rule", meta)
            self.assertIn("output_type", meta)
            
            # Assert feature names actually match output column headers
            self.assertIn(meta["feature_name"], enriched_df.columns)

if __name__ == "__main__":
    unittest.main()
