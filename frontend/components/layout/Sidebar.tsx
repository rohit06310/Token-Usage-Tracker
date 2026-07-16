"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  BarChart3,
  DollarSign,
  Bell,
  Settings,
  Zap,
  LogOut,
  User,
  Terminal,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { logout } from "@/lib/api";
import { useRouter } from "next/navigation";

const NAV_ITEMS = [
  { href: "/dashboard", label: "Overview", icon: LayoutDashboard },
  { href: "/dashboard/analytics", label: "Analytics", icon: BarChart3 },
  { href: "/dashboard/reconciliation", label: "Reconciliation", icon: BarChart3 }, // Reusing BarChart3 for now, or use another imported icon
  { href: "/dashboard/costs", label: "Costs", icon: DollarSign },
  { href: "/dashboard/limits", label: "Rate Limits", icon: Zap },
  { href: "/dashboard/alerts", label: "Alerts", icon: Bell },
  { href: "/dashboard/playground", label: "Playground", icon: Terminal },
  { href: "/dashboard/settings", label: "API Settings", icon: Settings },
  { href: "/dashboard/account", label: "Account", icon: User },
];

export function Sidebar() {
  const pathname = usePathname();
  const router = useRouter();

  async function handleLogout() {
    await logout();
    router.push("/login");
  }

  return (
    <aside className="flex h-screen w-64 flex-col border-r border-slate-700/50 bg-slate-900/95 backdrop-blur-xl print:hidden">
      {/* Logo */}
      <div className="flex items-center gap-3 border-b border-slate-700/50 px-5 py-5">
        <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-violet-500 to-blue-600 shadow-lg shadow-violet-500/20">
          <Zap className="h-5 w-5 text-white" />
        </div>
        <div>
          <p className="text-sm font-bold text-slate-100">AI Usage</p>
          <p className="text-[10px] text-slate-500">Dashboard v0.2</p>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto px-3 py-4">
        <p className="mb-2 px-3 text-[10px] font-semibold uppercase tracking-widest text-slate-600">
          Navigation
        </p>
        <ul className="space-y-0.5">
          {NAV_ITEMS.map(({ href, label, icon: Icon }) => {
            const isActive =
              href === "/dashboard" ? pathname === "/dashboard" : pathname.startsWith(href);

            return (
              <li key={href}>
                <Link
                  href={href}
                  className={cn(
                    "flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-all duration-150",
                    isActive
                      ? "bg-violet-500/15 text-violet-300 shadow-sm"
                      : "text-slate-400 hover:bg-slate-800/60 hover:text-slate-200"
                  )}
                >
                  <Icon
                    className={cn(
                      "h-4 w-4 shrink-0 transition-colors",
                      isActive ? "text-violet-400" : "text-slate-500"
                    )}
                  />
                  {label}
                  {href === "/dashboard/alerts" && (
                    <span className="ml-auto flex h-5 w-5 items-center justify-center rounded-full bg-red-500/20 text-[10px] font-bold text-red-400">
                      !
                    </span>
                  )}
                </Link>
              </li>
            );
          })}
        </ul>
      </nav>

      {/* Footer */}
      <div className="border-t border-slate-700/50 px-3 py-4">
        <button
          onClick={handleLogout}
          className="flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium text-slate-400 transition hover:bg-red-500/10 hover:text-red-400"
        >
          <LogOut className="h-4 w-4" />
          Sign Out
        </button>
      </div>
    </aside>
  );
}
