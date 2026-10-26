import React, { useState, useEffect } from 'react';
import { useBrand } from '../context/BrandContext';
import { analyticsAPI } from '../services/api';
import SentimentPie from '../components/charts/SentimentPie';
import TrendLine from '../components/charts/TrendLine';
import EmotionRadar from '../components/charts/EmotionRadar';
import ForecastChart from '../components/charts/ForecastChart';
import { 
  Sparkles, 
  TrendingUp, 
  PieChart, 
  Smile, 
  RefreshCw, 
  Layers 
} from 'lucide-react';

const SentimentAnalytics = () => {
  const { activeBrand } = useBrand();

  const [overview, setOverview] = useState(null);
  const [trends, setTrends] = useState([]);
  const [emotions, setEmotions] = useState([]);
  const [intents, setIntents] = useState([]);
  const [forecast, setForecast] = useState([]);
  const [loading, setLoading] = useState(true);
  const [timeRange, setTimeRange] = useState('7d');

  const fetchAnalytics = async () => {
    if (!activeBrand) return;
    setLoading(true);
    try {
      const [overviewRes, trendsRes, emotionsRes, intentsRes, forecastRes] = await Promise.all([
        analyticsAPI.getOverview(activeBrand.id, timeRange),
        analyticsAPI.getTrends(activeBrand.id, timeRange),
        analyticsAPI.getEmotions(activeBrand.id),
        analyticsAPI.getIntent(activeBrand.id),
        analyticsAPI.getForecast(activeBrand.id)
      ]);

      setOverview(overviewRes.data);
      setTrends(trendsRes.data);
      setEmotions(emotionsRes.data);
      setIntents(intentsRes.data);
      setForecast(forecastRes.data?.forecast || []);
    } catch (err) {
      console.error("Analytics fetch error:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAnalytics();
  }, [activeBrand, timeRange]);

  return (
    <div className="space-y-6 pb-12 animate-fade-in">
      {/* Header */}
      <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-3">
            <h1 className="text-xl lg:text-2xl font-extrabold text-slate-900 tracking-tight">
              Customer Mood & Emotions
            </h1>
            <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-emerald-50 text-[#16A34A] border border-emerald-200">
              AI Mood Analysis
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Breakdown of positive vs negative feedback, customer emotions, purchase intent, and 3-day future forecast
          </p>
        </div>

        {/* Time Selector */}
        <div className="flex items-center space-x-2.5">
          <div className="bg-slate-100 p-1 rounded-xl border border-slate-200 flex items-center space-x-1 text-xs">
            {['24h', '7d', '30d'].map((range) => (
              <button
                key={range}
                onClick={() => setTimeRange(range)}
                className={`px-3 py-1 rounded-lg font-semibold transition ${
                  timeRange === range
                    ? 'bg-[#2563EB] text-white shadow-sm'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                {range.toUpperCase()}
              </button>
            ))}
          </div>

          <button
            onClick={fetchAnalytics}
            className="p-2 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 transition border border-slate-200"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin text-[#2563EB]' : ''}`} />
          </button>
        </div>
      </div>

      {/* Row 1: Net Sentiment Polarity & Time-Series Trend */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4">
          <div>
            <h3 className="text-sm font-bold text-slate-900 tracking-tight flex items-center space-x-2">
              <PieChart className="w-4 h-4 text-[#2563EB]" />
              <span>Positive vs Negative Breakdown</span>
            </h3>
            <p className="text-xs text-slate-500 mt-0.5">Overall customer mood distribution</p>
          </div>
          <SentimentPie
            positive={overview?.positive_count || 0}
            neutral={overview?.neutral_count || 0}
            negative={overview?.negative_count || 0}
            nss={overview?.net_sentiment_score || 0}
          />
        </div>

        <div className="lg:col-span-2 bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm font-bold text-slate-900 tracking-tight flex items-center space-x-2">
                <TrendingUp className="w-4 h-4 text-[#16A34A]" />
                <span>Customer Mood Over Time</span>
              </h3>
              <p className="text-xs text-slate-500 mt-0.5">Daily volume of positive, neutral, and negative posts</p>
            </div>
            <div className="text-xs font-mono font-semibold text-[#16A34A] bg-emerald-50 px-2.5 py-1 rounded-xl border border-emerald-200">
              Happiness Score: {overview ? (overview.net_sentiment_score > 0 ? `+${overview.net_sentiment_score}%` : `${overview.net_sentiment_score}%`) : '+0%'}
            </div>
          </div>
          <TrendLine data={trends} height={280} />
        </div>
      </div>

      {/* Row 2: Multi-Class Emotion Radar & User Intent Distribution */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4">
          <div>
            <h3 className="text-sm font-bold text-slate-900 tracking-tight flex items-center space-x-2">
              <Smile className="w-4 h-4 text-[#2563EB]" />
              <span>Customer Emotions (Joy, Anger, Sadness, etc.)</span>
            </h3>
            <p className="text-xs text-slate-500 mt-0.5">Emotional tone detected across all customer messages</p>
          </div>
          <EmotionRadar data={emotions} />
        </div>

        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4">
          <div>
            <h3 className="text-sm font-bold text-slate-900 tracking-tight flex items-center space-x-2">
              <Layers className="w-4 h-4 text-[#7C3AED]" />
              <span>Why Customers Are Posting</span>
            </h3>
            <p className="text-xs text-slate-500 mt-0.5">Separated into Complaints, Questions, Buying Interest, and Praise</p>
          </div>

          <div className="space-y-3 pt-2">
            {intents.map((item) => (
              <div key={item.intent} className="space-y-1">
                <div className="flex items-center justify-between text-xs">
                  <span className="font-semibold text-slate-800">{item.label}</span>
                  <span className="font-mono text-slate-500">
                    <strong className="text-slate-900">{item.count}</strong> ({item.percentage}%)
                  </span>
                </div>
                <div className="h-2 w-full bg-slate-100 rounded-full overflow-hidden">
                  <div
                    className="h-full rounded-full transition-all duration-500"
                    style={{ width: `${item.percentage}%`, backgroundColor: item.color }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Row 3: 72-Hour AI Trend & Volume Forecast */}
      <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-sm font-bold text-slate-900 tracking-tight flex items-center space-x-2">
              <Sparkles className="w-4 h-4 text-[#7C3AED]" />
              <span>3-Day Future Forecast (Next 72 Hours)</span>
            </h3>
            <p className="text-xs text-slate-500 mt-0.5">
              AI forecast predicting upcoming post volume and customer satisfaction
            </p>
          </div>
        </div>

        <ForecastChart data={forecast} height={240} />
      </div>
    </div>
  );
};

export default SentimentAnalytics;
