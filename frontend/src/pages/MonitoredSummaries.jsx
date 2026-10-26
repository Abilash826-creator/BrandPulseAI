import React, { useState, useEffect } from 'react';
import { useBrand } from '../context/BrandContext';
import { monitoringAPI } from '../services/api';
import { 
  Database, 
  Sparkles, 
  RefreshCw, 
  Plus, 
  CheckCircle2, 
  ShieldAlert, 
  Clock, 
  Calendar, 
  Building2, 
  Trash2, 
  ChevronDown, 
  ChevronUp, 
  Search, 
  Check 
} from 'lucide-react';

const MonitoredSummaries = () => {
  const { activeBrand } = useBrand();
  const [summaries, setSummaries] = useState([]);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [newMeasureText, setNewMeasureText] = useState({});
  const [expandedSummaryId, setExpandedSummaryId] = useState(null);
  const [feedbackSuccess, setFeedbackSuccess] = useState('');

  const fetchSummaries = async () => {
    if (!activeBrand) return;
    setLoading(true);
    try {
      const res = await monitoringAPI.getSummaries(activeBrand.id);
      setSummaries(res.data || []);
      if (res.data && res.data.length > 0 && !expandedSummaryId) {
        setExpandedSummaryId(res.data[0].id);
      }
    } catch (err) {
      console.error("Failed to fetch monitored summaries:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSummaries();
  }, [activeBrand]);

  const handleGenerateSummary = async () => {
    if (!activeBrand) return;
    setGenerating(true);
    try {
      const res = await monitoringAPI.generateSummary(activeBrand.id);
      setSummaries([res.data, ...summaries]);
      setExpandedSummaryId(res.data.id);
      setFeedbackSuccess('New Monitored Summary successfully generated and stored in MongoDB!');
      setTimeout(() => setFeedbackSuccess(''), 4000);
    } catch (err) {
      console.error("Failed to generate summary:", err);
    } finally {
      setGenerating(false);
    }
  };

  const handleAddMeasure = async (summaryId) => {
    const text = newMeasureText[summaryId];
    if (!text || !text.trim()) return;

    const summary = summaries.find(s => s.id === summaryId);
    if (!summary) return;

    const updatedMeasures = [...(summary.measures_taken || []), text.trim()];
    try {
      const res = await monitoringAPI.updateSummary(summaryId, { measures_taken: updatedMeasures });
      setSummaries(summaries.map(s => s.id === summaryId ? res.data : s));
      setNewMeasureText({ ...newMeasureText, [summaryId]: '' });
    } catch (err) {
      console.error("Failed to update measures:", err);
    }
  };

  const handleDeleteSummary = async (summaryId) => {
    if (!window.confirm("Delete this summary from MongoDB?")) return;
    try {
      await monitoringAPI.deleteSummary(summaryId);
      setSummaries(summaries.filter(s => s.id !== summaryId));
    } catch (err) {
      console.error("Failed to delete summary:", err);
    }
  };

  const filteredSummaries = summaries.filter(s => {
    if (!searchTerm) return true;
    const term = searchTerm.toLowerCase();
    return (
      s.name_of_company?.toLowerCase().includes(term) ||
      s.product_service?.toLowerCase().includes(term) ||
      s.cause_of_feedback?.toLowerCase().includes(term) ||
      s.date?.includes(term)
    );
  });

  return (
    <div className="space-y-6 pb-12 animate-fade-in">
      {/* Header Panel */}
      <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-3">
            <h1 className="text-xl lg:text-2xl font-extrabold text-slate-900 tracking-tight">
              AI Summary Reports
            </h1>
            <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-emerald-50 text-[#16A34A] border border-emerald-200 flex items-center space-x-1">
              <Database className="w-3 h-3" />
              <span>Saved Reports</span>
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Executive summaries of brand feedback with why customers felt that way, prevention tips, and action steps taken.
          </p>
        </div>

        <div className="flex items-center space-x-2.5">
          <button
            onClick={fetchSummaries}
            className="p-2.5 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 transition border border-slate-200"
            title="Refresh reports"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin text-[#2563EB]' : ''}`} />
          </button>

          <button
            onClick={handleGenerateSummary}
            disabled={generating}
            className="px-4 py-2.5 rounded-xl bg-[#2563EB] hover:bg-[#1E3A8A] text-white font-bold text-xs shadow-sm transition flex items-center space-x-2 disabled:opacity-50"
          >
            <Sparkles className={`w-4 h-4 ${generating ? 'animate-spin' : ''}`} />
            <span>{generating ? 'Writing Report...' : 'Create New Summary Report'}</span>
          </button>
        </div>
      </div>

      {/* Success Notification Banner */}
      {feedbackSuccess && (
        <div className="p-3.5 rounded-2xl bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs font-semibold flex items-center space-x-2 animate-fade-in shadow-xs">
          <CheckCircle2 className="w-4 h-4 text-[#16A34A] shrink-0" />
          <span>{feedbackSuccess}</span>
        </div>
      )}

      {/* Filter and Search Bar */}
      <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-sm flex items-center justify-between gap-4">
        <div className="relative flex-1 max-w-md">
          <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-2.5" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search reports by company, product, reason, or date..."
            className="w-full bg-white border border-slate-200 rounded-xl pl-10 pr-4 py-2 text-xs text-slate-900 placeholder-slate-400 focus:outline-none focus:border-blue-600 focus:ring-1 focus:ring-blue-600"
          />
        </div>

        <div className="text-xs text-slate-500 font-mono font-medium">
          Total Reports: <strong className="text-slate-900">{summaries.length}</strong>
        </div>
      </div>

      {/* Summaries List */}
      {loading && summaries.length === 0 ? (
        <div className="bg-white p-12 text-center text-slate-500 text-xs space-y-2 rounded-2xl border border-slate-200">
          <RefreshCw className="w-6 h-6 animate-spin mx-auto text-[#2563EB]" />
          <p>Loading summary reports...</p>
        </div>
      ) : filteredSummaries.length === 0 ? (
        <div className="bg-white p-12 text-center text-slate-500 text-xs space-y-3 rounded-2xl border border-slate-200">
          <Database className="w-8 h-8 mx-auto text-slate-400" />
          <p className="font-semibold text-slate-700">No summary reports found matching your search</p>
          <p className="text-[11px] text-slate-400">Click "Create New Summary Report" to generate an executive report.</p>
        </div>
      ) : (
        <div className="space-y-4">
          {filteredSummaries.map((s) => {
            const isExpanded = expandedSummaryId === s.id;
            return (
              <div 
                key={s.id} 
                className="bg-white rounded-2xl border border-slate-200 overflow-hidden transition-all duration-200 shadow-sm hover:shadow-md"
              >
                {/* Summary Card Header (Collapsible Toggle) */}
                <div 
                  onClick={() => setExpandedSummaryId(isExpanded ? null : s.id)}
                  className="p-6 cursor-pointer hover:bg-slate-50/70 flex flex-col lg:flex-row lg:items-center justify-between gap-4"
                >
                  <div className="flex items-start space-x-4">
                    <div className="w-11 h-11 rounded-2xl bg-blue-50 border border-blue-200 flex items-center justify-center shrink-0">
                      <Building2 className="w-5 h-5 text-[#2563EB]" />
                    </div>
                    <div>
                      <div className="flex flex-wrap items-center gap-2">
                        <h2 className="text-base font-bold text-slate-900 tracking-tight">
                          {s.name_of_company}
                        </h2>
                        <span className="text-[10px] font-mono px-2 py-0.5 rounded-lg bg-blue-50 text-[#2563EB] border border-blue-200 font-semibold">
                          {s.product_service}
                        </span>
                        <span className="text-[10px] font-mono px-2 py-0.5 rounded-lg bg-emerald-50 text-[#16A34A] border border-emerald-200 font-semibold">
                          Customer Score: +{s.net_sentiment_score}%
                        </span>
                      </div>
                      <p className="text-xs text-slate-500 mt-1 line-clamp-1">
                        {s.company_details?.description || 'Brand summary report'}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center space-x-3 shrink-0 self-end lg:self-center">
                    <div className="flex items-center space-x-2 text-xs font-mono text-slate-600 bg-slate-100 px-3 py-1.5 rounded-xl border border-slate-200">
                      <Calendar className="w-3.5 h-3.5 text-[#2563EB]" />
                      <span>{s.date}</span>
                      <Clock className="w-3.5 h-3.5 text-[#2563EB] ml-1.5" />
                      <span>{s.time}</span>
                    </div>

                    <button 
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDeleteSummary(s.id);
                      }}
                      className="p-2 rounded-xl text-slate-400 hover:text-red-600 hover:bg-red-50 transition"
                      title="Delete Report"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>

                    <div className="text-slate-400">
                      {isExpanded ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
                    </div>
                  </div>
                </div>

                {/* Expanded Details Body */}
                {isExpanded && (
                  <div className="p-6 pt-0 border-t border-slate-100 space-y-6 animate-fade-in">
                    {/* Company Details Grid */}
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-4 text-xs">
                      <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200 space-y-1">
                        <span className="text-[10px] font-bold text-slate-500 uppercase">Industry</span>
                        <div className="font-semibold text-slate-800">{s.company_details?.industry || 'Enterprise Technology'}</div>
                      </div>
                      <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200 space-y-1">
                        <span className="text-[10px] font-bold text-slate-500 uppercase">Analyzed Posts</span>
                        <div className="font-semibold text-slate-900 font-mono">{s.total_mentions_analyzed} Feedback Posts</div>
                      </div>
                      <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200 space-y-1">
                        <span className="text-[10px] font-bold text-slate-500 uppercase">Key Competitors</span>
                        <div className="font-semibold text-slate-700 truncate">
                          {s.company_details?.competitors?.join(', ') || 'Direct Competitors'}
                        </div>
                      </div>
                    </div>

                    {/* Cause of the Feedback Section */}
                    <div className="p-5 rounded-2xl bg-blue-50/50 border border-blue-200 space-y-2">
                      <div className="flex items-center space-x-2">
                        <Sparkles className="w-4 h-4 text-[#2563EB]" />
                        <h3 className="text-xs font-bold text-[#1E3A8A] uppercase tracking-wider">
                          Why Customers Left Feedback (Key Drivers)
                        </h3>
                      </div>
                      <p className="text-xs text-slate-700 leading-relaxed font-sans">
                        {s.cause_of_feedback}
                      </p>
                    </div>

                    {/* Precautions and Measures Taken 2-Column Grid */}
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                      {/* Precautions Box */}
                      <div className="p-5 rounded-2xl bg-amber-50/50 border border-amber-200 space-y-3">
                        <div className="flex items-center space-x-2">
                          <ShieldAlert className="w-4 h-4 text-[#CA8A04]" />
                          <h3 className="text-xs font-bold text-[#CA8A04] uppercase tracking-wider">
                            Recommended Prevention & Safeguards
                          </h3>
                        </div>
                        <ul className="space-y-2 text-xs">
                          {s.precautions?.map((p, idx) => (
                            <li key={idx} className="flex items-start space-x-2.5 text-slate-700">
                              <span className="w-1.5 h-1.5 rounded-full bg-[#CA8A04] mt-1.5 shrink-0" />
                              <span className="leading-relaxed">{p}</span>
                            </li>
                          ))}
                        </ul>
                      </div>

                      {/* Measures Taken Box (Interactive Task List) */}
                      <div className="p-5 rounded-2xl bg-emerald-50/50 border border-emerald-200 space-y-3">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center space-x-2">
                            <CheckCircle2 className="w-4 h-4 text-[#16A34A]" />
                            <h3 className="text-xs font-bold text-[#16A34A] uppercase tracking-wider">
                              Action Steps Taken & Status
                            </h3>
                          </div>
                          <span className="text-[10px] font-mono text-[#16A34A] bg-emerald-100 px-2 py-0.5 rounded-full font-bold">
                            {s.measures_taken?.length || 0} Actions Done
                          </span>
                        </div>

                        <ul className="space-y-2 text-xs">
                          {s.measures_taken?.map((m, idx) => (
                            <li key={idx} className="flex items-start space-x-2.5 p-2 rounded-xl bg-white border border-emerald-200 text-slate-800 shadow-xs">
                              <Check className="w-3.5 h-3.5 text-[#16A34A] mt-0.5 shrink-0" />
                              <span className="leading-relaxed">{m}</span>
                            </li>
                          ))}
                        </ul>

                        {/* Add New Measure Taken Form */}
                        <div className="pt-2 flex items-center space-x-2">
                          <input
                            type="text"
                            value={newMeasureText[s.id] || ''}
                            onChange={(e) => setNewMeasureText({ ...newMeasureText, [s.id]: e.target.value })}
                            onKeyDown={(e) => e.key === 'Enter' && handleAddMeasure(s.id)}
                            placeholder="Add action taken to resolve this..."
                            className="flex-1 bg-white border border-slate-200 rounded-xl px-3 py-1.5 text-xs text-slate-900 placeholder-slate-400 focus:outline-none focus:border-blue-600 focus:ring-1 focus:ring-blue-600"
                          />
                          <button
                            type="button"
                            onClick={() => handleAddMeasure(s.id)}
                            className="px-3.5 py-1.5 rounded-xl bg-[#2563EB] hover:bg-[#1E3A8A] text-white text-xs font-bold flex items-center space-x-1 shadow-xs transition"
                          >
                            <Plus className="w-3.5 h-3.5" />
                            <span>Add Step</span>
                          </button>
                        </div>
                      </div>
                    </div>

                    {/* Metadata Footer */}
                    <div className="pt-2 flex items-center justify-between text-[10px] text-slate-400 font-mono border-t border-slate-100">
                      <span>Report ID: {s.id}</span>
                      <span>Generated by: {s.created_by || 'AI Automated Intelligence'}</span>
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default MonitoredSummaries;
