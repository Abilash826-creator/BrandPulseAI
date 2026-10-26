import React from 'react';
import { BarChart2, Tag, Layers } from 'lucide-react';

const ModelArchitectureMetrics = ({ metrics }) => {
  return (
    <>
      {/* Row 3: Model Evaluation Details & Feature Importances */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Confusion Matrix Card */}
        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4">
          <div>
            <h3 className="text-sm font-bold text-slate-900 tracking-tight flex items-center space-x-2">
              <BarChart2 className="w-4 h-4 text-[#2563EB]" />
              <span>Confusion Matrix (Test Evaluation Set)</span>
            </h3>
            <p className="text-xs text-slate-500 mt-0.5">
              Stratified 20% validation split (1,805 holdout Apple smartphone mentions)
            </p>
          </div>

          {metrics?.confusion_matrix ? (
            <div className="overflow-x-auto pt-2">
              <table className="w-full text-center text-xs">
                <thead>
                  <tr className="text-slate-500 uppercase text-[10px] font-bold">
                    <th className="text-left pb-2">Actual \ Pred</th>
                    <th className="pb-2 text-[#16A34A]">Pred Pos</th>
                    <th className="pb-2 text-slate-600">Pred Neu</th>
                    <th className="pb-2 text-[#DC2626]">Pred Neg</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 font-mono text-xs">
                  <tr>
                    <td className="text-left py-2 font-sans font-semibold text-slate-800">Actual Positive</td>
                    <td className="py-2 bg-emerald-50 text-[#16A34A] font-bold">{metrics.confusion_matrix[0][0]}</td>
                    <td className="py-2 text-slate-600">{metrics.confusion_matrix[0][1]}</td>
                    <td className="py-2 text-slate-600">{metrics.confusion_matrix[0][2]}</td>
                  </tr>
                  <tr>
                    <td className="text-left py-2 font-sans font-semibold text-slate-800">Actual Neutral</td>
                    <td className="py-2 text-slate-600">{metrics.confusion_matrix[1][0]}</td>
                    <td className="py-2 bg-slate-100 text-slate-800 font-bold">{metrics.confusion_matrix[1][1]}</td>
                    <td className="py-2 text-slate-600">{metrics.confusion_matrix[1][2]}</td>
                  </tr>
                  <tr>
                    <td className="text-left py-2 font-sans font-semibold text-slate-800">Actual Negative</td>
                    <td className="py-2 text-slate-600">{metrics.confusion_matrix[2][0]}</td>
                    <td className="py-2 text-slate-600">{metrics.confusion_matrix[2][1]}</td>
                    <td className="py-2 bg-red-50 text-[#DC2626] font-bold">{metrics.confusion_matrix[2][2]}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          ) : (
            <div className="py-6 text-center text-slate-400 text-xs">Metrics loading...</div>
          )}
        </div>

        {/* Top Informative Feature Keywords */}
        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4">
          <div>
            <h3 className="text-sm font-bold text-slate-900 tracking-tight flex items-center space-x-2">
              <Tag className="w-4 h-4 text-[#7C3AED]" />
              <span>Top Informative N-Gram Tokens</span>
            </h3>
            <p className="text-xs text-slate-500 mt-0.5">
              TF-IDF coefficients driving positive advocacy and negative risk predictions
            </p>
          </div>

          <div className="space-y-3 pt-1 text-xs">
            {/* Positive Tokens */}
            <div>
              <span className="text-[11px] font-bold text-[#16A34A] block mb-1.5">Top Positive Indicators:</span>
              <div className="flex flex-wrap gap-1.5">
                {(metrics?.top_keywords_per_class?.positive || [
                  { term: "great", weight: 3.4 },
                  { term: "love", weight: 3.1 },
                  { term: "best", weight: 2.8 },
                  { term: "awesome", weight: 2.5 },
                  { term: "camera", weight: 2.2 },
                  { term: "amazing", weight: 2.1 },
                  { term: "good", weight: 1.9 }
                ]).map((k, i) => (
                  <span key={i} className="px-2 py-0.5 rounded-lg bg-emerald-50 border border-emerald-200 text-[#16A34A] font-mono text-[11px] font-medium">
                    {k.term} ({k.weight > 0 ? `+${k.weight}` : k.weight})
                  </span>
                ))}
              </div>
            </div>

            {/* Negative Tokens */}
            <div className="pt-2 border-t border-slate-100">
              <span className="text-[11px] font-bold text-[#DC2626] block mb-1.5">Top Negative Indicators:</span>
              <div className="flex flex-wrap gap-1.5">
                {(metrics?.top_keywords_per_class?.negative || [
                  { term: "worst", weight: -3.8 },
                  { term: "sucks", weight: -3.2 },
                  { term: "broken", weight: -2.9 },
                  { term: "disappointed", weight: -2.6 },
                  { term: "bad", weight: -2.4 },
                  { term: "battery", weight: -2.1 },
                  { term: "heating", weight: -1.9 }
                ]).map((k, i) => (
                  <span key={i} className="px-2 py-0.5 rounded-lg bg-red-50 border border-red-200 text-[#DC2626] font-mono text-[11px] font-medium">
                    {k.term} ({k.weight > 0 ? `+${k.weight}` : k.weight})
                  </span>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Row 4: Thematic KMeans Smartphone Clusters */}
      <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4">
        <div>
          <h3 className="text-sm font-bold text-slate-900 tracking-tight flex items-center space-x-2">
            <Layers className="w-4 h-4 text-[#2563EB]" />
            <span>KMeans Thematic Topic Clusters (Apple Smartphone Domain)</span>
          </h3>
          <p className="text-xs text-slate-500 mt-0.5">
            5 unsupervised thematic clusters extracted automatically from customer reviews & social media
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-3 pt-1">
          {(metrics?.thematic_clusters || [
            { cluster_id: 0, name: "Camera System & Macro Photography", top_terms: ["camera", "photos", "quality", "macro", "night"] },
            { cluster_id: 1, name: "Battery Longevity & Charging", top_terms: ["battery", "life", "health", "drain", "charge"] },
            { cluster_id: 2, name: "iOS Software & Speed", top_terms: ["ios", "update", "fast", "smooth", "apps"] },
            { cluster_id: 3, name: "Design & Display Build", top_terms: ["titanium", "screen", "display", "color", "lightweight"] },
            { cluster_id: 4, name: "Retail Pricing & Trade-in", top_terms: ["price", "worth", "money", "deal", "trade"] }
          ]).map((cluster, i) => (
            <div key={i} className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-2">
              <div className="text-[11px] font-bold text-slate-900 line-clamp-1">{cluster.name}</div>
              <div className="flex flex-wrap gap-1 pt-1">
                {cluster.top_terms.slice(0, 4).map((term, ti) => (
                  <span key={ti} className="px-1.5 py-0.5 rounded bg-white border border-slate-200 text-slate-700 text-[10px] font-mono">
                    #{term}
                  </span>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>
    </>
  );
};

export default ModelArchitectureMetrics;
