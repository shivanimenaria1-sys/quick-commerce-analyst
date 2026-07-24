const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';

async function handleResponse(response) {
  if (!response.ok) {
    let errorDetail = 'An error occurred during request execution.';
    let missingColumns = null;
    try {
      const data = await response.json();
      errorDetail = data.detail || data.error || errorDetail;
      missingColumns = data.missing_columns || null;
    } catch (e) {
      // Response was not JSON
    }
    
    const error = new Error(errorDetail);
    if (missingColumns) {
      error.missingColumns = missingColumns;
    }
    throw error;
  }
  return response.json();
}

export const apiService = {
  /**
   * Uploads a CSV dataset.
   * @param {File} file 
   * @returns {Promise<{session_id: string, rows: number, columns: string[]}>}
   */
  uploadCSV: async (file) => {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await fetch(`${API_BASE_URL}/api/upload`, {
      method: 'POST',
      body: formData,
    });
    return handleResponse(response);
  },
  
  /**
   * Cleans a dataset for a given session.
   * @param {string} sessionId 
   */
  cleanDataset: async (sessionId) => {
    const response = await fetch(`${API_BASE_URL}/api/clean/${sessionId}`, {
      method: 'POST',
    });
    return handleResponse(response);
  },
  
  /**
   * Computes engineered features for a session.
   * @param {string} sessionId 
   */
  engineerFeatures: async (sessionId) => {
    const response = await fetch(`${API_BASE_URL}/api/engineer/${sessionId}`, {
      method: 'POST',
    });
    return handleResponse(response);
  },
  
  /**
   * Calculates business KPIs for a session.
   * @param {string} sessionId 
   */
  getKPIs: async (sessionId) => {
    const response = await fetch(`${API_BASE_URL}/api/kpis/${sessionId}`, {
      method: 'GET',
    });
    return handleResponse(response);
  },
  
  /**
   * Fetches AI-generated insights for a session.
   * @param {string} sessionId 
   */
  getInsights: async (sessionId) => {
    const response = await fetch(`${API_BASE_URL}/api/insights/${sessionId}`, {
      method: 'GET',
    });
    return handleResponse(response);
  },
  
  /**
   * Downloads the generated diagnostic report.
   * @param {string} sessionId 
   * @returns {Promise<{blob: Blob, contentDisposition: string}>}
   */
  getReportBlob: async (sessionId) => {
    const response = await fetch(`${API_BASE_URL}/api/report/${sessionId}`, {
      method: 'GET',
    });
    if (!response.ok) {
      let errorMsg = 'Failed to compile and download report.';
      try {
        const data = await response.json();
        errorMsg = data.detail || errorMsg;
      } catch (e) {}
      throw new Error(errorMsg);
    }
    const blob = await response.blob();
    const contentDisposition = response.headers.get("Content-Disposition");
    return { blob, contentDisposition };
  },
  
  /**
   * Uploads any CSV and profiles it, returning dataset profile and semantic mapping.
   * @param {File} file
   */
  profileAndMapSemantics: async (file) => {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await fetch(`${API_BASE_URL}/api/semantic/profile`, {
      method: 'POST',
      body: formData,
    });
    return handleResponse(response);
  },
  
  /**
   * Submits a user correction override to the backend corrections log.
   */
  submitSemanticCorrection: async (schemaFingerprint, columnName, originalRole, correctedRole) => {
    const response = await fetch(`${API_BASE_URL}/api/semantic/correct`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        schema_fingerprint: schemaFingerprint,
        column_name: columnName,
        original_role: originalRole,
        corrected_role: correctedRole
      }),
    });
    return handleResponse(response);
  },
  
  /**
   * Run LLM-powered business domain classification.
   */
  classifyDomain: async (semanticMapping, datasetProfile) => {
    const response = await fetch(`${API_BASE_URL}/api/process/classify`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        semantic_mapping: semanticMapping,
        dataset_profile: datasetProfile
      }),
    });
    return handleResponse(response);
  },
  
  /**
   * Run rule-based feature engineering engine.
   */
  engineerFeatures: async (sessionId, semanticMapping) => {
    const response = await fetch(`${API_BASE_URL}/api/process/engineer`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        session_id: sessionId,
        semantic_mapping: semanticMapping
      }),
    });
    return handleResponse(response);
  },
  
  /**
   * Generates candidate KPIs.
   */
  generateKPICandidates: async (sessionId, semanticMapping, domainProfile, datasetProfile) => {
    const response = await fetch(`${API_BASE_URL}/api/kpi/generate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        session_id: sessionId,
        semantic_mapping: semanticMapping,
        domain_profile: domainProfile,
        dataset_profile: datasetProfile
      }),
    });
    return handleResponse(response);
  },
  
  /**
   * Ranks candidate KPIs using the LLM ranker.
   */
  rankKPICandidates: async (pipelineContext, candidateKPIs) => {
    const response = await fetch(`${API_BASE_URL}/api/kpi/rank`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        pipeline_context: pipelineContext,
        candidate_kpis: candidateKPIs
      }),
    });
    return handleResponse(response);
  },

  /**
   * Fetches deterministic chart visualization recommendations.
   */
  recommendVisualizations: async (pipelineResult) => {
    const response = await fetch(`${API_BASE_URL}/api/visualizations/recommend`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        pipeline_result: pipelineResult
      }),
    });
    return handleResponse(response);
  },

  /**
   * Generates dynamic dashboard layout plan.
   */
  getDashboardPlan: async (pipelineResult) => {
    const response = await fetch(`${API_BASE_URL}/api/visualizations/plan`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        pipeline_result: pipelineResult
      }),
    });
    return handleResponse(response);
  },

  getAnalysis: async (sessionId) => {
    const response = await fetch(`${API_BASE_URL}/api/analysis/${sessionId}`, {
      method: 'GET',
    });
    return handleResponse(response);
  },

  getReportInsights: async (pipelineResult) => {
    const response = await fetch(`${API_BASE_URL}/api/report/insights`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        pipeline_result: pipelineResult
      }),
    });
    return handleResponse(response);
  },

  exportReport: async (pipelineResult, insights, format) => {
    const response = await fetch(`${API_BASE_URL}/api/report/export`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        pipeline_result: pipelineResult,
        insights: insights,
        format: format
      }),
    });
    if (!response.ok) {
      throw new Error("Failed to export report.");
    }
    return response.blob();
  },

  exportCompleteReport: async (sessionId, chartImages) => {
    const response = await fetch(`${API_BASE_URL}/api/report/export_complete`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        session_id: sessionId,
        chart_images: chartImages
      }),
    });
    if (!response.ok) {
      throw new Error("Failed to export complete report.");
    }
    return response.blob();
  }
};
export default apiService;
