import unittest
from app.services.visualization_recommendation import recommend_visualizations
from app.services.dashboard_planning import generate_dashboard_plan

class TestVisualizationPipeline(unittest.TestCase):
    def setUp(self):
        # 1. Retail Profile Mock (dates, categories, status, revenue KPIs)
        self.retail_result = {
            "dataset_profile": {
                "dataset_metadata": {"row_count": 1000, "column_count": 4},
                "columns": {
                    "txn_date": {"inferred_dtype": "datetime", "statistics": {"unique_value_count": 120}},
                    "sales_category": {"inferred_dtype": "categorical", "statistics": {"unique_value_count": 5}},  # <= 7 values (pie chart allowed)
                    "store_region": {"inferred_dtype": "categorical", "statistics": {"unique_value_count": 12}},    # <= 15 values (bar chart allowed)
                    "sales_amount": {"inferred_dtype": "float", "statistics": {"median": 150.0}}
                }
            },
            "confirmed_semantic_mapping": {
                "columns": {
                    "txn_date": {"semantic_role": "date_like"},
                    "sales_category": {"semantic_role": "category_like"},
                    "store_region": {"semantic_role": "location_like"},
                    "sales_amount": {"semantic_role": "revenue_like"}
                }
            },
            "selected_kpis": {
                "selected_kpis": [
                    {"id": "total_revenue", "display_name": "Total Revenue", "aggregation": "SUM", "selected": True}
                ]
            }
        }

        # 2. High Cardinality Mock to verify Pie chart restriction (> 7 categories)
        self.high_card_result = {
            "dataset_profile": {
                "dataset_metadata": {"row_count": 500, "column_count": 3},
                "columns": {
                    "large_cat": {"inferred_dtype": "categorical", "statistics": {"unique_value_count": 8}},  # > 7 values (pie chart FORBIDDEN)
                    "huge_cat": {"inferred_dtype": "categorical", "statistics": {"unique_value_count": 22}}, # > 15 values (treemap recommended)
                    "revenue_amt": {"inferred_dtype": "float", "statistics": {"median": 80.0}}
                }
            },
            "confirmed_semantic_mapping": {
                "columns": {
                    "large_cat": {"semantic_role": "category_like"},
                    "huge_cat": {"semantic_role": "category_like"},
                    "revenue_amt": {"semantic_role": "revenue_like"}
                }
            },
            "selected_kpis": {
                "selected_kpis": [
                    {"id": "total_revenue", "display_name": "Total Revenue", "aggregation": "SUM", "selected": True}
                ]
            }
        }

        # 3. HR Profile Mock
        self.hr_result = {
            "dataset_profile": {
                "dataset_metadata": {"row_count": 200, "column_count": 3},
                "columns": {
                    "emp_id": {"inferred_dtype": "id_like", "statistics": {"unique_value_count": 200}},
                    "dept_name": {"inferred_dtype": "categorical", "statistics": {"unique_value_count": 6}},
                    "employment_status": {"inferred_dtype": "categorical", "statistics": {"unique_value_count": 3}}
                }
            },
            "confirmed_semantic_mapping": {
                "columns": {
                    "emp_id": {"semantic_role": "employee_like"},
                    "dept_name": {"semantic_role": "category_like"},
                    "employment_status": {"semantic_role": "status_like"}
                }
            },
            "selected_kpis": {
                "selected_kpis": [
                    {"id": "headcount", "display_name": "Employee Headcount", "aggregation": "COUNT", "selected": True}
                ]
            }
        }

    def test_visualization_recommender_rules(self):
        """
        Verifies chart recommendations conform to exact deterministic rules,
        specifically line trends and cardinality restrictions.
        """
        # Test Retail recommendations
        recs = recommend_visualizations(self.retail_result)
        self.assertTrue(len(recs) > 0)
        
        # Verify line chart trend
        trend_recs = [r for r in recs if r["chart_type"] == "line"]
        self.assertTrue(len(trend_recs) > 0)
        self.assertEqual(trend_recs[0]["required_kpis"], ["total_revenue"])
        self.assertEqual(trend_recs[0]["required_roles"], ["date_like"])
        
        # Verify pie chart recommended for cardinality <= 7 (sales_category has 5)
        pie_recs = [r for r in recs if r["chart_id"] == "pie_sales_category_total_revenue"]
        self.assertEqual(len(pie_recs), 1)
        self.assertEqual(pie_recs[0]["chart_type"], "pie")
        
        # Verify bar chart recommended for cardinality <= 15 (store_region has 12)
        bar_recs = [r for r in recs if r["chart_id"] == "bar_grouped_store_region_total_revenue"]
        self.assertEqual(len(bar_recs), 1)
        self.assertEqual(bar_recs[0]["chart_type"], "bar")

    def test_pie_chart_cardinality_forbidding(self):
        """
        Verifies that pie chart recommendations are STRICTLY forbidden
        when categorical cardinality exceeds 7 values.
        """
        recs = recommend_visualizations(self.high_card_result)
        
        # Check that no pie chart is suggested for large_cat (cardinality 8 > 7)
        pie_charts = [r for r in recs if r["chart_type"] == "pie"]
        self.assertEqual(len(pie_charts), 0, "Pie charts must be forbidden for cardinality > 7")
        
        # Check that large_cat (8 values) got recommended a bar chart
        large_cat_bar = [r for r in recs if r["chart_id"] == "bar_large_cat_total_revenue"]
        self.assertEqual(len(large_cat_bar), 1)
        self.assertEqual(large_cat_bar[0]["chart_type"], "bar")
        
        # Check that huge_cat (22 values > 15) got recommended a treemap
        huge_cat_treemap = [r for r in recs if r["chart_id"] == "treemap_huge_cat_total_revenue"]
        self.assertEqual(len(huge_cat_treemap), 1)
        self.assertEqual(huge_cat_treemap[0]["chart_type"], "treemap")

    def test_dashboard_planning_sections_and_filters(self):
        """
        Verifies dashboard plans segment layouts and generate semantic filter types dynamically.
        """
        # Run Retail dashboard plan
        retail_plan = generate_dashboard_plan(self.retail_result)
        db = retail_plan["dashboard"]
        
        # Confirm components exist
        self.assertIn("kpi_cards", db)
        self.assertIn("charts", db)
        self.assertIn("filters", db)
        self.assertIn("tables", db)
        
        # Confirm Dynamic Filters
        filter_types = {f["column_name"]: f["control_type"] for f in db["filters"]}
        self.assertEqual(filter_types["txn_date"], "date_picker")
        self.assertEqual(filter_types["sales_category"], "dropdown")
        self.assertEqual(filter_types["store_region"], "dropdown")
        
        # Run HR dashboard plan
        hr_plan = generate_dashboard_plan(self.hr_result)
        hr_db = hr_plan["dashboard"]
        
        # Confirm dynamic filters for status and category
        hr_filter_types = {f["column_name"]: f["control_type"] for f in hr_db["filters"]}
        self.assertEqual(hr_filter_types["employment_status"], "multi_select") # status_like
        self.assertEqual(hr_filter_types["dept_name"], "dropdown")             # category_like
        
        # Confirm sections are different
        retail_sections = db["metadata"]["active_sections"]
        hr_sections = hr_db["metadata"]["active_sections"]
        
        self.assertIn("Trend Analysis", retail_sections)
        self.assertNotIn("Trend Analysis", hr_sections, "HR context with no dates should hide Trend Analysis section")

if __name__ == "__main__":
    unittest.main()
