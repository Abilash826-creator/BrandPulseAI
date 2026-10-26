import React, { useState, useEffect } from 'react';
import { googleAPI } from '../../services/api';
import { 
  Star, 
  MapPin, 
  RefreshCw, 
  CheckCircle2, 
  AlertCircle, 
  Loader2, 
  ExternalLink 
} from 'lucide-react';

const GoogleBusinessSettingsCard = ({ activeBrand }) => {
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [placeId, setPlaceId] = useState('');
  const [mapsUrl, setMapsUrl] = useState('');
  const [locationName, setLocationName] = useState('');
  const [msg, setMsg] = useState('');
  const [error, setError] = useState('');

  const fetchStatus = async () => {
    if (!activeBrand) {
      setLoading(false);
      return;
    }
    setLoading(true);
    try {
      const res = await googleAPI.getStatus(activeBrand.id);
      setStatus(res.data);
      if (res.data?.place_id) setPlaceId(res.data.place_id);
      if (res.data?.maps_url) setMapsUrl(res.data.maps_url);
      if (res.data?.location_name) setLocationName(res.data.location_name);
    } catch (err) {
      console.error('Failed to load Google status:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStatus();
  }, [activeBrand]);

  const handleConnect = async (e) => {
    e.preventDefault();
    if (!activeBrand) return;
    setSaving(true);
    setError('');
    setMsg('');
    try {
      const res = await googleAPI.connect({
        brand_id: activeBrand.id,
        place_id: placeId.trim() || undefined,
        maps_url: mapsUrl.trim() || undefined,
        location_name: locationName.trim() || undefined
      });
      setMsg(res.data?.message || 'Google Business Profile connected!');
      fetchStatus();
      setTimeout(() => setMsg(''), 4500);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to connect Google Business Profile.');
    } finally {
      setSaving(false);
    }
  };

  const handleSync = async () => {
    if (!activeBrand) return;
    setSyncing(true);
    setError('');
    setMsg('');
    try {
      const res = await googleAPI.sync(activeBrand.id);
      setMsg(`✓ ${res.data?.message || 'Reviews synced successfully!'}`);
      fetchStatus();
      setTimeout(() => setMsg(''), 4500);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to sync Google Reviews.');
    } finally {
      setSyncing(false);
    }
  };

  return (
    <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-5">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-100 pb-4">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-xl bg-blue-50 border border-blue-200 flex items-center justify-center text-blue-600 shadow-xs">
            <Star className="w-5 h-5 fill-amber-400 text-amber-500" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h3 className="text-sm font-bold text-slate-900 tracking-tight">
                Google Business Profile & Maps Reviews
              </h3>
            </div>
            <p className="text-xs text-slate-500 mt-0.5">
              Pull real customer reviews, ratings (1-5 stars), and post owner replies to Google Maps.
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          {status?.is_connected ? (
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

      {error && (
        <div className="p-3.5 rounded-xl bg-red-50 border border-red-200 text-red-700 text-xs flex items-center space-x-2">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {msg && (
        <div className="p-3.5 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs flex items-center space-x-2 animate-fade-in">
          <CheckCircle2 className="w-4 h-4 shrink-0 text-[#16A34A]" />
          <span>{msg}</span>
        </div>
      )}

      {loading ? (
        <div className="py-6 flex items-center justify-center space-x-2 text-slate-500 text-xs">
          <Loader2 className="w-4 h-4 animate-spin text-[#2563EB]" />
          <span>Checking Google Business Profile status...</span>
        </div>
      ) : (
        <form onSubmit={handleConnect} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Google Place ID or Maps CID
              </label>
              <input
                type="text"
                value={placeId}
                onChange={(e) => setPlaceId(e.target.value)}
                placeholder="e.g. ChIJN1t_tDeuEmsRUsoyG83frY4 or sample"
                className="w-full text-xs p-2.5 bg-white border border-slate-200 rounded-xl text-slate-900 focus:outline-none focus:border-blue-600"
              />
              <span className="text-[10px] text-slate-400 mt-0.5 block">
                Found in Google Maps URL or Google Place ID Finder
              </span>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Google Maps Public Listing URL (Optional)
              </label>
              <input
                type="text"
                value={mapsUrl}
                onChange={(e) => setMapsUrl(e.target.value)}
                placeholder="https://maps.google.com/?cid=..."
                className="w-full text-xs p-2.5 bg-white border border-slate-200 rounded-xl text-slate-900 focus:outline-none focus:border-blue-600"
              />
              <span className="text-[10px] text-slate-400 mt-0.5 block">
                Link to your business on Google Maps
              </span>
            </div>
          </div>

          <div className="flex items-center justify-between pt-2 border-t border-slate-100 flex-wrap gap-3">
            <div className="text-xs text-slate-500">
              {status?.total_reviews_synced !== undefined && (
                <span>Total Google Reviews Synced: <strong className="font-bold text-slate-800">{status.total_reviews_synced}</strong></span>
              )}
            </div>

            <div className="flex items-center space-x-2">
              <button
                type="button"
                onClick={handleSync}
                disabled={syncing}
                className="px-3.5 py-2 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold text-xs transition flex items-center space-x-1.5 border border-slate-200 disabled:opacity-50"
              >
                {syncing ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <RefreshCw className="w-3.5 h-3.5" />}
                <span>{syncing ? 'Syncing...' : 'Sync Reviews Now'}</span>
              </button>

              <button
                type="submit"
                disabled={saving}
                className="px-4 py-2 rounded-xl bg-[#2563EB] hover:bg-[#1E3A8A] text-white font-semibold text-xs shadow-sm transition flex items-center space-x-1.5 disabled:opacity-50"
              >
                {saving && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
                <span>Save Google Profile</span>
              </button>
            </div>
          </div>
        </form>
      )}
    </div>
  );
};

export default GoogleBusinessSettingsCard;
