import logging
from typing import Dict, Any, Tuple
import pandas as pd
from app.services.data_ingestion import sessions
from app.services.dataset_profiler.parser import CSVParser
from app.services.dataset_profiler.profiler import profile_dataset
from app.services.semantic_mapper import map_semantics
from app.services.domain_classifier import classify_domain
from app.services.feature_engineering_engine import engineer_features
from app.services.kpi_generator.context import PipelineContext

logger = logging.getLogger("dataset_profiler")

class PipelineRuntime:
    """
    Lightweight runtime object to hold active execution states (Pandas DataFrame
    and session_id) isolated from metadata contexts.
    """
    def __init__(self, df: pd.DataFrame, session_id: str):
        self.df = df
        self.session_id = session_id


class PipelineOrchestrator:
    """
    Central coordinator responsible for executing analytical stages sequentially.
    Ensures individual modules remain decoupled and never invoke each other directly.
    """
    
    @staticmethod
    def profile_and_map(contents: bytes) -> Tuple[Dict[str, Any], Dict[str, Any], pd.DataFrame]:
        """
        Stage 1: Parses dataset contents, profiles statistics, and maps semantics.
        """
        logger.info("Orchestration: Starting Stage 1 (Profiling & Mapping)...")
        parser = CSVParser(contents)
        df = parser.parse()
        
        # Profile using a preparsed container to avoid double reading
        from app.services.dataset_profiler.parser import BaseParser
        class PreparsedParser(BaseParser):
            def __init__(self, parsed_df):
                self.parsed_df = parsed_df
            def parse(self):
                return self.parsed_df
                
        profile = profile_dataset(PreparsedParser(df))
        mapping = map_semantics(profile)
        
        return profile, mapping, df

    @staticmethod
    def post_process_features(df: pd.DataFrame, semantic_mapping: dict, dataset_profile: dict) -> Tuple[dict, list, pd.DataFrame]:
        """
        Stage 2: Classifies the business domain and performs rule-based feature engineering.
        """
        logger.info("Orchestration: Starting Stage 2 (Domain Classification & Feature Engineering)...")
        
        # In parallel/sequence, run the modules independently
        domain_profile = classify_domain(semantic_mapping, dataset_profile)
        engineered_df, metadata = engineer_features(df, semantic_mapping)
        
        return domain_profile, metadata, engineered_df

    @staticmethod
    def build_context(dataset_profile: dict, semantic_mapping: dict, domain_profile: dict, engineered_features: list, session_id: str = None) -> PipelineContext:
        """
        Helper: Compiles context parameters into the structured PipelineContext payload.
        """
        return PipelineContext(
            dataset_profile=dataset_profile,
            confirmed_semantic_mapping=semantic_mapping,
            domain_profile=domain_profile,
            engineered_features=engineered_features,
            session_id=session_id
        )

    @staticmethod
    def generate_dashboard_plan_with_data(pipeline_result: dict) -> dict:
        """
        Sequence: Feature Engineering & KPIs (done) -> Visualization Recommendation -> Chart Data Generation -> Dashboard Planning
        """
        # 1. Resolve session ID and DataFrame
        session_id = pipeline_result.get("session_id")
        from app.services.data_ingestion import get_session_data, sessions
        df = None
        if session_id:
            df = get_session_data(session_id)
        if df is None and sessions:
            # Fallback to the latest session in store (mostly for testing fallback)
            latest_session_id = list(sessions.keys())[-1]
            df = sessions[latest_session_id]
            
        # Create PipelineRuntime and PipelineContext
        runtime = PipelineRuntime(df=df, session_id=session_id)
        context = PipelineContext(
            dataset_profile=pipeline_result.get("dataset_profile", {}),
            confirmed_semantic_mapping=pipeline_result.get("confirmed_semantic_mapping", {}),
            domain_profile=pipeline_result.get("domain_profile", {}),
            engineered_features=pipeline_result.get("engineered_features", []),
            session_id=session_id
        )
        
        # 2. Run Visualization Recommendation
        from app.services.visualization_recommendation import recommend_visualizations
        recommendations = recommend_visualizations(pipeline_result)
        
        # 3. Chart Data Generation (passing both runtime and context)
        from app.services.chart_data_engine import enrich_recommendations_with_data
        enriched_recs = enrich_recommendations_with_data(
            runtime=runtime,
            context=context,
            recommendations=recommendations
        )
        
        # 4. Dashboard Planning
        from app.services.dashboard_planning.planner import generate_dashboard_plan
        plan = generate_dashboard_plan(pipeline_result, enriched_recs)
        
        return plan

