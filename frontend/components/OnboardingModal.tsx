"use client";

import { useState, useEffect } from "react";
import {
  Eye,
  Headphones,
  BookOpen,
  Code2,
  Sparkles,
  Check,
  Loader2,
  ArrowRight,
  ArrowLeft,
  Zap,
  Play,
  RotateCcw,
} from "lucide-react";
import { useAuth } from "../context/AuthContext";

export type LearningStyleType = "visual" | "auditory" | "read_write" | "kinesthetic";

interface OnboardingModalProps {
  isOpen: boolean;
  onSave: (style: LearningStyleType) => void;
}

interface QuestionScenario {
  id: string;
  stepTitle: string;
  question: string;
  subtitle: string;
  options: {
    code: "V" | "A" | "R" | "K";
    style: LearningStyleType;
    icon: any;
    title: string;
    description: string;
    badge: string;
    color: string;
  }[];
}

const SCENARIOS: QuestionScenario[] = [
  {
    id: "q1_ingestion",
    stepTitle: "Scenario 1 of 4: Ingesting Theory",
    question: "How do you grasp a brand-new, complex architecture or theory fastest?",
    subtitle: "Select the format that naturally clicks with your mental models.",
    options: [
      {
        code: "V",
        style: "visual",
        icon: Eye,
        title: "Visual Architecture",
        description: "Flowcharts, sequence diagrams, and visual maps connecting components.",
        badge: "Spatial / Visual",
        color: "from-cyan-500 to-blue-600",
      },
      {
        code: "A",
        style: "auditory",
        icon: Headphones,
        title: "Conversational Dialogue",
        description: "Socratic Q&A, audio breakdown, or podcast-style conceptual discussions.",
        badge: "Verbal / Dialogue",
        color: "from-purple-500 to-indigo-600",
      },
      {
        code: "R",
        style: "read_write",
        icon: BookOpen,
        title: "Structured Documentation",
        description: "Hierarchical markdown notes, formal definitions, and bulleted takeaways.",
        badge: "Textual / Outline",
        color: "from-emerald-500 to-teal-600",
      },
      {
        code: "K",
        style: "kinesthetic",
        icon: Code2,
        title: "Hands-on Sandbox",
        description: "Jumping directly into interactive code playgrounds or experimental labs.",
        badge: "Hands-on / Build",
        color: "from-amber-500 to-orange-600",
      },
    ],
  },
  {
    id: "q2_unblocking",
    stepTitle: "Scenario 2 of 4: Overcoming Blockers",
    question: "When struggling with a difficult problem late at night, what unblocks you?",
    subtitle: "Think about the quickest way you diagnose where your understanding broke.",
    options: [
      {
        code: "V",
        style: "visual",
        icon: Eye,
        title: "Visual State Tracing",
        description: "An annotated diagram tracing input-to-output data transitions.",
        badge: "Trace Diagram",
        color: "from-cyan-500 to-blue-600",
      },
      {
        code: "A",
        style: "auditory",
        icon: Headphones,
        title: "Socratic Inquirer",
        description: "A verbal question-and-answer prompt guiding me to the logical flaw.",
        badge: "Interactive Audio",
        color: "from-purple-500 to-indigo-600",
      },
      {
        code: "R",
        style: "read_write",
        icon: BookOpen,
        title: "Technical Walkthrough",
        description: "A detailed written guide with edge cases, proofs, and references.",
        badge: "In-depth Guide",
        color: "from-emerald-500 to-teal-600",
      },
      {
        code: "K",
        style: "kinesthetic",
        icon: Code2,
        title: "Micro Bug-Fix Puzzle",
        description: "A minimal runnable reproduction snippet where I can fix failing tests.",
        badge: "Code Snippet",
        color: "from-amber-500 to-orange-600",
      },
    ],
  },
  {
    id: "q3_crunch",
    stepTitle: "Scenario 3 of 4: 15-Minute Exam Crunch",
    question: "You have 15 minutes before an exam. What study artifact gives you peak confidence?",
    subtitle: "Directly coupled with LearnSync's Busy Mode high-stress relief engine.",
    options: [
      {
        code: "V",
        style: "visual",
        icon: Eye,
        title: "High-Contrast Cheat Sheet",
        description: "Color-coded diagram cards highlighting core relationship maps.",
        badge: "Visual Map",
        color: "from-cyan-500 to-blue-600",
      },
      {
        code: "A",
        style: "auditory",
        icon: Headphones,
        title: "30s Rapid Audio Recap",
        description: "High-yield rapid audio summary to listen to while walking into class.",
        badge: "Quick Audio",
        color: "from-purple-500 to-indigo-600",
      },
      {
        code: "R",
        style: "read_write",
        icon: BookOpen,
        title: "Pareto 80/20 Bullet List",
        description: "Condensed 1-page summary of core formulas, definitions, and primitives.",
        badge: "Key Terms",
        color: "from-emerald-500 to-teal-600",
      },
      {
        code: "K",
        style: "kinesthetic",
        icon: Code2,
        title: "Rapid-Fire Syntax Challenge",
        description: "3 rapid interactive snippet challenges verifying mechanical recall.",
        badge: "Snippet Quiz",
        color: "from-amber-500 to-orange-600",
      },
    ],
  },
  {
    id: "q4_retention",
    stepTitle: "Scenario 4 of 4: Long-Term Recall",
    question: "When reviewing materials weeks later, what makes the concepts permanently stick?",
    subtitle: "Determines your Feynman Loop active recall and flashcard generation style.",
    options: [
      {
        code: "V",
        style: "visual",
        icon: Eye,
        title: "Spatial Mind Map",
        description: "Rebuilding a mental hierarchy or concept tree across course modules.",
        badge: "Concept Map",
        color: "from-cyan-500 to-blue-600",
      },
      {
        code: "A",
        style: "auditory",
        icon: Headphones,
        title: "Explaining Out Loud",
        description: "Explaining the concept out loud and receiving verbal corrective prompts.",
        badge: "Voice Feynman",
        color: "from-purple-500 to-indigo-600",
      },
      {
        code: "R",
        style: "read_write",
        icon: BookOpen,
        title: "Personalized Markdown Notes",
        description: "Writing and refining comprehensive notes with active recall flashcards.",
        badge: "Flashcards",
        color: "from-emerald-500 to-teal-600",
      },
      {
        code: "K",
        style: "kinesthetic",
        icon: Code2,
        title: "Building From Scratch",
        description: "Writing clean implementations and passing test suites without assistance.",
        badge: "Build Lab",
        color: "from-amber-500 to-orange-600",
      },
    ],
  },
];

