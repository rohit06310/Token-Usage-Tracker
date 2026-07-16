"use client";

import { PieChart, Pie, Cell, Tooltip, Legend, ResponsiveContainer } from "recharts";
import type { PieLabelRenderProps } from "recharts";
import { formatCost, getProviderColor, CHART_COLORS } from "@/lib/utils";
import type { CostByProvider } from "@/lib/types";
import { EmptyState } from "@/components/shared/EmptyState";

interface CostPieChartProps {
  data: CostByProvider[];
}

const RADIAN = Math.PI / 180;

function renderCustomLabel(props: PieLabelRenderProps) {
  const { cx, cy, midAngle, innerRadius, outerRadius, percent } = props;
  if (
    typeof cx !== "number" ||
    typeof cy !== "number" ||
    typeof midAngle !== "number" ||
    typeof innerRadius !== "number" ||
    typeof outerRadius !== "number" ||
    typeof percent !== "number"
  ) return null;
  if (percent < 0.05) return null;
  const radius = innerRadius + (outerRadius - innerRadius) * 0.5;
  const x = cx + radius * Math.cos(-midAngle * RADIAN);
  const y = cy + radius * Math.sin(-midAngle * RADIAN);

  return (
    <text x={x} y={y} fill="white" textAnchor="middle" dominantBaseline="central" fontSize={11} fontWeight={600}>
      {`${(percent * 100).toFixed(0)}%`}
    </text>
  );
}

export function CostPieChart({ data }: CostPieChartProps) {
  if (!data || data.length === 0) {
    return <EmptyState title="No cost data" message="Costs will appear once API calls are made." className="min-h-[280px]" />;
  }

  const chartData = data.map((d) => ({
    name: d.provider_name,
    value: parseFloat(d.total_cost),
    slug: d.provider_slug,
  }));

  return (
    <ResponsiveContainer width="100%" height={300}>
      <PieChart>
        <Pie
          data={chartData}
          cx="50%"
          cy="50%"
          innerRadius={60}
          outerRadius={110}
          paddingAngle={3}
          dataKey="value"
          labelLine={false}
          label={renderCustomLabel}
        >
          {chartData.map((entry, i) => (
            <Cell
              key={entry.name}
              fill={getProviderColor(entry.slug) ?? CHART_COLORS[i % CHART_COLORS.length]}
              strokeWidth={0}
            />
          ))}
        </Pie>
        <Tooltip
          contentStyle={{
            backgroundColor: "#1e293b",
            border: "1px solid #334155",
            borderRadius: "10px",
          }}
          formatter={(value) => [formatCost(Number(value), 4), "Cost"]}
        />
        <Legend
          formatter={(value) => <span style={{ color: "#94a3b8", fontSize: 12 }}>{value}</span>}
        />
      </PieChart>
    </ResponsiveContainer>
  );
}
