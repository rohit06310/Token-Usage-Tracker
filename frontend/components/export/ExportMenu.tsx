"use client";

import { Download, FileText, Printer } from "lucide-react";
import { useState, useRef, useEffect } from "react";
import { triggerPdfExport } from "@/lib/export";
import { cn } from "@/lib/utils";

interface ExportMenuProps {
  csvUrl: string;  // e.g. /api/export/csv?type=usage&range=7d
  label?: string;
  className?: string;
}

export function ExportMenu({ csvUrl, label = "Export", className }: ExportMenuProps) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  // Close on outside click
  useEffect(() => {
    function handler(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  function handleCsvExport() {
    const a = document.createElement("a");
    a.href = csvUrl;
    a.click();
    setOpen(false);
  }

  function handlePdfExport() {
    setOpen(false);
    // Small delay to let the menu close before print dialog opens
    setTimeout(() => triggerPdfExport(), 100);
  }

  return (
    <div ref={ref} className={cn("relative", className)}>
      <button
        onClick={() => setOpen((v) => !v)}
        className="flex items-center gap-2 rounded-lg border border-slate-700/50 bg-slate-800/60 px-3 py-2 text-xs font-medium text-slate-300 transition hover:border-slate-600 hover:bg-slate-800 hover:text-slate-100"
        aria-expanded={open}
        aria-haspopup="true"
        id="export-menu-btn"
      >
        <Download className="h-3.5 w-3.5" />
        {label}
      </button>

      {open && (
        <div
          className="absolute right-0 z-30 mt-1 w-44 origin-top-right overflow-hidden rounded-xl border border-slate-700/50 bg-slate-800 shadow-xl shadow-black/40"
          role="menu"
          aria-labelledby="export-menu-btn"
        >
          <button
            onClick={handleCsvExport}
            className="flex w-full items-center gap-3 px-4 py-3 text-left text-sm text-slate-300 transition hover:bg-slate-700/50 hover:text-slate-100"
            role="menuitem"
          >
            <FileText className="h-4 w-4 text-emerald-400" />
            Export CSV
          </button>
          <button
            onClick={handlePdfExport}
            className="flex w-full items-center gap-3 border-t border-slate-700/50 px-4 py-3 text-left text-sm text-slate-300 transition hover:bg-slate-700/50 hover:text-slate-100"
            role="menuitem"
          >
            <Printer className="h-4 w-4 text-violet-400" />
            Print / PDF
          </button>
        </div>
      )}
    </div>
  );
}
