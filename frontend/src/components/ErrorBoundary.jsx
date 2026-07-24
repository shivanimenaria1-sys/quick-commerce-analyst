import React, { Component } from 'react';

export class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    // Update state so the next render will show the fallback UI.
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error("ErrorBoundary caught an error:", error, errorInfo);
  }

  handleRetry = () => {
    this.setState({ hasError: false, error: null });
    if (this.props.onRetry) {
      this.props.onRetry();
    }
  };

  render() {
    if (this.state.hasError) {
      return (
        <div className="p-6 rounded-3xl border border-red-500/20 bg-red-500/[0.02] text-center space-y-4 min-h-[160px] flex flex-col items-center justify-center">
          <div className="w-10 h-10 rounded-full bg-red-500/10 flex items-center justify-center text-red-500">
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          </div>
          <div className="space-y-1">
            <h4 className="text-sm font-bold text-slate-800 dark:text-slate-100">Component Render Failure</h4>
            <p className="text-xs text-slate-500 dark:text-slate-400 max-w-sm leading-relaxed">
              {this.props.message || "An error occurred while compiling the user interface details for this card."}
            </p>
          </div>
          <button
            onClick={this.handleRetry}
            className="px-4 py-1.5 rounded-lg bg-slate-200 dark:bg-slate-800 text-[10px] font-bold transition-all hover:bg-slate-350 dark:hover:bg-slate-750 cursor-pointer"
          >
            Retry Render
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
