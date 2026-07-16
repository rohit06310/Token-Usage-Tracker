/**
 * /api/proxy/[...path] — BFF Proxy Route Handler
 *
 * Forwards ALL requests to FastAPI, injecting the X-API-Key from the
 * httpOnly ai_session cookie. This means the API key is NEVER accessible
 * to browser JavaScript — all authenticated requests go server-side.
 *
 * Usage: GET /api/proxy/dashboard/summary  →  GET /api/v1/dashboard/summary
 */
import { NextRequest, NextResponse } from "next/server";
import { cookies } from "next/headers";

const BACKEND_URL = process.env.BACKEND_URL ?? "http://localhost:8000";

async function proxyRequest(
  request: NextRequest,
  { params }: { params: Promise<{ path: string[] }> }
) {
  const { path } = await params;
  const token = (await cookies()).get("ai_session")?.value;

  if (!token) {
    return NextResponse.json(
      { detail: "Not authenticated. Please log in." },
      { status: 401 }
    );
  }

  // Reconstruct the upstream URL, forwarding any query params
  const upstreamPath = path.join("/");
  const searchParams = request.nextUrl.searchParams.toString();
  const upstreamUrl = `${BACKEND_URL}/api/v1/${upstreamPath}${searchParams ? `?${searchParams}` : ""}`;

  const headers: Record<string, string> = {
    "Authorization": `Bearer ${token}`,
    "Content-Type": "application/json",
  };

  let body: BodyInit | undefined;
  if (request.method !== "GET" && request.method !== "HEAD") {
    try {
      const text = await request.text();
      if (text) body = text;
    } catch {}
  }

  try {
    const upstream = await fetch(upstreamUrl, {
      method: request.method,
      headers,
      body,
      signal: AbortSignal.timeout(15000),
    });

    const data = await upstream.text();

    return new NextResponse(data, {
      status: upstream.status,
      headers: {
        "Content-Type": upstream.headers.get("Content-Type") ?? "application/json",
      },
    });
  } catch (err) {
    console.error("[proxy] Backend error:", err);
    return NextResponse.json(
      { detail: "Backend service is unreachable. Please try again later." },
      { status: 503 }
    );
  }
}

export const GET = proxyRequest;
export const POST = proxyRequest;
export const PATCH = proxyRequest;
export const DELETE = proxyRequest;
