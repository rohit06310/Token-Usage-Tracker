"use client";

import { CheckCircle2, AlertTriangle, XCircle } from "lucide-react";
import { cn } from "@/lib/utils";
import type { ConfidenceLevel } from "@/lib/types";

interface ConfidenceBadgeProps {
  level: ConfidenceLevel;
  showLabel?: boolean;
}

const CONFIG = {
  verified: {
    icon: CheckCircle2,
    label: "Verified",
    className: "bg-emerald-500/15 text-emerald-400 border-emerald-500/30",
  },
  self_logged_only: {
    icon: AlertTriangle,
    label: "Self-logged only",
    className: "bg-amber-500/15 text-amber-400 border-amber-500/30",
  },
  unreliable: {
    icon: XCircle,
    label: "Unreliable",
    className: "bg-red-500/15 text-red-400 border-red-500/30",
  },
} as const;

export function ConfidenceBadge({ level, showLabel = true }: ConfidenceBadgeProps) {
  const config = CONFIG[level] ?? CONFIG.self_logged_only;
  const Icon = config.icon;

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-xs font-medium",
        config.className
      )}
      title={`Confidence: ${config.label}`}
    >
      <Icon className="h-3 w-3" />
      {showLabel && config.label}
    </span>
  );
}
