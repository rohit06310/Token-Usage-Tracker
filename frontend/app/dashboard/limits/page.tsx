"use client";

import { useState, useEffect } from "react";
import { formatNumber, formatCost } from "@/lib/utils";
import { api } from "@/lib/api";
import { Plus, Trash2, Zap, DollarSign, Activity } from "lucide-react";

type RateLimit = {
  id: string;
  provider_id: string;
  tier_name: string;
  rpm: number | null;
  tpm: number | null;
  rpd: number | null;
  budget_usd: number | null;
  effective_date: string;
};

export default function LimitsPage() {
  const [limits, setLimits] = useState<RateLimit[]>([]);
  const [providerSlug, setProviderSlug] = useState("openai");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  
  // Form state
  const [showForm, setShowForm] = useState(false);
  const [formData, setFormData] = useState({
    tier_name: "Default",
    rpm: "",
    tpm: "",
    rpd: "",
    budget_usd: "",
    effective_date: new Date().toISOString().split("T")[0]
  });

  useEffect(() => {
    fetchLimits();
  }, [providerSlug]);

  const fetchLimits = async () => {
    setLoading(true);
    setError("");
    try {
      const res = await api.get(`/${providerSlug}/limits`);
      setLimits(res as any);
    } catch (err: any) {
      if (err.response?.status !== 404) {
        setError("Failed to fetch limits");
      } else {
        setLimits([]);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      const payload = {
        tier_name: formData.tier_name,
        rpm: formData.rpm ? parseInt(formData.rpm) : null,
        tpm: formData.tpm ? parseInt(formData.tpm) : null,
        rpd: formData.rpd ? parseInt(formData.rpd) : null,
        budget_usd: formData.budget_usd ? parseFloat(formData.budget_usd) : null,
        effective_date: formData.effective_date
      };
      await api.post(`/${providerSlug}/limits`, payload);
      setShowForm(false);
      setFormData({
        tier_name: "Default",
        rpm: "",
        tpm: "",
        rpd: "",
        budget_usd: "",
        effective_date: new Date().toISOString().split("T")[0]
      });
      fetchLimits();
    } catch (err) {
      setError("Failed to create limit");
      setLoading(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Are you sure you want to delete this limit?")) return;
    try {
      await api.delete(`/limits/${id}`);
      fetchLimits();
    } catch (err) {
      setError("Failed to delete limit");
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-100">Rate & Budget Limits</h1>
          <p className="text-slate-400 text-sm mt-1">
            Manage provider-specific limits to prevent unexpected costs.
          </p>
        </div>
        <div className="flex items-center gap-4">
          <select 
            value={providerSlug}
            onChange={(e) => setProviderSlug(e.target.value)}
            className="bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200"
          >
            <option value="openai">OpenAI</option>
            <option value="anthropic">Anthropic</option>
            <option value="groq">Groq</option>
            <option value="gemini">Gemini</option>
          </select>
          <button
            onClick={() => setShowForm(!showForm)}
            className="flex items-center gap-2 px-4 py-2 bg-violet-600 hover:bg-violet-500 text-white rounded-lg text-sm font-medium transition-colors"
          >
            <Plus className="h-4 w-4" />
            Add Limit
          </button>
        </div>
      </div>

      {error && (
        <div className="bg-red-500/10 border border-red-500/20 text-red-400 px-4 py-3 rounded-lg text-sm">
          {error}
        </div>
      )}

      {showForm && (
        <div className="bg-slate-800/40 border border-slate-700/50 rounded-2xl p-6">
          <h3 className="text-lg font-semibold text-slate-200 mb-4">Create New Limit Tier</h3>
          <form onSubmit={handleCreate} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">Tier Name</label>
                <input 
                  type="text" 
                  value={formData.tier_name}
                  onChange={(e) => setFormData({...formData, tier_name: e.target.value})}
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200"
                  required
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">Effective Date</label>
                <input 
                  type="date" 
                  value={formData.effective_date}
                  onChange={(e) => setFormData({...formData, effective_date: e.target.value})}
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200"
                  required
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">Requests / Min (RPM)</label>
                <input 
                  type="number" 
                  value={formData.rpm}
                  onChange={(e) => setFormData({...formData, rpm: e.target.value})}
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200"
                  placeholder="e.g. 500"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">Requests / Day (RPD)</label>
                <input 
                  type="number" 
                  value={formData.rpd}
                  onChange={(e) => setFormData({...formData, rpd: e.target.value})}
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200"
                  placeholder="e.g. 10000"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">Tokens / Min (TPM)</label>
                <input 
                  type="number" 
                  value={formData.tpm}
                  onChange={(e) => setFormData({...formData, tpm: e.target.value})}
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200"
                  placeholder="e.g. 200000"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">Monthly Budget (USD)</label>
                <input 
                  type="number" 
                  step="0.01"
                  value={formData.budget_usd}
                  onChange={(e) => setFormData({...formData, budget_usd: e.target.value})}
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200"
                  placeholder="e.g. 100.00"
                />
              </div>
            </div>
            <div className="flex justify-end gap-3 pt-4">
              <button 
                type="button" 
                onClick={() => setShowForm(false)}
                className="px-4 py-2 text-sm font-medium text-slate-400 hover:text-slate-200"
              >
                Cancel
              </button>
              <button 
                type="submit" 
                disabled={loading}
                className="px-4 py-2 bg-violet-600 hover:bg-violet-500 text-white rounded-lg text-sm font-medium"
              >
                Save Limit
              </button>
            </div>
          </form>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {loading && !showForm ? (
          <div className="col-span-full flex justify-center py-12">
            <div className="h-6 w-6 rounded-full border-2 border-violet-500 border-t-transparent animate-spin"></div>
          </div>
        ) : limits.length === 0 ? (
          <div className="col-span-full bg-slate-800/40 border border-slate-700/50 rounded-2xl p-12 flex flex-col items-center justify-center text-center">
            <Zap className="h-12 w-12 text-slate-600 mb-4" />
            <p className="text-slate-300 font-medium">No limits configured for {providerSlug}</p>
            <p className="text-slate-500 text-sm mt-1">Add a limit tier to start monitoring usage.</p>
          </div>
        ) : (
          limits.map((limit) => (
            <div key={limit.id} className="bg-slate-800/40 border border-slate-700/50 rounded-2xl p-5 hover:border-slate-600/50 transition-colors">
              <div className="flex justify-between items-start mb-4">
                <div>
                  <h3 className="text-lg font-bold text-slate-200 flex items-center gap-2">
                    {limit.tier_name}
                  </h3>
                  <span className="text-xs text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded mt-1 inline-block">
                    Active from {new Date(limit.effective_date).toLocaleDateString()}
                  </span>
                </div>
                <button 
                  onClick={() => handleDelete(limit.id)}
                  className="p-1.5 text-slate-500 hover:text-red-400 hover:bg-red-500/10 rounded-lg transition-colors"
                >
                  <Trash2 className="h-4 w-4" />
                </button>
              </div>

              <div className="space-y-3">
                <div className="flex items-center justify-between text-sm">
                  <span className="flex items-center gap-2 text-slate-400">
                    <Activity className="h-4 w-4" /> RPM
                  </span>
                  <span className="text-slate-200 font-mono">
                    {limit.rpm ? formatNumber(limit.rpm) : "∞"}
                  </span>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span className="flex items-center gap-2 text-slate-400">
                    <Activity className="h-4 w-4" /> TPM
                  </span>
                  <span className="text-slate-200 font-mono">
                    {limit.tpm ? formatNumber(limit.tpm) : "∞"}
                  </span>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span className="flex items-center gap-2 text-slate-400">
                    <Activity className="h-4 w-4" /> RPD
                  </span>
                  <span className="text-slate-200 font-mono">
                    {limit.rpd ? formatNumber(limit.rpd) : "∞"}
                  </span>
                </div>
                <div className="pt-3 border-t border-slate-700/50 flex items-center justify-between text-sm">
                  <span className="flex items-center gap-2 text-slate-400 font-medium">
                    <DollarSign className="h-4 w-4 text-emerald-500" /> Monthly Budget
                  </span>
                  <span className="text-emerald-400 font-mono font-medium">
                    {limit.budget_usd ? formatCost(limit.budget_usd.toString()) : "∞"}
                  </span>
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
