/**
 * POST /api/auth/login
 *
 * Authenticates the user against the FastAPI backend.
 * If successful, stores the JWT in an httpOnly cookie.
 */

import { NextRequest, NextResponse } from "next/server";

const BACKEND_URL = process.env.BACKEND_URL;

if (!BACKEND_URL) {
  throw new Error(
    "BACKEND_URL environment variable is not configured."
  );
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();

    const email = body.email?.trim();
    const password = body.password;

    if (!email || !password) {
      return NextResponse.json(
        {
          message: "Email and password are required.",
        },
        {
          status: 400,
        }
      );
    }

    const formData = new URLSearchParams();
    formData.append("username", email);
    formData.append("password", password);

    const backendResponse = await fetch(
      `${BACKEND_URL}/api/v1/auth/login`,
      {
        method: "POST",
        headers: {
          "Content-Type":
            "application/x-www-form-urlencoded",
        },
        body: formData,
        cache: "no-store",
      }
    );

    if (!backendResponse.ok) {
      const error = await backendResponse.text();

      console.error(
        "Backend authentication failed:",
        error
      );

      return NextResponse.json(
        {
          message: "Invalid email or password.",
        },
        {
          status: backendResponse.status,
        }
      );
    }

    const data = await backendResponse.json();

    const response = NextResponse.json({
      success: true,
    });

    response.cookies.set(
      "ai_session",
      data.access_token,
      {
        httpOnly: true,
        secure: process.env.NODE_ENV === "production",
        sameSite: "strict",
        path: "/",
        maxAge: 60 * 60 * 24,
      }
    );

    return response;
  } catch (error) {
    console.error("Login Route Error:", error);

    return NextResponse.json(
      {
        message: "Backend unreachable.",
      },
      {
        status: 503,
      }
    );
  }
}