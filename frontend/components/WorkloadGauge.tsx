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
    <div className="glass-card p-8 relative overflow-hidden">
      {/* Background radial glow */}
      <div 
        className={`absolute top-0 right-0 w-80 h-80 rounded-full blur-[100px] pointer-events-none opacity-20 transition-all duration-700 ${
          isBusy ? "bg-rose-500" : "bg-cyan-500"
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
                className="stroke-slate-800"
                strokeWidth="10"
                fill="transparent"
              />
              <circle
                cx="60"
                cy="60"
                r="50"
                className={`transition-all duration-1000 ease-out ${
                  isBusy ? "stroke-rose-500" : percentage > 55 ? "stroke-amber-400" : "stroke-accent-cyan"
                }`}
                strokeWidth="10"
                strokeDasharray={314}
                strokeDashoffset={314 - (314 * percentage) / 100}
                strokeLinecap="round"
                fill="transparent"
              />
            </svg>
            <div className="absolute flex flex-col items-center justify-center text-center">
              <span className="text-3xl font-black tracking-tight text-white">{percentage}%</span>
              <span className="text-[10px] font-bold uppercase tracking-widest text-slate-400">W(t)</span>
            </div>
          </div>

          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-400">Continuous 3-Day Lookahead</span>
              <span
                className={`px-2.5 py-0.5 rounded-full text-[11px] font-extrabold uppercase tracking-wider ${
                  isBusy
                    ? "bg-rose-500/20 text-rose-400 border border-rose-500/30"
                    : "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30"
                }`}
              >
                {isBusy ? "Busy Mode Active" : "Free Mode Active"}
              </span>
            </div>
            <h2 className="text-2xl font-black text-white tracking-tight">Workload Cockpit</h2>
            <p className="text-sm text-slate-300 max-w-md mt-1">
              {isBusy
                ? "High cognitive density detected. System scaled retention target to 80% and activated bite-sized 90s micro-tasks."
                : "Optimal cognitive bandwidth. System delivering deep Socratic dialogues, Mermaid flowcharts, and code sandboxes."}
            </p>
          </div>
        </div>

        {/* Right Info Cards: Hysteresis Thresholds & Critical Events */}
        <div className="flex flex-col sm:flex-row gap-4 w-full lg:w-auto">
          {/* Hysteresis Threshold Info */}
          <div className="p-4 rounded-[20px] bg-obsidian-950/60 border border-slate-800/80 min-w-[200px]">
            <span className="text-[11px] font-bold uppercase text-slate-400 block mb-1">Schmitt Hysteresis</span>
            <div className="flex items-center justify-between text-xs py-1 border-b border-slate-800/60 text-slate-300">
              <span>Free Mode Cutoff</span>
              <span className="font-mono font-bold text-emerald-400">≤ 55%</span>
            </div>
            <div className="flex items-center justify-between text-xs py-1 border-b border-slate-800/60 text-slate-300">
              <span>Dead-Band Hold</span>
              <span className="font-mono font-bold text-amber-400">55% - 70%</span>
            </div>
            <div className="flex items-center justify-between text-xs py-1 text-slate-300">
              <span>Busy Mode Spike</span>
              <span className="font-mono font-bold text-rose-400">&gt; 70%</span>
            </div>
          </div>

          {/* Active Events Density */}
          <div className="p-4 rounded-[20px] bg-obsidian-950/60 border border-slate-800/80 min-w-[220px]">
            <div className="flex items-center justify-between mb-2">
              <span className="text-[11px] font-bold uppercase text-slate-400">Upcoming Deadlines</span>
              <span className="text-xs font-bold font-mono text-accent-cyan px-2 py-0.5 rounded bg-cyan-950/50 border border-cyan-800/50">
                {activeEventCount} active
              </span>
            </div>
            <ul className="space-y-1.5">
              {criticalEvents.slice(0, 2).map((ev, i) => (
                <li key={i} className="text-xs text-slate-200 flex items-center gap-1.5 truncate">
                  <Flame className="w-3 h-3 text-amber-400 flex-shrink-0" />
                  <span className="truncate">{ev}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}
