"use client";

import { useState } from "react";
import { Bell, RefreshCw, AlertTriangle, XCircle } from "lucide-react";
import { useRecentAlerts } from "@/hooks/useRecentAlerts";
import { AlertsList } from "@/components/alerts/AlertItem";
import { ExportMenu } from "@/components/export/ExportMenu";
import { PageLoader } from "@/components/shared/LoadingSpinner";
import { ErrorState } from "@/components/shared/ErrorState";
import type { AlertSeverity } from "@/lib/types";

export default function AlertsPage() {
  const [severityFilter, setSeverityFilter] = useState<AlertSeverity | "all">("all");
  const { data, isLoading, isError, error, refresh } = useRecentAlerts({ limit: 100 });

  const allItems = data?.items ?? [];
  const filteredItems =
    severityFilter === "all"
      ? allItems
      : allItems.filter((a) => a.severity === severityFilter);

  const criticalCount = allItems.filter((a) => a.severity === "critical").length;
  const warningCount = allItems.filter((a) => a.severity === "warning").length;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-red-500/15">
            <Bell className="h-5 w-5 text-red-400" />
          </div>
          <div>
            <h2 className="text-lg font-bold text-slate-100">Alerts & Notifications</h2>
            <p className="text-xs text-slate-500">
              Recent rate limit threshold crossings
              {data?.total !== undefined && ` · ${data.total} total`}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => refresh()}
            className="flex items-center gap-1.5 rounded-lg border border-slate-700/50 bg-slate-800/60 px-3 py-2 text-xs font-medium text-slate-400 transition hover:text-slate-200"
          >
            <RefreshCw className="h-3.5 w-3.5" />
            Refresh
          </button>
          <ExportMenu csvUrl="/api/export/csv?type=alerts" />
        </div>
      </div>

      {/* Severity summary cards */}
      {!isLoading && !isError && (
        <div className="grid grid-cols-3 gap-4 sm:grid-cols-3">
          <SeverityCard
            label="Total Alerts"
            count={allItems.length}
            color="#64748b"
            onClick={() => setSeverityFilter("all")}
            active={severityFilter === "all"}
          />
          <SeverityCard
            icon={<XCircle className="h-4 w-4" />}
            label="Critical"
            count={criticalCount}
            color="#ef4444"
            onClick={() => setSeverityFilter("critical")}
            active={severityFilter === "critical"}
          />
          <SeverityCard
            icon={<AlertTriangle className="h-4 w-4" />}
            label="Warnings"
            count={warningCount}
            color="#f59e0b"
            onClick={() => setSeverityFilter("warning")}
            active={severityFilter === "warning"}
          />
        </div>
      )}

      {/* Alert list */}
      <div className="rounded-2xl border border-slate-700/50 bg-slate-800/60 p-6">
        <div className="mb-4 flex items-center justify-between">
          <h3 className="text-sm font-semibold text-slate-300">
            {severityFilter === "all" ? "All Alerts" : `${severityFilter.charAt(0).toUpperCase() + severityFilter.slice(1)} Alerts`}
            <span className="ml-2 rounded-full bg-slate-700/60 px-2 py-0.5 text-xs text-slate-400">
              {filteredItems.length}
            </span>
          </h3>
        </div>

        {isLoading ? (
          <PageLoader label="Loading alerts..." />
        ) : isError ? (
          <ErrorState
            title="Failed to load alerts"
            message={error?.message ?? "An error occurred"}
            onRetry={() => refresh()}
          />
        ) : (
          <AlertsList alerts={filteredItems} />
        )}
      </div>
    </div>
  );
}

function SeverityCard({
  icon,
  label,
  count,
  color,
  onClick,
  active,
}: {
  icon?: React.ReactNode;
  label: string;
  count: number;
  color: string;
  onClick: () => void;
  active: boolean;
}) {
  return (
    <button
      onClick={onClick}
      className={`flex flex-col gap-2 rounded-xl border p-4 text-left transition-all ${
        active
          ? "border-opacity-50 bg-opacity-15"
          : "border-slate-700/50 bg-slate-800/60 hover:bg-slate-800"
      }`}
      style={
        active
          ? {
              borderColor: `${color}50`,
              backgroundColor: `${color}10`,
            }
          : undefined
      }
    >
      <div className="flex items-center gap-2" style={{ color }}>
        {icon}
        <span className="text-xs font-medium text-slate-400">{label}</span>
      </div>
      <p className="text-3xl font-bold tabular-nums" style={{ color }}>
        {count}
      </p>
    </button>
  );
}
