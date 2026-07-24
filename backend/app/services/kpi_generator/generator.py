import logging
from typing import Dict, Any, List
from app.services.kpi_generator.context import PipelineContext
from app.services.kpi_generator.registry import kpi_registry
# Import plugins module to trigger registry decorators
import app.services.kpi_generator.plugins

logger = logging.getLogger("dataset_profiler")

def generate_candidate_kpis(context: PipelineContext) -> Dict[str, Any]:
    """
    Main rule-based orchestrator. Executes all registered candidate KPI plugins.
    Strictly deterministic and schema-agnostic. Operates on the PipelineContext object.
    """
    logger.info("Executing rule-based KPI Candidate Generator...")
    
    generators = kpi_registry.get_generators()
    logger.info(f"Loaded {len(generators)} KPI generator plugins.")
    
    all_candidates: List[Dict[str, Any]] = []
    
    for name, gen_func in generators:
        try:
            logger.info(f"Running KPI generator plugin: '{name}'...")
            candidates = gen_func(context)
            if candidates:
                logger.info(f"  - Generator '{name}' produced {len(candidates)} candidates.")
                all_candidates.extend(candidates)
            else:
                logger.info(f"  - Generator '{name}' produced 0 candidates.")
        except Exception as e:
            logger.error(f"Error executing KPI generator plugin '{name}': {e}")
            continue
            
    # Filter duplicate candidates if any (by id)
    unique_candidates = []
    seen_ids = set()
    for cand in all_candidates:
        if cand["id"] not in seen_ids:
            seen_ids.add(cand["id"])
            unique_candidates.append(cand)
            
    logger.info(f"KPI Candidate Generation complete. Total unique candidates: {len(unique_candidates)}.")
    
    return {
        "schema_version": "1.0.0",
        "candidate_kpis": unique_candidates
    }
