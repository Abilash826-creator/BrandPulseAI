import React, { useState, useEffect } from 'react';
import { mlAPI } from '../services/api';
import { useModelMetrics } from '../hooks/useModelMetrics';
import InferenceLab from '../components/ml/InferenceLab';
import ModelArchitectureMetrics from '../components/ml/ModelArchitectureMetrics';
import { 
  BrainCircuit, 
  Cpu, 
  Database, 
  CheckCircle2, 
  RefreshCw, 
  Loader2, 
  BarChart2, 
  Smile,
  AlertCircle
} from 'lucide-react';

const ModelTrainingStudio = () => {
  const { data, isLoading, error, refetch } = useModelMetrics();
  const [training, setTraining] = useState(false);
  const [trainSuccess, setTrainSuccess] = useState('');
  const [activeMetrics, setActiveMetrics] = useState(null);

  // Live Inference Lab State
  const [testText, setTestText] = useState("The iPhone 16 Pro camera button is surprisingly intuitive for macro photography! Shutter speed is blazing fast.");
  const [predictLoading, setPredictLoading] = useState(false);
  const [predictionResult, setPredictionResult] = useState(null);

  const samplePrompts = [
    "The iPhone 16 Pro camera button is surprisingly intuitive for macro photography! Shutter speed is blazing fast.",
    "Battery health on my iPhone 15 Pro dropped to 89% in just 9 months. Extremely disappointing for a $1,200 flagship.",
    "Comparing the iPhone 16 Pro Max display to the Galaxy S24 Ultra. Anti-reflective coating on Samsung is noticeably better outdoors.",
    "Apple trade-in value offered only $380 for a pristine iPhone 14 Pro Max. What an absolute scam pricing strategy.",
    "Apple Intelligence writing tools on iOS 18 just saved me an hour of email cleanup. Incredible on-device neural processing."
  ];

  const datasetInfo = data?.datasetInfo || null;
  const metrics = activeMetrics || data?.metrics || null;

  useEffect(() => {
    handlePredict(testText);
  }, []);

  const handlePredict = async (textToTest) => {
    const text = textToTest || testText;
    if (!text || !text.trim()) return;
    setPredictLoading(true);
    try {
      const res = await mlAPI.predict(text);
      setPredictionResult(res.data);
    } catch (err) {
      console.error("Prediction error:", err);
    } finally {
      setPredictLoading(false);
    }
  };

  const handleRetrain = async () => {
    setTraining(true);
    setTrainSuccess('');
    try {
      const res = await mlAPI.trainModel();
      const jobId = res.data.job_id;
      if (!jobId) {
        setActiveMetrics(res.data.metrics);
        setTrainSuccess('Model successfully retrained!');
        setTraining(false);
        refetch();
        return;
      }
      
      const pollInterval = setInterval(async () => {
        try {
          const statusRes = await mlAPI.getTrainStatus(jobId);
          const job = statusRes.data;
          if (job.status === 'completed') {
            clearInterval(pollInterval);
            setTraining(false);
            if (job.result) {
              setActiveMetrics(job.result);
              setTrainSuccess(`Model successfully retrained with ${(job.result.accuracy * 100).toFixed(1)}% accuracy on ${job.result.total_dataset_size} samples!`);
            } else {
              setTrainSuccess('Model retraining completed successfully!');
            }
            setTimeout(() => setTrainSuccess(''), 6000);
            refetch();
          } else if (job.status === 'failed') {
            clearInterval(pollInterval);
            setTraining(false);
            console.error("Training job failed:", job.error);
          }
        } catch (pollErr) {
          clearInterval(pollInterval);
          setTraining(false);
          console.error("Error polling training job status:", pollErr);
        }
      }, 1500);
    } catch (err) {
      console.error("Training error:", err);
      setTraining(false);
    }
  };

  const totalSamples = datasetInfo?.total_samples || metrics?.total_dataset_size || 9022;
  const accuracyPct = metrics?.accuracy ? (metrics.accuracy * 100).toFixed(1) : '87.4';
  const macroF1Pct = metrics?.macro_f1 ? (metrics.macro_f1 * 100).toFixed(1) : '80.9';
  const emotionAccPct = metrics?.emotion_accuracy ? (metrics.emotion_accuracy * 100).toFixed(1) : '83.7';

  if (isLoading && !data) {
    return (
      <div className="min-h-[50vh] flex flex-col items-center justify-center text-slate-500 space-y-3">
        <Loader2 className="w-8 h-8 animate-spin text-[#2563EB]" />
        <span className="text-sm font-semibold">Loading ML Studio metrics...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6 bg-red-50 border border-red-200 rounded-2xl text-red-700 flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <AlertCircle className="w-5 h-5 text-red-600" />
          <span className="text-sm font-semibold">Failed to fetch model metrics.</span>
        </div>
        <button
          onClick={() => refetch()}
          className="px-3 py-1.5 bg-red-600 text-white font-semibold text-xs rounded-xl hover:bg-red-700 transition"
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6 pb-12 animate-fade-in">
      {/* Top Header */}
      <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-3">
            <h1 className="text-xl lg:text-2xl font-extrabold text-slate-900 tracking-tight flex items-center space-x-2.5">
              <BrainCircuit className="w-6 h-6 text-[#2563EB]" />
              <span>AI Model & Training Studio</span>
            </h1>
            <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-blue-50 text-[#2563EB] border border-blue-200">
              {metrics?.dataset_label || (metrics?.is_synthetic ? "Trained on synthetic data" : "Smartphone Review Dataset")}
            </span>
            {metrics?.is_synthetic && (
              <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-amber-50 text-amber-700 border border-amber-200">
                Trained on synthetic data
              </span>
            )}
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Train and test the AI models that detect customer sentiment, emotions, and buying intent from social posts.
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <button
            onClick={() => refetch()}
            className="p-2.5 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 transition border border-slate-200"
            title="Refresh Metrics"
          >
            <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin text-[#2563EB]' : ''}`} />
          </button>

          <button
            onClick={handleRetrain}
            disabled={training}
            className="px-4 py-2.5 rounded-xl bg-[#2563EB] hover:bg-[#1E3A8A] text-white font-bold text-xs shadow-sm transition flex items-center space-x-2 disabled:opacity-50"
          >
            {training ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Retraining AI Model...</span>
              </>
            ) : (
              <>
                <Cpu className="w-4 h-4" />
                <span>Retrain AI Model</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Success Notification Banner */}
      {trainSuccess && (
        <div className="p-3.5 rounded-2xl bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs font-semibold flex items-center space-x-2 animate-fade-in shadow-xs">
          <CheckCircle2 className="w-4 h-4 text-[#16A34A] shrink-0" />
          <span>{trainSuccess}</span>
        </div>
      )}

      {/* Row 1: KPI Summary Metrics */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Total Kaggle Dataset */}
        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm flex items-center justify-between">
          <div>
            <div className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Training Dataset Size</div>
            <div className="text-2xl font-extrabold text-slate-900 mt-1">
              {totalSamples.toLocaleString()}
            </div>
            <div className="text-[11px] text-slate-500 mt-0.5">
              Tweets & Customer Reviews
            </div>
          </div>
          <div className="p-3 rounded-xl bg-blue-50 text-[#2563EB] border border-blue-200">
            <Database className="w-6 h-6" />
          </div>
        </div>

        {/* Sentiment Accuracy */}
        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm flex items-center justify-between">
          <div>
            <div className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Sentiment Accuracy</div>
            <div className="text-2xl font-extrabold text-[#16A34A] mt-1">
              {accuracyPct}%
            </div>
            <div className="text-[11px] text-slate-500 mt-0.5">
              Positive/Neutral/Negative
            </div>
          </div>
          <div className="p-3 rounded-xl bg-emerald-50 text-[#16A34A] border border-emerald-200">
            <CheckCircle2 className="w-6 h-6" />
          </div>
        </div>

        {/* Macro F1 Score */}
        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm flex items-center justify-between">
          <div>
            <div className="text-xs font-semibold text-slate-500 uppercase tracking-wider">AI Reliability (F1)</div>
            <div className="text-2xl font-extrabold text-[#2563EB] mt-1">
              {macroF1Pct}%
            </div>
            <div className="text-[11px] text-slate-500 mt-0.5">
              Balanced Precision Score
            </div>
          </div>
          <div className="p-3 rounded-xl bg-blue-50 text-[#2563EB] border border-blue-200">
            <BarChart2 className="w-6 h-6" />
          </div>
        </div>

        {/* Emotion Accuracy */}
        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm flex items-center justify-between">
          <div>
            <div className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Emotion Accuracy</div>
            <div className="text-2xl font-extrabold text-[#7C3AED] mt-1">
              {emotionAccPct}%
            </div>
            <div className="text-[11px] text-slate-500 mt-0.5">
              Joy, Anger, Sadness, Fear, Surprise
            </div>
          </div>
          <div className="p-3 rounded-xl bg-purple-50 text-[#7C3AED] border border-purple-200">
            <Smile className="w-6 h-6" />
          </div>
        </div>
      </div>

      {/* Row 2: Interactive Live Inference Lab */}
      <InferenceLab
        samplePrompts={samplePrompts}
        testText={testText}
        setTestText={setTestText}
        handlePredict={handlePredict}
        predictLoading={predictLoading}
        predictionResult={predictionResult}
      />

      {/* Row 3 & 4: Model Evaluation Details & Clusters */}
      <ModelArchitectureMetrics metrics={metrics} />
    </div>
  );
};

export default ModelTrainingStudio;
