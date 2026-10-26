import React, { useState } from 'react';
import { 
  Flame, 
  CheckCircle2, 
  Copy, 
  ExternalLink, 
  Key, 
  Settings, 
  X, 
  Save, 
  RotateCcw,
  AlertCircle
} from 'lucide-react';
import { 
  getActiveFirebaseConfig, 
  saveActiveFirebaseConfig, 
  isCustomFirebaseConfigured 
} from '../../services/firebase';

const FirebaseConfigModal = ({ isOpen, onClose }) => {
  const [config, setConfig] = useState(getActiveFirebaseConfig());
  const [copied, setCopied] = useState(false);
  const [savedSuccess, setSavedSuccess] = useState(false);
  const isCustom = isCustomFirebaseConfigured();

  if (!isOpen) return null;

  const handleSave = (e) => {
    e.preventDefault();
    saveActiveFirebaseConfig(config);
    setSavedSuccess(true);
    setTimeout(() => {
      setSavedSuccess(false);
      onClose();
    }, 1200);
  };

  const handleResetDefaults = () => {
    localStorage.removeItem('brandpulse_firebase_config');
    window.location.reload();
  };

  const copyConfigJson = () => {
    navigator.clipboard.writeText(JSON.stringify(config, null, 2));
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-xs animate-fade-in font-sans">
      <div className="bg-white rounded-3xl border border-slate-200 shadow-2xl max-w-lg w-full overflow-hidden text-slate-800 flex flex-col max-h-[90vh]">
        
        {/* Header */}
        <div className="bg-gradient-to-r from-amber-500 via-orange-500 to-amber-600 p-5 text-white flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-white/20 rounded-xl backdrop-blur-xs">
              <Flame className="w-6 h-6 text-white animate-pulse" />
            </div>
            <div>
              <h3 className="font-extrabold text-base tracking-tight">Firebase Authentication Engine</h3>
              <p className="text-[11px] text-amber-100 font-medium">Configure credentials, Google OAuth & Project ID</p>
            </div>
          </div>
          <button 
            onClick={onClose}
            className="p-1.5 rounded-full hover:bg-white/20 transition text-white/80 hover:text-white"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Body */}
        <div className="p-6 overflow-y-auto space-y-4 text-xs">
          
          {/* Status Alert */}
          <div className={`p-3.5 rounded-2xl border flex items-center justify-between ${
            isCustom 
              ? 'bg-emerald-50 border-emerald-200 text-emerald-900' 
              : 'bg-blue-50 border-blue-200 text-blue-900'
          }`}>
            <div className="flex items-center space-x-2.5">
              <div className={`w-2.5 h-2.5 rounded-full ${isCustom ? 'bg-emerald-500 animate-ping' : 'bg-blue-500'}`} />
              <div>
                <div className="font-bold text-xs">
                  {isCustom ? "Custom Firebase Project Connected" : "Pre-Configured Enterprise Firebase Mode"}
                </div>
                <div className="text-[10px] text-slate-500">
                  Project: <span className="font-mono font-semibold">{config.projectId}</span>
                </div>
              </div>
            </div>
            <span className="px-2 py-0.5 rounded-full bg-white text-[10px] font-bold border shadow-2xs">
              Ready
            </span>
          </div>

          <p className="text-slate-600 leading-relaxed text-[11px]">
            BrandPulse AI integrates with <strong>Firebase Auth</strong> for enterprise Google OAuth sign-in, self-service email authentication, token encryption, and automated session syncing with MongoDB.
          </p>

          <form onSubmit={handleSave} className="space-y-3">
            <div className="space-y-1">
              <label className="font-bold text-slate-700 flex items-center justify-between">
                <span>Firebase API Key (apiKey)</span>
                <Key className="w-3 h-3 text-slate-400" />
              </label>
              <input
                type="text"
                value={config.apiKey || ''}
                onChange={(e) => setConfig({ ...config, apiKey: e.target.value })}
                required
                className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 text-slate-900 font-mono text-[11px] focus:bg-white focus:outline-none focus:border-amber-500"
                placeholder="AIzaSy..."
              />
            </div>

            <div className="grid grid-cols-2 gap-2">
              <div className="space-y-1">
                <label className="font-bold text-slate-700">Auth Domain</label>
                <input
                  type="text"
                  value={config.authDomain || ''}
                  onChange={(e) => setConfig({ ...config, authDomain: e.target.value })}
                  required
                  className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 text-slate-900 font-mono text-[11px] focus:bg-white focus:outline-none focus:border-amber-500"
                  placeholder="your-app.firebaseapp.com"
                />
              </div>

              <div className="space-y-1">
                <label className="font-bold text-slate-700">Project ID</label>
                <input
                  type="text"
                  value={config.projectId || ''}
                  onChange={(e) => setConfig({ ...config, projectId: e.target.value })}
                  required
                  className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 text-slate-900 font-mono text-[11px] focus:bg-white focus:outline-none focus:border-amber-500"
                  placeholder="your-project-id"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-2">
              <div className="space-y-1">
                <label className="font-bold text-slate-700">App ID</label>
                <input
                  type="text"
                  value={config.appId || ''}
                  onChange={(e) => setConfig({ ...config, appId: e.target.value })}
                  className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 text-slate-900 font-mono text-[11px] focus:bg-white focus:outline-none focus:border-amber-500"
                  placeholder="1:123456789:web:abcdef"
                />
              </div>

              <div className="space-y-1">
                <label className="font-bold text-slate-700">Storage Bucket</label>
                <input
                  type="text"
                  value={config.storageBucket || ''}
                  onChange={(e) => setConfig({ ...config, storageBucket: e.target.value })}
                  className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 text-slate-900 font-mono text-[11px] focus:bg-white focus:outline-none focus:border-amber-500"
                  placeholder="your-app.appspot.com"
                />
              </div>
            </div>

            {savedSuccess && (
              <div className="p-2.5 rounded-xl bg-emerald-50 text-emerald-800 font-semibold text-center border border-emerald-200 flex items-center justify-center space-x-1.5 animate-fade-in">
                <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                <span>Configuration Saved & Active!</span>
              </div>
            )}

            <div className="flex items-center space-x-2 pt-2">
              <button
                type="submit"
                className="flex-1 py-2.5 px-4 rounded-xl bg-gradient-to-r from-amber-500 to-orange-600 hover:from-amber-600 hover:to-orange-700 text-white font-bold shadow-md transition flex items-center justify-center space-x-2"
              >
                <Save className="w-3.5 h-3.5" />
                <span>Save Firebase Config</span>
              </button>

              <button
                type="button"
                onClick={handleResetDefaults}
                className="py-2.5 px-3 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold transition flex items-center space-x-1.5"
                title="Reset to default configuration"
              >
                <RotateCcw className="w-3.5 h-3.5" />
                <span>Reset</span>
              </button>

              <button
                type="button"
                onClick={copyConfigJson}
                className="py-2.5 px-3 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold transition flex items-center space-x-1.5"
                title="Copy config JSON"
              >
                <Copy className="w-3.5 h-3.5" />
                <span>{copied ? "Copied!" : "Copy"}</span>
              </button>
            </div>
          </form>

        </div>

        {/* Footer info */}
        <div className="bg-slate-50 p-3.5 px-6 border-t border-slate-100 text-[11px] text-slate-500 flex items-center justify-between">
          <span>Firebase Web SDK v11.x Active</span>
          <a 
            href="https://console.firebase.google.com" 
            target="_blank" 
            rel="noreferrer"
            className="text-amber-600 hover:text-amber-700 font-bold flex items-center space-x-1"
          >
            <span>Firebase Console</span>
            <ExternalLink className="w-3 h-3" />
          </a>
        </div>

      </div>
    </div>
  );
};

export default FirebaseConfigModal;
