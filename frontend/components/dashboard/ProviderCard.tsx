"use client";

import { Activity, DollarSign, Zap } from "lucide-react";
import { ConfidenceBadge } from "./ConfidenceBadge";
import { QuotaProgressBar } from "./QuotaProgressBar";
import { formatCost, formatTokens, formatNumber, getProviderColor } from "@/lib/utils";
import type { ProviderSummary } from "@/lib/types";

interface ProviderCardProps {
  provider: ProviderSummary;
}

const PROVIDER_ICONS: Record<string, string> = {
  openai: "🟢",
  anthropic: "🟣",
  groq: "🟡",
  gemini: "🔵",
};

export function ProviderCard({ provider }: ProviderCardProps) {
  const color = getProviderColor(provider.provider_slug);
  const icon = PROVIDER_ICONS[provider.provider_slug] ?? "⚪";
  const hasQuota = Object.keys(provider.remaining_quota).length > 0;

  return (
    <div className="group relative overflow-hidden rounded-2xl border border-slate-700/50 bg-slate-800/60 p-5 backdrop-blur-sm transition-all duration-300 hover:border-slate-600/50 hover:bg-slate-800/80 hover:shadow-xl hover:shadow-black/20 print:shadow-none">
      {/* Accent line */}
      <div
        className="absolute inset-x-0 top-0 h-[2px] opacity-70 transition-opacity group-hover:opacity-100"
        style={{ background: `linear-gradient(to right, ${color}, transparent)` }}
      />

      {/* Header */}
      <div className="mb-4 flex items-start justify-between">
        <div className="flex items-center gap-3">
          <div
            className="flex h-10 w-10 items-center justify-center rounded-xl text-xl"
            style={{ background: `${color}20`, border: `1px solid ${color}30` }}
          >
            {icon}
          </div>
          <div>
            <h3 className="font-semibold text-slate-100">{provider.provider_name}</h3>
            <code className="text-xs text-slate-500">{provider.provider_slug}</code>
          </div>
        </div>
        <ConfidenceBadge level={provider.confidence_level} />
      </div>

      {/* Stats Grid */}
      <div className="mb-4 grid grid-cols-3 gap-3">
        <StatItem
          icon={<Activity className="h-3.5 w-3.5" />}
          label="Calls today"
          value={formatNumber(provider.call_count_today)}
          color={color}
        />
        <StatItem
          icon={<Zap className="h-3.5 w-3.5" />}
          label="Tokens today"
          value={formatTokens(provider.total_tokens_today)}
          color={color}
        />
        <StatItem
          icon={<DollarSign className="h-3.5 w-3.5" />}
          label="Cost today"
          value={formatCost(provider.total_cost_today)}
          color={color}
        />
      </div>

      {/* 30-day cost */}
      <div className="mb-4 flex items-center justify-between rounded-lg bg-slate-700/30 px-3 py-2">
        <span className="text-xs text-slate-400">30-day cost</span>
        <span className="text-sm font-semibold text-slate-200">
          {formatCost(provider.total_cost_30d)}
        </span>
      </div>

      {/* Quota bars */}
      {hasQuota && (
        <div className="space-y-3 border-t border-slate-700/50 pt-4">
          <p className="text-xs font-medium uppercase tracking-wider text-slate-500">Rate Limits</p>
          {provider.remaining_quota.tpm && (
            <QuotaProgressBar label="TPM" quota={provider.remaining_quota.tpm} />
          )}
          {provider.remaining_quota.rpm && (
            <QuotaProgressBar label="RPM" quota={provider.remaining_quota.rpm} />
          )}
          {provider.remaining_quota.rpd && (
            <QuotaProgressBar label="RPD" quota={provider.remaining_quota.rpd} />
          )}
        </div>
      )}

      {!hasQuota && (
        <p className="mt-2 text-xs text-slate-600">No rate limits configured</p>
      )}
    </div>
  );
}

function StatItem({
  icon,
  label,
  value,
  color,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
  color: string;
}) {
  return (
    <div className="flex flex-col gap-1 rounded-lg bg-slate-700/30 p-2.5 text-center">
      <div className="flex items-center justify-center gap-1 text-slate-400" style={{ color }}>
        {icon}
      </div>
      <div className="text-sm font-bold text-slate-100 tabular-nums">{value}</div>
      <div className="text-[10px] text-slate-500">{label}</div>
    </div>
  );
}