const ARCHETYPE_METADATA: Record<
  LearningStyleType,
  {
    name: string;
    badge: string;
    tagline: string;
    description: string;
    color: string;
  }
> = {
  visual: {
    name: "Visual Architect",
    badge: "Spatial & Structural Thinker",
    tagline: "Your brain naturally maps ideas into visual graphs and diagrams.",
    description:
      "LearnSync AI will generate interactive Mermaid flowcharts, SVG architectural maps, and high-contrast visual cheat sheets.",
    color: "from-cyan-500 to-blue-600",
  },
  auditory: {
    name: "Socratic Inquirer",
    badge: "Conversational & Verbal Thinker",
    tagline: "You process ideas best through discussion and dialogue.",
    description:
      "LearnSync AI will prioritize Socratic audio dialogues, podcast-style explanations, and 30-second rapid verbal recaps.",
    color: "from-purple-500 to-indigo-600",
  },
  read_write: {
    name: "Analytical Scribe",
    badge: "Textual & Precision Thinker",
    tagline: "You thrive on comprehensive written prose and structured documentation.",
    description:
      "LearnSync AI will produce deep structured markdown study guides, formal definitions, and Pareto 80/20 bullet summaries.",
    color: "from-emerald-500 to-teal-600",
  },
  kinesthetic: {
    name: "Pragmatic Hacker",
    badge: "Hands-on & Experimental Thinker",
    tagline: "You learn by building, modifying code, and breaking things.",
    description:
      "LearnSync AI will prioritize interactive code sandboxes, runnable test suites, and micro-snippet bug fixes.",
    color: "from-amber-500 to-orange-600",
  },
};

