/**
 * Abstraction layer for user personalization settings and selection logs.
 * Currently uses LocalStorage, but can be seamlessly replaced with an API
 * database adapter without altering any frontend UI components.
 */

// ---------------------------------------------------------------------------
// Internal: Recursive deep-merge utility
//
// Rules:
//   • Both sides are plain objects  → recurse (keys in `target` not in
//     `source` are preserved; keys in `source` win for everything else)
//   • Arrays, primitives, null      → source value wins outright
//   • Source key is `undefined`     → target value is preserved (no clobber)
//
// Pure function – neither `target` nor `source` is mutated.
// ---------------------------------------------------------------------------
function deepMerge(target, source) {
  // If either side is not a plain, non-null object, source wins
  // (unless source is undefined, in which case we keep target).
  if (source === undefined) return target;
  if (
    target === null || typeof target !== 'object' || Array.isArray(target) ||
    source === null || typeof source !== 'object' || Array.isArray(source)
  ) {
    return source;
  }

  // Both are plain objects → shallow-copy target then recurse for each key
  const result = { ...target };
  for (const key of Object.keys(source)) {
    const srcVal = source[key];
    const tgtVal = target[key];

    if (
      srcVal !== null && typeof srcVal === 'object' && !Array.isArray(srcVal) &&
      tgtVal !== null && typeof tgtVal === 'object' && !Array.isArray(tgtVal)
    ) {
      result[key] = deepMerge(tgtVal, srcVal);
    } else {
      result[key] = srcVal;
    }
  }
  return result;
}

// ---------------------------------------------------------------------------
// KPI personalisation storage (unchanged public API)
// ---------------------------------------------------------------------------
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
      console.error('Personalization storage error:', e);
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
      console.error('Personalization load error:', e);
      return null;
    }
  },
};

// ---------------------------------------------------------------------------
// Analysis session storage
// ---------------------------------------------------------------------------
export const analysisSessionStorage = {
  /**
   * Fully replaces the stored session for a given sessionId.
   * Prefer `mergeSessionData()` in most cases to avoid accidentally
   * dropping fields that were saved earlier (e.g. `insights`).
   *
   * @param {string} sessionId
   * @param {object} data
   * @returns {boolean} success
   */
  saveSessionData: (sessionId, data) => {
    try {
      localStorage.setItem(`analysis_session_${sessionId}`, JSON.stringify(data));
      return true;
    } catch (e) {
      console.error('Failed to save analysis session:', e);
      return false;
    }
  },

  /**
   * Returns the stored session object for a given sessionId, or null.
   *
   * @param {string} sessionId
   * @returns {object|null}
   */
  getSessionData: (sessionId) => {
    try {
      const item = localStorage.getItem(`analysis_session_${sessionId}`);
      return item ? JSON.parse(item) : null;
    } catch (e) {
      console.error('Failed to load analysis session:', e);
      return null;
    }
  },

  /**
   * Deep-merges `patch` into the existing cached session so that fields
   * absent from `patch` (e.g. `insights` stored by Upload.jsx) are always
   * preserved.  Keys that exist in `patch` override the cached values;
   * for nested plain objects the merge recurses instead of replacing.
   *
   * @param {string} sessionId
   * @param {object} patch  – partial session object to merge in
   * @returns {boolean} success
   */
  mergeSessionData: (sessionId, patch) => {
    try {
      const existing = analysisSessionStorage.getSessionData(sessionId) || {};
      const merged = deepMerge(existing, patch);
      return analysisSessionStorage.saveSessionData(sessionId, merged);
    } catch (e) {
      console.error('Failed to merge analysis session:', e);
      return false;
    }
  },

  /**
   * Canonical helper used by every page that calls apiService.getAnalysis().
   *
   * Maps the raw GET /api/analysis/{sessionId} response to the standard
   * frontend session shape, then deep-merges the result into the existing
   * cache.  This guarantees that fields already saved by Upload.jsx
   * (especially `insights`) are NEVER overwritten with empty/absent values
   * from the API response.
   *
   * Policy for each field:
   *   • profileData / mappingData / domainData / finalKPIs / dashboardPlan
   *       → always taken from the fresh API response (authoritative)
   *   • insights
   *       → taken from the API response only when the response contains a
   *         non-empty insights object; otherwise the cached value is kept
   *   • pipelineContext (saved only by Upload.jsx)
   *       → never touched here, always preserved by deepMerge
   *
   * @param {string} sessionId
   * @param {object} freshApiResponse – the object returned by apiService.getAnalysis()
   * @returns {object|null} the merged session (also written to localStorage)
   */
  updateFromAnalysis: (sessionId, freshApiResponse) => {
    // Build the incoming patch – only include defined, non-null values so
    // that deepMerge doesn't clobber existing cache entries with empty data.
    const apiInsights = freshApiResponse.insights;
    const hasInsights =
      apiInsights != null && typeof apiInsights === 'object' &&
      Object.keys(apiInsights).length > 0;

    const patch = {};
    if (freshApiResponse.dataset_profile != null)
      patch.profileData = freshApiResponse.dataset_profile;
    if (freshApiResponse.confirmed_semantic_mapping != null)
      patch.mappingData = freshApiResponse.confirmed_semantic_mapping;
    if (freshApiResponse.domain_profile != null)
      patch.domainData = freshApiResponse.domain_profile;
    if (freshApiResponse.selected_kpis != null)
      patch.finalKPIs = freshApiResponse.selected_kpis;
    if (freshApiResponse.dashboard_plan != null)
      patch.dashboardPlan = { dashboard: freshApiResponse.dashboard_plan };
    if (hasInsights)
      patch.insights = apiInsights;

    // ── DEBUG LOG (remove after verification) ──────────────────────────────
    const existing = analysisSessionStorage.getSessionData(sessionId) || {};
    const existingInsightKeys = Object.keys(existing.insights || {});
    const incomingInsightKeys = hasInsights ? Object.keys(apiInsights) : [];
    console.debug('[SESSION_DEBUG] updateFromAnalysis:', {
      sessionId: sessionId?.substring(0, 8),
      existingInsightKeys,
      incomingInsightKeys,
      insightSource: hasInsights ? 'API response' : 'preserved from cache',
      finalKPIsCount: (patch.finalKPIs ?? existing.finalKPIs ?? []).length,
      dashboardChartsCount:
        (patch.dashboardPlan?.dashboard?.charts ?? existing.dashboardPlan?.dashboard?.charts ?? []).length,
    });
    // ── END DEBUG LOG ──────────────────────────────────────────────────────

    analysisSessionStorage.mergeSessionData(sessionId, patch);
    return analysisSessionStorage.getSessionData(sessionId);
  },
};

export default kpiPersonalizationStorage;
