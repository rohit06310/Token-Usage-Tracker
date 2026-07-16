import { NextRequest, NextResponse } from "next/server";

const PROTECTED_PATHS = ["/dashboard"];
const LOGIN_PATH = "/login";

/**
 * Next.js 16 proxy (formerly "middleware").
 * Guards all /dashboard/* routes — redirects to /login if ai_session cookie is absent.
 */
export function proxy(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // Check if path is protected
  const isProtected = PROTECTED_PATHS.some((p) => pathname.startsWith(p));

  if (isProtected) {
    const sessionCookie = request.cookies.get("ai_session");
    if (!sessionCookie?.value) {
      const loginUrl = new URL(LOGIN_PATH, request.url);
      loginUrl.searchParams.set("from", pathname);
      return NextResponse.redirect(loginUrl);
    }
  }

  // Redirect root to dashboard or login
  if (pathname === "/") {
    const sessionCookie = request.cookies.get("ai_session");
    const destination = sessionCookie?.value ? "/dashboard" : LOGIN_PATH;
    return NextResponse.redirect(new URL(destination, request.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    /*
     * Match all request paths except Next.js internals and API route handlers
     * that manage their own auth (auth, proxy, export routes).
     */
    "/((?!_next/static|_next/image|favicon.ico|api/auth|api/proxy|api/export).*)",
  ],
};
