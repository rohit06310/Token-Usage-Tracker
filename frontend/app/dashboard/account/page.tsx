"use client";

import { useState, useEffect } from "react";
import { User, Lock, Save, Globe } from "lucide-react";
import { api } from "@/lib/api";

export default function AccountPage() {
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [preferredCurrency, setPreferredCurrency] = useState("USD");

  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState("");
  const [successMsg, setSuccessMsg] = useState("");

  useEffect(() => {
    // Fetch current user settings
    api.get("/auth/me").then((res) => {
      setPreferredCurrency((res as any).preferred_currency || "USD");
    }).catch(console.error);
  }, []);

  const handleChangePassword = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg("");
    setSuccessMsg("");

    if (newPassword !== confirmPassword) {
      setErrorMsg("New passwords do not match.");
      return;
    }

    if (newPassword.length < 8) {
      setErrorMsg("New password must be at least 8 characters long.");
      return;
    }

    setLoading(true);
    try {
      await api.post("/auth/change-password", {
        current_password: currentPassword,
        new_password: newPassword,
      });
      setSuccessMsg("Password updated successfully.");
      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to update password.");
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateCurrency = async (currency: string) => {
    setPreferredCurrency(currency);
    if (typeof window !== "undefined") {
      localStorage.setItem("preferred_currency", currency);
    }
    try {
      await api.patch("/auth/me", { preferred_currency: currency });
      window.location.reload();
    } catch (err: any) {
      console.error("Failed to update currency", err);
    }
  };

  return (
    <div className="space-y-8 max-w-2xl">
      {/* Header */}
      <div className="flex items-center gap-3 border-b border-slate-700/50 pb-5">
        <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-violet-500/10 border border-violet-500/20">
          <User className="h-5 w-5 text-violet-400" />
        </div>
        <div>
          <h2 className="text-xl font-bold text-slate-100 tracking-tight">Account Settings</h2>
          <p className="text-sm text-slate-400">Manage your preferences, password and security.</p>
        </div>
      </div>

      {/* Preferences Section */}
      <section className="space-y-6">
        <div className="flex items-center gap-2 text-slate-200 font-semibold text-lg">
          <Globe className="h-5 w-5 text-emerald-400" />
          Preferences
        </div>
        <div className="rounded-2xl border border-slate-700/50 bg-slate-800/40 p-6 space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-400 mb-1">Preferred Currency</label>
            <p className="text-xs text-slate-500 mb-3">Changes will refresh the page to apply new display currency.</p>
            <select
              value={preferredCurrency}
              onChange={(e) => handleUpdateCurrency(e.target.value)}
              className="w-full sm:w-1/2 bg-slate-900 border border-slate-700 rounded-lg px-4 py-2 text-sm text-slate-200 focus:outline-none focus:border-violet-500 focus:ring-1 focus:ring-violet-500"
            >
              <option value="USD">USD ($)</option>
              <option value="EUR">EUR (€)</option>
              <option value="GBP">GBP (£)</option>
              <option value="INR">INR (₹)</option>
            </select>
          </div>
        </div>
      </section>

      {/* Password Section */}
      <section className="space-y-6">
        <div className="flex items-center gap-2 text-slate-200 font-semibold text-lg">
          <Lock className="h-5 w-5 text-blue-400" />
          Change Password
        </div>

        <form onSubmit={handleChangePassword} className="rounded-2xl border border-slate-700/50 bg-slate-800/40 p-6 space-y-4">
          {errorMsg && (
            <div className="rounded-xl border border-red-500/50 bg-red-500/10 p-4 text-sm font-medium text-red-400">
              {errorMsg}
            </div>
          )}
          {successMsg && (
            <div className="rounded-xl border border-emerald-500/50 bg-emerald-500/10 p-4 text-sm font-medium text-emerald-400">
              {successMsg}
            </div>
          )}

          <div>
            <label className="block text-sm font-medium text-slate-400 mb-1">Current Password</label>
            <input 
              type="password" 
              required 
              value={currentPassword} 
              onChange={(e) => setCurrentPassword(e.target.value)} 
              className="w-full bg-slate-900 border border-slate-700 rounded-lg px-4 py-2 text-sm text-slate-200 focus:outline-none focus:border-violet-500 focus:ring-1 focus:ring-violet-500" 
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-400 mb-1">New Password</label>
            <input 
              type="password" 
              required 
              value={newPassword} 
              onChange={(e) => setNewPassword(e.target.value)} 
              className="w-full bg-slate-900 border border-slate-700 rounded-lg px-4 py-2 text-sm text-slate-200 focus:outline-none focus:border-violet-500 focus:ring-1 focus:ring-violet-500" 
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-400 mb-1">Confirm New Password</label>
            <input 
              type="password" 
              required 
              value={confirmPassword} 
              onChange={(e) => setConfirmPassword(e.target.value)} 
              className="w-full bg-slate-900 border border-slate-700 rounded-lg px-4 py-2 text-sm text-slate-200 focus:outline-none focus:border-violet-500 focus:ring-1 focus:ring-violet-500" 
            />
          </div>

          <div className="pt-4 border-t border-slate-700/50">
            <button 
              disabled={loading} 
              type="submit" 
              className="flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-500 text-white font-medium rounded-lg px-6 py-2 text-sm transition-colors disabled:opacity-50"
            >
              <Save className="h-4 w-4" /> 
              {loading ? "Updating..." : "Update Password"}
            </button>
          </div>
        </form>
      </section>
    </div>
  );
}
