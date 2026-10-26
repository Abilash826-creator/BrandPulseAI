import React from 'react';
import { Sparkles, CheckCircle2, TrendingUp, ShieldCheck } from 'lucide-react';

const InsightsBox = ({ insights = {}, loading = false }) => {
  if (loading) {
    return (
      <div className="p-6 rounded-2xl bg-white border border-slate-200 animate-pulse space-y-3 shadow-sm">
        <div className="h-4 bg-slate-100 rounded w-1/3"></div>
        <div className="h-16 bg-slate-100 rounded"></div>
        <div className="h-10 bg-slate-100 rounded"></div>
      </div>
    );
  }

  const { health_status, executive_summary, key_drivers = [], recommended_actions = [] } = insights;

  return (
    <div className="p-6 rounded-2xl bg-white border border-purple-200 shadow-sm relative overflow-hidden space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2.5">
          <div className="p-2 rounded-xl bg-purple-50 text-[#7C3AED] border border-purple-200">
            <Sparkles className="w-4 h-4" />
          </div>
          <div>
            <h4 className="text-sm font-bold text-slate-900 tracking-tight">Executive AI Intelligence Summary</h4>
            <p className="text-[11px] text-slate-500">Autonomous synthesis of sentiment, topics & consumer friction</p>
          </div>
        </div>

        <div className={`flex items-center space-x-1.5 px-3 py-1 rounded-full text-xs font-semibold ${
          health_status 
            ? 'bg-emerald-50 border border-emerald-200 text-[#16A34A]'
            : 'bg-slate-100 border border-slate-200 text-slate-600'
        }`}>
          <ShieldCheck className="w-3.5 h-3.5" />
          <span>Health: {health_status || 'Pending Data'}</span>
        </div>
      </div>

      {/* Executive Brief Paragraph */}
      <p className="text-xs text-slate-700 leading-relaxed bg-purple-50/50 p-3.5 rounded-xl border border-purple-100">
        {executive_summary || 'No customer reviews recorded yet. Upload reviews or connect feedback sources to generate autonomous AI intelligence and sentiment drivers.'}
      </p>

      {/* Two columns: Drivers & Recommended Actions */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-1 text-xs">
        {/* Key Sentiment Drivers */}
        <div className="space-y-2">
          <div className="font-bold flex items-center space-x-1.5 text-[11px] uppercase tracking-wider text-[#7C3AED]">
            <TrendingUp className="w-3.5 h-3.5" />
            <span>Key Conversation Drivers</span>
          </div>
          <div className="space-y-1.5">
            {key_drivers.length > 0 ? (
              key_drivers.map((driver, idx) => (
                <div key={idx} className="p-2.5 rounded-xl bg-slate-50 border border-slate-200 text-slate-700 flex items-start space-x-2">
                  <span className="w-1.5 h-1.5 rounded-full bg-[#7C3AED] mt-1.5 shrink-0" />
                  <span className="leading-relaxed">{driver}</span>
                </div>
              ))
            ) : (
              <div className="p-3.5 rounded-xl bg-slate-50 border border-dashed border-slate-200 text-slate-400 text-xs">
                No conversation drivers identified yet.
              </div>
            )}
          </div>
        </div>

        {/* Actionable Recommendations */}
        <div className="space-y-2">
          <div className="font-bold flex items-center space-x-1.5 text-[11px] uppercase tracking-wider text-[#16A34A]">
            <CheckCircle2 className="w-3.5 h-3.5" />
            <span>Actionable Next Steps</span>
          </div>
          <div className="space-y-1.5">
            {recommended_actions.length > 0 ? (
              recommended_actions.map((action, idx) => (
                <div key={idx} className="p-2.5 rounded-xl bg-emerald-50/60 border border-emerald-200 text-emerald-900 flex items-start space-x-2">
                  <span className="w-1.5 h-1.5 rounded-full bg-[#16A34A] mt-1.5 shrink-0" />
                  <span className="leading-relaxed">{action}</span>
                </div>
              ))
            ) : (
              <div className="p-3.5 rounded-xl bg-slate-50 border border-dashed border-slate-200 text-slate-400 text-xs">
                No immediate actions required yet.
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default InsightsBox;
