import React, { useState } from 'react';
import { NavLink } from 'react-router-dom';
import { 
  Home, 
  MessageSquareQuote, 
  Sparkles, 
  TrendingUp, 
  Menu, 
  X, 
  BarChart3, 
  FileText, 
  Settings2, 
  UploadCloud, 
  ShieldAlert 
} from 'lucide-react';

const MobileBottomNav = ({ activeAlertCount = 0 }) => {
  const [moreDrawerOpen, setMoreDrawerOpen] = useState(false);

  const mainTabs = [
    { to: '/', label: 'Home', icon: Home, exact: true },
    { to: '/social-listening', label: 'Reviews', icon: MessageSquareQuote },
    { to: '/ask', label: 'Ask AI', icon: Sparkles, isAi: true },
    { to: '/sentiment-analytics', label: 'Insights', icon: TrendingUp },
  ];

  const moreItems = [
    { to: '/competitor-analysis', label: 'Compare Nearby', icon: BarChart3 },
    { to: '/reports', label: 'Reports', icon: FileText },
    { to: '/dataset-ingestion', label: 'Upload Reviews', icon: UploadCloud },
    { to: '/crisis-alerts', label: 'Needs Attention', icon: ShieldAlert, badge: activeAlertCount > 0 ? activeAlertCount : null },
    { to: '/brand-settings', label: 'Settings', icon: Settings2 },
  ];

  return (
    <>
      {/* Mobile Slide-Up "More" Sheet */}
      {moreDrawerOpen && (
        <div 
          className="fixed inset-0 bg-slate-900/50 backdrop-blur-xs z-50 lg:hidden"
          onClick={() => setMoreDrawerOpen(false)}
        >
          <div 
            className="absolute bottom-0 left-0 right-0 bg-white rounded-t-3xl p-5 shadow-2xl border-t border-slate-200 animate-slide-up"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between pb-3 mb-2 border-b border-slate-100">
              <span className="font-extrabold text-sm text-slate-900">More Actions</span>
              <button 
                onClick={() => setMoreDrawerOpen(false)}
                className="p-1 rounded-full text-slate-400 hover:text-slate-700"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="grid grid-cols-2 gap-2.5 py-2">
              {moreItems.map((item) => {
                const Icon = item.icon;
                return (
                  <NavLink
                    key={item.to}
                    to={item.to}
                    onClick={() => setMoreDrawerOpen(false)}
                    className={({ isActive }) =>
                      `flex items-center space-x-3 p-3 rounded-2xl text-xs font-semibold transition ${
                        isActive
                          ? 'bg-blue-50 text-blue-700 border border-blue-200'
                          : 'bg-slate-50 text-slate-700 hover:bg-slate-100'
                      }`
                    }
                  >
                    <Icon className="w-4 h-4 text-slate-500" />
                    <span>{item.label}</span>
                    {item.badge && (
                      <span className="ml-auto bg-red-500 text-white text-[10px] px-1.5 py-0.2 rounded-full font-bold">
                        {item.badge}
                      </span>
                    )}
                  </NavLink>
                );
              })}
            </div>
          </div>
        </div>
      )}

      {/* Fixed Bottom Tab Bar (Visible on mobile/tablet < 1024px) */}
      <nav 
        aria-label="Mobile Navigation"
        className="lg:hidden fixed bottom-0 left-0 right-0 h-16 bg-white border-t border-slate-200 z-40 px-2 flex items-center justify-around shadow-lg"
      >
        {mainTabs.map((tab) => {
          const Icon = tab.icon;
          if (tab.isAi) {
            return (
              <NavLink
                key={tab.to}
                to={tab.to}
                className={({ isActive }) =>
                  `flex flex-col items-center justify-center -mt-4 group`
                }
              >
                {({ isActive }) => (
                  <>
                    <div className={`w-12 h-12 rounded-full flex items-center justify-center shadow-lg transition-transform active:scale-95 ${
                      isActive 
                        ? 'bg-gradient-to-tr from-blue-600 to-indigo-600 ring-4 ring-blue-100 text-white' 
                        : 'bg-gradient-to-tr from-blue-600 to-indigo-600 text-white'
                    }`}>
                      <Sparkles className="w-5 h-5 text-amber-300" />
                    </div>
                    <span className={`text-[10px] mt-1 font-bold ${isActive ? 'text-blue-600' : 'text-slate-600'}`}>
                      {tab.label}
                    </span>
                  </>
                )}
              </NavLink>
            );
          }

          return (
            <NavLink
              key={tab.to}
              to={tab.to}
              end={tab.exact}
              className={({ isActive }) =>
                `flex flex-col items-center justify-center py-1 px-2.5 rounded-xl transition ${
                  isActive ? 'text-blue-600 font-bold' : 'text-slate-500 hover:text-slate-900 font-medium'
                }`
              }
            >
              <Icon className="w-5 h-5 mb-0.5" />
              <span className="text-[10px] tracking-tight">{tab.label}</span>
            </NavLink>
          );
        })}

        {/* More Button */}
        <button
          type="button"
          onClick={() => setMoreDrawerOpen(true)}
          className="flex flex-col items-center justify-center py-1 px-2.5 rounded-xl text-slate-500 hover:text-slate-900 font-medium transition"
        >
          <div className="relative">
            <Menu className="w-5 h-5 mb-0.5" />
            {activeAlertCount > 0 && (
              <span className="absolute -top-1 -right-1 w-2 h-2 bg-red-500 rounded-full"></span>
            )}
          </div>
          <span className="text-[10px] tracking-tight">More</span>
        </button>
      </nav>
    </>
  );
};

export default MobileBottomNav;
