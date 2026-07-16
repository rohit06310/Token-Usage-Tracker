"use client";

import { BarChart3 } from "lucide-react";
import { cn } from "@/lib/utils";

interface EmptyStateProps {
  title?: string;
  message?: string;
  icon?: React.ReactNode;
  className?: string;
}

export function EmptyState({
  title = "No data yet",
  message = "Data will appear here once API calls are logged.",
  icon,
  className,
}: EmptyStateProps) {
  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center gap-4 rounded-xl border border-slate-700/50 bg-slate-800/30 p-10 text-center",
        className
      )}
    >
      <div className="flex h-14 w-14 items-center justify-center rounded-full bg-slate-700/50">
        {icon ?? <BarChart3 className="h-7 w-7 text-slate-500" />}
      </div>
      <div>
        <h3 className="text-base font-semibold text-slate-300">{title}</h3>
        <p className="mt-1 text-sm text-slate-500">{message}</p>
      </div>
    </div>
  );
}
