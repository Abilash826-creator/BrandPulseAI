import React from 'react';
import { Zap, Send, Loader2, Tag } from 'lucide-react';

const InferenceLab = ({
  samplePrompts,
  testText,
  setTestText,
  handlePredict,
  predictLoading,
  predictionResult
}) => {
  return (
    <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-5">
      <div>
        <h3 className="text-sm font-bold text-slate-900 tracking-tight flex items-center space-x-2">
          <Zap className="w-4 h-4 text-[#2563EB]" />
          <span>Test Any Text with AI</span>
        </h3>
        <p className="text-xs text-slate-500 mt-0.5">
          Type or paste any customer review or post to see how the AI evaluates it.
        </p>
      </div>

      {/* Quick Sample Chips */}
      <div className="space-y-1.5">
        <span className="text-[11px] font-semibold text-slate-500">Try an Example:</span>
        <div className="flex flex-wrap gap-2">
          {samplePrompts.map((prompt, idx) => (
            <button
              key={idx}
              onClick={() => {
                setTestText(prompt);
                handlePredict(prompt);
              }}
              className="text-[11px] px-3 py-1.5 rounded-xl bg-slate-50 hover:bg-blue-50 hover:border-blue-300 border border-slate-200 text-slate-700 text-left transition max-w-md truncate"
              title={prompt}
            >
              {prompt}
            </button>
          ))}
        </div>
      </div>

      {/* Inference Input & Prediction Output Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 pt-2">
        {/* Input Box */}
        <div className="lg:col-span-7 space-y-3">
          <label className="text-xs font-semibold text-slate-700 block">Customer Post / Review Text:</label>
          <textarea
            rows={4}
            value={testText}
            onChange={(e) => setTestText(e.target.value)}
            className="w-full bg-white border border-slate-200 rounded-xl p-3 text-xs text-slate-900 focus:outline-none focus:border-blue-600 focus:ring-1 focus:ring-blue-600"
            placeholder="Type or paste customer post..."
          />
          <div className="flex justify-end">
            <button
              onClick={() => handlePredict(testText)}
              disabled={predictLoading}
              className="px-5 py-2.5 rounded-xl bg-[#2563EB] hover:bg-[#1E3A8A] text-white font-bold text-xs shadow-sm transition flex items-center space-x-2 disabled:opacity-50"
            >
              {predictLoading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Send className="w-3.5 h-3.5" />}
              <span>Evaluate with AI</span>
            </button>
          </div>
        </div>

        {/* Real-Time Prediction Results Box */}
        <div className="lg:col-span-5 bg-slate-50 p-5 rounded-2xl border border-slate-200 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-200 pb-3">
            <span className="text-xs font-bold text-slate-900 uppercase tracking-wider">AI Evaluation Result</span>
            {predictionResult && (
              <span className={`px-2.5 py-0.5 rounded-full text-xs font-bold uppercase ${
                predictionResult.sentiment === 'positive' ? 'bg-emerald-100 text-[#16A34A] border border-emerald-200' :
                predictionResult.sentiment === 'negative' ? 'bg-red-100 text-[#DC2626] border border-red-200' :
                'bg-slate-200 text-slate-800 border border-slate-300'
              }`}>
                {predictionResult.sentiment} Mood
              </span>
            )}
          </div>

          {predictionResult ? (
            <div className="space-y-3.5 text-xs">
              {/* Sentiment Probability Bars */}
              <div className="space-y-2">
                <div className="flex items-center justify-between text-[11px]">
                  <span className="font-semibold text-slate-600">Model Posterior Probabilities:</span>
                  <span className="font-mono text-slate-500">Confidence: {(predictionResult.confidence * 100).toFixed(1)}%</span>
                </div>

                <div className="space-y-1.5 font-mono text-[11px]">
                  <div>
                    <div className="flex justify-between text-slate-700 pb-0.5">
                      <span>Positive Advocacy</span>
                      <span className="font-bold text-[#16A34A]">{(predictionResult.probabilities.positive * 100).toFixed(1)}%</span>
                    </div>
                    <div className="w-full bg-slate-200 h-2 rounded-full overflow-hidden">
                      <div className="bg-[#16A34A] h-full rounded-full transition-all duration-300" style={{ width: `${predictionResult.probabilities.positive * 100}%` }} />
                    </div>
                  </div>

                  <div>
                    <div className="flex justify-between text-slate-700 pb-0.5">
                      <span>Neutral / Information</span>
                      <span className="font-bold text-slate-600">{(predictionResult.probabilities.neutral * 100).toFixed(1)}%</span>
                    </div>
                    <div className="w-full bg-slate-200 h-2 rounded-full overflow-hidden">
                      <div className="bg-slate-400 h-full rounded-full transition-all duration-300" style={{ width: `${predictionResult.probabilities.neutral * 100}%` }} />
                    </div>
                  </div>

                  <div>
                    <div className="flex justify-between text-slate-700 pb-0.5">
                      <span>Negative / Risk</span>
                      <span className="font-bold text-[#DC2626]">{(predictionResult.probabilities.negative * 100).toFixed(1)}%</span>
                    </div>
                    <div className="w-full bg-slate-200 h-2 rounded-full overflow-hidden">
                      <div className="bg-[#DC2626] h-full rounded-full transition-all duration-300" style={{ width: `${predictionResult.probabilities.negative * 100}%` }} />
                    </div>
                  </div>
                </div>
              </div>

              {/* Detected Emotion & Intent Tags */}
              <div className="pt-2 border-t border-slate-200 grid grid-cols-2 gap-2 text-[11px]">
                <div className="p-2.5 rounded-xl bg-white border border-slate-200">
                  <span className="text-slate-500 block mb-0.5">Detected Emotion</span>
                  <span className="font-bold text-[#7C3AED] capitalize flex items-center space-x-1">
                    <span>✨</span>
                    <span>{predictionResult.emotion || 'Joy'}</span>
                  </span>
                </div>

                <div className="p-2.5 rounded-xl bg-white border border-slate-200">
                  <span className="text-slate-500 block mb-0.5">Customer Intent</span>
                  <span className="font-bold text-[#2563EB] capitalize flex items-center space-x-1">
                    <Tag className="w-3 h-3 text-[#2563EB]" />
                    <span>{predictionResult.intent || 'Praise'}</span>
                  </span>
                </div>
              </div>
            </div>
          ) : (
            <div className="py-8 text-center text-slate-400 text-xs">
              Enter text above and click Evaluate to inspect AI analysis.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default InferenceLab;
