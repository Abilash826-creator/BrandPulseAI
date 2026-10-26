import React from 'react';
import { NavLink } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { 
  Home, 
  MessageSquareQuote, 
  TrendingUp, 
  BarChart3, 
  FileText, 
  Settings2,
  Sparkles,
  UploadCloud,
  BrainCircuit,
  ShieldAlert,
  Database
} from 'lucide-react';

const Sidebar = ({ activeAlertCount = 0 }) => {
  const { user } = useAuth();
  const isAdmin = user?.role === 'admin';

  // 6 Primary Owner Navigation Items + Ask AI & Upload Data
  const mainNavItems = [
    { to: '/', label: 'Home', icon: Home, exact: true },
    { 
      to: '/ask', 
      label: 'Ask AI Advisor', 
      icon: Sparkles,
      badge: 'AI',
      badgeColor: 'bg-gradient-to-r from-blue-500 to-indigo-500 text-white font-bold text-[9px]'
    },
    { to: '/social-listening', label: 'Reviews & Feed', icon: MessageSquareQuote },
    { to: '/sentiment-analytics', label: 'Insights & Topics', icon: TrendingUp },
    { to: '/competitor-analysis', label: 'Compare Nearby', icon: BarChart3 },
    { to: '/reports', label: 'Reports', icon: FileText },
    { 
      to: '/dataset-ingestion', 
      label: 'Upload Reviews', 
      icon: UploadCloud,
      badge: 'PDF/CSV',
      badgeColor: 'bg-blue-600 text-white font-mono text-[9px]'
    },
    { to: '/brand-settings', label: 'Settings', icon: Settings2 },
  ];

  const adminNavItems = [
    ...(isAdmin ? [{ to: '/ml-studio', label: 'AI Model Studio', icon: BrainCircuit }] : []),
    ...(isAdmin ? [{ to: '/summaries', label: 'Raw Summaries', icon: Database }] : []),
    { 
      to: '/crisis-alerts', 
      label: 'Needs Attention', 
      icon: ShieldAlert,
      badge: activeAlertCount > 0 ? `${activeAlertCount} active` : null,
      badgeColor: 'bg-red-500 text-white animate-pulse'
    },
  ];

  return (
    <aside className="hidden lg:flex w-64 border-r border-slate-800 bg-[#0F172A] flex-col justify-between shrink-0 h-screen sticky top-0 z-40 text-slate-300">
      {/* Brand Header */}
      <div>
        <div className="h-16 px-4 flex items-center space-x-3 border-b border-slate-800 bg-[#0F172A]">
          <img 
            src="/logo.jpg" 
            alt="BrandPulse AI Logo" 
            className="w-9 h-9 rounded-xl object-cover shadow-sm ring-1 ring-blue-500/30"
          />
          <div className="flex-1 min-w-0">
            <div className="font-extrabold text-sm tracking-wider text-white flex items-center space-x-1.5 truncate">
              <span>BrandPulse</span>
              <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-blue-600/30 text-blue-300 border border-blue-500/40">AI</span>
            </div>
            <div className="text-[10px] text-slate-400 tracking-tight font-medium truncate">Small Business Reputation</div>
          </div>
        </div>

        {/* Navigation Items */}
        <nav className="p-3 space-y-1 mt-2">
          {mainNavItems.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.exact}
                className={({ isActive }) =>
                  `flex items-center justify-between px-3.5 py-2.5 rounded-xl text-xs font-semibold tracking-wide transition-all ${
                    isActive
                      ? 'bg-[#2563EB] text-white shadow-md'
                      : 'text-slate-300 hover:text-white hover:bg-slate-800/80'
                  }`
                }
              >
                <div className="flex items-center space-x-3">
                  <Icon className="w-4 h-4" />
                  <span>{item.label}</span>
                </div>
                {item.badge && (
                  <span className={`text-[10px] px-2 py-0.5 rounded-full font-bold shadow-sm ${item.badgeColor}`}>
                    {item.badge}
                  </span>
                )}
              </NavLink>
            );
          })}

          {/* Secondary / Admin Items */}
          <div className="pt-3 mt-3 border-t border-slate-800/80">
            <span className="text-[10px] font-bold text-slate-500 uppercase px-3 tracking-wider block mb-1">
              Alerts & Tools
            </span>
            {adminNavItems.map((item) => {
              const Icon = item.icon;
              return (
                <NavLink
                  key={item.to}
                  to={item.to}
                  className={({ isActive }) =>
                    `flex items-center justify-between px-3.5 py-2 rounded-xl text-xs font-medium tracking-wide transition-all ${
                      isActive
                        ? 'bg-[#2563EB] text-white shadow-md'
                        : 'text-slate-400 hover:text-white hover:bg-slate-800/60'
                    }`
                  }
                >
                  <div className="flex items-center space-x-3">
                    <Icon className="w-4 h-4" />
                    <span>{item.label}</span>
                  </div>
                  {item.badge && (
                    <span className={`text-[10px] px-2 py-0.5 rounded-full font-bold shadow-sm ${item.badgeColor}`}>
                      {item.badge}
                    </span>
                  )}
                </NavLink>
              );
            })}
          </div>
        </nav>
      </div>

      {/* Footer System Status Banner */}
      <div className="p-3.5 m-3 rounded-2xl bg-slate-900/90 border border-slate-800">
        <div className="flex items-center space-x-2 mb-1">
          <div className="w-2 h-2 rounded-full bg-[#16A34A] animate-pulse"></div>
          <span className="text-xs font-semibold text-white">Active Protection</span>
        </div>
        <p className="text-[11px] text-slate-400 leading-relaxed">
          Listening to customer reviews & feedback in real-time.
        </p>
      </div>
    </aside>
  );
};

export default Sidebar;
