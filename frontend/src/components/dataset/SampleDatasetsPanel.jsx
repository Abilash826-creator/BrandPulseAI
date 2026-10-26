import React from 'react';
import { Database, Loader2, Sparkles } from 'lucide-react';

const SampleDatasetsPanel = ({
  samples,
  samplesLoading,
  processing,
  processingSampleId,
  handleIngestSample
}) => {
  if (!samplesLoading && (!samples || samples.length === 0)) {
    return null;
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <Database className="w-4 h-4 text-[#2563EB]" />
          <h2 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
            Standard Review Datasets & Templates
          </h2>
        </div>
        <span className="text-[11px] text-slate-500">Benchmark datasets for quick analysis</span>
      </div>

      {samplesLoading ? (
        <div className="py-8 flex items-center justify-center text-slate-400 text-xs space-x-2">
          <Loader2 className="w-4 h-4 animate-spin text-[#2563EB]" />
          <span>Loading dataset templates...</span>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {samples.map((sample) => (
            <div 
              key={sample.id}
              className="bg-white p-4.5 rounded-2xl border border-slate-200 hover:border-blue-300 shadow-sm transition space-y-3 flex flex-col justify-between"
            >
              <div>
                <div className="flex items-center justify-between">
                  <span className={`text-[10px] font-bold px-2 py-0.5 rounded-md uppercase ${
                    sample.format === 'csv' 
                      ? 'bg-emerald-50 text-[#16A34A] border border-emerald-200' 
                      : 'bg-purple-50 text-[#7C3AED] border border-purple-200'
                  }`}>
                    {sample.format.toUpperCase()}
                  </span>
                  <span className="text-[11px] font-mono text-slate-500">{sample.records_count} records</span>
                </div>

                <h3 className="font-bold text-slate-900 text-xs mt-2.5 leading-snug">
                  {sample.name}
                </h3>
                <p className="text-[11px] text-slate-500 mt-1 leading-relaxed">
                  {sample.description}
                </p>

                <div className="flex items-center space-x-2 mt-2.5 pt-2 border-t border-slate-100 text-[10px] text-slate-600">
                  <span>Product: <strong className="text-slate-800">{sample.primary_product}</strong></span>
                </div>
              </div>

              <button
                onClick={() => handleIngestSample(sample)}
                disabled={processing}
                className="w-full mt-2 py-2 px-3 rounded-xl bg-slate-900 hover:bg-[#2563EB] text-white text-xs font-bold transition flex items-center justify-center space-x-1.5 disabled:opacity-50"
              >
                {processing && processingSampleId === sample.id ? (
                  <>
                    <Loader2 className="w-3.5 h-3.5 animate-spin" />
                    <span>Analyzing Dataset...</span>
                  </>
                ) : (
                  <>
                    <Sparkles className="w-3.5 h-3.5" />
                    <span>Load {sample.name.split(' ')[0]} Dataset</span>
                  </>
                )}
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default SampleDatasetsPanel;
