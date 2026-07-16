/**
 * GET /api/export/csv
 * Streams CSV data from the backend for the currently filtered view.
 * Accepts query params: type=usage|costs|alerts, plus filter params.
 */
import { NextRequest, NextResponse } from "next/server";
import { cookies } from "next/headers";

const BACKEND_URL = process.env.BACKEND_URL ?? "http://localhost:8000";

export async function GET(request: NextRequest) {
  const apiKey = (await cookies()).get("ai_session")?.value;
  if (!apiKey) {
    return NextResponse.json({ detail: "Not authenticated" }, { status: 401 });
  }

  const sp = request.nextUrl.searchParams;
  const type = sp.get("type") ?? "usage";

  // Determine which backend endpoint to call
  let endpoint: string;
  let filename: string;

  switch (type) {
    case "costs":
      endpoint = `/api/v1/usage/cost-breakdown?${sp.toString()}`;
      filename = "cost-breakdown.csv";
      break;
    case "alerts":
      endpoint = `/api/v1/alerts/recent?limit=200&${sp.toString()}`;
      filename = "alerts.csv";
      break;
    case "reconciliation":
      endpoint = `/api/v1/reconciliation/?limit=500&${sp.toString()}`;
      filename = "reconciliation.csv";
      break;
    default:
      endpoint = `/api/v1/usage/history?${sp.toString()}`;
      filename = "usage-history.csv";
  }

  const upstreamRes = await fetch(`${BACKEND_URL}${endpoint}`, {
    headers: { "X-API-Key": apiKey },
    signal: AbortSignal.timeout(15000),
  });

  if (!upstreamRes.ok) {
    return NextResponse.json({ detail: "Failed to fetch data" }, { status: upstreamRes.status });
  }

  const rawData = await upstreamRes.json();

  // Build CSV server-side
  let csv = "";

  if (type === "costs" && rawData.by_model) {
    csv = buildCostsCsv(rawData.by_model);
  } else if (type === "alerts" && rawData.items) {
    csv = buildAlertsCsv(rawData.items);
  } else if (type === "reconciliation" && rawData.items) {
    csv = buildReconciliationCsv(rawData.items);
  } else if (rawData.data) {
    csv = buildUsageCsv(rawData.data);
  } else {
    return NextResponse.json({ detail: "No data to export" }, { status: 204 });
  }

  return new NextResponse(csv, {
    headers: {
      "Content-Type": "text/csv",
      "Content-Disposition": `attachment; filename="${filename}"`,
    },
  });
}

function escapeCell(v: unknown): string {
  const s = String(v ?? "");
  return s.includes(",") || s.includes('"') ? `"${s.replace(/"/g, '""')}"` : s;
}

function row(cells: unknown[]): string {
  return cells.map(escapeCell).join(",");
}

function buildUsageCsv(data: Record<string, unknown>[]): string {
  const lines = [
    row(["Period", "Provider", "Call Count", "Tokens In", "Tokens Out", "Total Tokens", "Cost (USD)"]),
  ];
  for (const d of data) {
    lines.push(row([d.period, d.provider_name, d.call_count, d.tokens_in, d.tokens_out, d.total_tokens, d.total_cost]));
  }
  return lines.join("\n");
}

function buildCostsCsv(data: Record<string, unknown>[]): string {
  const lines = [row(["Provider", "Model", "Call Count", "Tokens In", "Tokens Out", "Cost (USD)"])];
  for (const d of data) {
    lines.push(row([d.provider_name, d.model, d.call_count, d.tokens_in, d.tokens_out, d.total_cost]));
  }
  return lines.join("\n");
}

function buildAlertsCsv(data: Record<string, unknown>[]): string {
  const lines = [row(["Provider", "Type", "Threshold %", "Severity", "Message", "Sent At"])];
  for (const a of data) {
    lines.push(row([a.provider_name, a.alert_type, a.threshold_percent, a.severity, a.message, a.sent_at]));
  }
  return lines.join("\n");
}

function buildReconciliationCsv(data: Record<string, unknown>[]): string {
  const lines = [row(["Date", "Provider", "Local Calls", "Provider Calls", "Local Cost", "Provider Cost", "Discrepancy %", "Notes"])];
  for (const r of data) {
    lines.push(row([
      r.created_at, 
      r.provider_name, 
      r.local_calls, 
      r.provider_calls, 
      r.local_cost, 
      r.provider_cost, 
      r.discrepancy_percent, 
      r.notes
    ]));
  }
  return lines.join("\n");
}
