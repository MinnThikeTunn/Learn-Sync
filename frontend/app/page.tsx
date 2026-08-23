"use client";

import { useState } from "react";
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

export default function DashboardPage() {
  const [workloadScore, setWorkloadScore] = useState(0.48);
  const [activeMode, setActiveMode] = useState<"free" | "busy" | "hysteresis_hold">("free");
  const [learningStyle, setLearningStyle] = useState("visual");
  const [showBurnoutModal, setShowBurnoutModal] = useState(false);
  const [showOnboarding, setShowOnboarding] = useState(false);

  const focusFolders = [
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
  ];

  const handleSimulateSpike = () => {
    setWorkloadScore(0.78);
    setActiveMode("busy");
  };

  const handleSimulateFree = () => {
    setWorkloadScore(0.42);
    setActiveMode("free");
  };

  return (
    <div className="min-h-screen flex flex-col bg-obsidian-950">
      <Navbar
        workloadScore={workloadScore}
        activeMode={activeMode}
        learningStyle={learningStyle}
        onOpenBurnoutModal={() => setShowBurnoutModal(true)}
      />

      <main className="flex-1 max-w-7xl w-full mx-auto px-6 py-8 space-y-8">
        {/* Top Hero Section */}
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
          <div>
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-slate-900 border border-slate-800 text-xs font-semibold text-slate-300 mb-2">
              <span className="w-2 h-2 rounded-full bg-accent-cyan" />
              <span>Welcome Back, Student</span>
            </div>
            <h1 className="text-4xl font-black text-white tracking-tight">Adaptive Study Cockpit</h1>
            <p className="text-slate-400 text-sm mt-1">
              Your real-time workload-aware learning co-pilot and virtual folder resource manager.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => setShowOnboarding(true)}
              className="px-4 py-2 rounded-full bg-slate-900 hover:bg-slate-800 border border-slate-800 text-xs font-bold text-slate-300 transition-colors"
            >
              Change Style
            </button>
            <button
              onClick={activeMode === "busy" ? handleSimulateFree : handleSimulateSpike}
              className={`px-4 py-2 rounded-full text-xs font-bold transition-all ${
                activeMode === "busy"
                  ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 hover:bg-emerald-500/30"
                  : "bg-rose-500/20 text-rose-300 border border-rose-500/30 hover:bg-rose-500/30"
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
          <Link href="/folders" className="glass-card-interactive p-6 group">
            <div className="w-12 h-12 rounded-[18px] bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center text-accent-cyan mb-4 group-hover:scale-110 transition-transform duration-300">
              <FolderTree className="w-6 h-6" />
            </div>
            <h3 className="text-xl font-black text-white mb-2 flex items-center justify-between">
              <span>Virtual Folders</span>
              <ArrowRight className="w-4 h-4 text-slate-500 group-hover:text-accent-cyan group-hover:translate-x-1 transition-all" />
            </h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              Explore course material scoped to materialized week paths and ingest syllabi via Docling parser.
            </p>
          </Link>

          {/* Multimodal Study Engine */}
          <Link href="/study" className="glass-card-interactive p-6 group">
            <div className="w-12 h-12 rounded-[18px] bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-accent-indigo mb-4 group-hover:scale-110 transition-transform duration-300">
              <Sparkles className="w-6 h-6" />
            </div>
            <h3 className="text-xl font-black text-white mb-2 flex items-center justify-between">
              <span>Multimodal Study</span>
              <ArrowRight className="w-4 h-4 text-slate-500 group-hover:text-accent-indigo group-hover:translate-x-1 transition-all" />
            </h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              Generate grounded Mermaid diagrams, Socratic dialogue scripts, code labs, and Pareto cheat-sheets.
            </p>
          </Link>

          {/* Spaced Repetition & Feynman Loop */}
          <Link href="/review" className="glass-card-interactive p-6 group">
            <div className="w-12 h-12 rounded-[18px] bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400 mb-4 group-hover:scale-110 transition-transform duration-300">
              <BrainCircuit className="w-6 h-6" />
            </div>
            <h3 className="text-xl font-black text-white mb-2 flex items-center justify-between">
              <span>Review & Feynman</span>
              <ArrowRight className="w-4 h-4 text-slate-500 group-hover:text-emerald-400 group-hover:translate-x-1 transition-all" />
            </h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              Elastic FSRS flashcard deck with leech quarantine and active recall plain-language precision gap analyzer.
            </p>
          </Link>
        </div>

        {/* Priority Focus Virtual Folders Grid */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-2xl font-black text-white tracking-tight">Active Priority Folders</h2>
            <Link href="/folders" className="text-xs font-bold text-accent-cyan hover:underline flex items-center gap-1">
              <span>View all folders</span>
              <ArrowRight className="w-3 h-3" />
            </Link>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {focusFolders.map((folder) => {
              const masteryPct = Math.round(folder.mastery * 100);
              return (
                <div key={folder.id} className="glass-card p-6 border border-slate-800 space-y-4">
                  <div className="flex items-center justify-between">
                    <span className="px-2.5 py-1 rounded-full bg-slate-900 border border-slate-800 text-[11px] font-mono font-bold text-accent-cyan">
                      {folder.course}
                    </span>
                    <span className="text-xs text-slate-400 font-medium flex items-center gap-1">
                      <Clock className="w-3.5 h-3.5" />
                      {folder.dueDays}d lookahead
                    </span>
                  </div>

                  <div>
                    <h3 className="text-lg font-bold text-white tracking-tight">{folder.name.replace(/_/g, " ")}</h3>
                    <p className="text-xs text-slate-500 font-mono mt-0.5">{folder.path}</p>
                  </div>

                  {/* Bayesian Knowledge Tracing Mastery Meter */}
                  <div>
                    <div className="flex items-center justify-between text-xs mb-1.5">
                      <span className="text-slate-400 font-semibold">BKT Concept Mastery P(L_t)</span>
                      <span className="font-mono font-bold text-white">{masteryPct}%</span>
                    </div>
                    <div className="w-full h-2 bg-slate-900 rounded-full overflow-hidden">
                      <div
                        className={`h-full rounded-full transition-all duration-500 ${
                          masteryPct >= 85 ? "bg-emerald-400" : masteryPct >= 50 ? "bg-amber-400" : "bg-rose-400"
                        }`}
                        style={{ width: `${masteryPct}%` }}
                      />
                    </div>
                  </div>

                  <div className="pt-2 border-t border-slate-800/80 flex items-center justify-between">
                    <span className="text-xs text-slate-400 font-semibold">{folder.cardsDue} cards due</span>
                    <Link
                      href={`/study?folder=${folder.id}&topic=${encodeURIComponent(folder.name)}`}
                      className="px-3.5 py-1.5 rounded-full bg-accent-cyan/10 hover:bg-accent-cyan/20 text-accent-cyan text-xs font-bold transition-colors"
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
