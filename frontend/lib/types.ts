// All shared TypeScript interfaces for the dashboard frontend.
// Keep in sync with FastAPI response shapes.

// ─── Provider & Confidence ──────────────────────────────────────────────────

export type ConfidenceLevel = "verified" | "self_logged_only" | "unreliable";

export interface ProviderSummary {
  provider_id: string;
  provider_name: string;
  provider_slug: string;
  confidence_level: ConfidenceLevel;
  call_count_today: number;
  total_tokens_today: number;
  total_cost_today: string; // Decimal as string
  total_cost_30d: string;
  remaining_quota: {
    tpm?: QuotaDetail;
    rpm?: QuotaDetail;
    rpd?: QuotaDetail;
  };
}

export interface QuotaDetail {
  limit: number;
  used: number;
  remaining: number;
  percent_used: number;
}

export interface DashboardSummaryResponse {
  providers: ProviderSummary[];
  generated_at: string;
}

// ─── Usage History ───────────────────────────────────────────────────────────

export interface UsageHistoryPoint {
  period: string;
  provider_id: string;
  provider_slug: string;
  provider_name: string;
  call_count: number;
  tokens_in: number;
  tokens_out: number;
  total_tokens: number;
  total_cost: string;
}

export interface UsageHistoryResponse {
  data: UsageHistoryPoint[];
  range: string;
  group_by: string;
  start: string;
  end: string;
}

// ─── Cost Breakdown ──────────────────────────────────────────────────────────

export interface CostByProvider {
  provider_id: string;
  provider_name: string;
  provider_slug: string;
  call_count: number;
  total_cost: string;
  total_tokens: number;
}

export interface CostByModel {
  provider_id: string;
  provider_name: string;
  provider_slug: string;
  model: string;
  call_count: number;
  tokens_in: number;
  tokens_out: number;
  total_cost: string;
}

export interface CostBreakdownResponse {
  by_provider: CostByProvider[];
  by_model: CostByModel[];
}

// ─── Alerts ──────────────────────────────────────────────────────────────────

export type AlertSeverity = "critical" | "warning" | "info";

export interface AlertItem {
  id: string;
  provider_id: string;
  provider_name: string;
  provider_slug: string;
  alert_type: string; // "tpm" | "rpm" | "rpd"
  threshold_percent: string;
  window_start: string;
  sent_at: string;
  severity: AlertSeverity;
  message: string;
}

export interface AlertsResponse {
  items: AlertItem[];
  total: number;
  limit: number;
  offset: number;
}

// ─── Providers ───────────────────────────────────────────────────────────────

export interface Provider {
  id: string;
  name: string;
  slug: string;
  base_url: string | null;
  notes: string | null;
  confidence_level: ConfidenceLevel;
  created_at: string;
  updated_at: string;
}

// ─── Filters ─────────────────────────────────────────────────────────────────

export interface TagItem {
  tag: string;
  call_count: number;
}

export interface ModelItem {
  model: string;
  provider_id: string;
  provider_slug: string;
  call_count: number;
}

// ─── Filter State ────────────────────────────────────────────────────────────

export interface FilterState {
  range: "today" | "7d" | "30d" | "custom";
  dateFrom: string | null;
  dateTo: string | null;
  providerId: string | null;
  model: string | null;
  projectTag: string | null;
}
