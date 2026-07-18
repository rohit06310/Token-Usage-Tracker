import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

/** Merge Tailwind class names safely. */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export const getCurrencyConfig = () => {
  if (typeof window === "undefined") return { code: "USD", rate: 1 };
  const code = localStorage.getItem("preferred_currency") || "USD";
  const rates = { USD: 1, EUR: 0.92, GBP: 0.79, INR: 83.5 };
  return { code, rate: rates[code as keyof typeof rates] || 1 };
};

/** Format a cost string (Decimal as string from API) as currency. */
export function formatCost(value: string | number, decimals = 4): string {
  const num = typeof value === "string" ? parseFloat(value) : value;
  const { code, rate } = getCurrencyConfig();
  
  if (isNaN(num)) {
    return new Intl.NumberFormat("en-US", { style: "currency", currency: code }).format(0);
  }
  
  const converted = num * rate;
  
  if (converted === 0) {
    return new Intl.NumberFormat("en-US", { style: "currency", currency: code }).format(0);
  }
  
  if (converted < 0.01) {
    return new Intl.NumberFormat("en-US", { 
      style: "currency", 
      currency: code,
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals
    }).format(converted);
  }
  
  return new Intl.NumberFormat("en-US", { 
    style: "currency", 
    currency: code 
  }).format(converted);
}

/** Format token count with K/M suffix. */
export function formatTokens(value: number): string {
  if (value >= 1_000_000) return `${(value / 1_000_000).toFixed(1)}M`;
  if (value >= 1_000) return `${(value / 1_000).toFixed(1)}K`;
  return value.toString();
}

/** Format a number with comma separators. */
export function formatNumber(value: number): string {
  return new Intl.NumberFormat("en-US").format(value);
}

/** Format an ISO datetime string for display. */
export function formatDate(iso: string, includeTime = false): string {
  const d = new Date(iso);
  if (includeTime) {
    return d.toLocaleString("en-US", {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  }
  return d.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

/** Convert FilterState range to ISO date strings for API calls. */
export function resolveRange(
  range: string,
  dateFrom: string | null,
  dateTo: string | null
): { date_from?: string; date_to?: string } {
  if (range === "custom" && dateFrom && dateTo) {
    return { date_from: dateFrom, date_to: dateTo };
  }
  return {};
}

/** Build URLSearchParams from a filter object, omitting null/undefined. */
export function buildParams(
  params: Record<string, string | number | boolean | null | undefined>
): URLSearchParams {
  const p = new URLSearchParams();
  for (const [key, val] of Object.entries(params)) {
    if (val !== null && val !== undefined && val !== "") {
      p.set(key, String(val));
    }
  }
  return p;
}

/** Provider color palette — consistent across all charts. */
export const PROVIDER_COLORS: Record<string, string> = {
  openai: "#10b981",
  anthropic: "#8b5cf6",
  groq: "#f59e0b",
  gemini: "#3b82f6",
  default: "#6b7280",
};

export function getProviderColor(slug: string): string {
  return PROVIDER_COLORS[slug.toLowerCase()] ?? PROVIDER_COLORS.default;
}

/** Chart color palette for multi-series charts. */
export const CHART_COLORS = [
  "#10b981",
  "#8b5cf6",
  "#f59e0b",
  "#3b82f6",
  "#ef4444",
  "#ec4899",
  "#14b8a6",
  "#f97316",
];
