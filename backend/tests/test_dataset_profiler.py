import unittest
import os
import io
import json
import pandas as pd
from app.services.dataset_profiler import CSVParser, profile_dataset

class TestDatasetProfiler(unittest.TestCase):
    def setUp(self):
        # 1. Retail CSV data
        self.retail_csv = """Transaction_ID,Sale_Date,Amount_USD,Quantity_Sold,Category_Name,Discount_Pct,Total_Sales
TX001,02-06-2026,$100.00,2,Groceries,10%,200.0
TX002,20-07-2026,$50.50,4,Electronics,5%,202.0
TX003,14-07-2026,$10.00,5,Groceries,0%,50.0
TX004,25-06-2026,$25.00,3,Snacks,15%,75.0
TX005,15-06-2026,$200.00,1,Electronics,20%,200.0
"""

        # 2. HR CSV data (consecutive integers as codes, currency formats, subtraction derivation, boolean columns)
        self.hr_csv = """Employee_Code,Hire_Date,Base_Salary,Bonus,Total_Compensation,Department,Is_Active
10001,2020-01-15,"$5,000.00",500.0,5500.0,Sales,True
10002,2021-03-22,"$6,500.00",1000.0,7500.0,Tech,True
10003,2019-11-05,"$4,200.00",200.0,4400.0,HR,False
10004,2023-08-30,"$8,000.00",1500.0,9500.0,Tech,True
10005,2022-05-12,"$5,500.00",600.0,6100.0,Sales,True
"""

        # 3. Healthcare CSV data (mixed codes, slash date format, high nulls column, constant column)
        self.healthcare_csv = """Patient_No,Admission_Date,Treatment_Cost,Insurance_Cover,Out_Of_Pocket,Diagnosis,Age,Hospital_Country,Secondary_Diagnosis
PT-1092,2025/12/01,12000.0,10000.0,2000.0,Flu,45,India,
PT-8293,2025/12/02,8500.0,7000.0,1500.0,Cold,32,India,Bronchitis
PT-7482,2025/12/03,15000.0,12000.0,3000.0,Covid,58,India,
PT-3849,2025/12/04,6000.0,6000.0,0.0,Flu,19,India,
PT-9201,2025/12/05,9500.0,8000.0,1500.0,Covid,27,India,Pneumonia
"""

    def test_retail_dataset_profile(self):
        """
        Validates profiling on a Retail dataset (contains multiplication derived column: Total_Sales = Amount_USD * Quantity_Sold).
        """
        parser = CSVParser(self.retail_csv)
        profile = profile_dataset(parser)
        
        # Output verification
        self.assertEqual(profile["schema_version"], "1.0.0")
        self.assertEqual(profile["dataset_metadata"]["row_count"], 5)
        self.assertEqual(profile["dataset_metadata"]["column_count"], 7)
        
        # Verify columns & inferred dtypes
        cols = profile["columns"]
        self.assertEqual(cols["Transaction_ID"]["inferred_dtype"], "id_like")
        self.assertEqual(cols["Sale_Date"]["inferred_dtype"], "datetime")
        self.assertEqual(cols["Amount_USD"]["inferred_dtype"], "float")
        self.assertEqual(cols["Quantity_Sold"]["inferred_dtype"], "integer")
        self.assertEqual(cols["Category_Name"]["inferred_dtype"], "categorical")
        self.assertEqual(cols["Total_Sales"]["inferred_dtype"], "float")
        
        # Verify derived column detection (multiplication)
        derived = profile["relationships"]["derived_columns"]
        self.assertTrue(len(derived) >= 1)
        multiplication_derived = [d for d in derived if d["relationship_type"] == "multiplication"]
        self.assertTrue(len(multiplication_derived) >= 1)
        self.assertEqual(multiplication_derived[0]["target_column"], "Total_Sales")
        
        # Verify primary key detection
        pks = profile["relationships"]["primary_keys"]
        self.assertIn("Transaction_ID", pks)

    def test_hr_dataset_profile(self):
        """
        Validates profiling on an HR dataset (consecutive integers as codes, addition derivation, boolean columns).
        """
        parser = CSVParser(self.hr_csv)
        profile = profile_dataset(parser)
        
        # Output verification
        self.assertEqual(profile["schema_version"], "1.0.0")
        self.assertEqual(profile["dataset_metadata"]["row_count"], 5)
        
        cols = profile["columns"]
        self.assertEqual(cols["Employee_Code"]["inferred_dtype"], "id_like")
        self.assertEqual(cols["Base_Salary"]["inferred_dtype"], "integer") # cleaned from "$5,000.00"
        self.assertEqual(cols["Bonus"]["inferred_dtype"], "float")
        self.assertEqual(cols["Total_Compensation"]["inferred_dtype"], "float")
        self.assertEqual(cols["Is_Active"]["inferred_dtype"], "boolean")
        
        # Verify derived column detection (addition)
        derived = profile["relationships"]["derived_columns"]
        addition_derived = [d for d in derived if d["relationship_type"] == "addition"]
        self.assertTrue(len(addition_derived) >= 1)
        self.assertEqual(addition_derived[0]["target_column"], "Total_Compensation")
        
        pks = profile["relationships"]["primary_keys"]
        self.assertIn("Employee_Code", pks)

    def test_healthcare_dataset_profile(self):
        """
        Validates profiling on a Healthcare dataset (slash dates, high nulls column, constant column, subtraction derived).
        """
        parser = CSVParser(self.healthcare_csv)
        profile = profile_dataset(parser)
        
        # Output verification
        self.assertEqual(profile["schema_version"], "1.0.0")
        self.assertEqual(profile["dataset_metadata"]["row_count"], 5)
        
        cols = profile["columns"]
        self.assertEqual(cols["Patient_No"]["inferred_dtype"], "id_like")
        self.assertEqual(cols["Admission_Date"]["inferred_dtype"], "datetime")
        self.assertEqual(cols["Treatment_Cost"]["inferred_dtype"], "float")
        self.assertEqual(cols["Insurance_Cover"]["inferred_dtype"], "float")
        self.assertEqual(cols["Out_Of_Pocket"]["inferred_dtype"], "float")
        
        # Verify derived column detection (subtraction)
        derived = profile["relationships"]["derived_columns"]
        subtraction_derived = [d for d in derived if d["relationship_type"] == "subtraction"]
        self.assertTrue(len(subtraction_derived) >= 1)
        self.assertEqual(subtraction_derived[0]["target_column"], "Out_Of_Pocket")
        
        # Verify primary key candidate
        pks = profile["relationships"]["primary_keys"]
        self.assertIn("Patient_No", pks)
        
        # Verify quality issues
        issues = profile["quality_issues"]
        self.assertIn("Hospital_Country", issues["constant_columns"])
        self.assertIn("Secondary_Diagnosis", issues["high_null_columns"])

if __name__ == "__main__":
    unittest.main()
