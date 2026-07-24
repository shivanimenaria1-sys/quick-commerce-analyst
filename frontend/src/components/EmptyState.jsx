import React from 'react';

export const EmptyState = ({ title, description, actionText, onAction, iconType = 'default' }) => {
  let icon = (
    <svg className="w-10 h-10 text-slate-350 dark:text-slate-700 mx-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
  );

  if (iconType === 'search') {
    icon = (
      <svg className="w-10 h-10 text-slate-350 dark:text-slate-700 mx-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
      </svg>
    );
  } else if (iconType === 'session') {
    icon = (
      <svg className="w-10 h-10 text-red-500/80 mx-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    );
  }

  return (
    <div className="rounded-3xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-[#111217]/30 p-12 text-center space-y-4 max-w-lg mx-auto shadow-sm animate-fade-in select-none">
      <div className="p-3 bg-slate-50 dark:bg-slate-900/50 rounded-2xl w-fit mx-auto border border-slate-200 dark:border-slate-800/80">
        {icon}
      </div>
      <div className="space-y-1">
        <h4 className="text-sm font-bold text-slate-800 dark:text-slate-100">{title}</h4>
        <p className="text-xs text-slate-450 dark:text-slate-500 max-w-sm mx-auto leading-relaxed">{description}</p>
      </div>
      {actionText && onAction && (
        <button
          onClick={onAction}
          className="px-5 py-2.5 rounded-xl border border-indigo-500/20 bg-indigo-500/10 hover:bg-indigo-500/15 text-indigo-500 text-xs font-bold transition-all cursor-pointer"
        >
          {actionText}
        </button>
      )}
    </div>
  );
};

export default EmptyState;
