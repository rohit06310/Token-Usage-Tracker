"use client";

import { useState, useTransition, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { Zap, Eye, EyeOff, AlertCircle, Loader2, CheckCircle2 } from "lucide-react";
import { login } from "@/lib/api";

export default function LoginPage() {
  return (
    <Suspense fallback={<div className="flex min-h-screen items-center justify-center"><Loader2 className="h-8 w-8 animate-spin text-violet-500" /></div>}>
      <LoginForm />
    </Suspense>
  );
}

function LoginForm() {
  const router = useRouter();
  const params = useSearchParams();
  const from = params.get("from") ?? "/dashboard";

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isPending, startTransition] = useTransition();

  const justRegistered = params.get("registered") === "1";

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);

    startTransition(async () => {
      try {
        await login(email.trim(), password);
        router.push(from);
        router.refresh();
      } catch (err: unknown) {
        setError(err instanceof Error ? err.message : "Login failed");
      }
    });
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-mesh p-4" style={{ background: "var(--background)" }}>
      {/* Background grid */}
      <div className="absolute inset-0 bg-grid opacity-50" />

      {/* Glow effects */}
      <div className="pointer-events-none absolute inset-0 overflow-hidden">
        <div className="absolute -left-40 -top-40 h-80 w-80 rounded-full bg-violet-600/10 blur-3xl" />
        <div className="absolute -bottom-40 -right-40 h-80 w-80 rounded-full bg-blue-600/8 blur-3xl" />
      </div>

      <div className="relative w-full max-w-md">
        {/* Logo */}
        <div className="mb-8 flex flex-col items-center gap-3 text-center">
          <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-to-br from-violet-500 to-blue-600 shadow-2xl shadow-violet-500/30">
            <Zap className="h-8 w-8 text-white" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-slate-100">AI Usage Dashboard</h1>
            <p className="text-sm text-slate-400">Sign in to your account</p>
          </div>
        </div>

        {/* Card */}
        <div className="glass overflow-hidden rounded-2xl p-8 shadow-2xl shadow-black/40">
          <form onSubmit={handleSubmit} noValidate className="space-y-5">
            {/* Success banner after registration */}
            {justRegistered && !error && (
              <div className="flex items-center gap-2.5 rounded-xl border border-emerald-500/30 bg-emerald-500/10 px-4 py-3 text-sm text-emerald-300">
                <CheckCircle2 className="h-4 w-4 shrink-0" />
                Account created! Please sign in.
              </div>
            )}

            {/* Error banner */}
            {error && (
              <div className="flex items-center gap-2.5 rounded-xl border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-300">
                <AlertCircle className="h-4 w-4 shrink-0" />
                {error}
              </div>
            )}

            {/* Email input */}
            <div className="space-y-2">
              <label htmlFor="email" className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                Email Address
              </label>
              <input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@example.com"
                required
                autoComplete="email"
                autoFocus
                className="w-full rounded-xl border border-slate-700/50 bg-slate-800/60 px-4 py-3 text-sm text-slate-200 placeholder-slate-600 outline-none transition focus:border-violet-500/50 focus:ring-2 focus:ring-violet-500/10"
              />
            </div>

            {/* Password input */}
            <div className="space-y-2">
              <label htmlFor="password" className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                Password
              </label>
              <div className="relative">
                <input
                  id="password"
                  type={showPassword ? "text" : "password"}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Enter your password..."
                  required
                  autoComplete="current-password"
                  className="w-full rounded-xl border border-slate-700/50 bg-slate-800/60 px-4 py-3 pr-12 text-sm text-slate-200 placeholder-slate-600 outline-none transition focus:border-violet-500/50 focus:ring-2 focus:ring-violet-500/10"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword((v) => !v)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-500 transition hover:text-slate-300"
                  aria-label={showPassword ? "Hide password" : "Show password"}
                >
                  {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>
            </div>

            {/* Submit */}
            <button
              type="submit"
              disabled={!email.trim() || !password.trim() || isPending}
              id="login-submit-btn"
              className="relative flex w-full items-center justify-center gap-2 overflow-hidden rounded-xl bg-gradient-to-r from-violet-600 to-blue-600 px-4 py-3 text-sm font-semibold text-white shadow-lg shadow-violet-500/20 transition-all hover:shadow-violet-500/30 hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {isPending ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Verifying...
                </>
              ) : (
                "Sign In"
              )}
            </button>
          </form>

          <div className="mt-6 text-center">
            <p className="text-sm text-slate-500">
              Don&apos;t have an account?{" "}
              <Link
                href="/signup"
                className="font-medium text-violet-400 transition hover:text-violet-300"
              >
                Create one
              </Link>
            </p>
          </div>

          <div className="mt-4 rounded-xl border border-slate-700/30 bg-slate-800/30 p-4">
            <p className="text-xs text-slate-500 leading-relaxed">
              Your session token is validated server-side and stored in an{" "}
              <code className="text-violet-400">httpOnly</code> cookie.
              It is never accessible to browser JavaScript.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
