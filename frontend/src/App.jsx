import React, { useState, useEffect, Suspense, lazy } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import { BrandProvider, useBrand } from './context/BrandContext';
import Navbar from './components/common/Navbar';
import Sidebar from './components/common/Sidebar';
import MobileBottomNav from './components/common/MobileBottomNav';
import Modal from './components/common/Modal';
import { crisisAPI } from './services/api';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
      staleTime: 30000,
    },
  },
});

// Lazy-loaded Pages for Route Code-Splitting
const Login = lazy(() => import('./pages/Login'));
const Register = lazy(() => import('./pages/Register'));
const Dashboard = lazy(() => import('./pages/Dashboard'));
const SocialListening = lazy(() => import('./pages/SocialListening'));
const SentimentAnalytics = lazy(() => import('./pages/SentimentAnalytics'));
const CrisisAlerts = lazy(() => import('./pages/CrisisAlerts'));
const CompetitorAnalysis = lazy(() => import('./pages/CompetitorAnalysis'));
const TopicModeling = lazy(() => import('./pages/TopicModeling'));
const Reports = lazy(() => import('./pages/Reports'));
const BrandSettings = lazy(() => import('./pages/BrandSettings'));
const MonitoredSummaries = lazy(() => import('./pages/MonitoredSummaries'));
const ModelTrainingStudio = lazy(() => import('./pages/ModelTrainingStudio'));
const DatasetUpload = lazy(() => import('./pages/DatasetUpload'));
const Onboarding = lazy(() => import('./pages/Onboarding'));
const AskAI = lazy(() => import('./pages/AskAI'));
const Landing = lazy(() => import('./pages/Landing'));

import AskAIDrawer from './components/assistant/AskAIDrawer';
import ErrorBoundary from './components/common/ErrorBoundary';

const PageLoader = () => (
  <div className="min-h-[50vh] flex flex-col items-center justify-center space-y-3">
    <div className="w-8 h-8 border-2 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
    <span className="text-xs font-semibold text-slate-500">Loading module...</span>
  </div>
);

// Protected Route Wrapper
const ProtectedRoute = ({ children }) => {
  const { isAuthenticated, loading } = useAuth();
  if (loading) {
    return (
      <div className="min-h-screen bg-[#F8FAFC] flex items-center justify-center text-slate-500 text-xs font-semibold">
        Initializing BrandPulse AI Security...
      </div>
    );
  }
  return isAuthenticated ? children : <Navigate to="/login" replace />;
};

// Root Route: Public Landing Page for Guests, Protected App Layout for Authenticated Users
const RootRoute = () => {
  const { isAuthenticated, loading } = useAuth();
  if (loading) {
    return (
      <div className="min-h-screen bg-[#F8FAFC] flex items-center justify-center text-slate-500 text-xs font-semibold">
        Initializing BrandPulse AI Security...
      </div>
    );
  }
  return isAuthenticated ? <Layout /> : <Landing />;
};

