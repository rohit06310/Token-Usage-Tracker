/**
 * POST /api/auth/login
 *
 * Validates the provided API key against the FastAPI backend (health check),
 * then sets an httpOnly session cookie so the raw key is never exposed to
 * browser JavaScript.
 */
import { NextRequest, NextResponse } from "next/server";

const BACKEND_URL = process.env.BACKEND_URL ?? "http://localhost:8000";

export async function POST(request: NextRequest) {
  let body: { email?: string; password?: string };
  try {
    body = await request.json();
  } catch {
    return NextResponse.json({ message: "Invalid request body" }, { status: 400 });
  }

  const email = body?.email?.trim();
  const password = body?.password;
  
  if (!email || !password) {
    return NextResponse.json({ message: "Email and password are required" }, { status: 400 });
  }

  // Authenticate against the FastAPI backend
  try {
    const formData = new URLSearchParams();
    formData.append("username", email);
    formData.append("password", password);

    const verifyRes = await fetch(`${BACKEND_URL}/api/v1/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: formData,
      signal: AbortSignal.timeout(8000),
    });

    if (!verifyRes.ok) {
      return NextResponse.json(
        { message: "Invalid email or password." },
        { status: 401 }
      );
    }

    const data = await verifyRes.json();
    const accessToken = data.access_token;

    // Set the httpOnly session cookie containing the JWT
    const response = NextResponse.json({ success: true });
    response.cookies.set("ai_session", accessToken, {
      httpOnly: true,
      secure: process.env.NODE_ENV === "production",
      sameSite: "strict",
      path: "/",
      maxAge: 60 * 60 * 24, // 24 hours
    });

    return response;

  } catch (err) {
    console.error("[auth/login] Backend unreachable:", err);
    return NextResponse.json(
      { message: "Backend unreachable. Please ensure the API server is running." },
      { status: 503 }
    );
  }
}
