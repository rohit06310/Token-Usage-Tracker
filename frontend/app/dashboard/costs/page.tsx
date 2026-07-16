"use client";

import { useState } from "react";
import { DollarSign } from "lucide-react";
import { useCostBreakdown } from "@/hooks/useCostBreakdown";
import { CostPieChart } from "@/components/charts/CostPieChart";
import { CostBarChart } from "@/components/charts/CostBarChart";
import { CostModelTable } from "@/components/tables/CostModelTable";
import { FilterBar, type FilterValues } from "@/components/filters/FilterBar";
import { ExportMenu } from "@/components/export/ExportMenu";
import { PageLoader } from "@/components/shared/LoadingSpinner";
import { ErrorState } from "@/components/shared/ErrorState";

const DEFAULT_FILTERS: FilterValues = {
  range: "30d",
  dateFrom: "",
  dateTo: "",
  providerId: "",
  model: "",
  projectTag: "",
};

export default function CostsPage() {
  const [filters, setFilters] = useState<FilterValues>(DEFAULT_FILTERS);
  const [view, setView] = useState<"pie" | "bar">("pie");

  let effectiveDateFrom = filters.dateFrom || undefined;
  let effectiveDateTo = filters.dateTo || undefined;
  
  if (filters.range !== "custom") {
    const today = new Date();
    effectiveDateTo = today.toISOString().split("T")[0];
    if (filters.range === "today") {
       effectiveDateFrom = effectiveDateTo;
    } else if (filters.range === "7d") {
       const past = new Date(today);
       past.setDate(past.getDate() - 7);
       effectiveDateFrom = past.toISOString().split("T")[0];
    } else if (filters.range === "30d") {
       const past = new Date(today);
       past.setDate(past.getDate() - 30);
       effectiveDateFrom = past.toISOString().split("T")[0];
    }
  }

  const { data, isLoading, isError, error } = useCostBreakdown({
    dateFrom: effectiveDateFrom,
    dateTo: effectiveDateTo,
    projectTag: filters.projectTag || undefined,
  });

  const csvParams = new URLSearchParams({
    type: "costs",
    ...(filters.projectTag ? { project_tag: filters.projectTag } : {}),
    ...(effectiveDateFrom ? { date_from: effectiveDateFrom } : {}),
    ...(effectiveDateTo ? { date_to: effectiveDateTo } : {}),
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-amber-500/15">
            <DollarSign className="h-5 w-5 text-amber-400" />
          </div>
          <div>
            <h2 className="text-lg font-bold text-slate-100">Cost Breakdown</h2>
            <p className="text-xs text-slate-500">Spending by provider and model</p>
          </div>
        </div>
        <ExportMenu csvUrl={`/api/export/csv?${csvParams.toString()}`} />
      </div>

      {/* Filters — only tag and custom date for costs */}
      <FilterBar
        values={filters}
        onChange={setFilters}
        showProviderFilter={false}
        showModelFilter={false}
        showTagFilter
      />

      {isLoading ? (
        <PageLoader label="Loading cost data..." />
      ) : isError ? (
        <ErrorState
          title="Failed to load cost data"
          message={error?.message ?? "An error occurred"}
        />
      ) : (
        <div className="space-y-6">
          {/* Charts row */}
          <div className="grid gap-6 lg:grid-cols-2">
            {/* Pie / Bar toggle + chart */}
            <div className="rounded-2xl border border-slate-700/50 bg-slate-800/60 p-6">
              <div className="mb-4 flex items-center justify-between">
                <h3 className="text-sm font-semibold text-slate-300">By Provider</h3>
                <div className="inline-flex rounded-lg border border-slate-700/50 bg-slate-800/60 p-0.5">
                  {(["pie", "bar"] as const).map((v) => (
                    <button
                      key={v}
                      onClick={() => setView(v)}
                      className={`rounded-md px-3 py-1 text-xs font-medium capitalize transition-all ${
                        view === v
                          ? "bg-violet-500/20 text-violet-300"
                          : "text-slate-500 hover:text-slate-300"
                      }`}
                    >
                      {v}
                    </button>
                  ))}
                </div>
              </div>
              {view === "pie" ? (
                <CostPieChart data={data?.by_provider ?? []} />
              ) : (
                <CostBarChart
                  data={(data?.by_provider ?? []).map((p) => ({
                    provider_id: p.provider_id,
                    provider_name: p.provider_name,
                    provider_slug: p.provider_slug,
                    model: p.provider_name,
                    call_count: p.call_count,
                    tokens_in: 0,
                    tokens_out: 0,
                    total_cost: p.total_cost,
                  }))}
                  maxItems={10}
                />
              )}
            </div>

            {/* Top models bar chart */}
            <div className="rounded-2xl border border-slate-700/50 bg-slate-800/60 p-6">
              <h3 className="mb-4 text-sm font-semibold text-slate-300">Top Models by Cost</h3>
              <CostBarChart data={data?.by_model ?? []} maxItems={10} />
            </div>
          </div>

          {/* Detailed model table */}
          <div className="rounded-2xl border border-slate-700/50 bg-slate-800/60 p-6">
            <h3 className="mb-4 text-sm font-semibold text-slate-300">All Models</h3>
            <CostModelTable data={data?.by_model ?? []} />
          </div>
        </div>
      )}
    </div>
  );
}
