import React from 'react';
import { Instagram, Package, Sparkles, ThumbsUp, ThumbsDown, ChevronRight, ShieldCheck, Info } from 'lucide-react';

const DashboardAspectIntelligence = ({ activeBrand, igMetrics, trackedProducts, navigate }) => {
  return (
    <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-5">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 pb-3 border-b border-slate-100">
        <div>
          <div className="flex items-center space-x-2">
            <div className="p-1.5 rounded-lg bg-pink-50 border border-pink-200 text-pink-600">
              <Instagram className="w-4 h-4" />
            </div>
            <h3 className="text-sm font-extrabold text-slate-900 tracking-tight">
              Instagram Business & Customer Feedback Summary
            </h3>
            <span className="px-2 py-0.5 rounded-full bg-emerald-50 border border-emerald-200 text-[#16A34A] text-[10px] font-bold">
              Automated Analysis Active
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Real-time breakdown of customer praises and complaints across posts, Reels, and reviews
          </p>
        </div>

        <button
          onClick={() => navigate('/brand-settings')}
          className="text-xs font-semibold text-[#2563EB] hover:text-[#1E3A8A] flex items-center space-x-1 transition"
        >
          <span>Manage Social Channels</span>
          <ChevronRight className="w-3.5 h-3.5" />
        </button>
      </div>

      {/* 4 Mini Stat Blocks */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
        <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200/60">
          <span className="text-[11px] text-slate-500 font-medium block">Total Customer Posts</span>
          <span className="text-lg font-bold text-slate-900 mt-1 block">
            {igMetrics?.total_media_ingested !== undefined ? igMetrics.total_media_ingested : 0}
          </span>
          <span className="text-[10px] text-slate-400 font-semibold">
            {igMetrics?.total_media_ingested ? '100% relevant to brand' : 'No posts synced'}
          </span>
        </div>

        <div className="p-3.5 rounded-xl bg-blue-50/50 border border-blue-200/60">
          <span className="text-[11px] text-blue-800 font-medium block">Products Tracked</span>
          <span className="text-lg font-bold text-[#2563EB] mt-1 block">
            {trackedProducts.length}
          </span>
          <span className="text-[10px] text-blue-500 truncate block">
            {trackedProducts.join(', ')}
          </span>
        </div>

        <div className="p-3.5 rounded-xl bg-emerald-50/50 border border-emerald-200/60">
          <span className="text-[11px] text-emerald-800 font-medium block">Happy Customer Rate</span>
          <span className="text-lg font-bold text-[#16A34A] mt-1 block">
            {igMetrics?.positive_rate !== undefined ? `${Math.round(igMetrics.positive_rate)}%` : '—'}
          </span>
          <span className="text-[10px] text-slate-400">
            {igMetrics?.positive_rate !== undefined ? 'Calculated from feedback' : 'Awaiting feedback'}
          </span>
        </div>

        <div className="p-3.5 rounded-xl bg-purple-50/50 border border-purple-200/60">
          <span className="text-[11px] text-purple-800 font-medium block">Video & Reels Audio</span>
          <span className="text-lg font-bold text-purple-700 mt-1 block">
            {igMetrics?.media_type_distribution?.REEL || 0} Transcripts
          </span>
          <span className="text-[10px] text-purple-500">Speech transcribed with AI</span>
        </div>
      </div>

      {/* Aspect Praise vs Complaints Row */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs pt-1">
        {/* Top Aspect Praise */}
        <div className="p-4 rounded-xl bg-emerald-50/30 border border-emerald-200/60 space-y-2">
          <div className="flex items-center space-x-1.5 font-bold text-[#16A34A]">
            <ThumbsUp className="w-3.5 h-3.5" />
            <span>What Customers Love Most</span>
          </div>
          <div className="space-y-1.5 pt-1">
            {igMetrics?.top_aspect_praise && igMetrics.top_aspect_praise.length > 0 ? (
              igMetrics.top_aspect_praise.map((item, idx) => (
                <div key={idx} className="flex items-center justify-between text-[11px]">
                  <span className="text-slate-700 font-medium">✨ {item.aspect}</span>
                  <span className="px-2 py-0.5 rounded-md bg-emerald-100 text-[#16A34A] font-bold text-[10px]">
                    {item.count} positive mentions
                  </span>
                </div>
              ))
            ) : (
              <div className="p-4 text-center text-slate-400 text-xs">
                No praised aspects detected yet.
              </div>
            )}
          </div>
        </div>

        {/* Top Aspect Complaints */}
        <div className="p-4 rounded-xl bg-red-50/30 border border-red-200/60 space-y-2">
          <div className="flex items-center space-x-1.5 font-bold text-[#DC2626]">
            <ThumbsDown className="w-3.5 h-3.5" />
            <span>Top Customer Complaints & Issues</span>
          </div>
          <div className="space-y-1.5 pt-1">
            {igMetrics?.top_aspect_complaints && igMetrics.top_aspect_complaints.length > 0 ? (
              igMetrics.top_aspect_complaints.map((item, idx) => (
                <div key={idx} className="flex items-center justify-between text-[11px]">
                  <span className="text-slate-700 font-medium">⚠️ {item.aspect}</span>
                  <span className="px-2 py-0.5 rounded-md bg-red-100 text-[#DC2626] font-bold text-[10px]">
                    {item.count} complaints
                  </span>
                </div>
              ))
            ) : (
              <div className="p-4 text-center text-slate-400 text-xs">
                No complaint aspects detected yet.
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default DashboardAspectIntelligence;
