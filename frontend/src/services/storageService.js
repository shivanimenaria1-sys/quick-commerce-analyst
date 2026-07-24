/**
 * Abstraction layer for user personalization settings and selection logs.
 * Currently uses LocalStorage, but can be seamlessly replaced with an API database adapter
 * without altering any frontend UI components.
 */
export const kpiPersonalizationStorage = {
  /**
   * Saves the list of selected KPI candidate IDs for a given dataset fingerprint.
   * @param {string} fingerprint 
   * @param {string[]} selections 
   * @returns {Promise<boolean>}
   */
  saveSelection: async (fingerprint, selections) => {
    try {
      localStorage.setItem(`kpi_selections_${fingerprint}`, JSON.stringify(selections));
      return true;
    } catch (e) {
      console.error("Personalization storage error:", e);
      return false;
    }
  },

  /**
   * Retrieves the previously selected KPI candidate IDs for a dataset fingerprint.
   * @param {string} fingerprint 
   * @returns {Promise<string[]|null>}
   */
  getSelection: async (fingerprint) => {
    try {
      const item = localStorage.getItem(`kpi_selections_${fingerprint}`);
      return item ? JSON.parse(item) : null;
    } catch (e) {
      console.error("Personalization load error:", e);
      return null;
    }
  }
};

export const analysisSessionStorage = {
  saveSessionData: (sessionId, data) => {
    try {
      localStorage.setItem(`analysis_session_${sessionId}`, JSON.stringify(data));
      return true;
    } catch (e) {
      console.error("Failed to save analysis session:", e);
      return false;
    }
  },
  
  getSessionData: (sessionId) => {
    try {
      const item = localStorage.getItem(`analysis_session_${sessionId}`);
      return item ? JSON.parse(item) : null;
    } catch (e) {
      console.error("Failed to load analysis session:", e);
      return null;
    }
  }
};

export default kpiPersonalizationStorage;
