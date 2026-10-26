import React from 'react';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts';

const SentimentPie = ({ positive = 0, neutral = 0, negative = 0, nss = 0 }) => {
  const total = positive + neutral + negative;

  if (total === 0) {
    return (
      <div className="h-56 flex flex-col items-center justify-center p-6 bg-slate-50 border border-dashed border-slate-200 rounded-2xl text-slate-400 text-xs text-center space-y-1 my-auto">
        <p className="font-semibold text-slate-600">No sentiment breakdown yet</p>
        <p className="text-[11px]">Upload customer reviews to view positive, neutral, and negative distribution.</p>
      </div>
    );
  }

  const data = [
    { name: 'Positive', value: positive, color: '#16A34A' },
    { name: 'Neutral', value: neutral, color: '#64748B' },
    { name: 'Negative', value: negative, color: '#DC2626' },
  ];

  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      const d = payload[0];
      const pct = round((d.value / total) * 100, 1);
      return (
        <div className="bg-white px-3 py-2 rounded-xl text-xs shadow-md border border-slate-200">
          <div className="font-bold flex items-center space-x-1.5" style={{ color: d.payload.color }}>
            <span className="w-2 h-2 rounded-full" style={{ backgroundColor: d.payload.color }}></span>
            <span>{d.name}</span>
          </div>
          <div className="text-slate-900 mt-1 font-semibold">
            <span>{d.value.toLocaleString()}</span> mentions ({pct}%)
          </div>
        </div>
      );
    }
    return null;
  };

  function round(val, dec = 1) {
    return Number(Math.round(val + 'e' + dec) + 'e-' + dec);
  }

  return (
    <div className="w-full flex flex-col items-center justify-center">
      <div className="relative w-full h-56 flex items-center justify-center">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Tooltip content={<CustomTooltip />} />
            <Pie
              data={data}
              cx="50%"
              cy="50%"
              innerRadius={68}
              outerRadius={92}
              paddingAngle={4}
              dataKey="value"
              stroke="none"
            >
              {data.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.color} />
              ))}
            </Pie>
          </PieChart>
        </ResponsiveContainer>

        {/* Center NSS Metric */}
        <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
          <span className="text-[10px] uppercase font-bold text-slate-400 tracking-wider">Net Score</span>
          <span className={`text-2xl font-black ${nss >= 0 ? 'text-[#16A34A]' : 'text-[#DC2626]'}`}>
            {nss > 0 ? `+${nss}%` : `${nss}%`}
          </span>
          <span className="text-[9px] text-slate-500 font-medium">NSS Index</span>
        </div>
      </div>

      {/* Legend */}
      <div className="grid grid-cols-3 gap-2 w-full mt-2 pt-3 border-t border-slate-100 text-center text-xs">
        <div className="bg-emerald-50 p-2 rounded-xl border border-emerald-200">
          <div className="text-[#16A34A] font-bold">{positive.toLocaleString()}</div>
          <div className="text-[10px] text-slate-600 font-medium">Positive ({round((positive/total)*100)}%)</div>
        </div>
        <div className="bg-slate-50 p-2 rounded-xl border border-slate-200">
          <div className="text-slate-700 font-bold">{neutral.toLocaleString()}</div>
          <div className="text-[10px] text-slate-500 font-medium">Neutral ({round((neutral/total)*100)}%)</div>
        </div>
        <div className="bg-red-50 p-2 rounded-xl border border-red-200">
          <div className="text-[#DC2626] font-bold">{negative.toLocaleString()}</div>
          <div className="text-[10px] text-slate-600 font-medium">Negative ({round((negative/total)*100)}%)</div>
        </div>
      </div>
    </div>
  );
};

export default SentimentPie;
