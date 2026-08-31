"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Layers, Lock, KeyRound, ArrowRight, CheckCircle2, AlertCircle, Loader2 } from "lucide-react";
import { useAuth } from "../../context/AuthContext";

export default function ResetPasswordPage() {
  const router = useRouter();
  const { updatePassword } = useAuth();

  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (password.length < 6) {
      setError("Password must be at least 6 characters long.");
      return;
    }
    if (password !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }

    setLoading(true);
    try {
      const { error: updateError } = await updatePassword(password);
      if (updateError) {
        setError(updateError.message || "Failed to update password.");
      } else {
        setSuccess(true);
        setTimeout(() => {
          router.push("/");
        }, 2000);
      }
    } catch (err: any) {
      setError(err?.message || "An unexpected error occurred.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="min-h-screen flex flex-col items-center justify-center p-4 sm:p-6 md:p-10 bg-gradient-to-b from-[#f8f9fb] via-[#ffffff] to-[#f4f5f8]">
      <div className="w-full max-w-[480px] bg-white border border-brand-outline-variant rounded-[32px] p-6 sm:p-10 shadow-elevation-md">
        <div className="text-center mb-8">
          <Link href="/" className="inline-flex items-center gap-2.5 mb-3 group">
            <div className="w-11 h-11 rounded-[14px] bg-brand-primary flex items-center justify-center shadow-md shadow-brand-primary/25">
              <Layers className="w-6 h-6 text-white" />
            </div>
            <div className="text-left">
              <span className="text-2xl font-black tracking-tight text-brand-secondary">LearnSync <span className="text-xs font-black px-2 py-0.5 rounded-full bg-brand-tertiary text-brand-secondary">AI</span></span>
            </div>
          </Link>
          <h1 className="text-2xl font-black text-brand-secondary">Set New Password</h1>
          <p className="text-sm font-medium text-brand-on-surface-variant mt-1.5">
            Enter your new secure password below.
          </p>
        </div>

        {error && (
          <div className="flex items-start gap-2.5 p-3.5 mb-5 rounded-[14px] bg-brand-error-container border border-brand-error/20 text-brand-on-error-container text-xs font-semibold">
            <AlertCircle className="w-4 h-4 text-brand-error shrink-0 mt-0.5" />
            <span>{error}</span>
          </div>
        )}

        {success ? (
          <div className="p-6 rounded-[20px] bg-emerald-50 border border-emerald-200 text-center">
            <CheckCircle2 className="w-10 h-10 text-emerald-600 mx-auto mb-3" />
            <h3 className="text-base font-bold text-emerald-900 mb-1">Password Updated Successfully</h3>
            <p className="text-xs text-emerald-700">Redirecting to your learning cockpit...</p>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-bold text-brand-secondary mb-1.5">
                New Password
              </label>
              <div className="relative">
                <Lock className="w-4 h-4 text-brand-outline absolute left-3.5 top-1/2 -translate-y-1/2" />
                <input
                  type="password"
                  required
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full pl-10 pr-4 py-2.5 bg-brand-surface rounded-[14px] border border-brand-outline-variant focus:border-brand-primary focus:ring-4 focus:ring-brand-primary/10 text-sm text-brand-secondary outline-none transition-all duration-150"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-bold text-brand-secondary mb-1.5">
                Confirm New Password
              </label>
              <div className="relative">
                <KeyRound className="w-4 h-4 text-brand-outline absolute left-3.5 top-1/2 -translate-y-1/2" />
                <input
                  type="password"
                  required
                  placeholder="••••••••"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  className="w-full pl-10 pr-4 py-2.5 bg-brand-surface rounded-[14px] border border-brand-outline-variant focus:border-brand-primary focus:ring-4 focus:ring-brand-primary/10 text-sm text-brand-secondary outline-none transition-all duration-150"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full mt-2 flex items-center justify-center gap-2 py-3 px-4 bg-brand-tertiary hover:bg-brand-tertiary-dim text-brand-secondary rounded-[14px] text-sm font-black transition-all duration-150 hover:scale-[1.01] active:scale-[0.99] shadow-md shadow-brand-tertiary/20 disabled:opacity-60"
            >
              {loading ? (
                <Loader2 className="w-4 h-4 animate-spin text-brand-secondary" />
              ) : (
                <>
                  <span>Save New Password</span>
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </form>
        )}
      </div>
    </main>
  );
}
