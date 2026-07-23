import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useAnalysis } from '../context/AnalysisContext';
import { useTheme } from '../context/ThemeContext';
import { apiService } from '../services/api';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip
} from 'recharts';
import { CustomBarChart } from '../components/CustomBarChart';
import {
  Sun,
  Moon,
  ArrowLeft,
  ShieldCheck,
  AlertTriangle,
  Lightbulb,
  ClipboardList,
  Download,
  DollarSign,
  ShoppingCart,
  Clock,
  Coins,
  Percent,
  TrendingUp,
  Smile,
  Table,
  CheckCircle,
  Activity
} from 'lucide-react';

const COLORS = ['#6366f1', '#a855f7', '#ec4899', '#f43f5e', '#eab308', '#06b6d4', '#10b981'];
const monthNames = ["", "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

// Client-side Business Health Score calculation matching report_generator.py logic
const calculateHealthScore = (kpis) => {
  const rating = kpis?.satisfaction_kpis?.avg_customer_rating ?? 4.0;
  const repeat = kpis?.customer_kpis?.repeat_customer_rate ?? 20.0;
  const cancellation = kpis?.order_kpis?.cancellation_rate ?? 5.0;
  const delay = kpis?.delivery_kpis?.delayed_order_rate ?? 15.0;
  const lowMargin = kpis?.unit_economics_kpis?.low_margin_order_pct ?? 10.0;

  let score = 80;
  score += (rating - 4.0) * 15.0;
  score += (repeat - 20.0) * 0.4;
  score -= (cancellation - 5.0) * 3.0;
  score -= (delay - 15.0) * 0.5;
  score -= (lowMargin - 10.0) * 0.8;

  score = Math.max(0, Math.min(100, Math.round(score)));

  let classification = "Healthy";
  let themeColor = "indigo"; // colors: green, blue, purple, rose
  if (score >= 90) {
    classification = "Excellent";
    themeColor = "emerald";
  } else if (score >= 75) {
    classification = "Healthy";
    themeColor = "indigo";
  } else if (score >= 60) {
    classification = "Needs Improvement";
    themeColor = "amber";
  } else {
    classification = "Critical";
    themeColor = "rose";
  }

  const explanation = `The business receives an operational score of ${score} (${classification}). This diagnostic is driven by customer satisfaction metrics (average rating: ${rating.toFixed(2)}) and repeat order rates (${repeat.toFixed(2)}%). However, addressing a ${cancellation.toFixed(2)}% cancellation index and ${delay.toFixed(2)}% SLA delivery delays represent crucial paths for unlocking margin optimization.`;

  return { score, classification, explanation, themeColor };
};

const Dashboard = () => {
  const { logout, user, sessionId, analysisResults } = useAnalysis();
  const { darkMode, toggleDarkMode } = useTheme();
  
  const [downloading, setDownloading] = useState(false);
  const [downloadError, setDownloadError] = useState('');

  if (!analysisResults) {
    return (
      <div className="min-h-screen bg-slate-50 dark:bg-[#0d0e12] flex items-center justify-center flex-col gap-6 text-slate-900 dark:text-slate-100 p-4 transition-colors duration-200">
        <div className="text-center max-w-sm">
          <AlertTriangle className="w-12 h-12 text-slate-400 dark:text-slate-500 mx-auto mb-4" />
          <h2 className="text-xl font-bold mb-2">No Analysis Found</h2>
          <p className="text-slate-600 dark:text-slate-400 text-sm mb-6 leading-relaxed">
            You haven't run any data diagnostics yet. Please upload a dataset first.
          </p>
          <Link
            to="/upload"
            className="inline-flex items-center justify-center px-5 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-semibold cursor-pointer transition-all duration-200"
          >
            Go to Upload Page
          </Link>
        </div>
      </div>
    );
  }

  const { cleaning_report, kpis, insights, engineering } = analysisResults;

  // Calculate Health score details
  const health = calculateHealthScore(kpis);

  // Download executive PDF/HTML report from backend
  const handleDownloadReport = async () => {
    if (!sessionId) return;
    setDownloading(true);
    setDownloadError('');
    try {
      const { blob, contentDisposition } = await apiService.getReportBlob(sessionId);
      
      let filename = `diagnostic_report_${sessionId.substring(0, 8)}.pdf`;
      if (contentDisposition) {
        const matches = /filename="?([^"]+)"?/.exec(contentDisposition);
        if (matches && matches[1]) {
          filename = matches[1];
        }
      }
      
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.setAttribute("href", url);
      link.setAttribute("download", filename);
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
    } catch (err) {
      console.error(err);
      setDownloadError(err.message || "Failed to download executive report. Please check if the backend is running.");
    } finally {
      setDownloading(false);
    }
  };

  // Chart data formatting
  const categoryData = Object.entries(kpis?.revenue_kpis?.revenue_by_category || {}).map(([key, val]) => ({
    name: key,
    revenue: val
  }));

  const cityData = Object.entries(kpis?.revenue_kpis?.revenue_by_city || {}).map(([key, val]) => ({
    name: key,
    revenue: val
  }));

  const slotOrder = ["Morning", "Afternoon", "Evening", "Night"];
  const timeSlotData = Object.entries(kpis?.revenue_kpis?.revenue_by_time_slot || {}).map(([key, val]) => ({
    name: key,
    revenue: val
  })).sort((a, b) => slotOrder.indexOf(a.name) - slotOrder.indexOf(b.name));

  const dayOrder = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];
  const dayOfWeekData = Object.entries(kpis?.revenue_kpis?.revenue_by_day_of_week || {}).map(([key, val]) => ({
    name: key,
    revenue: val
  })).sort((a, b) => dayOrder.indexOf(a.name) - dayOrder.indexOf(b.name));

  const ratingData = Object.entries(kpis?.satisfaction_kpis?.rating_trend_by_month || {}).map(([key, val]) => ({
    name: monthNames[parseInt(key)] || `Month ${key}`,
    rating: val
  })).sort((a, b) => monthNames.indexOf(a.name) - monthNames.indexOf(b.name));

  const pincodeData = Object.entries(kpis?.hyperlocal_kpis?.orders_by_pincode || {})
    .slice(0, 10)
    .map(([key, val]) => ({
      name: key,
      orders: val
    }));

  const cancelReasons = Object.entries(kpis?.satisfaction_kpis?.cancellation_reason_breakdown || {}).map(([key, val]) => ({
    name: key,
    value: val
  }));

  const axisColor = darkMode ? "#94a3b8" : "#475569";
  const gridColor = darkMode ? "#1e293b" : "#e2e8f0";
  const tooltipBg = darkMode ? "#1e2030" : "#ffffff";
  const tooltipBorder = darkMode ? "#3b4252" : "#cbd5e1";
  const tooltipText = darkMode ? "#f8fafc" : "#0f172a";

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-[#0d0e12] text-slate-800 dark:text-slate-100 font-sans transition-colors duration-200">
      
      {/* Header */}
      <header className="sticky top-0 z-40 w-full border-b border-slate-200 dark:border-slate-800 bg-white/80 dark:bg-[#0d0e12]/80 backdrop-blur-md">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Link to="/upload" className="w-8 h-8 rounded-xl bg-gradient-to-tr from-indigo-500 to-violet-600 flex items-center justify-center cursor-pointer transition-transform hover:scale-105">
              <ArrowLeft className="w-4 h-4 text-white" />
            </Link>
            <span className="text-base sm:text-lg font-black tracking-tight">Diagnostics Workspace</span>
          </div>

          <div className="flex items-center gap-2 sm:gap-4">
            <button
              onClick={toggleDarkMode}
              className="p-2 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-100 hover:bg-slate-200 dark:bg-slate-900/50 dark:hover:bg-slate-800 cursor-pointer transition-colors duration-200 text-slate-600 dark:text-slate-300"
              title={darkMode ? "Switch to Light Mode" : "Switch to Dark Mode"}
            >
              {darkMode ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
            </button>

            {user && (
              <div className="flex items-center gap-2 sm:gap-3">
                {user.photoURL ? (
                  <img src={user.photoURL} alt="Avatar" className="w-8 h-8 rounded-full border border-slate-300 dark:border-slate-700" />
                ) : (
                  <div className="w-8 h-8 rounded-full bg-slate-200 dark:bg-slate-800 flex items-center justify-center text-xs font-semibold border border-slate-300 dark:border-slate-700 text-slate-600 dark:text-slate-300">
                    {user.email?.charAt(0).toUpperCase()}
                  </div>
                )}
                <button
                  onClick={logout}
                  className="px-3 py-1.5 rounded-lg border border-slate-200 dark:border-slate-850 bg-white hover:bg-slate-100 dark:bg-slate-900/50 dark:hover:bg-slate-800 text-xs font-medium cursor-pointer transition-all duration-200 text-slate-600 dark:text-slate-300"
                >
                  Logout
                </button>
              </div>
            )}
          </div>
        </div>
      </header>

      {/* Main body */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        
        {/* Workspace Title & PDF download action */}
        <section className="mb-8 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h2 className="text-2xl sm:text-3xl font-black tracking-tight">Executive Summary</h2>
            <p className="text-slate-500 dark:text-slate-400 text-xs sm:text-sm mt-0.5">Performance insights computed from {cleaning_report?.cleaned_rows?.toLocaleString()} verified q-commerce orders.</p>
          </div>
          <button
            onClick={handleDownloadReport}
            disabled={downloading}
            className="inline-flex items-center justify-center gap-1.5 px-4 py-2.5 rounded-xl border border-slate-200 dark:border-indigo-500/30 hover:border-slate-400 dark:hover:border-indigo-500/60 bg-white dark:bg-indigo-500/10 text-slate-700 dark:text-indigo-400 font-bold text-xs cursor-pointer hover:scale-[1.02] active:scale-[0.98] transition-all duration-200 disabled:opacity-50 disabled:pointer-events-none"
          >
            {downloading ? (
              <div className="w-3.5 h-3.5 rounded-full border border-indigo-500/20 border-t-indigo-500 animate-spin"></div>
            ) : (
              <Download className="w-3.5 h-3.5" />
            )}
            {downloading ? "Compiling PDF..." : "Download Report (PDF)"}
          </button>
        </section>

        {downloadError && (
          <div className="mb-6 p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-500 dark:text-rose-450 text-xs flex items-center gap-2.5 shadow-sm">
            <AlertTriangle className="w-4 h-4 shrink-0 animate-bounce" />
            <span>{downloadError}</span>
          </div>
        )}

        {/* Business Health Score Callout Card */}
        <section className="mb-8 rounded-3xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-[#12131a]/40 p-6 shadow-sm flex flex-col md:flex-row items-center gap-6">
          <div className={`w-28 h-28 shrink-0 rounded-2xl flex flex-col items-center justify-center text-white font-black text-center shadow-lg ${
            health.themeColor === 'emerald' ? 'bg-emerald-500 shadow-emerald-500/10' :
            health.themeColor === 'indigo' ? 'bg-indigo-500 shadow-indigo-500/10' :
            health.themeColor === 'amber' ? 'bg-amber-500 shadow-amber-500/10' :
            'bg-rose-500 shadow-rose-500/10'
          }`}>
            <span className="text-3xl">{health.score}</span>
            <span className="text-[9px] font-bold uppercase tracking-wider mt-1">{health.classification}</span>
          </div>
          <div className="space-y-1 text-center md:text-left">
            <h3 className="text-lg font-bold tracking-tight">AI Diagnostics & Operations Health Score</h3>
            <p className="text-sm text-slate-500 dark:text-slate-400 leading-relaxed max-w-3xl">{health.explanation}</p>
          </div>
        </section>

        {/* 1. Top row: 5 KPI Cards */}
        <section className="grid grid-cols-2 lg:grid-cols-5 gap-4 mb-8">
          <div className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-[#12131a]/40 p-4 sm:p-5 backdrop-blur-sm shadow-sm transition-all duration-200 hover:border-indigo-500/30">
            <div className="flex items-center justify-between text-slate-400 mb-2">
              <span className="text-[10px] sm:text-xs font-bold uppercase tracking-wider">Total Revenue</span>
              <DollarSign className="w-4 h-4 text-indigo-500" />
            </div>
            <h3 className="text-xl sm:text-2xl font-black">₹{(kpis?.revenue_kpis?.total_revenue || 0).toLocaleString()}</h3>
            <p className="text-[10px] text-slate-500 dark:text-slate-400 mt-1">Platform gross sales value</p>
          </div>

          <div className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-[#12131a]/40 p-4 sm:p-5 backdrop-blur-sm shadow-sm transition-all duration-200 hover:border-purple-500/30">
            <div className="flex items-center justify-between text-slate-400 mb-2">
              <span className="text-[10px] sm:text-xs font-bold uppercase tracking-wider">Total Orders</span>
              <ShoppingCart className="w-4 h-4 text-purple-500" />
            </div>
            <h3 className="text-xl sm:text-2xl font-black">{(kpis?.order_kpis?.total_orders || 0).toLocaleString()}</h3>
            <p className="text-[10px] text-slate-500 dark:text-slate-400 mt-1">Cleaned transactions logged</p>
          </div>

          <div className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-[#12131a]/40 p-4 sm:p-5 backdrop-blur-sm shadow-sm transition-all duration-200 hover:border-pink-500/30">
            <div className="flex items-center justify-between text-slate-400 mb-2">
              <span className="text-[10px] sm:text-xs font-bold uppercase tracking-wider">Avg Delivery Time</span>
              <Clock className="w-4 h-4 text-pink-500" />
            </div>
            <h3 className="text-xl sm:text-2xl font-black">{kpis?.delivery_kpis?.avg_delivery_time}m</h3>
            <p className="text-[10px] text-slate-500 dark:text-slate-400 mt-1">Fulfillment cycle time</p>
          </div>

          <div className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-[#12131a]/40 p-4 sm:p-5 backdrop-blur-sm shadow-sm transition-all duration-200 hover:border-emerald-500/30">
            <div className="flex items-center justify-between text-slate-400 mb-2">
              <span className="text-[10px] sm:text-xs font-bold uppercase tracking-wider">Avg Profit Margin</span>
              <Coins className="w-4 h-4 text-emerald-500" />
            </div>
            <h3 className="text-xl sm:text-2xl font-black">₹{kpis?.unit_economics_kpis?.avg_profit_margin_per_order}</h3>
            <p className="text-[10px] text-slate-500 dark:text-slate-400 mt-1">Unit economics net margin</p>
          </div>

          <div className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-[#12131a]/40 p-4 sm:p-5 backdrop-blur-sm shadow-sm transition-all duration-200 hover:border-rose-500/30 col-span-2 lg:col-span-1">
            <div className="flex items-center justify-between text-slate-400 mb-2">
              <span className="text-[10px] sm:text-xs font-bold uppercase tracking-wider">Cancel Rate</span>
              <Percent className="w-4 h-4 text-rose-500" />
            </div>
            <h3 className="text-xl sm:text-2xl font-black">{kpis?.order_kpis?.cancellation_rate}%</h3>
            <p className="text-[10px] text-slate-500 dark:text-slate-400 mt-1">Percent orders cancelled</p>
          </div>
        </section>

        {/* Ingestion & Feature Engineering Summaries */}
        <section className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          {/* Data Cleansing Report */}
          <div className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-[#12131a]/40 p-5 shadow-sm md:col-span-1">
            <div className="flex items-center gap-2 mb-4 text-indigo-500">
              <CheckCircle className="w-4 h-4" />
              <h4 className="text-xs font-bold uppercase tracking-wider">Data Cleansing Summary</h4>
            </div>
            <div className="space-y-3.5 text-xs">
              <div className="flex justify-between border-b border-slate-100 dark:border-slate-900 pb-2">
                <span className="text-slate-500 dark:text-slate-400 font-medium">Initial Ingested Rows</span>
                <span className="font-bold">{cleaning_report?.initial_rows?.toLocaleString()}</span>
              </div>
              <div className="flex justify-between border-b border-slate-100 dark:border-slate-900 pb-2">
                <span className="text-slate-500 dark:text-slate-400 font-medium">Cleaned Output Rows</span>
                <span className="font-bold">{cleaning_report?.cleaned_rows?.toLocaleString()}</span>
              </div>
              <div className="flex justify-between border-b border-slate-100 dark:border-slate-900 pb-2">
                <span className="text-slate-500 dark:text-slate-400 font-medium">Removed Duplicates</span>
                <span className="font-bold text-indigo-500">{cleaning_report?.duplicates_removed}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500 dark:text-slate-400 font-medium">Capped Negative Fields</span>
                <span className="font-bold text-amber-500">
                  {Object.values(cleaning_report?.impossible_values_capped || {}).reduce((a, b) => a + b, 0)}
                </span>
              </div>
            </div>
          </div>

          {/* Feature Engineering Report */}
          <div className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-[#12131a]/40 p-5 shadow-sm md:col-span-2">
            <div className="flex items-center gap-2 mb-4 text-purple-500">
              <Activity className="w-4 h-4" />
              <h4 className="text-xs font-bold uppercase tracking-wider">Feature Engineering Summary</h4>
            </div>
            <p className="text-xs text-slate-500 dark:text-slate-400 mb-3.5 leading-relaxed">
              Added <strong>{engineering?.new_columns?.length || 12}</strong> derived features to enrich operations metrics. Newly added analysis headers:
            </p>
            <div className="flex flex-wrap gap-1.5 max-h-[110px] overflow-y-auto">
              {(engineering?.new_columns || [
                "order_day_of_week", "order_month", "is_weekend", "order_hour", 
                "time_slot", "customer_order_count", "delivery_delay_minutes", 
                "is_delayed", "estimated_fulfillment_cost", "estimated_profit_margin", 
                "is_low_margin_order", "rider_utilization_pct"
              ]).map((col) => (
                <span key={col} className="px-2 py-1 rounded bg-slate-100 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-[10px] font-semibold text-slate-600 dark:text-slate-300">
                  {col}
                </span>
              ))}
            </div>
          </div>
        </section>

        {/* Feature Engineering Preview Table */}
        {engineering?.preview && engineering.preview.length > 0 && (
          <section className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-[#12131a]/40 p-5 shadow-sm mb-8">
            <div className="flex items-center gap-2 mb-4 text-teal-500">
              <Table className="w-4 h-4" />
              <h4 className="text-xs font-bold uppercase tracking-wider">Engineered Dataset Preview (Top Rows)</h4>
            </div>
            <div className="overflow-x-auto border border-slate-200 dark:border-slate-850 rounded-xl">
              <table className="w-full text-[10px] text-left border-collapse">
                <thead>
                  <tr className="bg-slate-50 dark:bg-slate-900 text-slate-500 uppercase tracking-wider font-semibold border-b border-slate-200 dark:border-slate-850">
                    <th className="px-4 py-2.5">Order ID</th>
                    <th className="px-4 py-2.5">Day of Week</th>
                    <th className="px-4 py-2.5">Time Slot</th>
                    <th className="px-4 py-2.5">Delayed</th>
                    <th className="px-4 py-2.5">Fulfillment Cost</th>
                    <th className="px-4 py-2.5">Profit Margin</th>
                    <th className="px-4 py-2.5">Rider Util %</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-150 dark:divide-slate-850">
                  {engineering.preview.map((row, idx) => (
                    <tr key={idx} className="hover:bg-slate-100/30 dark:hover:bg-slate-900/10">
                      <td className="px-4 py-2.5 font-bold">{row.order_id}</td>
                      <td className="px-4 py-2.5 text-slate-500 dark:text-slate-400">{row.order_day_of_week || "N/A"}</td>
                      <td className="px-4 py-2.5 text-slate-500 dark:text-slate-400">{row.time_slot || "N/A"}</td>
                      <td className="px-4 py-2.5">
                        <span className={`px-2 py-0.5 rounded text-[8px] font-bold ${row.is_delayed ? 'bg-rose-500/10 text-rose-500' : 'bg-emerald-500/10 text-emerald-500'}`}>
                          {row.is_delayed ? 'DELAYED' : 'ON TIME'}
                        </span>
                      </td>
                      <td className="px-4 py-2.5 font-medium">₹{parseFloat(row.estimated_fulfillment_cost || 0).toFixed(2)}</td>
                      <td className={`px-4 py-2.5 font-bold ${row.estimated_profit_margin < 0 ? 'text-rose-500' : 'text-emerald-500'}`}>
                        ₹{parseFloat(row.estimated_profit_margin || 0).toFixed(2)}
                      </td>
                      <td className="px-4 py-2.5 font-medium">{parseFloat(row.rider_utilization_pct || 0).toFixed(2)}%</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        )}

        {/* 2. Charts Section */}
        <section className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          <div className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-[#12131a]/40 p-5 backdrop-blur-sm shadow-sm">
            <h4 className="text-sm font-bold tracking-wide mb-4 text-slate-700 dark:text-slate-300">Revenue by Category</h4>
            <CustomBarChart
              data={categoryData}
              dataKey="name"
              barKey="revenue"
              barColor="#6366f1"
              axisColor={axisColor}
              gridColor={gridColor}
              tooltipBg={tooltipBg}
              tooltipBorder={tooltipBorder}
              tooltipText={tooltipText}
              labelName="Revenue (₹)"
            />
          </div>

          <div className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-[#12131a]/40 p-5 backdrop-blur-sm shadow-sm">
            <h4 className="text-sm font-bold tracking-wide mb-4 text-slate-700 dark:text-slate-300">Revenue by City</h4>
            <CustomBarChart
              data={cityData}
              dataKey="name"
              barKey="revenue"
              barColor="#a855f7"
              axisColor={axisColor}
              gridColor={gridColor}
              tooltipBg={tooltipBg}
              tooltipBorder={tooltipBorder}
              tooltipText={tooltipText}
              labelName="Revenue (₹)"
            />
          </div>

          <div className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-[#12131a]/40 p-5 backdrop-blur-sm shadow-sm">
            <h4 className="text-sm font-bold tracking-wide mb-4 text-slate-700 dark:text-slate-300">Revenue by Time Slot</h4>
            <CustomBarChart
              data={timeSlotData}
              dataKey="name"
              barKey="revenue"
              barColor="#06b6d4"
              axisColor={axisColor}
              gridColor={gridColor}
              tooltipBg={tooltipBg}
              tooltipBorder={tooltipBorder}
              tooltipText={tooltipText}
              labelName="Revenue (₹)"
            />
          </div>

          <div className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-[#12131a]/40 p-5 backdrop-blur-sm shadow-sm">
            <h4 className="text-sm font-bold tracking-wide mb-4 text-slate-700 dark:text-slate-300">Revenue by Day of Week</h4>
            <CustomBarChart
              data={dayOfWeekData}
              dataKey="name"
              barKey="revenue"
              barColor="#10b981"
              axisColor={axisColor}
              gridColor={gridColor}
              tooltipBg={tooltipBg}
              tooltipBorder={tooltipBorder}
              tooltipText={tooltipText}
              labelName="Revenue (₹)"
            />
          </div>

          <div className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-[#12131a]/40 p-5 backdrop-blur-sm shadow-sm">
            <h4 className="text-sm font-bold tracking-wide mb-4 text-slate-700 dark:text-slate-300">Rating Trend by Month</h4>
            <div className="w-full h-[260px]">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={ratingData} margin={{ top: 10, right: 15, left: -10, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke={gridColor} />
                  <XAxis dataKey="name" stroke={axisColor} fontSize={10} tickLine={false} />
                  <YAxis stroke={axisColor} domain={[1, 5]} fontSize={10} tickLine={false} />
                  <Tooltip contentStyle={{ backgroundColor: tooltipBg, borderColor: tooltipBorder, color: tooltipText }} />
                  <Line type="monotone" dataKey="rating" stroke="#ec4899" strokeWidth={3} activeDot={{ r: 6 }} name="Avg Rating" />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-[#12131a]/40 p-5 backdrop-blur-sm shadow-sm">
            <h4 className="text-sm font-bold tracking-wide mb-4 text-slate-700 dark:text-slate-300">Orders by Pincode (Top 10)</h4>
            <div className="w-full h-[260px]">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={pincodeData} margin={{ top: 10, right: 10, left: -10, bottom: 5 }} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" stroke={gridColor} />
                  <XAxis type="number" stroke={axisColor} fontSize={10} tickLine={false} />
                  <YAxis dataKey="name" type="category" stroke={axisColor} fontSize={10} tickLine={false} />
                  <Tooltip contentStyle={{ backgroundColor: tooltipBg, borderColor: tooltipBorder, color: tooltipText }} />
                  <Bar dataKey="orders" fill="#06b6d4" radius={[0, 4, 4, 0]} name="Order Count" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-[#12131a]/40 p-5 backdrop-blur-sm shadow-sm lg:col-span-2">
            <h4 className="text-sm font-bold tracking-wide mb-4 text-slate-700 dark:text-slate-300">Cancellation Reason Breakdown</h4>
            <div className="w-full h-[260px] flex flex-col sm:flex-row items-center justify-center gap-6">
              {cancelReasons.length > 0 ? (
                <>
                  <div className="w-[180px] h-[180px] shrink-0">
                    <ResponsiveContainer width="100%" height="100%">
                      <PieChart>
                        <Pie
                          data={cancelReasons}
                          cx="50%"
                          cy="50%"
                          innerRadius={50}
                          outerRadius={80}
                          paddingAngle={3}
                          dataKey="value"
                        >
                          {cancelReasons.map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                          ))}
                        </Pie>
                        <Tooltip contentStyle={{ backgroundColor: tooltipBg, borderColor: tooltipBorder, color: tooltipText }} />
                      </PieChart>
                    </ResponsiveContainer>
                  </div>
                  
                  <div className="flex flex-col gap-2 max-w-sm">
                    {cancelReasons.map((entry, index) => (
                      <div key={entry.name} className="flex items-center gap-2 text-xs font-medium">
                        <span className="w-3 h-3 rounded-full shrink-0" style={{ backgroundColor: COLORS[index % COLORS.length] }}></span>
                        <span className="text-slate-600 dark:text-slate-300 truncate max-w-xs">{entry.name}: <strong>{entry.value}</strong></span>
                      </div>
                    ))}
                  </div>
                </>
              ) : (
                <div className="text-center py-10">
                  <Smile className="w-10 h-10 text-emerald-500 mx-auto mb-2" />
                  <p className="text-sm font-bold text-slate-700 dark:text-slate-300">No Cancellations Recorded</p>
                  <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">The dataset contains 100% successful and active orders.</p>
                </div>
              )}
            </div>
          </div>
        </section>

        {/* 3. AI Insights Section */}
        <section className="mb-8">
          <div className="flex items-center gap-2 mb-6">
            <TrendingUp className="w-5 h-5 text-indigo-500" />
            <h3 className="text-xl font-black tracking-tight">AI Executive Diagnostics</h3>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="rounded-2xl border border-indigo-200 dark:border-indigo-950 bg-indigo-500/5 p-6 backdrop-blur-sm">
              <div className="flex items-center gap-2 mb-4 text-indigo-600 dark:text-indigo-400">
                <ShieldCheck className="w-5 h-5 shrink-0" />
                <h4 className="font-bold text-sm uppercase tracking-wider">Key Strengths</h4>
              </div>
              <ul className="space-y-3">
                {(insights?.strengths || []).map((strength, idx) => (
                  <li key={idx} className="text-slate-700 dark:text-slate-300 text-xs sm:text-sm leading-relaxed flex items-start gap-2.5">
                    <span className="w-1.5 h-1.5 rounded-full bg-indigo-500 shrink-0 mt-2"></span>
                    {strength}
                  </li>
                ))}
              </ul>
            </div>

            <div className="rounded-2xl border border-rose-200 dark:border-rose-950 bg-rose-500/5 p-6 backdrop-blur-sm">
              <div className="flex items-center gap-2 mb-4 text-rose-600 dark:text-rose-400">
                <AlertTriangle className="w-5 h-5 shrink-0" />
                <h4 className="font-bold text-sm uppercase tracking-wider">Bottlenecks & Risks</h4>
              </div>
              <ul className="space-y-3">
                {(insights?.bottlenecks || []).map((bottleneck, idx) => (
                  <li key={idx} className="text-slate-700 dark:text-slate-300 text-xs sm:text-sm leading-relaxed flex items-start gap-2.5">
                    <span className="w-1.5 h-1.5 rounded-full bg-rose-500 shrink-0 mt-2"></span>
                    {bottleneck}
                  </li>
                ))}
              </ul>
            </div>

            <div className="rounded-2xl border border-purple-200 dark:border-purple-950 bg-purple-500/5 p-6 backdrop-blur-sm">
              <div className="flex items-center gap-2 mb-4 text-purple-600 dark:text-purple-400">
                <Lightbulb className="w-5 h-5 shrink-0" />
                <h4 className="font-bold text-sm uppercase tracking-wider">Opportunities</h4>
              </div>
              <ul className="space-y-3">
                {(insights?.opportunities || []).map((opportunity, idx) => (
                  <li key={idx} className="text-slate-700 dark:text-slate-300 text-xs sm:text-sm leading-relaxed flex items-start gap-2.5">
                    <span className="w-1.5 h-1.5 rounded-full bg-purple-500 shrink-0 mt-2"></span>
                    {opportunity}
                  </li>
                ))}
              </ul>
            </div>

            <div className="rounded-2xl border border-emerald-200 dark:border-emerald-950 bg-emerald-500/5 p-6 backdrop-blur-sm">
              <div className="flex items-center gap-2 mb-4 text-emerald-600 dark:text-emerald-400">
                <ClipboardList className="w-5 h-5 shrink-0" />
                <h4 className="font-bold text-sm uppercase tracking-wider">Actionable Recommendations</h4>
              </div>
              <ul className="space-y-3">
                {(insights?.recommendations || []).map((rec, idx) => (
                  <li key={idx} className="text-slate-700 dark:text-slate-300 text-xs sm:text-sm leading-relaxed flex items-start gap-2.5">
                    <span className="font-bold text-emerald-500 shrink-0">{idx + 1}.</span>
                    {rec.replace(/^\d+\.\s*/, '')}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </section>
      </main>
    </div>
  );
};

export default Dashboard;
