import React, { useState } from 'react';
import { Search, Star, Filter, MessageSquare, CheckCircle2, ChevronDown, ChevronUp, AlertCircle } from 'lucide-react';

const SocialListeningFilters = ({
  search,
  setSearch,
  handleSearchSubmit,
  source = 'all',
  setSource,
  rating = 'all',
  setRating,
  sentiment = 'all',
  setSentiment,
  replied = 'all',
  setReplied,
  language = 'all',
  setLanguage,
  topic = 'all',
  setTopic,
  productFilter = 'all',
  setProductFilter,
  availableProducts = []
}) => {
  const [showAdvanced, setShowAdvanced] = useState(false);

  // Quick chips: All | Google | Instagram | Facebook | Needs reply | 1-2 stars
  const quickChips = [
    {
      id: 'all',
      label: 'All',
      isActive: source === 'all' && rating === 'all' && replied === 'all' && sentiment === 'all',
      onClick: () => {
        setSource('all');
        setRating('all');
        setReplied('all');
        setSentiment('all');
      }
    },
    {
      id: 'google',
      label: 'Google ⭐',
      isActive: source === 'google',
      onClick: () => {
        setSource(source === 'google' ? 'all' : 'google');
      }
    },
    {
      id: 'instagram',
      label: 'Instagram 📸',
      isActive: source === 'instagram',
      onClick: () => {
        setSource(source === 'instagram' ? 'all' : 'instagram');
      }
    },
    {
      id: 'facebook',
      label: 'Facebook 💬',
      isActive: source === 'facebook',
      onClick: () => {
        setSource(source === 'facebook' ? 'all' : 'facebook');
      }
    },
    {
      id: 'needs_reply',
      label: 'Needs reply ⏳',
      isActive: replied === 'needs_reply',
      onClick: () => {
        setReplied(replied === 'needs_reply' ? 'all' : 'needs_reply');
      }
    },
    {
      id: 'low_stars',
      label: '1-2 stars ⚠️',
      isActive: rating === '1' || rating === '2' || rating === 'low',
      onClick: () => {
        setRating(rating === 'low' || rating === '1' || rating === '2' ? 'all' : '2');
      }
    }
  ];

  const activeAdvancedFiltersCount = [
    sentiment !== 'all',
    language !== 'all',
    topic !== 'all',
    productFilter !== 'all'
  ].filter(Boolean).length;

  return (
    <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-sm space-y-3.5">
      {/* Top Row: Search & Quick Chips */}
      <div className="flex flex-col lg:flex-row items-stretch lg:items-center justify-between gap-3">
        {/* Search Input */}
        <form onSubmit={handleSearchSubmit} className="relative w-full lg:w-80">
          <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search keywords, customer names..."
            className="w-full min-h-[44px] bg-white border border-slate-200 rounded-xl pl-10 pr-4 py-2.5 text-xs text-slate-900 placeholder-slate-400 focus:outline-none focus:border-blue-600 focus:ring-1 focus:ring-blue-600 transition"
          />
        </form>

        {/* Quick Filter Chips (horizontal scroll on mobile) */}
        <div className="flex items-center space-x-2 overflow-x-auto pb-1 scrollbar-none">
          {quickChips.map((chip) => (
            <button
              key={chip.id}
              type="button"
              onClick={chip.onClick}
              className={`min-h-[40px] px-3.5 py-2 rounded-xl text-xs font-bold transition whitespace-nowrap border shrink-0 flex items-center space-x-1.5 ${
                chip.isActive
                  ? 'bg-blue-600 text-white border-blue-600 shadow-xs'
                  : 'bg-slate-50 text-slate-700 border-slate-200 hover:bg-slate-100'
              }`}
            >
              <span>{chip.label}</span>
            </button>
          ))}

          {/* Toggle More Filters */}
          <button
            type="button"
            onClick={() => setShowAdvanced(!showAdvanced)}
            className={`min-h-[40px] px-3.5 py-2 rounded-xl text-xs font-bold transition whitespace-nowrap border shrink-0 flex items-center space-x-1.5 ${
              showAdvanced || activeAdvancedFiltersCount > 0
                ? 'bg-blue-50 text-blue-700 border-blue-200'
                : 'bg-white text-slate-600 border-slate-200 hover:bg-slate-50'
            }`}
          >
            <Filter className="w-3.5 h-3.5 text-blue-600" />
            <span>More Filters</span>
            {activeAdvancedFiltersCount > 0 && (
              <span className="w-4 h-4 rounded-full bg-blue-600 text-white text-[10px] flex items-center justify-center font-mono">
                {activeAdvancedFiltersCount}
              </span>
            )}
            {showAdvanced ? (
              <ChevronUp className="w-3.5 h-3.5 text-slate-400" />
            ) : (
              <ChevronDown className="w-3.5 h-3.5 text-slate-400" />
            )}
          </button>
        </div>
      </div>

      {/* Expandable Advanced Filter Dropdowns */}
      {showAdvanced && (
        <div className="pt-3 border-t border-slate-100 grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2.5 animate-fade-in">
          {/* Source Filter */}
          <div>
            <label className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block mb-1">Source</label>
            <select
              value={source}
              onChange={(e) => setSource && setSource(e.target.value)}
              className="w-full bg-slate-50 border border-slate-200 rounded-xl px-2.5 py-2 text-xs text-slate-700 focus:outline-none focus:border-blue-600 font-medium"
            >
              <option value="all">All Sources</option>
              <option value="google">Google Reviews ⭐</option>
              <option value="facebook">Facebook Reviews 💬</option>
              <option value="instagram">Instagram 📸</option>
              <option value="pasted">Pasted Reviews 📋</option>
              <option value="csv">CSV / Excel 📊</option>
            </select>
          </div>

          {/* Star Rating Filter */}
          <div>
            <label className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block mb-1">Rating</label>
            <select
              value={rating}
              onChange={(e) => setRating && setRating(e.target.value)}
              className="w-full bg-slate-50 border border-slate-200 rounded-xl px-2.5 py-2 text-xs text-slate-700 focus:outline-none focus:border-blue-600 font-medium"
            >
              <option value="all">All Ratings</option>
              <option value="5">5 Stars (★★★★★)</option>
              <option value="4">4 Stars (★★★★)</option>
              <option value="3">3 Stars (★★★)</option>
              <option value="2">2 Stars (★★)</option>
              <option value="1">1 Star (★)</option>
            </select>
          </div>

          {/* Mood / Sentiment Filter */}
          <div>
            <label className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block mb-1">Customer Mood</label>
            <select
              value={sentiment}
              onChange={(e) => setSentiment && setSentiment(e.target.value)}
              className="w-full bg-slate-50 border border-slate-200 rounded-xl px-2.5 py-2 text-xs text-slate-700 focus:outline-none focus:border-blue-600 font-medium"
            >
              <option value="all">All Moods</option>
              <option value="positive">Happy 😊</option>
              <option value="neutral">Neutral 😐</option>
              <option value="negative">Unhappy 😟</option>
            </select>
          </div>

          {/* Replied Status */}
          <div>
            <label className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block mb-1">Status</label>
            <select
              value={replied}
              onChange={(e) => setReplied && setReplied(e.target.value)}
              className="w-full bg-slate-50 border border-slate-200 rounded-xl px-2.5 py-2 text-xs text-slate-700 focus:outline-none focus:border-blue-600 font-medium"
            >
              <option value="all">All Status</option>
              <option value="replied">Replied ✓</option>
              <option value="needs_reply">Needs Reply ⏳</option>
            </select>
          </div>

          {/* Language Filter */}
          <div>
            <label className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block mb-1">Language</label>
            <select
              value={language}
              onChange={(e) => setLanguage && setLanguage(e.target.value)}
              className="w-full bg-slate-50 border border-slate-200 rounded-xl px-2.5 py-2 text-xs text-slate-700 focus:outline-none focus:border-blue-600 font-medium"
            >
              <option value="all">All Languages</option>
              <option value="en">English</option>
              <option value="ta">Tamil (தமிழ்)</option>
              <option value="tanglish">Tanglish</option>
              <option value="hi">Hindi (हिंदी)</option>
              <option value="hinglish">Hinglish</option>
            </select>
          </div>

          {/* Topic Filter */}
          <div>
            <label className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block mb-1">Topic</label>
            <select
              value={topic}
              onChange={(e) => setTopic && setTopic(e.target.value)}
              className="w-full bg-slate-50 border border-slate-200 rounded-xl px-2.5 py-2 text-xs text-slate-700 focus:outline-none focus:border-blue-600 font-medium"
            >
              <option value="all">All Topics</option>
              <option value="taste">Food & Taste</option>
              <option value="service">Service & Staff</option>
              <option value="pricing">Value & Pricing</option>
              <option value="hygiene">Hygiene & Clean</option>
              <option value="ambience">Ambience</option>
              <option value="delivery">Delivery / Wait</option>
            </select>
          </div>
        </div>
      )}
    </div>
  );
};

export default SocialListeningFilters;
