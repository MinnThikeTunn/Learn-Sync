"use client";

import React, { useState, useRef, useEffect } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { 
  FolderTree, 
  Sparkles, 
  Layers, 
  ShieldAlert, 
  Activity, 
  Flame, 
  BrainCircuit,
  LogOut,
  User,
  Settings,
  ChevronDown,
  LogIn,
  Eye,
  Headphones,
  BookOpen,
  Code2,
  Check
} from "lucide-react";
import { useAuth } from "../context/AuthContext";

interface NavbarProps {
  workloadScore?: number;
  activeMode?: "free" | "busy" | "hysteresis_hold";
  learningStyle?: string;
  onOpenBurnoutModal?: () => void;
  onOpenOnboardingModal?: () => void;
}

export default function Navbar({
  workloadScore: propWorkloadScore,
  activeMode: propActiveMode,
  learningStyle: propLearningStyle,
  onOpenBurnoutModal,
  onOpenOnboardingModal,
}: NavbarProps) {
  const pathname = usePathname();
  const { user, session, profile, signOut, setLearningStyle } = useAuth();
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const [styleMenuOpen, setStyleMenuOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const styleMenuRef = useRef<HTMLDivElement>(null);

  // Self-synchronizing workload telemetry
  const [internalScore, setInternalScore] = useState<number | null>(
    typeof propWorkloadScore === "number" ? propWorkloadScore : null
  );
  const [internalMode, setInternalMode] = useState<"free" | "busy" | "hysteresis_hold">(
    propActiveMode || "free"
  );

  useEffect(() => {
    if (typeof propWorkloadScore === "number") {
      setInternalScore(propWorkloadScore);
    }
  }, [propWorkloadScore]);

  useEffect(() => {
    if (propActiveMode) {
      setInternalMode(propActiveMode);
    }
  }, [propActiveMode]);

  // Autonomous fetch when not passed as prop
  useEffect(() => {
    if (typeof propWorkloadScore === "number") return;

    let isMounted = true;
    const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

    const fetchLiveTelemetry = async () => {
      try {
        const headers: Record<string, string> = {
          "Content-Type": "application/json",
        };
        if (session?.access_token) {
          headers["Authorization"] = `Bearer ${session.access_token}`;
        }
        const uid = user?.id || "00000000-0000-0000-0000-000000000001";
        headers["X-Test-User-Id"] = uid;

        const res = await fetch(`${API_URL}/workload/live?days_ahead=7`, { headers });
        if (res.ok && isMounted) {
          const data = await res.json();
          if (typeof data.score === "number") {
            setInternalScore(data.score);
          }
          if (data.current_mode) {
            setInternalMode(data.current_mode);
          }
        }
      } catch (err) {
        console.warn("Navbar live workload fetch fallback error:", err);
      }
    };

    fetchLiveTelemetry();
    return () => {
      isMounted = false;
    };
  }, [propWorkloadScore, session?.access_token, user?.id]);

  const effectiveLearningStyle = profile?.learning_style || propLearningStyle || "visual";
  const currentScore = typeof propWorkloadScore === "number" ? propWorkloadScore : internalScore;
  const currentMode = propActiveMode || internalMode;
  const isBusy = currentMode === "busy";

  const navItems = [
    { label: "Cockpit", href: "/", icon: Activity },
    { label: "Virtual Folders", href: "/folders", icon: FolderTree },
    { label: "Multimodal Study", href: "/study", icon: Sparkles },
    { label: "Review & Feynman", href: "/review", icon: BrainCircuit },
  ];

  // Close dropdown on outside click
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setDropdownOpen(false);
      }
      if (styleMenuRef.current && !styleMenuRef.current.contains(event.target as Node)) {
        setStyleMenuOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const getInitials = (name?: string | null, email?: string | null) => {
    if (name) {
      const parts = name.trim().split(" ");
      if (parts.length >= 2) return `${parts[0][0]}${parts[1][0]}`.toUpperCase();
      return name.slice(0, 2).toUpperCase();
    }
    if (email) return email.slice(0, 2).toUpperCase();
    return "ST";
  };

  return (
    <header className="sticky top-0 z-50 px-4 sm:px-6 py-3.5 backdrop-blur-md bg-white/90 border-b border-brand-outline-variant shadow-elevation-sm">
      <div className="max-w-7xl mx-auto flex items-center justify-between">
        {/* Brand */}
        <Link href="/" className="flex items-center gap-3 group">
          <div className="w-10 h-10 rounded-[14px] bg-brand-primary flex items-center justify-center shadow-md shadow-brand-primary/25 group-hover:scale-105 transition-transform duration-200">
            <Layers className="w-5 h-5 text-white" />
          </div>
          <div>
            <span className="text-xl font-black tracking-tight text-brand-secondary flex items-center gap-1.5">
              LearnSync <span className="text-brand-secondary font-extrabold text-xs px-2 py-0.5 rounded-full bg-brand-tertiary border border-brand-tertiary-dim">AI</span>
            </span>
            <p className="text-[11px] font-semibold text-brand-on-surface-variant">Adaptive Co-Pilot</p>
          </div>
        </Link>

        {/* Center Nav Links */}
        <nav className="hidden lg:flex items-center gap-1 p-1.5 bg-brand-surface-dim border border-brand-outline-variant rounded-full shadow-sm">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`flex items-center gap-2 px-4 py-2 rounded-full text-sm font-bold transition-all duration-150 ${
                  isActive
                    ? "bg-brand-secondary text-white shadow-sm"
                    : "text-brand-on-surface-variant hover:text-brand-primary hover:bg-white"
                }`}
              >
                <Icon className={`w-4 h-4 ${isActive ? "text-brand-tertiary" : "text-brand-on-surface-variant"}`} />
                {item.label}
              </Link>
            );
          })}
        </nav>

        {/* Right Action & Telemetry */}
        <div className="flex items-center gap-2.5 sm:gap-3">
          {/* Interactive Learning Style Switcher */}
          <div className="relative hidden sm:block" ref={styleMenuRef}>
            <button
              onClick={() => setStyleMenuOpen(!styleMenuOpen)}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-brand-surface-dim hover:bg-white border border-brand-outline-variant hover:border-brand-primary text-xs font-bold text-brand-secondary transition-all shadow-sm"
              title="Click to switch learning style"
            >
              <span className="w-2 h-2 rounded-full bg-brand-primary animate-pulse" />
              <span className="capitalize">{effectiveLearningStyle.replace("_", " ")}</span>
              <ChevronDown className="w-3 h-3 text-brand-on-surface-variant opacity-70" />
            </button>

            {/* Quick Switch Dropdown */}
            {styleMenuOpen && (
              <div className="absolute right-0 mt-2 w-64 bg-white border border-brand-outline-variant rounded-[20px] shadow-elevation-md py-2.5 px-2 z-50 animate-in fade-in slide-in-from-top-2 duration-150">
                <div className="px-2.5 py-1.5 border-b border-brand-outline-variant/60 mb-1.5 flex items-center justify-between">
                  <span className="text-[11px] font-black uppercase tracking-wider text-brand-on-surface-variant">
                    Cognitive Modality
                  </span>
                  <span className="text-[10px] text-brand-primary font-bold">1-Click Switch</span>
                </div>

                <div className="space-y-1">
                  {[
                    { id: "visual", label: "Visual", desc: "Mermaid diagrams & flowcharts", icon: Eye, color: "text-cyan-600" },
                    { id: "auditory", label: "Auditory", desc: "Socratic podcasts & voice recaps", icon: Headphones, color: "text-purple-600" },
                    { id: "read_write", label: "Read / Write", desc: "Structured markdown & notes", icon: BookOpen, color: "text-emerald-600" },
                    { id: "kinesthetic", label: "Kinesthetic", desc: "Interactive sandboxes & labs", icon: Code2, color: "text-amber-600" },
                  ].map((item) => {
                    const Icon = item.icon;
                    const isCurrent = effectiveLearningStyle === item.id;
                    return (
                      <button
                        key={item.id}
                        onClick={async () => {
                          await setLearningStyle(item.id as any);
                          setStyleMenuOpen(false);
                        }}
                        className={`w-full flex items-center justify-between p-2 rounded-[14px] text-left transition-colors ${
                          isCurrent
                            ? "bg-brand-surface-dim border border-brand-primary/40 font-bold"
                            : "hover:bg-brand-surface-dim/60 font-medium"
                        }`}
                      >
                        <div className="flex items-center gap-2.5">
                          <div className={`w-7 h-7 rounded-[10px] bg-brand-surface flex items-center justify-center ${item.color}`}>
                            <Icon className="w-4 h-4" />
                          </div>
                          <div>
                            <p className="text-xs font-bold text-brand-secondary">{item.label}</p>
                            <p className="text-[10px] text-brand-on-surface-variant line-clamp-1">{item.desc}</p>
                          </div>
                        </div>
                        {isCurrent && <Check className="w-3.5 h-3.5 text-brand-primary stroke-[3]" />}
                      </button>
                    );
                  })}
                </div>

                {onOpenOnboardingModal && (
                  <div className="mt-2 pt-2 border-t border-brand-outline-variant/60">
                    <button
                      onClick={() => {
                        setStyleMenuOpen(false);
                        onOpenOnboardingModal();
                      }}
                      className="w-full flex items-center gap-2 px-2.5 py-1.5 rounded-[12px] text-xs font-bold text-brand-primary hover:bg-brand-surface-dim transition-colors"
                    >
                      <Sparkles className="w-3.5 h-3.5" />
                      <span>Take Diagnostic Assessment</span>
                    </button>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Workload Status Pill */}
          <div
            className={`flex items-center gap-1.5 sm:gap-2 px-3 py-1.5 rounded-full border text-xs font-bold transition-colors ${
              isBusy
                ? "bg-rose-50 border-rose-200 text-rose-700"
                : "bg-emerald-50 border-emerald-200 text-emerald-700"
            }`}
          >
            {isBusy ? <Flame className="w-3.5 h-3.5 text-rose-600 animate-bounce" /> : <Activity className="w-3.5 h-3.5 text-emerald-600" />}
            <span className="hidden xs:inline">{isBusy ? "Busy Mode" : "Free Mode"}</span>
            <span className="font-mono opacity-80">
              ({currentScore !== null ? `${(currentScore * 100).toFixed(0)}%` : "..."})
            </span>
          </div>

          {/* Burnout Guard Button */}
          {onOpenBurnoutModal && (
            <button
              onClick={onOpenBurnoutModal}
              className="hidden md:flex items-center gap-1.5 px-3.5 py-1.5 rounded-full bg-brand-tertiary-container hover:bg-brand-tertiary border border-brand-tertiary text-brand-on-tertiary-container text-xs font-bold transition-all duration-150 hover:scale-105 shadow-sm"
            >
              <ShieldAlert className="w-3.5 h-3.5 text-brand-secondary" />
              <span>Burnout Guard</span>
            </button>
          )}

          {/* Auth Identity Dropdown or Sign In CTA */}
          {user ? (
            <div className="relative" ref={dropdownRef}>
              <button
                onClick={() => setDropdownOpen(!dropdownOpen)}
                className="flex items-center gap-2 p-1 pl-1.5 pr-2.5 rounded-full bg-brand-surface border border-brand-outline-variant hover:border-brand-primary hover:shadow-elevation-sm transition-all duration-150"
              >
                <div className="w-7 h-7 rounded-full bg-brand-secondary text-brand-tertiary flex items-center justify-center text-xs font-black">
                  {getInitials(profile?.full_name, user.email)}
                </div>
                <span className="hidden md:inline text-xs font-bold text-brand-secondary max-w-[100px] truncate">
                  {profile?.full_name || user.email?.split("@")[0]}
                </span>
                <ChevronDown className="w-3.5 h-3.5 text-brand-outline" />
              </button>

              {/* Profile Dropdown Menu */}
              {dropdownOpen && (
                <div className="absolute right-0 mt-2 w-64 bg-white border border-brand-outline-variant rounded-[20px] shadow-elevation-md py-3 px-3 z-50 animate-in fade-in slide-in-from-top-2 duration-150">
                  <div className="px-3 py-2 border-b border-brand-outline-variant mb-2">
                    <p className="text-xs font-black text-brand-secondary truncate">
                      {profile?.full_name || "Student"}
                    </p>
                    <p className="text-[11px] text-brand-on-surface-variant truncate">
                      {user.email}
                    </p>
                    <div className="mt-2 flex items-center gap-1.5 text-[10px] font-bold text-brand-primary bg-brand-surface-dim px-2 py-1 rounded-md">
                      <span>Retention Goal:</span>
                      <span>{Math.round((profile?.target_retention || 0.90) * 100)}%</span>
                    </div>
                  </div>

                  {onOpenOnboardingModal && (
                    <button
                      onClick={() => {
                        setDropdownOpen(false);
                        onOpenOnboardingModal();
                      }}
                      className="w-full flex items-center gap-2 px-3 py-2 text-xs font-bold text-brand-secondary hover:bg-brand-surface-dim rounded-[10px] transition-colors"
                    >
                      <Settings className="w-4 h-4 text-brand-outline" />
                      <span>Adjust Learning Style</span>
                    </button>
                  )}

                  <button
                    onClick={() => {
                      setDropdownOpen(false);
                      signOut();
                    }}
                    className="w-full flex items-center gap-2 px-3 py-2 text-xs font-bold text-brand-error hover:bg-brand-error-container rounded-[10px] transition-colors mt-1"
                  >
                    <LogOut className="w-4 h-4 text-brand-error" />
                    <span>Sign Out</span>
                  </button>
                </div>
              )}
            </div>
          ) : (
            <Link
              href="/login"
              className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-full bg-brand-primary hover:bg-brand-primary-dim text-white text-xs font-bold transition-all duration-150 hover:scale-105 shadow-sm"
            >
              <LogIn className="w-3.5 h-3.5" />
              <span>Sign In</span>
            </Link>
          )}
        </div>
      </div>
    </header>
  );
}
