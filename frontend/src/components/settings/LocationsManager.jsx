import React, { useState } from 'react';
import { useBrand } from '../../context/BrandContext';
import { MapPin, Plus, Trash2, CheckCircle2, Phone, Star, Building2, Edit2, Loader2, Save, X } from 'lucide-react';

const LocationsManager = () => {
  const { activeBrand, addLocation, updateLocation, deleteLocation, refreshBrands } = useBrand();

  const [isAdding, setIsAdding] = useState(false);
  const [editingLocId, setEditingLocId] = useState(null);
  const [loading, setLoading] = useState(false);

  const [form, setForm] = useState({
    name: '',
    city: '',
    address: '',
    phone: '',
    google_place_id: '',
    is_primary: false
  });

  const locations = Array.isArray(activeBrand?.locations) ? activeBrand.locations : [];

  const handleResetForm = () => {
    setForm({
      name: '',
      city: '',
      address: '',
      phone: '',
      google_place_id: '',
      is_primary: false
    });
    setIsAdding(false);
    setEditingLocId(null);
  };

  const handleStartEdit = (loc) => {
    setForm({
      name: loc.name || '',
      city: loc.city || '',
      address: loc.address || '',
      phone: loc.phone || '',
      google_place_id: loc.google_place_id || '',
      is_primary: !!loc.is_primary
    });
    setEditingLocId(loc.id);
    setIsAdding(false);
  };

  const handleSaveLocation = async (e) => {
    e.preventDefault();
    if (!activeBrand || !form.name.trim()) return;
    setLoading(true);
    try {
      if (editingLocId) {
        await updateLocation(activeBrand.id, editingLocId, form);
      } else {
        await addLocation(activeBrand.id, form);
      }
      handleResetForm();
    } catch (err) {
      console.error('Failed to save branch location:', err);
      alert('Could not save location. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteLocation = async (locId) => {
    if (!activeBrand) return;
    if (locations.length <= 1) {
      alert('Your business must have at least one branch location.');
      return;
    }
    if (!window.confirm('Are you sure you want to remove this branch location?')) return;
    setLoading(true);
    try {
      await deleteLocation(activeBrand.id, locId);
    } catch (err) {
      console.error('Failed to delete location:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-6 text-xs">
      <div className="flex items-center justify-between border-b border-slate-100 pb-4">
        <div>
          <h3 className="text-sm font-bold text-slate-900 tracking-tight flex items-center gap-2">
            <MapPin className="w-4 h-4 text-blue-600" />
            <span>Branches & Locations ({locations.length})</span>
          </h3>
          <p className="text-[11px] text-slate-500 mt-0.5">
            Manage multiple branch outlets, local addresses, and Google Maps IDs for your business.
          </p>
        </div>

        {!isAdding && !editingLocId && (
          <button
            type="button"
            onClick={() => {
              handleResetForm();
              setIsAdding(true);
            }}
            className="px-3.5 py-2 bg-blue-600 hover:bg-blue-700 text-white font-bold text-xs rounded-xl flex items-center gap-1.5 transition shadow-sm"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>Add Branch</span>
          </button>
        )}
      </div>

      {/* Add / Edit Form Modal or Inline Panel */}
      {(isAdding || editingLocId) && (
        <form onSubmit={handleSaveLocation} className="p-4 rounded-2xl bg-blue-50/60 border border-blue-200/80 space-y-3 animate-fade-in">
          <div className="flex items-center justify-between font-bold text-xs text-blue-900">
            <span>{editingLocId ? 'Edit Branch Location' : 'New Branch Location'}</span>
            <button
              type="button"
              onClick={handleResetForm}
              className="text-slate-400 hover:text-slate-600 p-1"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label className="block text-[11px] font-semibold text-slate-700 mb-1">Branch Name *</label>
              <input
                type="text"
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
                placeholder="e.g. T. Nagar Branch, Indiranagar Outlet"
                required
                className="w-full bg-white border border-slate-200 rounded-xl p-2.5 text-xs text-slate-900 focus:outline-none focus:border-blue-600"
              />
            </div>
            <div>
              <label className="block text-[11px] font-semibold text-slate-700 mb-1">City / Locality</label>
              <input
                type="text"
                value={form.city}
                onChange={(e) => setForm({ ...form, city: e.target.value })}
                placeholder="e.g. Chennai, Bengaluru, Mumbai"
                className="w-full bg-white border border-slate-200 rounded-xl p-2.5 text-xs text-slate-900 focus:outline-none focus:border-blue-600"
              />
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label className="block text-[11px] font-semibold text-slate-700 mb-1">Street Address or Landmark</label>
              <input
                type="text"
                value={form.address}
                onChange={(e) => setForm({ ...form, address: e.target.value })}
                placeholder="e.g. 42 Usman Road, near Bus Stand"
                className="w-full bg-white border border-slate-200 rounded-xl p-2.5 text-xs text-slate-900 focus:outline-none focus:border-blue-600"
              />
            </div>
            <div>
              <label className="block text-[11px] font-semibold text-slate-700 mb-1">Contact Phone</label>
              <input
                type="text"
                value={form.phone}
                onChange={(e) => setForm({ ...form, phone: e.target.value })}
                placeholder="e.g. +91 98401 23456"
                className="w-full bg-white border border-slate-200 rounded-xl p-2.5 text-xs text-slate-900 focus:outline-none focus:border-blue-600"
              />
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 items-center">
            <div>
              <label className="block text-[11px] font-semibold text-slate-700 mb-1">Google Place ID (Optional)</label>
              <input
                type="text"
                value={form.google_place_id}
                onChange={(e) => setForm({ ...form, google_place_id: e.target.value })}
                placeholder="e.g. ChIJ..."
                className="w-full bg-white border border-slate-200 rounded-xl p-2.5 text-xs text-slate-900 focus:outline-none focus:border-blue-600 font-mono"
              />
            </div>
            <div className="flex items-center gap-2 pt-4">
              <input
                type="checkbox"
                id="is_primary_checkbox"
                checked={form.is_primary}
                onChange={(e) => setForm({ ...form, is_primary: e.target.checked })}
                className="w-4 h-4 rounded text-blue-600 focus:ring-blue-500"
              />
              <label htmlFor="is_primary_checkbox" className="text-xs font-semibold text-slate-800 cursor-pointer">
                Set as Primary / Main Branch
              </label>
            </div>
          </div>

          <div className="flex justify-end gap-2 pt-2">
            <button
              type="button"
              onClick={handleResetForm}
              className="px-3.5 py-1.5 bg-slate-200 hover:bg-slate-300 text-slate-700 font-bold rounded-lg transition"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="px-4 py-1.5 bg-blue-600 hover:bg-blue-700 text-white font-bold rounded-lg flex items-center gap-1.5 transition disabled:opacity-50"
            >
              {loading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Save className="w-3.5 h-3.5" />}
              <span>{editingLocId ? 'Update Branch' : 'Save Branch'}</span>
            </button>
          </div>
        </form>
      )}

      {/* Locations List */}
      <div className="space-y-3">
        {locations.length === 0 ? (
          <div className="text-center py-6 text-slate-400 bg-slate-50 rounded-2xl border border-dashed border-slate-200">
            No branch locations configured. Click "Add Branch" to create your first outlet.
          </div>
        ) : (
          locations.map((loc) => (
            <div
              key={loc.id}
              className="p-4 rounded-2xl border border-slate-200 hover:border-slate-300 bg-slate-50/50 flex flex-col sm:flex-row sm:items-center justify-between gap-3 transition"
            >
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <span className="font-bold text-slate-900 text-sm">{loc.name}</span>
                  {loc.is_primary && (
                    <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-100 text-emerald-800 border border-emerald-200 flex items-center gap-1">
                      <Star className="w-3 h-3 fill-emerald-600 text-emerald-600" />
                      Primary Branch
                    </span>
                  )}
                  {loc.city && (
                    <span className="px-2 py-0.5 rounded-full text-[10px] font-medium bg-slate-200/70 text-slate-700">
                      {loc.city}
                    </span>
                  )}
                </div>

                <div className="text-slate-500 text-[11px] flex flex-wrap gap-x-4 gap-y-1">
                  {loc.address && <span>📍 {loc.address}</span>}
                  {loc.phone && <span>📞 {loc.phone}</span>}
                  {loc.google_place_id && <span className="font-mono text-[10px] text-slate-400">Google ID: {loc.google_place_id.slice(0, 15)}...</span>}
                </div>
              </div>

              <div className="flex items-center gap-2 shrink-0">
                <button
                  type="button"
                  title="Edit branch"
                  onClick={() => handleStartEdit(loc)}
                  className="p-2 rounded-xl text-slate-500 hover:text-blue-600 hover:bg-blue-50 transition border border-transparent hover:border-blue-200"
                >
                  <Edit2 className="w-3.5 h-3.5" />
                </button>
                <button
                  type="button"
                  title="Remove branch"
                  onClick={() => handleDeleteLocation(loc.id)}
                  className="p-2 rounded-xl text-slate-400 hover:text-red-600 hover:bg-red-50 transition border border-transparent hover:border-red-200"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

export default LocationsManager;
