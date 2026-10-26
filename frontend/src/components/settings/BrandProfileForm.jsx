import React, { useState } from 'react';
import { Building, Package, Hash, AtSign, ShieldAlert, X, Save, Loader2, Tag, UtensilsCrossed, Plus } from 'lucide-react';

const BrandProfileForm = ({
  formData,
  setFormData,
  productInput,
  setProductInput,
  addProduct,
  removeProduct,
  keywordInput,
  setKeywordInput,
  addKeyword,
  removeKeyword,
  hashtagInput,
  setHashtagInput,
  addHashtag,
  removeHashtag,
  competitorInput,
  setCompetitorInput,
  addCompetitor,
  removeCompetitor,
  handleSave,
  saving
}) => {
  const [topicInput, setTopicInput] = useState('');

  const addTopic = () => {
    if (!topicInput.trim()) return;
    const current = formData.topics || [];
    if (!current.includes(topicInput.trim())) {
      setFormData({ ...formData, topics: [...current, topicInput.trim()] });
    }
    setTopicInput('');
  };

  const removeTopic = (topic) => {
    const current = formData.topics || [];
    setFormData({ ...formData, topics: current.filter(t => t !== topic) });
  };

  return (
    <form onSubmit={handleSave} className="space-y-6 text-xs">
      {/* Business Details */}
      <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4">
        <h3 className="text-sm font-bold text-slate-900 tracking-tight flex items-center space-x-2">
          <Building className="w-4 h-4 text-blue-600" />
          <span>Business Profile & Category</span>
        </h3>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div>
            <label className="font-semibold text-slate-700 block mb-1.5">Business / Shop Name *</label>
            <input
              type="text"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              required
              placeholder="e.g. Annapoorna Bhavan"
              className="w-full bg-white border border-slate-200 rounded-xl p-3 text-slate-900 focus:outline-none focus:border-blue-600 font-medium"
            />
          </div>

          <div>
            <label className="font-semibold text-slate-700 block mb-1.5">Business Type</label>
            <select
              value={formData.business_type || 'restaurant'}
              onChange={(e) => setFormData({ ...formData, business_type: e.target.value })}
              className="w-full bg-white border border-slate-200 rounded-xl p-3 text-slate-900 focus:outline-none focus:border-blue-600 font-medium"
            >
              <option value="restaurant">Restaurant / Cafe / Eatery</option>
              <option value="retail">Retail Shop / Store</option>
              <option value="salon">Salon & Spa / Grooming</option>
              <option value="clinic">Clinic / Healthcare</option>
              <option value="supermarket">Supermarket / Grocery</option>
              <option value="bakery">Bakery & Sweets</option>
              <option value="other">Other Local Business</option>
            </select>
          </div>

          <div>
            <label className="font-semibold text-slate-700 block mb-1.5">Industry Vertical</label>
            <input
              type="text"
              value={formData.industry}
              onChange={(e) => setFormData({ ...formData, industry: e.target.value })}
              placeholder="e.g. Food & Beverage"
              className="w-full bg-white border border-slate-200 rounded-xl p-3 text-slate-900 focus:outline-none focus:border-blue-600 font-medium"
            />
          </div>
        </div>

        <div>
          <label className="font-semibold text-slate-700 block mb-1.5">Business Overview</label>
          <textarea
            rows={2}
            value={formData.description}
            onChange={(e) => setFormData({ ...formData, description: e.target.value })}
            className="w-full bg-white border border-slate-200 rounded-xl p-3 text-slate-900 focus:outline-none focus:border-blue-600"
            placeholder="Describe your shop, specialities, or service offerings..."
          />
        </div>
      </div>

      {/* Tracked Customer Topics & Aspects */}
      <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4">
        <h3 className="text-sm font-bold text-slate-900 tracking-tight flex items-center space-x-2">
          <Tag className="w-4 h-4 text-blue-600" />
          <span>Tracked Review Topics (Service, Cleanliness, Pricing, etc.)</span>
        </h3>
        <p className="text-[11px] text-slate-500">
          Aspects analyzed in customer reviews to score sentiment and identify problem areas.
        </p>

        <div>
          <div className="flex items-center space-x-2 mb-2">
            <input
              type="text"
              value={topicInput}
              onChange={(e) => setTopicInput(e.target.value)}
              onKeyDown={(e) => { if (e.key === 'Enter') { e.preventDefault(); addTopic(); } }}
              placeholder="Add topic (e.g. Waiting Time, Cleanliness, Food Quality)..."
              className="w-full bg-white border border-slate-200 rounded-xl p-2.5 text-slate-900 focus:outline-none focus:border-blue-600"
            />
            <button
              type="button"
              onClick={addTopic}
              className="px-4 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-bold shrink-0"
            >
              Add
            </button>
          </div>
          <div className="flex flex-wrap gap-1.5 pt-1">
            {(formData.topics || []).map((topic) => (
              <span
                key={topic}
                className="px-3 py-1 rounded-xl bg-blue-50 border border-blue-200 text-xs font-semibold text-blue-700 flex items-center space-x-1.5"
              >
                <span>{topic}</span>
                <button
                  type="button"
                  onClick={() => removeTopic(topic)}
                  className="text-blue-400 hover:text-red-600 ml-1"
                >
                  <X className="w-3 h-3" />
                </button>
              </span>
            ))}
          </div>
        </div>
      </div>

      {/* Popular Products & Specialities */}
      <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4">
        <h3 className="text-sm font-bold text-slate-900 tracking-tight flex items-center space-x-2">
          <Package className="w-4 h-4 text-blue-600" />
          <span>Key Items & Specialities</span>
        </h3>

        <div>
          <label className="font-semibold text-slate-700 block mb-1.5">Item Names / Services</label>
          <div className="flex items-center space-x-2 mb-2">
            <input
              type="text"
              value={productInput}
              onChange={(e) => setProductInput(e.target.value)}
              onKeyDown={(e) => { if (e.key === 'Enter') { e.preventDefault(); addProduct(); } }}
              placeholder="Add item (e.g. Ghee Roast Dosa, Filter Coffee, Hair Spa)..."
              className="w-full bg-white border border-slate-200 rounded-xl p-2.5 text-slate-900 focus:outline-none focus:border-blue-600"
            />
            <button
              type="button"
              onClick={addProduct}
              className="px-4 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-bold shrink-0"
            >
              Add
            </button>
          </div>
          <div className="flex flex-wrap gap-1.5 pt-1">
            {(formData?.products || []).map((prod) => (
              <span
                key={prod}
                className="px-3 py-1 rounded-xl bg-slate-100 border border-slate-200 text-xs text-slate-800 flex items-center space-x-1.5 font-medium"
              >
                <span>{prod}</span>
                <button
                  type="button"
                  onClick={() => removeProduct(prod)}
                  className="text-slate-400 hover:text-red-600 ml-1"
                >
                  <X className="w-3 h-3" />
                </button>
              </span>
            ))}
          </div>
        </div>
      </div>

      {/* Tracked Keywords & Hashtags */}
      <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4">
        <h3 className="text-sm font-bold text-slate-900 tracking-tight flex items-center space-x-2">
          <Hash className="w-4 h-4 text-blue-600" />
          <span>Monitored Keywords & Hashtags</span>
        </h3>

        <div>
          <label className="font-semibold text-slate-700 block mb-1.5">Tracked Keywords</label>
          <div className="flex items-center space-x-2 mb-2">
            <input
              type="text"
              value={keywordInput}
              onChange={(e) => setKeywordInput(e.target.value)}
              onKeyDown={(e) => { if (e.key === 'Enter') { e.preventDefault(); addKeyword(); } }}
              placeholder="Add keyword (e.g. taste, billing, coffee, delivery)..."
              className="w-full bg-white border border-slate-200 rounded-xl p-2.5 text-slate-900 focus:outline-none focus:border-blue-600"
            />
            <button
              type="button"
              onClick={addKeyword}
              className="px-4 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-bold shrink-0"
            >
              Add
            </button>
          </div>
          <div className="flex flex-wrap gap-1.5 pt-1">
            {(formData?.keywords || []).map((kw) => (
              <span
                key={kw}
                className="px-3 py-1 rounded-xl bg-slate-100 border border-slate-200 text-xs font-mono text-slate-800 flex items-center space-x-1.5 font-semibold"
              >
                <span>{kw}</span>
                <button
                  type="button"
                  onClick={() => removeKeyword(kw)}
                  className="text-slate-400 hover:text-red-600"
                >
                  <X className="w-3 h-3" />
                </button>
              </span>
            ))}
          </div>
        </div>
      </div>

      {/* Nearby / Competing Shops */}
      <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4">
        <h3 className="text-sm font-bold text-slate-900 tracking-tight flex items-center space-x-2">
          <AtSign className="w-4 h-4 text-blue-600" />
          <span>Nearby Shops to Compare With (Optional)</span>
        </h3>

        <div>
          <label className="font-semibold text-slate-700 block mb-1.5">Shop Names in Your Area</label>
          <div className="flex items-center space-x-2 mb-2">
            <input
              type="text"
              value={competitorInput}
              onChange={(e) => setCompetitorInput(e.target.value)}
              onKeyDown={(e) => { if (e.key === 'Enter') { e.preventDefault(); addCompetitor(); } }}
              placeholder="Add nearby shop name (e.g. Sangeetha, Murugan Idli)..."
              className="w-full bg-white border border-slate-200 rounded-xl p-2.5 text-slate-900 focus:outline-none focus:border-blue-600"
            />
            <button
              type="button"
              onClick={addCompetitor}
              className="px-4 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-bold shrink-0"
            >
              Add
            </button>
          </div>
          <div className="flex flex-wrap gap-1.5 pt-1">
            {(formData?.competitors || []).map((comp) => (
              <span
                key={comp}
                className="px-3 py-1 rounded-xl bg-slate-100 border border-slate-200 text-xs font-mono text-slate-800 flex items-center space-x-1.5 font-semibold"
              >
                <span>{comp}</span>
                <button
                  type="button"
                  onClick={() => removeCompetitor(comp)}
                  className="text-slate-400 hover:text-red-600"
                >
                  <X className="w-3 h-3" />
                </button>
              </span>
            ))}
          </div>
        </div>
      </div>

      {/* Alert Preferences */}
      <div className="bg-white p-6 rounded-2xl border border-slate-200 space-y-4 shadow-sm">
        <div>
          <h3 className="text-sm font-bold text-slate-900 tracking-tight flex items-center space-x-2">
            <ShieldAlert className="w-4 h-4 text-amber-600" />
            <span>Alert Preferences</span>
          </h3>
          <p className="text-xs text-slate-500 mt-0.5">Choose how and when BrandPulse notifies you about customer feedback.</p>
        </div>

        <div className="space-y-3 pt-1">
          <label className="flex items-start space-x-3 p-3 rounded-xl bg-slate-50 border border-slate-200 cursor-pointer hover:bg-slate-100 transition">
            <input
              type="checkbox"
              checked={formData.notify_bad_reviews !== false}
              onChange={(e) => setFormData({ ...formData, notify_bad_reviews: e.target.checked })}
              className="mt-0.5 h-4 w-4 rounded text-blue-600 border-slate-300 focus:ring-blue-500 cursor-pointer"
            />
            <div className="text-xs">
              <span className="font-bold text-slate-800 block">Tell me about every 1-2 star review</span>
              <span className="text-slate-500 text-[11px]">Get alerted immediately whenever an unhappy customer posts feedback.</span>
            </div>
          </label>

          <label className="flex items-start space-x-3 p-3 rounded-xl bg-slate-50 border border-slate-200 cursor-pointer hover:bg-slate-100 transition">
            <input
              type="checkbox"
              checked={formData.notify_weekly_summary !== false}
              onChange={(e) => setFormData({ ...formData, notify_weekly_summary: e.target.checked })}
              className="mt-0.5 h-4 w-4 rounded text-blue-600 border-slate-300 focus:ring-blue-500 cursor-pointer"
            />
            <div className="text-xs">
              <span className="font-bold text-slate-800 block">Weekly plain-English summary</span>
              <span className="text-slate-500 text-[11px]">Receive a Monday morning briefing summarizing what customers loved and what needs fixing.</span>
            </div>
          </label>

          <label className="flex items-start space-x-3 p-3 rounded-xl bg-slate-50 border border-slate-200 cursor-pointer hover:bg-slate-100 transition">
            <input
              type="checkbox"
              checked={formData.notify_spike !== false}
              onChange={(e) => setFormData({ ...formData, notify_spike: e.target.checked, crisis_threshold_negative: e.target.checked ? 0.30 : 0.60 })}
              className="mt-0.5 h-4 w-4 rounded text-blue-600 border-slate-300 focus:ring-blue-500 cursor-pointer"
            />
            <div className="text-xs">
              <span className="font-bold text-slate-800 block">Alert me if 3+ complaints happen in a single day</span>
              <span className="text-slate-500 text-[11px]">Notice sudden drops in rating or unexpected quality issues immediately.</span>
            </div>
          </label>

          {/* Delivery Channels & Timing */}
          <div className="pt-2 border-t border-slate-200 grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label className="font-semibold text-slate-700 block mb-1">Alert Notification Email</label>
              <input
                type="email"
                value={formData.notification_email || ''}
                onChange={(e) => setFormData({ ...formData, notification_email: e.target.value })}
                placeholder="owner@example.com"
                className="w-full bg-slate-50 border border-slate-200 rounded-xl p-2.5 text-slate-900 focus:outline-none focus:border-blue-600"
              />
            </div>

            <div>
              <label className="font-semibold text-slate-700 block mb-1">WhatsApp / SMS Phone</label>
              <input
                type="tel"
                value={formData.notification_phone || ''}
                onChange={(e) => setFormData({ ...formData, notification_phone: e.target.value })}
                placeholder="+91 98765 43210"
                className="w-full bg-slate-50 border border-slate-200 rounded-xl p-2.5 text-slate-900 focus:outline-none focus:border-blue-600"
              />
            </div>

            <div>
              <label className="font-semibold text-slate-700 block mb-1">Weekly Digest Day</label>
              <select
                value={formData.weekly_digest_day || 'Monday'}
                onChange={(e) => setFormData({ ...formData, weekly_digest_day: e.target.value })}
                className="w-full bg-slate-50 border border-slate-200 rounded-xl p-2.5 text-slate-900 focus:outline-none focus:border-blue-600 font-medium"
              >
                {['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'].map(d => (
                  <option key={d} value={d}>{d}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="font-semibold text-slate-700 block mb-1">Weekly Digest Time</label>
              <input
                type="time"
                value={formData.weekly_digest_time || '09:00'}
                onChange={(e) => setFormData({ ...formData, weekly_digest_time: e.target.value })}
                className="w-full bg-slate-50 border border-slate-200 rounded-xl p-2.5 text-slate-900 focus:outline-none focus:border-blue-600 font-medium"
              />
            </div>
          </div>
        </div>
      </div>

      {/* Submit Save Button */}
      <div className="flex justify-end pt-2">
        <button
          type="submit"
          disabled={saving}
          className="px-6 py-3 rounded-2xl bg-blue-600 hover:bg-blue-700 text-white font-bold text-xs shadow-sm transition flex items-center space-x-2 disabled:opacity-50"
        >
          {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
          <span>Save Business Profile</span>
        </button>
      </div>
    </form>
  );
};

export default BrandProfileForm;
