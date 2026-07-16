"use client";

import { useState } from "react";
import { Calendar, X } from "lucide-react";
import { useProviders } from "@/hooks/useProviders";
import { useTags } from "@/hooks/useTags";
import { useModels } from "@/hooks/useModels";

export interface FilterValues {
  range: "today" | "7d" | "30d" | "custom";
  dateFrom: string;
  dateTo: string;
  providerId: string;
  model: string;
  projectTag: string;
}

interface FilterBarProps {
  values: FilterValues;
  onChange: (values: FilterValues) => void;
  showProviderFilter?: boolean;
  showModelFilter?: boolean;
  showTagFilter?: boolean;
}

const RANGES = [
  { value: "today", label: "Today" },
  { value: "7d", label: "7 Days" },
  { value: "30d", label: "30 Days" },
  { value: "custom", label: "Custom" },
];

export function FilterBar({
  values,
  onChange,
  showProviderFilter = true,
  showModelFilter = true,
  showTagFilter = true,
}: FilterBarProps) {
  const { providers } = useProviders();
  const { tags } = useTags();
  const { models } = useModels(values.providerId || null);

  const update = (patch: Partial<FilterValues>) => onChange({ ...values, ...patch });
  const activeFilterCount = [values.providerId, values.model, values.projectTag, values.range !== "7d" ? values.range : null].filter(Boolean).length;

  return (
    <div className="flex flex-wrap items-center gap-2 rounded-xl border border-slate-700/50 bg-slate-800/40 p-3">
      {/* Range Toggles */}
      <div className="flex rounded-lg border border-slate-700/50 bg-slate-800/60 p-0.5">
        {RANGES.map((r) => (
          <button
            key={r.value}
            onClick={() => update({ range: r.value as FilterValues["range"] })}
            className={`rounded-md px-2.5 py-1 text-xs font-medium transition-all ${
              values.range === r.value
                ? "bg-violet-500/20 text-violet-300"
                : "text-slate-500 hover:text-slate-300"
            }`}
          >
            {r.label}
          </button>
        ))}
      </div>

      {/* Custom Date Range */}
      {values.range === "custom" && (
        <div className="flex items-center gap-1.5">
          <Calendar className="h-3.5 w-3.5 text-slate-500" />
          <input
            type="date"
            value={values.dateFrom}
            onChange={(e) => update({ dateFrom: e.target.value })}
            className="rounded-lg border border-slate-700/50 bg-slate-800 px-2 py-1 text-xs text-slate-300 focus:border-violet-500/50 focus:outline-none"
            aria-label="Date from"
          />
          <span className="text-xs text-slate-600">→</span>
          <input
            type="date"
            value={values.dateTo}
            onChange={(e) => update({ dateTo: e.target.value })}
            className="rounded-lg border border-slate-700/50 bg-slate-800 px-2 py-1 text-xs text-slate-300 focus:border-violet-500/50 focus:outline-none"
            aria-label="Date to"
          />
        </div>
      )}

      {/* Provider Filter */}
      {showProviderFilter && (
        <select
          value={values.providerId}
          onChange={(e) => update({ providerId: e.target.value, model: "" })}
          className="rounded-lg border border-slate-700/50 bg-slate-800 px-2.5 py-1.5 text-xs text-slate-300 focus:border-violet-500/50 focus:outline-none"
          aria-label="Filter by provider"
        >
          <option value="">All Providers</option>
          {providers.map((p) => (
            <option key={p.id} value={p.id}>
              {p.name}
            </option>
          ))}
        </select>
      )}

      {/* Model Filter */}
      {showModelFilter && models.length > 0 && (
        <select
          value={values.model}
          onChange={(e) => update({ model: e.target.value })}
          className="rounded-lg border border-slate-700/50 bg-slate-800 px-2.5 py-1.5 text-xs text-slate-300 focus:border-violet-500/50 focus:outline-none"
          aria-label="Filter by model"
        >
          <option value="">All Models</option>
          {models.map((m) => (
            <option key={`${m.provider_id}-${m.model}`} value={m.model}>
              {m.model}
            </option>
          ))}
        </select>
      )}

      {/* Project Tag Filter */}
      {showTagFilter && tags.length > 0 && (
        <select
          value={values.projectTag}
          onChange={(e) => update({ projectTag: e.target.value })}
          className="rounded-lg border border-slate-700/50 bg-slate-800 px-2.5 py-1.5 text-xs text-slate-300 focus:border-violet-500/50 focus:outline-none"
          aria-label="Filter by project tag"
        >
          <option value="">All Tags</option>
          {tags.map((t) => (
            <option key={t.tag} value={t.tag}>
              {t.tag} ({t.call_count})
            </option>
          ))}
        </select>
      )}

      {/* Clear Filters */}
      {activeFilterCount > 0 && (
        <button
          onClick={() =>
            onChange({
              range: "7d",
              dateFrom: "",
              dateTo: "",
              providerId: "",
              model: "",
              projectTag: "",
            })
          }
          className="flex items-center gap-1 rounded-lg border border-slate-700/50 px-2 py-1 text-xs text-slate-500 hover:border-slate-600 hover:text-slate-300"
        >
          <X className="h-3 w-3" />
          Clear ({activeFilterCount})
        </button>
      )}
    </div>
  );
}
