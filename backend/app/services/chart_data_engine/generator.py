import logging
from typing import Dict, Any, List
from app.services.chart_data_engine.registry import chart_registry

# Import generators package to trigger dynamic plugin registrations
import app.services.chart_data_engine.generators

logger = logging.getLogger("dataset_profiler")

def enrich_recommendations_with_data(
    runtime: Any,
    context: Any,
    recommendations: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Enriches every visualization recommendation dictionary in-place by computing
    its required real chart_data from the provided PipelineRuntime active DataFrame.
    """
    logger.info("Enriching visualization recommendations with real chart data...")
    enriched_recs = []
    
    df = runtime.df if runtime else None
    
    for rec in recommendations:
        chart_type = rec.get("chart_type")
        dimensions = rec.get("dimensions", [])
        required_kpis = rec.get("required_kpis", [])
        
        # Make a copy to avoid mutating inputs directly
        rec_copy = dict(rec)
        rec_copy["chart_data"] = None
        
        if df is not None and not df.empty:
            generator_inst = chart_registry.get_generator(chart_type)
            if generator_inst:
                try:
                    chart_data = generator_inst.generate(
                        runtime=runtime,
                        context=context,
                        dimensions=dimensions,
                        required_kpis=required_kpis
                    )
                    rec_copy["chart_data"] = chart_data
                    logger.info(f"Successfully generated chart data for recommendation: {rec_copy.get('chart_id')}")
                except Exception as e:
                    logger.error(f"Failed to generate chart data for recommendation {rec_copy.get('chart_id')}: {e}")
            else:
                logger.warning(f"No chart data generator found in registry for type: {chart_type}")
        else:
            logger.warning(f"Active DataFrame is empty or None; skipping data generation for {rec_copy.get('chart_id')}")
            
        enriched_recs.append(rec_copy)
        
    return enriched_recs
