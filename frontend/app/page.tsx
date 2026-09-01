"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { 
  FolderTree, 
  Sparkles, 
  BrainCircuit, 
  ArrowRight, 
  BookOpen, 
  Calendar, 
  Clock, 
  Flame, 
  Layers, 
  CheckCircle,
  TrendingUp,
  ShieldAlert
} from "lucide-react";

import Navbar from "@/components/Navbar";
import WorkloadGauge from "@/components/WorkloadGauge";
import BurnoutGuardModal from "@/components/BurnoutGuardModal";
import OnboardingModal from "@/components/OnboardingModal";
import ManualEventModal from "@/components/ManualEventModal";
import { useAuth } from "@/context/AuthContext";
import { createClient } from "@/lib/supabase/client";

export default function DashboardPage() {
  const { user, profile } = useAuth();
  const [workloadScore, setWorkloadScore] = useState(0.48);
  const [activeMode, setActiveMode] = useState<"free" | "busy" | "hysteresis_hold">("free");
  const [learningStyle, setLearningStyle] = useState(profile?.learning_style || "visual");
  const [showBurnoutModal, setShowBurnoutModal] = useState(false);
  const [showOnboarding, setShowOnboarding] = useState(false);
  const [showEventModal, setShowEventModal] = useState(false);
  const [upcomingEvents, setUpcomingEvents] = useState<any[]>([]);
  const [focusFolders, setFocusFolders] = useState<any[]>([
    {
      id: "f1",
      name: "Week_03_Recursion",
      course: "CS101",
      path: "/CS101/Week_03_Recursion",
      mastery: 0.72,
      dueDays: 2,
      cardsDue: 6,
    },
    {
      id: "f2",
      name: "Week_05_Dynamic_Programming",
      course: "CS101",
      path: "/CS101/Week_05_Dynamic_Programming",
      mastery: 0.35,
      dueDays: 4,
      cardsDue: 12,
    },
    {
      id: "f3",
      name: "Module_02_Graph_Traversals",
      course: "CS204",
      path: "/CS204/Module_02_Graph_Traversals",
      mastery: 0.88,
      dueDays: 7,
      cardsDue: 3,
    },
  ]);

  const fetchLiveWorkloadAndEvents = async () => {
    try {
      const supabase = createClient();
      const currentUser = (await supabase.auth.getUser()).data.user;
      if (currentUser) {
        // Fetch live upcoming events
        const { data: events } = await supabase
          .from("events")
          .select("*")
          .eq("user_id", currentUser.id)
          .gte("start_time", new Date().toISOString())
          .order("start_time")
          .limit(6);

        if (events && events.length > 0) {
          setUpcomingEvents(events);
        }

        // Fetch live workload calculation
        const res = await fetch("http://localhost:8000/api/v1/workload/live", {
          headers: { "X-Test-User-Id": currentUser.id },
        });
        if (res.ok) {
          const data = await res.json();
          setWorkloadScore(data.score);
          setActiveMode(data.current_mode);
        }
      }
    } catch (err) {
      console.warn("Could not fetch live workload:", err);
    }
  };

  useEffect(() => {
    if (profile) {
      if (profile.learning_style) {
        setLearningStyle(profile.learning_style);
      }
      if (profile.onboarding_completed === false || !profile.learning_style) {
        setShowOnboarding(true);
      }
    } else {
      // Check client-side storage for new / testing / unconfirmed sessions
      if (typeof window !== "undefined") {
        const completed = localStorage.getItem("learnsync_onboarding_completed");
        const cachedStyle = localStorage.getItem("learnsync_learning_style");
        if (completed !== "true" || !cachedStyle) {
          setShowOnboarding(true);
        } else {
          setLearningStyle(cachedStyle as any);
        }
      }
    }
    fetchLiveWorkloadAndEvents();
  }, [profile]);

  const handleConnectGoogle = async () => {
    try {
      const res = await fetch("http://localhost:8000/api/v1/oauth/google/url", {
        headers: { "X-Test-User-Id": user?.id || "demo-user" },
      });
      if (res.ok) {
        const data = await res.json();
        if (data.auth_url) {
          window.open(data.auth_url, "_blank");
        }
      }
    } catch (err) {
      console.error("Google OAuth URL error:", err);
    }
  };

  const handleSimulateSpike = () => {
    setWorkloadScore(0.78);
    setActiveMode("busy");
  };

  const handleSimulateFree = () => {
    setWorkloadScore(0.42);
    setActiveMode("free");
  };

  return (
    <div className="min-h-screen flex flex-col bg-[#f8f9fb]">
      <Navbar
        workloadScore={workloadScore}
        activeMode={activeMode}
        learningStyle={learningStyle}
        onOpenBurnoutModal={() => setShowBurnoutModal(true)}
        onOpenOnboardingModal={() => setShowOnboarding(true)}
      />

      <main className="flex-1 max-w-7xl w-full mx-auto px-6 py-8 space-y-8">
        {/* Top Hero Section */}
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
          <div>
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-brand-tertiary-container border border-brand-tertiary/40 text-xs font-bold text-brand-on-tertiary-container mb-2">
              <span className="w-2 h-2 rounded-full bg-brand-tertiary-dim" />
              <span>Welcome Back, {profile?.full_name || "Student"}</span>
            </div>
            <h1 className="text-4xl font-black text-brand-secondary tracking-tight">Adaptive Study Cockpit</h1>
            <p className="text-brand-on-surface-variant text-sm mt-1">
              Your real-time workload-aware learning co-pilot and virtual folder resource manager.
            </p>
          </div>

          <div className="flex items-center flex-wrap gap-2">
            <button
              onClick={() => setShowEventModal(true)}
              className="px-4 py-2 rounded-md bg-brand-primary text-white text-xs font-bold transition-all shadow-sm hover:bg-brand-primary/90 flex items-center gap-1.5"
            >
              <Calendar className="w-3.5 h-3.5" />
              <span>+ Add Deadline</span>
            </button>
            <button
              onClick={handleConnectGoogle}
              className="px-4 py-2 rounded-md bg-white hover:bg-brand-surface-dim border border-brand-outline-variant text-xs font-bold text-brand-secondary transition-all shadow-sm flex items-center gap-1.5"
            >
              <span>Sync Calendar</span>
            </button>
            <button
              onClick={() => setShowOnboarding(true)}
              className="px-4 py-2 rounded-md bg-white hover:bg-brand-surface-dim border border-brand-outline-variant text-xs font-bold text-brand-secondary transition-all shadow-sm"
            >
              Change Style
            </button>
            <button
              onClick={activeMode === "busy" ? handleSimulateFree : handleSimulateSpike}
              className={`px-4 py-2 rounded-md text-xs font-bold transition-all shadow-sm ${
                activeMode === "busy"
                  ? "bg-emerald-50 text-emerald-700 border border-emerald-300 hover:bg-emerald-100"
                  : "bg-rose-50 text-rose-700 border border-rose-300 hover:bg-rose-100"
              }`}
            >
              {activeMode === "busy" ? "Simulate Free Mode" : "Simulate Workload Spike"}
            </button>
          </div>
        </div>

        {/* Workload Cockpit Gauge Card */}
        <WorkloadGauge
          score={workloadScore}
          mode={activeMode}
          activeEventCount={3}
          criticalEvents={["CS101 Midterm Examination", "CS204 Graph Search Project"]}
        />

        {/* 3 Quick Action Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Virtual Folders Card */}
          <Link href="/folders" className="design-card-interactive p-6 group block">
            <div className="w-12 h-12 rounded-[14px] bg-brand-primary/10 border border-brand-primary/20 flex items-center justify-center text-brand-primary mb-4 group-hover:scale-105 transition-transform duration-150">
              <FolderTree className="w-6 h-6" />
            </div>
            <h3 className="text-xl font-black text-brand-secondary mb-2 flex items-center justify-between">
              <span>Virtual Folders</span>
              <ArrowRight className="w-4 h-4 text-brand-on-surface-variant group-hover:text-brand-primary group-hover:translate-x-1 transition-all" />
            </h3>
            <p className="text-xs text-brand-on-surface-variant leading-relaxed">
              Explore course material scoped to materialized week paths and ingest syllabi via Docling parser.
            </p>
          </Link>

          {/* Multimodal Study Engine */}
          <Link href="/study" className="design-card-interactive p-6 group block">
            <div className="w-12 h-12 rounded-[14px] bg-brand-primary/10 border border-brand-primary/20 flex items-center justify-center text-brand-primary mb-4 group-hover:scale-105 transition-transform duration-150">
              <Sparkles className="w-6 h-6" />
            </div>
            <h3 className="text-xl font-black text-brand-secondary mb-2 flex items-center justify-between">
              <span>Multimodal Study</span>
              <ArrowRight className="w-4 h-4 text-brand-on-surface-variant group-hover:text-brand-primary group-hover:translate-x-1 transition-all" />
            </h3>
            <p className="text-xs text-brand-on-surface-variant leading-relaxed">
              Generate grounded Mermaid diagrams, Socratic dialogue scripts, code labs, and Pareto cheat-sheets.
            </p>
          </Link>

          {/* Spaced Repetition & Feynman Loop */}
          <Link href="/review" className="design-card-interactive p-6 group block">
            <div className="w-12 h-12 rounded-[14px] bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-600 mb-4 group-hover:scale-105 transition-transform duration-150">
              <BrainCircuit className="w-6 h-6" />
            </div>
            <h3 className="text-xl font-black text-brand-secondary mb-2 flex items-center justify-between">
              <span>Review & Feynman</span>
              <ArrowRight className="w-4 h-4 text-brand-on-surface-variant group-hover:text-emerald-600 group-hover:translate-x-1 transition-all" />
            </h3>
            <p className="text-xs text-brand-on-surface-variant leading-relaxed">
              Elastic FSRS flashcard deck with leech quarantine and active recall plain-language precision gap analyzer.
            </p>
          </Link>
        </div>

        {/* Priority Focus Virtual Folders Grid */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-2xl font-black text-brand-secondary tracking-tight">Active Priority Folders</h2>
            <Link href="/folders" className="text-xs font-bold text-brand-primary hover:underline flex items-center gap-1">
              <span>View all folders</span>
              <ArrowRight className="w-3 h-3" />
            </Link>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {focusFolders.map((folder) => {
              const masteryPct = Math.round(folder.mastery * 100);
              return (
                <div key={folder.id} className="design-card p-6 space-y-4">
                  <div className="flex items-center justify-between">
                    <span className="px-2.5 py-1 rounded-full bg-brand-surface-dim border border-brand-outline-variant text-[11px] font-mono font-bold text-brand-primary">
                      {folder.course}
                    </span>
                    <span className="text-xs text-brand-on-surface-variant font-medium flex items-center gap-1">
                      <Clock className="w-3.5 h-3.5" />
                      {folder.dueDays}d lookahead
                    </span>
                  </div>

                  <div>
                    <h3 className="text-lg font-bold text-brand-secondary tracking-tight">{folder.name.replace(/_/g, " ")}</h3>
                    <p className="text-xs text-brand-on-surface-variant font-mono mt-0.5">{folder.path}</p>
                  </div>

                  {/* Bayesian Knowledge Tracing Mastery Meter */}
                  <div>
                    <div className="flex items-center justify-between text-xs mb-1.5">
                      <span className="text-brand-on-surface-variant font-semibold">BKT Concept Mastery P(L_t)</span>
                      <span className="font-mono font-bold text-brand-secondary">{masteryPct}%</span>
                    </div>
                    <div className="w-full h-2 bg-brand-surface-container-highest rounded-full overflow-hidden">
                      <div
                        className={`h-full rounded-full transition-all duration-500 ${
                          masteryPct >= 85 ? "bg-emerald-500" : masteryPct >= 50 ? "bg-brand-tertiary-dim" : "bg-rose-500"
                        }`}
                        style={{ width: `${masteryPct}%` }}
                      />
                    </div>
                  </div>

                  <div className="pt-3 border-t border-brand-outline-variant flex items-center justify-between">
                    <span className="text-xs text-brand-on-surface-variant font-semibold">{folder.cardsDue} cards due</span>
                    <Link
                      href={`/study?folder=${folder.id}&topic=${encodeURIComponent(folder.name)}`}
                      className="px-3.5 py-1.5 rounded-md bg-brand-tertiary hover:bg-brand-tertiary-dim text-brand-on-tertiary text-xs font-bold transition-all duration-150 shadow-sm"
                    >
                      Study Topic
                    </Link>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </main>

      {/* Manual Deadline Creation Modal */}
      <ManualEventModal
        isOpen={showEventModal}
        onClose={() => setShowEventModal(false)}
        onEventCreated={fetchLiveWorkloadAndEvents}
        userId={user?.id}
      />

      {/* Burnout Guard Modal */}
      <BurnoutGuardModal
        isOpen={showBurnoutModal}
        onClose={() => setShowBurnoutModal(false)}
      />

      {/* Onboarding Style Modal */}
      <OnboardingModal
        isOpen={showOnboarding}
        onSave={(style) => {
          setLearningStyle(style);
          setShowOnboarding(false);
        }}
      />
    </div>
  );
}
