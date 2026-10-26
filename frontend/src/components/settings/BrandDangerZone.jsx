import React from 'react';
import Modal from '../common/Modal';
import { Trash2, AlertTriangle, Loader2 } from 'lucide-react';

const BrandDangerZone = ({
  activeBrand,
  showDeleteModal,
  setShowDeleteModal,
  deleting,
  handleDeleteBrand
}) => {
  if (!activeBrand) return null;

  return (
    <>
      {/* Danger Zone Card */}
      <div className="bg-red-50/50 p-6 rounded-2xl border border-red-200 space-y-3 shadow-sm">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h3 className="text-sm font-bold text-red-700 tracking-tight flex items-center space-x-2">
              <Trash2 className="w-4 h-4 text-red-600" />
              <span>Delete Brand Workspace</span>
            </h3>
            <p className="text-xs text-slate-500 mt-1">
              Permanently delete <strong className="text-slate-800">{activeBrand.name}</strong> and all its associated mentions, alerts, summaries, and intelligence datasets.
            </p>
          </div>
          <button
            type="button"
            onClick={() => setShowDeleteModal(true)}
            className="px-4 py-2.5 rounded-xl bg-red-600 hover:bg-red-700 text-white font-bold text-xs shadow-sm transition flex items-center justify-center space-x-2 shrink-0"
          >
            <Trash2 className="w-4 h-4" />
            <span>Delete Brand</span>
          </button>
        </div>
      </div>

      {/* Delete Confirmation Modal */}
      <Modal
        isOpen={showDeleteModal}
        onClose={() => {
          if (!deleting) setShowDeleteModal(false);
        }}
        title="Delete Monitored Brand Workspace"
        maxWidth="max-w-md"
      >
        <div className="space-y-4">
          <div className="p-3.5 bg-red-50 border border-red-200 rounded-2xl flex items-start space-x-3">
            <AlertTriangle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
            <div className="text-xs text-red-800 space-y-1">
              <p className="font-bold text-red-900">Irreversible Action</p>
              <p>
                Are you sure you want to permanently delete <strong className="text-red-950 font-bold underline">{activeBrand?.name}</strong>?
              </p>
            </div>
          </div>

          <p className="text-xs text-slate-600 leading-relaxed">
            This will permanently erase all social mentions, sentiment timelines, crisis alerts, and intelligence reports for this brand. This cannot be recovered.
          </p>

          <div className="flex items-center justify-end space-x-3 pt-3 border-t border-slate-100">
            <button
              type="button"
              disabled={deleting}
              onClick={() => setShowDeleteModal(false)}
              className="px-4 py-2 rounded-xl border border-slate-200 text-xs font-semibold text-slate-700 hover:bg-slate-50 transition"
            >
              Cancel
            </button>
            <button
              type="button"
              disabled={deleting}
              onClick={handleDeleteBrand}
              className="px-4 py-2 rounded-xl bg-red-600 hover:bg-red-700 text-white text-xs font-bold shadow-sm transition flex items-center space-x-2 disabled:opacity-50"
            >
              {deleting ? (
                <>
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  <span>Deleting...</span>
                </>
              ) : (
                <>
                  <Trash2 className="w-3.5 h-3.5" />
                  <span>Delete Brand</span>
                </>
              )}
            </button>
          </div>
        </div>
      </Modal>
    </>
  );
};

export default BrandDangerZone;
