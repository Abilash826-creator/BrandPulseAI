import React from 'react';
import Modal from '../common/Modal';
import { Loader2, Send } from 'lucide-react';

const ManualMentionModal = ({
  isOpen,
  onClose,
  onSubmit,
  injectForm,
  setInjectForm,
  injectLoading
}) => {
  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Add Custom Social Post or Reel"
    >
      <form onSubmit={onSubmit} className="space-y-4 text-xs">
        <p className="text-slate-500">
          Simulate a real-time post from Instagram, X/Twitter, Reddit, or YouTube with instant AI sentiment, emotion, and aspect detection.
        </p>

        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="font-semibold text-slate-700 block mb-1">Platform</label>
            <select
              value={injectForm.platform}
              onChange={(e) => setInjectForm({ ...injectForm, platform: e.target.value })}
              className="w-full bg-white border border-slate-200 rounded-xl p-2.5 text-slate-900 focus:outline-none focus:border-blue-600"
            >
              <option value="instagram">Instagram (Meta)</option>
              <option value="twitter">X / Twitter</option>
              <option value="reddit">Reddit</option>
              <option value="linkedin">LinkedIn</option>
              <option value="news">Tech News</option>
              <option value="review">Trustpilot / Review</option>
            </select>
          </div>

          <div>
            <label className="font-semibold text-slate-700 block mb-1">Media Type</label>
            <select
              value={injectForm.media_type}
              onChange={(e) => setInjectForm({ ...injectForm, media_type: e.target.value })}
              className="w-full bg-white border border-slate-200 rounded-xl p-2.5 text-slate-900 focus:outline-none focus:border-blue-600"
            >
              <option value="REEL">Reel / Video</option>
              <option value="IMAGE">Image Post</option>
              <option value="CAROUSEL_ALBUM">Carousel Album</option>
              <option value="COMMENT">Public Comment</option>
            </select>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="font-semibold text-slate-700 block mb-1">Author Name</label>
            <input
              type="text"
              value={injectForm.author}
              onChange={(e) => setInjectForm({ ...injectForm, author: e.target.value })}
              required
              className="w-full bg-white border border-slate-200 rounded-xl p-2.5 text-slate-900 focus:outline-none focus:border-blue-600"
            />
          </div>

          <div>
            <label className="font-semibold text-slate-700 block mb-1">Handle / Username</label>
            <input
              type="text"
              value={injectForm.author_handle}
              onChange={(e) => setInjectForm({ ...injectForm, author_handle: e.target.value })}
              required
              className="w-full bg-white border border-slate-200 rounded-xl p-2.5 text-slate-900 focus:outline-none focus:border-blue-600"
            />
          </div>
        </div>

        <div>
          <label className="font-semibold text-slate-700 block mb-1">Post Caption</label>
          <textarea
            rows={2}
            value={injectForm.content}
            onChange={(e) => setInjectForm({ ...injectForm, content: e.target.value })}
            required
            className="w-full bg-white border border-slate-200 rounded-xl p-3 text-slate-900 focus:outline-none focus:border-blue-600"
            placeholder="Type post caption or comment..."
          />
        </div>

        {injectForm.media_type === 'REEL' && (
          <div>
            <label className="font-semibold text-slate-700 block mb-1">Reel Audio Transcript (Optional / Simulated Speech-to-Text)</label>
            <textarea
              rows={2}
              value={injectForm.transcript}
              onChange={(e) => setInjectForm({ ...injectForm, transcript: e.target.value })}
              className="w-full bg-white border border-slate-200 rounded-xl p-3 text-slate-900 focus:outline-none focus:border-blue-600 font-mono text-[11px]"
              placeholder="Spoken words in video..."
            />
          </div>
        )}

        <div className="flex justify-end space-x-2 pt-2 border-t border-slate-200">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 rounded-xl bg-slate-100 text-slate-700 hover:bg-slate-200 font-semibold transition"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={injectLoading}
            className="px-4 py-2 rounded-xl bg-[#2563EB] hover:bg-[#1E3A8A] text-white font-bold flex items-center space-x-1.5 shadow-sm transition disabled:opacity-50"
          >
            {injectLoading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Send className="w-3.5 h-3.5" />}
            <span>Analyze & Ingest Mention</span>
          </button>
        </div>
      </form>
    </Modal>
  );
};

export default ManualMentionModal;
