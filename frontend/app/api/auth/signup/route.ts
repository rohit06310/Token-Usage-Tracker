/**
 * POST /api/auth/signup
 *
 * Creates a new user account via the FastAPI backend's signup endpoint.
 * Automatically logs the user in after successful registration by forwarding
 * to the login route to obtain and set the session cookie.
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
    return NextResponse.json(
      { message: "Email and password are required" },
      { status: 400 }
    );
  }

  if (password.length < 8) {
    return NextResponse.json(
      { message: "Password must be at least 8 characters" },
      { status: 400 }
    );
  }

  // 1. Register via FastAPI
  try {
    const signupRes = await fetch(`${BACKEND_URL}/api/v1/auth/signup`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
      signal: AbortSignal.timeout(8000),
    });

    if (!signupRes.ok) {
      const err = await signupRes.json().catch(() => ({}));
      return NextResponse.json(
        { message: err?.detail ?? "Registration failed" },
        { status: signupRes.status }
      );
    }
  } catch (err) {
    console.error("[auth/signup] Backend unreachable:", err);
    return NextResponse.json(
      { message: "Backend unreachable. Please ensure the API server is running." },
      { status: 503 }
    );
  }

  // 2. Auto-login — obtain JWT and set the session cookie
  try {
    const formData = new URLSearchParams();
    formData.append("username", email);
    formData.append("password", password);

    const loginRes = await fetch(`${BACKEND_URL}/api/v1/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: formData,
      signal: AbortSignal.timeout(8000),
    });

    if (!loginRes.ok) {
      // Signup succeeded but auto-login failed — still 201, user can log in manually
      return NextResponse.json(
        { success: true, autoLoginFailed: true },
        { status: 201 }
      );
    }

    const data = await loginRes.json();
    const accessToken = data.access_token;

    const response = NextResponse.json({ success: true }, { status: 201 });
    response.cookies.set("ai_session", accessToken, {
      httpOnly: true,
      secure: process.env.NODE_ENV === "production",
      sameSite: "strict",
      path: "/",
      maxAge: 60 * 60 * 24, // 24 hours
    });

    return response;
  } catch (err) {
    console.error("[auth/signup] Auto-login failed after signup:", err);
    return NextResponse.json({ success: true, autoLoginFailed: true }, { status: 201 });
  }
}
