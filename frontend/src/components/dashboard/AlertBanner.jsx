import React, { useState } from 'react';
import { SeverityBadge } from '../common/StatusBadge';
import { ShieldAlert, CheckCircle2, ChevronRight, AlertOctagon, Lightbulb } from 'lucide-react';
import Modal from '../common/Modal';

const AlertBanner = ({ alerts = [], onAcknowledge, onResolve }) => {
  const [selectedAlert, setSelectedAlert] = useState(null);
  const activeAlerts = alerts.filter(a => a.status === 'active' || a.status === 'acknowledged');

  if (activeAlerts.length === 0) return null;

  const topAlert = activeAlerts[0];
  const isCritical = topAlert.severity === 'critical';
  const isWarning = topAlert.severity === 'warning' || topAlert.severity === 'high';

  return (
    <>
      <div 
        className={`p-4 rounded-2xl border mb-6 relative overflow-hidden transition-all shadow-sm ${
          isCritical 
            ? 'bg-red-50/80 border-red-200 border-l-4 border-l-[#DC2626]' 
            : isWarning
            ? 'bg-orange-50/80 border-orange-200 border-l-4 border-l-[#F97316]'
            : 'bg-yellow-50/80 border-yellow-200 border-l-4 border-l-[#EAB308]'
        }`}
      >
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
          <div className="flex items-start space-x-3.5">
            <div className={`p-2.5 rounded-xl shrink-0 ${
              isCritical 
                ? 'bg-red-100 text-[#DC2626] border border-red-200' 
                : 'bg-amber-100 text-[#CA8A04] border border-amber-200'
            }`}>
              <ShieldAlert className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center space-x-2.5 flex-wrap gap-1">
                <SeverityBadge severity={topAlert.severity} />
                <span className="text-xs font-bold text-slate-900 tracking-tight">{topAlert.title}</span>
                {activeAlerts.length > 1 && (
                  <span className="text-[10px] px-2 py-0.5 rounded-full bg-white text-slate-600 border border-slate-200 font-medium">
                    +{activeAlerts.length - 1} other active alerts
                  </span>
                )}
              </div>
              <p className="text-xs text-slate-700 mt-1 leading-relaxed">
                {topAlert.description}
              </p>
              <div className="text-[11px] text-slate-500 mt-1 flex items-center space-x-1 font-mono">
                <span className="text-[#2563EB] font-semibold">AI Root Cause:</span>
                <span className="truncate max-w-xl text-slate-700">{topAlert.ai_root_cause}</span>
              </div>
            </div>
          </div>

          {/* Action buttons */}
          <div className="flex items-center space-x-2 self-end md:self-center shrink-0">
            <button
              onClick={() => setSelectedAlert(topAlert)}
              className="px-3 py-1.5 rounded-xl bg-white hover:bg-slate-50 text-xs font-semibold text-slate-800 border border-slate-200 flex items-center space-x-1 transition shadow-sm"
            >
              <span>View Mitigation Plan</span>
              <ChevronRight className="w-3.5 h-3.5" />
            </button>

            {topAlert.status === 'active' && onAcknowledge && (
              <button
                onClick={() => onAcknowledge(topAlert.id)}
                className="px-3 py-1.5 rounded-xl bg-amber-50 hover:bg-amber-100 text-[#CA8A04] border border-amber-200 text-xs font-semibold transition"
              >
                Acknowledge
              </button>
            )}

            {onResolve && (
              <button
                onClick={() => onResolve(topAlert.id)}
                className="px-3 py-1.5 rounded-xl bg-emerald-50 hover:bg-emerald-100 text-[#16A34A] border border-emerald-200 text-xs font-semibold flex items-center space-x-1 transition"
              >
                <CheckCircle2 className="w-3.5 h-3.5" />
                <span>Resolve</span>
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Mitigation Details Modal */}
      {selectedAlert && (
        <Modal
          isOpen={!!selectedAlert}
          onClose={() => setSelectedAlert(null)}
          title="Crisis Anomaly Mitigation & Action Protocol"
          maxWidth="max-w-2xl"
        >
          <div className="space-y-4 text-xs">
            <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-2">
              <div className="flex items-center justify-between">
                <SeverityBadge severity={selectedAlert.severity} />
                <span className="text-[10px] text-slate-500 font-mono">
                  Trigger Value: {selectedAlert.trigger_value}% (Threshold: {selectedAlert.threshold_value}%)
                </span>
              </div>
              <div className="text-sm font-bold text-slate-900">{selectedAlert.title}</div>
              <p className="text-slate-700 leading-relaxed">{selectedAlert.description}</p>
            </div>

            {/* Root Cause */}
            <div className="p-3.5 rounded-xl bg-blue-50 border border-blue-200 space-y-1">
              <div className="font-bold text-[#2563EB] flex items-center space-x-1.5">
                <AlertOctagon className="w-4 h-4 text-[#2563EB]" />
                <span>Automated Root Cause Diagnosis</span>
              </div>
              <p className="text-slate-700 leading-relaxed">{selectedAlert.ai_root_cause}</p>
            </div>

            {/* Recommendations */}
            <div className="space-y-2">
              <div className="font-bold text-slate-900 flex items-center space-x-1.5">
                <Lightbulb className="w-4 h-4 text-amber-500" />
                <span>Recommended Action Plan & PR Protocol</span>
              </div>
              <div className="space-y-1.5">
                {selectedAlert.recommendations?.map((rec, idx) => (
                  <div key={idx} className="p-2.5 rounded-lg bg-slate-50 border border-slate-200 flex items-start space-x-2 text-slate-800">
                    <span className="w-4 h-4 rounded-full bg-blue-100 text-[#2563EB] font-mono text-[10px] flex items-center justify-center shrink-0 mt-0.5 font-bold">
                      {idx + 1}
                    </span>
                    <span className="leading-relaxed">{rec}</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="flex justify-end space-x-2 pt-3 border-t border-slate-200">
              <button
                onClick={() => setSelectedAlert(null)}
                className="px-4 py-2 rounded-xl bg-slate-100 text-slate-700 hover:bg-slate-200 transition font-semibold text-xs"
              >
                Close
              </button>
              {onResolve && (
                <button
                  onClick={() => {
                    onResolve(selectedAlert.id);
                    setSelectedAlert(null);
                  }}
                  className="px-4 py-2 rounded-xl bg-[#16A34A] hover:bg-emerald-700 text-white font-semibold text-xs transition flex items-center space-x-1.5 shadow-sm"
                >
                  <CheckCircle2 className="w-4 h-4" />
                  <span>Mark Incident as Resolved</span>
                </button>
              )}
            </div>
          </div>
        </Modal>
      )}
    </>
  );
};

export default AlertBanner;
