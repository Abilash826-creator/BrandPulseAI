import React from 'react';
import { 
  Star, 
  MessageSquare, 
  CheckCircle2, 
  AlertTriangle, 
  Sparkles, 
  X, 
  ArrowUpRight,
  ArrowDownRight,
  TrendingUp,
  BarChart3
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';

const DashboardKpis = ({ overview, activeBrand, ingestToast, onDismissToast }) => {
  const navigate = useNavigate();

  // Compute average star rating from overview or fallback
  const totalReviews = overview?.total_mentions || 0;
  const netMood = overview?.net_sentiment_score || 0;
  const hasReviews = totalReviews > 0;
  
  // Convert net sentiment score (-100 to +100) to estimated stars (1.0 to 5.0) if raw rating is not directly exposed
  const estimatedStars = hasReviews
    ? (overview?.average_rating 
        ? Number(overview.average_rating).toFixed(1)
        : (netMood ? ((3.0 + (netMood / 50.0)).toFixed(1)) : '3.0'))
    : null;

  const unrepliedCount = overview?.unreplied_count !== undefined 
    ? overview.unreplied_count 
    : Math.max(0, Math.floor(totalReviews * 0.25));

  const needsAttention = overview?.crisis_risk_index > 35;

  return (
    <div className="space-y-4">
      {/* Ingested Dataset Celebration Banner */}
      {ingestToast && (
        <div className="p-4 rounded-2xl bg-gradient-to-r from-emerald-600 to-teal-600 text-white shadow-md flex items-center justify-between animate-fade-in border border-emerald-400/30">
          <div className="flex items-center space-x-3.5">
            <div className="p-2.5 rounded-xl bg-white/20 shadow-xs shrink-0">
              <Sparkles className="w-5 h-5 text-white animate-pulse" />
            </div>
            <div>
              <div className="flex items-center space-x-2 flex-wrap">
                <h4 className="text-sm font-extrabold tracking-tight text-white">
                  Customer Reviews Analyzed Successfully!
                </h4>
                <span className="px-2 py-0.5 rounded-full bg-white/20 text-white text-[10px] font-bold">
                  Ready
                </span>
              </div>
              <p className="text-xs text-emerald-100 mt-0.5">
                Processed <strong>{ingestToast.count} customer reviews</strong> for <strong>{ingestToast.brandName}</strong>. Your ratings and feedback topics are updated.
              </p>
            </div>
          </div>

          <button
            onClick={onDismissToast}
            className="p-1.5 rounded-xl bg-white/20 hover:bg-white/30 text-white transition text-xs shrink-0 ml-2"
            title="Dismiss notification"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* 3 Core Small-Business KPIs + Nearby Comparison */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* KPI 1: Average Customer Rating */}
        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs flex flex-col justify-between">
          <div>
            <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider block mb-1">
              Customer Happiness (Rating)
            </span>
            <div className="flex items-baseline space-x-2">
              <span className="text-3xl font-black text-slate-900">
                {hasReviews ? estimatedStars : '—'}
              </span>
              <div className="flex text-amber-400 text-sm">
                {hasReviews ? (
                  '★'.repeat(Math.min(5, Math.max(1, Math.round(Number(estimatedStars)))))
                ) : (
                  <span className="text-xs text-slate-400 font-medium">No ratings yet</span>
                )}
              </div>
            </div>
          </div>
          <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-xs">
            <span className="text-slate-500 text-[11px]">Mood score:</span>
            {hasReviews ? (
              <span className={`font-bold px-2 py-0.5 rounded-full text-[11px] ${
                netMood >= 0 ? 'bg-emerald-50 text-emerald-700' : 'bg-red-50 text-red-700'
              }`}>
                {netMood >= 0 ? `+${netMood}% Positive` : `${netMood}% Negative`}
              </span>
            ) : (
              <span className="font-medium text-slate-400 text-[11px]">No reviews yet</span>
            )}
          </div>
        </div>

        {/* KPI 2: Total Customer Reviews */}
        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs flex flex-col justify-between">
          <div>
            <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider block mb-1">
              Customer Reviews This Period
            </span>
            <div className="flex items-baseline space-x-2">
              <span className="text-3xl font-black text-slate-900">{totalReviews.toLocaleString()}</span>
              <span className="text-xs font-semibold text-slate-500">reviews</span>
            </div>
          </div>
          <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-xs">
            <span className="text-slate-500 text-[11px]">Trajectory:</span>
            {hasReviews ? (
              <span className="font-bold text-emerald-600 flex items-center text-[11px]">
                <ArrowUpRight className="w-3.5 h-3.5 mr-0.5" />
                <span>Active reviews</span>
              </span>
            ) : (
              <span className="font-medium text-slate-400 text-[11px]">Awaiting data</span>
            )}
          </div>
        </div>

        {/* KPI 3: Unreplied Reviews (With direct action) */}
        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-1">
              <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider">
                Unreplied Reviews
              </span>
              {unrepliedCount > 0 && (
                <span className="w-2 h-2 rounded-full bg-amber-500 animate-pulse"></span>
              )}
            </div>
            <div className="flex items-baseline space-x-2">
              <span className={`text-3xl font-black ${unrepliedCount > 0 ? 'text-amber-600' : 'text-slate-900'}`}>
                {unrepliedCount}
              </span>
              <span className="text-xs font-medium text-slate-500">waiting for reply</span>
            </div>
          </div>
          <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-xs">
            <button
              onClick={() => navigate('/social-listening')}
              className="text-xs font-bold text-blue-600 hover:text-blue-800 transition flex items-center space-x-1"
            >
              <span>Reply to reviews →</span>
            </button>
          </div>
        </div>

        {/* KPI 4: Comparison with Nearby Shops */}
        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs flex flex-col justify-between">
          <div>
            <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider block mb-1">
              How you compare with nearby shops
            </span>
            <div className="flex items-baseline space-x-2">
              <span className="text-3xl font-black text-slate-900">
                {overview?.share_of_voice !== undefined && overview?.share_of_voice !== null
                  ? `${overview.share_of_voice}%`
                  : (hasReviews ? '0%' : '—')}
              </span>
              <span className="text-xs font-medium text-slate-500">local visibility</span>
            </div>
          </div>
          <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-xs">
            <button
              onClick={() => navigate('/competitor-analysis')}
              className="text-xs font-bold text-slate-700 hover:text-blue-600 transition flex items-center space-x-1"
            >
              <BarChart3 className="w-3.5 h-3.5 mr-1" />
              <span>View local shops →</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DashboardKpis;
