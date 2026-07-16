"use client";

import { useState, useEffect } from "react";
import { Terminal, Send, Tag, AlertCircle } from "lucide-react";
import { api } from "@/lib/api";
import { formatCost, formatNumber } from "@/lib/utils";

export default function PlaygroundPage() {
  const [prompt, setPrompt] = useState("");
  const [projectTag, setProjectTag] = useState("");
  const [providerSlug, setProviderSlug] = useState("openai");
  const [model, setModel] = useState("gpt-4o-mini");
  
  const [availableTags, setAvailableTags] = useState<{tag: string}[]>([]);
  const [loading, setLoading] = useState(false);
  const [response, setResponse] = useState<any>(null);
  const [error, setError] = useState("");

  const [isStreaming, setIsStreaming] = useState(true);

  useEffect(() => {
    // Fetch tags for auto-suggest
    api.get("/usage/tags")
      .then((res: any) => {
        setAvailableTags(res || []);
      })
      .catch(console.error);
  }, []);

  const handleRun = async () => {
    if (!prompt) return;
    setLoading(true);
    setError("");
    setResponse(null);
    
    try {
      if (isStreaming) {
        const token = localStorage.getItem("token"); // Fallback for auth if needed
        const res = await fetch("http://localhost:8000/api/v1/completions/", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "Authorization": `Bearer ${token}`
          },
          body: JSON.stringify({
            provider_slug: providerSlug,
            model: model,
            prompt: prompt,
            project_tag: projectTag || undefined,
            stream: true,
          }),
        });

        if (!res.ok) {
          throw new Error(`Request failed with status ${res.status}`);
        }

        const reader = res.body?.getReader();
        const decoder = new TextDecoder();
        let currentText = "";
        
        setResponse({ content: "", status: "streaming", total_tokens: 0, cost_usd: "0" });

        while (reader) {
          const { done, value } = await reader.read();
          if (done) break;
          
          const chunk = decoder.decode(value);
          const lines = chunk.split("\n");
          
          for (const line of lines) {
            if (line.startsWith("data: ")) {
              try {
                const data = JSON.parse(line.slice(6));
                if (data.error) {
                  setError(data.error);
                } else if (data.status === "success") {
                  setResponse((prev: any) => ({
                    ...prev,
                    status: "success",
                    total_tokens: data.tokens_in + data.tokens_out,
                    cost_usd: data.cost_usd,
                  }));
                } else if (data.content !== undefined) {
                  currentText += data.content;
                  setResponse((prev: any) => ({
                    ...prev,
                    content: currentText
                  }));
                }
              } catch (e) {
                // Ignore parse errors from partial chunks
              }
            }
          }
        }
      } else {
        const res = await api.post("/completions/", {
          provider_slug: providerSlug,
          model: model,
          prompt: prompt,
          project_tag: projectTag || undefined,
        });
        setResponse(res);
      }
    } catch (err: any) {
      setError(err.message || "Request failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6 max-w-4xl h-[calc(100vh-8rem)] flex flex-col">
      {/* Header */}
      <div className="flex items-center gap-3 border-b border-slate-700/50 pb-4 shrink-0 justify-between">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-violet-500/10 border border-violet-500/20">
            <Terminal className="h-5 w-5 text-violet-400" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-slate-100 tracking-tight">API Playground</h2>
            <p className="text-sm text-slate-400">Test prompts and tag completions for cost tracking.</p>
          </div>
        </div>
        
        <div className="flex items-center gap-2">
          <label className="text-sm text-slate-300">Stream</label>
          <input 
            type="checkbox" 
            checked={isStreaming} 
            onChange={(e) => setIsStreaming(e.target.checked)}
            className="rounded border-slate-700 bg-slate-900 text-violet-500 focus:ring-violet-500/50"
          />
        </div>
      </div>

      <div className="flex gap-4 shrink-0">
        <div className="flex-1">
          <label className="block text-xs font-medium text-slate-400 mb-1">Provider</label>
          <select 
            value={providerSlug} 
            onChange={(e) => {
              setProviderSlug(e.target.value);
              if (e.target.value === "openai") setModel("gpt-4o-mini");
              if (e.target.value === "anthropic") setModel("claude-3-haiku-20240307");
              if (e.target.value === "groq") setModel("llama3-8b-8192");
              if (e.target.value === "gemini") setModel("gemini-1.5-flash");
            }}
            className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200"
          >
            <option value="openai">OpenAI</option>
            <option value="anthropic">Anthropic</option>
            <option value="groq">Groq</option>
            <option value="gemini">Gemini</option>
          </select>
        </div>
        <div className="flex-1">
          <label className="block text-xs font-medium text-slate-400 mb-1">Model</label>
          <input 
            type="text" 
            value={model} 
            onChange={(e) => setModel(e.target.value)}
            className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200"
          />
        </div>
        <div className="flex-1 relative">
          <label className="block text-xs font-medium text-slate-400 mb-1 flex items-center gap-1">
            <Tag className="h-3 w-3" /> Project Tag
          </label>
          <input 
            type="text" 
            value={projectTag} 
            onChange={(e) => setProjectTag(e.target.value)}
            placeholder="e.g. testing, prod-v2"
            list="tags-list"
            className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200"
          />
          <datalist id="tags-list">
            {availableTags.map((t) => (
              <option key={t.tag} value={t.tag} />
            ))}
          </datalist>
        </div>
      </div>

      <div className="flex-1 flex flex-col min-h-0 bg-slate-800/40 border border-slate-700/50 rounded-2xl overflow-hidden">
        {/* Output area */}
        <div className="flex-1 overflow-y-auto p-4 flex flex-col">
          {error && (
            <div className="bg-red-500/10 border border-red-500/20 rounded-xl p-4 text-red-400 flex items-start gap-3">
              <AlertCircle className="h-5 w-5 shrink-0" />
              <div className="text-sm font-medium">{error}</div>
            </div>
          )}
          
          {response && (
            <div className="flex flex-col gap-4">
              <div className="bg-slate-900/50 rounded-xl p-4 border border-slate-700/50 font-mono text-sm text-slate-300 whitespace-pre-wrap">
                {response.content || (response.status === 'streaming' ? <span className="animate-pulse">|</span> : <span className="text-slate-500 italic">No output returned. Check status.</span>)}
              </div>
              
              <div className="flex items-center gap-4 text-xs font-medium">
                <span className={`px-2 py-1 rounded-md ${response.status === 'success' ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' : response.status === 'streaming' ? 'bg-amber-500/10 text-amber-400 border border-amber-500/20' : 'bg-red-500/10 text-red-400 border border-red-500/20'}`}>
                  {response.status.toUpperCase()}
                </span>
                <span className="text-slate-400">Tokens: <span className="text-slate-200">{formatNumber(response.total_tokens || 0)}</span></span>
                <span className="text-slate-400">Cost: <span className="text-slate-200">{formatCost(response.cost_usd || "0")}</span></span>
                {response.log_id && <span className="text-slate-500 ml-auto">Log ID: {response.log_id}</span>}
              </div>
            </div>
          )}
          
          {!response && !error && !loading && (
            <div className="flex-1 flex items-center justify-center text-slate-500 text-sm">
              Enter a prompt below and run to see the completion.
            </div>
          )}
          
          {loading && !response && (
            <div className="flex-1 flex items-center justify-center text-slate-400 text-sm animate-pulse">
              Generating response...
            </div>
          )}
        </div>
        
        {/* Input area */}
        <div className="p-3 bg-slate-900 border-t border-slate-700/50 flex gap-3">
          <textarea 
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="Type your prompt here..."
            className="flex-1 bg-transparent border-none resize-none focus:outline-none focus:ring-0 text-sm text-slate-200 p-2"
            rows={2}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
                handleRun();
              }
            }}
          />
          <button 
            onClick={handleRun}
            disabled={loading || !prompt}
            className="self-end bg-violet-600 hover:bg-violet-500 disabled:opacity-50 text-white rounded-xl h-10 px-4 flex items-center justify-center transition-colors"
          >
            <Send className="h-4 w-4" />
          </button>
        </div>
      </div>
    </div>
  );
}
