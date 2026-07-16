"use client";

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";
import { formatCost, getProviderColor, CHART_COLORS } from "@/lib/utils";
import type { CostByModel } from "@/lib/types";
import { EmptyState } from "@/components/shared/EmptyState";

interface CostBarChartProps {
  data: CostByModel[];
  maxItems?: number;
}

export function CostBarChart({ data, maxItems = 15 }: CostBarChartProps) {
  if (!data || data.length === 0) {
    return <EmptyState title="No model cost data" message="Costs by model will appear once API calls are logged." className="min-h-[280px]" />;
  }

  const chartData = data
    .slice(0, maxItems)
    .map((d) => ({
      label: `${d.model}`,
      provider: d.provider_slug,
      value: parseFloat(d.total_cost),
      calls: d.call_count,
    }));

  return (
    <ResponsiveContainer width="100%" height={Math.max(250, chartData.length * 38)}>
      <BarChart
        data={chartData}
        layout="vertical"
        margin={{ top: 0, right: 20, left: 8, bottom: 0 }}
      >
        <CartesianGrid strokeDasharray="3 3" stroke="#334155" strokeOpacity={0.4} horizontal={false} />
        <XAxis
          type="number"
          tickFormatter={(v) => formatCost(v)}
          tick={{ fill: "#94a3b8", fontSize: 10 }}
          axisLine={{ stroke: "#334155" }}
          tickLine={false}
        />
        <YAxis
          type="category"
          dataKey="label"
          width={160}
          tick={{ fill: "#94a3b8", fontSize: 10 }}
          axisLine={false}
          tickLine={false}
        />
        <Tooltip
          contentStyle={{
            backgroundColor: "#1e293b",
            border: "1px solid #334155",
            borderRadius: "10px",
          }}
          formatter={(value, _name, props) => [
            formatCost(Number(value), 6),
            `${(props as { payload?: { calls?: number } }).payload?.calls ?? 0} calls`,
          ]}
        />
        <Bar dataKey="value" radius={[0, 4, 4, 0]} maxBarSize={20}>
          {chartData.map((entry, i) => (
            <Cell
              key={entry.label}
              fill={getProviderColor(entry.provider) ?? CHART_COLORS[i % CHART_COLORS.length]}
            />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
