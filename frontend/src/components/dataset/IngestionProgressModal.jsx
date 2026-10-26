import React from 'react';
import { Cpu, CheckCircle2, Loader2, ArrowRight, ThumbsUp, ThumbsDown } from 'lucide-react';

const IngestionProgressModal = ({
  processing,
  pipelineStep,
  ingestResult,
  navigate
}) => {
  return (
    <>
      {/* Real-time Ingestion Progress Banner */}
      {processing && (
        <div className="bg-white p-6 rounded-2xl border-2 border-blue-500 shadow-lg space-y-4 animate-fade-in">
          <div className="flex items-center space-x-3">
            <div className="p-2.5 rounded-xl bg-blue-50 text-[#2563EB] animate-pulse">
              <Cpu className="w-6 h-6" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-slate-900 tracking-tight">
                AI Ingestion & Model Enrichment Pipeline Active
              </h3>
              <p className="text-xs text-slate-500 mt-0.5">
                Executing 5-stage deep NLP pipeline: parsing file, extracting topics, classifying sentiment/emotion, and generating MongoDB summaries.
              </p>
            </div>
          </div>

          {/* 5-Stage Step Indicators */}
          <div className="grid grid-cols-1 sm:grid-cols-5 gap-2 pt-2">
            {[
              { num: 1, label: "File Ingestion & Tokenizing" },
              { num: 2, label: "Entity Disambiguation" },
              { num: 3, label: "ML Sentiment & Emotion" },
              { num: 4, label: "KMeans Topic Clustering" },
              { num: 5, label: "Synthesizing Summary" }
            ].map((step) => {
              const isCompleted = pipelineStep > step.num;
              const isCurrent = pipelineStep === step.num;
              return (
                <div
                  key={step.num}
                  className={`p-3 rounded-xl border text-xs transition flex flex-col justify-between ${
                    isCompleted
                      ? 'bg-emerald-50 border-emerald-200 text-[#16A34A]'
                      : isCurrent
                      ? 'bg-blue-50 border-blue-300 text-[#2563EB] ring-2 ring-blue-200'
                      : 'bg-slate-50 border-slate-200 text-slate-400'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="font-mono text-[10px] font-bold">STAGE 0{step.num}</span>
                    {isCompleted && <CheckCircle2 className="w-3.5 h-3.5 text-[#16A34A]" />}
                    {isCurrent && <Loader2 className="w-3.5 h-3.5 animate-spin text-[#2563EB]" />}
                  </div>
                  <span className="font-bold mt-2 text-[11px] leading-tight">{step.label}</span>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Post-Ingestion Analysis Summary */}
      {ingestResult && !processing && (
        <div className="bg-white p-6 rounded-2xl border-2 border-emerald-400 shadow-md space-y-5 animate-fade-in">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-100 pb-4">
            <div className="flex items-center space-x-3">
              <div className="p-3 rounded-xl bg-emerald-50 text-[#16A34A] border border-emerald-200">
                <CheckCircle2 className="w-6 h-6" />
              </div>
              <div>
                <div className="flex items-center space-x-2">
                  <h3 className="text-base font-extrabold text-slate-900 tracking-tight">
                    Dataset Successfully Ingested & Analyzed!
                  </h3>
                  <span className="px-2.5 py-0.5 rounded-full bg-emerald-100 text-[#16A34A] text-xs font-bold">
                    100% Synced
                  </span>
                </div>
                <p className="text-xs text-slate-500 mt-0.5">
                  All <strong className="text-slate-800">{ingestResult.total_records_processed} mentions</strong> processed into <strong>{ingestResult.brand_name}</strong> dashboard profile.
                </p>
              </div>
            </div>

            <button
              onClick={() => navigate('/')}
              className="px-5 py-2.5 rounded-xl bg-[#2563EB] hover:bg-[#1E3A8A] text-white font-bold text-xs shadow-sm transition flex items-center space-x-2"
            >
              <span>🚀 Open Updated Dashboard</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>

          {/* 4 Summary Stats */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 text-xs">
            <div className="p-4 rounded-xl bg-emerald-50/40 border border-emerald-200/60">
              <span className="text-[11px] font-semibold text-emerald-800 uppercase block">Net Sentiment Score (NSS)</span>
              <span className="text-2xl font-extrabold text-[#16A34A] mt-1 block">
                {ingestResult.net_sentiment_score > 0 ? `+${ingestResult.net_sentiment_score}%` : `${ingestResult.net_sentiment_score}%`}
              </span>
              <span className="text-[10px] text-emerald-600">Calculated across dataset</span>
            </div>

            <div className="p-4 rounded-xl bg-blue-50/40 border border-blue-200/60">
              <span className="text-[11px] font-semibold text-[#2563EB] uppercase block">Records Ingested</span>
              <span className="text-2xl font-extrabold text-[#2563EB] mt-1 block">
                {ingestResult.total_records_processed}
              </span>
              <span className="text-[10px] text-blue-500">Stored in db.mentions</span>
            </div>

            <div className="p-4 rounded-xl bg-purple-50/40 border border-purple-200/60">
              <span className="text-[11px] font-semibold text-[#7C3AED] uppercase block">Registered Product</span>
              <span className="text-lg font-bold text-[#7C3AED] mt-1 block truncate" title={ingestResult.primary_product}>
                {ingestResult.primary_product}
              </span>
              <span className="text-[10px] text-purple-500">Added to tracked products</span>
            </div>

            <div className="p-4 rounded-xl bg-slate-50 border border-slate-200">
              <span className="text-[11px] font-semibold text-slate-600 uppercase block">Polarity Split</span>
              <div className="flex items-center space-x-2 mt-2 font-mono text-[11px]">
                <span className="text-[#16A34A] font-bold">{ingestResult.positive_count} Pos</span>
                <span>•</span>
                <span className="text-slate-500 font-bold">{ingestResult.neutral_count} Neu</span>
                <span>•</span>
                <span className="text-[#DC2626] font-bold">{ingestResult.negative_count} Neg</span>
              </div>
            </div>
          </div>

          {/* Top Praise & Friction Dimensions */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs pt-1">
            <div className="p-4 rounded-xl bg-emerald-50/30 border border-emerald-200/60 space-y-2">
              <div className="flex items-center space-x-1.5 font-bold text-[#16A34A]">
                <ThumbsUp className="w-3.5 h-3.5" />
                <span>Extracted Product Praise Dimensions</span>
              </div>
              <div className="space-y-1.5 pt-1">
                {ingestResult.top_aspect_praise?.slice(0, 4).map((item, idx) => (
                  <div key={idx} className="flex items-center justify-between text-[11px]">
                    <span className="text-slate-700 font-medium">✨ {item.aspect}</span>
                    <span className="px-2 py-0.5 rounded-md bg-emerald-100 text-[#16A34A] font-bold text-[10px]">
                      {item.count} positive mentions
                    </span>
                  </div>
                ))}
              </div>
            </div>

            <div className="p-4 rounded-xl bg-red-50/30 border border-red-200/60 space-y-2">
              <div className="flex items-center space-x-1.5 font-bold text-[#DC2626]">
                <ThumbsDown className="w-3.5 h-3.5" />
                <span>Extracted Product Friction Points</span>
              </div>
              <div className="space-y-1.5 pt-1">
                {ingestResult.top_aspect_friction?.slice(0, 4).map((item, idx) => (
                  <div key={idx} className="flex items-center justify-between text-[11px]">
                    <span className="text-slate-700 font-medium">⚠️ {item.aspect}</span>
                    <span className="px-2 py-0.5 rounded-md bg-red-100 text-[#DC2626] font-bold text-[10px]">
                      {item.count} complaints
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Navigation Action Buttons */}
          <div className="flex flex-wrap gap-2.5 pt-2 border-t border-slate-100">
            <button
              onClick={() => navigate('/')}
              className="px-4 py-2 rounded-xl bg-[#2563EB] hover:bg-[#1E3A8A] text-white font-bold text-xs shadow-sm transition flex items-center space-x-1.5"
            >
              <span>View Main Dashboard</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>

            <button
              onClick={() => navigate('/sentiment-analytics')}
              className="px-4 py-2 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold text-xs transition flex items-center space-x-1.5 border border-slate-200"
            >
              <span>Explore Sentiment & Emotions</span>
            </button>

            <button
              onClick={() => navigate('/summaries')}
              className="px-4 py-2 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold text-xs transition flex items-center space-x-1.5 border border-slate-200"
            >
              <span>View Monitored Summaries in MongoDB</span>
            </button>
          </div>
        </div>
      )}
    </>
  );
};

export default IngestionProgressModal;
