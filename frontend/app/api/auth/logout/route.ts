/**
 * POST /api/auth/logout
 * Clears the ai_session httpOnly cookie.
 */
import { NextResponse } from "next/server";

export async function POST() {
  const response = NextResponse.json({ success: true });
  response.cookies.set("ai_session", "", {
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    sameSite: "strict",
    path: "/",
    maxAge: 0, // Expire immediately
  });
  return response;
}
