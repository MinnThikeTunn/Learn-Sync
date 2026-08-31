"use client";

import { Activity, Flame, Sparkles, ShieldCheck } from "lucide-react";

interface WorkloadGaugeProps {
  score: number;
  mode: "free" | "busy" | "hysteresis_hold";
  activeEventCount?: number;
  criticalEvents?: string[];
}

export default function WorkloadGauge({
  score,
  mode,
  activeEventCount = 3,
  criticalEvents = ["CS101 Midterm Exam", "Algorithms Project 2"],
}: WorkloadGaugeProps) {
  const percentage = Math.min(100, Math.max(0, Math.round(score * 100)));
  const isBusy = mode === "busy";

  return (
    <div className="bg-white border border-brand-outline-variant shadow-elevation-md rounded-[32px] p-8 relative overflow-hidden">
      {/* Background soft tint */}
      <div 
        className={`absolute top-0 right-0 w-80 h-80 rounded-full blur-[100px] pointer-events-none opacity-10 transition-all duration-700 ${
          isBusy ? "bg-rose-500" : "bg-brand-primary"
        }`} 
      />

      <div className="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-8 relative z-10">
        {/* Left Stats & Gauge Display */}
        <div className="flex items-center gap-6">
          <div className="relative w-32 h-32 flex items-center justify-center">
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
                className={`transition-all duration-1000 ease-out ${
                  isBusy ? "stroke-brand-error" : percentage > 55 ? "stroke-brand-tertiary" : "stroke-brand-primary"
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
            <div className="flex items-center gap-2 mb-1">
              <span className="text-xs font-bold uppercase tracking-wider text-brand-on-surface-variant">Continuous 3-Day Lookahead</span>
              <span
                className={`px-2.5 py-0.5 rounded-full text-[11px] font-extrabold uppercase tracking-wider ${
                  isBusy
                    ? "bg-rose-50 text-rose-700 border border-rose-200"
                    : "bg-emerald-50 text-emerald-700 border border-emerald-200"
                }`}
              >
                {isBusy ? "Busy Mode Active" : "Free Mode Active"}
              </span>
            </div>
            <h2 className="text-2xl font-black text-brand-secondary tracking-tight">Workload Cockpit</h2>
            <p className="text-sm text-brand-on-surface-variant max-w-md mt-1 leading-relaxed">
              {isBusy
                ? "High cognitive density detected. System scaled retention target to 80% and activated bite-sized 90s micro-tasks."
                : "Optimal cognitive bandwidth. System delivering deep Socratic dialogues, Mermaid flowcharts, and code sandboxes."}
            </p>
          </div>
        </div>

        {/* Right Info Cards: Hysteresis Thresholds & Critical Events */}
        <div className="flex flex-col sm:flex-row gap-4 w-full lg:w-auto">
          {/* Hysteresis Threshold Info */}
          <div className="p-4 rounded-[20px] bg-brand-surface-dim border border-brand-outline-variant min-w-[200px]">
            <span className="text-[11px] font-bold uppercase text-brand-on-surface-variant block mb-1">Schmitt Hysteresis</span>
            <div className="flex items-center justify-between text-xs py-1 border-b border-brand-outline-variant text-brand-secondary">
              <span>Free Mode Cutoff</span>
              <span className="font-mono font-bold text-emerald-600">≤ 55%</span>
            </div>
            <div className="flex items-center justify-between text-xs py-1 border-b border-brand-outline-variant text-brand-secondary">
              <span>Dead-Band Hold</span>
              <span className="font-mono font-bold text-amber-600">55% - 70%</span>
            </div>
            <div className="flex items-center justify-between text-xs py-1 text-brand-secondary">
              <span>Busy Mode Spike</span>
              <span className="font-mono font-bold text-rose-600">&gt; 70%</span>
            </div>
          </div>

          {/* Active Events Density */}
          <div className="p-4 rounded-[20px] bg-brand-surface-dim border border-brand-outline-variant min-w-[220px]">
            <div className="flex items-center justify-between mb-2">
              <span className="text-[11px] font-bold uppercase text-brand-on-surface-variant">Upcoming Deadlines</span>
              <span className="text-xs font-bold font-mono text-brand-primary px-2 py-0.5 rounded bg-brand-primary/10 border border-brand-primary/20">
                {activeEventCount} active
              </span>
            </div>
            <ul className="space-y-1.5">
              {criticalEvents.slice(0, 2).map((ev, i) => (
                <li key={i} className="text-xs text-brand-secondary flex items-center gap-1.5 truncate">
                  <Flame className="w-3.5 h-3.5 text-brand-tertiary-dim flex-shrink-0" />
                  <span className="truncate font-medium">{ev}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}
