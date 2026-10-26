import React from 'react';
import { Sliders, UploadCloud, Loader2 } from 'lucide-react';

const IngestionConfigCard = ({
  brands = [],
  targetBrandMode,
  setTargetBrandMode,
  selectedBrandId,
  setSelectedBrandId,
  newBrandName,
  setNewBrandName,
  productNameInput,
  setProductNameInput,
  autoDetectProduct,
  setAutoDetectProduct,
  ingestionMode,
  setIngestionMode,
  generateSummary,
  setGenerateSummary,
  handleUploadAndProcess,
  selectedFile,
  processing,
}) => {
  return (
    <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4 text-xs">
      <div className="flex items-center space-x-2 border-b border-slate-100 pb-3">
        <Sliders className="w-4 h-4 text-[#2563EB]" />
        <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
          Model Feeding & Brand Target Configuration
        </h3>
      </div>

      {/* Target Brand Mode */}
      <div className="space-y-2">
        <label className="text-xs font-semibold text-slate-700 block">Target Brand Context:</label>
        <div className="grid grid-cols-3 gap-1.5 bg-slate-100 p-1 rounded-xl text-xs">
          <button
            type="button"
            onClick={() => setTargetBrandMode('active')}
            className={`py-1.5 rounded-lg font-semibold transition ${
              targetBrandMode === 'active' ? 'bg-white text-slate-900 shadow-xs' : 'text-slate-600'
            }`}
          >
            Active Brand
          </button>
          <button
            type="button"
            onClick={() => setTargetBrandMode('existing')}
            className={`py-1.5 rounded-lg font-semibold transition ${
              targetBrandMode === 'existing' ? 'bg-white text-slate-900 shadow-xs' : 'text-slate-600'
            }`}
          >
            Select Brand
          </button>
          <button
            type="button"
            onClick={() => setTargetBrandMode('new')}
            className={`py-1.5 rounded-lg font-semibold transition ${
              targetBrandMode === 'new' ? 'bg-white text-slate-900 shadow-xs' : 'text-slate-600'
            }`}
          >
            + New Brand
          </button>
        </div>

        {targetBrandMode === 'existing' && (
          <select
            value={selectedBrandId}
            onChange={(e) => setSelectedBrandId(e.target.value)}
            className="w-full bg-white border border-slate-200 rounded-xl p-2.5 text-xs text-slate-900 focus:outline-none focus:border-blue-600"
          >
            {brands.map(b => (
              <option key={b.id} value={b.id}>{b.name} ({b.industry})</option>
            ))}
          </select>
        )}

        {targetBrandMode === 'new' && (
          <input
            type="text"
            value={newBrandName}
            onChange={(e) => setNewBrandName(e.target.value)}
            placeholder="e.g. Acme Tech Corporation"
            className="w-full bg-white border border-slate-200 rounded-xl p-2.5 text-xs text-slate-900 focus:outline-none focus:border-blue-600"
          />
        )}
      </div>

      {/* Product Name Input */}
      <div className="space-y-2 pt-1 border-t border-slate-100">
        <div className="flex items-center justify-between">
          <label className="text-xs font-semibold text-slate-700">Tracked Product Name:</label>
          <button
            type="button"
            onClick={() => setAutoDetectProduct(!autoDetectProduct)}
            className={`text-[10px] font-bold px-2 py-0.5 rounded-md transition ${
              autoDetectProduct ? 'bg-blue-50 text-[#2563EB] border border-blue-200' : 'bg-slate-100 text-slate-500'
            }`}
          >
            {autoDetectProduct ? '✓ Auto-Detect Active' : 'Manual Override'}
          </button>
        </div>
        <input
          type="text"
          value={productNameInput}
          onChange={(e) => setProductNameInput(e.target.value)}
          placeholder="e.g. iPhone 16 Pro, Ghee Roast, or Cloud API"
          className="w-full bg-white border border-slate-200 rounded-xl p-2.5 text-xs text-slate-900 focus:outline-none focus:border-blue-600"
        />
        <p className="text-[10px] text-slate-500">
          This product name will be registered into the brand profile and displayed on dashboard aspect meters.
        </p>
      </div>

      {/* Ingestion Mode */}
      <div className="space-y-2 pt-1 border-t border-slate-100">
        <label className="text-xs font-semibold text-slate-700 block">How to add this data:</label>
        <div className="grid grid-cols-2 gap-2 text-xs">
          <label className={`p-3 rounded-xl border cursor-pointer transition flex items-start space-x-2 ${
            ingestionMode === 'append' ? 'border-blue-500 bg-blue-50/50' : 'border-slate-200 bg-white'
          }`}>
            <input
              type="radio"
              name="mode"
              checked={ingestionMode === 'append'}
              onChange={() => setIngestionMode('append')}
              className="mt-0.5 text-blue-600"
            />
            <div>
              <span className="font-bold text-slate-900 block text-[11px]">Add to Existing Data</span>
              <span className="text-[10px] text-slate-500">Keeps past posts and adds new ones</span>
            </div>
          </label>

          <label className={`p-3 rounded-xl border cursor-pointer transition flex items-start space-x-2 ${
            ingestionMode === 'replace' ? 'border-blue-500 bg-blue-50/50' : 'border-slate-200 bg-white'
          }`}>
            <input
              type="radio"
              name="mode"
              checked={ingestionMode === 'replace'}
              onChange={() => setIngestionMode('replace')}
              className="mt-0.5 text-blue-600"
            />
            <div>
              <span className="font-bold text-slate-900 block text-[11px]">Replace Current Data</span>
              <span className="text-[10px] text-slate-500">Clears past posts and uses only this file</span>
            </div>
          </label>
        </div>
      </div>

      {/* Generate Summary Checkbox */}
      <div className="flex items-center space-x-2 pt-1">
        <input
          type="checkbox"
          id="summary-cb"
          checked={generateSummary}
          onChange={(e) => setGenerateSummary(e.target.checked)}
          className="w-4 h-4 text-blue-600 rounded"
        />
        <label htmlFor="summary-cb" className="text-xs text-slate-700 font-medium">
          Create AI Summary Report automatically
        </label>
      </div>

      {/* Action Trigger Button */}
      <button
        onClick={handleUploadAndProcess}
        disabled={!selectedFile || processing}
        className="w-full py-3 rounded-xl bg-[#2563EB] hover:bg-[#1E3A8A] text-white font-bold text-xs shadow-sm transition flex items-center justify-center space-x-2 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {processing ? (
          <>
            <Loader2 className="w-4 h-4 animate-spin" />
            <span>Analyzing File with AI...</span>
          </>
        ) : (
          <>
            <UploadCloud className="w-4 h-4" />
            <span>Upload & Analyze File</span>
          </>
        )}
      </button>
    </div>
  );
};

export default IngestionConfigCard;
