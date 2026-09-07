"use client";

import { useState } from "react";
import { Activity, Flame, Sparkles, ShieldCheck, Plus, RefreshCw, Sliders, Play, RotateCcw, Layers } from "lucide-react";
import { resolveCockpitMode, getHysteresisBand, getRetentionTarget, formatLookaheadDays } from "@/lib/workloadCockpitUtils";

interface WorkloadGaugeProps {
  score: number;
  mode: "free" | "busy" | "hysteresis_hold";
  activeEventCount?: number;
  criticalEvents?: string[];
  lookaheadDays?: number;
  onLookaheadChange?: (days: number) => void;
  onAddDeadline?: () => void;
  onSeedDemo?: (scenario: "busy" | "deadband" | "free") => void;
  onRefresh?: () => void;
  isRefreshing?: boolean;
}

export default function WorkloadGauge({
  score,
  mode,
  activeEventCount = 0,
  criticalEvents = [],
  lookaheadDays = 3,
  onLookaheadChange,
  onAddDeadline,
  onSeedDemo,
  onRefresh,
  isRefreshing = false,
}: WorkloadGaugeProps) {
  // Interactive Simulation Sandbox State
  const [isSimulating, setIsSimulating] = useState(false);
  const [simScore, setSimScore] = useState(score);
  const [simMode, setSimMode] = useState<"free" | "busy" | "hysteresis_hold">(mode);

  // Active values based on live vs simulation
  const effectiveScore = isSimulating ? simScore : score;
  const effectiveMode = isSimulating ? simMode : mode;
  const percentage = Math.min(100, Math.max(0, Math.round(effectiveScore * 100)));
  const isBusy = effectiveMode === "busy";
  const activeBand = getHysteresisBand(effectiveScore);
  const retentionTarget = getRetentionTarget(effectiveMode);

  const handleSimSliderChange = (newVal: number) => {
    const s = newVal / 100;
    setSimScore(s);
    setSimMode((prev) => resolveCockpitMode(s, prev));
  };

  const handleSimPreset = (presetScore: number) => {
    setSimScore(presetScore);
    setSimMode((prev) => resolveCockpitMode(presetScore, prev));
  };

  const lookaheadOptions = [1, 3, 5, 7];

  return (
    <div className="bg-white border border-brand-outline-variant shadow-elevation-md rounded-[32px] p-8 relative overflow-hidden transition-all duration-300">
      {/* Background soft tint */}
      <div 
        className={`absolute top-0 right-0 w-80 h-80 rounded-full blur-[100px] pointer-events-none opacity-10 transition-all duration-700 ${
          isBusy ? "bg-rose-500" : "bg-brand-primary"
        }`} 
      />

      {/* Main Cockpit Flex Row */}
      <div className="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-8 relative z-10">
        
        {/* Left Stats & Circular Gauge Display */}
        <div className="flex items-center gap-6">
          <div className="relative w-32 h-32 flex-shrink-0 flex items-center justify-center">
            {/* SVG Circular Progress Meter */}
            <svg className="w-full h-full transform -rotate-90" viewBox="0 0 120 120">
              <circle
                cx="60"
                cy="60"
                r="50"
                className="stroke-brand-surface-container-highest"
                strokeWidth="10"
                fill="transparent"
              />
              <circle
                cx="60"
                cy="60"
                r="50"
                className={`transition-all duration-700 ease-out ${
                  isBusy ? "stroke-brand-error" : percentage > 55 ? "stroke-amber-500" : "stroke-brand-primary"
                }`}
                strokeWidth="10"
                strokeDasharray={314}
                strokeDashoffset={314 - (314 * percentage) / 100}
                strokeLinecap="round"
                fill="transparent"
              />
            </svg>
            <div className="absolute flex flex-col items-center justify-center text-center">
              <span className="text-3xl font-black tracking-tight text-brand-secondary">{percentage}%</span>
              <span className="text-[10px] font-bold uppercase tracking-widest text-brand-on-surface-variant">W(t)</span>
            </div>
          </div>

          <div>
            {/* Horizon & Mode Badge Row */}
            <div className="flex flex-wrap items-center gap-2 mb-1.5">
              {/* Lookahead Horizon Selector */}
              <div className="flex items-center gap-1 bg-brand-surface-dim border border-brand-outline-variant px-2 py-0.5 rounded-full">
                <span className="text-[10px] font-bold uppercase tracking-wider text-brand-on-surface-variant mr-1">
                  {formatLookaheadDays(lookaheadDays)}
                </span>
                {lookaheadOptions.map((days) => (
                  <button
                    key={days}
                    onClick={() => onLookaheadChange?.(days)}
                    className={`text-[10px] font-bold px-1.5 py-0.2 rounded-full transition-all ${
                      lookaheadDays === days
                        ? "bg-brand-primary text-white shadow-xs"
                        : "text-brand-on-surface-variant hover:text-brand-secondary"
                    }`}
                    title={`Set ${days}-day rolling lookahead horizon`}
                  >
                    {days}d
                  </button>
                ))}
              </div>

              {/* Mode State Indicator */}
              <span
                className={`px-2.5 py-0.5 rounded-full text-[11px] font-extrabold uppercase tracking-wider transition-colors ${
                  isBusy
                    ? "bg-rose-50 text-rose-700 border border-rose-200"
                    : "bg-emerald-50 text-emerald-700 border border-emerald-200"
                }`}
              >
                {isBusy ? "Busy Mode Active" : "Free Mode Active"}
              </span>

              {/* Retention Target Modulation Pill */}
              <span className="px-2 py-0.5 rounded-full text-[10px] font-mono font-bold bg-brand-surface-dim border border-brand-outline-variant text-brand-secondary">
                Target {retentionTarget}%
              </span>
            </div>

            {/* Title & Microcopy */}
            <div className="flex items-center gap-3">
              <h2 className="text-2xl font-black text-brand-secondary tracking-tight">Workload Cockpit</h2>
              {onRefresh && (
                <button
                  onClick={onRefresh}
                  disabled={isRefreshing}
                  title="Re-evaluate live workload telemetry"
                  className="p-1 rounded-full text-brand-on-surface-variant hover:text-brand-primary hover:bg-brand-surface-dim transition-all"
                >
                  <RefreshCw className={`w-3.5 h-3.5 ${isRefreshing ? "animate-spin text-brand-primary" : ""}`} />
                </button>
              )}
            </div>

            <p className="text-sm text-brand-on-surface-variant max-w-md mt-1 leading-relaxed">
              {isBusy
                ? "High cognitive density detected. System scaled retention target to 80% and activated bite-sized 90s micro-tasks."
                : "Optimal cognitive bandwidth. System delivering deep Socratic dialogues, Mermaid flowcharts, and code sandboxes."}
            </p>
          </div>
        </div>

        {/* Right Info Cards: Hysteresis Thresholds & Critical Events */}
        <div className="flex flex-col sm:flex-row gap-4 w-full lg:w-auto">
          
          {/* Hysteresis Threshold Info Card */}
          <div className="p-4 rounded-[20px] bg-brand-surface-dim border border-brand-outline-variant min-w-[210px] transition-all">
            <div className="flex items-center justify-between mb-1">
              <span className="text-[11px] font-bold uppercase text-brand-on-surface-variant block">Schmitt Hysteresis</span>
              <button
                onClick={() => {
                  if (isSimulating) {
                    setIsSimulating(false);
                  } else {
                    setSimScore(score);
                    setSimMode(mode);
                    setIsSimulating(true);
                  }
                }}
                className={`text-[10px] font-bold px-2 py-0.5 rounded-full border transition-all flex items-center gap-1 ${
                  isSimulating
                    ? "bg-brand-primary text-white border-brand-primary"
                    : "bg-white text-brand-secondary border-brand-outline-variant hover:border-brand-primary"
                }`}
                title="Toggle interactive Hysteresis simulator"
              >
                <Sliders className="w-2.5 h-2.5" />
                <span>{isSimulating ? "Exit Sim" : "Simulate"}</span>
              </button>
            </div>

            {/* Threshold Rows with Active Band Highlights */}
            <div className={`flex items-center justify-between text-xs py-1 border-b border-brand-outline-variant text-brand-secondary px-1.5 rounded-md transition-colors ${
              activeBand === "free" ? "bg-emerald-50 text-emerald-800 font-semibold" : ""
            }`}>
              <div className="flex items-center gap-1.5">
                {activeBand === "free" && <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />}
                <span>Free Mode Cutoff</span>
              </div>
              <span className="font-mono font-bold text-emerald-600">≤ 55%</span>
            </div>

            <div className={`flex items-center justify-between text-xs py-1 border-b border-brand-outline-variant text-brand-secondary px-1.5 rounded-md transition-colors ${
              activeBand === "deadband" ? "bg-amber-50 text-amber-800 font-semibold" : ""
            }`}>
              <div className="flex items-center gap-1.5">
                {activeBand === "deadband" && <span className="w-1.5 h-1.5 rounded-full bg-amber-500 animate-pulse" />}
                <span>Dead-Band Hold</span>
              </div>
              <span className="font-mono font-bold text-amber-600">55% - 70%</span>
            </div>

            <div className={`flex items-center justify-between text-xs py-1 text-brand-secondary px-1.5 rounded-md transition-colors ${
              activeBand === "busy" ? "bg-rose-50 text-rose-800 font-semibold" : ""
            }`}>
              <div className="flex items-center gap-1.5">
                {activeBand === "busy" && <span className="w-1.5 h-1.5 rounded-full bg-rose-500 animate-pulse" />}
                <span>Busy Mode Spike</span>
              </div>
              <span className="font-mono font-bold text-rose-600">&gt; 70%</span>
            </div>
          </div>

          {/* Active Events Density Card */}
          <div className="p-4 rounded-[20px] bg-brand-surface-dim border border-brand-outline-variant min-w-[220px]">
            <div className="flex items-center justify-between mb-2">
              <span className="text-[11px] font-bold uppercase text-brand-on-surface-variant">Upcoming Deadlines</span>
              <div className="flex items-center gap-1.5">
                <span className={`text-xs font-bold font-mono px-2 py-0.5 rounded border ${
                  activeEventCount > 0
                    ? "text-brand-primary bg-brand-primary/10 border-brand-primary/20"
                    : "text-emerald-700 bg-emerald-50 border-emerald-200"
                }`}>
                  {activeEventCount > 0 ? `${activeEventCount} active` : "None acute"}
                </span>
                {onAddDeadline && (
                  <button
                    onClick={onAddDeadline}
                    title="Add new academic event deadline"
                    className="p-1 rounded-full bg-white hover:bg-brand-primary hover:text-white border border-brand-outline-variant text-brand-secondary transition-all"
                  >
                    <Plus className="w-3 h-3" />
                  </button>
                )}
              </div>
            </div>

            {criticalEvents && criticalEvents.length > 0 ? (
              <ul className="space-y-1.5">
                {criticalEvents.slice(0, 3).map((ev, i) => (
                  <li key={i} className="text-xs text-brand-secondary flex items-center gap-1.5 truncate">
                    <Flame className="w-3.5 h-3.5 text-brand-tertiary-dim flex-shrink-0" />
                    <span className="truncate font-medium">{ev}</span>
                  </li>
                ))}
              </ul>
            ) : (
              <div className="space-y-2">
                <div className="text-xs text-emerald-700 flex items-center gap-1.5 py-0.5">
                  <ShieldCheck className="w-4 h-4 text-emerald-600 flex-shrink-0" />
                  <span className="font-medium">Optimal cognitive bandwidth</span>
                </div>
                {onSeedDemo && (
                  <div className="flex items-center gap-1 pt-1 border-t border-brand-outline-variant">
                    <button
                      onClick={() => onSeedDemo("busy")}
                      className="text-[10px] font-bold px-2 py-1 rounded bg-white hover:bg-brand-surface border border-brand-outline-variant text-brand-primary transition-all flex items-center gap-1"
                    >
                      <Plus className="w-2.5 h-2.5" />
                      <span>Seed Deadlines</span>
                    </button>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Interactive Simulator Drawer (when active) */}
      {isSimulating && (
        <div className="mt-6 pt-5 border-t border-brand-outline-variant/60 flex flex-col md:flex-row items-center justify-between gap-4 animate-fadeIn">
          <div className="flex items-center gap-3 w-full md:w-auto">
            <span className="text-xs font-bold text-brand-secondary flex items-center gap-1.5">
              <Sliders className="w-3.5 h-3.5 text-brand-primary" />
              <span>Simulate Score W(t):</span>
            </span>
            <input
              type="range"
              min="0"
              max="100"
              value={Math.round(simScore * 100)}
              onChange={(e) => handleSimSliderChange(Number(e.target.value))}
              className="w-48 h-1.5 bg-brand-surface-container-highest rounded-lg appearance-none cursor-pointer accent-brand-primary"
            />
            <span className="text-xs font-mono font-bold text-brand-secondary w-10 text-right">
              {Math.round(simScore * 100)}%
            </span>
          </div>

          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-[11px] font-medium text-brand-on-surface-variant">Presets:</span>
            <button
              onClick={() => handleSimPreset(0.35)}
              className="text-xs px-2.5 py-1 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200 font-bold hover:bg-emerald-100 transition-all"
            >
              Free (35%)
            </button>
            <button
              onClick={() => handleSimPreset(0.65)}
              className="text-xs px-2.5 py-1 rounded-full bg-amber-50 text-amber-700 border border-amber-200 font-bold hover:bg-amber-100 transition-all"
            >
              Dead-Band (65%)
            </button>
            <button
              onClick={() => handleSimPreset(0.85)}
              className="text-xs px-2.5 py-1 rounded-full bg-rose-50 text-rose-700 border border-rose-200 font-bold hover:bg-rose-100 transition-all"
            >
              Busy Spike (85%)
            </button>
            <button
              onClick={() => {
                setSimScore(score);
                setSimMode(mode);
              }}
              title="Reset simulation to live data"
              className="p-1 rounded-full text-brand-on-surface-variant hover:text-brand-secondary hover:bg-brand-surface-dim transition-all"
            >
              <RotateCcw className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
