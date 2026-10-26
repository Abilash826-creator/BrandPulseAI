import React, { useState, useEffect } from 'react';
import { useBrand } from '../context/BrandContext';
import { brandsAPI, instagramAPI } from '../services/api';
import InstagramSettingsCard from '../components/settings/InstagramSettingsCard';
import GoogleBusinessSettingsCard from '../components/settings/GoogleBusinessSettingsCard';
import BrandProfileForm from '../components/settings/BrandProfileForm';

import LocationsManager from '../components/settings/LocationsManager';
import BrandDangerZone from '../components/settings/BrandDangerZone';
import { CheckCircle2, Building, Loader2 } from 'lucide-react';

const BrandSettings = () => {
  const { activeBrand, refreshBrands, deleteBrand, loading: brandLoading } = useBrand();

  const [formData, setFormData] = useState({
    name: '',
    business_type: 'restaurant',
    industry: '',
    description: '',
    topics: [],
    products: [],
    keywords: [],
    hashtags: [],
    social_handles: {},
    competitors: [],
    crisis_threshold_negative: 0.35,
    notify_bad_reviews: true,
    notify_weekly_summary: true,
    notify_spike: true,
    notification_email: '',
    notification_phone: '',
    weekly_digest_day: 'Monday',
    weekly_digest_time: '09:00'
  });

  const [productInput, setProductInput] = useState('');
  const [keywordInput, setKeywordInput] = useState('');
  const [hashtagInput, setHashtagInput] = useState('');
  const [competitorInput, setCompetitorInput] = useState('');
  const [saving, setSaving] = useState(false);
  const [savedSuccess, setSavedSuccess] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [deleting, setDeleting] = useState(false);

  // Instagram Connection State
  const [igStatus, setIgStatus] = useState(null);
  const [igLoading, setIgLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [syncSuccessMsg, setSyncSuccessMsg] = useState('');
  const [igError, setIgError] = useState('');

  // Check URL query parameters for OAuth redirect callback
  useEffect(() => {
    const queryParams = new URLSearchParams(window.location.search);
    const code = queryParams.get('code');
    const brandIdParam = queryParams.get('brand_id');

    if (code && activeBrand && (brandIdParam === activeBrand.id || !brandIdParam)) {
      handleCompleteOAuth(code);
      window.history.replaceState({}, document.title, window.location.pathname);
    }
  }, [activeBrand]);

  const fetchInstagramStatus = async () => {
    if (!activeBrand) {
      setIgLoading(false);
      return;
    }
    setIgLoading(true);
    try {
      const res = await instagramAPI.getStatus(activeBrand.id);
      setIgStatus(res.data);
    } catch (err) {
      console.error("Instagram status error:", err);
      setIgStatus({ is_connected: false });
    } finally {
      setIgLoading(false);
    }
  };

  useEffect(() => {
    if (activeBrand) {
      setFormData({
        name: activeBrand.name || '',
        business_type: activeBrand.business_type || 'restaurant',
        industry: activeBrand.industry || '',
        description: activeBrand.description || '',
        topics: activeBrand.topics || [],
        products: activeBrand.products || [],
        keywords: activeBrand.keywords || [],
        hashtags: activeBrand.hashtags || [],
        social_handles: activeBrand.social_handles || {},
        competitors: activeBrand.competitors || [],
        crisis_threshold_negative: activeBrand.crisis_threshold_negative || 0.35,
        notify_bad_reviews: activeBrand.notify_bad_reviews !== false,
        notify_weekly_summary: activeBrand.notify_weekly_summary !== false,
        notify_spike: activeBrand.notify_spike !== false,
        notification_email: activeBrand.notification_email || '',
        notification_phone: activeBrand.notification_phone || '',
        weekly_digest_day: activeBrand.weekly_digest_day || 'Monday',
        weekly_digest_time: activeBrand.weekly_digest_time || '09:00'
      });
      fetchInstagramStatus();
    }
  }, [activeBrand]);

  const handleConnectInstagram = async () => {
    if (!activeBrand) return;
    setIgError('');
    try {
      const res = await instagramAPI.getAuthUrl(activeBrand.id);
      if (res.data?.auth_url) {
        window.location.href = res.data.auth_url;
      }
    } catch (err) {
      console.error(err);
      setIgError('Failed to initiate Meta OAuth authorization.');
    }
  };

  const handleCompleteOAuth = async (code) => {
    setIgLoading(true);
    try {
      await instagramAPI.exchangeToken({
        brand_id: activeBrand.id,
        code: code
      });
      setSyncSuccessMsg('Meta Instagram account connected successfully!');
      setTimeout(() => setSyncSuccessMsg(''), 5000);
      fetchInstagramStatus();
    } catch (err) {
      console.error("Token exchange failed:", err);
      setIgError(err.response?.data?.detail || 'Failed to exchange Meta OAuth code.');
    } finally {
      setIgLoading(false);
    }
  };

  const handleSyncInstagramNow = async () => {
    if (!activeBrand) return;
    setSyncing(true);
    setSyncSuccessMsg('');
    try {
      const res = await instagramAPI.sync(activeBrand.id);
      setSyncSuccessMsg(res.data.message || 'Instagram media sync completed.');
      setTimeout(() => setSyncSuccessMsg(''), 5000);
      fetchInstagramStatus();
    } catch (err) {
      console.error(err);
      setIgError(err.response?.data?.detail || 'Instagram sync failed.');
    } finally {
      setSyncing(false);
    }
  };

  const handleDisconnectInstagram = async () => {
    if (!activeBrand) return;
    if (!window.confirm("Are you sure you want to disconnect this Instagram account?")) return;
    try {
      await instagramAPI.disconnect(activeBrand.id);
      setIgStatus({ is_connected: false });
      setSyncSuccessMsg('Instagram disconnected.');
      setTimeout(() => setSyncSuccessMsg(''), 4000);
    } catch (err) {
      console.error(err);
    }
  };

  const addProduct = () => {
    const val = productInput.trim();
    if (val && !formData.products.includes(val)) {
      setFormData({ ...formData, products: [...formData.products, val] });
      setProductInput('');
    }
  };

  const removeProduct = (prod) => {
    setFormData({ ...formData, products: formData.products.filter(p => p !== prod) });
  };

  const addKeyword = () => {
    const val = keywordInput.trim();
    if (val && !formData.keywords.includes(val)) {
      setFormData({ ...formData, keywords: [...formData.keywords, val] });
      setKeywordInput('');
    }
  };

  const removeKeyword = (kw) => {
    setFormData({ ...formData, keywords: formData.keywords.filter(k => k !== kw) });
  };

  const addHashtag = () => {
    let val = hashtagInput.trim();
    if (val) {
      if (!val.startsWith('#')) val = `#${val}`;
      if (!formData.hashtags.includes(val)) {
        setFormData({ ...formData, hashtags: [...formData.hashtags, val] });
        setHashtagInput('');
      }
    }
  };

  const removeHashtag = (tag) => {
    setFormData({ ...formData, hashtags: formData.hashtags.filter(t => t !== tag) });
  };

  const addCompetitor = () => {
    const val = competitorInput.trim();
    if (val && !formData.competitors.includes(val)) {
      setFormData({ ...formData, competitors: [...formData.competitors, val] });
      setCompetitorInput('');
    }
  };

  const removeCompetitor = (comp) => {
    setFormData({ ...formData, competitors: formData.competitors.filter(c => c !== comp) });
  };

  const handleSave = async (e) => {
    e.preventDefault();
    if (!activeBrand) return;
    setSaving(true);
    setSavedSuccess(false);
    try {
      await brandsAPI.update(activeBrand.id, formData);
      await refreshBrands();
      setSavedSuccess(true);
      setTimeout(() => setSavedSuccess(false), 4000);
    } catch (err) {
      console.error("Brand settings update error:", err);
    } finally {
      setSaving(false);
    }
  };

  const handleDeleteBrand = async () => {
    if (!activeBrand) return;
    setDeleting(true);
    try {
      await deleteBrand(activeBrand.id);
      setShowDeleteModal(false);
    } catch (err) {
      console.error("Delete brand error:", err);
    } finally {
      setDeleting(false);
    }
  };

  if (brandLoading && !activeBrand) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-slate-500 space-y-3">
        <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
        <p className="text-sm font-medium">Loading your business profile...</p>
      </div>
    );
  }

  if (!activeBrand) {
    return (
      <div className="bg-white p-8 rounded-2xl border border-slate-200 shadow-sm text-center max-w-xl mx-auto my-12 space-y-4">
        <div className="w-12 h-12 rounded-2xl bg-blue-50 text-blue-600 flex items-center justify-center mx-auto">
          <Building className="w-6 h-6" />
        </div>
        <h2 className="text-lg font-bold text-slate-900">No Business Profile Found</h2>
        <p className="text-xs text-slate-500 leading-relaxed">
          You don't have an active business profile yet. Set up a business or branch profile to start monitoring customer reviews, sentiment, and local competitor ratings.
        </p>
        <button
          type="button"
          onClick={() => window.location.href = '/onboarding'}
          className="px-5 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-bold text-xs shadow-sm transition inline-flex items-center space-x-2"
        >
          <span>Setup Business Profile</span>
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6 pb-12 animate-fade-in max-w-5xl">
      {/* Header */}
      <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-3">
            <h1 className="text-xl lg:text-2xl font-extrabold text-slate-900 tracking-tight">
              Business & Branch Settings
            </h1>
            <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-blue-50 text-blue-700 border border-blue-200">
              {activeBrand?.name}
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Manage your shop profile, multi-branch outlets, tracked topics, and customer feedback sources.
          </p>
        </div>

        {savedSuccess && (
          <div className="flex items-center space-x-1.5 px-3.5 py-2 rounded-xl bg-emerald-50 text-[#16A34A] border border-emerald-200 text-xs font-bold animate-fade-in shadow-xs">
            <CheckCircle2 className="w-4 h-4" />
            <span>Settings Saved!</span>
          </div>
        )}
      </div>

      {/* 1. Branch Locations Management Card */}
      <LocationsManager />

      {/* 2. Business Profile & Topics Form */}
      <BrandProfileForm
        formData={formData}
        setFormData={setFormData}
        productInput={productInput}
        setProductInput={setProductInput}
        addProduct={addProduct}
        removeProduct={removeProduct}
        keywordInput={keywordInput}
        setKeywordInput={setKeywordInput}
        addKeyword={addKeyword}
        removeKeyword={removeKeyword}
        hashtagInput={hashtagInput}
        setHashtagInput={setHashtagInput}
        addHashtag={addHashtag}
        removeHashtag={removeHashtag}
        competitorInput={competitorInput}
        setCompetitorInput={setCompetitorInput}
        addCompetitor={addCompetitor}
        removeCompetitor={removeCompetitor}
        handleSave={handleSave}
        saving={saving}
      />

      {/* 3. Google Business Profile & Maps Reviews */}
      <GoogleBusinessSettingsCard activeBrand={activeBrand} />

      {/* 4. Official Instagram Integration Card */}
      <InstagramSettingsCard

        igStatus={igStatus}
        igLoading={igLoading}
        igError={igError}
        syncSuccessMsg={syncSuccessMsg}
        syncing={syncing}
        handleConnectInstagram={handleConnectInstagram}
        handleSyncInstagramNow={handleSyncInstagramNow}
        handleDisconnectInstagram={handleDisconnectInstagram}
      />

      {/* Danger Zone: Delete Business */}
      <BrandDangerZone
        activeBrand={activeBrand}
        showDeleteModal={showDeleteModal}
        setShowDeleteModal={setShowDeleteModal}
        deleting={deleting}
        handleDeleteBrand={handleDeleteBrand}
      />
    </div>
  );
};

export default BrandSettings;
