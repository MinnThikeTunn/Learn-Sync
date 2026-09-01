"use client";

import React, { useState, useEffect, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { 
  Layers, 
  Sparkles, 
  Mail, 
  Lock, 
  User, 
  ArrowRight, 
  CheckCircle2, 
  AlertCircle, 
  Loader2,
  BrainCircuit,
  KeyRound
} from "lucide-react";
import { useAuth } from "../../context/AuthContext";
import { getAuthStageDetails, AuthStage } from "../../lib/authFeedback";

type AuthMode = "signin" | "signup" | "forgot";

function LoginForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { user, signInWithPassword, signUpWithPassword, resetPassword, isLoading: isAuthLoading } = useAuth();

  const [mode, setMode] = useState<AuthMode>("signin");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [stage, setStage] = useState<AuthStage>("idle");
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const redirectTo = searchParams?.get("redirectTo") || "/";

  // Redirect if already logged in
  useEffect(() => {
    if (user && !isAuthLoading) {
      router.push(redirectTo);
    }
  }, [user, isAuthLoading, router, redirectTo]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccessMessage(null);
    setLoading(true);
    setStage("validating");

    try {
      if (mode === "signin") {
        if (!email || !password) {
          setError("Please enter both email and password.");
          setLoading(false);
          setStage("error");
          return;
        }
        setStage("processing");
        const { error: signInError } = await signInWithPassword(email, password);
        if (signInError) {
          setError(signInError.message || "Failed to sign in. Please check your credentials.");
          setStage("error");
        } else {
          setStage("redirecting");
          setSuccessMessage("Credentials verified! Redirecting to your learning cockpit...");
          setTimeout(() => {
            router.push(redirectTo);
          }, 800);
        }
      } else if (mode === "signup") {
        if (!email || !password) {
          setError("Please provide an email and password.");
          setLoading(false);
          setStage("error");
          return;
        }
        if (password.length < 6) {
          setError("Password must be at least 6 characters long.");
          setLoading(false);
          setStage("error");
          return;
        }
        if (password !== confirmPassword) {
          setError("Passwords do not match.");
          setLoading(false);
          setStage("error");
          return;
        }

        setStage("processing");
        const { data: signUpData, error: signUpError } = await signUpWithPassword(email, password, fullName);
        if (signUpError) {
          setError(signUpError.message || "Registration failed. Please try again.");
          setStage("error");
        } else if (signUpData?.session) {
          setStage("redirecting");
          setSuccessMessage("Account created! Directing you to your learner onboarding...");
          setTimeout(() => {
            router.push(redirectTo);
          }, 800);
        } else {
          setStage("email_sent");
          setSuccessMessage("Account registered! Check your email or use the Quick Demo session below to test onboarding immediately.");
        }
      } else if (mode === "forgot") {
        if (!email) {
          setError("Please enter your registered email address.");
          setLoading(false);
          setStage("error");
          return;
        }
        setStage("processing");
        const { error: resetError } = await resetPassword(email);
        if (resetError) {
          setError(resetError.message || "Unable to send recovery email.");
          setStage("error");
        } else {
          setStage("email_sent");
          setSuccessMessage("Password reset link dispatched! Please check your email inbox.");
        }
      }
    } catch (err: any) {
      setError(err?.message || "An unexpected error occurred.");
      setStage("error");
    } finally {
      setLoading(false);
    }
  };


  const stageDetails = getAuthStageDetails(mode, stage, { email, errorMsg: error || undefined });

  return (
    <main className="min-h-screen flex flex-col items-center justify-center p-4 sm:p-6 md:p-10 bg-gradient-to-b from-[#f8f9fb] via-[#ffffff] to-[#f4f5f8]">
      {/* Background Decorative Ambient Blobs */}
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[350px] bg-gradient-to-tr from-brand-primary/10 to-brand-tertiary/20 blur-[100px] rounded-full pointer-events-none -z-10" />

      {/* Main Container Card (Perplexity-aesthetic rounded-[32px]) */}
      <div className="w-full max-w-[480px] bg-white border border-brand-outline-variant rounded-[32px] p-6 sm:p-10 shadow-elevation-md transition-all duration-200">
        
        {/* Brand Header */}
        <div className="text-center mb-8">
          <Link href="/" className="inline-flex items-center gap-2.5 mb-3 group">
            <div className="w-11 h-11 rounded-[14px] bg-brand-primary flex items-center justify-center shadow-md shadow-brand-primary/25 group-hover:scale-105 transition-transform duration-200">
              <Layers className="w-6 h-6 text-white" />
            </div>
            <div className="text-left">
              <div className="flex items-center gap-1.5">
                <span className="text-2xl font-black tracking-tight text-brand-secondary">LearnSync</span>
                <span className="text-xs font-black px-2 py-0.5 rounded-full bg-brand-tertiary text-brand-secondary border border-brand-tertiary-dim">AI</span>
              </div>
            </div>
          </Link>

          <h1 className="text-2xl sm:text-3xl font-black tracking-tight text-brand-secondary">
            {mode === "signin" && "Welcome back"}
            {mode === "signup" && "Start your learning journey"}
            {mode === "forgot" && "Reset your password"}
          </h1>
          <p className="text-sm font-medium text-brand-on-surface-variant mt-1.5">
            {mode === "signin" && "Sign in to access your adaptive workload co-pilot."}
            {mode === "signup" && "Join LearnSync AI to sync curriculum with cognitive mastery."}
            {mode === "forgot" && "Enter your email to receive recovery instructions."}
          </p>
        </div>

        {/* Tab Switcher (Sign In vs Create Account) */}
        {mode !== "forgot" && (
          <div className="flex p-1 bg-brand-surface-dim border border-brand-outline-variant rounded-full mb-6">
            <button
              type="button"
              onClick={() => {
                setMode("signin");
                setStage("idle");
                setError(null);
                setSuccessMessage(null);
              }}
              className={`flex-1 py-2 text-sm font-bold rounded-full transition-all duration-150 ${
                mode === "signin"
                  ? "bg-brand-secondary text-white shadow-sm"
                  : "text-brand-on-surface-variant hover:text-brand-secondary"
              }`}
            >
              Sign In
            </button>
            <button
              type="button"
              onClick={() => {
                setMode("signup");
                setStage("idle");
                setError(null);
                setSuccessMessage(null);
              }}
              className={`flex-1 py-2 text-sm font-bold rounded-full transition-all duration-150 ${
                mode === "signup"
                  ? "bg-brand-secondary text-white shadow-sm"
                  : "text-brand-on-surface-variant hover:text-brand-secondary"
              }`}
            >
              Create Account
            </button>
          </div>
        )}

        {/* Multi-Stage Active Progress Indicator */}
        {stage !== "idle" && stage !== "error" && stageDetails.title && (
          <div className="flex items-center gap-3 p-3.5 mb-5 rounded-[16px] bg-brand-surface-dim border border-brand-outline-variant text-brand-secondary animate-in fade-in duration-200">
            {stageDetails.isSpinning ? (
              <Loader2 className="w-4 h-4 text-brand-primary animate-spin shrink-0" />
            ) : (
              <Sparkles className="w-4 h-4 text-brand-tertiary-dim shrink-0" />
            )}
            <div className="flex-1 text-xs">
              <div className="flex items-center justify-between">
                <span className="font-bold text-brand-secondary">{stageDetails.title}</span>
                <span className="text-[10px] font-black uppercase tracking-wider px-2 py-0.5 rounded-full bg-brand-primary/10 text-brand-primary">
                  {stageDetails.badge}
                </span>
              </div>
              <p className="text-brand-on-surface-variant text-[11px] mt-0.5">{stageDetails.description}</p>
            </div>
          </div>
        )}

        {/* Perplexity-Aesthetic Inbox Verification Alert Card */}
        {stageDetails.isInboxNotice && (
          <div className="p-5 mb-6 rounded-[24px] bg-gradient-to-b from-amber-50/80 to-amber-100/40 border border-amber-200/80 text-amber-950 shadow-sm animate-in fade-in duration-200">
            <div className="flex items-start gap-3">
              <div className="w-9 h-9 rounded-2xl bg-amber-500/10 flex items-center justify-center shrink-0 border border-amber-400/20">
                <Mail className="w-5 h-5 text-amber-600" />
              </div>
              <div className="flex-1">
                <h3 className="text-sm font-black text-amber-900 tracking-tight">
                  Action Required: Check Your Inbox
                </h3>
                <p className="text-xs text-amber-800/90 mt-1 leading-relaxed">
                  We sent an email to <span className="font-bold text-amber-950 underline underline-offset-2">{email || "your address"}</span>. Please check your inbox and follow the verification instructions.
                </p>
                <div className="mt-3 pt-3 border-t border-amber-200/60 space-y-1.5">
                  {stageDetails.inboxTips.map((tip, idx) => (
                    <div key={idx} className="flex items-center gap-2 text-[11px] font-medium text-amber-800">
                      <CheckCircle2 className="w-3.5 h-3.5 text-amber-600 shrink-0" />
                      <span>{tip}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}



        {/* Auth Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          {mode === "signup" && (
            <div>
              <label className="block text-xs font-bold text-brand-secondary mb-1.5">
                Full Name
              </label>
              <div className="relative">
                <User className="w-4 h-4 text-brand-outline absolute left-3.5 top-1/2 -translate-y-1/2" />
                <input
                  type="text"
                  placeholder="e.g. Alex Morgan"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  className="w-full pl-10 pr-4 py-2.5 bg-brand-surface rounded-[14px] border border-brand-outline-variant focus:border-brand-primary focus:ring-4 focus:ring-brand-primary/10 text-sm text-brand-secondary outline-none transition-all duration-150 placeholder:text-brand-outline"
                />
              </div>
            </div>
          )}

          <div>
            <label className="block text-xs font-bold text-brand-secondary mb-1.5">
              Email Address
            </label>
            <div className="relative">
              <Mail className="w-4 h-4 text-brand-outline absolute left-3.5 top-1/2 -translate-y-1/2" />
              <input
                type="email"
                required
                placeholder="student@university.edu"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full pl-10 pr-4 py-2.5 bg-brand-surface rounded-[14px] border border-brand-outline-variant focus:border-brand-primary focus:ring-4 focus:ring-brand-primary/10 text-sm text-brand-secondary outline-none transition-all duration-150 placeholder:text-brand-outline"
              />
            </div>
          </div>

          {mode !== "forgot" && (
            <div>
              <div className="flex items-center justify-between mb-1.5">
                <label className="block text-xs font-bold text-brand-secondary">
                  Password
                </label>
                {mode === "signin" && (
                  <button
                    type="button"
                    onClick={() => {
                      setMode("forgot");
                      setError(null);
                      setSuccessMessage(null);
                    }}
                    className="text-xs font-bold text-brand-primary hover:underline"
                  >
                    Forgot password?
                  </button>
                )}
              </div>
              <div className="relative">
                <Lock className="w-4 h-4 text-brand-outline absolute left-3.5 top-1/2 -translate-y-1/2" />
                <input
                  type="password"
                  required
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full pl-10 pr-4 py-2.5 bg-brand-surface rounded-[14px] border border-brand-outline-variant focus:border-brand-primary focus:ring-4 focus:ring-brand-primary/10 text-sm text-brand-secondary outline-none transition-all duration-150 placeholder:text-brand-outline"
                />
              </div>
            </div>
          )}

          {mode === "signup" && (
            <div>
              <label className="block text-xs font-bold text-brand-secondary mb-1.5">
                Confirm Password
              </label>
              <div className="relative">
                <KeyRound className="w-4 h-4 text-brand-outline absolute left-3.5 top-1/2 -translate-y-1/2" />
                <input
                  type="password"
                  required
                  placeholder="••••••••"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  className="w-full pl-10 pr-4 py-2.5 bg-brand-surface rounded-[14px] border border-brand-outline-variant focus:border-brand-primary focus:ring-4 focus:ring-brand-primary/10 text-sm text-brand-secondary outline-none transition-all duration-150 placeholder:text-brand-outline"
                />
              </div>
            </div>
          )}

          {/* Primary CTA Button (Vivid Yellow #ffd300 with #10162f text per DESIGN.md) */}
          <button
            type="submit"
            disabled={loading}
            className="w-full mt-2 flex items-center justify-center gap-2 py-3 px-4 bg-brand-tertiary hover:bg-brand-tertiary-dim text-brand-secondary rounded-[14px] text-sm font-black transition-all duration-150 hover:scale-[1.01] active:scale-[0.99] shadow-md shadow-brand-tertiary/20 disabled:opacity-60"
          >
            {loading ? (
              <Loader2 className="w-4 h-4 animate-spin text-brand-secondary" />
            ) : (
              <>
                <span>
                  {mode === "signin" && "Sign In"}
                  {mode === "signup" && "Create Student Account"}
                  {mode === "forgot" && "Send Reset Link"}
                </span>
                <ArrowRight className="w-4 h-4 text-brand-secondary" />
              </>
            )}
          </button>

          {/* Quick Demo Option for Instant Onboarding Testing */}
          <div className="relative flex items-center justify-center my-4">
            <div className="border-t border-brand-outline-variant w-full" />
            <span className="bg-white px-2 text-[10px] font-bold text-brand-outline uppercase tracking-wider">
              Or Fast Track
            </span>
            <div className="border-t border-brand-outline-variant w-full" />
          </div>

          <button
            type="button"
            onClick={() => {
              if (typeof window !== "undefined") {
                document.cookie = "learnsync_demo_session=true; path=/; max-age=86400";
                localStorage.removeItem("learnsync_onboarding_completed");
                localStorage.removeItem("learnsync_learning_style");
              }
              router.push(redirectTo || "/");
            }}
            className="w-full flex items-center justify-center gap-2 py-2.5 px-4 bg-brand-surface-dim hover:bg-brand-surface border border-brand-outline-variant hover:border-brand-primary text-brand-secondary rounded-[14px] text-xs font-bold transition-all duration-150 shadow-sm"
          >
            <Sparkles className="w-3.5 h-3.5 text-brand-primary" />
            <span>Launch Instant Demo & Onboarding Test</span>
          </button>
        </form>

        {/* Back Link for Forgot Password */}
        {mode === "forgot" && (
          <div className="text-center mt-6">
            <button
              type="button"
              onClick={() => {
                setMode("signin");
                setError(null);
                setSuccessMessage(null);
              }}
              className="text-xs font-bold text-brand-primary hover:underline inline-flex items-center gap-1"
            >
              ← Back to Sign In
            </button>
          </div>
        )}

        {/* Footer Features Micro-Badge */}
        <div className="mt-8 pt-6 border-t border-brand-outline-variant flex items-center justify-center gap-4 text-[11px] font-semibold text-brand-on-surface-variant">
          <span className="flex items-center gap-1">
            <BrainCircuit className="w-3.5 h-3.5 text-brand-primary" /> FSRS v4 & BKT
          </span>
          <span>•</span>
          <span className="flex items-center gap-1">
            <Sparkles className="w-3.5 h-3.5 text-brand-tertiary-dim" /> Adaptive RAG
          </span>
        </div>
      </div>
    </main>
  );
}

export default function LoginPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen flex items-center justify-center bg-[#f8f9fb]">
          <div className="w-8 h-8 rounded-full border-2 border-brand-primary border-t-transparent animate-spin" />
        </div>
      }
    >
      <LoginForm />
    </Suspense>
  );
}
