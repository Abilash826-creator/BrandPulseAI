import React from 'react';
import TrendLine from '../charts/TrendLine';
import SentimentPie from '../charts/SentimentPie';
import EmotionRadar from '../charts/EmotionRadar';
import SOVBar from '../charts/SOVBar';
import { TrendingUp } from 'lucide-react';

const DashboardCharts = ({ trends, overview, emotions, sovData }) => {
  return (
    <>
      {/* Charts Row 1: Net Sentiment Trend Area Chart + Donut */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm font-bold text-slate-900 tracking-tight flex items-center space-x-2">
                <TrendingUp className="w-4 h-4 text-[#16A34A]" />
                <span>Customer Mood & Post Volume Over Time</span>
              </h3>
              <p className="text-xs text-slate-500 mt-0.5">
                Daily breakdown of positive, neutral, and negative posts across all channels
              </p>
            </div>
            <div className="flex items-center space-x-3 text-[11px] font-semibold">
              <span className="flex items-center space-x-1 text-[#16A34A]">
                <span className="w-2 h-2 rounded-full bg-[#16A34A]" />
                <span>Positive</span>
              </span>
              <span className="flex items-center space-x-1 text-[#64748B]">
                <span className="w-2 h-2 rounded-full bg-[#64748B]" />
                <span>Neutral</span>
              </span>
              <span className="flex items-center space-x-1 text-[#DC2626]">
                <span className="w-2 h-2 rounded-full bg-[#DC2626]" />
                <span>Negative</span>
              </span>
            </div>
          </div>

          <TrendLine data={trends} height={280} />
        </div>

        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-3">
          <div>
            <h3 className="text-sm font-bold text-slate-900 tracking-tight">Positive vs Negative Breakdown</h3>
            <p className="text-xs text-slate-500 mt-0.5">Overall distribution of customer satisfaction</p>
          </div>
          <SentimentPie
            positive={overview?.positive_count || 0}
            neutral={overview?.neutral_count || 0}
            negative={overview?.negative_count || 0}
            nss={overview?.net_sentiment_score || 0}
          />
        </div>
      </div>

      {/* Row 2: Emotion Radar & Share of Voice */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4">
          <div>
            <h3 className="text-sm font-bold text-slate-900 tracking-tight">Customer Emotions Breakdown</h3>
            <p className="text-xs text-slate-500 mt-0.5">Joy, anger, sadness, surprise, and fear detected in posts</p>
          </div>
          <EmotionRadar data={emotions} />
        </div>

        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4">
          <div>
            <h3 className="text-sm font-bold text-slate-900 tracking-tight">Brand vs Competitor Share of Voice</h3>
            <p className="text-xs text-slate-500 mt-0.5">Comparison of total posts mentioning your brand vs competitors</p>
          </div>
          <SOVBar data={sovData} totalVolume={overview?.total_mentions || 0} />
        </div>
      </div>
    </>
  );
};

export default DashboardCharts;
