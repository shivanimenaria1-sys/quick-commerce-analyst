import datetime
from typing import Dict, Any

class AnalysisSessionStore:
    def __init__(self):
        # In-memory store: session_id -> analysis dictionary containing metadata and data
        self._store: Dict[str, dict] = {}
        
    def save(self, session_id: str, analysis: dict):
        """
        Saves a completed analysis result, wrapping it with lightweight metadata.
        """
        dataset_profile = analysis.get("dataset_profile", {})
        metadata_profile = dataset_profile.get("dataset_metadata", {})
        
        row_count = metadata_profile.get("row_count", 0)
        column_count = metadata_profile.get("column_count", 0)
        detected_domain = analysis.get("domain_profile", {}).get("domain", "Unknown")
        dataset_name = analysis.get("dataset_name", "Unknown Dataset")
        
        # Build structure with metadata and flat data access matching standard contract
        self._store[session_id] = {
            "metadata": {
                "session_id": session_id,
                "created_at": datetime.datetime.now(datetime.UTC).isoformat() + "Z",
                "dataset_name": dataset_name,
                "row_count": row_count,
                "column_count": column_count,
                "detected_domain": detected_domain,
                "analysis_version": "1.0"
            },
            "dataset_profile": dataset_profile,
            "confirmed_semantic_mapping": analysis.get("confirmed_semantic_mapping"),
            "domain_profile": analysis.get("domain_profile"),
            "selected_kpis": analysis.get("selected_kpis"),
            "dashboard_plan": analysis.get("dashboard_plan"),
            "visualization_recommendations": analysis.get("visualization_recommendations"),
            "insights": analysis.get("insights", {})
        }
        
    def get(self, session_id: str) -> dict:
        """
        Retrieves the completed analysis object for a given session ID.
        """
        return self._store.get(session_id)
        
    def exists(self, session_id: str) -> bool:
        """
        Checks if a completed analysis exists for a session ID.
        """
        return session_id in self._store
        
    def delete(self, session_id: str):
        """
        Deletes a completed analysis from the store.
        """
        if session_id in self._store:
            del self._store[session_id]
            
    def clear(self):
        """
        Clears all stored analyses.
        """
        self._store.clear()

# Global Singleton Instance
analysis_store = AnalysisSessionStore()
