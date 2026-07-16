"use client";

import { useState } from "react";
import { BarChart3 } from "lucide-react";
import { useUsageHistory } from "@/hooks/useUsageHistory";
import { UsageChart } from "@/components/charts/UsageChart";
import { FilterBar, type FilterValues } from "@/components/filters/FilterBar";
import { ExportMenu } from "@/components/export/ExportMenu";
import { RecentLogsTable } from "@/components/logs/RecentLogsTable";
import { PageLoader } from "@/components/shared/LoadingSpinner";
import { ErrorState } from "@/components/shared/ErrorState";

const DEFAULT_FILTERS: FilterValues = {
  range: "7d",
  dateFrom: "",
  dateTo: "",
  providerId: "",
  model: "",
  projectTag: "",
};

type Metric = "total_tokens" | "call_count" | "total_cost";
type GroupBy = "day" | "hour";

export default function AnalyticsPage() {
  const [filters, setFilters] = useState<FilterValues>(DEFAULT_FILTERS);
  const [metric, setMetric] = useState<Metric>("total_tokens");
  const [groupBy, setGroupBy] = useState<GroupBy>("day");

  const { data, isLoading, isError, error } = useUsageHistory({
    range: filters.range,
    groupBy,
    providerId: filters.providerId || null,
    projectTag: filters.projectTag || null,
    model: filters.model || null,
    dateFrom: filters.dateFrom || null,
    dateTo: filters.dateTo || null,
  });

  // Build CSV export URL from current filters
  const csvParams = new URLSearchParams({
    type: "usage",
    range: filters.range,
    group_by: groupBy,
    ...(filters.providerId ? { provider_id: filters.providerId } : {}),
    ...(filters.model ? { model: filters.model } : {}),
    ...(filters.projectTag ? { project_tag: filters.projectTag } : {}),
    ...(filters.dateFrom ? { date_from: filters.dateFrom } : {}),
    ...(filters.dateTo ? { date_to: filters.dateTo } : {}),
  });
  const csvUrl = `/api/export/csv?${csvParams.toString()}`;

  const METRIC_LABELS: Record<Metric, string> = {
    total_tokens: "Tokens",
    call_count: "API Calls",
    total_cost: "Cost (USD)",
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-blue-500/15">
            <BarChart3 className="h-5 w-5 text-blue-400" />
          </div>
          <div>
            <h2 className="text-lg font-bold text-slate-100">Usage Over Time</h2>
            <p className="text-xs text-slate-500">Token consumption and API call trends</p>
          </div>
        </div>
        <ExportMenu csvUrl={csvUrl} />
      </div>

      {/* Filters */}
      <FilterBar values={filters} onChange={setFilters} />

      {/* Metric + groupBy toggles */}
      <div className="flex flex-wrap items-center gap-3">
        <div>
          <p className="mb-1.5 text-[10px] font-semibold uppercase tracking-wider text-slate-500">Metric</p>
          <div className="inline-flex rounded-lg border border-slate-700/50 bg-slate-800/60 p-0.5">
            {(Object.keys(METRIC_LABELS) as Metric[]).map((m) => (
              <button
                key={m}
                onClick={() => setMetric(m)}
                className={`rounded-md px-3 py-1.5 text-xs font-medium transition-all ${
                  metric === m
                    ? "bg-violet-500/20 text-violet-300"
                    : "text-slate-500 hover:text-slate-300"
                }`}
              >
                {METRIC_LABELS[m]}
              </button>
            ))}
          </div>
        </div>
        <div>
          <p className="mb-1.5 text-[10px] font-semibold uppercase tracking-wider text-slate-500">Group by</p>
          <div className="inline-flex rounded-lg border border-slate-700/50 bg-slate-800/60 p-0.5">
            {(["day", "hour"] as GroupBy[]).map((g) => (
              <button
                key={g}
                onClick={() => setGroupBy(g)}
                className={`rounded-md px-3 py-1.5 text-xs font-medium capitalize transition-all ${
                  groupBy === g
                    ? "bg-violet-500/20 text-violet-300"
                    : "text-slate-500 hover:text-slate-300"
                }`}
              >
                {g}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Chart */}
      <div className="rounded-2xl border border-slate-700/50 bg-slate-800/60 p-6">
        {isLoading ? (
          <PageLoader label="Loading chart data..." />
        ) : isError ? (
          <ErrorState
            title="Failed to load usage data"
            message={error?.message ?? "An error occurred"}
          />
        ) : (
          <UsageChart data={data?.data ?? []} groupBy={groupBy} metric={metric} />
        )}
      </div>

      {/* Data summary */}
      {data && (
        <p className="text-xs text-slate-600">
          Showing {data.data.length} data points from {new Date(data.start).toLocaleDateString()} to{" "}
          {new Date(data.end).toLocaleDateString()}
        </p>
      )}
      
      {/* Detailed Logs Table */}
      <div className="pt-6 border-t border-slate-700/50 mt-10">
        <RecentLogsTable 
          providerId={filters.providerId || null}
          projectTag={filters.projectTag || null}
          model={filters.model || null}
          dateFrom={filters.dateFrom || null}
          dateTo={filters.dateTo || null}
        />
      </div>
    </div>
  );
}
