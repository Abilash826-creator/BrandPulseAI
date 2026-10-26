import React, { useState, useEffect } from 'react';
import { useBrand } from '../context/BrandContext';
import { reportsAPI, analyticsAPI } from '../services/api';
import { 
  FileText, 
  Download, 
  Sparkles, 
  FileSpreadsheet, 
  FileCode, 
  Clock, 
  CheckCircle2, 
  Loader2, 
  RefreshCw,
  Share2
} from 'lucide-react';

const Reports = () => {
  const { activeBrand } = useBrand();

  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [reportType, setReportType] = useState('executive_summary');
  const [timeRange, setTimeRange] = useState('7d');
  const [format, setFormat] = useState('pdf');
  const [insights, setInsights] = useState(null);

  const fetchHistory = async () => {
    if (!activeBrand) return;
    try {
      const [histRes, insRes] = await Promise.all([
        reportsAPI.getHistory(activeBrand.id),
        analyticsAPI.getInsights(activeBrand.id)
      ]);
      setHistory(histRes.data);
      setInsights(insRes.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHistory();
  }, [activeBrand]);

  const [downloadingFilename, setDownloadingFilename] = useState(null);

  const handleDownloadFile = async (filename) => {
    try {
      setDownloadingFilename(filename);
      await reportsAPI.downloadReport(filename);
    } catch (err) {
      console.error('Download error:', err);
      // Fallback to direct navigation with token query param
      const url = reportsAPI.getDownloadUrl(filename);
      window.location.href = url;
    } finally {
      setDownloadingFilename(null);
    }
  };

  const handleGenerate = async (e) => {
    e.preventDefault();
    if (!activeBrand) return;
    setGenerating(true);
    try {
      const res = await reportsAPI.generate({
        brand_id: activeBrand.id,
        report_type: reportType,
        time_range: timeRange,
        format: format
      });
      fetchHistory();

      // Trigger automatic direct browser download via blob
      if (res.data?.filename) {
        await reportsAPI.downloadReport(res.data.filename);
      }
    } catch (err) {
      console.error('Failed to generate report:', err);
    } finally {
      setGenerating(false);
    }
  };

  return (
    <div className="space-y-6 pb-12 animate-fade-in">
      {/* Header */}
      <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-3">
            <h1 className="text-xl lg:text-2xl font-extrabold text-slate-900 tracking-tight">
              Download Reports & Data
            </h1>
            <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-blue-50 text-[#2563EB] border border-blue-200">
              PDF / CSV / JSON
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Download PDF summary reports, spreadsheet CSV files, or raw JSON data.
          </p>
        </div>

        <button
          onClick={fetchHistory}
          className="p-2 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 transition border border-slate-200"
          title="Refresh download history"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin text-[#2563EB]' : ''}`} />
        </button>
      </div>

      {/* Generator Form & Format Chooser */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-5">
          <div>
            <h3 className="text-sm font-bold text-slate-900 tracking-tight flex items-center space-x-2">
              <FileText className="w-4 h-4 text-[#2563EB]" />
              <span>Create New Report</span>
            </h3>
            <p className="text-xs text-slate-500 mt-0.5">
              Choose what to include and select a file format to download.
            </p>
          </div>

          <form onSubmit={handleGenerate} className="space-y-4 text-xs">
            {/* Report Type */}
            <div>
              <label className="font-semibold text-slate-700 block mb-2">Report Content</label>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                {[
                  { id: 'executive_summary', title: 'Executive Summary', desc: 'Overall customer satisfaction score & key recommendations' },
                  { id: 'full_audit', title: 'Full Brand Report', desc: 'Complete breakdown with emotions, topics, and post volumes' },
                  { id: 'crisis_postmortem', title: 'Urgent Issues Report', desc: 'Log of complaint spikes, root causes & action steps' },
                ].map((t) => (
                  <button
                    key={t.id}
                    type="button"
                    onClick={() => setReportType(t.id)}
                    className={`p-3.5 rounded-xl border text-left transition ${
                      reportType === t.id
                        ? 'bg-blue-50 border-[#2563EB] text-[#2563EB] shadow-xs'
                        : 'bg-white border-slate-200 text-slate-700 hover:bg-slate-50'
                    }`}
                  >
                    <div className="font-bold text-xs text-slate-900">{t.title}</div>
                    <div className="text-[10px] text-slate-500 mt-1">{t.desc}</div>
                  </button>
                ))}
              </div>
            </div>

            {/* Time Range & Format */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="font-semibold text-slate-700 block mb-2">Time Period</label>
                <div className="grid grid-cols-3 gap-2">
                  {['24h', '7d', '30d'].map((r) => (
                    <button
                      key={r}
                      type="button"
                      onClick={() => setTimeRange(r)}
                      className={`py-2 rounded-xl border text-center font-bold font-mono transition ${
                        timeRange === r
                          ? 'bg-[#2563EB] border-[#2563EB] text-white shadow-xs'
                          : 'bg-white border-slate-200 text-slate-700 hover:bg-slate-50'
                      }`}
                    >
                      {r.toUpperCase()}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="font-semibold text-slate-700 block mb-2">File Format</label>
                <div className="grid grid-cols-3 gap-2">
                  {[
                    { id: 'pdf', label: 'PDF Document', icon: FileText },
                    { id: 'csv', label: 'Excel / CSV', icon: FileSpreadsheet },
                    { id: 'json', label: 'Raw JSON', icon: FileCode },
                  ].map((f) => {
                    const Icon = f.icon;
                    return (
                      <button
                        key={f.id}
                        type="button"
                        onClick={() => setFormat(f.id)}
                        className={`py-2 px-1 rounded-xl border flex items-center justify-center space-x-1.5 font-bold transition ${
                          format === f.id
                            ? 'bg-[#2563EB] border-[#2563EB] text-white shadow-xs'
                            : 'bg-white border-slate-200 text-slate-700 hover:bg-slate-50'
                        }`}
                      >
                        <Icon className="w-3.5 h-3.5" />
                        <span>{f.label}</span>
                      </button>
                    );
                  })}
                </div>
              </div>
            </div>

            {/* Submit Button */}
            <div className="pt-2">
              <button
                type="submit"
                disabled={generating}
                className="w-full py-3 rounded-xl bg-[#2563EB] hover:bg-[#1E3A8A] text-white font-bold text-xs shadow-sm transition flex items-center justify-center space-x-2 disabled:opacity-50"
              >
                {generating ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    <span>Compiling Report & Generating Document...</span>
                  </>
                ) : (
                  <>
                    <Download className="w-4 h-4" />
                    <span>Compile & Download {format.toUpperCase()} Report</span>
                  </>
                )}
              </button>
            </div>
          </form>
        </div>

        {/* Live Executive Brief Preview */}
        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4 flex flex-col justify-between">
          <div className="space-y-3">
            <div className="flex items-center space-x-2 text-[#7C3AED]">
              <Sparkles className="w-4 h-4" />
              <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wider">Executive Brief Summary</h4>
            </div>

            <div className="p-3.5 rounded-xl bg-purple-50/50 border border-purple-100 text-xs text-slate-700 leading-relaxed">
              {insights?.executive_summary || 'No review data available yet to generate an executive brief. Ingest customer feedback to see real-time insights.'}
            </div>

            <div className="space-y-2 text-xs">
              <div className="font-semibold text-slate-800">Strategic PR Actions:</div>
              <div className="space-y-1.5">
                {insights?.recommended_actions?.slice(0, 2).map((rec, i) => (
                  <div key={i} className="p-2 rounded-xl bg-emerald-50/70 border border-emerald-200 text-emerald-900 text-[11px] flex items-start space-x-2">
                    <CheckCircle2 className="w-3.5 h-3.5 text-[#16A34A] shrink-0 mt-0.5" />
                    <span>{rec}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          <div className="pt-3 border-t border-slate-200 text-[11px] text-slate-500 font-mono flex items-center justify-between">
            <span>Branded for {activeBrand?.name}</span>
            <span className="text-[#16A34A] font-semibold">ReportLab Engine</span>
          </div>
        </div>
      </div>

      {/* Generated Reports History Audit Table */}
      <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4">
        <div className="flex items-center justify-between border-b border-slate-200 pb-4">
          <div>
            <h3 className="text-sm font-bold text-slate-900 tracking-tight">Export & Audit History</h3>
            <p className="text-xs text-slate-500">Past generated analytical briefs with direct download links</p>
          </div>
          <span className="text-xs font-mono font-semibold text-slate-600 bg-slate-100 px-3 py-1 rounded-xl border border-slate-200">
            {history.length} Reports Archived
          </span>
        </div>

        {history.length === 0 ? (
          <div className="py-10 text-center text-slate-500 text-xs">
            No reports generated yet. Compile your first report above!
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-slate-200 text-slate-500 uppercase text-[10px] font-bold tracking-wider">
                  <th className="pb-3">Report Name / File</th>
                  <th className="pb-3">Template</th>
                  <th className="pb-3">Format</th>
                  <th className="pb-3">Time Range</th>
                  <th className="pb-3">Generated Date</th>
                  <th className="pb-3 text-right">Download</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {history.map((item) => (
                  <tr key={item.id} className="transition hover:bg-slate-50">
                    <td className="py-3.5 font-mono text-[#2563EB] font-semibold flex items-center space-x-2">
                      <FileText className="w-4 h-4 text-slate-400" />
                      <span className="truncate max-w-xs">{item.filename}</span>
                    </td>
                    <td className="py-3.5 text-slate-700 capitalize">
                      {item.report_type?.replace(/_/g, ' ')}
                    </td>
                    <td className="py-3.5">
                      <span className="uppercase font-mono font-bold text-[10px] px-2 py-0.5 rounded bg-blue-50 text-[#2563EB] border border-blue-200">
                        {item.format}
                      </span>
                    </td>
                    <td className="py-3.5 font-mono text-slate-500">{item.time_range?.toUpperCase()}</td>
                    <td className="py-3.5 text-slate-500 flex items-center space-x-1">
                      <Clock className="w-3 h-3" />
                      <span>{new Date(item.created_at).toLocaleString()}</span>
                    </td>
                    <td className="py-3.5 text-right space-x-2">
                      <a
                        href={`https://api.whatsapp.com/send?text=${encodeURIComponent(
                          `BrandPulse Health Report for ${activeBrand?.name || 'our business'}: ${item.report_type?.replace(/_/g, ' ')} (${item.time_range?.toUpperCase()}). Download file: ${window.location.origin}${reportsAPI.getDownloadUrl(item.filename)}`
                        )}`}
                        target="_blank"
                        rel="noreferrer"
                        className="inline-flex items-center space-x-1 px-2.5 py-1.5 rounded-xl bg-emerald-50 hover:bg-emerald-100 border border-emerald-200 text-emerald-700 font-bold transition text-xs shadow-xs"
                        title="Share report summary via WhatsApp"
                      >
                        <Share2 className="w-3.5 h-3.5 text-emerald-600" />
                        <span>WhatsApp</span>
                      </a>
                      <button
                        type="button"
                        onClick={() => handleDownloadFile(item.filename)}
                        disabled={downloadingFilename === item.filename}
                        className="inline-flex items-center space-x-1 px-3 py-1.5 rounded-xl bg-blue-50 hover:bg-blue-100 border border-blue-200 text-[#2563EB] font-bold transition text-xs shadow-xs disabled:opacity-50"
                        title="Download report file"
                      >
                        {downloadingFilename === item.filename ? (
                          <Loader2 className="w-3.5 h-3.5 animate-spin" />
                        ) : (
                          <Download className="w-3.5 h-3.5" />
                        )}
                        <span>Download</span>
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};

export default Reports;
