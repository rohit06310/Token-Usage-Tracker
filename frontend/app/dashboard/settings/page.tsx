"use client";

import { useState } from "react";
import useSWR, { mutate } from "swr";
import { Settings, Plus, Trash2, Shield, Link as LinkIcon, Database } from "lucide-react";
import { api, swrFetcher } from "@/lib/api";

type Provider = {
  id: string;
  name: string;
  slug: string;
  base_url: string | null;
  confidence_level: string;
};

type ApiKey = {
  id: string;
  provider_id: string;
  label: string;
  is_active: boolean;
  created_at: string;
};

export default function SettingsPage() {
  const { data: providers, error: providersError } = useSWR<Provider[]>("/api/proxy/providers/", swrFetcher);
  const { data: apiKeys, error: keysError } = useSWR<ApiKey[]>("/api/proxy/api-keys/", swrFetcher);

  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState("");

  // New Provider Form State
  const [newProvName, setNewProvName] = useState("");
  const [newProvSlug, setNewProvSlug] = useState("");
  const [newProvBaseUrl, setNewProvBaseUrl] = useState("");
  const [newProvConfidence, setNewProvConfidence] = useState("verified");

  // New API Key Form State
  const [newKeyProviderId, setNewKeyProviderId] = useState("");
  const [newKeyLabel, setNewKeyLabel] = useState("");
  const [newKeyRaw, setNewKeyRaw] = useState("");

  const handleCreateProvider = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setErrorMsg("");
    try {
      await api.post("/providers/", {
        name: newProvName,
        slug: newProvSlug,
        base_url: newProvBaseUrl || null,
        confidence_level: newProvConfidence,
      });
      mutate("/api/proxy/providers/");
      setNewProvName("");
      setNewProvSlug("");
      setNewProvBaseUrl("");
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to create provider");
    } finally {
      setLoading(false);
    }
  };

  const handleCreateApiKey = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setErrorMsg("");
    try {
      await api.post("/api-keys/", {
        provider_id: newKeyProviderId,
        label: newKeyLabel,
        raw_key: newKeyRaw,
      });
      mutate("/api/proxy/api-keys/");
      setNewKeyLabel("");
      setNewKeyRaw("");
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to create API key");
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteProvider = async (id: string) => {
    if (!confirm("Delete this provider and all its keys/logs?")) return;
    try {
      await fetch(`/api/proxy/providers/${id}`, { method: "DELETE" });
      mutate("/api/proxy/providers/");
      mutate("/api/proxy/api-keys/");
    } catch (err: any) {
      alert("Error deleting provider");
    }
  };

  const handleDeleteApiKey = async (id: string) => {
    if (!confirm("Delete this API key?")) return;
    try {
      await fetch(`/api/proxy/api-keys/${id}`, { method: "DELETE" });
      mutate("/api/proxy/api-keys/");
    } catch (err: any) {
      alert("Error deleting API key");
    }
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center gap-3 border-b border-slate-700/50 pb-5">
        <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-violet-500/10 border border-violet-500/20">
          <Settings className="h-5 w-5 text-violet-400" />
        </div>
        <div>
          <h2 className="text-xl font-bold text-slate-100 tracking-tight">API & Settings</h2>
          <p className="text-sm text-slate-400">Manage LLM providers, custom endpoints, and API keys.</p>
        </div>
      </div>

      {errorMsg && (
        <div className="rounded-xl border border-red-500/50 bg-red-500/10 p-4 text-sm font-medium text-red-400">
          {errorMsg}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* PROVIDERS SECTION */}
        <section className="space-y-6">
          <div className="flex items-center gap-2 text-slate-200 font-semibold text-lg">
            <Database className="h-5 w-5 text-blue-400" />
            Providers
          </div>

          <div className="rounded-2xl border border-slate-700/50 bg-slate-800/40 p-6 overflow-hidden">
            <h3 className="text-sm font-medium text-slate-400 mb-4 uppercase tracking-wider">Registered Providers</h3>
            <div className="space-y-3 mb-8">
              {providersError ? (
                <p className="text-red-400 text-sm">Error loading providers</p>
              ) : !providers ? (
                <p className="text-slate-500 text-sm animate-pulse">Loading...</p>
              ) : providers.length === 0 ? (
                <p className="text-slate-500 text-sm">No providers registered yet.</p>
              ) : (
                providers.map((p) => (
                  <div key={p.id} className="flex items-center justify-between p-3 rounded-xl bg-slate-800/80 border border-slate-700/50 group hover:border-slate-600 transition-colors">
                    <div>
                      <div className="font-medium text-slate-200">{p.name} <span className="text-xs text-slate-500 font-mono ml-2">({p.slug})</span></div>
                      {p.base_url && (
                        <div className="text-xs text-blue-400 mt-1 flex items-center gap-1">
                          <LinkIcon className="h-3 w-3" /> {p.base_url}
                        </div>
                      )}
                    </div>
                    <button onClick={() => handleDeleteProvider(p.id)} className="p-2 text-slate-500 hover:text-red-400 hover:bg-red-400/10 rounded-lg transition-colors opacity-0 group-hover:opacity-100">
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>
                ))
              )}
            </div>

            <h3 className="text-sm font-medium text-slate-400 mb-4 uppercase tracking-wider">Add New Provider</h3>
            <form onSubmit={handleCreateProvider} className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-medium text-slate-400 mb-1">Name</label>
                  <input required value={newProvName} onChange={(e) => setNewProvName(e.target.value)} placeholder="e.g. Local vLLM" className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-violet-500 focus:ring-1 focus:ring-violet-500" />
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-400 mb-1">Slug</label>
                  <input required value={newProvSlug} onChange={(e) => setNewProvSlug(e.target.value)} placeholder="e.g. custom-vllm" className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-violet-500 focus:ring-1 focus:ring-violet-500" />
                </div>
              </div>
              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">Custom Base URL (Optional)</label>
                <input value={newProvBaseUrl} onChange={(e) => setNewProvBaseUrl(e.target.value)} placeholder="e.g. http://localhost:8000/v1" className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-violet-500 focus:ring-1 focus:ring-violet-500" />
                <p className="text-[10px] text-slate-500 mt-1">If provided, the generic OpenAI-compatible adapter will be used.</p>
              </div>
              <button disabled={loading} type="submit" className="w-full flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-500 text-white font-medium rounded-lg px-4 py-2 text-sm transition-colors disabled:opacity-50">
                <Plus className="h-4 w-4" /> Add Provider
              </button>
            </form>
          </div>
        </section>

        {/* API KEYS SECTION */}
        <section className="space-y-6">
          <div className="flex items-center gap-2 text-slate-200 font-semibold text-lg">
            <Shield className="h-5 w-5 text-emerald-400" />
            API Keys
          </div>

          <div className="rounded-2xl border border-slate-700/50 bg-slate-800/40 p-6 overflow-hidden">
            <h3 className="text-sm font-medium text-slate-400 mb-4 uppercase tracking-wider">Active Keys</h3>
            <div className="space-y-3 mb-8">
              {keysError ? (
                <p className="text-red-400 text-sm">Error loading keys</p>
              ) : !apiKeys ? (
                <p className="text-slate-500 text-sm animate-pulse">Loading...</p>
              ) : apiKeys.length === 0 ? (
                <p className="text-slate-500 text-sm">No API keys registered yet.</p>
              ) : (
                apiKeys.map((k) => {
                  const pName = providers?.find(p => p.id === k.provider_id)?.name || "Unknown Provider";
                  return (
                    <div key={k.id} className="flex items-center justify-between p-3 rounded-xl bg-slate-800/80 border border-slate-700/50 group hover:border-slate-600 transition-colors">
                      <div>
                        <div className="font-medium text-slate-200">{k.label}</div>
                        <div className="text-xs text-slate-500 mt-1 flex items-center gap-2">
                          <span className="px-2 py-0.5 rounded-md bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">{pName}</span>
                          • Added {new Date(k.created_at).toLocaleDateString()}
                        </div>
                      </div>
                      <div className="flex items-center opacity-0 group-hover:opacity-100 transition-opacity">
                        <button onClick={async () => {
                          try {
                            const res = await api.post(`/api-keys/${k.id}/test`);
                            if ((res as any).success) {
                              alert("✅ Connection successful!");
                            } else {
                              alert("❌ Connection failed: " + (res as any).message);
                            }
                          } catch (err: any) {
                            alert("❌ Error: " + err.message);
                          }
                        }} className="p-2 text-slate-400 hover:text-emerald-400 hover:bg-emerald-400/10 rounded-lg transition-colors text-xs font-medium mr-1">
                          Test
                        </button>
                        <button onClick={() => handleDeleteApiKey(k.id)} className="p-2 text-slate-500 hover:text-red-400 hover:bg-red-400/10 rounded-lg transition-colors">
                          <Trash2 className="h-4 w-4" />
                        </button>
                      </div>
                    </div>
                  );
                })
              )}
            </div>

            <h3 className="text-sm font-medium text-slate-400 mb-4 uppercase tracking-wider">Add New Key</h3>
            <form onSubmit={handleCreateApiKey} className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">Provider</label>
                <select required value={newKeyProviderId} onChange={(e) => setNewKeyProviderId(e.target.value)} className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-violet-500 focus:ring-1 focus:ring-violet-500">
                  <option value="" disabled>Select a provider...</option>
                  {providers?.map((p) => (
                    <option key={p.id} value={p.id}>{p.name} ({p.slug})</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">Label</label>
                <input required value={newKeyLabel} onChange={(e) => setNewKeyLabel(e.target.value)} placeholder="e.g. Production Key" className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-violet-500 focus:ring-1 focus:ring-violet-500" />
              </div>
              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">API Key</label>
                <input required type="password" value={newKeyRaw} onChange={(e) => setNewKeyRaw(e.target.value)} placeholder="sk-..." className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-violet-500 focus:ring-1 focus:ring-violet-500" />
                <p className="text-[10px] text-slate-500 mt-1">Keys are encrypted with AES (Fernet) before storing.</p>
              </div>
              <button disabled={loading || !newKeyProviderId} type="submit" className="w-full flex items-center justify-center gap-2 bg-emerald-600 hover:bg-emerald-500 text-white font-medium rounded-lg px-4 py-2 text-sm transition-colors disabled:opacity-50">
                <Plus className="h-4 w-4" /> Save API Key
              </button>
            </form>
          </div>
        </section>

      </div>
    </div>
  );
}
