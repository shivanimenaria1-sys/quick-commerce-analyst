import React, { useState, useEffect } from 'react';

const EvaluationDashboard = ({ onClose }) => {
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchMetrics = async () => {
      try {
        const response = await fetch('/api/evaluation/metrics');
        if (!response.ok) {
          throw new Error('Failed to load evaluation metrics.');
        }
        const data = await response.json();
        setMetrics(data);
      } catch (err) {
        setError(err.message || 'An error occurred while loading developer insights.');
      } finally {
        setLoading(false);
      }
    };
    fetchMetrics();
  }, []);

  if (loading) {
    return (
      <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm z-50 flex items-center justify-center">
        <div className="bg-white dark:bg-[#111217] rounded-3xl p-8 max-w-sm w-full text-center space-y-4 shadow-2xl border border-slate-200 dark:border-slate-800">
          <div className="w-10 h-10 border-4 border-indigo-500/20 border-t-indigo-500 rounded-full animate-spin mx-auto"></div>
          <p className="text-xs text-slate-500 dark:text-slate-400 font-bold">Compiling Developer Calibration Metrics...</p>
        </div>
      </div>
    );
  }

  if (error || !metrics) {
    return (
      <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm z-50 flex items-center justify-center">
        <div className="bg-white dark:bg-[#111217] rounded-3xl p-8 max-w-sm w-full text-center space-y-4 shadow-2xl border border-slate-200 dark:border-slate-850">
          <p className="text-rose-500 text-sm font-bold">{error || 'Data Unavailable'}</p>
          <button onClick={onClose} className="px-4 py-2 bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 text-xs font-bold rounded-xl cursor-pointer">
            Close
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 bg-slate-950/70 backdrop-blur-md z-50 flex items-center justify-center p-4 overflow-y-auto">
      <div className="bg-white dark:bg-[#111217] rounded-3xl max-w-4xl w-full p-8 shadow-2xl border border-slate-200 dark:border-slate-800 relative space-y-6 max-h-[90vh] overflow-y-auto">
        
        {/* Header */}
        <div className="flex justify-between items-center border-b border-slate-200 dark:border-slate-800 pb-4">
          <div>
            <span className="text-[10px] bg-indigo-500/10 text-indigo-500 px-2 py-0.5 rounded font-bold uppercase tracking-wider">Devs Only &bull; Calibration Sandbox</span>
            <h3 className="text-xl font-black mt-1 bg-gradient-to-r from-indigo-500 to-violet-500 bg-clip-text text-transparent">
              Semantic Mapping Calibration & Performance Metrics
            </h3>
          </div>
          <button
            onClick={onClose}
            className="w-8 h-8 rounded-full bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 flex items-center justify-center text-slate-500 hover:text-slate-700 dark:hover:text-slate-200 transition-colors cursor-pointer text-sm font-bold"
          >
            &times;
          </button>
        </div>

        {/* Top metrics summary grid */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="p-4 rounded-2xl border border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-900/30">
            <span className="block text-[10px] uppercase font-bold text-slate-400">Mapping Accuracy</span>
            <span className="text-2xl font-black text-indigo-500 mt-1 block">
              {Math.round(metrics.mapping_accuracy * 100)}%
            </span>
            <span className="text-[9px] text-slate-500 dark:text-slate-400 mt-1 block">Total sample: {metrics.total_evaluations} corrections</span>
          </div>
          
          <div className="p-4 rounded-2xl border border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-900/30">
            <span className="block text-[10px] uppercase font-bold text-slate-400">Cache Hit Rate</span>
            <span className="text-2xl font-black text-emerald-500 mt-1 block">
              {Math.round(metrics.cache_hit_rate * 100)}%
            </span>
            <span className="text-[9px] text-slate-500 dark:text-slate-400 mt-1 block">Hits from semantic_cache.json</span>
          </div>

          <div className="p-4 rounded-2xl border border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-900/30">
            <span className="block text-[10px] uppercase font-bold text-slate-400">Avg Pipeline Time</span>
            <span className="text-2xl font-black text-slate-800 dark:text-slate-200 mt-1 block">
              {metrics.average_pipeline_execution_time_ms}ms
            </span>
            <span className="text-[9px] text-slate-500 dark:text-slate-400 mt-1 block">End-to-End processing log</span>
          </div>

          <div className="p-4 rounded-2xl border border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-900/30">
            <span className="block text-[10px] uppercase font-bold text-slate-400">LLM Retries / Fails</span>
            <span className="text-2xl font-black text-rose-500 mt-1 block">
              {metrics.llm_retry_counts} / {metrics.validation_failures}
            </span>
            <span className="text-[9px] text-slate-500 dark:text-slate-400 mt-1 block">Structured parsing recovery logs</span>
          </div>
        </div>

        {/* Detailed Precision/Recall Table */}
        <div className="space-y-2">
          <h4 className="text-xs uppercase font-bold text-slate-400 tracking-wider">Per-Semantic-Role Classification Metrics</h4>
          <div className="overflow-x-auto rounded-xl border border-slate-200 dark:border-slate-800">
            <table className="min-w-full text-left text-xs text-slate-600 dark:text-slate-350">
              <thead className="bg-slate-50 dark:bg-slate-900/30 text-[10px] uppercase font-bold text-slate-500 dark:text-slate-400">
                <tr>
                  <th className="px-4 py-3">Semantic Role</th>
                  <th className="px-4 py-3">Precision</th>
                  <th className="px-4 py-3">Recall</th>
                  <th className="px-4 py-3">F1 Score</th>
                  <th className="px-4 py-3">Support</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200 dark:divide-slate-800">
                {Object.entries(metrics.precision_recall).map(([role, stats]) => (
                  <tr key={role} className="hover:bg-slate-50/40 dark:hover:bg-slate-800/10">
                    <td className="px-4 py-3 font-mono text-[11px] text-indigo-500 dark:text-indigo-400 font-bold">{role}</td>
                    <td className="px-4 py-3">{stats.precision}</td>
                    <td className="px-4 py-3">{stats.recall}</td>
                    <td className="px-4 py-3">{stats.f1_score}</td>
                    <td className="px-4 py-3 text-slate-400">{stats.support}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Confusion matrix structure analysis */}
        <div className="space-y-2">
          <h4 className="text-xs uppercase font-bold text-slate-400 tracking-wider">Historical Confusion Matrix Map (Actual vs Inferred)</h4>
          <div className="overflow-x-auto rounded-xl border border-slate-200 dark:border-slate-800 p-4 bg-slate-50/20 dark:bg-slate-900/10 font-mono text-[10px]">
            <pre className="text-indigo-400 whitespace-pre-wrap">
              {JSON.stringify(metrics.confusion_matrix, null, 2)}
            </pre>
          </div>
        </div>

        {/* Confidence Calibration */}
        <div className="space-y-2">
          <h4 className="text-xs uppercase font-bold text-slate-400 tracking-wider">Calibration Accuracy Bin checks</h4>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            {metrics.confidence_calibration.map((cal, idx) => (
              <div key={idx} className="p-3 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-transparent text-xs space-y-1">
                <div className="font-bold text-slate-700 dark:text-slate-300">Conf. Bin: {cal.confidence_bucket}</div>
                <div className="flex justify-between text-[11px] text-slate-500">
                  <span>Target: {Math.round(cal.expected_accuracy * 100)}%</span>
                  <span className="font-bold text-indigo-500">Observed: {Math.round(cal.actual_accuracy * 100)}%</span>
                </div>
              </div>
            ))}
          </div>
        </div>

      </div>
    </div>
  );
};

export default EvaluationDashboard;
