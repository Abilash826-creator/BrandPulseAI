import React from 'react';
import { 
  AreaChart, 
  Area, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer 
} from 'recharts';
import { Sparkles } from 'lucide-react';

const ForecastChart = ({ data = [], height = 220 }) => {
  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      const d = payload[0].payload;
      return (
        <div className="bg-white p-3 rounded-xl border border-purple-200 text-xs shadow-md space-y-1">
          <div className="font-bold text-slate-900 flex items-center justify-between border-b border-slate-100 pb-1">
            <span className="flex items-center space-x-1 text-[#7C3AED]">
              <Sparkles className="w-3 h-3" />
              <span>{label} (AI Forecast)</span>
            </span>
          </div>
          <div className="text-slate-900 mt-1 font-semibold">
            Predicted Volume: <span className="text-[#2563EB]">{d.predicted_volume} mentions</span>
          </div>
          <div className="text-slate-500 text-[10px]">
            Confidence Range: {d.lower_bound} – {d.upper_bound} mentions
          </div>
          <div className="text-slate-500 text-[10px]">
            Predicted Sentiment: <span className={d.predicted_sentiment >= 0 ? 'text-[#16A34A] font-bold' : 'text-[#DC2626] font-bold'}>
              {d.predicted_sentiment > 0 ? `+${d.predicted_sentiment}` : d.predicted_sentiment}
            </span>
          </div>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="w-full space-y-2">
      <div className="flex items-center justify-between text-xs">
        <span className="text-slate-600 font-semibold flex items-center space-x-1.5">
          <Sparkles className="w-3.5 h-3.5 text-[#7C3AED]" />
          <span>Next 72-Hour Volume & Sentiment Projection</span>
        </span>
        <span className="text-[10px] font-mono font-semibold text-[#7C3AED] bg-purple-50 px-2 py-0.5 rounded-full border border-purple-200">
          95% Confidence Interval
        </span>
      </div>

      <div className="w-full" style={{ height }}>
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data} margin={{ top: 10, right: 10, left: -25, bottom: 0 }}>
            <defs>
              <linearGradient id="forecastGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#7C3AED" stopOpacity={0.25} />
                <stop offset="95%" stopColor="#7C3AED" stopOpacity={0.0} />
              </linearGradient>
              <linearGradient id="boundGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#2563EB" stopOpacity={0.10} />
                <stop offset="95%" stopColor="#2563EB" stopOpacity={0.01} />
              </linearGradient>
            </defs>

            <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" vertical={false} />
            <XAxis 
              dataKey="date" 
              stroke="#94A3B8" 
              fontSize={11} 
              tickLine={false} 
              axisLine={{ stroke: '#E2E8F0' }} 
            />
            <YAxis 
              stroke="#94A3B8" 
              fontSize={11} 
              tickLine={false} 
              axisLine={false} 
            />
            <Tooltip content={<CustomTooltip />} />

            <Area 
              type="monotone" 
              dataKey="upper_bound" 
              stroke="none" 
              fill="url(#boundGrad)" 
            />
            <Area 
              type="monotone" 
              dataKey="predicted_volume" 
              stroke="#7C3AED" 
              strokeWidth={2.5} 
              strokeDasharray="4 4"
              fill="url(#forecastGrad)" 
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

export default ForecastChart;
