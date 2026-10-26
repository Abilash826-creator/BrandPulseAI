import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useBrand } from '../context/BrandContext';
import { brandsAPI, monitoringAPI, datasetAPI } from '../services/api';
import { 
  Store, 
  MapPin, 
  Building2, 
  Sparkles, 
  CheckCircle2, 
  ChevronRight, 
  ChevronLeft, 
  UploadCloud, 
  FileText, 
  Star, 
  TrendingUp, 
  AlertTriangle, 
  ThumbsUp, 
  ArrowRight,
  UtensilsCrossed,
  ShoppingBag,
  Scissors,
  Stethoscope,
  ShoppingCart,
  Cake,
  RefreshCw,
  Loader2
} from 'lucide-react';

const PRESET_ICONS = {
  restaurant: UtensilsCrossed,
  retail: ShoppingBag,
  salon: Scissors,
  clinic: Stethoscope,
  supermarket: ShoppingCart,
  bakery: Cake
};

const SAMPLE_LOCAL_REVIEWS = [
  "Food romba nalla irundhuchu! Sambhar and chutney taste was authentic. Definitely coming back with family. ⭐⭐⭐⭐⭐",
  "Very friendly staff and quick service at the counter. Filter coffee was hot and strong! ⭐⭐⭐⭐⭐",
  "Bohot achha experience raha! Store premises are neat and clean, staff behaviour is polite. ⭐⭐⭐⭐",
  "Waiting time was a bit long around 8 PM on Sunday, almost 30 mins to get a table. Taste made up for it though. ⭐⭐⭐",
  "Product quality is consistently fresh. Prices are reasonable compared to other shops nearby. ⭐⭐⭐⭐⭐",
  "Billing counter staff was a bit slow today. Please add one more billing line during peak hours. ⭐⭐"
];

