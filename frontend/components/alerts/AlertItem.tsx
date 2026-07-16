"use client";

import { AlertTriangle, XCircle, Info, Clock } from "lucide-react";
import { cn, formatDate } from "@/lib/utils";
import type { AlertItem, AlertSeverity } from "@/lib/types";
import { EmptyState } from "@/components/shared/EmptyState";

interface AlertItemProps {
  alert: AlertItem;
}

const SEVERITY_CONFIG: Record<
  AlertSeverity,
  { icon: typeof AlertTriangle; label: string; classes: string }
> = {
  critical: {
    icon: XCircle,
    label: "Critical",
    classes: "border-red-500/30 bg-red-500/10",
  },
  warning: {
    icon: AlertTriangle,
    label: "Warning",
    classes: "border-amber-500/30 bg-amber-500/10",
  },
  info: {
    icon: Info,
    label: "Info",
    classes: "border-blue-500/30 bg-blue-500/10",
  },
};

const ICON_COLORS: Record<AlertSeverity, string> = {
  critical: "text-red-400",
  warning: "text-amber-400",
  info: "text-blue-400",
};

export function AlertListItem({ alert }: AlertItemProps) {
  const config = SEVERITY_CONFIG[alert.severity];
  const Icon = config.icon;

  return (
    <div
      className={cn(
        "flex items-start gap-3 rounded-xl border p-4 transition-colors hover:opacity-90",
        config.classes
      )}
    >
      <div className={cn("mt-0.5 shrink-0", ICON_COLORS[alert.severity])}>
        <Icon className="h-4 w-4" />
      </div>

      <div className="min-w-0 flex-1">
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-sm font-medium text-slate-200">{alert.message}</span>
          <span
            className={cn(
              "rounded-full border px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider",
              alert.severity === "critical"
                ? "border-red-500/30 text-red-400"
                : alert.severity === "warning"
                ? "border-amber-500/30 text-amber-400"
                : "border-blue-500/30 text-blue-400"
            )}
          >
            {config.label}
          </span>
        </div>
        <div className="mt-1 flex items-center gap-3 text-xs text-slate-500">
          <span className="inline-flex items-center gap-1">
            <Clock className="h-3 w-3" />
            {formatDate(alert.sent_at, true)}
          </span>
          <span>
            {alert.alert_type.toUpperCase()} • {parseFloat(alert.threshold_percent).toFixed(0)}% threshold
          </span>
          <span className="rounded bg-slate-700/50 px-1.5 py-0.5 font-mono text-[10px]">
            {alert.provider_slug}
          </span>
        </div>
      </div>
    </div>
  );
}

interface AlertsListProps {
  alerts: AlertItem[];
}

export function AlertsList({ alerts }: AlertsListProps) {
  if (alerts.length === 0) {
    return (
      <EmptyState
        title="No alerts"
        message="Alerts will appear here when usage thresholds are crossed."
        className="min-h-[200px]"
      />
    );
  }

  return (
    <div className="space-y-2">
      {alerts.map((alert) => (
        <AlertListItem key={alert.id} alert={alert} />
      ))}
    </div>
  );
}
