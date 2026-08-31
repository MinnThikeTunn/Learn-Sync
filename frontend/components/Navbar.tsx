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
  LogIn
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
  workloadScore = 0.42,
  activeMode = "free",
  learningStyle: propLearningStyle,
  onOpenBurnoutModal,
  onOpenOnboardingModal,
}: NavbarProps) {
  const pathname = usePathname();
  const { user, profile, signOut } = useAuth();
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  const effectiveLearningStyle = profile?.learning_style || propLearningStyle || "visual";
  const isBusy = activeMode === "busy";

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
          {/* Learning Style Pill */}
          <div className="hidden sm:flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-brand-surface-dim border border-brand-outline-variant text-xs font-bold text-brand-secondary">
            <span className="w-2 h-2 rounded-full bg-brand-primary animate-pulse" />
            <span className="capitalize">{effectiveLearningStyle}</span>
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
            <span className="font-mono opacity-80">({(workloadScore * 100).toFixed(0)}%)</span>
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
