"use client";

import { useState, useEffect } from "react";
import { formatNumber } from "@/lib/utils";
import { api } from "@/lib/api";
import { Shield, ShieldAlert, ShieldCheck, ShieldQuestion, AlertTriangle, CheckCircle2 } from "lucide-react";

type ReconciliationResult = {
  id: string;
  provider_id: string;
  provider_name: string;
  provider_slug: string;
  confidence_level: string;
  period_start: string;
  period_end: string;
  self_logged_tokens: number;
  provider_reported_tokens: number;
  difference: number;
  percent_diff: string;
  status: string;
  checked_at: string;
};

export default function ReconciliationPage() {
  const [results, setResults] = useState<ReconciliationResult[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchResults();
  }, []);

  const fetchResults = async () => {
    try {
      const res: any = await api.get("/reconciliation/");
      setResults(res.items);
    } catch (err) {
      console.error("Failed to fetch reconciliation results", err);
    } finally {
      setLoading(false);
    }
  };

  const renderConfidenceIcon = (level: string) => {
    switch (level) {
      case "verified":
        return <ShieldCheck className="h-5 w-5 text-emerald-400" />;
      case "unreliable":
        return <ShieldAlert className="h-5 w-5 text-red-400" />;
      case "self_logged_only":
        return <ShieldQuestion className="h-5 w-5 text-slate-400" />;
      default:
        return <Shield className="h-5 w-5 text-slate-500" />;
    }
  };

  const getStatusBadge = (status: string) => {
    if (status === "matched") {
      return (
        <span className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs font-medium w-fit">
          <CheckCircle2 className="h-3.5 w-3.5" />
          Matched
        </span>
      );
    } else if (status === "mismatched") {
      return (
        <span className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-red-500/10 border border-red-500/20 text-red-400 text-xs font-medium w-fit">
          <AlertTriangle className="h-3.5 w-3.5" />
          Mismatched
        </span>
      );
    } else {
      return (
        <span className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-slate-500/10 border border-slate-500/20 text-slate-400 text-xs font-medium w-fit">
          <ShieldQuestion className="h-3.5 w-3.5" />
          No Data
        </span>
      );
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-100">Data Reconciliation</h1>
          <p className="text-slate-400 text-sm mt-1">
            Compare self-logged usage against provider-reported usage to verify tracking accuracy.
          </p>
        </div>
      </div>

      <div className="rounded-2xl border border-slate-700/50 bg-slate-800/40 backdrop-blur-sm overflow-hidden flex flex-col min-h-[500px]">
        {loading ? (
          <div className="flex-1 flex items-center justify-center p-12">
            <div className="h-6 w-6 rounded-full border-2 border-violet-500 border-t-transparent animate-spin"></div>
          </div>
        ) : results.length === 0 ? (
          <div className="flex-1 flex flex-col items-center justify-center p-12 text-center text-slate-400">
            <Shield className="h-12 w-12 text-slate-600 mb-4" />
            <p className="text-base font-medium text-slate-300">No reconciliation data found</p>
            <p className="text-sm mt-1 max-w-md">
              The background job runs periodically to fetch provider usage and compare it with local logs.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-slate-700/50 bg-slate-900/50">
                  <th className="px-6 py-4 text-xs font-semibold text-slate-400 uppercase tracking-wider">Provider</th>
                  <th className="px-6 py-4 text-xs font-semibold text-slate-400 uppercase tracking-wider">Date Period</th>
                  <th className="px-6 py-4 text-xs font-semibold text-slate-400 uppercase tracking-wider text-right">Self Logged Tokens</th>
                  <th className="px-6 py-4 text-xs font-semibold text-slate-400 uppercase tracking-wider text-right">Provider Tokens</th>
                  <th className="px-6 py-4 text-xs font-semibold text-slate-400 uppercase tracking-wider text-right">Difference</th>
                  <th className="px-6 py-4 text-xs font-semibold text-slate-400 uppercase tracking-wider">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-700/50">
                {results.map((r) => (
                  <tr key={r.id} className="hover:bg-slate-700/20 transition-colors">
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-3">
                        <div title={`Confidence: ${r.confidence_level}`}>
                          {renderConfidenceIcon(r.confidence_level)}
                        </div>
                        <div>
                          <div className="text-sm font-medium text-slate-200">{r.provider_name}</div>
                          <div className="text-xs text-slate-500">{r.confidence_level.replace(/_/g, " ")}</div>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 text-sm text-slate-300">
                      {new Date(r.period_start).toLocaleDateString()}
                    </td>
                    <td className="px-6 py-4 text-sm text-right text-slate-300 font-mono">
                      {formatNumber(r.self_logged_tokens)}
                    </td>
                    <td className="px-6 py-4 text-sm text-right text-slate-300 font-mono">
                      {formatNumber(r.provider_reported_tokens)}
                    </td>
                    <td className="px-6 py-4 text-sm text-right font-mono">
                      <span className={r.difference !== 0 ? (r.percent_diff && parseFloat(r.percent_diff) > 2 ? 'text-red-400' : 'text-amber-400') : 'text-slate-400'}>
                        {r.difference > 0 ? "+" : ""}{formatNumber(r.difference)} ({parseFloat(r.percent_diff).toFixed(2)}%)
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      {getStatusBadge(r.status)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
