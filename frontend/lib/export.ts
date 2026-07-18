/**
 * CSV export utilities.
 * Converts API data shapes into downloadable CSV files.
 */

import type { UsageHistoryPoint, CostByModel, AlertItem } from "./types";

function escapeCsvCell(value: string | number | null | undefined): string {
  if (value === null || value === undefined) return "";
  const str = String(value);
  if (str.includes(",") || str.includes('"') || str.includes("\n")) {
    return `"${str.replace(/"/g, '""')}"`;
  }
  return str;
}

function buildCsv(headers: string[], rows: (string | number | null)[][]): string {
  const lines = [headers.map(escapeCsvCell).join(",")];
  for (const row of rows) {
    lines.push(row.map(escapeCsvCell).join(","));
  }
  return lines.join("\n");
}

export function exportUsageHistoryToCsv(data: UsageHistoryPoint[]): void {
  const headers = ["Period", "Provider", "Call Count", "Tokens In", "Tokens Out", "Total Tokens", "Cost (USD)"];
  const rows = data.map((d) => [
    d.period,
    d.provider_name,
    d.call_count,
    d.tokens_in,
    d.tokens_out,
    d.total_tokens,
    d.total_cost,
  ]);
  downloadCsv(buildCsv(headers, rows), `usage-history-${formatDateForFilename()}.csv`);
}

export function exportCostBreakdownToCsv(data: CostByModel[]): void {
  const headers = ["Provider", "Model", "Call Count", "Tokens In", "Tokens Out", "Cost (USD)"];
  const rows = data.map((d) => [
    d.provider_name,
    d.model,
    d.call_count,
    d.tokens_in,
    d.tokens_out,
    d.total_cost,
  ]);
  downloadCsv(buildCsv(headers, rows), `cost-breakdown-${formatDateForFilename()}.csv`);
}

export function exportAlertsToCsv(data: AlertItem[]): void {
  const headers = ["Provider", "Alert Type", "Threshold %", "Severity", "Message", "Sent At"];
  const rows = data.map((a) => [
    a.provider_name,
    a.alert_type.toUpperCase(),
    a.threshold_percent,
    a.severity,
    a.message,
    a.sent_at,
  ]);
  downloadCsv(buildCsv(headers, rows), `alerts-${formatDateForFilename()}.csv`);
}

function downloadCsv(content: string, filename: string): void {
  const blob = new Blob([content], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

function formatDateForFilename(): string {
  return new Date().toISOString().slice(0, 10);
}

export function triggerPdfExport(): void {
  window.print();
}
