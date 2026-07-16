import { useState } from "react";
import { List } from "lucide-react";
import { useUsageLogs } from "@/hooks/useUsageLogs";
import { PageLoader } from "@/components/shared/LoadingSpinner";
import { ErrorState } from "@/components/shared/ErrorState";
import { formatNumber, formatCost } from "@/lib/utils";

interface RecentLogsTableProps {
  providerId?: string | null;
  projectTag?: string | null;
  model?: string | null;
  dateFrom?: string | null;
  dateTo?: string | null;
}

export function RecentLogsTable({
  providerId,
  projectTag,
  model,
  dateFrom,
  dateTo,
}: RecentLogsTableProps) {
  const [page, setPage] = useState(0);
  const limit = 10;

  const { data: logs, total, isLoading, isError, error } = useUsageLogs({
    providerId,
    projectTag,
    model,
    dateFrom,
    dateTo,
    limit,
    offset: page * limit,
  });

  const totalPages = Math.ceil(total / limit);

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3">
        <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-orange-500/15">
          <List className="h-5 w-5 text-orange-400" />
        </div>
        <div>
          <h2 className="text-lg font-bold text-slate-100">Detailed Usage Logs</h2>
          <p className="text-xs text-slate-500">Individual API requests and token breakdown</p>
        </div>
      </div>

      <div className="rounded-2xl border border-slate-700/50 bg-slate-800/60 overflow-hidden">
        {isLoading ? (
          <div className="p-8">
             <PageLoader label="Loading logs..." />
          </div>
        ) : isError ? (
          <div className="p-8">
            <ErrorState title="Failed to load logs" message={error?.message || "Error"} />
          </div>
        ) : !logs || logs.length === 0 ? (
          <div className="p-8 text-center text-slate-400">No logs found for the selected filters.</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-slate-300">
              <thead className="bg-slate-800/80 text-xs uppercase text-slate-400">
                <tr>
                  <th className="px-6 py-4 font-medium tracking-wider">Date & Time</th>
                  <th className="px-6 py-4 font-medium tracking-wider">Model</th>
                  <th className="px-6 py-4 font-medium tracking-wider">Status</th>
                  <th className="px-6 py-4 font-medium tracking-wider text-right">Tokens In</th>
                  <th className="px-6 py-4 font-medium tracking-wider text-right">Tokens Out</th>
                  <th className="px-6 py-4 font-medium tracking-wider text-right">Cost (USD)</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-700/50">
                {logs.map((log) => (
                  <tr key={log.id} className="hover:bg-slate-700/20 transition-colors">
                    <td className="px-6 py-4 whitespace-nowrap">
                      {new Date(log.created_at).toLocaleString()}
                    </td>
                    <td className="px-6 py-4">
                      <span className="inline-flex items-center rounded-md bg-slate-700/50 px-2 py-1 text-xs font-medium text-slate-300">
                        {log.model}
                      </span>
                      {log.project_tag && (
                        <span className="ml-2 inline-flex items-center rounded-md bg-blue-500/10 px-2 py-1 text-xs font-medium text-blue-400">
                          {log.project_tag}
                        </span>
                      )}
                    </td>
                    <td className="px-6 py-4">
                      <span className={`inline-flex items-center rounded-md px-2 py-1 text-xs font-medium ${
                        log.status === 'success' ? 'bg-emerald-500/10 text-emerald-400' : 'bg-rose-500/10 text-rose-400'
                      }`}>
                        {log.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-right font-mono text-emerald-400/90">
                      {formatNumber(log.tokens_in)}
                    </td>
                    <td className="px-6 py-4 text-right font-mono text-sky-400/90">
                      {formatNumber(log.tokens_out)}
                    </td>
                    <td className="px-6 py-4 text-right font-mono">
                      {formatCost(log.cost)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        
        {/* Pagination UI */}
        <div className="border-t border-slate-700/50 bg-slate-800/80 px-6 py-3 flex items-center justify-between">
          <button 
            onClick={() => setPage(p => Math.max(0, p - 1))}
            disabled={page === 0 || isLoading}
            className="text-sm text-slate-400 hover:text-white disabled:opacity-50"
          >
            Previous
          </button>
          <span className="text-xs text-slate-500">
            Page {page + 1} {totalPages > 0 && `of ${totalPages}`}
          </span>
          <button 
            onClick={() => setPage(p => p + 1)}
            disabled={page >= totalPages - 1 || isLoading}
            className="text-sm text-slate-400 hover:text-white disabled:opacity-50"
          >
            Next
          </button>
        </div>
      </div>
    </div>
  );
}
