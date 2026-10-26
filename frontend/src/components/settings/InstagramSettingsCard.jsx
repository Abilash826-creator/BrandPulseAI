import React from 'react';
import { 
  Instagram, 
  RefreshCw, 
  Unlink, 
  ShieldCheck, 
  Clock, 
  CheckCircle2, 
  AlertCircle, 
  Loader2 
} from 'lucide-react';

const InstagramSettingsCard = ({
  igStatus,
  igLoading,
  igError,
  syncSuccessMsg,
  syncing,
  handleConnectInstagram,
  handleSyncInstagramNow,
  handleDisconnectInstagram
}) => {
  return (
    <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-5">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-100 pb-4">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-amber-500 via-rose-500 to-purple-600 flex items-center justify-center text-white shadow-xs">
            <Instagram className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h3 className="text-sm font-bold text-slate-900 tracking-tight">
                Instagram Account Connection
              </h3>
            </div>
            <p className="text-xs text-slate-500 mt-0.5">
              Connect your Instagram Business or Professional account to pull customer comments and posts.
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          {igStatus?.is_connected ? (
            <span className="inline-flex items-center space-x-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-50 text-[#16A34A] border border-emerald-200">
              <div className="w-2 h-2 rounded-full bg-[#16A34A] animate-pulse" />
              <span>Connected</span>
            </span>
          ) : (
            <span className="inline-flex items-center space-x-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-slate-100 text-slate-600 border border-slate-200">
              <div className="w-2 h-2 rounded-full bg-slate-400" />
              <span>Not Connected</span>
            </span>
          )}
        </div>
      </div>

      {igError && (
        <div className="p-3.5 rounded-xl bg-red-50 border border-red-200 text-red-700 text-xs flex items-center space-x-2">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>{igError}</span>
        </div>
      )}

      {syncSuccessMsg && (
        <div className="p-3.5 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs flex items-center space-x-2 animate-fade-in">
          <CheckCircle2 className="w-4 h-4 shrink-0 text-[#16A34A]" />
          <span>{syncSuccessMsg}</span>
        </div>
      )}

      {igLoading ? (
        <div className="py-6 flex items-center justify-center space-x-2 text-slate-500 text-xs">
          <Loader2 className="w-4 h-4 animate-spin text-[#2563EB]" />
          <span>Verifying Meta Graph API status...</span>
        </div>
      ) : igStatus?.is_connected ? (
        /* Connected State Details */
        <div className="space-y-4 pt-1">
          <div className="p-4 rounded-2xl bg-slate-50 border border-slate-200 flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div className="flex items-center space-x-3.5">
              <img
                src={igStatus.profile_picture_url || `https://api.dicebear.com/7.x/bottts/svg?seed=${igStatus.instagram_username}`}
                alt={igStatus.account_name}
                className="w-12 h-12 rounded-xl bg-white border border-slate-200 object-cover shadow-xs"
              />
              <div>
                <div className="flex items-center space-x-2">
                  <span className="font-bold text-slate-900 text-sm">{igStatus.account_name}</span>
                  <span className="text-xs font-mono text-[#2563EB] bg-blue-50 px-2 py-0.5 rounded-md border border-blue-200">
                    @{igStatus.instagram_username}
                  </span>
                </div>
                <div className="flex items-center space-x-3 text-[11px] text-slate-500 mt-1 flex-wrap gap-1">
                  <span>Account ID: <strong className="font-mono text-slate-700">{igStatus.instagram_business_account_id}</strong></span>
                  <span>•</span>
                  <span>Followers: <strong className="text-slate-700">{igStatus.followers_count?.toLocaleString()}</strong></span>
                </div>
              </div>
            </div>

            {/* Action Buttons: Sync Now & Disconnect */}
            <div className="flex items-center space-x-2.5">
              <button
                type="button"
                onClick={handleSyncInstagramNow}
                disabled={syncing}
                className="px-3.5 py-2 rounded-xl bg-[#2563EB] hover:bg-[#1E3A8A] text-white text-xs font-bold transition flex items-center space-x-1.5 shadow-xs disabled:opacity-50"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${syncing ? 'animate-spin' : ''}`} />
                <span>{syncing ? 'Syncing...' : 'Sync Now'}</span>
              </button>

              <button
                type="button"
                onClick={handleDisconnectInstagram}
                className="px-3 py-2 rounded-xl bg-white hover:bg-red-50 text-red-600 border border-slate-200 hover:border-red-200 text-xs font-semibold transition flex items-center space-x-1.5 shadow-xs"
              >
                <Unlink className="w-3.5 h-3.5" />
                <span>Disconnect</span>
              </button>
            </div>
          </div>

          {/* Permissions & Sync Timestamp info */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
            <div className="p-3 rounded-xl bg-white border border-slate-200 flex items-start space-x-2.5">
              <ShieldCheck className="w-4 h-4 text-[#16A34A] shrink-0 mt-0.5" />
              <div>
                <span className="font-semibold text-slate-800 block">Granted Meta Permissions</span>
                <div className="flex flex-wrap gap-1 mt-1.5">
                  {(igStatus.permissions || []).map((perm) => (
                    <span key={perm} className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-100 text-slate-700 border border-slate-200">
                      {perm}
                    </span>
                  ))}
                </div>
              </div>
            </div>

            <div className="p-3 rounded-xl bg-white border border-slate-200 flex items-center justify-between">
              <div className="flex items-center space-x-2 text-slate-600">
                <Clock className="w-4 h-4 text-[#2563EB]" />
                <span>Last Synchronized:</span>
              </div>
              <span className="font-mono text-slate-800 font-semibold">
                {igStatus.last_synced_at ? new Date(igStatus.last_synced_at).toLocaleString() : 'Just now'}
              </span>
            </div>
          </div>
        </div>
      ) : (
        /* Disconnected State - Connect CTA */
        <div className="p-6 rounded-2xl bg-gradient-to-br from-slate-50 to-blue-50/30 border border-slate-200 text-center space-y-3">
          <div className="max-w-md mx-auto space-y-1.5">
            <h4 className="text-xs font-bold text-slate-900">
              Connect your Meta Instagram Business Account
            </h4>
            <p className="text-[11px] text-slate-500 leading-relaxed">
              Seamlessly ingest official business media, customer comments, tagged posts, and Reels with automatic AI sentiment, topic modeling, and product aspect extraction.
            </p>
          </div>

          <button
            type="button"
            onClick={handleConnectInstagram}
            className="px-5 py-2.5 rounded-xl bg-gradient-to-r from-rose-600 to-purple-600 hover:from-rose-700 hover:to-purple-700 text-white font-bold text-xs shadow-sm transition inline-flex items-center space-x-2"
          >
            <Instagram className="w-4 h-4" />
            <span>Connect Instagram Business Account</span>
          </button>
        </div>
      )}
    </div>
  );
};

export default InstagramSettingsCard;
