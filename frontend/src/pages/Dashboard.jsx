import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useBrand } from '../context/BrandContext';
import { useAuth } from '../context/AuthContext';
import { crisisAPI } from '../services/api';
import { useDashboardData } from '../hooks/useDashboardData';
import AlertBanner from '../components/dashboard/AlertBanner';
import InsightsBox from '../components/dashboard/InsightsBox';
import FeedStream from '../components/dashboard/FeedStream';
import DashboardKpis from '../components/dashboard/DashboardKpis';
import DashboardAspectIntelligence from '../components/dashboard/DashboardAspectIntelligence';
import DashboardCharts from '../components/dashboard/DashboardCharts';
import OwnerInsightsCard from '../components/dashboard/OwnerInsightsCard';
import { 
  RefreshCw, 
  UploadCloud, 
  Package, 
  Sparkles,
  Loader2,
  AlertCircle
} from 'lucide-react';

const Dashboard = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { activeBrand } = useBrand();
  const { user } = useAuth();

  const [timeRange, setTimeRange] = useState('7d');
  const [dataFilter, setDataFilter] = useState('all'); // all, real, simulated
  const [ingestToast, setIngestToast] = useState(location.state?.justIngested ? location.state : null);

  useEffect(() => {
    if (location.state?.justIngested) {
      setIngestToast(location.state);
      const t = setTimeout(() => setIngestToast(null), 8000);
      return () => clearTimeout(t);
    }
  }, [location.state]);

  const { data, isLoading, error, refetch } = useDashboardData(activeBrand?.id, timeRange, dataFilter);

  const overview = data?.overview || null;
  const trends = data?.trends || [];
  const emotions = data?.emotions || [];
  const mentions = data?.mentions || [];
  const alerts = data?.alerts || [];
  const insights = data?.insights || {};
  const igMetrics = data?.igMetrics || null;
  const sovData = data?.sovData || [];

  const handleAcknowledgeAlert = async (alertId) => {
    try {
      await crisisAPI.acknowledgeAlert(alertId);
      refetch();
    } catch (e) {
      console.error(e);
    }
  };

  const handleResolveAlert = async (alertId) => {
    try {
      await crisisAPI.resolveAlert(alertId);
      refetch();
    } catch (e) {
      console.error(e);
    }
  };

  const trackedProducts = activeBrand?.products && activeBrand.products.length > 0 
    ? activeBrand.products 
    : ['Main Products & Services'];

  if (isLoading && !data) {
    return (
      <div className="min-h-[60vh] flex flex-col items-center justify-center text-slate-500 space-y-3">
        <Loader2 className="w-8 h-8 animate-spin text-[#2563EB]" />
        <span className="text-sm font-semibold">Loading real-time brand intelligence...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6 bg-red-50 border border-red-200 rounded-2xl text-red-700 flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <AlertCircle className="w-5 h-5 text-red-600" />
          <span className="text-sm font-semibold">Failed to fetch brand metrics. Please check network connectivity.</span>
        </div>
        <button
          onClick={() => refetch()}
          className="px-3 py-1.5 bg-red-600 text-white font-semibold text-xs rounded-xl hover:bg-red-700 transition"
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6 pb-12 animate-fade-in">
      {/* Brand Hero Greeting Bar */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 bg-white p-5 rounded-3xl border border-slate-200 shadow-xs">
        <div>
          <div className="flex items-center space-x-2.5 flex-wrap gap-1">
            <h1 className="text-xl lg:text-2xl font-black text-slate-900 tracking-tight">
              Good day, {activeBrand?.name || 'My Business'} 👋
            </h1>
            <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-blue-50 text-[#2563EB] border border-blue-200">
              Live Monitoring
            </span>
          </div>

          <div className="flex items-center space-x-3 text-xs text-slate-500 mt-1 flex-wrap gap-1.5">
            <span>Type: <strong className="text-slate-800 capitalize">{activeBrand?.business_type || activeBrand?.industry || 'Shop'}</strong></span>
            <span>•</span>
            <span>Location: <strong className="text-slate-800">{activeBrand?.locations?.[0]?.city || 'Main Branch'}</strong></span>
            <span>•</span>
            <span>Owner: <strong className="text-slate-800">{user?.full_name || 'Owner'}</strong></span>
          </div>
        </div>

        {/* Time Range Selector, Upload Data Button & Refresh */}
        <div className="flex items-center space-x-2.5 self-end md:self-center flex-wrap gap-2">
          <button
            onClick={() => navigate('/dataset-ingestion')}
            className="px-3.5 py-1.5 rounded-xl bg-blue-50 hover:bg-[#2563EB] text-[#2563EB] hover:text-white font-bold text-xs transition border border-blue-200 shadow-xs flex items-center space-x-1.5"
          >
            <UploadCloud className="w-3.5 h-3.5" />
            <span>Upload Reviews</span>
          </button>

          <div className="bg-slate-100 p-1 rounded-xl border border-slate-200 flex items-center space-x-1 text-xs">
            {['24h', '7d', '30d'].map((range) => (
              <button
                key={range}
                onClick={() => setTimeRange(range)}
                className={`px-3 py-1 rounded-lg font-semibold transition ${
                  timeRange === range
                    ? 'bg-[#2563EB] text-white shadow-xs'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                {range.toUpperCase()}
              </button>
            ))}
          </div>

          <button
            onClick={() => refetch()}
            disabled={isLoading}
            className="p-2 rounded-xl bg-slate-100 hover:bg-slate-200 border border-slate-200 text-slate-700 transition"
            title="Refresh Metrics"
          >
            <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin text-[#2563EB]' : ''}`} />
          </button>
        </div>
      </div>

      {/* 3 Core Small Business KPIs */}
      <DashboardKpis
        overview={overview}
        activeBrand={activeBrand}
        ingestToast={ingestToast}
        onDismissToast={() => setIngestToast(null)}
      />

      {/* Needs Attention, What Customers Love & What to Fix First */}
      <OwnerInsightsCard
        insights={insights}
        overview={overview}
        mentions={mentions}
        activeBrand={activeBrand}
      />

      {/* Charts Grid */}
      <DashboardCharts
        trends={trends}
        overview={overview}
        emotions={emotions}
        sovData={sovData}
      />

      {/* Executive AI Insights Box */}
      <InsightsBox insights={insights} loading={isLoading} />

      {/* Real-time Live Feed Preview */}
      <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2.5">
            <div className="w-2.5 h-2.5 rounded-full bg-[#16A34A] live-indicator" />
            <div>
              <h3 className="text-sm font-bold text-slate-900 tracking-tight">Live Customer Posts Feed</h3>
              <p className="text-xs text-slate-500">Recent posts and comments with sentiment and emotion analysis</p>
            </div>
          </div>
          <button
            onClick={() => navigate('/social-listening')}
            className="text-xs font-semibold text-[#2563EB] hover:text-[#1E3A8A] transition underline"
          >
            View All Customer Posts →
          </button>
        </div>

        <FeedStream
          mentions={mentions}
          maxItems={5}
          showViewAll={true}
          onViewAll={() => navigate('/social-listening')}
        />
      </div>
    </div>
  );
};

export default Dashboard;
