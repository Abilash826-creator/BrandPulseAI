import React, { useState, useEffect } from 'react';
import { useBrand } from '../context/BrandContext';
import { competitorsAPI, brandsAPI } from '../services/api';
import SOVBar from '../components/charts/SOVBar';
import Modal from '../components/common/Modal';
import { 
  Swords, 
  Plus, 
  CheckCircle2, 
  AlertTriangle, 
  RefreshCw, 
  Trophy 
} from 'lucide-react';

const CompetitorAnalysis = () => {
  const { activeBrand, refreshBrands } = useBrand();

  const [benchmarks, setBenchmarks] = useState([]);
  const [sovData, setSovData] = useState([]);
  const [headToHead, setHeadToHead] = useState(null);
  const [selectedCompetitor, setSelectedCompetitor] = useState(activeBrand?.competitors?.[0] || '');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (activeBrand?.competitors?.length && (!selectedCompetitor || !activeBrand.competitors.includes(selectedCompetitor))) {
      setSelectedCompetitor(activeBrand.competitors[0]);
    }
  }, [activeBrand]);

  // Add Competitor Modal
  const [modalOpen, setModalOpen] = useState(false);
  const [newCompetitorName, setNewCompetitorName] = useState('');

  const fetchCompetitorData = async () => {
    if (!activeBrand) return;
    setLoading(true);
    try {
      const [benchRes, sovRes, h2hRes] = await Promise.all([
        competitorsAPI.getBenchmarks(activeBrand.id),
        competitorsAPI.getSOV(activeBrand.id),
        competitorsAPI.getHeadToHead(activeBrand.id, selectedCompetitor)
      ]);

      setBenchmarks(benchRes.data);
      setSovData(sovRes.data?.share_of_voice || []);
      setHeadToHead(h2hRes.data);
    } catch (err) {
      console.error("Competitor data error:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCompetitorData();
  }, [activeBrand, selectedCompetitor]);

  const handleAddCompetitor = async (e) => {
    e.preventDefault();
    if (!newCompetitorName.trim() || !activeBrand) return;
    try {
      const updatedList = [...(activeBrand.competitors || []), newCompetitorName.trim()];
      await brandsAPI.update(activeBrand.id, { competitors: updatedList });
      setNewCompetitorName('');
      setModalOpen(false);
      refreshBrands();
      fetchCompetitorData();
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="space-y-6 pb-12 animate-fade-in">
      {/* Header */}
      <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-3">
            <h1 className="text-xl lg:text-2xl font-extrabold text-slate-900 tracking-tight">
              Compare Nearby Shops
            </h1>
            <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-blue-50 text-[#2563EB] border border-blue-200">
              Local Comparison
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            See how your ratings, review count, and customer satisfaction compare with 2-5 nearby shops in your area.
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <button
            onClick={() => setModalOpen(true)}
            className="px-4 py-2 rounded-xl bg-[#2563EB] hover:bg-[#1E3A8A] text-white font-semibold text-xs shadow-sm transition flex items-center space-x-1.5"
          >
            <Plus className="w-4 h-4" />
            <span>Add Nearby Shop</span>
          </button>

          <button
            onClick={fetchCompetitorData}
            className="p-2 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 transition border border-slate-200"
            title="Refresh comparison data"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin text-[#2563EB]' : ''}`} />
          </button>
        </div>
      </div>

      {/* Row 1: How you compare & Benchmarks */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4">
          <div>
            <h3 className="text-sm font-bold text-slate-900 tracking-tight">How You Compare with Nearby Shops</h3>
            <p className="text-xs text-slate-500 mt-0.5">Share of total customer reviews in your neighborhood</p>
          </div>
          <SOVBar data={sovData} />
        </div>

        {/* Benchmarking Comparison Matrix Table */}
        <div className="lg:col-span-2 bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm font-bold text-slate-900 tracking-tight">Nearby Shops Comparison</h3>
              <p className="text-xs text-slate-500 mt-0.5">Customer happiness, review volume, and positive sentiment</p>
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-slate-200 text-slate-500 uppercase text-[10px] font-bold tracking-wider">
                  <th className="pb-3">Shop / Business</th>
                  <th className="pb-3">Total Reviews</th>
                  <th className="pb-3">Customer Happiness</th>
                  <th className="pb-3">Positive %</th>
                  <th className="pb-3">Top Mood</th>
                  <th className="pb-3">Praise vs Complaints</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {benchmarks.map((b) => (
                  <tr key={b.brand} className={`transition hover:bg-slate-50 ${b.is_primary ? 'bg-blue-50/50 font-medium' : ''}`}>
                    <td className="py-3.5 flex items-center space-x-2">
                      <span className="w-2.5 h-2.5 rounded-full shrink-0" style={{ backgroundColor: b.color }} />
                      <span className="font-bold text-slate-900 flex items-center space-x-1.5">
                        <span>{b.brand}</span>
                        {b.is_primary && (
                          <span className="text-[9px] font-mono px-1.5 py-0.2 rounded bg-blue-100 text-[#2563EB] border border-blue-200 font-bold">
                            YOUR BRAND
                          </span>
                        )}
                      </span>
                    </td>
                    <td className="py-3.5 text-slate-700 font-mono">{b.volume?.toLocaleString()}</td>
                    <td className="py-3.5">
                      <span className={`font-bold font-mono px-2 py-0.5 rounded-md ${
                        b.net_sentiment >= 0 ? 'bg-emerald-50 text-[#16A34A] border border-emerald-200' : 'bg-red-50 text-[#DC2626] border border-red-200'
                      }`}>
                        {b.net_sentiment > 0 ? `+${b.net_sentiment}%` : `${b.net_sentiment}%`}
                      </span>
                    </td>
                    <td className="py-3.5 text-[#16A34A] font-mono font-semibold">{b.positive_pct}%</td>
                    <td className="py-3.5 text-slate-700 capitalize">{b.dominant_emotion}</td>
                    <td className="py-3.5 font-mono text-[#2563EB] font-semibold">{b.praise_ratio}x</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Row 2: Head-to-Head Matrix & SWOT Analysis */}
      <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-200 pb-4">
          <div>
            <h3 className="text-sm font-bold text-slate-900 tracking-tight flex items-center space-x-2">
              <Swords className="w-4 h-4 text-[#2563EB]" />
              <span>Head-to-Head Comparison</span>
            </h3>
            <p className="text-xs text-slate-500 mt-0.5">Select a competitor to compare category by category</p>
          </div>

          <div className="flex items-center space-x-2">
            <span className="text-xs text-slate-500 font-semibold">Comparing with:</span>
            <select
              value={selectedCompetitor}
              onChange={(e) => setSelectedCompetitor(e.target.value)}
              className="bg-white border border-slate-200 rounded-xl px-3 py-1.5 text-xs text-slate-900 focus:outline-none focus:border-blue-600 font-semibold"
            >
              {activeBrand?.competitors?.length ? (
                activeBrand.competitors.map((c) => (
                  <option key={c} value={c}>{c}</option>
                ))
              ) : (
                <option value="">No competitors added</option>
              )}
            </select>
          </div>
        </div>

        {/* Head-to-Head Category Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {headToHead?.categories?.map((cat, idx) => {
            const isPrimaryWinner = cat.winner === 'primary';
            return (
              <div key={idx} className="p-4 rounded-2xl bg-slate-50 border border-slate-200 space-y-2">
                <div className="text-xs font-semibold text-slate-500">{cat.dimension}</div>
                <div className="flex items-center justify-between pt-1">
                  <div className={`text-sm font-bold ${isPrimaryWinner ? 'text-[#16A34A]' : 'text-slate-700'}`}>
                    <div>{activeBrand?.name}</div>
                    <div className="text-base font-extrabold font-mono">{cat.primary_val}</div>
                  </div>
                  <span className="text-xs font-bold text-slate-400">VS</span>
                  <div className={`text-sm font-bold text-right ${!isPrimaryWinner ? 'text-[#16A34A]' : 'text-slate-700'}`}>
                    <div>{selectedCompetitor}</div>
                    <div className="text-base font-extrabold font-mono">{cat.comp_val}</div>
                  </div>
                </div>
                <div className="pt-2 border-t border-slate-200 text-[11px] flex items-center justify-between">
                  <span className="text-slate-500 font-medium">Winner:</span>
                  <span className="font-bold text-[#2563EB] flex items-center space-x-1">
                    <Trophy className="w-3 h-3 text-amber-500" />
                    <span>{isPrimaryWinner ? activeBrand?.name : selectedCompetitor}</span>
                  </span>
                </div>
              </div>
            );
          })}
        </div>

        {/* What Customers Praise & Compare */}
        {headToHead?.swot_analysis && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-2">
            <div className="p-4 rounded-2xl bg-emerald-50/70 border border-emerald-200 space-y-2">
              <div className="text-xs font-bold text-[#16A34A] flex items-center space-x-1.5">
                <CheckCircle2 className="w-4 h-4" />
                <span>Your Shop's Strengths</span>
              </div>
              <ul className="space-y-1 text-xs text-slate-700 list-disc list-inside">
                {headToHead.swot_analysis.strengths?.map((s, i) => (
                  <li key={i} className="leading-relaxed">{s}</li>
                ))}
              </ul>
            </div>

            <div className="p-4 rounded-2xl bg-amber-50/70 border border-amber-200 space-y-2">
              <div className="text-xs font-bold text-[#CA8A04] flex items-center space-x-1.5">
                <AlertTriangle className="w-4 h-4" />
                <span>Things Customers Want Improved</span>
              </div>
              <ul className="space-y-1 text-xs text-slate-700 list-disc list-inside">
                {headToHead.swot_analysis.vulnerabilities?.map((v, i) => (
                  <li key={i} className="leading-relaxed">{v}</li>
                ))}
              </ul>
            </div>

            <div className="p-4 rounded-2xl bg-blue-50/70 border border-blue-200 space-y-2">
              <div className="text-xs font-bold text-[#2563EB] flex items-center space-x-1.5">
                <Swords className="w-4 h-4" />
                <span>What Nearby Shops Do Well</span>
              </div>
              <ul className="space-y-1 text-xs text-slate-700 list-disc list-inside">
                {headToHead.swot_analysis.competitor_threats?.map((t, i) => (
                  <li key={i} className="leading-relaxed">{t}</li>
                ))}
              </ul>
            </div>
          </div>
        )}
      </div>

      {/* Add Nearby Shop Modal */}
      <Modal
        isOpen={modalOpen}
        onClose={() => setModalOpen(false)}
        title="Add a Nearby Shop to Compare"
      >
        <form onSubmit={handleAddCompetitor} className="space-y-4 text-xs">
          <p className="text-slate-600">
            Add 2 to 5 nearby businesses or competitor shops in your neighborhood to see how customer ratings and feedback compare.
          </p>

          <div>
            <label className="font-semibold text-slate-700 block mb-1">Nearby Shop Name</label>
            <input
              type="text"
              value={newCompetitorName}
              onChange={(e) => setNewCompetitorName(e.target.value)}
              placeholder="e.g. Sangeetha Vegetarian, Murugan Idli, Annapoorna"
              required
              className="w-full bg-white border border-slate-200 rounded-xl p-3 text-slate-900 focus:outline-none focus:border-blue-600 font-medium"
            />
          </div>

          <div className="flex justify-end space-x-2 pt-3 border-t border-slate-200">
            <button
              type="button"
              onClick={() => setModalOpen(false)}
              className="px-4 py-2 rounded-xl bg-slate-100 text-slate-700 hover:bg-slate-200 font-semibold"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-4 py-2 rounded-xl bg-[#2563EB] hover:bg-[#1E3A8A] text-white font-bold transition"
            >
              Add Shop
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
};

export default CompetitorAnalysis;
