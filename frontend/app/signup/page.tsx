"use client";

import { useState, useTransition, Suspense } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import {
  Zap,
  Eye,
  EyeOff,
  AlertCircle,
  Loader2,
  CheckCircle2,
  User,
  Lock,
} from "lucide-react";
import { ApiError } from "@/lib/api";

export default function SignupPage() {
  return (
    <Suspense
      fallback={
        <div className="flex min-h-screen items-center justify-center">
          <Loader2 className="h-8 w-8 animate-spin text-violet-500" />
        </div>
      }
    >
      <SignupForm />
    </Suspense>
  );
}

function PasswordStrengthBar({ password }: { password: string }) {
  const checks = [
    password.length >= 8,
    /[A-Z]/.test(password),
    /[0-9]/.test(password),
    /[^A-Za-z0-9]/.test(password),
  ];
  const strength = checks.filter(Boolean).length;

  const colors = ["", "bg-red-500", "bg-orange-500", "bg-yellow-500", "bg-emerald-500"];
  const labels = ["", "Weak", "Fair", "Good", "Strong"];

  if (!password) return null;

  return (
    <div className="mt-2 space-y-1.5">
      <div className="flex gap-1">
        {[1, 2, 3, 4].map((i) => (
          <div
            key={i}
            className={`h-1 flex-1 rounded-full transition-all duration-300 ${
              i <= strength ? colors[strength] : "bg-slate-700"
            }`}
          />
        ))}
      </div>
      <p className={`text-[10px] font-medium ${strength >= 3 ? "text-emerald-400" : "text-slate-500"}`}>
        {labels[strength]}
      </p>
    </div>
  );
}

