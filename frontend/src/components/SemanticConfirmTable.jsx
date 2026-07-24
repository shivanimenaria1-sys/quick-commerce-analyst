import React, { useState } from 'react';

const SEMANTIC_ROLES = [
  "revenue_like",
  "cost_like",
  "profit_like",
  "price_like",
  "quantity_like",
  "date_like",
  "datetime_like",
  "customer_id_like",
  "product_id_like",
  "employee_like",
  "category_like",
  "location_like",
  "rating_like",
  "duration_like",
  "status_like",
  "boolean_flag_like",
  "percentage_like",
  "currency_like",
  "text_like",
  "id_like",
  "unknown"
];

const SemanticConfirmTable = ({ mapping, onConfirm, onOverride }) => {
  const [currentColumns, setCurrentColumns] = useState(mapping.columns || {});
  const [confirming, setConfirming] = useState(false);

  const handleRoleChange = async (columnName, newRole) => {
    const originalRole = currentColumns[columnName].semantic_role;
    if (originalRole === newRole) return;

    // Local UI update
    const updated = {
      ...currentColumns,
      [columnName]: {
        ...currentColumns[columnName],
        semantic_role: newRole,
        confidence: 1.0, // Mark override as absolute confidence
        needs_user_confirmation: false
      }
    };
    setCurrentColumns(updated);

    // Call parent handler to log user correction backend override
    if (onOverride) {
      await onOverride(columnName, originalRole, newRole);
    }
  };

  const handleConfirmAll = () => {
    setConfirming(true);
    setTimeout(() => {
      onConfirm(currentColumns);
      setConfirming(false);
    }, 600);
  };

  return (
    <div className="w-full max-w-4xl mx-auto rounded-3xl border border-slate-200 dark:border-slate-800 bg-white/70 dark:bg-[#111217]/50 backdrop-blur-xl p-8 shadow-2xl relative overflow-hidden transition-all duration-300">
      {/* Background radial highlight */}
      <div className="absolute -top-10 -right-10 w-48 h-48 bg-indigo-500/10 rounded-full blur-[80px] pointer-events-none"></div>
      
      <div className="flex flex-col md:flex-row md:items-center md:justify-between border-b border-slate-200 dark:border-slate-800 pb-6 mb-6 gap-4">
        <div>
          <h3 className="text-xl font-black tracking-tight bg-gradient-to-r from-indigo-500 to-violet-500 bg-clip-text text-transparent">
            Confirm Column Semantics
          </h3>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
            Gemini has inferred the semantic meaning of each column based on its datatypes and statistics. Overwrite roles if necessary.
          </p>
        </div>
        
        <button
          onClick={handleConfirmAll}
          disabled={confirming}
          className="inline-flex items-center justify-center gap-2 px-6 py-2.5 rounded-2xl bg-gradient-to-tr from-indigo-500 to-violet-600 hover:from-indigo-600 hover:to-violet-700 text-white text-xs font-bold transition-all duration-200 cursor-pointer shadow-lg shadow-indigo-500/25 active:scale-[0.98]"
        >
          {confirming ? (
            <>
              <div className="w-4 h-4 border-2 border-white/20 border-t-white rounded-full animate-spin"></div>
              Saving Mappings...
            </>
          ) : (
            <>
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
              </svg>
              Confirm and Continue
            </>
          )}
        </button>
      </div>

      <div className="overflow-x-auto rounded-2xl border border-slate-200 dark:border-slate-800">
        <table className="min-w-full divide-y divide-slate-200 dark:divide-slate-800 text-left text-xs">
          <thead className="bg-slate-50/50 dark:bg-slate-900/30 text-slate-500 dark:text-slate-400 font-bold uppercase tracking-wider">
            <tr>
              <th className="px-5 py-4">Column</th>
              <th className="px-5 py-4">Suggested Role</th>
              <th className="px-5 py-4">Confidence</th>
              <th className="px-5 py-4">Alternatives / Reasoning</th>
            </tr>
          </thead>
          
          <tbody className="divide-y divide-slate-200 dark:divide-slate-800 bg-white/30 dark:bg-transparent">
            {Object.entries(currentColumns).map(([colName, colData]) => {
              const { semantic_role, confidence, reasoning, alternative_roles, needs_user_confirmation } = colData;
              
              // Color tags based on confidence level
              let confColor = 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/20';
              if (needs_user_confirmation) {
                confColor = 'bg-rose-500/10 text-rose-500 dark:text-rose-400 border-rose-500/20';
              } else if (confidence < 0.8) {
                confColor = 'bg-amber-500/10 text-amber-600 dark:text-amber-400 border-amber-500/20';
              }
              
              return (
                <tr
                  key={colName}
                  className={`transition-colors duration-150 hover:bg-slate-50/40 dark:hover:bg-slate-800/10 ${
                    needs_user_confirmation ? 'bg-rose-500/[0.02]' : ''
                  }`}
                >
                  <td className="px-5 py-4 font-bold tracking-tight text-slate-800 dark:text-slate-200">
                    {colName}
                    {needs_user_confirmation && (
                      <span className="block mt-1 text-[9px] font-bold text-rose-500 dark:text-rose-400 uppercase tracking-wider animate-pulse">
                        Requires Confirmation
                      </span>
                    )}
                  </td>
                  
                  <td className="px-5 py-4">
                    <div className="relative inline-block w-48">
                      <select
                        value={semantic_role}
                        onChange={(e) => handleRoleChange(colName, e.target.value)}
                        className="w-full px-3 py-1.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/80 font-medium text-xs text-slate-700 dark:text-slate-200 focus:outline-none focus:ring-1 focus:ring-indigo-500 transition-all duration-200 cursor-pointer"
                      >
                        {SEMANTIC_ROLES.map((role) => (
                          <option key={role} value={role}>
                            {role.replace('_like', '')}
                          </option>
                        ))}
                      </select>
                    </div>
                  </td>
                  
                  <td className="px-5 py-4">
                    <span className={`inline-flex items-center px-2.5 py-1 rounded-full text-[10px] font-bold border ${confColor}`}>
                      {Math.round(confidence * 100)}%
                    </span>
                  </td>
                  
                  <td className="px-5 py-4 max-w-sm">
                    <p className="text-slate-600 dark:text-slate-350 italic text-[11px]">
                      "{reasoning}"
                    </p>
                    
                    {alternative_roles && alternative_roles.length > 0 && (
                      <div className="mt-1.5 flex flex-wrap gap-1 items-center">
                        <span className="text-[10px] text-slate-400">Alt:</span>
                        {alternative_roles.map((alt, index) => (
                          <span
                            key={index}
                            className="inline-flex items-center px-1.5 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-slate-500 dark:text-slate-400 text-[10px]"
                          >
                            {alt.role.replace('_like', '')} ({Math.round(alt.confidence * 100)}%)
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

export default SemanticConfirmTable;
