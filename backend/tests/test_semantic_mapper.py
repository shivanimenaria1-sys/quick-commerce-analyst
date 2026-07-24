import unittest
import os
import json
import tempfile
from unittest.mock import patch, MagicMock
from app.services.semantic_mapper import map_semantics, save_correction, generate_schema_fingerprint, JSONFileCacheProvider

class MockResponse:
    def __init__(self, text):
        self.text = text

class TestSemanticMapper(unittest.TestCase):
    def setUp(self):
        # Temp files for cache and corrections to isolate tests
        self.temp_cache_file = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
        with open(self.temp_cache_file.name, 'w') as f:
            f.write("{}")
        self.temp_cache_file.close()
        
        # Instantiate cache provider with temp file
        self.cache_provider = JSONFileCacheProvider(file_path=self.temp_cache_file.name)
        
        # Retail dataset profile mock
        self.retail_profile = {
            "schema_version": "1.0.0",
            "dataset_metadata": {"row_count": 100, "column_count": 4},
            "columns": {
                "Transaction_ID": {
                    "inferred_dtype": "id_like",
                    "confidence_score": 0.95,
                    "statistics": {"cardinality_ratio": 1.0, "null_percentage": 0.0, "sample_values": ["TX001", "TX002"]}
                },
                "Sale_Date": {
                    "inferred_dtype": "datetime",
                    "confidence_score": 1.0,
                    "statistics": {"cardinality_ratio": 0.5, "null_percentage": 0.0, "sample_values": ["2026-06-02", "2026-06-03"]}
                },
                "Amount_USD": {
                    "inferred_dtype": "float",
                    "confidence_score": 0.98,
                    "statistics": {"cardinality_ratio": 0.9, "null_percentage": 0.0, "sample_values": ["$100.00", "$250.50"]}
                },
                "Low_Conf_Col": {
                    "inferred_dtype": "categorical",
                    "confidence_score": 0.45,
                    "statistics": {"cardinality_ratio": 0.2, "null_percentage": 10.0, "sample_values": ["val1", "val2"]}
                }
            }
        }

    def tearDown(self):
        if os.path.exists(self.temp_cache_file.name):
            os.remove(self.temp_cache_file.name)

    @patch("app.services.semantic_mapper.mapper.get_gemini_client")
    def test_semantic_mapping_generation_and_caching(self, mock_get_client):
        """
        Verifies that map_semantics correctly hits the LLM, parses response,
        applies threshold logic, caches the results, and hits the cache on a repeat request.
        """
        # Mock Gemini response
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        
        mock_json_response = {
            "mappings": [
                {
                    "column_name": "Transaction_ID",
                    "semantic_role": "id_like",
                    "confidence": 0.98,
                    "reasoning": "Primary key column.",
                    "alternative_roles": []
                },
                {
                    "column_name": "Sale_Date",
                    "semantic_role": "date_like",
                    "confidence": 0.95,
                    "reasoning": "Represents sale dates.",
                    "alternative_roles": []
                },
                {
                    "column_name": "Amount_USD",
                    "semantic_role": "revenue_like",
                    "confidence": 0.92,
                    "reasoning": "Transaction values.",
                    "alternative_roles": [{"role": "price_like", "confidence": 0.30}]
                },
                {
                    "column_name": "Low_Conf_Col",
                    "semantic_role": "category_like",
                    "confidence": 0.40,  # Low confidence to trigger user confirmation
                    "reasoning": "Unclear category naming.",
                    "alternative_roles": []
                }
            ]
        }
        
        mock_client.models.generate_content.return_value = MockResponse(json.dumps(mock_json_response))
        
        # 1. First run (Cache miss)
        mapping = map_semantics(self.retail_profile, cache_provider=self.cache_provider)
        
        self.assertIsNotNone(mapping)
        self.assertEqual(len(mapping["columns"]), 4)
        
        # Check standard properties
        self.assertEqual(mapping["columns"]["Transaction_ID"]["semantic_role"], "id_like")
        self.assertEqual(mapping["columns"]["Amount_USD"]["semantic_role"], "revenue_like")
        self.assertEqual(len(mapping["columns"]["Amount_USD"]["alternative_roles"]), 1)
        
        # Check user confirmation flag (confidence 0.40 < 0.60 should be True)
        self.assertTrue(mapping["columns"]["Low_Conf_Col"]["needs_user_confirmation"])
        self.assertFalse(mapping["columns"]["Transaction_ID"]["needs_user_confirmation"])
        
        # Check that Gemini was called exactly once
        self.assertEqual(mock_client.models.generate_content.call_count, 1)
        
        # 2. Second run (Cache hit)
        # Reset mock call count
        mock_client.models.generate_content.reset_mock()
        
        cached_mapping = map_semantics(self.retail_profile, cache_provider=self.cache_provider)
        self.assertEqual(cached_mapping, mapping)
        
        # Verify Gemini was NOT called again
        mock_client.models.generate_content.assert_not_called()

    @patch("app.services.semantic_mapper.corrections.JSONFileCacheProvider")
    def test_corrections_log_and_cache_override(self, mock_json_provider):
        """
        Validates that save_correction appends correction to file and updates cache mapping.
        """
        # Set up mock cache provider in corrections
        mock_cache = MagicMock()
        mock_json_provider.return_value = mock_cache
        
        fingerprint = generate_schema_fingerprint(self.retail_profile)
        mock_cache_data = {
            "schema_fingerprint": fingerprint,
            "columns": {
                "Amount_USD": {
                    "semantic_role": "revenue_like",
                    "confidence": 0.92,
                    "reasoning": "Transaction values.",
                    "alternative_roles": [],
                    "needs_user_confirmation": False
                }
            }
        }
        mock_cache.get.return_value = mock_cache_data
        
        # Trigger correction override
        save_correction(
            fingerprint=fingerprint,
            column_name="Amount_USD",
            original_role="revenue_like",
            corrected_role="price_like"
        )
        
        # Verify cache update checks
        mock_cache.get.assert_called_with(fingerprint)
        mock_cache.set.assert_called_once()
        
        # Verify cache content update
        updated_cache = mock_cache.set.call_args[0][1]
        self.assertEqual(updated_cache["columns"]["Amount_USD"]["semantic_role"], "price_like")
        self.assertEqual(updated_cache["columns"]["Amount_USD"]["confidence"], 1.0)
        self.assertFalse(updated_cache["columns"]["Amount_USD"]["needs_user_confirmation"])

if __name__ == "__main__":
    unittest.main()