// Main Layout
const Layout = () => {
  const { activeBrand, createBrand } = useBrand();
  const [newBrandModalOpen, setNewBrandModalOpen] = useState(false);
  const [activeAlertCount, setActiveAlertCount] = useState(0);

  // New Business Form State
  const [newBrandForm, setNewBrandForm] = useState({
    name: '',
    business_type: 'restaurant',
    industry: 'Food & Beverage',
    branch: 'Main Branch',
    city: '',
    description: '',
    keywords: '',
    competitors: ''
  });
  const [creatingBrand, setCreatingBrand] = useState(false);

  useEffect(() => {
    const fetchAlertStatus = async () => {
      if (!activeBrand) return;
      try {
        const res = await crisisAPI.getStatus(activeBrand.id);
        setActiveAlertCount(res.data?.active_alerts_count || 0);
      } catch (e) {
        // silent fail
      }
    };
    fetchAlertStatus();
    const interval = setInterval(fetchAlertStatus, 15000);
    return () => clearInterval(interval);
  }, [activeBrand]);

  const handleCreateBrand = async (e) => {
    e.preventDefault();
    if (!newBrandForm.name.trim()) return;
    setCreatingBrand(true);
    try {
      const keywordsArray = newBrandForm.keywords
        ? newBrandForm.keywords.split(',').map(k => k.trim()).filter(Boolean)
        : [newBrandForm.name];

      const competitorsArray = newBrandForm.competitors
        ? newBrandForm.competitors.split(',').map(c => c.trim()).filter(Boolean)
        : [];

      await createBrand({
        name: newBrandForm.name,
        business_type: newBrandForm.business_type,
        industry: newBrandForm.industry,
        description: newBrandForm.description,
        locations: [
          {
            id: `loc_${Date.now().toString(36)}`,
            name: newBrandForm.branch || 'Main Branch',
            city: newBrandForm.city || '',
            is_primary: true
          }
        ],
        keywords: keywordsArray,
        hashtags: [`#${newBrandForm.name.replace(/\s+/g, '')}`],
        competitors: competitorsArray,
        social_handles: {},
        is_primary: false
      });

      setNewBrandModalOpen(false);
      setNewBrandForm({
        name: '',
        business_type: 'restaurant',
        industry: 'Food & Beverage',
        branch: 'Main Branch',
        city: '',
        description: '',
        keywords: '',
        competitors: ''
      });
    } catch (err) {
      console.error(err);
    } finally {
      setCreatingBrand(false);
    }
  };

  return (
    <div className="flex min-h-screen bg-[#F8FAFC] text-slate-800 selection:bg-blue-600 selection:text-white font-sans">
      {/* Sidebar */}
      <Sidebar activeAlertCount={activeAlertCount} />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0">
        <Navbar 
          onOpenNewBrandModal={() => setNewBrandModalOpen(true)} 
          activeAlertCount={activeAlertCount} 
        />

        <main className="flex-1 p-4 sm:p-6 lg:p-8 max-w-7xl w-full mx-auto pb-24 lg:pb-8">
          <ErrorBoundary>
            <Suspense fallback={<PageLoader />}>
              <Routes>
                <Route path="/" element={<Dashboard />} />
                <Route path="/dashboard" element={<Dashboard />} />
                <Route path="/onboarding" element={<Onboarding />} />
                <Route path="/dataset-ingestion" element={<DatasetUpload />} />
                <Route path="/social-listening" element={<SocialListening />} />
                <Route path="/sentiment-analytics" element={<SentimentAnalytics />} />
                <Route path="/ml-studio" element={<ModelTrainingStudio />} />
                <Route path="/summaries" element={<MonitoredSummaries />} />
                <Route path="/crisis-alerts" element={<CrisisAlerts />} />
                <Route path="/competitor-analysis" element={<CompetitorAnalysis />} />
                <Route path="/topic-clusters" element={<TopicModeling />} />
                <Route path="/reports" element={<Reports />} />
                <Route path="/brand-settings" element={<BrandSettings />} />
                <Route path="/profile" element={<BrandSettings />} />
                <Route path="/settings" element={<BrandSettings />} />
                <Route path="/ask" element={<AskAI />} />
                <Route path="*" element={<Navigate to="/" replace />} />
              </Routes>
            </Suspense>
          </ErrorBoundary>
        </main>
      </div>

      {/* Mobile Bottom Navigation Bar (<1024px) */}
      <MobileBottomNav activeAlertCount={activeAlertCount} />

      {/* Global Floating Ask AI Assistant Drawer */}
      <AskAIDrawer />

      {/* New Business Modal */}
      <Modal
        isOpen={newBrandModalOpen}
        onClose={() => setNewBrandModalOpen(false)}
        title="Add New Business & Branch"
      >
        <form onSubmit={handleCreateBrand} className="space-y-4 text-xs">
          <p className="text-slate-600">
            Add a new shop or business profile to start monitoring customer reviews, sentiment, and branch performance.
          </p>

          <div>
            <label className="font-semibold text-slate-700 block mb-1">Business / Shop Name *</label>
            <input
              type="text"
              value={newBrandForm.name}
              onChange={(e) => setNewBrandForm({ ...newBrandForm, name: e.target.value })}
              placeholder="e.g. Annapoorna Sweets, City Dental, Modern Mart"
              required
              className="w-full bg-white border border-slate-200 rounded-xl p-3 text-slate-900 focus:outline-none focus:border-blue-600 focus:ring-1 focus:ring-blue-600"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="font-semibold text-slate-700 block mb-1">Business Type</label>
              <select
                value={newBrandForm.business_type}
                onChange={(e) => setNewBrandForm({ ...newBrandForm, business_type: e.target.value })}
                className="w-full bg-white border border-slate-200 rounded-xl p-3 text-slate-900 focus:outline-none focus:border-blue-600 font-medium"
              >
                <option value="restaurant">Restaurant / Cafe</option>
                <option value="retail">Retail Shop</option>
                <option value="salon">Salon & Spa</option>
                <option value="clinic">Clinic / Healthcare</option>
                <option value="supermarket">Supermarket / Grocery</option>
                <option value="bakery">Bakery & Sweets</option>
              </select>
            </div>

            <div>
              <label className="font-semibold text-slate-700 block mb-1">Branch Name</label>
              <input
                type="text"
                value={newBrandForm.branch}
                onChange={(e) => setNewBrandForm({ ...newBrandForm, branch: e.target.value })}
                placeholder="e.g. Main Branch, T. Nagar"
                className="w-full bg-white border border-slate-200 rounded-xl p-3 text-slate-900 focus:outline-none focus:border-blue-600"
              />
            </div>
          </div>

          <div>
            <label className="font-semibold text-slate-700 block mb-1">City / Locality</label>
            <input
              type="text"
              value={newBrandForm.city}
              onChange={(e) => setNewBrandForm({ ...newBrandForm, city: e.target.value })}
              placeholder="e.g. Chennai, Bengaluru, Mumbai"
              className="w-full bg-white border border-slate-200 rounded-xl p-3 text-slate-900 focus:outline-none focus:border-blue-600"
            />
          </div>

          <div className="p-3 bg-blue-50/60 rounded-xl border border-blue-100 flex items-center justify-between">
            <span className="text-[11px] text-blue-900 font-medium">Want to import initial reviews now?</span>
            <a
              href="/onboarding"
              onClick={() => setNewBrandModalOpen(false)}
              className="text-[11px] font-bold text-blue-600 hover:underline"
            >
              Open 3-Step Guided Onboarding →
            </a>
          </div>

          <div className="flex justify-end space-x-2 pt-3 border-t border-slate-200">
            <button
              type="button"
              onClick={() => setNewBrandModalOpen(false)}
              className="px-4 py-2 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold transition"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={creatingBrand}
              className="px-5 py-2 rounded-xl bg-[#2563EB] hover:bg-[#1E3A8A] text-white font-bold transition disabled:opacity-50"
            >
              {creatingBrand ? 'Creating Business...' : 'Create Business'}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
};

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Router>
        <AuthProvider>
          <BrandProvider>
            <Suspense fallback={<PageLoader />}>
              <Routes>
                <Route path="/" element={<RootRoute />} />
                <Route path="/landing" element={<Landing />} />
                <Route path="/login" element={<Login />} />
                <Route path="/register" element={<Register />} />
                <Route
                  path="/*"
                  element={
                    <ProtectedRoute>
                      <Layout />
                    </ProtectedRoute>
                  }
                />
              </Routes>
            </Suspense>
          </BrandProvider>
        </AuthProvider>
      </Router>
    </QueryClientProvider>
  );
}

export default App;
