import logging
import pandas as pd
from typing import Tuple, List, Dict, Any
from app.services.feature_engineering_engine.registry import registry
# Import plugins to register them
import app.services.feature_engineering_engine.plugins

logger = logging.getLogger("dataset_profiler")

def engineer_features(df: pd.DataFrame, semantic_mapping: Dict[str, Any]) -> Tuple[pd.DataFrame, List[Dict[str, Any]]]:
    """
    Orchestration core for the rule-based Feature Engineering Engine.
    Runs all registered feature generator plugins on the dataframe based on semantic roles.
    Never uses hardcoded column names.
    """
    logger.info("Initializing rule-based Feature Engineering Engine...")
    
    enriched_df = df.copy()
    all_metadata: List[Dict[str, Any]] = []
    
    # Get all registered plugins
    generators = registry.get_generators()
    logger.info(f"Loaded {len(generators)} feature engineering plugins.")
    
    for name, gen_func in generators:
        try:
            logger.info(f"Running feature generator: '{name}'...")
            new_cols, metadata = gen_func(enriched_df, semantic_mapping)
            
            if not new_cols.empty:
                logger.info(f"  - Generator '{name}' appended {len(new_cols.columns)} columns.")
                # Merge into df (avoiding duplicate column name clashes)
                for col in new_cols.columns:
                    if col in enriched_df.columns:
                        logger.warning(f"Feature column '{col}' already exists. Overwriting.")
                    enriched_df[col] = new_cols[col]
                    
                all_metadata.extend(metadata)
            else:
                logger.info(f"  - Generator '{name}' returned 0 columns.")
        except Exception as e:
            logger.error(f"Error running feature generator plugin '{name}': {e}")
            continue
            
    logger.info(f"Feature engineering pipeline completed. Total derived features added: {len(all_metadata)}.")
    return enriched_df, all_metadata
