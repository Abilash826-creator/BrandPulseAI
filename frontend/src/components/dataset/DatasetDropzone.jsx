import React from 'react';
import { UploadCloud, CheckCircle2, AlertTriangle, Loader2, Eye, Tag } from 'lucide-react';

const DatasetDropzone = ({
  fileInputRef,
  dragActive,
  handleDrag,
  handleDrop,
  handleFileInputChange,
  selectedFile,
  errorMessage,
  previewLoading,
  previewData
}) => {
  return (
    <div className="space-y-4">
      <div 
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        className={`cursor-pointer rounded-2xl border-2 border-dashed p-8 text-center transition-all bg-white flex flex-col items-center justify-center space-y-3 ${
          dragActive 
            ? 'border-blue-600 bg-blue-50/50 ring-4 ring-blue-100' 
            : 'border-slate-300 hover:border-blue-400 hover:bg-slate-50/60 shadow-sm'
        }`}
      >
        <input 
          ref={fileInputRef}
          type="file"
          accept=".csv,.xlsx,.xls,.pdf,.json,.txt"
          onChange={handleFileInputChange}
          className="hidden"
        />

        <div className="w-14 h-14 rounded-2xl bg-blue-50 text-[#2563EB] flex items-center justify-center border border-blue-200 shadow-xs">
          <UploadCloud className="w-7 h-7" />
        </div>

        <div>
          <p className="text-sm font-bold text-slate-900">
            {selectedFile ? selectedFile.name : 'Click to upload or drag & drop dataset'}
          </p>
          <p className="text-xs text-slate-500 mt-0.5">
            Supports <strong className="text-slate-700">CSV & Excel (.xlsx, .xls)</strong> (Reviews, Mentions), <strong className="text-slate-700">PDF</strong> (Audits, Feedback), JSON & TXT
          </p>
        </div>


        {selectedFile && (
          <div className="flex items-center space-x-2 text-xs font-semibold px-3 py-1 rounded-full bg-emerald-50 text-[#16A34A] border border-emerald-200">
            <CheckCircle2 className="w-3.5 h-3.5" />
            <span>Selected: {(selectedFile.size / 1024).toFixed(1)} KB</span>
          </div>
        )}
      </div>

      {/* Error Message */}
      {errorMessage && (
        <div className="p-4 rounded-2xl bg-red-50 border border-red-200 text-red-800 text-xs font-semibold flex items-center space-x-2 animate-fade-in">
          <AlertTriangle className="w-4 h-4 text-[#DC2626] shrink-0" />
          <span>{errorMessage}</span>
        </div>
      )}

      {/* Real-Time File Preview Card */}
      {previewLoading && (
        <div className="bg-white p-6 rounded-2xl border border-slate-200 text-center text-xs text-slate-500 space-y-2">
          <Loader2 className="w-5 h-5 text-[#2563EB] animate-spin mx-auto" />
          <span>Analyzing file structure and extracting preview rows...</span>
        </div>
      )}

      {previewData && !previewLoading && (
        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm space-y-3 animate-fade-in">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <div className="flex items-center space-x-2">
              <Eye className="w-4 h-4 text-[#2563EB]" />
              <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
                File Structure & Entity Preview ({previewData.format.toUpperCase()})
              </h3>
            </div>
            {previewData.extracted_products && previewData.extracted_products.length > 0 && (
              <div className="flex items-center space-x-1 text-[11px] font-semibold text-[#16A34A] bg-emerald-50 px-2.5 py-0.5 rounded-full border border-emerald-200">
                <Tag className="w-3 h-3" />
                <span>Detected: {previewData.extracted_products.join(', ')}</span>
              </div>
            )}
          </div>

          {/* Sample Records Snippet */}
          <div className="space-y-2 max-h-56 overflow-y-auto pr-1">
            {previewData.sample_records?.slice(0, 4).map((rec, i) => (
              <div key={i} className="p-3 rounded-xl bg-slate-50 border border-slate-200 text-xs space-y-1">
                <div className="flex items-center justify-between text-[10px] text-slate-500 font-mono">
                  <span>Record #{i + 1}</span>
                  {rec.product && <span className="font-bold text-[#2563EB]">{rec.product}</span>}
                </div>
                <p className="text-slate-800 text-[11px] line-clamp-2">
                  {rec.content || rec.text || rec.review || JSON.stringify(rec)}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default DatasetDropzone;
