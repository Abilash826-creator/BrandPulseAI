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

const TrendLine = ({ data = [], height = 280 }) => {
  if (!data || data.length === 0) {
    return (
      <div className="h-64 flex items-center justify-center text-xs text-slate-400">
        No time-series data available
      </div>
    );
  }

  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-white p-3 rounded-xl border border-slate-200 text-xs shadow-md space-y-1">
          <div className="font-bold text-slate-900 mb-1.5 border-b border-slate-100 pb-1 flex items-center justify-between">
            <span>{label}</span>
            {payload[0]?.payload?.net_sentiment !== undefined && (
              <span className={`text-[10px] px-1.5 py-0.5 rounded font-mono font-semibold ${
                payload[0].payload.net_sentiment >= 0 ? 'bg-emerald-50 text-[#16A34A]' : 'bg-red-50 text-[#DC2626]'
              }`}>
                NSS: {payload[0].payload.net_sentiment > 0 ? `+${payload[0].payload.net_sentiment}%` : `${payload[0].payload.net_sentiment}%`}
              </span>
            )}
          </div>
          {payload.map((item, idx) => (
            <div key={idx} className="flex items-center justify-between space-x-4">
              <span className="flex items-center space-x-1.5" style={{ color: item.color }}>
                <span className="w-2 h-2 rounded-full" style={{ backgroundColor: item.color }} />
                <span>{item.name}:</span>
              </span>
              <span className="font-bold text-slate-900 font-mono">{item.value}</span>
            </div>
          ))}
        </div>
      );
    }
    return null;
  };

  return (
    <div className="w-full" style={{ height }}>
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
          <defs>
            <linearGradient id="posGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#16A34A" stopOpacity={0.25} />
              <stop offset="95%" stopColor="#16A34A" stopOpacity={0.0} />
            </linearGradient>
            <linearGradient id="negGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#DC2626" stopOpacity={0.25} />
              <stop offset="95%" stopColor="#DC2626" stopOpacity={0.0} />
            </linearGradient>
            <linearGradient id="neuGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#64748B" stopOpacity={0.15} />
              <stop offset="95%" stopColor="#64748B" stopOpacity={0.0} />
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
            dataKey="positive" 
            name="Positive" 
            stroke="#16A34A" 
            strokeWidth={2}
            fillOpacity={1} 
            fill="url(#posGrad)" 
          />
          <Area 
            type="monotone" 
            dataKey="neutral" 
            name="Neutral" 
            stroke="#64748B" 
            strokeWidth={1.5}
            fillOpacity={1} 
            fill="url(#neuGrad)" 
          />
          <Area 
            type="monotone" 
            dataKey="negative" 
            name="Negative" 
            stroke="#DC2626" 
            strokeWidth={2}
            fillOpacity={1} 
            fill="url(#negGrad)" 
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
};

export default TrendLine;