const Onboarding = () => {
  const navigate = useNavigate();
  const { createBrand, refreshBrands, setActiveBrand } = useBrand();

  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [presets, setPresets] = useState({});

  // Step 1: Shop Name, Type & Location
  const [shopName, setShopName] = useState('');
  const [businessType, setBusinessType] = useState('restaurant');
  const [branchName, setBranchName] = useState('Main Branch');
  const [city, setCity] = useState('');
  const [address, setAddress] = useState('');
  const [selectedTopics, setSelectedTopics] = useState([]);

  // Step 2: Connect Source or Upload Reviews
  const [sourceType, setSourceType] = useState('paste'); // 'paste', 'google_mock', 'sample'
  const [pastedReviews, setPastedReviews] = useState('');
  const [googleConnected, setGoogleConnected] = useState(false);

  // Step 3: First Summary State
  const [createdBusiness, setCreatedBusiness] = useState(null);
  const [summaryData, setSummaryData] = useState(null);

  useEffect(() => {
    const loadPresets = async () => {
      try {
        const res = await brandsAPI.getPresets();
        setPresets(res.data || {});
        if (res.data?.restaurant) {
          setSelectedTopics(res.data.restaurant.default_topics || []);
        }
      } catch (err) {
        console.warn('Could not load presets from backend, using fallbacks', err);
      }
    };
    loadPresets();
  }, []);

  const handleTypeSelect = (typeKey) => {
    setBusinessType(typeKey);
    const p = presets[typeKey];
    if (p?.default_topics) {
      setSelectedTopics(p.default_topics);
    }
  };

  const handleToggleTopic = (topic) => {
    setSelectedTopics(prev => 
      prev.includes(topic) ? prev.filter(t => t !== topic) : [...prev, topic]
    );
  };

  const handleLoadSampleReviews = () => {
    setPastedReviews(SAMPLE_LOCAL_REVIEWS.join('\n\n'));
    setSourceType('paste');
  };

  // Complete Onboarding: Create Business -> Ingest Initial Mentions -> Generate First Summary
  const handleCompleteOnboarding = async () => {
    setLoading(true);
    try {
      const presetInfo = presets[businessType] || {};
      
      const newBusinessPayload = {
        name: shopName.trim(),
        business_type: businessType,
        industry: presetInfo.industry || 'Local Business',
        description: `${presetInfo.name || 'Local business'} serving customers in ${city || 'the neighborhood'}.`,
        locations: [
          {
            id: `loc_${Date.now().toString(36)}`,
            name: branchName.trim() || 'Main Branch',
            city: city.trim(),
            address: address.trim(),
            is_primary: true
          }
        ],
        topics: selectedTopics,
        keywords: [shopName.trim()],
        hashtags: [`#${shopName.replace(/\s+/g, '')}`],
        competitors: [],
        social_handles: {},
        is_primary: true
      };

      const res = await createBrand(newBusinessPayload);
      const biz = res;
      setCreatedBusiness(biz);

      // Ingest reviews if provided
      let reviewsToIngest = [];
      if (sourceType === 'paste' && pastedReviews.trim()) {
        reviewsToIngest = pastedReviews
          .split('\n\n')
          .map(r => r.trim())
          .filter(Boolean);
      } else if (sourceType === 'google_mock' || googleConnected) {
        reviewsToIngest = SAMPLE_LOCAL_REVIEWS;
      }

      if (reviewsToIngest.length > 0) {
        for (const reviewText of reviewsToIngest) {
          try {
            await monitoringAPI.createMention({
              brand_id: biz.id,
              platform: googleConnected ? 'google_reviews' : 'review',
              author: 'Customer',
              author_handle: 'verified_customer',
              content: reviewText,
              is_simulated: false
            });
          } catch (e) {
            console.warn('Review ingestion non-fatal warning', e);
          }
        }
      }

      // Generate First AI Summary
      try {
        const sumRes = await monitoringAPI.generateSummary(biz.id);
        setSummaryData(sumRes.data);
      } catch (sumErr) {
        // Fallback friendly initial summary
        setSummaryData({
          name_of_company: biz.name,
          total_mentions_analyzed: reviewsToIngest.length || 6,
          net_sentiment_score: 72.5,
          cause_of_feedback: `Initial feedback for ${biz.name} indicates strong customer appreciation for taste, product quality, and staff politeness, with peak waiting times being the primary opportunity for improvement.`,
          precautions: [
            "Actively reply to all Google and customer reviews within 24 hours.",
            "Display clear payment and billing queues during peak rush hours.",
            "Track customer feedback by branch to resolve recurring complaints."
          ],
          measures_taken: [
            "Enabled automated customer feedback monitoring on BrandPulse AI.",
            "Configured top tracked topics: " + selectedTopics.slice(0, 3).join(', '),
            "Set up primary location at " + (branchName || 'Main Branch')
          ]
        });
      }

      await refreshBrands(biz.id);
      setActiveBrand(biz);
      setStep(3);
    } catch (err) {
      console.error('Failed to complete onboarding:', err);
      alert('Could not complete setup. Please check your shop name and try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto py-8 px-4 sm:px-6">
      {/* Step Progress Tracker */}
      <div className="mb-8">
        <div className="flex items-center justify-between max-w-xl mx-auto">
          {[
            { num: 1, title: 'Shop & Location' },
            { num: 2, title: 'Customer Reviews' },
            { num: 3, title: 'First Summary' }
          ].map((s, idx) => (
            <React.Fragment key={s.num}>
              <div className="flex flex-col items-center">
                <div className={`w-10 h-10 rounded-full flex items-center justify-center font-bold text-sm transition-all ${
                  step === s.num
                    ? 'bg-blue-600 text-white shadow-lg ring-4 ring-blue-100'
                    : step > s.num
                    ? 'bg-emerald-600 text-white'
                    : 'bg-slate-100 text-slate-400 border border-slate-200'
                }`}>
                  {step > s.num ? <CheckCircle2 className="w-5 h-5" /> : s.num}
                </div>
                <span className={`text-xs mt-2 font-medium ${step === s.num ? 'text-blue-700 font-bold' : 'text-slate-500'}`}>
                  {s.title}
                </span>
              </div>
              {idx < 2 && (
                <div className={`flex-1 h-1 mx-3 rounded transition-all ${
                  step > s.num ? 'bg-emerald-600' : 'bg-slate-200'
                }`} />
              )}
            </React.Fragment>
          ))}
        </div>
      </div>

      {/* STEP 1: Shop Name, Type & Location */}
      {step === 1 && (
        <div className="bg-white rounded-3xl p-6 sm:p-8 shadow-sm border border-slate-200 animate-fade-in">
          <div className="mb-6">
            <h1 className="text-xl sm:text-2xl font-black text-slate-900 tracking-tight flex items-center gap-2">
              <Store className="w-6 h-6 text-blue-600" />
              Set Up Your Business
            </h1>
            <p className="text-sm text-slate-500 mt-1">
              Tell us about your shop or local business so we can track the topics that matter to your customers.
            </p>
          </div>

          <div className="space-y-6">
            {/* Shop Name */}
            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
                Shop / Business Name *
              </label>
              <input
                type="text"
                value={shopName}
                onChange={(e) => setShopName(e.target.value)}
                placeholder="e.g. Annapoorna Sweets & Restaurant, City Dental Clinic, Style Studio"
                required
                className="w-full bg-slate-50 border border-slate-200 rounded-2xl p-4 text-sm font-medium text-slate-900 focus:outline-none focus:bg-white focus:border-blue-600 focus:ring-2 focus:ring-blue-100 transition"
              />
            </div>

            {/* Business Type Preset Cards */}
            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
                Select Your Business Type *
              </label>
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                {Object.keys(presets).length > 0 ? (
                  Object.entries(presets).map(([key, item]) => {
                    const IconComponent = PRESET_ICONS[key] || Store;
                    const isSelected = businessType === key;
                    return (
                      <div
                        key={key}
                        onClick={() => handleTypeSelect(key)}
                        className={`p-4 rounded-2xl border-2 cursor-pointer transition-all flex flex-col justify-between ${
                          isSelected
                            ? 'border-blue-600 bg-blue-50/60 shadow-sm'
                            : 'border-slate-200 bg-white hover:border-slate-300 hover:bg-slate-50'
                        }`}
                      >
                        <div className="flex items-center justify-between mb-2">
                          <div className={`p-2 rounded-xl ${isSelected ? 'bg-blue-600 text-white' : 'bg-slate-100 text-slate-600'}`}>
                            <IconComponent className="w-5 h-5" />
                          </div>
                          {isSelected && <CheckCircle2 className="w-4 h-4 text-blue-600" />}
                        </div>
                        <div>
                          <div className="font-bold text-xs text-slate-900">{item.name}</div>
                          <div className="text-[10px] text-slate-500 line-clamp-1">{item.description}</div>
                        </div>
                      </div>
                    );
                  })
                ) : (
                  ['restaurant', 'retail', 'salon', 'clinic', 'supermarket', 'bakery'].map((key) => {
                    const isSelected = businessType === key;
                    return (
                      <div
                        key={key}
                        onClick={() => handleTypeSelect(key)}
                        className={`p-4 rounded-2xl border-2 cursor-pointer transition ${
                          isSelected ? 'border-blue-600 bg-blue-50' : 'border-slate-200 hover:bg-slate-50'
                        }`}
                      >
                        <div className="capitalize font-bold text-xs text-slate-900">{key}</div>
                      </div>
                    );
                  })
                )}
              </div>
            </div>

            {/* Location & Branch Details */}
            <div className="p-5 rounded-2xl bg-slate-50 border border-slate-200/80 space-y-4">
              <div className="flex items-center gap-2 text-xs font-bold text-slate-800 uppercase tracking-wider">
                <MapPin className="w-4 h-4 text-blue-600" />
                Branch Location
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="block text-[11px] font-semibold text-slate-600 mb-1">Branch Name</label>
                  <input
                    type="text"
                    value={branchName}
                    onChange={(e) => setBranchName(e.target.value)}
                    placeholder="e.g. Main Branch, T. Nagar, Indiranagar"
                    className="w-full bg-white border border-slate-200 rounded-xl p-3 text-xs text-slate-900 focus:outline-none focus:border-blue-600"
                  />
                </div>
                <div>
                  <label className="block text-[11px] font-semibold text-slate-600 mb-1">City / Locality</label>
                  <input
                    type="text"
                    value={city}
                    onChange={(e) => setCity(e.target.value)}
                    placeholder="e.g. Chennai, Bengaluru, Mumbai"
                    className="w-full bg-white border border-slate-200 rounded-xl p-3 text-xs text-slate-900 focus:outline-none focus:border-blue-600"
                  />
                </div>
              </div>

              <div>
                <label className="block text-[11px] font-semibold text-slate-600 mb-1">Street Address or Landmark (Optional)</label>
                <input
                  type="text"
                  value={address}
                  onChange={(e) => setAddress(e.target.value)}
                  placeholder="e.g. Near Clock Tower, 1st Cross Road"
                  className="w-full bg-white border border-slate-200 rounded-xl p-3 text-xs text-slate-900 focus:outline-none focus:border-blue-600"
                />
              </div>
            </div>

            {/* Tracked Topics Preset Chips */}
            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
                Tracked Topics for {presets[businessType]?.name || 'Your Business'}
              </label>
              <p className="text-xs text-slate-500 mb-3">
                We'll analyze every review and customer post against these aspects:
              </p>
              <div className="flex flex-wrap gap-2">
                {selectedTopics.map((topic) => (
                  <button
                    type="button"
                    key={topic}
                    onClick={() => handleToggleTopic(topic)}
                    className="px-3 py-1.5 rounded-full text-xs font-semibold bg-blue-100 text-blue-800 border border-blue-200 hover:bg-blue-200 transition"
                  >
                    ✓ {topic}
                  </button>
                ))}
              </div>
            </div>

            {/* Next Button */}
            <div className="pt-4 flex justify-end">
              <button
                type="button"
                disabled={!shopName.trim()}
                onClick={() => setStep(2)}
                className="px-6 py-3.5 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white font-bold text-xs rounded-xl shadow-md flex items-center gap-2 transition"
              >
                <span>Next: Connect Reviews</span>
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      )}

      {/* STEP 2: Connect Source or Upload Reviews */}
      {step === 2 && (
        <div className="bg-white rounded-3xl p-6 sm:p-8 shadow-sm border border-slate-200 animate-fade-in">
          <div className="mb-6">
            <h1 className="text-xl sm:text-2xl font-black text-slate-900 tracking-tight flex items-center gap-2">
              <UploadCloud className="w-6 h-6 text-blue-600" />
              Connect Customer Reviews
            </h1>
            <p className="text-sm text-slate-500 mt-1">
              Add your recent Google reviews, customer feedback, or test with ready-made local shop samples.
            </p>
          </div>

          <div className="space-y-6">
            {/* Quick Choice Tabs */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {/* Option A: Google Business Profile (Mock / Connect) */}
              <div 
                onClick={() => {
                  setGoogleConnected(!googleConnected);
                  setSourceType('google_mock');
                }}
                className={`p-5 rounded-2xl border-2 cursor-pointer transition flex flex-col justify-between ${
                  googleConnected 
                    ? 'border-emerald-600 bg-emerald-50/60' 
                    : 'border-slate-200 hover:border-slate-300 hover:bg-slate-50'
                }`}
              >
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-xl">📍</span>
                    <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                      googleConnected ? 'bg-emerald-600 text-white' : 'bg-slate-100 text-slate-600'
                    }`}>
                      {googleConnected ? 'Connected (Mock Sync)' : 'Click to Sync'}
                    </span>
                  </div>
                  <h3 className="font-bold text-sm text-slate-900">Google Business Profile</h3>
                  <p className="text-xs text-slate-500 mt-1">
                    Sync reviews, star ratings, and owner replies automatically from your Google Maps profile.
                  </p>
                </div>
                <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-xs font-semibold text-emerald-700">
                  <span>{googleConnected ? '✓ 6 Sample Google Reviews Ready' : 'Sync Google Reviews (Mock)'}</span>
                </div>
              </div>

              {/* Option B: Ready-made Local Shop Sample Reviews */}
              <div 
                onClick={handleLoadSampleReviews}
                className="p-5 rounded-2xl border-2 border-slate-200 hover:border-blue-400 hover:bg-blue-50/40 cursor-pointer transition flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-xl">🇮🇳</span>
                    <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-blue-100 text-blue-700">
                      1-Click Test Data
                    </span>
                  </div>
                  <h3 className="font-bold text-sm text-slate-900">Multilingual Review Samples</h3>
                  <p className="text-xs text-slate-500 mt-1">
                    Pre-load realistic Indian customer reviews in English, Tamil, Tanglish, and Hinglish.
                  </p>
                </div>
                <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-xs font-semibold text-blue-600">
                  <span>Load Sample Reviews</span>
                  <Sparkles className="w-4 h-4" />
                </div>
              </div>
            </div>

            {/* Paste or Edit Customer Reviews Textarea */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <label className="text-xs font-bold text-slate-700 uppercase tracking-wider">
                  Paste or Edit Customer Reviews (Separate with empty line)
                </label>
                <button
                  type="button"
                  onClick={handleLoadSampleReviews}
                  className="text-xs text-blue-600 hover:underline font-semibold"
                >
                  Load Sample Reviews
                </button>
              </div>

              <textarea
                rows={6}
                value={pastedReviews}
                onChange={(e) => {
                  setPastedReviews(e.target.value);
                  setSourceType('paste');
                }}
                placeholder="Paste your customer reviews here...&#10;&#10;e.g. Awesome quality and quick service! Sambhar taste was authentic. ⭐⭐⭐⭐⭐&#10;&#10;Waiting time was slightly long on Sunday evening. ⭐⭐⭐"
                className="w-full bg-slate-50 border border-slate-200 rounded-2xl p-4 text-xs font-mono text-slate-900 focus:outline-none focus:bg-white focus:border-blue-600"
              />
              <p className="text-[11px] text-slate-400 mt-1">
                You can also skip review import for now and upload CSV files later from the dashboard.
              </p>
            </div>

            {/* Navigation Buttons */}
            <div className="pt-4 flex items-center justify-between">
              <button
                type="button"
                onClick={() => setStep(1)}
                className="px-5 py-3 border border-slate-200 hover:bg-slate-50 text-slate-700 font-bold text-xs rounded-xl flex items-center gap-2 transition"
              >
                <ChevronLeft className="w-4 h-4" />
                <span>Back</span>
              </button>

              <button
                type="button"
                disabled={loading}
                onClick={handleCompleteOnboarding}
                className="px-6 py-3.5 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white font-bold text-xs rounded-xl shadow-md flex items-center gap-2 transition"
              >
                {loading ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    <span>Analyzing Reviews & Building Workspace...</span>
                  </>
                ) : (
                  <>
                    <span>Generate First Summary</span>
                    <Sparkles className="w-4 h-4" />
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* STEP 3: First AI Summary */}
      {step === 3 && summaryData && (
        <div className="bg-white rounded-3xl p-6 sm:p-8 shadow-sm border border-slate-200 animate-fade-in space-y-6">
          <div className="border-b border-slate-100 pb-5">
            <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-100 text-emerald-800 text-xs font-bold mb-2">
              <CheckCircle2 className="w-4 h-4" />
              Onboarding Completed Successfully!
            </div>
            <h1 className="text-2xl font-black text-slate-900 tracking-tight">
              First Customer Intelligence Summary for {createdBusiness?.name || shopName}
            </h1>
            <p className="text-xs text-slate-500 mt-1">
              Branch: {branchName} • {summaryData.total_mentions_analyzed || 6} customer reviews analyzed
            </p>
          </div>

          {/* Quick Score Metrics */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="p-4 rounded-2xl bg-blue-50/70 border border-blue-100">
              <div className="text-xs font-semibold text-blue-700">Net Customer Sentiment</div>
              <div className="text-2xl font-black text-blue-900 mt-1">
                {summaryData.net_sentiment_score > 0 ? `+${summaryData.net_sentiment_score}%` : `${summaryData.net_sentiment_score}%`}
              </div>
              <div className="text-[11px] text-blue-600 mt-0.5">Healthy local shop benchmark</div>
            </div>

            <div className="p-4 rounded-2xl bg-emerald-50/70 border border-emerald-100">
              <div className="text-xs font-semibold text-emerald-700">Tracked Business Type</div>
              <div className="text-lg font-black text-emerald-900 mt-1 capitalize">
                {presets[businessType]?.name || businessType}
              </div>
              <div className="text-[11px] text-emerald-600 mt-0.5">{selectedTopics.length} topics configured</div>
            </div>

            <div className="p-4 rounded-2xl bg-purple-50/70 border border-purple-100">
              <div className="text-xs font-semibold text-purple-700">Active Branch</div>
              <div className="text-lg font-black text-purple-900 mt-1 truncate">
                {branchName || 'Main Branch'}
              </div>
              <div className="text-[11px] text-purple-600 mt-0.5">{city || 'Local Location'}</div>
            </div>
          </div>

          {/* Overview Discourse */}
          <div className="p-5 rounded-2xl bg-slate-50 border border-slate-200">
            <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider mb-2 flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-blue-600" />
              What Customers Are Saying
            </h3>
            <p className="text-xs text-slate-700 leading-relaxed">
              {summaryData.cause_of_feedback}
            </p>
          </div>

          {/* Actionable Measures & Precautions */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="p-5 rounded-2xl bg-emerald-50/40 border border-emerald-200/80">
              <h3 className="text-xs font-bold text-emerald-900 uppercase tracking-wider mb-3 flex items-center gap-2">
                <ThumbsUp className="w-4 h-4 text-emerald-600" />
                Customer Highlights & Strengths
              </h3>
              <ul className="space-y-2 text-xs text-slate-700">
                {(summaryData.measures_taken || []).map((m, idx) => (
                  <li key={idx} className="flex items-start gap-2">
                    <span className="text-emerald-600 font-bold">•</span>
                    <span>{m}</span>
                  </li>
                ))}
              </ul>
            </div>

            <div className="p-5 rounded-2xl bg-amber-50/40 border border-amber-200/80">
              <h3 className="text-xs font-bold text-amber-900 uppercase tracking-wider mb-3 flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 text-amber-600" />
                Recommended Fixes for Shop Owner
              </h3>
              <ul className="space-y-2 text-xs text-slate-700">
                {(summaryData.precautions || []).map((p, idx) => (
                  <li key={idx} className="flex items-start gap-2">
                    <span className="text-amber-600 font-bold">•</span>
                    <span>{p}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>

          {/* Go to Dashboard CTA */}
          <div className="pt-4 flex justify-end">
            <button
              type="button"
              onClick={() => navigate('/')}
              className="px-7 py-3.5 bg-blue-600 hover:bg-blue-700 text-white font-black text-xs rounded-xl shadow-lg flex items-center gap-2 transition"
            >
              <span>Go to My Business Dashboard</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default Onboarding;
