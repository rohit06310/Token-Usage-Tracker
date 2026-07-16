"use client";

import { usePathname } from "next/navigation";
import { RefreshCw, Menu } from "lucide-react";
import { useState } from "react";
import { MobileNav } from "./MobileNav";

const PAGE_TITLES: Record<string, string> = {
  "/dashboard": "Overview",
  "/dashboard/analytics": "Analytics",
  "/dashboard/costs": "Cost Breakdown",
  "/dashboard/alerts": "Alerts",
  "/dashboard/settings": "Settings",
};

interface TopbarProps {
  onRefresh?: () => void;
  isRefreshing?: boolean;
}

export function Topbar({ onRefresh, isRefreshing }: TopbarProps) {
  const pathname = usePathname();
  const [mobileOpen, setMobileOpen] = useState(false);
  const title = PAGE_TITLES[pathname] ?? "Dashboard";
  const now = new Date().toLocaleString("en-US", {
    weekday: "short",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });

  return (
    <>
      <header className="flex h-16 shrink-0 items-center justify-between border-b border-slate-700/50 bg-slate-900/80 px-6 backdrop-blur-xl print:hidden">
        {/* Mobile menu button */}
        <button
          className="mr-3 flex items-center justify-center rounded-lg p-2 text-slate-400 hover:bg-slate-800 hover:text-slate-200 lg:hidden"
          onClick={() => setMobileOpen(true)}
          aria-label="Open navigation"
        >
          <Menu className="h-5 w-5" />
        </button>

        <div>
          <h1 className="text-lg font-bold text-slate-100">{title}</h1>
          <p className="text-xs text-slate-500">{now}</p>
        </div>

        <div className="flex items-center gap-3">
          {onRefresh && (
            <button
              onClick={onRefresh}
              disabled={isRefreshing}
              className="flex items-center gap-2 rounded-lg border border-slate-700/50 bg-slate-800/60 px-3 py-1.5 text-xs font-medium text-slate-400 transition hover:border-slate-600 hover:text-slate-200 disabled:opacity-50"
              aria-label="Refresh data"
            >
              <RefreshCw className={`h-3.5 w-3.5 ${isRefreshing ? "animate-spin" : ""}`} />
              Refresh
            </button>
          )}
          <div className="flex h-8 w-8 items-center justify-center rounded-full bg-violet-500/20 text-sm font-bold text-violet-400">
            A
          </div>
        </div>
      </header>

      <MobileNav open={mobileOpen} onClose={() => setMobileOpen(false)} />
    </>
  );
}
