import logging
import pandas as pd

logger = logging.getLogger("dataset_profiler")

class DatasetScalabilityLayer:
    """
    Implements configurable processing policies and sampling algorithms for large datasets.
    Ensures sub-second profiling times and low memory footprint for large datasets (>100k rows)
    while preserving deterministic down-stream KPI exact calculations.
    """
    
    @staticmethod
    def get_processing_policy(row_count: int) -> str:
        if row_count <= 10000:
            return "Small (Exact Calculations)"
        elif row_count <= 100000:
            return "Medium (Streaming/Exact Calculations)"
        else:
            return "Large (Bounded Profiling & Approximate Statistics)"

    @classmethod
    def apply_profiling_policy(cls, df: pd.DataFrame) -> pd.DataFrame:
        """
        Samples the dataset for dtype detection and statistics computation if it's large.
        Ensures exact calculations are default, but applies a 10,000 row random sample
        for profiling columns of datasets exceeding 100,000 rows.
        """
        row_count = len(df)
        policy = cls.get_processing_policy(row_count)
        logger.info(f"Scalability Layer: Enforcing dataset processing policy: '{policy}' (Total Rows: {row_count})")
        
        if row_count > 100000:
            # Bounded sample for schema/dtype profiling
            logger.info("Dataset exceeds 100,000 rows. Creating a 10,000 row bounded sample for profiling.")
            # Use random state for deterministic reproducibility
            return df.sample(n=10000, random_state=42)
        return df
