import React from 'react';
import { 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  Tooltip, 
  ResponsiveContainer, 
  Cell 
} from 'recharts';
import { Smile, Flame, Frown, Sparkles, AlertCircle } from 'lucide-react';

const EmotionRadar = ({ data = [] }) => {
  if (!data || data.length === 0 || data.every(d => Number(d.value || 0) === 0)) {
    return (
      <div className="h-56 flex flex-col items-center justify-center p-6 bg-slate-50 border border-dashed border-slate-200 rounded-2xl text-slate-400 text-xs text-center space-y-1">
        <p className="font-semibold text-slate-600">No emotional signals detected yet</p>
        <p className="text-[11px]">Emotions (Joy, Anger, Surprise, etc.) will appear after customer reviews are analyzed.</p>
      </div>
    );
  }

  const icons = {
    Joy: Smile,
    Anger: Flame,
    Sadness: Frown,
    Surprise: Sparkles,
    Fear: AlertCircle,
  };

  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      const d = payload[0].payload;
      return (
        <div className="bg-white px-3 py-2 rounded-xl text-xs border border-slate-200 shadow-md">
          <div className="font-bold flex items-center space-x-1.5" style={{ color: d.color }}>
            <span>{d.emotion}</span>
          </div>
          <div className="text-slate-900 mt-1 font-semibold">
            <span className="font-bold text-sm">{d.value}%</span> of total emotional signal
          </div>
          <div className="text-[10px] text-slate-500">
            {d.count} dominant mentions
          </div>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="w-full space-y-3">
      <div className="h-48 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} layout="vertical" margin={{ top: 0, right: 20, left: 10, bottom: 0 }}>
            <XAxis type="number" domain={[0, 100]} hide />
            <YAxis 
              type="category" 
              dataKey="emotion" 
              stroke="#64748B" 
              fontSize={12} 
              tickLine={false} 
              axisLine={false}
              width={65}
            />
            <Tooltip content={<CustomTooltip />} />
            <Bar dataKey="value" radius={[0, 6, 6, 0]} barSize={16}>
              {data.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.color} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Emotion Cards */}
      <div className="grid grid-cols-5 gap-1.5 pt-2 border-t border-slate-100">
        {data.map((item) => {
          const Icon = icons[item.emotion] || Smile;
          return (
            <div 
              key={item.emotion}
              className="p-2 rounded-xl bg-slate-50 border border-slate-200 flex flex-col items-center text-center transition hover:bg-slate-100"
            >
              <Icon className="w-4 h-4 mb-1" style={{ color: item.color }} />
              <span className="text-[10px] text-slate-500 font-semibold">{item.emotion}</span>
              <span className="text-xs font-bold text-slate-900 mt-0.5">{item.value}%</span>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default EmotionRadar;
