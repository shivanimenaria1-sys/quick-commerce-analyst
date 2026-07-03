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
  }
};
export default apiService;
