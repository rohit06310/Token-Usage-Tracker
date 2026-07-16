"use client";

import { cn } from "@/lib/utils";
import type { QuotaDetail } from "@/lib/types";

interface QuotaProgressBarProps {
  label: string; // e.g. "TPM", "RPM", "RPD"
  quota: QuotaDetail;
}

function getSeverityClass(percentUsed: number): string {
  if (percentUsed >= 95) return "bg-red-500";
  if (percentUsed >= 80) return "bg-amber-500";
  return "bg-emerald-500";
}

function getTextClass(percentUsed: number): string {
  if (percentUsed >= 95) return "text-red-400";
  if (percentUsed >= 80) return "text-amber-400";
  return "text-emerald-400";
}

export function QuotaProgressBar({ label, quota }: QuotaProgressBarProps) {
  const pct = Math.min(100, quota.percent_used);

  return (
    <div className="space-y-1.5">
      <div className="flex items-center justify-between text-xs">
        <span className="font-medium text-slate-400">{label}</span>
        <span className={cn("font-semibold tabular-nums", getTextClass(pct))}>
          {pct.toFixed(1)}%
        </span>
      </div>
      <div className="h-1.5 w-full overflow-hidden rounded-full bg-slate-700/60">
        <div
          className={cn("h-full rounded-full transition-all duration-700", getSeverityClass(pct))}
          style={{ width: `${pct}%` }}
        />
      </div>
      <div className="flex justify-between text-[10px] text-slate-500">
        <span>{quota.used.toLocaleString()} used</span>
        <span>{quota.remaining.toLocaleString()} left</span>
      </div>
    </div>
  );
}
