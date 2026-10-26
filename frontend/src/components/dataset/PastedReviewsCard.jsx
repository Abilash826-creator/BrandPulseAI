import React from 'react';
import { FileText, Loader2 } from 'lucide-react';

const PastedReviewsCard = ({
  pastedSource,
  setPastedSource,
  pastedRating,
  setPastedRating,
  pastedText,
  setPastedText,
  errorMessage,
  processing,
  handlePasteReviews
}) => {
  return (
    <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4 text-xs">
      <div>
        <h3 className="font-bold text-slate-900 text-sm">Paste Customer Reviews or WhatsApp Messages</h3>
        <p className="text-slate-500 text-xs mt-0.5">
          Paste raw text copied from WhatsApp feedback, review screenshots (OCR), or offline comment registers.
        </p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        <div>
          <label className="block font-semibold text-slate-700 mb-1">Feedback Channel / Source:</label>
          <select
            value={pastedSource}
            onChange={(e) => setPastedSource(e.target.value)}
            className="w-full bg-white border border-slate-200 rounded-xl p-2.5 text-xs text-slate-900 focus:outline-none focus:border-blue-600"
          >
            <option value="WhatsApp Feedback">WhatsApp Customer Message</option>
            <option value="Google Reviews Screenshot">Google Maps Screenshot</option>
            <option value="Offline Register">Offline Visitor Book / Register</option>
            <option value="Swiggy / Zomato Feedback">Swiggy / Zomato Feedback</option>
            <option value="Pasted Feedback">General Pasted Feedback</option>
          </select>
        </div>

        <div>
          <label className="block font-semibold text-slate-700 mb-1">Default Rating (if not detected):</label>
          <select
            value={pastedRating}
            onChange={(e) => setPastedRating(e.target.value)}
            className="w-full bg-white border border-slate-200 rounded-xl p-2.5 text-xs text-slate-900 focus:outline-none focus:border-blue-600"
          >
            <option value="5">5 Stars (★★★★★)</option>
            <option value="4">4 Stars (★★★★)</option>
            <option value="3">3 Stars (★★★)</option>
            <option value="2">2 Stars (★★)</option>
            <option value="1">1 Star (★)</option>
          </select>
        </div>
      </div>

      <div>
        <label className="block font-semibold text-slate-700 mb-1">
          Customer Review Content (One review per line or separate paragraphs):
        </label>
        <textarea
          rows={8}
          value={pastedText}
          onChange={(e) => setPastedText(e.target.value)}
          placeholder={`Example:\nDelicious dosa and hot filter coffee, best breakfast place in town! 5 stars\nVery poor service today. Waited 45 mins and the waiter forgot our order.\nSuper friendly staff and very clean dining area.`}
          className="w-full p-3 bg-white border border-slate-200 rounded-xl text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-1 focus:ring-blue-600 font-mono text-xs leading-relaxed"
        />
      </div>

      {errorMessage && (
        <div className="p-3 rounded-xl bg-red-50 text-red-700 font-semibold text-xs border border-red-200">
          {errorMessage}
        </div>
      )}

      <button
        type="button"
        onClick={handlePasteReviews}
        disabled={processing || !pastedText.trim()}
        className="w-full py-3 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs shadow-sm transition flex items-center justify-center space-x-2 disabled:opacity-50"
      >
        {processing ? (
          <>
            <Loader2 className="w-4 h-4 animate-spin" />
            <span>Analyzing Reviews with AI...</span>
          </>
        ) : (
          <>
            <FileText className="w-4 h-4" />
            <span>Parse & Ingest Pasted Reviews</span>
          </>
        )}
      </button>
    </div>
  );
};

export default PastedReviewsCard;
