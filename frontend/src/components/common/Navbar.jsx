import React, { useState, useEffect } from 'react';
import { useBrand } from '../../context/BrandContext';
import { useAuth } from '../../context/AuthContext';
import { systemAPI, authAPI } from '../../services/api';
import { 
  Building2, 
  ChevronDown, 
  Plus, 
  Activity, 
  Flame, 
  Sparkles, 
  Swords, 
  User, 
  LogOut, 
  ShieldCheck, 
  Key, 
  Database, 
  CheckCircle2, 
  AlertTriangle, 
  RefreshCw, 
  Server,
  Trash2,
  Loader2,
  Bell,
  Globe
} from 'lucide-react';
import { Link } from 'react-router-dom';
import Modal from './Modal';

const Navbar = ({ onOpenNewBrandModal, activeAlertCount = 0 }) => {
  const { brands, activeBrand, setActiveBrand, refreshBrands, deleteBrand } = useBrand();
  const { user, logout } = useAuth();
  const [brandDropdownOpen, setBrandDropdownOpen] = useState(false);
  const [langDropdownOpen, setLangDropdownOpen] = useState(false);
  const [currentLang, setCurrentLang] = useState('English');
  const [dbModalOpen, setDbModalOpen] = useState(false);
  const [authModalOpen, setAuthModalOpen] = useState(false);
  const [userDropdownOpen, setUserDropdownOpen] = useState(false);
  const [brandToDelete, setBrandToDelete] = useState(null);
  const [deletingBrand, setDeletingBrand] = useState(false);

  const handleDeleteBrand = async () => {
    if (!brandToDelete) return;
    setDeletingBrand(true);
    try {
      await deleteBrand(brandToDelete.id);
      setBrandToDelete(null);
    } catch (err) {
      console.error("Failed to delete brand:", err);
    } finally {
      setDeletingBrand(false);
    }
  };
  
  // Database status state
  const [dbStatus, setDbStatus] = useState(null);
  const [customMongoUri, setCustomMongoUri] = useState('');
  const [connectingDb, setConnectingDb] = useState(false);
  const [dbConnectMsg, setDbConnectMsg] = useState(null);

  // Auth audit logs state
  const [auditLogs, setAuditLogs] = useState([]);
  const [loadingAuditLogs, setLoadingAuditLogs] = useState(false);

  const fetchAuditLogs = async () => {
    setLoadingAuditLogs(true);
    try {
      const res = await authAPI.getAuditLogs(20);
      setAuditLogs(res.data || []);
    } catch (e) {
      console.warn('Could not fetch audit logs', e);
    } finally {
      setLoadingAuditLogs(false);
    }
  };

  const fetchDbStatus = async () => {
    if (user?.role !== 'admin') return;
    try {
      const res = await systemAPI.getDbStatus();
      setDbStatus(res.data);
    } catch (e) {
      console.warn('Could not fetch DB status', e);
    }
  };

  useEffect(() => {
    if (user?.role === 'admin') {
      fetchDbStatus();
      const interval = setInterval(fetchDbStatus, 15000);
      return () => clearInterval(interval);
    }
  }, [user?.role]);

  const handleConnectMongo = async (uriToUse) => {
    const uri = uriToUse || customMongoUri;
    if (!uri) return;
    setConnectingDb(true);
    setDbConnectMsg(null);
    try {
      const res = await systemAPI.connectDb(uri);
      setDbStatus(res.data.status);
      setDbConnectMsg({
        success: res.data.success,
        text: res.data.message
      });
      if (res.data.success) {
        setCustomMongoUri('');
        if (refreshBrands) refreshBrands();
      }
    } catch (err) {
      setDbConnectMsg({
        success: false,
        text: err?.response?.data?.detail || err.message || 'Failed to connect to MongoDB'
      });
    } finally {
      setConnectingDb(false);
    }
  };

  return (
    <header className="h-16 border-b border-slate-200 bg-white sticky top-0 z-30 px-4 sm:px-6 flex items-center justify-between shadow-xs">
      {/* Left: Active Business Display / Switcher */}
      <div className="flex items-center space-x-3 min-w-0">
        <div className="relative">
          {brands.length > 1 ? (
            <button
              onClick={() => setBrandDropdownOpen(!brandDropdownOpen)}
              className="flex items-center space-x-2.5 bg-slate-50 hover:bg-slate-100 border border-slate-200 px-3 py-1.5 rounded-xl transition text-xs font-semibold text-slate-800"
            >
              <div className="w-6 h-6 rounded-lg bg-[#1E3A8A] flex items-center justify-center text-white text-xs font-bold shrink-0">
                {activeBrand?.name?.charAt(0) || 'B'}
              </div>
              <span className="tracking-tight text-slate-900 truncate max-w-[120px] sm:max-w-[200px]">
                {activeBrand?.name || 'Select Business'}
              </span>
              <ChevronDown className="w-3.5 h-3.5 text-slate-400" />
            </button>
          ) : (
            <div className="flex items-center space-x-2.5 px-1 py-1">
              <div className="w-7 h-7 rounded-lg bg-[#1E3A8A] flex items-center justify-center text-white text-xs font-bold shrink-0">
                {activeBrand?.name?.charAt(0) || 'B'}
              </div>
              <span className="text-xs font-extrabold text-slate-900 tracking-tight truncate max-w-[140px] sm:max-w-[220px]">
                {activeBrand?.name || 'My Shop'}
              </span>
            </div>
          )}

          {/* Business Switcher Dropdown */}
          {brandDropdownOpen && brands.length > 1 && (
            <div className="absolute left-0 mt-2 w-80 bg-white rounded-2xl shadow-2xl py-2 z-50 animate-fade-in border border-slate-200">
              <div className="px-3.5 py-1.5 flex items-center justify-between border-b border-slate-100 mb-1">
                <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">
                  Switch Business ({brands.length})
                </span>
              </div>

              <div className="max-h-64 overflow-y-auto px-1.5 space-y-0.5">
                {brands.map((b) => (
                  <div
                    key={b.id}
                    onClick={() => {
                      setActiveBrand(b);
                      setBrandDropdownOpen(false);
                    }}
                    className={`group w-full px-2.5 py-2 rounded-xl text-left flex items-center justify-between text-xs transition cursor-pointer ${
                      activeBrand?.id === b.id 
                        ? 'bg-blue-50/80 text-blue-700 font-semibold border border-blue-100' 
                        : 'text-slate-700 hover:bg-slate-50 border border-transparent'
                    }`}
                  >
                    <div className="flex items-center space-x-2.5 min-w-0 flex-1 pr-2">
                      <div className={`w-6 h-6 rounded-lg flex items-center justify-center text-[11px] font-bold shrink-0 ${
                        activeBrand?.id === b.id ? 'bg-[#2563EB] text-white' : 'bg-slate-100 text-slate-600'
                      }`}>
                        {b.name?.charAt(0) || 'B'}
                      </div>
                      <div className="truncate">
                        <div className="font-semibold text-slate-900">{b.name}</div>
                        {b.locations?.[0] && (
                          <div className="text-[10px] text-slate-500 font-normal">
                            📍 {b.locations[0].name}
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Location pill */}
        {activeBrand?.locations?.[0]?.city && (
          <span className="hidden sm:inline-flex items-center gap-1 px-2.5 py-1 rounded-lg text-xs font-semibold bg-emerald-50 text-emerald-800 border border-emerald-200">
            <span>📍</span>
            <span>{activeBrand.locations[0].city}</span>
          </span>
        )}
      </div>

      {/* Right: Language switch + Notifications + User Profile */}
      <div className="flex items-center space-x-2 sm:space-x-3">
        {/* Language Switcher */}
        <div className="relative">
          <button
            type="button"
            onClick={() => setLangDropdownOpen(!langDropdownOpen)}
            className="flex items-center space-x-1 px-2.5 py-1.5 rounded-xl border border-slate-200 text-xs text-slate-700 hover:bg-slate-50 transition font-medium"
            title="Switch Language"
          >
            <Globe className="w-3.5 h-3.5 text-slate-500" />
            <span className="hidden sm:inline text-xs">{currentLang}</span>
            <ChevronDown className="w-3 h-3 text-slate-400" />
          </button>

          {langDropdownOpen && (
            <div className="absolute right-0 mt-2 w-32 bg-white rounded-xl shadow-xl py-1.5 z-50 border border-slate-200 text-xs">
              {[
                { code: 'en', label: 'English' },
                { code: 'ta', label: 'தமிழ் (Tamil)' },
                { code: 'hi', label: 'हिन्दी (Hindi)' }
              ].map((lang) => (
                <button
                  key={lang.code}
                  onClick={() => {
                    setCurrentLang(lang.label.split(' ')[0]);
                    setLangDropdownOpen(false);
                  }}
                  className={`w-full text-left px-3 py-2 text-xs hover:bg-blue-50 hover:text-blue-600 transition ${
                    currentLang.startsWith(lang.label.split(' ')[0]) ? 'font-bold text-blue-600 bg-blue-50/50' : 'text-slate-700'
                  }`}
                >
                  {lang.label}
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Notifications Bell */}
        <Link
          to="/crisis-alerts"
          className="relative p-2 rounded-xl text-slate-500 hover:text-slate-800 hover:bg-slate-100 transition"
          title="Notifications & Needs Attention"
        >
          <Bell className="w-4 h-4" />
          {activeAlertCount > 0 && (
            <span className="absolute top-1 right-1 w-2.5 h-2.5 bg-red-500 rounded-full ring-2 ring-white animate-pulse" />
          )}
        </Link>

        {/* Admin only: Database status */}
        {user?.role === 'admin' && (
          <button
            onClick={() => {
              fetchDbStatus();
              setDbModalOpen(true);
            }}
            className="hidden xl:flex items-center space-x-1.5 px-2.5 py-1 rounded-xl border border-slate-200 text-[11px] font-medium text-slate-600 hover:bg-slate-50 transition"
            title="Database status (admin)"
          >
            <Database className="w-3 h-3 text-emerald-600" />
            <span>DB Online</span>
          </button>
        )}

        {/* User Account Menu */}
        <div className="relative">
          <button
            onClick={() => setUserDropdownOpen(!userDropdownOpen)}
            className="flex items-center space-x-2 pl-1.5 pr-2 py-1.5 rounded-xl hover:bg-slate-100 border border-transparent hover:border-slate-200 transition"
          >
            <div className="w-7 h-7 rounded-lg bg-[#1E3A8A] flex items-center justify-center text-white font-bold text-xs shadow-xs">
              {user?.full_name?.charAt(0) || 'U'}
            </div>
            <span className="hidden md:inline text-xs font-semibold text-slate-800 truncate max-w-[100px]">
              {user?.full_name?.split(' ')[0] || 'Owner'}
            </span>
            <ChevronDown className="w-3 h-3 text-slate-400 hidden sm:block" />
          </button>

          {userDropdownOpen && (
            <div className="absolute right-0 mt-2 w-52 bg-white rounded-xl shadow-xl py-2 z-50 animate-fade-in border border-slate-200 text-xs">
              <div className="px-3 py-2 border-b border-slate-100">
                <p className="font-bold text-slate-900 truncate">{user?.full_name}</p>
                <p className="text-[11px] text-slate-500 truncate">{user?.email}</p>
              </div>
              <div className="py-1">
                <Link
                  to="/brand-settings"
                  onClick={() => setUserDropdownOpen(false)}
                  className="w-full px-3 py-2 text-left flex items-center space-x-2 text-slate-700 hover:bg-slate-50 text-xs transition font-medium"
                >
                  <User className="w-3.5 h-3.5 text-blue-600" />
                  <span>Business Profile & Settings</span>
                </Link>
                <Link
                  to="/landing"
                  onClick={() => setUserDropdownOpen(false)}
                  className="w-full px-3 py-2 text-left flex items-center space-x-2 text-slate-700 hover:bg-slate-50 text-xs transition font-medium"
                >
                  <Globe className="w-3.5 h-3.5 text-indigo-600" />
                  <span>Public Landing Page</span>
                </Link>
                <button
                  onClick={() => {
                    setUserDropdownOpen(false);
                    logout();
                  }}
                  className="w-full px-3 py-2 text-left flex items-center space-x-2 text-red-600 hover:bg-red-50 text-xs font-medium transition"
                >
                  <LogOut className="w-3.5 h-3.5" />
                  <span>Sign Out</span>
                </button>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* MongoDB Connection Modal */}
      <Modal
        isOpen={dbModalOpen}
        onClose={() => setDbModalOpen(false)}
        title="MongoDB Database Connection Hub"
      >
        <div className="space-y-4 text-xs">
          {/* Status Box */}
          <div className="p-4 rounded-2xl bg-slate-50 border border-slate-200 space-y-2.5">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <Server className="w-4 h-4 text-[#2563EB]" />
                <span className="font-semibold text-slate-800">Active Storage Driver:</span>
              </div>
              <span className={`px-2.5 py-0.5 rounded-full text-xs font-mono font-bold ${
                dbStatus?.is_connected ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' : 'bg-red-50 text-red-700 border border-red-200'
              }`}>
                {dbStatus?.mode || 'Loading...'}
              </span>
            </div>

            <div className="text-slate-600 space-y-1">
              <div><strong>Target Database:</strong> <span className="text-slate-900 font-mono">{dbStatus?.database_name || 'brandpulse_ai'}</span></div>
              <div><strong>Active URI:</strong> <span className="text-[#2563EB] font-mono break-all">{dbStatus?.uri || 'mongodb://localhost:27017'}</span></div>
            </div>

            {/* Collection counts */}
            {dbStatus?.collections && (
              <div className="pt-2 border-t border-slate-200">
                <div className="text-[11px] font-semibold text-slate-500 mb-1.5 uppercase tracking-wider">Persisted Documents</div>
                <div className="grid grid-cols-3 sm:grid-cols-5 gap-2">
                  {Object.entries(dbStatus.collections).map(([coll, count]) => (
                    <div key={coll} className="p-2 rounded-xl bg-white border border-slate-200 text-center shadow-sm">
                      <div className="text-slate-900 font-bold font-mono">{count}</div>
                      <div className="text-[10px] text-slate-500 capitalize">{coll}</div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Quick Connect Options */}
          <div className="space-y-2">
            <label className="font-semibold text-slate-800 block">Switch / Test Database Connection:</label>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
              <button
                type="button"
                onClick={() => handleConnectMongo("mongodb+srv://gokuladarshini47_db_user:Gokula060906@gokula06.dv2ulci.mongodb.net/brandpulse_ai?retryWrites=true&w=majority&appName=gokula06")}
                disabled={connectingDb}
                className="p-3 rounded-xl bg-slate-50 hover:bg-slate-100 border border-slate-200 text-left transition flex items-center justify-between"
              >
                <div>
                  <div className="font-semibold text-slate-900">MongoDB Atlas (Live Cloud)</div>
                  <div className="text-[10px] text-slate-500">Cloud Cluster with TLS</div>
                </div>
                <Database className="w-4 h-4 text-emerald-600" />
              </button>

              <button
                type="button"
                onClick={() => handleConnectMongo("mongodb://127.0.0.1:27017")}
                disabled={connectingDb}
                className="p-3 rounded-xl bg-slate-50 hover:bg-slate-100 border border-slate-200 text-left transition flex items-center justify-between"
              >
                <div>
                  <div className="font-semibold text-slate-900">Local MongoDB Service</div>
                  <div className="text-[10px] text-slate-500">mongodb://127.0.0.1:27017</div>
                </div>
                <Server className="w-4 h-4 text-[#2563EB]" />
              </button>
            </div>
          </div>

          {/* Custom URI Input */}
          <div className="space-y-1.5 pt-1">
            <label className="font-semibold text-slate-800 block">Or Connect via Custom MongoDB URI:</label>
            <div className="flex space-x-2">
              <input
                type="text"
                value={customMongoUri}
                onChange={(e) => setCustomMongoUri(e.target.value)}
                placeholder="mongodb+srv://user:pass@cluster.mongodb.net/brandpulse_ai"
                className="flex-1 bg-white border border-slate-200 rounded-xl px-3 py-2 text-slate-900 placeholder-slate-400 text-xs focus:outline-none focus:border-blue-600 focus:ring-1 focus:ring-blue-600"
              />
              <button
                type="button"
                onClick={() => handleConnectMongo(customMongoUri)}
                disabled={connectingDb || !customMongoUri.trim()}
                className="px-4 py-2 bg-[#2563EB] hover:bg-[#1E3A8A] text-white rounded-xl font-semibold text-xs transition disabled:opacity-50 flex items-center space-x-1.5 shadow-sm"
              >
                {connectingDb && <RefreshCw className="w-3.5 h-3.5 animate-spin" />}
                <span>{connectingDb ? 'Connecting...' : 'Connect'}</span>
              </button>
            </div>
          </div>

          {/* Connection Feedback Message */}
          {dbConnectMsg && (
            <div className={`p-3 rounded-xl border text-xs font-semibold flex items-start space-x-2 ${
              dbConnectMsg.success
                ? 'bg-emerald-50 border-emerald-200 text-emerald-700'
                : 'bg-red-50 border-red-200 text-red-700'
            }`}>
              {dbConnectMsg.success ? <CheckCircle2 className="w-4 h-4 shrink-0 mt-0.5" /> : <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" />}
              <span>{dbConnectMsg.text}</span>
            </div>
          )}
        </div>
      </Modal>

      {/* Auth & Security Session Monitor Modal */}
      <Modal
        isOpen={authModalOpen}
        onClose={() => setAuthModalOpen(false)}
        title="Authentication & Security Session Monitor"
      >
        <div className="space-y-4 text-xs">
          {/* Active User Security Credentials */}
          <div className="p-4 rounded-2xl bg-slate-50 border border-slate-200 space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2.5">
                <div className="w-8 h-8 rounded-xl bg-[#1E3A8A] flex items-center justify-center font-bold text-white shadow-sm">
                  {user?.full_name?.charAt(0) || 'U'}
                </div>
                <div>
                  <div className="font-bold text-slate-900 text-sm">{user?.full_name || 'Authenticated Executive'}</div>
                  <div className="text-slate-500 font-mono text-[11px]">{user?.email}</div>
                </div>
              </div>

              <span className="px-2.5 py-1 rounded-full text-[10px] font-mono font-bold bg-emerald-50 text-emerald-700 border border-emerald-200 flex items-center space-x-1">
                <ShieldCheck className="w-3 h-3 text-emerald-600" />
                <span>JWT SIGNED & VERIFIED</span>
              </span>
            </div>

            <div className="grid grid-cols-2 gap-3 pt-2 border-t border-slate-200 text-[11px]">
              <div>
                <span className="text-slate-400 font-bold block">Assigned Role</span>
                <span className="text-[#2563EB] font-semibold capitalize">{user?.role?.replace('_', ' ') || 'Brand Manager'}</span>
              </div>
              <div>
                <span className="text-slate-400 font-bold block">Organization</span>
                <span className="text-slate-700">{user?.organization || 'Enterprise Brandpulse Suite'}</span>
              </div>
            </div>
          </div>

          {/* MongoDB Login Audit Logs Header */}
          <div className="flex items-center justify-between pt-1">
            <div className="flex items-center space-x-2">
              <Key className="w-4 h-4 text-amber-500" />
              <h3 className="text-xs font-bold text-slate-800 uppercase tracking-wider">
                MongoDB Login Audit Trail ('auth_logs')
              </h3>
            </div>
            <button
              onClick={fetchAuditLogs}
              className="p-1.5 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-600 transition"
              title="Refresh Audit Logs"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${loadingAuditLogs ? 'animate-spin text-[#2563EB]' : ''}`} />
            </button>
          </div>

          {/* Audit Logs List */}
          <div className="max-h-56 overflow-y-auto space-y-2 pr-1">
            {loadingAuditLogs ? (
              <div className="p-6 text-center text-slate-500">Loading MongoDB audit records...</div>
            ) : auditLogs.length === 0 ? (
              <div className="p-6 text-center text-slate-400">No login audit events recorded yet.</div>
            ) : (
              auditLogs.map((log) => (
                <div
                  key={log.id}
                  className="p-3 rounded-xl bg-slate-50 border border-slate-200 flex items-center justify-between text-[11px]"
                >
                  <div className="space-y-0.5">
                    <div className="flex items-center space-x-2">
                      <span className="font-semibold text-slate-900">{log.full_name}</span>
                      <span className="text-slate-500 font-mono text-[10px]">({log.email})</span>
                      <span className="text-[9px] px-1.5 py-0.2 rounded bg-blue-50 text-[#2563EB] font-mono border border-blue-200">
                        {log.auth_method}
                      </span>
                    </div>
                    <div className="text-slate-500 text-[10px] flex items-center space-x-2">
                      <span>IP: <strong className="text-slate-700 font-mono">{log.ip_address}</strong></span>
                      <span>•</span>
                      <span className="truncate max-w-[200px]">{log.user_agent}</span>
                    </div>
                  </div>

                  <div className="text-right font-mono text-[10px] text-slate-500 shrink-0">
                    <div className="text-emerald-600 font-bold">{log.status}</div>
                    <div>{log.login_date} {log.login_time}</div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </Modal>

      {/* Brand Deletion Confirmation Modal */}
      <Modal
        isOpen={!!brandToDelete}
        onClose={() => {
          if (!deletingBrand) setBrandToDelete(null);
        }}
        title="Delete Monitored Brand"
        maxWidth="max-w-md"
      >
        <div className="space-y-4">
          <div className="p-3.5 bg-red-50 border border-red-200 rounded-2xl flex items-start space-x-3">
            <AlertTriangle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
            <div className="text-xs text-red-800 space-y-1">
              <p className="font-bold text-red-900">This action cannot be undone.</p>
              <p>
                Are you sure you want to delete <strong className="text-red-950 font-bold underline">{brandToDelete?.name}</strong>?
              </p>
            </div>
          </div>

          <p className="text-xs text-slate-600 leading-relaxed">
            Deleting this brand will permanently remove all associated intelligence data, monitored mentions, sentiment timelines, crisis alerts, and summaries from MongoDB.
          </p>

          <div className="flex items-center justify-end space-x-3 pt-3 border-t border-slate-100">
            <button
              type="button"
              disabled={deletingBrand}
              onClick={() => setBrandToDelete(null)}
              className="px-4 py-2 rounded-xl border border-slate-200 text-xs font-semibold text-slate-700 hover:bg-slate-50 transition"
            >
              Cancel
            </button>
            <button
              type="button"
              disabled={deletingBrand}
              onClick={handleDeleteBrand}
              className="px-4 py-2 rounded-xl bg-red-600 hover:bg-red-700 text-white text-xs font-bold shadow-sm transition flex items-center space-x-2 disabled:opacity-50"
            >
              {deletingBrand ? (
                <>
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  <span>Deleting...</span>
                </>
              ) : (
                <>
                  <Trash2 className="w-3.5 h-3.5" />
                  <span>Delete Brand</span>
                </>
              )}
            </button>
          </div>
        </div>
      </Modal>
    </header>
  );
};

export default Navbar;
