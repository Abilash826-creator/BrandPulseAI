import React from 'react';
import { 
  ThumbsUp, 
  Wrench, 
  Sparkles, 
  ArrowRight, 
  MessageSquare, 
  FileText, 
  ShieldAlert,
  CheckCircle2,
  AlertCircle
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';

const OwnerInsightsCard = ({ insights, overview, mentions = [], activeBrand }) => {
  const navigate = useNavigate();

  // Extract top praised topics and top issues
  const rawPraises = insights?.top_positive_topics || [];
  const rawIssues = insights?.top_negative_topics || [];

  const praises = rawPraises.slice(0, 3);
  const issues = rawIssues.slice(0, 3);

  // 1-2 star recent reviews needing attention
  const attentionReviews = mentions.filter(m => (m.rating && m.rating <= 2) || m.sentiment === 'negative').slice(0, 2);

  const totalReviews = overview?.total_mentions || 0;

  return (
    <div className="space-y-5">
      {/* Big "Needs Your Attention" Card */}
      {attentionReviews.length > 0 ? (
        <div className="bg-gradient-to-r from-amber-500/10 via-red-500/10 to-transparent p-5 sm:p-6 rounded-3xl border border-amber-300/80 shadow-xs">
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 mb-4">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 rounded-2xl bg-amber-500 text-white flex items-center justify-center shrink-0 shadow-sm">
                <AlertCircle className="w-5 h-5" />
              </div>
              <div>
                <h3 className="font-extrabold text-slate-900 text-sm sm:text-base">
                  Needs Your Attention ({attentionReviews.length} recent complaint{attentionReviews.length > 1 ? 's' : ''})
                </h3>
                <p className="text-xs text-slate-600">
                  Customers gave low ratings. Responding within 24 hours protects your shop's reputation.
                </p>
              </div>
            </div>

            <button
              onClick={() => navigate('/social-listening')}
              className="px-4 py-2 rounded-xl bg-amber-600 hover:bg-amber-700 text-white font-bold text-xs transition shadow-xs flex items-center space-x-1.5 shrink-0"
            >
              <span>Reply to Reviews</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {attentionReviews.map((rev, idx) => (
              <div key={idx} className="bg-white p-3.5 rounded-2xl border border-amber-200/80 shadow-2xs text-xs space-y-1.5">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-slate-900">{rev.author || 'Customer'}</span>
                  <span className="text-amber-600 font-bold">{'★'.repeat(rev.rating || 1)} ({rev.rating || 1} star)</span>
                </div>
                <p className="text-slate-700 italic line-clamp-2">
                  "{rev.content || rev.translated_text || 'Customer expressed dissatisfaction.'}"
                </p>
                <div className="pt-1 flex items-center justify-between text-[11px] text-slate-400">
                  <span>Source: {rev.source || 'Google'}</span>
                  <button
                    onClick={() => navigate('/ask')}
                    className="text-blue-600 font-semibold hover:underline flex items-center space-x-1"
                  >
                    <Sparkles className="w-3 h-3" />
                    <span>Draft AI reply</span>
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      ) : totalReviews > 0 ? (
        <div className="bg-gradient-to-r from-emerald-50 to-teal-50 p-5 rounded-2xl border border-emerald-200 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <CheckCircle2 className="w-6 h-6 text-emerald-600 shrink-0" />
            <div>
              <h4 className="font-extrabold text-sm text-emerald-950">Needs Attention: All Clear!</h4>
              <p className="text-xs text-emerald-700">No urgent complaints or sudden rating drops detected this week.</p>
            </div>
          </div>
          <button
            onClick={() => navigate('/ask')}
            className="hidden sm:flex items-center space-x-1.5 px-3.5 py-1.5 rounded-xl bg-white text-emerald-800 font-bold text-xs border border-emerald-300 shadow-2xs hover:bg-emerald-100 transition"
          >
            <Sparkles className="w-3.5 h-3.5 text-emerald-600" />
            <span>Ask AI for Ideas</span>
          </button>
        </div>
      ) : (
        <div className="bg-gradient-to-r from-slate-50 to-blue-50/40 p-5 rounded-2xl border border-slate-200 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <CheckCircle2 className="w-6 h-6 text-slate-400 shrink-0" />
            <div>
              <h4 className="font-extrabold text-sm text-slate-800">Needs Attention: No Activity Yet</h4>
              <p className="text-xs text-slate-500">No reviews recorded yet. Upload reviews to monitor customer sentiment and complaints in real time.</p>
            </div>
          </div>
          <button
            onClick={() => navigate('/dataset-ingestion')}
            className="hidden sm:flex items-center space-x-1.5 px-3.5 py-1.5 rounded-xl bg-white text-blue-700 font-bold text-xs border border-blue-200 shadow-2xs hover:bg-blue-50 transition"
          >
            <Sparkles className="w-3.5 h-3.5 text-blue-600" />
            <span>Upload Reviews</span>
          </button>
        </div>
      )}

      {/* Two Columns: "What Customers Love" & "What to Fix First" */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        {/* What Customers Love */}
        <div className="bg-white p-5 sm:p-6 rounded-3xl border border-slate-200 shadow-xs space-y-4">
          <div className="flex items-center space-x-2.5 pb-3 border-b border-slate-100">
            <div className="w-8 h-8 rounded-xl bg-emerald-50 text-emerald-700 flex items-center justify-center font-bold">
              <ThumbsUp className="w-4 h-4" />
            </div>
            <div>
              <h3 className="font-extrabold text-sm text-slate-900">What Customers Love Most</h3>
              <p className="text-[11px] text-slate-500">Top positive themes mentioned in your 4-5 star reviews</p>
            </div>
          </div>

          <div className="space-y-2.5">
            {praises.length > 0 ? (
              praises.map((p, idx) => (
                <div key={idx} className="flex items-center justify-between p-3 rounded-2xl bg-emerald-50/50 border border-emerald-100/60 text-xs">
                  <div className="flex items-center space-x-2.5">
                    <span className="w-5 h-5 rounded-full bg-emerald-600 text-white flex items-center justify-center text-[10px] font-bold shrink-0">
                      {idx + 1}
                    </span>
                    <span className="font-bold text-slate-800">{p.topic || p.theme}</span>
                  </div>
                  <span className="text-[11px] font-semibold text-emerald-700 bg-white px-2.5 py-0.5 rounded-full border border-emerald-200 shadow-2xs">
                    {p.count} praises
                  </span>
                </div>
              ))
            ) : (
              <div className="p-6 rounded-2xl bg-slate-50 border border-dashed border-slate-200 text-center text-xs text-slate-400 space-y-1">
                <p className="font-semibold text-slate-600">No praises recorded yet</p>
                <p className="text-[11px]">Upload customer reviews or sync your channels to see top highlights.</p>
              </div>
            )}
          </div>
        </div>

        {/* What to Fix First */}
        <div className="bg-white p-5 sm:p-6 rounded-3xl border border-slate-200 shadow-xs space-y-4">
          <div className="flex items-center space-x-2.5 pb-3 border-b border-slate-100">
            <div className="w-8 h-8 rounded-xl bg-amber-50 text-amber-700 flex items-center justify-center font-bold">
              <Wrench className="w-4 h-4" />
            </div>
            <div>
              <h3 className="font-extrabold text-sm text-slate-900">What to Fix First</h3>
              <p className="text-[11px] text-slate-500">Frequent pain points causing lower star ratings</p>
            </div>
          </div>

          <div className="space-y-2.5">
            {issues.length > 0 ? (
              issues.map((iss, idx) => (
                <div key={idx} className="flex items-center justify-between p-3 rounded-2xl bg-amber-50/40 border border-amber-100/60 text-xs">
                  <div className="flex items-center space-x-2.5">
                    <span className="w-5 h-5 rounded-full bg-amber-600 text-white flex items-center justify-center text-[10px] font-bold shrink-0">
                      {idx + 1}
                    </span>
                    <span className="font-bold text-slate-800">{iss.topic || iss.theme}</span>
                  </div>
                  <span className="text-[11px] font-semibold text-amber-700 bg-white px-2.5 py-0.5 rounded-full border border-amber-200 shadow-2xs">
                    {iss.count} complaints
                  </span>
                </div>
              ))
            ) : (
              <div className="p-6 rounded-2xl bg-slate-50 border border-dashed border-slate-200 text-center text-xs text-slate-400 space-y-1">
                <p className="font-semibold text-slate-600">No complaints detected</p>
                <p className="text-[11px]">No friction points or issues found. Customer feedback looks clean.</p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Weekly Plain-Language Summary Box */}
      <div className="bg-white p-5 sm:p-6 rounded-3xl border border-slate-200 shadow-xs space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Sparkles className="w-4 h-4 text-blue-600" />
            <h3 className="font-extrabold text-sm text-slate-900">Weekly Customer Mood Summary</h3>
          </div>
          <span className="text-[11px] text-slate-400 font-medium">Real-time AI Synthesis</span>
        </div>

        <p className="text-xs sm:text-sm text-slate-700 leading-relaxed bg-slate-50 p-4 rounded-2xl border border-slate-200/80">
          {insights?.summary_text || (overview?.total_mentions > 0 
            ? `Customer satisfaction for ${activeBrand?.name || 'your business'} is currently being synthesized from ${overview.total_mentions} reviews.`
            : 'No customer reviews have been uploaded yet. Upload reviews or connect Google Places to automatically generate your weekly customer mood summary.')}
        </p>

        {/* Quick Actions Row */}
        <div className="pt-2 flex items-center space-x-2.5 flex-wrap gap-2">
          <button
            onClick={() => navigate('/social-listening')}
            className="px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-bold text-xs transition flex items-center space-x-1.5 shadow-2xs"
          >
            <MessageSquare className="w-3.5 h-3.5" />
            <span>Reply to Reviews</span>
          </button>

          <button
            onClick={() => navigate('/ask')}
            className="px-4 py-2 rounded-xl bg-indigo-50 hover:bg-indigo-100 text-indigo-700 font-bold text-xs transition flex items-center space-x-1.5 border border-indigo-200"
          >
            <Sparkles className="w-3.5 h-3.5 text-indigo-600" />
            <span>Ask AI Advisor</span>
          </button>

          <button
            onClick={() => navigate('/reports')}
            className="px-4 py-2 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold text-xs transition flex items-center space-x-1.5"
          >
            <FileText className="w-3.5 h-3.5" />
            <span>Download Weekly PDF</span>
          </button>
        </div>
      </div>
    </div>
  );
};

export default OwnerInsightsCard;
