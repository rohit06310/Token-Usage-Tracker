"use client";

import { cn } from "@/lib/utils";

interface LoadingSpinnerProps {
  size?: "sm" | "md" | "lg";
  className?: string;
  label?: string;
}

const sizeMap = {
  sm: "h-4 w-4 border-2",
  md: "h-8 w-8 border-2",
  lg: "h-12 w-12 border-[3px]",
};

export function LoadingSpinner({ size = "md", className, label }: LoadingSpinnerProps) {
  return (
    <div className={cn("flex flex-col items-center justify-center gap-3", className)}>
      <div
        className={cn(
          "animate-spin rounded-full border-slate-600 border-t-violet-500",
          sizeMap[size]
        )}
        role="status"
        aria-label={label ?? "Loading"}
      />
      {label && <p className="text-sm text-slate-400">{label}</p>}
    </div>
  );
}

export function PageLoader({ label = "Loading..." }: { label?: string }) {
  return (
    <div className="flex min-h-[300px] items-center justify-center">
      <LoadingSpinner size="lg" label={label} />
    </div>
  );
}
