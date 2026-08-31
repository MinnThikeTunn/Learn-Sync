"use client";

import { useState } from "react";
import { Eye, Headphones, BookOpen, Code2, Sparkles, Check, Loader2 } from "lucide-react";
import { useAuth } from "../context/AuthContext";

export type LearningStyleType = "visual" | "auditory" | "read_write" | "kinesthetic";

interface OnboardingModalProps {
  isOpen: boolean;
  onSave: (style: LearningStyleType) => void;
}

export default function OnboardingModal({ isOpen, onSave }: OnboardingModalProps) {
  const { profile, updateProfile } = useAuth();
  const [selectedStyle, setSelectedStyle] = useState<LearningStyleType>(
    (profile?.learning_style as LearningStyleType) || "visual"
  );
  const [saving, setSaving] = useState(false);

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

  const handleConfirm = async () => {
    setSaving(true);
    try {
      await updateProfile({
        learning_style: selectedStyle as any,
        onboarding_completed: true,
      });
    } catch (e) {
      console.error("Failed to save profile during onboarding:", e);
    } finally {
      setSaving(false);
      onSave(selectedStyle);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-brand-secondary/40 backdrop-blur-md animate-in fade-in duration-200">
      <div className="bg-white max-w-2xl w-full p-6 sm:p-8 border border-brand-outline-variant shadow-elevation-lg rounded-[32px] relative">
        <div className="text-center mb-8">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-brand-tertiary-container border border-brand-tertiary/40 text-brand-on-tertiary-container text-xs font-bold uppercase tracking-wider mb-3">
            <Sparkles className="w-3.5 h-3.5 text-brand-secondary" />
            <span>Personalized Co-Pilot Setup</span>
          </div>
          <h2 className="text-2xl sm:text-3xl font-black text-brand-secondary tracking-tight">Select Your Learning Style</h2>
          <p className="text-brand-on-surface-variant text-sm max-w-md mx-auto mt-2 leading-relaxed">
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
                onClick={() => setSelectedStyle(st.id as LearningStyleType)}
                className={`p-5 rounded-[20px] cursor-pointer transition-all duration-150 border relative ${
                  isSelected
                    ? "bg-white border-2 border-brand-primary shadow-elevation-md scale-[1.02]"
                    : "bg-brand-surface-dim border-brand-outline-variant hover:border-brand-primary/40 hover:bg-white"
                }`}
              >
                {isSelected && (
                  <div className="absolute top-4 right-4 w-6 h-6 rounded-full bg-brand-primary flex items-center justify-center text-white">
                    <Check className="w-3.5 h-3.5 stroke-[3]" />
                  </div>
                )}
                <div className={`w-10 h-10 rounded-[14px] bg-gradient-to-br ${st.color} flex items-center justify-center text-white mb-3 shadow-md`}>
                  <Icon className="w-5 h-5" />
                </div>
                <h4 className="font-bold text-brand-secondary text-base mb-1">{st.label}</h4>
                <p className="text-xs text-brand-on-surface-variant leading-relaxed">{st.description}</p>
              </div>
            );
          })}
        </div>

        <button
          onClick={handleConfirm}
          disabled={saving}
          className="w-full py-3.5 rounded-[14px] bg-brand-tertiary hover:bg-brand-tertiary-dim text-brand-secondary font-black text-base shadow-cta-glow transition-all duration-150 flex items-center justify-center gap-2 disabled:opacity-60"
        >
          {saving ? (
            <Loader2 className="w-5 h-5 animate-spin text-brand-secondary" />
          ) : (
            <span>Confirm & Launch Cockpit</span>
          )}
        </button>
      </div>
    </div>
  );
}
