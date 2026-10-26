import React, { useState } from 'react';
import { ArrowUpRight, ArrowDownRight, Minus, HelpCircle } from 'lucide-react';

const KPICard = ({
  title,
  value,
  trend,
  trendLabel = 'vs last period',
  icon: Icon,
  variant = 'blue',
  subtext,
  badge,
  description
}) => {
  const [showTooltip, setShowTooltip] = useState(false);

  const variantStyles = {
    blue: {
      iconBg: 'bg-blue-50 text-[#2563EB] border border-blue-200',
    },
    indigo: {
      iconBg: 'bg-blue-50 text-[#1E3A8A] border border-blue-200',
    },
    emerald: {
      iconBg: 'bg-emerald-50 text-[#16A34A] border border-emerald-200',
    },
    cyan: {
      iconBg: 'bg-blue-50 text-[#2563EB] border border-blue-200',
    },
    purple: {
      iconBg: 'bg-purple-50 text-[#7C3AED] border border-purple-200',
    },
    rose: {
      iconBg: 'bg-red-50 text-[#DC2626] border border-red-200',
    },
    amber: {
      iconBg: 'bg-amber-50 text-[#CA8A04] border border-amber-200',
    }
  };

  const currentVariant = variantStyles[variant] || variantStyles.blue;
  const isPositiveTrend = typeof trend === 'number' && trend > 0;
  const isNegativeTrend = typeof trend === 'number' && trend < 0;

  return (
    <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm hover:shadow-md hover:border-slate-300 transition-all duration-200 relative overflow-hidden group">
      <div className="flex items-start justify-between">
        <div className="min-w-0 pr-2">
          <div className="flex items-center space-x-1.5">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-500 truncate">{title}</span>
            {description && (
              <div className="relative inline-block">
                <button
                  type="button"
                  onMouseEnter={() => setShowTooltip(true)}
                  onMouseLeave={() => setShowTooltip(false)}
                  onClick={() => setShowTooltip(!showTooltip)}
                  className="text-slate-400 hover:text-slate-600 focus:outline-none"
                  aria-label="More information"
                >
                  <HelpCircle className="w-3.5 h-3.5" />
                </button>
                {showTooltip && (
                  <div className="absolute left-0 bottom-full mb-1.5 w-52 p-2 bg-slate-900 text-white text-[11px] leading-snug rounded-lg shadow-lg z-30 font-normal">
                    {description}
                  </div>
                )}
              </div>
            )}
          </div>
          <div className="text-2xl lg:text-3xl font-extrabold text-slate-900 mt-1.5 tracking-tight flex items-baseline space-x-2">
            <span>{value}</span>
            {badge && (
              <span className="text-[11px] px-2 py-0.5 rounded-full font-semibold bg-blue-50 text-[#2563EB] border border-blue-200">
                {badge}
              </span>
            )}
          </div>
        </div>

        {Icon && (
          <div className={`p-2.5 rounded-xl ${currentVariant.iconBg} transition-transform duration-200 group-hover:scale-105 shadow-sm shrink-0`}>
            <Icon className="w-5 h-5" />
          </div>
        )}
      </div>

      {/* Trend & Subtext */}
      <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-xs">
        {trend !== undefined && (
          <div className="flex items-center space-x-1 font-semibold">
            {isPositiveTrend && (
              <span className="flex items-center text-[#16A34A] bg-emerald-50 px-1.5 py-0.5 rounded-md border border-emerald-200">
                <ArrowUpRight className="w-3.5 h-3.5 mr-0.5" />
                +{trend}%
              </span>
            )}
            {isNegativeTrend && (
              <span className="flex items-center text-[#DC2626] bg-red-50 px-1.5 py-0.5 rounded-md border border-red-200">
                <ArrowDownRight className="w-3.5 h-3.5 mr-0.5" />
                {trend}%
              </span>
            )}
            {trend === 0 && (
              <span className="flex items-center text-slate-500 bg-slate-100 px-1.5 py-0.5 rounded-md border border-slate-200">
                <Minus className="w-3.5 h-3.5 mr-0.5" />
                0%
              </span>
            )}
            <span className="text-slate-500 text-[11px] ml-1">{trendLabel}</span>
          </div>
        )}
        {subtext && !trend && (
          <span className="text-slate-500 text-[11px] font-medium">{subtext}</span>
        )}
      </div>
    </div>
  );
};

export default KPICard;
