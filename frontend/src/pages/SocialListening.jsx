import React, { useState, useEffect } from 'react';
import { useBrand } from '../context/BrandContext';
import { monitoringAPI, instagramAPI, googleAPI, facebookAPI } from '../services/api';
import { useMentionsQuery } from '../hooks/useMentionsQuery';
import FeedStream from '../components/dashboard/FeedStream';
import SocialListeningFilters from '../components/listening/SocialListeningFilters';
import ManualMentionModal from '../components/listening/ManualMentionModal';
import { 
  Radio, 
  Plus, 
  Play, 
  Pause, 
  Star, 
  Instagram, 
  MessageSquare,
  FileText,
  RefreshCw, 
  CheckCircle2,
  Loader2,
  AlertCircle
} from 'lucide-react';

const SocialListening = () => {
  const { activeBrand } = useBrand();

  const [platform, setPlatform] = useState('all');
  const [source, setSource] = useState('all');
  const [rating, setRating] = useState('all');
  const [sentiment, setSentiment] = useState('all');
  const [replied, setReplied] = useState('all');
  const [language, setLanguage] = useState('all');
  const [topic, setTopic] = useState('all');
  const [productFilter, setProductFilter] = useState('all');
  const [timeRange, setTimeRange] = useState('7d');
  const [search, setSearch] = useState('');
  const [autoStream, setAutoStream] = useState(false);

  // Syncing states
  const [syncingGoogle, setSyncingGoogle] = useState(false);
  const [syncingFacebook, setSyncingFacebook] = useState(false);
  const [syncingInstagram, setSyncingInstagram] = useState(false);
  const [syncBannerMsg, setSyncBannerMsg] = useState('');

  // Manual Ingestion Modal State
  const [injectModalOpen, setInjectModalOpen] = useState(false);
  const [injectForm, setInjectForm] = useState({
    platform: 'Google Reviews',
    author: 'Customer',
    author_handle: '@reviewer',
    author_followers: 50,
    media_type: 'REVIEW',
    content: 'Excellent food and quick service! Highly recommend this place.',
    rating: 5
  });
  const [injectLoading, setInjectLoading] = useState(false);

  // Determine effective platform/source query
  const effectiveSource = platform !== 'all' ? platform : (source !== 'all' ? source : undefined);

  const queryParams = {
    source: effectiveSource,
    rating: rating !== 'all' ? parseInt(rating, 10) : undefined,
    mood: sentiment !== 'all' ? sentiment : undefined,
    replied: replied !== 'all' ? (replied === 'replied') : undefined,
    language: language !== 'all' ? language : undefined,
    topic: topic !== 'all' ? topic : undefined,
    search: search.trim() || undefined,
    limit: 100
  };

  const { data, isLoading, error, refetch } = useMentionsQuery(queryParams, activeBrand?.id);

  let rawMentions = data?.mentions || [];

  // Filter product client-side if selected
  if (productFilter !== 'all') {
    rawMentions = rawMentions.filter(m => {
      const text = `${m.content || ''} ${m.matched_product || ''} ${m.product_detected || ''}`.toLowerCase();
      return text.includes(productFilter.toLowerCase());
    });
  }

  const mentions = rawMentions;

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    refetch();
  };

  useEffect(() => {
    if (!autoStream || !activeBrand) return;
    const interval = setInterval(() => {
      refetch();
    }, 10000);
    return () => clearInterval(interval);
  }, [autoStream, activeBrand, refetch]);

  const handleSyncGoogle = async () => {
    if (!activeBrand) return;
    setSyncingGoogle(true);
    try {
      const res = await googleAPI.sync(activeBrand.id);
      setSyncBannerMsg(`✓ ${res.data?.message || 'Google Reviews synced successfully!'}`);
      setTimeout(() => setSyncBannerMsg(''), 4500);
      refetch();
    } catch (err) {
      console.error(err);
      setSyncBannerMsg('Could not sync Google Reviews. Please check Place ID.');
      setTimeout(() => setSyncBannerMsg(''), 4000);
    } finally {
      setSyncingGoogle(false);
    }
  };

  const handleSyncFacebook = async () => {
    if (!activeBrand) return;
    setSyncingFacebook(true);
    try {
      const res = await facebookAPI.sync(activeBrand.id);
      setSyncBannerMsg(`✓ ${res.data?.message || 'Facebook Reviews synced successfully!'}`);
      setTimeout(() => setSyncBannerMsg(''), 4500);
      refetch();
    } catch (err) {
      console.error(err);
      setSyncBannerMsg('Could not sync Facebook Reviews.');
      setTimeout(() => setSyncBannerMsg(''), 4000);
    } finally {
      setSyncingFacebook(false);
    }
  };

  const handleSyncInstagram = async () => {
    if (!activeBrand) return;
    setSyncingInstagram(true);
    try {
      const res = await instagramAPI.sync(activeBrand.id);
      setSyncBannerMsg(`✓ ${res.data?.message || 'Instagram synced successfully!'}`);
      setTimeout(() => setSyncBannerMsg(''), 4500);
      refetch();
    } catch (err) {
      console.error(err);
      setSyncBannerMsg('Could not sync Instagram.');
      setTimeout(() => setSyncBannerMsg(''), 4000);
    } finally {
      setSyncingInstagram(false);
    }
  };

  const handleInjectMention = async (e) => {
    e.preventDefault();
    if (!injectForm.content.trim() || !activeBrand) return;
    setInjectLoading(true);
    try {
      await monitoringAPI.createMention({
        ...injectForm,
        brand_id: activeBrand.id,
        business_id: activeBrand.id,
        source: injectForm.platform
      });
      setInjectModalOpen(false);
      refetch();
    } catch (err) {
      console.error(err);
    } finally {
      setInjectLoading(false);
    }
  };

  // Small Business Specific Channel Tabs (Google, Facebook, Instagram, Pasted)
  const platformsList = [
    { id: 'all', label: 'All Customer Feedback', icon: Radio },
    { id: 'google', label: 'Google Reviews ⭐', icon: Star },
    { id: 'facebook', label: 'Facebook Reviews', icon: MessageSquare },
    { id: 'instagram', label: 'Instagram', icon: Instagram, isGradient: true },
    { id: 'pasted', label: 'Pasted Reviews', icon: FileText },
  ];

  const availableProducts = activeBrand?.products || [];

  return (
    <div className="space-y-6 pb-12 animate-fade-in">
      {/* Top Header */}
      <div className="bg-white p-4 sm:p-6 rounded-2xl border border-slate-200 shadow-sm flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-3">
            <h1 className="text-xl lg:text-2xl font-extrabold text-slate-900 tracking-tight">
              Customer Reviews
            </h1>
            <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-blue-50 text-[#2563EB] border border-blue-200">
              {mentions.length} Reviews
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Real feedback from Google Maps, Facebook, Instagram, and pasted offline reviews.
          </p>
        </div>

        {/* Action Controls & Sync Buttons */}
        <div className="flex items-center space-x-2 flex-wrap gap-2 w-full md:w-auto">
          {/* Quick Sync Google */}
          <button
            onClick={handleSyncGoogle}
            disabled={syncingGoogle}
            className="min-h-[40px] px-3 py-2 rounded-xl bg-blue-50 hover:bg-blue-100 text-blue-700 border border-blue-200 font-semibold text-xs shadow-2xs transition flex items-center space-x-1.5 disabled:opacity-50"
            title="Sync latest reviews from Google Business Profile"
          >
            {syncingGoogle ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Star className="w-3.5 h-3.5 fill-amber-400 text-amber-500" />}
            <span>Sync Google</span>
          </button>

          {/* Quick Sync Facebook */}
          <button
            onClick={handleSyncFacebook}
            disabled={syncingFacebook}
            className="min-h-[40px] px-3 py-2 rounded-xl bg-indigo-50 hover:bg-indigo-100 text-indigo-700 border border-indigo-200 font-semibold text-xs shadow-2xs transition flex items-center space-x-1.5 disabled:opacity-50"
            title="Sync Facebook page reviews"
          >
            {syncingFacebook ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <MessageSquare className="w-3.5 h-3.5 text-indigo-600" />}
            <span>Sync Facebook</span>
          </button>

          {/* Add Review Manually */}
          <button
            onClick={() => setInjectModalOpen(true)}
            className="min-h-[40px] px-3.5 py-2 rounded-xl bg-[#2563EB] hover:bg-[#1E3A8A] text-white font-semibold text-xs shadow-sm transition flex items-center space-x-1.5 ml-auto md:ml-0"
          >
            <Plus className="w-4 h-4" />
            <span>Add Review</span>
          </button>
        </div>
      </div>

      {/* Sync Status Toast/Banner */}
      {syncBannerMsg && (
        <div className="p-3.5 rounded-xl bg-emerald-50 border border-emerald-200 text-xs font-semibold text-[#16A34A] flex items-center space-x-2 shadow-xs animate-fade-in">
          <CheckCircle2 className="w-4 h-4 text-[#16A34A] shrink-0" />
          <span>{syncBannerMsg}</span>
        </div>
      )}

      {/* Small Business Filter Bar */}
      <SocialListeningFilters
        search={search}
        setSearch={setSearch}
        handleSearchSubmit={handleSearchSubmit}
        source={source}
        setSource={(val) => {
          setSource(val);
          setPlatform(val);
        }}
        rating={rating}
        setRating={setRating}
        sentiment={sentiment}
        setSentiment={setSentiment}
        replied={replied}
        setReplied={setReplied}
        language={language}
        setLanguage={setLanguage}
        topic={topic}
        setTopic={setTopic}
        productFilter={productFilter}
        setProductFilter={setProductFilter}
        availableProducts={availableProducts}
      />

      {/* Feed Stream */}
      {isLoading && !data ? (
        <div className="min-h-[40vh] flex flex-col items-center justify-center text-slate-500 space-y-3">
          <Loader2 className="w-7 h-7 animate-spin text-[#2563EB]" />
          <span className="text-xs font-semibold">Filtering reviews and customer feedback...</span>
        </div>
      ) : error ? (
        <div className="p-6 bg-red-50 border border-red-200 rounded-2xl text-red-700 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <AlertCircle className="w-5 h-5 text-red-600" />
            <span className="text-sm font-semibold">Could not load reviews. Please verify backend connection.</span>
          </div>
          <button
            onClick={() => refetch()}
            className="px-3 py-1.5 bg-red-600 text-white font-semibold text-xs rounded-xl hover:bg-red-700 transition"
          >
            Retry
          </button>
        </div>
      ) : (
        <FeedStream
          mentions={mentions}
          onRefresh={() => refetch()}
          onReplySuccess={() => refetch()}
        />
      )}

      {/* Custom Mention Modal */}
      <ManualMentionModal
        isOpen={injectModalOpen}
        onClose={() => setInjectModalOpen(false)}
        onSubmit={handleInjectMention}
        injectForm={injectForm}
        setInjectForm={setInjectForm}
        injectLoading={injectLoading}
      />
    </div>
  );
};

export default SocialListening;
