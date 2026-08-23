"use client";

import { useState } from "react";
import { Eye, Headphones, BookOpen, Code2, Sparkles, Check } from "lucide-react";

interface OnboardingModalProps {
  isOpen: boolean;
  onSave: (style: string) => void;
}

export default function OnboardingModal({ isOpen, onSave }: OnboardingModalProps) {
  const [selectedStyle, setSelectedStyle] = useState("visual");

  if (!isOpen) return null;

  const styles = [
    {
      id: "visual",
      label: "Visual Learner",
      icon: Eye,
      description: "Interactive Mermaid diagrams, flowcharts, high-contrast cheat-sheets, and structural maps.",
      color: "from-cyan-500 to-blue-600",
    },
    {
      id: "auditory",
      label: "Auditory Learner",
      icon: Headphones,
      description: "Socratic audio dialogue scripts, conversational podcasts, and 30-second rapid verbal recaps.",
      color: "from-purple-500 to-indigo-600",
    },
    {
      id: "read_write",
      label: "Read / Write Learner",
      icon: BookOpen,
      description: "Deep structured markdown guides, detailed definitions, formulas, and 3-bullet Pareto takeaways.",
      color: "from-emerald-500 to-teal-600",
    },
    {
      id: "kinesthetic",
      label: "Kinesthetic Learner",
      icon: Code2,
      description: "Interactive code sandboxes, runnable test suites, and 90-second micro-snippet bug fixes.",
      color: "from-amber-500 to-orange-600",
    },
  ];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-obsidian-950/85 backdrop-blur-lg animate-in fade-in duration-300">
      <div className="glass-card max-w-2xl w-full p-8 border border-slate-700 shadow-2xl relative">
        <div className="text-center mb-8">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-accent-cyan/10 border border-accent-cyan/20 text-accent-cyan text-xs font-bold uppercase tracking-wider mb-3">
            <Sparkles className="w-3.5 h-3.5" />
            <span>Personalized Co-Pilot Setup</span>
          </div>
          <h2 className="text-3xl font-black text-white tracking-tight">Select Your Learning Style</h2>
          <p className="text-slate-400 text-sm max-w-md mx-auto mt-2">
            LearnSync AI dynamically customizes study artifacts, diagrams, audio scripts, and code exercises to your cognitive preference.
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-8">
          {styles.map((st) => {
            const Icon = st.icon;
            const isSelected = selectedStyle === st.id;
            return (
              <div
                key={st.id}
                onClick={() => setSelectedStyle(st.id)}
                className={`p-5 rounded-[24px] cursor-pointer transition-all duration-300 border relative ${
                  isSelected
                    ? "bg-slate-900/90 border-accent-cyan shadow-lg shadow-cyan-500/10 scale-[1.02]"
                    : "bg-obsidian-950/60 border-slate-800 hover:border-slate-700 hover:bg-slate-900/40"
                }`}
              >
                {isSelected && (
                  <div className="absolute top-4 right-4 w-6 h-6 rounded-full bg-accent-cyan flex items-center justify-center text-obsidian-950">
                    <Check className="w-3.5 h-3.5 stroke-[3]" />
                  </div>
                )}
                <div className={`w-10 h-10 rounded-[14px] bg-gradient-to-br ${st.color} flex items-center justify-center text-white mb-3 shadow-md`}>
                  <Icon className="w-5 h-5" />
                </div>
                <h4 className="font-bold text-white text-base mb-1">{st.label}</h4>
                <p className="text-xs text-slate-400 leading-relaxed">{st.description}</p>
              </div>
            );
          })}
        </div>

        <button
          onClick={() => onSave(selectedStyle)}
          className="w-full py-4 rounded-full bg-accent-cyan text-obsidian-950 font-black text-base hover:brightness-110 shadow-lg shadow-cyan-500/25 transition-all duration-200 hover:scale-[1.01]"
        >
          Confirm & Launch Cockpit
        </button>
      </div>
    </div>
  );
}
