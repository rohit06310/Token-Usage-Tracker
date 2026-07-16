"use client";

import { formatCost, formatNumber, getProviderColor } from "@/lib/utils";
import type { CostByModel } from "@/lib/types";
import { EmptyState } from "@/components/shared/EmptyState";

interface CostModelTableProps {
  data: CostByModel[];
}

export function CostModelTable({ data }: CostModelTableProps) {
  if (!data || data.length === 0) {
    return <EmptyState title="No data" message="Cost data by model will appear here." className="min-h-[200px]" />;
  }

  const totalCost = data.reduce((sum, d) => sum + parseFloat(d.total_cost), 0);

  return (
    <div className="overflow-hidden rounded-xl border border-slate-700/50">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-slate-700/50 bg-slate-800/60">
            <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-slate-400">
              Provider / Model
            </th>
            <th className="px-4 py-3 text-right text-xs font-semibold uppercase tracking-wider text-slate-400">
              Calls
            </th>
            <th className="px-4 py-3 text-right text-xs font-semibold uppercase tracking-wider text-slate-400">
              Tokens In
            </th>
            <th className="px-4 py-3 text-right text-xs font-semibold uppercase tracking-wider text-slate-400">
              Tokens Out
            </th>
            <th className="px-4 py-3 text-right text-xs font-semibold uppercase tracking-wider text-slate-400">
              Cost
            </th>
            <th className="px-4 py-3 text-right text-xs font-semibold uppercase tracking-wider text-slate-400">
              % of Total
            </th>
          </tr>
        </thead>
        <tbody>
          {data.map((row, i) => {
            const cost = parseFloat(row.total_cost);
            const pct = totalCost > 0 ? (cost / totalCost) * 100 : 0;
            const color = getProviderColor(row.provider_slug);

            return (
              <tr
                key={`${row.provider_id}-${row.model}`}
                className="border-b border-slate-700/30 transition-colors hover:bg-slate-800/30"
              >
                <td className="px-4 py-3">
                  <div className="flex items-center gap-2">
                    <div
                      className="h-2 w-2 shrink-0 rounded-full"
                      style={{ backgroundColor: color }}
                    />
                    <div>
                      <div className="font-medium text-slate-200">{row.model}</div>
                      <div className="text-[10px] text-slate-500">{row.provider_name}</div>
                    </div>
                  </div>
                </td>
                <td className="px-4 py-3 text-right tabular-nums text-slate-300">
                  {formatNumber(row.call_count)}
                </td>
                <td className="px-4 py-3 text-right tabular-nums text-slate-400">
                  {formatNumber(row.tokens_in)}
                </td>
                <td className="px-4 py-3 text-right tabular-nums text-slate-400">
                  {formatNumber(row.tokens_out)}
                </td>
                <td className="px-4 py-3 text-right tabular-nums font-medium text-slate-200">
                  {formatCost(row.total_cost, 4)}
                </td>
                <td className="px-4 py-3">
                  <div className="flex items-center justify-end gap-2">
                    <div className="h-1.5 w-16 overflow-hidden rounded-full bg-slate-700/50">
                      <div
                        className="h-full rounded-full"
                        style={{ width: `${pct}%`, backgroundColor: color }}
                      />
                    </div>
                    <span className="w-10 text-right text-xs tabular-nums text-slate-400">
                      {pct.toFixed(1)}%
                    </span>
                  </div>
                </td>
              </tr>
            );
          })}
        </tbody>
        <tfoot>
          <tr className="bg-slate-800/40">
            <td className="px-4 py-3 text-xs font-semibold text-slate-400">
              Total ({data.length} models)
            </td>
            <td className="px-4 py-3 text-right tabular-nums text-xs font-semibold text-slate-300">
              {formatNumber(data.reduce((s, d) => s + d.call_count, 0))}
            </td>
            <td colSpan={2} />
            <td className="px-4 py-3 text-right tabular-nums text-xs font-semibold text-slate-200">
              {formatCost(totalCost, 4)}
            </td>
            <td />
          </tr>
        </tfoot>
      </table>
    </div>
  );
}
