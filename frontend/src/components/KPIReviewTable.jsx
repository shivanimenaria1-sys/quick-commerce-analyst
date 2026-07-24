import React, { useState, useEffect } from 'react';
import kpiPersonalizationStorage from '../services/storageService';

const KPIReviewTable = ({ kpis, fingerprint, onConfirm }) => {
  const [items, setItems] = useState([]);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    const loadSelections = async () => {
      const savedSelections = await kpiPersonalizationStorage.getSelection(fingerprint);
      
      const initialized = kpis.map((kpi) => {
        const isSelected = savedSelections
          ? savedSelections.includes(kpi.id)
          : kpi.selected;
        return { ...kpi, selected: isSelected };
      });
      
      setItems(initialized);
    };

    if (kpis) {
      loadSelections();
    }
  }, [kpis, fingerprint]);

  const handleToggle = async (kpiId) => {
    const updated = items.map((item) => {
      if (item.id === kpiId) {
        return { ...item, selected: !item.selected };
      }
      return item;
    });
    setItems(updated);

    // Save selection configuration using storage abstraction
    const activeIds = updated.filter((item) => item.selected).map((item) => item.id);
    await kpiPersonalizationStorage.saveSelection(fingerprint, activeIds);
  };

  const handleSaveAndContinue = () => {
    setSaving(true);
    setTimeout(() => {
      onConfirm(items.filter((item) => item.selected));
      setSaving(false);
    }, 600);
  };

  // Helper to format structured formula to user-friendly string
  const formatFormula = (formula) => {
    if (!formula) return 'N/A';
    const op = formula.operation || 'AGG';
    const fields = formula.fields || [];
    const fieldString = fields.map(f => f.replace('_like', '')).join(', ');
    return `${op}(${fieldString})`;
  };

  return (
    <div className="w-full max-w-4xl mx-auto rounded-3xl border border-slate-200 dark:border-slate-800 bg-white/70 dark:bg-[#111217]/50 backdrop-blur-xl p-8 shadow-2xl relative overflow-hidden transition-all duration-300">
      {/* Background radial highlight */}
      <div className="absolute -top-10 -right-10 w-48 h-48 bg-indigo-500/10 rounded-full blur-[80px] pointer-events-none"></div>

      <div className="flex flex-col md:flex-row md:items-center md:justify-between border-b border-slate-200 dark:border-slate-800 pb-6 mb-6 gap-4">
        <div>
          <h3 className="text-xl font-black tracking-tight bg-gradient-to-r from-indigo-500 to-violet-500 bg-clip-text text-transparent">
            Review Prioritized KPIs
          </h3>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
            Gemini ranked candidates based on domain context. Select which metrics you want to enable for final insights.
          </p>
        </div>

        <button
          onClick={handleSaveAndContinue}
          disabled={saving}
          className="inline-flex items-center justify-center gap-2 px-6 py-2.5 rounded-2xl bg-gradient-to-tr from-indigo-500 to-violet-600 hover:from-indigo-600 hover:to-violet-700 text-white text-xs font-bold transition-all duration-200 cursor-pointer shadow-lg shadow-indigo-500/25 active:scale-[0.98]"
        >
          {saving ? (
            <>
              <div className="w-4 h-4 border-2 border-white/20 border-t-white rounded-full animate-spin"></div>
              Saving Priorities...
            </>
          ) : (
            <>
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
              </svg>
              Confirm KPIs & Continue
            </>
          )}
        </button>
      </div>

      <div className="overflow-x-auto rounded-2xl border border-slate-200 dark:border-slate-800">
        <table className="min-w-full divide-y divide-slate-200 dark:divide-slate-800 text-left text-xs">
          <thead className="bg-slate-50/50 dark:bg-slate-900/30 text-slate-500 dark:text-slate-400 font-bold uppercase tracking-wider">
            <tr>
              <th className="px-5 py-4 w-12 text-center">Active</th>
              <th className="px-5 py-4">KPI / Label</th>
              <th className="px-5 py-4">Formula / Roles</th>
              <th className="px-5 py-4">Importance</th>
              <th className="px-5 py-4">Domain Reasoning</th>
            </tr>
          </thead>

          <tbody className="divide-y divide-slate-200 dark:divide-slate-800 bg-white/30 dark:bg-transparent">
            {items.map((kpi) => {
              const importancePct = Math.round(kpi.importance * 100);
              
              // Color tags based on priority/importance
              let impColor = 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/20';
              if (kpi.importance < 0.4) {
                impColor = 'bg-slate-100 text-slate-500 dark:bg-slate-800 dark:text-slate-400 border-slate-200 dark:border-slate-800';
              } else if (kpi.importance < 0.7) {
                impColor = 'bg-amber-500/10 text-amber-600 dark:text-amber-400 border-amber-500/20';
              }

              return (
                <tr
                  key={kpi.id}
                  className={`transition-colors duration-150 hover:bg-slate-50/40 dark:hover:bg-slate-800/10 ${
                    kpi.selected ? '' : 'opacity-60 bg-slate-100/10'
                  }`}
                >
                  <td className="px-5 py-4 text-center">
                    <button
                      onClick={() => handleToggle(kpi.id)}
                      className={`w-10 h-6 rounded-full p-0.5 transition-colors duration-250 focus:outline-none cursor-pointer inline-flex items-center ${
                        kpi.selected ? 'bg-indigo-500 justify-end' : 'bg-slate-300 dark:bg-slate-700 justify-start'
                      }`}
                    >
                      <span className="w-5 h-5 rounded-full bg-white shadow-md transform transition-transform duration-250"></span>
                    </button>
                  </td>

                  <td className="px-5 py-4">
                    <div className="font-bold tracking-tight text-slate-800 dark:text-slate-200">
                      {kpi.display_name}
                    </div>
                    <div className="font-mono text-[10px] text-slate-400 mt-0.5">
                      id: {kpi.id}
                    </div>
                  </td>

                  <td className="px-5 py-4">
                    <div className="font-mono text-[11px] text-indigo-500 dark:text-indigo-400 font-bold">
                      {formatFormula(kpi.formula)}
                    </div>
                    <div className="flex flex-wrap gap-1 mt-1">
                      {kpi.required_semantic_roles.map((role) => (
                        <span
                          key={role}
                          className="px-1.5 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-slate-500 dark:text-slate-400 text-[9px] font-semibold"
                        >
                          {role.replace('_like', '')}
                        </span>
                      ))}
                    </div>
                  </td>

                  <td className="px-5 py-4">
                    <span className={`inline-flex items-center px-2.5 py-1 rounded-full text-[10px] font-bold border ${impColor}`}>
                      {importancePct}%
                    </span>
                  </td>

                  <td className="px-5 py-4 max-w-xs">
                    <p className="text-slate-600 dark:text-slate-350 italic text-[11px]">
                      "{kpi.reason || kpi.explanation}"
                    </p>
                    {kpi.dependencies && kpi.dependencies.length > 0 && (
                      <div className="mt-1 flex flex-wrap gap-1 items-center">
                        <span className="text-[9px] text-slate-400 uppercase tracking-wider font-semibold">Depends on:</span>
                        {kpi.dependencies.map(depId => (
                          <span
                            key={depId}
                            className="inline-flex items-center px-1 rounded bg-indigo-500/10 text-indigo-500 dark:text-indigo-400 text-[9px] font-semibold"
                          >
                            {depId}
                          </span>
                        ))}
                      </div>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default KPIReviewTable;
