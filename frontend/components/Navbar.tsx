"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { 
  FolderTree, 
  Sparkles, 
  Layers, 
  ShieldAlert, 
  Activity,
  Flame,
  BrainCircuit
} from "lucide-react";

interface NavbarProps {
  workloadScore?: number;
  activeMode?: "free" | "busy" | "hysteresis_hold";
  learningStyle?: string;
  onOpenBurnoutModal?: () => void;
}

export default function Navbar({
  workloadScore = 0.42,
  activeMode = "free",
  learningStyle = "visual",
  onOpenBurnoutModal,
}: NavbarProps) {
  const pathname = usePathname();

  const navItems = [
    { label: "Cockpit", href: "/", icon: Activity },
    { label: "Virtual Folders", href: "/folders", icon: FolderTree },
    { label: "Multimodal Study", href: "/study", icon: Sparkles },
    { label: "Review & Feynman", href: "/review", icon: BrainCircuit },
  ];

  const isBusy = activeMode === "busy";

  return (
    <header className="sticky top-0 z-50 px-6 py-4 backdrop-blur-md bg-obsidian-950/80 border-b border-slate-800/60">
      <div className="max-w-7xl mx-auto flex items-center justify-between">
        {/* Brand */}
        <Link href="/" className="flex items-center gap-3 group">
          <div className="w-10 h-10 rounded-[14px] bg-gradient-to-br from-cyan-400 to-indigo-600 flex items-center justify-center shadow-lg shadow-cyan-500/20 group-hover:scale-105 transition-transform duration-300">
            <Layers className="w-5 h-5 text-white" />
          </div>
          <div>
            <span className="text-xl font-black tracking-tight text-white flex items-center gap-1.5">
              LearnSync <span className="text-accent-cyan font-extrabold text-sm px-2 py-0.5 rounded-full bg-accent-cyan/10 border border-accent-cyan/20">AI</span>
            </span>
            <p className="text-[11px] font-medium text-slate-400">Adaptive Co-Pilot</p>
          </div>
        </Link>

        {/* Center Nav Links */}
        <nav className="hidden md:flex items-center gap-1 p-1.5 bg-obsidian-900/90 border border-slate-800/80 rounded-full shadow-inner">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`flex items-center gap-2 px-4 py-2 rounded-full text-sm font-semibold transition-all duration-200 ${
                  isActive
                    ? "bg-slate-800 text-white shadow-sm"
                    : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/50"
                }`}
              >
                <Icon className={`w-4 h-4 ${isActive ? "text-accent-cyan" : "text-slate-400"}`} />
                {item.label}
              </Link>
            );
          })}
        </nav>

        {/* Right Action & Workload Telemetry */}
        <div className="flex items-center gap-3">
          {/* Learning Style Indicator */}
          <div className="hidden sm:flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-slate-900/90 border border-slate-800 text-xs font-semibold text-slate-300">
            <span className="w-2 h-2 rounded-full bg-accent-indigo animate-pulse" />
            <span className="capitalize">{learningStyle}</span>
          </div>

          {/* Workload Status Pill */}
          <div
            className={`flex items-center gap-2 px-3.5 py-1.5 rounded-full border text-xs font-bold transition-colors ${
              isBusy
                ? "bg-rose-500/10 border-rose-500/30 text-rose-400"
                : "bg-emerald-500/10 border-emerald-500/30 text-emerald-400"
            }`}
          >
            {isBusy ? <Flame className="w-3.5 h-3.5 text-rose-400 animate-bounce" /> : <Activity className="w-3.5 h-3.5 text-emerald-400" />}
            <span>{isBusy ? "Busy Mode" : "Free Mode"}</span>
            <span className="font-mono opacity-80">({(workloadScore * 100).toFixed(0)}%)</span>
          </div>

          {/* Burnout Guard Button */}
          {onOpenBurnoutModal && (
            <button
              onClick={onOpenBurnoutModal}
              className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-full bg-amber-500/10 hover:bg-amber-500/20 border border-amber-500/30 text-amber-400 text-xs font-bold transition-all duration-200 hover:scale-105"
            >
              <ShieldAlert className="w-3.5 h-3.5 text-amber-400" />
              <span>Burnout Guard</span>
            </button>
          )}
        </div>
      </div>
    </header>
  );
}
