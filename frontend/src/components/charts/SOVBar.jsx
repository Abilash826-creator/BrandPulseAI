import React from 'react';

const SOVBar = ({ data = [] }) => {
  if (!data || data.length === 0) {
    return (
      <div className="h-56 flex flex-col items-center justify-center p-6 bg-slate-50 border border-dashed border-slate-200 rounded-2xl text-slate-400 text-xs text-center space-y-1">
        <p className="font-semibold text-slate-600">No competitor share of voice data</p>
        <p className="text-[11px]">Add competitors in Brand Settings or ingest competitor data to view market share.</p>
      </div>
    );
  }

  return (
    <div className="space-y-4 w-full">
      {/* Multi-segment unified progress bar */}
      <div className="h-4 w-full rounded-full overflow-hidden flex bg-slate-100 p-0.5 border border-slate-200">
        {data.map((item, idx) => (
          <div
            key={idx}
            style={{ width: `${item.sov_percentage}%`, backgroundColor: item.color }}
            className="h-full first:rounded-l-full last:rounded-r-full transition-all duration-500 relative group"
            title={`${item.brand}: ${item.sov_percentage}%`}
          />
        ))}
      </div>

      {/* Individual Brand Breakdown Cards */}
      <div className="space-y-2.5">
        {data.map((item, idx) => (
          <div
            key={idx}
            className={`p-3 rounded-xl border flex items-center justify-between transition ${
              item.is_primary 
                ? 'bg-blue-50 border-blue-200' 
                : 'bg-slate-50 border-slate-200 hover:bg-slate-100'
            }`}
          >
            <div className="flex items-center space-x-3">
              <span className="w-3 h-3 rounded-full shrink-0" style={{ backgroundColor: item.color }} />
              <div>
                <div className="text-xs font-bold text-slate-900 flex items-center space-x-1.5">
                  <span>{item.brand}</span>
                  {item.is_primary && (
                    <span className="text-[9px] font-mono px-1.5 py-0.2 rounded bg-blue-100 text-[#2563EB] border border-blue-200 font-bold">
                      YOUR BRAND
                    </span>
                  )}
                </div>
                <div className="text-[11px] text-slate-500">
                  {item.volume.toLocaleString()} tracked mentions
                </div>
              </div>
            </div>

            <div className="text-right">
              <div className="text-sm font-extrabold text-slate-900 font-mono">{item.sov_percentage}%</div>
              <div className="text-[10px] text-slate-500">Market SOV</div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default SOVBar;
