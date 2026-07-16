"use client";

import { useDashboardSummary } from "@/hooks/useDashboardSummary";
import { ProviderCard } from "@/components/dashboard/ProviderCard";
import { ProviderCardSkeleton } from "@/components/dashboard/ProviderCardSkeleton";
import { ErrorState } from "@/components/shared/ErrorState";
import { EmptyState } from "@/components/shared/EmptyState";
import { formatCost, formatTokens, formatNumber } from "@/lib/utils";
import { Activity, DollarSign, Zap, LayoutDashboard } from "lucide-react";

export default function DashboardPage() {
  const { data, isLoading, isError, error, refresh } = useDashboardSummary();

  if (isError) {
    return (
      <ErrorState
        title="Failed to load dashboard"
        message={
          error?.message?.includes("503")
            ? "The backend API is unreachable. Ensure FastAPI is running on port 8000."
            : error?.message ?? "An unexpected error occurred."
        }
        onRetry={refresh}
        className="min-h-[400px]"
      />
    );
  }

  const providers = data?.providers ?? [];

  // Aggregate totals
  const totalCallsToday = providers.reduce((s, p) => s + p.call_count_today, 0);
  const totalTokensToday = providers.reduce((s, p) => s + p.total_tokens_today, 0);
  const totalCostToday = providers.reduce((s, p) => s + parseFloat(p.total_cost_today), 0);
  const totalCost30d = providers.reduce((s, p) => s + parseFloat(p.total_cost_30d), 0);

  return (
    <div className="space-y-6">
      {/* Page header */}
      <div className="flex items-center gap-3">
        <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-violet-500/15">
          <LayoutDashboard className="h-5 w-5 text-violet-400" />
        </div>
        <div>
          <h2 className="text-lg font-bold text-slate-100">Provider Overview</h2>
          <p className="text-xs text-slate-500">
            Live rate-limit quotas refresh every 30 seconds
            {data?.generated_at && (
              <> · Last updated {new Date(data.generated_at).toLocaleTimeString()}</>
            )}
          </p>
        </div>
      </div>

      {/* Summary stat row */}
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        <SummaryStatCard
          icon={<Activity className="h-4 w-4" />}
          label="API Calls Today"
          value={isLoading ? "—" : formatNumber(totalCallsToday)}
          color="#10b981"
        />
        <SummaryStatCard
          icon={<Zap className="h-4 w-4" />}
          label="Tokens Today"
          value={isLoading ? "—" : formatTokens(totalTokensToday)}
          color="#8b5cf6"
        />
        <SummaryStatCard
          icon={<DollarSign className="h-4 w-4" />}
          label="Cost Today"
          value={isLoading ? "—" : formatCost(totalCostToday)}
          color="#f59e0b"
        />
        <SummaryStatCard
          icon={<DollarSign className="h-4 w-4" />}
          label="Cost (30 days)"
          value={isLoading ? "—" : formatCost(totalCost30d)}
          color="#3b82f6"
        />
      </div>

      {/* Provider cards grid */}
      {isLoading ? (
        <div className="grid gap-5 sm:grid-cols-2 xl:grid-cols-2 2xl:grid-cols-4">
          {[0, 1, 2, 3].map((i) => (
            <ProviderCardSkeleton key={i} />
          ))}
        </div>
      ) : providers.length === 0 ? (
        <EmptyState
          title="No providers configured"
          message="Register a provider via POST /api/v1/providers/ to get started."
          className="min-h-[300px]"
        />
      ) : (
        <div className="grid gap-5 sm:grid-cols-2 xl:grid-cols-2 2xl:grid-cols-4">
          {providers.map((provider) => (
            <ProviderCard key={provider.provider_id} provider={provider} />
          ))}
        </div>
      )}
    </div>
  );
}

function SummaryStatCard({
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
    <div className="relative overflow-hidden rounded-xl border border-slate-700/50 bg-slate-800/60 p-4 backdrop-blur-sm">
      <div className="mb-3 flex items-center gap-2" style={{ color }}>
        {icon}
        <span className="text-xs font-medium text-slate-400">{label}</span>
      </div>
      <p className="text-2xl font-bold tabular-nums text-slate-100">{value}</p>
      <div
        className="absolute bottom-0 left-0 right-0 h-[1px] opacity-30"
        style={{ background: `linear-gradient(to right, ${color}, transparent)` }}
      />
    </div>
  );
}