function SignupForm() {
  const router = useRouter();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isPending, startTransition] = useTransition();

  const passwordsMatch = confirmPassword === "" || password === confirmPassword;

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);

    if (password !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }
    if (password.length < 8) {
      setError("Password must be at least 8 characters.");
      return;
    }

    startTransition(async () => {
      try {
        const res = await fetch("/api/auth/signup", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ email: email.trim(), password }),
        });

        const data = await res.json().catch(() => ({}));

        if (!res.ok) {
          throw new ApiError(res.status, data?.message ?? "Registration failed");
        }

        if (data?.autoLoginFailed) {
          // Signup OK but auto-login failed — redirect to login
          router.push("/login?registered=1");
        } else {
          // Fully authenticated — go to dashboard
          router.push("/dashboard");
          router.refresh();
        }
      } catch (err: unknown) {
        setError(err instanceof Error ? err.message : "Registration failed");
      }
    });
  }

  return (
    <div
      className="flex min-h-screen items-center justify-center p-4"
      style={{ background: "var(--background)" }}
    >
      {/* Background grid */}
      <div className="absolute inset-0 bg-grid opacity-50" />

      {/* Glow effects */}
      <div className="pointer-events-none absolute inset-0 overflow-hidden">
        <div className="absolute -right-40 -top-40 h-80 w-80 rounded-full bg-violet-600/10 blur-3xl" />
        <div className="absolute -bottom-40 -left-40 h-80 w-80 rounded-full bg-blue-600/8 blur-3xl" />
      </div>

      <div className="relative w-full max-w-md">
        {/* Logo */}
        <div className="mb-8 flex flex-col items-center gap-3 text-center">
          <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-to-br from-violet-500 to-blue-600 shadow-2xl shadow-violet-500/30">
            <Zap className="h-8 w-8 text-white" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-slate-100">AI Usage Dashboard</h1>
            <p className="text-sm text-slate-400">Create your account</p>
          </div>
        </div>

        {/* Card */}
        <div className="glass overflow-hidden rounded-2xl p-8 shadow-2xl shadow-black/40">
          <form onSubmit={handleSubmit} noValidate className="space-y-5">
            {/* Error banner */}
            {error && (
              <div className="flex items-center gap-2.5 rounded-xl border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-300">
                <AlertCircle className="h-4 w-4 shrink-0" />
                {error}
              </div>
            )}

            {/* Email */}
            <div className="space-y-2">
              <label
                htmlFor="email"
                className="text-xs font-semibold uppercase tracking-wider text-slate-400"
              >
                Email Address
              </label>
              <div className="relative">
                <User className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-500" />
                <input
                  id="email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="you@example.com"
                  required
                  autoComplete="email"
                  autoFocus
                  className="w-full rounded-xl border border-slate-700/50 bg-slate-800/60 py-3 pl-10 pr-4 text-sm text-slate-200 placeholder-slate-600 outline-none transition focus:border-violet-500/50 focus:ring-2 focus:ring-violet-500/10"
                />
              </div>
            </div>

            {/* Password */}
            <div className="space-y-2">
              <label
                htmlFor="password"
                className="text-xs font-semibold uppercase tracking-wider text-slate-400"
              >
                Password
              </label>
              <div className="relative">
                <Lock className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-500" />
                <input
                  id="password"
                  type={showPassword ? "text" : "password"}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Min. 8 characters"
                  required
                  autoComplete="new-password"
                  className="w-full rounded-xl border border-slate-700/50 bg-slate-800/60 py-3 pl-10 pr-12 text-sm text-slate-200 placeholder-slate-600 outline-none transition focus:border-violet-500/50 focus:ring-2 focus:ring-violet-500/10"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword((v) => !v)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-500 transition hover:text-slate-300"
                  aria-label={showPassword ? "Hide password" : "Show password"}
                >
                  {showPassword ? (
                    <EyeOff className="h-4 w-4" />
                  ) : (
                    <Eye className="h-4 w-4" />
                  )}
                </button>
              </div>
              <PasswordStrengthBar password={password} />
            </div>

            {/* Confirm Password */}
            <div className="space-y-2">
              <label
                htmlFor="confirm-password"
                className="text-xs font-semibold uppercase tracking-wider text-slate-400"
              >
                Confirm Password
              </label>
              <div className="relative">
                <Lock className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-500" />
                <input
                  id="confirm-password"
                  type={showConfirm ? "text" : "password"}
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  placeholder="Re-enter your password"
                  required
                  autoComplete="new-password"
                  className={`w-full rounded-xl border bg-slate-800/60 py-3 pl-10 pr-12 text-sm text-slate-200 placeholder-slate-600 outline-none transition focus:ring-2 focus:ring-violet-500/10 ${
                    confirmPassword && !passwordsMatch
                      ? "border-red-500/50 focus:border-red-500/50"
                      : confirmPassword && passwordsMatch
                      ? "border-emerald-500/50 focus:border-emerald-500/50"
                      : "border-slate-700/50 focus:border-violet-500/50"
                  }`}
                />
                <button
                  type="button"
                  onClick={() => setShowConfirm((v) => !v)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-500 transition hover:text-slate-300"
                  aria-label={showConfirm ? "Hide password" : "Show password"}
                >
                  {showConfirm ? (
                    <EyeOff className="h-4 w-4" />
                  ) : (
                    <Eye className="h-4 w-4" />
                  )}
                </button>
                {confirmPassword && passwordsMatch && (
                  <CheckCircle2 className="pointer-events-none absolute right-9 top-1/2 h-4 w-4 -translate-y-1/2 text-emerald-400" />
                )}
              </div>
              {confirmPassword && !passwordsMatch && (
                <p className="text-[11px] text-red-400">Passwords do not match</p>
              )}
            </div>

            {/* Submit */}
            <button
              type="submit"
              id="signup-submit-btn"
              disabled={
                !email.trim() ||
                !password.trim() ||
                !confirmPassword.trim() ||
                !passwordsMatch ||
                isPending
              }
              className="relative flex w-full items-center justify-center gap-2 overflow-hidden rounded-xl bg-gradient-to-r from-violet-600 to-blue-600 px-4 py-3 text-sm font-semibold text-white shadow-lg shadow-violet-500/20 transition-all hover:shadow-violet-500/30 hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {isPending ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Creating account...
                </>
              ) : (
                "Create Account"
              )}
            </button>
          </form>

          {/* Sign in link */}
          <div className="mt-6 text-center">
            <p className="text-sm text-slate-500">
              Already have an account?{" "}
              <Link
                href="/login"
                className="font-medium text-violet-400 transition hover:text-violet-300"
              >
                Sign in
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