export default function OnboardingModal({ isOpen, onSave }: OnboardingModalProps) {
  const { user, profile, updateProfile } = useAuth();
  const [currentStep, setCurrentStep] = useState<number>(0); // 0..3: Questions, 4: Live Preview
  const [answers, setAnswers] = useState<Record<number, "V" | "A" | "R" | "K">>({});
  const [diagnosedStyle, setDiagnosedStyle] = useState<LearningStyleType>(
    (profile?.learning_style as LearningStyleType) || "visual"
  );
  const [secondaryStyle, setSecondaryStyle] = useState<LearningStyleType | null>(null);
  const [scores, setScores] = useState<Record<string, number>>({
    visual: 0,
    auditory: 0,
    read_write: 0,
    kinesthetic: 0,
  });
  const [saving, setSaving] = useState(false);
  const [simulatedSandboxOutput, setSimulatedSandboxOutput] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen) {
      if (profile?.learning_style) {
        setDiagnosedStyle(profile.learning_style as LearningStyleType);
      } else if (typeof window !== "undefined") {
        const cached = localStorage.getItem("learnsync_learning_style");
        if (cached) {
          setDiagnosedStyle(cached as LearningStyleType);
        }
      }
    }
  }, [isOpen, profile?.learning_style]);

  if (!isOpen) return null;

  const currentScenario = SCENARIOS[currentStep];

  const handleSelectOption = (code: "V" | "A" | "R" | "K") => {
    const updatedAnswers = { ...answers, [currentStep]: code };
    setAnswers(updatedAnswers);

    if (currentStep < 3) {
      setCurrentStep((prev) => prev + 1);
    } else {
      // Completed question 4 -> Calculate Diagnostic
      evaluateAndShowPreview(updatedAnswers);
    }
  };

  const evaluateAndShowPreview = (finalAnswers: Record<number, "V" | "A" | "R" | "K">) => {
    const counts: Record<string, number> = {
      visual: 0,
      auditory: 0,
      read_write: 0,
      kinesthetic: 0,
    };
    const mapping: Record<string, LearningStyleType> = {
      V: "visual",
      A: "auditory",
      R: "read_write",
      K: "kinesthetic",
    };

    Object.values(finalAnswers).forEach((c) => {
      const st = mapping[c];
      if (st) counts[st] = (counts[st] || 0) + 1;
    });

    setScores(counts);

    // Rank descending
    const ranked = (Object.keys(counts) as LearningStyleType[]).sort((a, b) => counts[b] - counts[a]);
    const topPrimary = ranked[0];
    const topSecondary = counts[ranked[1]] > 0 ? ranked[1] : null;

    setDiagnosedStyle(topPrimary);
    setSecondaryStyle(topSecondary);
    setCurrentStep(4); // Advance to preview
  };

  const handleSkipToDefault = () => {
    setDiagnosedStyle("read_write");
    setSecondaryStyle("visual");
    setCurrentStep(4);
  };

  const handleConfirmAndSave = async () => {
    setSaving(true);
    try {
      // 1. Submit to FastAPI onboarding assessment backend if available
      try {
        const responseList = Object.keys(answers)
          .sort()
          .map((k) => answers[Number(k)]);

        if (responseList.length > 0) {
          await fetch("http://localhost:8000/api/v1/onboarding/assessment", {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              "X-Test-User-Id": user?.id || "demo-user",
            },
            body: JSON.stringify({ responses: responseList }),
          });
        }
      } catch (backendErr) {
        console.warn("Backend assessment sync notification skipped:", backendErr);
      }

      // 2. Persist directly to Supabase profiles via AuthContext
      await updateProfile({
        learning_style: diagnosedStyle,
        secondary_learning_style: secondaryStyle,
        assessment_scores: scores,
        onboarding_completed: true,
      });
    } catch (e) {
      console.error("Failed to save profile during onboarding:", e);
    } finally {
      setSaving(false);
      onSave(diagnosedStyle);
    }
  };

  const archetype = ARCHETYPE_METADATA[diagnosedStyle] || ARCHETYPE_METADATA.visual;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-brand-secondary/50 backdrop-blur-md animate-in fade-in duration-200">
      <div className="bg-white max-w-3xl w-full p-6 sm:p-9 border border-brand-outline-variant shadow-elevation-lg rounded-[32px] relative overflow-hidden transition-all duration-300">
        {/* Step Indicator Header */}
        <div className="flex items-center justify-between mb-6 pb-4 border-b border-brand-outline-variant/60">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-full bg-brand-tertiary-container border border-brand-tertiary/40 flex items-center justify-center">
              <Sparkles className="w-4 h-4 text-brand-secondary" />
            </div>
            <div>
              <span className="text-xs font-black text-brand-on-surface-variant uppercase tracking-wider">
                LearnSync Adaptive Co-Pilot Setup
              </span>
              <p className="text-xs text-brand-on-surface-variant/70 font-medium">
                {currentStep < 4 ? `Step ${currentStep + 1} of 4 • < 30s` : "Diagnostic Result & Preview"}
              </p>
            </div>
          </div>

          {currentStep < 4 && (
            <button
              onClick={handleSkipToDefault}
              className="text-xs text-brand-on-surface-variant hover:text-brand-secondary font-bold underline decoration-dotted transition-colors"
            >
              Skip to Default
            </button>
          )}
        </div>

        {/* Progress Pill Bar */}
        <div className="w-full grid grid-cols-4 gap-2 mb-8">
          {[0, 1, 2, 3].map((stepIdx) => (
            <div
              key={stepIdx}
              className={`h-1.5 rounded-full transition-all duration-300 ${
                stepIdx < currentStep || currentStep === 4
                  ? "bg-brand-secondary"
                  : stepIdx === currentStep
                  ? "bg-brand-primary"
                  : "bg-brand-surface-dim border border-brand-outline-variant/40"
              }`}
            />
          ))}
        </div>

        {/* QUESTIONS VIEW (Steps 0 - 3) */}
        {currentStep < 4 && (
          <div className="animate-in fade-in slide-in-from-right-3 duration-200">
            <div className="mb-6">
              <span className="inline-block px-3 py-1 rounded-full bg-brand-surface-dim text-brand-secondary text-xs font-black tracking-wide mb-2">
                {currentScenario.stepTitle}
              </span>
              <h2 className="text-2xl sm:text-3xl font-black text-brand-secondary tracking-tight leading-snug">
                {currentScenario.question}
              </h2>
              <p className="text-brand-on-surface-variant text-sm mt-1.5 leading-relaxed">
                {currentScenario.subtitle}
              </p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-6">
              {currentScenario.options.map((opt) => {
                const Icon = opt.icon;
                const isSelected = answers[currentStep] === opt.code;

                return (
                  <button
                    key={opt.code}
                    onClick={() => handleSelectOption(opt.code)}
                    className={`text-left p-5 rounded-[24px] cursor-pointer transition-all duration-150 border relative flex flex-col justify-between ${
                      isSelected
                        ? "bg-brand-surface-dim border-2 border-brand-primary shadow-elevation-md scale-[1.01]"
                        : "bg-white border-brand-outline-variant hover:border-brand-primary/60 hover:bg-brand-surface-dim/40 hover:shadow-sm"
                    }`}
                  >
                    <div>
                      <div className="flex items-center justify-between mb-3">
                        <div
                          className={`w-10 h-10 rounded-[14px] bg-gradient-to-br ${opt.color} flex items-center justify-center text-white shadow-sm`}
                        >
                          <Icon className="w-5 h-5" />
                        </div>
                        <span className="text-[11px] font-black uppercase tracking-wider px-2.5 py-0.5 rounded-full bg-brand-surface-dim text-brand-on-surface-variant border border-brand-outline-variant/50">
                          {opt.badge}
                        </span>
                      </div>
                      <h3 className="font-black text-brand-secondary text-base mb-1">
                        {opt.title}
                      </h3>
                      <p className="text-xs text-brand-on-surface-variant leading-relaxed">
                        {opt.description}
                      </p>
                    </div>

                    <div className="mt-4 flex items-center gap-1.5 text-xs font-bold text-brand-primary">
                      <span>Choose this method</span>
                      <ArrowRight className="w-3.5 h-3.5" />
                    </div>
                  </button>
                );
              })}
            </div>

            {currentStep > 0 && (
              <button
                onClick={() => setCurrentStep((prev) => prev - 1)}
                className="inline-flex items-center gap-1.5 text-xs font-bold text-brand-on-surface-variant hover:text-brand-secondary transition-colors"
              >
                <ArrowLeft className="w-3.5 h-3.5" />
                <span>Previous question</span>
              </button>
            )}
          </div>
        )}

        {/* STEP 4: LIVE ARTIFACT PREVIEW & CONFIRMATION */}
        {currentStep === 4 && (
          <div className="animate-in fade-in slide-in-from-bottom-3 duration-200">
            {/* Diagnosed Header */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-5 rounded-[24px] bg-brand-surface-dim border border-brand-outline-variant mb-6">
              <div className="flex items-center gap-3.5">
                <div
                  className={`w-12 h-12 rounded-[18px] bg-gradient-to-br ${archetype.color} flex items-center justify-center text-white shadow-md`}
                >
                  <Zap className="w-6 h-6" />
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-black text-brand-primary uppercase tracking-wider">
                      Diagnosed Archetype
                    </span>
                    <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-white text-brand-secondary border border-brand-outline-variant">
                      {archetype.badge}
                    </span>
                  </div>
                  <h3 className="text-2xl font-black text-brand-secondary tracking-tight">
                    {archetype.name}
                  </h3>
                </div>
              </div>

              {/* 1-Click Override chips */}
              <div className="flex flex-wrap items-center gap-1.5">
                {(["visual", "auditory", "read_write", "kinesthetic"] as LearningStyleType[]).map(
                  (styleKey) => (
                    <button
                      key={styleKey}
                      onClick={() => setDiagnosedStyle(styleKey)}
                      className={`px-3 py-1.5 rounded-full text-xs font-black capitalize transition-all ${
                        diagnosedStyle === styleKey
                          ? "bg-brand-secondary text-white shadow-sm"
                          : "bg-white text-brand-on-surface-variant hover:bg-brand-surface-dim border border-brand-outline-variant/60"
                      }`}
                    >
                      {styleKey.replace("_", " ")}
                    </button>
                  )
                )}
              </div>
            </div>

            <p className="text-xs text-brand-on-surface-variant font-medium mb-3">
              {archetype.description} Here is a live preview of how LearnSync AI will structure study material for{" "}
              <strong className="text-brand-secondary font-bold">Binary Search Trees</strong>:
            </p>

            {/* Dynamic Live Artifact Demonstration Card */}
            <div className="rounded-[24px] border border-brand-outline-variant bg-white p-5 shadow-sm mb-6 relative overflow-hidden">
              {/* VISUAL PREVIEW */}
              {diagnosedStyle === "visual" && (
                <div>
                  <div className="flex items-center justify-between mb-3 border-b border-brand-outline-variant/40 pb-2">
                    <span className="text-xs font-black text-brand-secondary flex items-center gap-2">
                      <Eye className="w-4 h-4 text-cyan-600" />
                      Visual Mode: Interactive Tree Graph (Free Mode)
                    </span>
                    <span className="text-[10px] font-bold text-brand-on-surface-variant bg-brand-surface-dim px-2 py-0.5 rounded-full">
                      Mermaid / SVG
                    </span>
                  </div>
                  <div className="py-4 flex flex-col items-center justify-center bg-[#0d1117] rounded-[16px] text-white">
                    <div className="flex flex-col items-center">
                      <div className="w-10 h-10 rounded-full bg-cyan-500/20 border-2 border-cyan-400 flex items-center justify-center font-mono font-bold text-cyan-300 text-sm shadow-[0_0_12px_rgba(6,182,212,0.4)]">
                        50
                      </div>
                      <div className="w-0.5 h-4 bg-cyan-400/40" />
                    </div>
                    <div className="flex items-center gap-12 sm:gap-20">
                      <div className="flex flex-col items-center">
                        <div className="w-8 h-8 rounded-full bg-blue-500/20 border-2 border-blue-400 flex items-center justify-center font-mono font-bold text-blue-300 text-xs">
                          30
                        </div>
                        <span className="text-[10px] text-zinc-400 mt-1 font-mono">left &lt; 50</span>
                      </div>
                      <div className="flex flex-col items-center">
                        <div className="w-8 h-8 rounded-full bg-purple-500/20 border-2 border-purple-400 flex items-center justify-center font-mono font-bold text-purple-300 text-xs">
                          70
                        </div>
                        <span className="text-[10px] text-zinc-400 mt-1 font-mono">right &gt; 50</span>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* AUDITORY PREVIEW */}
              {diagnosedStyle === "auditory" && (
                <div>
                  <div className="flex items-center justify-between mb-3 border-b border-brand-outline-variant/40 pb-2">
                    <span className="text-xs font-black text-brand-secondary flex items-center gap-2">
                      <Headphones className="w-4 h-4 text-purple-600" />
                      Auditory Mode: Socratic Audio Dialogue Player
                    </span>
                    <span className="text-[10px] font-bold text-brand-on-surface-variant bg-brand-surface-dim px-2 py-0.5 rounded-full">
                      Audio / TTS
                    </span>
                  </div>
                  <div className="p-4 bg-purple-50/60 rounded-[16px] border border-purple-100 flex items-center gap-4">
                    <button className="w-11 h-11 rounded-full bg-purple-600 text-white flex items-center justify-center shadow-md hover:bg-purple-700 transition-transform active:scale-95">
                      <Play className="w-5 h-5 ml-0.5" />
                    </button>
                    <div className="flex-1">
                      <div className="flex items-center justify-between text-xs font-bold text-brand-secondary mb-1">
                        <span>Binary Search Tree Invariance (0:45)</span>
                        <span className="text-purple-600 font-mono">Socratic Voice</span>
                      </div>
                      {/* Animated Waveform Simulation */}
                      <div className="flex items-center gap-1 h-5">
                        {[12, 24, 18, 28, 14, 22, 10, 26, 16, 20, 30, 14, 22, 18, 12, 25].map(
                          (h, idx) => (
                            <div
                              key={idx}
                              style={{ height: `${h}px` }}
                              className="w-1 bg-purple-400 rounded-full animate-pulse"
                            />
                          )
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* READ / WRITE PREVIEW */}
              {diagnosedStyle === "read_write" && (
                <div>
                  <div className="flex items-center justify-between mb-3 border-b border-brand-outline-variant/40 pb-2">
                    <span className="text-xs font-black text-brand-secondary flex items-center gap-2">
                      <BookOpen className="w-4 h-4 text-emerald-600" />
                      Read / Write Mode: Structured Markdown Guide
                    </span>
                    <span className="text-[10px] font-bold text-brand-on-surface-variant bg-brand-surface-dim px-2 py-0.5 rounded-full">
                      Markdown / LaTeX
                    </span>
                  </div>
                  <div className="p-4 bg-emerald-50/40 rounded-[16px] border border-emerald-100 text-xs text-brand-secondary leading-relaxed font-mono">
                    <p className="font-bold text-emerald-800 mb-1">### 1. Invariance Property</p>
                    <p className="text-zinc-700 mb-2">
                      For any given node <code className="bg-emerald-100 px-1 rounded">N</code>:
                      all keys in <code className="bg-emerald-100 px-1 rounded">left(N) &lt; N.key</code> and all keys in{" "}
                      <code className="bg-emerald-100 px-1 rounded">right(N) &gt; N.key</code>.
                    </p>
                    <div className="bg-white p-2.5 rounded-[10px] border border-emerald-200/80 text-zinc-600">
                      • Average Search Complexity: <strong>O(log N)</strong>
                      <br />• Worst Case Degenerate Tree: <strong>O(N)</strong>
                    </div>
                  </div>
                </div>
              )}

              {/* KINESTHETIC PREVIEW */}
              {diagnosedStyle === "kinesthetic" && (
                <div>
                  <div className="flex items-center justify-between mb-3 border-b border-brand-outline-variant/40 pb-2">
                    <span className="text-xs font-black text-brand-secondary flex items-center gap-2">
                      <Code2 className="w-4 h-4 text-amber-600" />
                      Kinesthetic Mode: Interactive Sandbox Snippet
                    </span>
                    <button
                      onClick={() =>
                        setSimulatedSandboxOutput("✓ Tests Passed: insert(42) preserves BST property [1ms]")
                      }
                      className="text-[10px] font-black text-amber-900 bg-amber-200 hover:bg-amber-300 px-2.5 py-1 rounded-full flex items-center gap-1 transition-colors"
                    >
                      <Play className="w-3 h-3" />
                      Run Test Case
                    </button>
                  </div>
                  <div className="p-3.5 bg-[#1e1e1e] rounded-[16px] text-xs font-mono text-amber-100">
                    <p className="text-zinc-400">// Complete the insertion check:</p>
                    <p className="text-emerald-400">
                      def <span className="text-amber-300">insert</span>(root, val):
                    </p>
                    <p className="pl-4 text-zinc-300">
                      if not root: return Node(val)
                    </p>
                    <p className="pl-4 text-zinc-300">
                      if val &lt; root.val: root.left = insert(root.left, val)
                    </p>
                    {simulatedSandboxOutput && (
                      <div className="mt-2 pt-2 border-t border-zinc-700 text-emerald-400 font-bold">
                        {simulatedSandboxOutput}
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>

            {/* Launch Button */}
            <button
              onClick={handleConfirmAndSave}
              disabled={saving}
              className="w-full py-4 rounded-[18px] bg-brand-tertiary hover:bg-brand-tertiary-dim text-brand-secondary font-black text-base shadow-cta-glow transition-all duration-150 flex items-center justify-center gap-2 disabled:opacity-60"
            >
              {saving ? (
                <Loader2 className="w-5 h-5 animate-spin text-brand-secondary" />
              ) : (
                <div className="flex items-center gap-2">
                  <span>Save Diagnostic & Launch Cockpit</span>
                  <Check className="w-5 h-5 stroke-[2.5]" />
                </div>
              )}
            </button>

            <div className="mt-3 text-center">
              <button
                onClick={() => {
                  setAnswers({});
                  setCurrentStep(0);
                }}
                className="text-xs text-brand-on-surface-variant hover:text-brand-secondary inline-flex items-center gap-1 font-semibold"
              >
                <RotateCcw className="w-3 h-3" />
                Retake Assessment
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
