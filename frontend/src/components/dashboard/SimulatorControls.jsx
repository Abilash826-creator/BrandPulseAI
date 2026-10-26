import React, { useState } from 'react';
import { useBrand } from '../../context/BrandContext';
import { monitoringAPI, crisisAPI, brandsAPI } from '../../services/api';
import { 
  Play, 
  Flame, 
  Sparkles, 
  RotateCcw, 
  FlaskConical, 
  Send,
  Loader2,
  CheckCircle2
} from 'lucide-react';
import Modal from '../common/Modal';
import { SentimentBadge } from '../common/StatusBadge';

const SimulatorControls = ({ onFeedUpdated }) => {
  const { activeBrand, refreshBrands } = useBrand();
  const [nlpModalOpen, setNlpModalOpen] = useState(false);
  const [testText, setTestText] = useState('The filter coffee and ghee roast here are exceptional, but service was a bit delayed during evening rush hour.');
  const [nlpResult, setNlpResult] = useState(null);
  const [loadingNLP, setLoadingNLP] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);
  const [notification, setNotification] = useState(null);

  const showNotify = (msg) => {
    setNotification(msg);
    setTimeout(() => setNotification(null), 3500);
  };

  const handleSimulateOne = async (scenario) => {
    if (!activeBrand) return;
    setActionLoading(true);
    try {
      await monitoringAPI.simulateMention(activeBrand.id, scenario);
      showNotify(`Injected 1 ${scenario.replace('_', ' ')} mention!`);
      if (onFeedUpdated) onFeedUpdated();
    } catch (err) {
      console.error(err);
    } finally {
      setActionLoading(false);
    }
  };

  const handleTriggerCrisis = async () => {
    if (!activeBrand) return;
    setActionLoading(true);
    try {
      await crisisAPI.simulateCrisis(activeBrand.id, 'outage_disaster');
      showNotify('CRITICAL CRISIS ALERT TRIGGERED: Outage wave simulated!');
      if (onFeedUpdated) onFeedUpdated();
    } catch (err) {
      console.error(err);
    } finally {
      setActionLoading(false);
    }
  };

  const handleSeedHistory = async () => {
    if (!activeBrand) return;
    setActionLoading(true);
    try {
      await brandsAPI.seedHistory(activeBrand.id, 7);
      showNotify('Seeded 7 days of fresh historical mentions!');
      refreshBrands();
      if (onFeedUpdated) onFeedUpdated();
    } catch (err) {
      console.error(err);
    } finally {
      setActionLoading(false);
    }
  };

  const handleRunNLP = async () => {
    if (!testText.trim()) return;
    setLoadingNLP(true);
    try {
      const res = await monitoringAPI.testNLP(testText);
      setNlpResult(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoadingNLP(false);
    }
  };

  return (
    <>
      <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-sm flex flex-col md:flex-row items-center justify-between gap-4">
        {/* Left: Info */}
        <div className="flex items-center space-x-3">
          <div className="p-2 rounded-xl bg-blue-50 text-[#2563EB] border border-blue-200">
            <FlaskConical className="w-5 h-5" />
          </div>
          <div>
            <div className="text-xs font-bold text-slate-900 flex items-center space-x-2">
              <span>Live Testing Tools</span>
              {notification && (
                <span className="text-[11px] text-emerald-600 font-semibold animate-fade-in flex items-center space-x-1">
                  <CheckCircle2 className="w-3 h-3" />
                  <span>{notification}</span>
                </span>
              )}
            </div>
            <p className="text-[11px] text-slate-500">
              Generate sample customer posts to see real-time updates and alerts
            </p>
          </div>
        </div>

        {/* Right: Actions */}
        <div className="flex items-center space-x-2 flex-wrap gap-2">
          {/* Quick Scenario Injectors */}
          <button
            onClick={() => handleSimulateOne('normal')}
            disabled={actionLoading}
            className="px-3 py-1.5 rounded-xl bg-emerald-50 hover:bg-emerald-100 text-[#16A34A] border border-emerald-200 text-xs font-semibold flex items-center space-x-1.5 transition disabled:opacity-50"
            title="Add 1 sample positive/neutral post"
          >
            <Play className="w-3 h-3" />
            <span>+1 Normal Post</span>
          </button>

          <button
            onClick={handleTriggerCrisis}
            disabled={actionLoading}
            className="px-3 py-1.5 rounded-xl bg-red-50 hover:bg-red-100 text-[#DC2626] border border-red-200 text-xs font-semibold flex items-center space-x-1.5 transition disabled:opacity-50"
            title="Test a sudden wave of complaints"
          >
            <Flame className="w-3.5 h-3.5 text-[#DC2626]" />
            <span>Test Crisis Alert</span>
          </button>

          <button
            onClick={() => handleSimulateOne('viral_launch')}
            disabled={actionLoading}
            className="px-3 py-1.5 rounded-xl bg-blue-50 hover:bg-blue-100 text-[#2563EB] border border-blue-200 text-xs font-semibold flex items-center space-x-1.5 transition disabled:opacity-50"
            title="Simulate high-praise viral post"
          >
            <Sparkles className="w-3 h-3 text-[#2563EB]" />
            <span>+1 Viral Post</span>
          </button>

          <button
            onClick={handleSeedHistory}
            disabled={actionLoading}
            className="px-3 py-1.5 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 border border-slate-200 text-xs font-semibold flex items-center space-x-1.5 transition disabled:opacity-50"
            title="Generate 7 days of sample post history"
          >
            <RotateCcw className="w-3 h-3" />
            <span>Reset 7-Day Data</span>
          </button>

          <button
            onClick={() => {
              setNlpModalOpen(true);
              handleRunNLP();
            }}
            className="px-3.5 py-1.5 rounded-xl bg-[#2563EB] hover:bg-[#1E3A8A] text-white font-semibold text-xs shadow-sm transition flex items-center space-x-1.5"
          >
            <FlaskConical className="w-3.5 h-3.5" />
            <span>Test Text Analyzer</span>
          </button>
        </div>
      </div>

      {/* NLP Testing Modal */}
      <Modal
        isOpen={nlpModalOpen}
        onClose={() => setNlpModalOpen(false)}
        title="AI Text & Emotion Analyzer"
        maxWidth="max-w-2xl"
      >
        <div className="space-y-4 text-xs">
          <p className="text-slate-600">
            Paste any customer review, tweet, comment, or message to see how the AI detects customer mood, emotion, and purchase intent in real-time.
          </p>

          <div className="space-y-2">
            <textarea
              value={testText}
              onChange={(e) => setTestText(e.target.value)}
              rows={3}
              className="w-full bg-white border border-slate-200 rounded-xl p-3 text-slate-900 placeholder-slate-400 focus:outline-none focus:border-blue-600 focus:ring-1 focus:ring-blue-600 text-xs leading-relaxed"
              placeholder="Type or paste text to analyze..."
            />
            <div className="flex justify-end">
              <button
                onClick={handleRunNLP}
                disabled={loadingNLP || !testText.trim()}
                className="px-4 py-2 rounded-xl bg-[#2563EB] hover:bg-[#1E3A8A] text-white font-semibold flex items-center space-x-1.5 transition disabled:opacity-50 shadow-sm"
              >
                {loadingNLP ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Send className="w-3.5 h-3.5" />}
                <span>Analyze with AI</span>
              </button>
            </div>
          </div>

          {nlpResult && (
            <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-3 animate-fade-in">
              <div className="flex items-center justify-between border-b border-slate-200 pb-2">
                <div className="flex items-center space-x-2">
                  <span className="font-bold text-slate-900">Customer Mood:</span>
                  <SentimentBadge sentiment={nlpResult.sentiment} score={nlpResult.sentiment_score} />
                </div>
                <div className="font-mono text-slate-500">
                  Purpose: <span className="text-[#2563EB] font-bold uppercase">{nlpResult.intent}</span> ({Math.round(nlpResult.intent_confidence * 100)}% confidence)
                </div>
              </div>

              {/* Emotion Proportions */}
              <div>
                <span className="font-bold text-slate-900 block mb-1.5">Detected Emotions:</span>
                <div className="grid grid-cols-5 gap-2">
                  {Object.entries(nlpResult.emotions || {}).map(([emotion, val]) => (
                    <div key={emotion} className="p-2 rounded-lg bg-white border border-slate-200 text-center shadow-sm">
                      <div className="text-[10px] text-slate-500 uppercase font-semibold">{emotion}</div>
                      <div className="text-xs font-bold text-[#2563EB] mt-0.5">{Math.round(val * 100)}%</div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      </Modal>
    </>
  );
};

export default SimulatorControls;
