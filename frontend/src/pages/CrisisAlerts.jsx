import React, { useState, useEffect } from 'react';
import { useBrand } from '../context/BrandContext';
import { crisisAPI } from '../services/api';
import { SeverityBadge } from '../components/common/StatusBadge';
import { 
  ShieldAlert, 
  AlertTriangle, 
  CheckCircle2, 
  Flame, 
  Lightbulb, 
  Clock, 
  RefreshCw, 
  AlertOctagon, 
  ShieldCheck 
} from 'lucide-react';

const CrisisAlerts = () => {
  const { activeBrand } = useBrand();

  const [alerts, setAlerts] = useState([]);
  const [statusMetrics, setStatusMetrics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [filterTab, setFilterTab] = useState('all'); // all, active, resolved
  const [simLoading, setSimLoading] = useState(false);
  const [notification, setNotification] = useState(null);

  const fetchAlerts = async () => {
    if (!activeBrand) return;
    try {
      const [alertsRes, statusRes] = await Promise.all([
        crisisAPI.getAlerts(activeBrand.id, 'all'),
        crisisAPI.getStatus(activeBrand.id)
      ]);
      setAlerts(alertsRes.data);
      setStatusMetrics(statusRes.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAlerts();
  }, [activeBrand]);

  const handleAcknowledge = async (alertId) => {
    try {
      await crisisAPI.acknowledgeAlert(alertId);
      setAlerts(prev => prev.map(a => a.id === alertId ? { ...a, status: 'acknowledged' } : a));
    } catch (err) {
      console.error(err);
    }
  };

  const handleResolve = async (alertId) => {
    try {
      await crisisAPI.resolveAlert(alertId);
      setAlerts(prev => prev.map(a => a.id === alertId ? { ...a, status: 'resolved' } : a));
    } catch (err) {
      console.error(err);
    }
  };

  const handleSimulateCrisisScenario = async (scenarioType) => {
    if (!activeBrand) return;
    setSimLoading(true);
    try {
      const res = await crisisAPI.simulateCrisis(activeBrand.id, scenarioType);
      setNotification(`Triggered ${scenarioType.replace('_', ' ')} incident! Injected ${res.data.injected_mentions_count} viral posts.`);
      setTimeout(() => setNotification(null), 4000);
      fetchAlerts();
    } catch (err) {
      console.error(err);
    } finally {
      setSimLoading(false);
    }
  };

  const filteredAlerts = alerts.filter(a => {
    if (filterTab === 'active') return a.status === 'active' || a.status === 'acknowledged';
    if (filterTab === 'resolved') return a.status === 'resolved';
    return true;
  });

  return (
    <div className="space-y-6 pb-12 animate-fade-in">
      {/* Header */}
      <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-3">
            <h1 className="text-xl lg:text-2xl font-extrabold text-slate-900 tracking-tight">
              Urgent Alerts & Issue Hub
            </h1>
            <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-red-50 text-[#DC2626] border border-red-200">
              Active Monitoring
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Automatically spots sudden complaint spikes, viral negative posts, and suggested responses.
          </p>
        </div>

        <button
          onClick={fetchAlerts}
          className="p-2 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 transition border border-slate-200"
          title="Refresh alerts"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin text-[#2563EB]' : ''}`} />
        </button>
      </div>

      {/* Anomaly Detector Metrics Bar */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm flex items-center justify-between">
          <div>
            <div className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Current Risk Level</div>
            <div className="text-2xl font-extrabold text-slate-900 mt-1">
              {statusMetrics?.current_risk_score || 0}%
            </div>
            <div className="text-[11px] text-slate-500 mt-0.5 capitalize">
              Risk Status: <strong className={statusMetrics?.current_risk_score > 50 ? 'text-[#DC2626]' : 'text-[#16A34A]'}>
                {statusMetrics?.current_severity || 'Healthy'}
              </strong>
            </div>
          </div>
          <div className={`p-3 rounded-xl ${statusMetrics?.current_risk_score > 50 ? 'bg-red-100 text-[#DC2626] animate-pulse' : 'bg-emerald-50 text-[#16A34A] border border-emerald-200'}`}>
            <ShieldAlert className="w-6 h-6" />
          </div>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm flex items-center justify-between">
          <div>
            <div className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Active Urgent Alerts</div>
            <div className="text-2xl font-extrabold text-slate-900 mt-1">
              {statusMetrics?.active_alerts_count || 0}
            </div>
            <div className="text-[11px] text-slate-500 mt-0.5">
              Requires review and response
            </div>
          </div>
          <div className="p-3 rounded-xl bg-amber-50 text-[#CA8A04] border border-amber-200">
            <AlertTriangle className="w-6 h-6" />
          </div>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm flex items-center justify-between">
          <div>
            <div className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Spike Scanner Status</div>
            <div className="text-sm font-bold text-[#16A34A] mt-2 flex items-center space-x-1.5">
              <div className="w-2 h-2 rounded-full bg-[#16A34A] live-indicator" />
              <span>ACTIVELY SCANNING</span>
            </div>
            <div className="text-[11px] text-slate-500 mt-0.5 font-mono">
              Window: last 30 customer posts
            </div>
          </div>
          <div className="p-3 rounded-xl bg-blue-50 text-[#2563EB] border border-blue-200">
            <ShieldCheck className="w-6 h-6" />
          </div>
        </div>
      </div>

      {/* Incident Triage Board */}
      <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4">
        <div className="flex items-center justify-between border-b border-slate-200 pb-4">
          <div>
            <h3 className="text-sm font-bold text-slate-900 tracking-tight">Crisis Incidents & Triage Queue</h3>
            <p className="text-xs text-slate-500">All automated anomaly spikes and resolution audit history</p>
          </div>

          <div className="flex items-center space-x-1.5 bg-slate-100 p-1 rounded-xl border border-slate-200 text-xs">
            {['all', 'active', 'resolved'].map((tab) => (
              <button
                key={tab}
                onClick={() => setFilterTab(tab)}
                className={`px-3 py-1 rounded-lg font-semibold capitalize transition ${
                  filterTab === tab
                    ? 'bg-[#2563EB] text-white shadow-sm'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                {tab}
              </button>
            ))}
          </div>
        </div>

        {/* Alerts List */}
        {filteredAlerts.length === 0 ? (
          <div className="py-12 text-center text-slate-500 text-xs space-y-2">
            <CheckCircle2 className="w-8 h-8 text-[#16A34A] mx-auto" />
            <p className="font-semibold text-slate-700">No crisis incidents found matching this status filter.</p>
          </div>
        ) : (
          <div className="space-y-4">
            {filteredAlerts.map((alert) => {
              const isResolved = alert.status === 'resolved';
              const isCritical = alert.severity === 'critical';

              return (
                <div
                  key={alert.id}
                  className={`p-5 rounded-2xl border transition space-y-3 shadow-sm ${
                    isResolved 
                      ? 'border-slate-200 opacity-75 bg-slate-50' 
                      : (isCritical ? 'border-red-200 bg-red-50/50 border-l-4 border-l-[#DC2626]' : 'border-amber-200 bg-yellow-50/50 border-l-4 border-l-[#EAB308]')
                  }`}
                >
                  {/* Card Header */}
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                    <div className="flex items-center space-x-3 flex-wrap">
                      <SeverityBadge severity={alert.severity} />
                      <h4 className="text-sm font-bold text-slate-900">{alert.title}</h4>
                    </div>

                    <div className="flex items-center space-x-2 text-[11px] font-mono text-slate-500">
                      <Clock className="w-3.5 h-3.5" />
                      <span>{new Date(alert.created_at).toLocaleString()}</span>
                    </div>
                  </div>

                  {/* Description */}
                  <p className="text-xs text-slate-700 leading-relaxed">
                    {alert.description}
                  </p>

                  {/* AI Root Cause */}
                  <div className="p-3 rounded-xl bg-white border border-slate-200 text-xs text-slate-700 space-y-1">
                    <div className="font-bold text-[#2563EB] flex items-center space-x-1.5">
                      <AlertOctagon className="w-3.5 h-3.5 text-[#2563EB]" />
                      <span>Root Cause Diagnosis:</span>
                    </div>
                    <p>{alert.ai_root_cause}</p>
                  </div>

                  {/* Recommendations */}
                  <div className="space-y-1.5 text-xs">
                    <div className="font-bold text-slate-800 flex items-center space-x-1.5">
                      <Lightbulb className="w-3.5 h-3.5 text-amber-500" />
                      <span>Actionable Next Steps:</span>
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                      {alert.recommendations?.map((rec, i) => (
                        <div key={i} className="p-2 rounded-lg bg-white border border-slate-200 text-slate-800 text-[11px] flex items-start space-x-1.5 shadow-xs">
                          <span className="w-3.5 h-3.5 rounded-full bg-blue-100 text-[#2563EB] font-mono text-[9px] flex items-center justify-center shrink-0 mt-0.5 font-bold">
                            {i + 1}
                          </span>
                          <span>{rec}</span>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Footer Actions */}
                  <div className="pt-2 border-t border-slate-200 flex items-center justify-between">
                    <div className="text-[11px] text-slate-500">
                      Status: <strong className="uppercase text-slate-800">{alert.status}</strong>
                      {alert.acknowledged_by && ` (Ack by ${alert.acknowledged_by})`}
                      {alert.resolved_at && ` (Resolved on ${new Date(alert.resolved_at).toLocaleTimeString()})`}
                    </div>

                    {!isResolved && (
                      <div className="flex items-center space-x-2">
                        {alert.status === 'active' && (
                          <button
                            onClick={() => handleAcknowledge(alert.id)}
                            className="px-3 py-1.5 rounded-xl bg-amber-50 hover:bg-amber-100 text-[#CA8A04] border border-amber-200 text-xs font-semibold transition"
                          >
                            Acknowledge Incident
                          </button>
                        )}
                        <button
                          onClick={() => handleResolve(alert.id)}
                          className="px-3 py-1.5 rounded-xl bg-[#16A34A] hover:bg-emerald-700 text-white text-xs font-semibold shadow-sm transition flex items-center space-x-1.5"
                        >
                          <CheckCircle2 className="w-3.5 h-3.5" />
                          <span>Resolve Incident</span>
                        </button>
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};

export default CrisisAlerts;
