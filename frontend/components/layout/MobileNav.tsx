"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { X, LayoutDashboard, BarChart3, DollarSign, Bell, Settings, Zap } from "lucide-react";
import { cn } from "@/lib/utils";

const NAV_ITEMS = [
  { href: "/dashboard", label: "Overview", icon: LayoutDashboard },
  { href: "/dashboard/analytics", label: "Analytics", icon: BarChart3 },
  { href: "/dashboard/costs", label: "Costs", icon: DollarSign },
  { href: "/dashboard/alerts", label: "Alerts", icon: Bell },
  { href: "/dashboard/settings", label: "Settings", icon: Settings },
];

interface MobileNavProps {
  open: boolean;
  onClose: () => void;
}

export function MobileNav({ open, onClose }: MobileNavProps) {
  const pathname = usePathname();

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 lg:hidden">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/60 backdrop-blur-sm"
        onClick={onClose}
        aria-hidden
      />

      {/* Drawer */}
      <div className="absolute left-0 top-0 flex h-full w-72 flex-col bg-slate-900 shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-slate-700/50 px-5 py-5">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-violet-500 to-blue-600">
              <Zap className="h-5 w-5 text-white" />
            </div>
            <span className="text-sm font-bold text-slate-100">AI Usage Dashboard</span>
          </div>
          <button
            onClick={onClose}
            className="rounded-lg p-2 text-slate-400 hover:bg-slate-800 hover:text-slate-200"
            aria-label="Close navigation"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Nav */}
        <nav className="flex-1 px-3 py-4">
          <ul className="space-y-0.5">
            {NAV_ITEMS.map(({ href, label, icon: Icon }) => {
              const isActive =
                href === "/dashboard" ? pathname === "/dashboard" : pathname.startsWith(href);

              return (
                <li key={href}>
                  <Link
                    href={href}
                    onClick={onClose}
                    className={cn(
                      "flex items-center gap-3 rounded-xl px-3 py-3 text-sm font-medium transition-all",
                      isActive
                        ? "bg-violet-500/15 text-violet-300"
                        : "text-slate-400 hover:bg-slate-800 hover:text-slate-200"
                    )}
                  >
                    <Icon className={cn("h-4 w-4", isActive ? "text-violet-400" : "text-slate-500")} />
                    {label}
                  </Link>
                </li>
              );
            })}
          </ul>
        </nav>
      </div>
    </div>
  );
}
