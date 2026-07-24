import time
import logging
import datetime
import numpy as np
import pandas as pd
from typing import Dict, Any, List
from app.services.dataset_profiler.parser import BaseParser
from app.services.dataset_profiler.dtype_detector import detect_column_type
from app.services.dataset_profiler.statistics import compute_column_stats, safe_float
from app.services.dataset_profiler.relationships import compute_correlations, detect_derived_columns, detect_primary_keys
from app.services.dataset_profiler.quality import detect_dataset_quality_issues

# Configure structured logging
logger = logging.getLogger("dataset_profiler")
if not logger.handlers:
    logger.setLevel(logging.INFO)
    sh = logging.StreamHandler()
    sh.setFormatter(logging.Formatter('[%(asctime)s] [%(levelname)s] [PROFILER] %(message)s'))
    logger.addHandler(sh)

def profile_dataset(parser: BaseParser) -> Dict[str, Any]:
    """
    Main orchestration pipeline.
    Parses, cleans, type-detects, calculates stats/relationships, analyzes quality issues,
    and returns a structured versioned JSON dataset profile.
    """
    logger.info("Initializing profiling pipeline.")
    start_time = time.perf_counter()
    
    # 1. Parse Data Source
    logger.info("Parsing data source...")
    df = parser.parse()
    row_count = len(df)
    col_count = len(df.columns)
    logger.info(f"Successfully loaded dataset with dimensions: {row_count} rows x {col_count} columns.")
    
    # 2. Dataset Metadata
    logger.info("Calculating dataset-level metadata...")
    duplicate_rows = int(df.duplicated().sum())
    duplicate_pct = (duplicate_rows / row_count) * 100.0 if row_count > 0 else 0.0
    memory_usage_bytes = df.memory_usage(deep=True).sum()
    memory_usage_mb = memory_usage_bytes / (1024 * 1024)
    
    # Apply scalability profiling policy (sampling if dataset is large)
    from app.services.dataset_profiler.scalability import DatasetScalabilityLayer
    profile_df = DatasetScalabilityLayer.apply_profiling_policy(df)
    
    # 3. Data Type Detection
    logger.info("Detecting column datatypes and confidence scores...")
    inferred_types = {}
    type_confidences = {}
    for col in profile_df.columns:
        dtype, conf = detect_column_type(profile_df[col])
        inferred_types[col] = dtype
        type_confidences[col] = conf
        logger.info(f"  - Column '{col}' inferred as '{dtype}' (confidence: {conf})")
        
    # 4. Descriptive Statistics
    logger.info("Computing column descriptive statistics...")
    columns_profile = {}
    for col in profile_df.columns:
        col_type = inferred_types[col]
        col_stats = compute_column_stats(profile_df[col], col_type)
        columns_profile[col] = {
            "inferred_dtype": col_type,
            "confidence_score": safe_float(type_confidences[col]),
            "statistics": col_stats
        }
        
    # 5. Core Column Relationships
    logger.info("Analyzing column relationships...")
    numeric_cols = [col for col, dtype in inferred_types.items() if dtype in ("integer", "float", "numeric")]
    
    # Relationships & Primary Keys
    correlations = compute_correlations(profile_df, numeric_cols, method="pearson")
    derived_cols = detect_derived_columns(profile_df, numeric_cols, tolerance=1e-4)
    primary_keys = detect_primary_keys(profile_df, inferred_types)
    logger.info(f"Relationships analyzed: Found {len(derived_cols)} derived columns and {len(primary_keys)} primary key candidates.")
    
    # 6. Quality Checks
    logger.info("Performing dataset quality and anomaly checks...")
    quality_issues = detect_dataset_quality_issues(profile_df, inferred_types)
    
    # Total profiling execution duration
    elapsed_ms = (time.perf_counter() - start_time) * 1000.0
    logger.info(f"Dataset profiling completed in {elapsed_ms:.2f} ms.")
    
    # Build stable versioned JSON profile object
    profile = {
        "schema_version": "1.0.0",
        "generated_at": datetime.datetime.utcnow().isoformat() + "Z",
        "dataset_metadata": {
            "row_count": int(row_count),
            "column_count": int(col_count),
            "duplicate_row_count": int(duplicate_rows),
            "duplicate_row_percentage": safe_float(duplicate_pct),
            "memory_usage_mb": safe_float(memory_usage_mb),
            "profiling_time_ms": safe_float(elapsed_ms)
        },
        "columns": columns_profile,
        "relationships": {
            "primary_keys": primary_keys,
            "correlations": correlations,
            "derived_columns": derived_cols
        },
        "quality_issues": quality_issues
    }
    
    return profile
