"use client";

import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import { useMemo, useState } from "react";
import { formatDate, getProviderColor, CHART_COLORS, formatTokens } from "@/lib/utils";
import type { UsageHistoryPoint } from "@/lib/types";
import { EmptyState } from "@/components/shared/EmptyState";

interface UsageChartProps {
  data: UsageHistoryPoint[];
  groupBy?: string;
  metric?: "total_tokens" | "call_count" | "total_cost";
}

type ChartType = "line" | "bar";

// Pivot flat data into chart-friendly format: { period, openai: 1234, anthropic: 456 }
function pivotData(data: UsageHistoryPoint[], metric: string) {
  const periodMap = new Map<string, Record<string, number>>();
  const providers = new Set<string>();

  for (const point of data) {
    const existing = periodMap.get(point.period) ?? {};
    existing[point.provider_slug] = (existing[point.provider_slug] ?? 0) + Number(point[metric as keyof UsageHistoryPoint] ?? 0);
    periodMap.set(point.period, existing);
    providers.add(point.provider_slug);
  }

  const sorted = Array.from(periodMap.entries())
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([period, values]) => ({ period, ...values }));

  return { rows: sorted, providers: Array.from(providers) };
}

const METRIC_LABELS: Record<string, string> = {
  total_tokens: "Tokens",
  call_count: "API Calls",
  total_cost: "Cost (USD)",
};

export function UsageChart({ data, groupBy = "day", metric = "total_tokens" }: UsageChartProps) {
  const [chartType, setChartType] = useState<ChartType>("line");

  const { rows, providers } = useMemo(() => pivotData(data, metric), [data, metric]);

  if (rows.length === 0) {
    return (
      <EmptyState
        title="No usage data"
        message="API calls will appear here once your adapters log usage."
        className="min-h-[300px]"
      />
    );
  }

  const formatXTick = (val: string) => {
    try {
      const d = new Date(val);
      return groupBy === "hour"
        ? d.toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit" })
        : d.toLocaleDateString("en-US", { month: "short", day: "numeric" });
    } catch {
      return val;
    }
  };

  const formatYTick = (val: number) => {
    if (metric === "total_cost") return `$${val.toFixed(2)}`;
    return formatTokens(val);
  };

  const tooltipFormatter = (value: unknown, name: unknown) => {
    const formatted =
      metric === "total_cost" ? `$${Number(value).toFixed(4)}` : formatTokens(Number(value));
    return [formatted, String(name)];
  };

  const ChartComponent = chartType === "line" ? LineChart : BarChart;

  return (
    <div className="space-y-3">
      {/* Chart type toggle */}
      <div className="flex justify-end">
        <div className="inline-flex rounded-lg border border-slate-700/50 bg-slate-800/60 p-0.5">
          {(["line", "bar"] as ChartType[]).map((t) => (
            <button
              key={t}
              onClick={() => setChartType(t)}
              className={`rounded-md px-3 py-1 text-xs font-medium capitalize transition-all ${
                chartType === t
                  ? "bg-violet-500/20 text-violet-300"
                  : "text-slate-500 hover:text-slate-300"
              }`}
            >
              {t}
            </button>
          ))}
        </div>
      </div>

      <ResponsiveContainer width="100%" height={320}>
        <ChartComponent data={rows}>
          <CartesianGrid strokeDasharray="3 3" stroke="#334155" strokeOpacity={0.5} />
          <XAxis
            dataKey="period"
            tickFormatter={formatXTick}
            tick={{ fill: "#94a3b8", fontSize: 11 }}
            axisLine={{ stroke: "#334155" }}
            tickLine={false}
          />
          <YAxis
            tickFormatter={formatYTick}
            tick={{ fill: "#94a3b8", fontSize: 11 }}
            axisLine={{ stroke: "#334155" }}
            tickLine={false}
            width={65}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: "#1e293b",
              border: "1px solid #334155",
              borderRadius: "10px",
              boxShadow: "0 4px 24px rgba(0,0,0,0.4)",
            }}
            labelStyle={{ color: "#94a3b8", fontSize: 11, marginBottom: 4 }}
            labelFormatter={(label) => formatDate(label, true)}
            formatter={tooltipFormatter}
          />
          <Legend
            wrapperStyle={{ paddingTop: 16 }}
            formatter={(value) => (
              <span style={{ color: "#94a3b8", fontSize: 11 }}>{value}</span>
            )}
          />
          {providers.map((slug, i) => {
            const color = getProviderColor(slug) ?? CHART_COLORS[i % CHART_COLORS.length];
            return chartType === "line" ? (
              <Line
                key={slug}
                type="monotone"
                dataKey={slug}
                name={slug}
                stroke={color}
                strokeWidth={2}
                dot={false}
                activeDot={{ r: 5, strokeWidth: 0 }}
              />
            ) : (
              <Bar key={slug} dataKey={slug} name={slug} fill={color} radius={[3, 3, 0, 0]} />
            );
          })}
        </ChartComponent>
      </ResponsiveContainer>
    </div>
  );
}
