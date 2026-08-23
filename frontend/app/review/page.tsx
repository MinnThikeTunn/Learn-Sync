"use client";

import { useState } from "react";
import { 
  BrainCircuit, 
  Sparkles, 
  RotateCw, 
  CheckCircle2, 
  AlertTriangle, 
  Clock, 
  ShieldAlert,
  ArrowRight,
  Flame,
  Activity
} from "lucide-react";
import Navbar from "@/components/Navbar";

export default function ReviewPage() {
  const [tab, setTab] = useState<"flashcards" | "feynman">("flashcards");
  const [cardIndex, setCardIndex] = useState(0);
  const [isFlipped, setIsFlipped] = useState(false);
  const [explanation, setExplanation] = useState("");
  const [isEvaluating, setIsEvaluating] = useState(false);
  const [feynmanFeedback, setFeynmanFeedback] = useState<any>(null);

  const sampleCards = [
    {
      id: "c1",
      front: "What is a base case in recursion?",
      back: "The stopping condition in a recursive function that returns a value directly without spawning further recursive calls, preventing call stack overflow.",
      stability: 3.2,
      difficulty: 4.5,
      lapses: 0,
      isLeech: false,
      folder: "/CS101/Week_03_Recursion",
    },
    {
      id: "c2",
      front: "Why can't call stack frames be stored in permanent hard disk storage?",
      back: "Stack allocation requires microsecond low-latency L1/L2 cache and RAM access. Disk I/O latency is orders of magnitude too slow for routine call frames.",
      stability: 1.1,
      difficulty: 8.0,
      lapses: 4,
      isLeech: true,
      folder: "/CS101/Week_03_Recursion",
    },
  ];

  const currentCard = sampleCards[cardIndex % sampleCards.length];

  const handleNextCard = (rating: string) => {
    setIsFlipped(false);
    setCardIndex((prev) => prev + 1);
  };

  const handleEvaluateFeynman = () => {
    setIsEvaluating(true);
    setTimeout(() => {
      setIsEvaluating(false);
      setFeynmanFeedback({
        score: 0.88,
        is_sufficient: true,
        feedback: "Outstanding plain-language analogy! You clearly articulated the stopping base case and the memory unwinding process.",
        missing_concepts: [],
        misconceptions: [],
      });
    }, 1200);
  };

  return (
    <div className="min-h-screen flex flex-col bg-obsidian-950">
      <Navbar />

      <main className="flex-1 max-w-7xl w-full mx-auto px-6 py-8 space-y-8">
        {/* Header & Tabs */}
        <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4">
          <div>
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-slate-900 border border-slate-800 text-xs font-semibold text-accent-emerald mb-2">
              <BrainCircuit className="w-3.5 h-3.5" />
              <span>Cognitive Mastery & Active Recall Arena</span>
            </div>
            <h1 className="text-4xl font-black text-white tracking-tight">Review Deck & Feynman Loop</h1>
            <p className="text-slate-400 text-sm mt-1">
              Spaced repetition powered by py-fsrs scheduler with leech quarantine and active recall plain-language precision gap analysis.
            </p>
          </div>

          <div className="flex items-center gap-2 p-1.5 rounded-full bg-obsidian-900 border border-slate-800">
            <button
              onClick={() => setTab("flashcards")}
              className={`px-4 py-1.5 rounded-full text-xs font-bold transition-all ${
                tab === "flashcards" ? "bg-emerald-500 text-obsidian-950 font-black shadow" : "text-slate-400 hover:text-white"
              }`}
            >
              FSRS Flashcards
            </button>
            <button
              onClick={() => setTab("feynman")}
              className={`px-4 py-1.5 rounded-full text-xs font-bold transition-all ${
                tab === "feynman" ? "bg-accent-indigo text-white font-black shadow" : "text-slate-400 hover:text-white"
              }`}
            >
              Feynman Active Recall
            </button>
          </div>
        </div>

        {/* Tab 1: py-fsrs Spaced Repetition Review Deck */}
        {tab === "flashcards" && (
          <div className="max-w-2xl mx-auto space-y-6">
            {/* Flashcard Card View (Perplexity aesthetic rounded-[32px]) */}
            <div
              onClick={() => setIsFlipped(!isFlipped)}
              className={`glass-card p-10 min-h-[320px] flex flex-col justify-between cursor-pointer border transition-all duration-300 hover:border-slate-600 relative ${
                currentCard.isLeech ? "border-rose-500/50 bg-rose-950/10" : ""
              }`}
            >
              {/* Leech Badge */}
              {currentCard.isLeech && (
                <div className="absolute top-6 right-6 flex items-center gap-1 px-3 py-1 rounded-full bg-rose-500/20 border border-rose-500/40 text-rose-400 text-xs font-bold">
                  <AlertTriangle className="w-3.5 h-3.5" />
                  <span>Leech Quarantined ({currentCard.lapses} Lapses)</span>
                </div>
              )}

              <div>
                <span className="text-xs font-bold font-mono text-slate-400 block mb-3">{currentCard.folder}</span>
                <span className="text-xs font-bold uppercase tracking-wider text-accent-cyan block mb-2">
                  {isFlipped ? "Answer / Explanation" : "Question / Prompt"}
                </span>
                <h3 className="text-2xl font-black text-white leading-snug">
                  {isFlipped ? currentCard.back : currentCard.front}
                </h3>
              </div>

              <div className="flex items-center justify-between pt-6 border-t border-slate-800/80 text-xs text-slate-400 font-mono">
                <span>Stability: {currentCard.stability}d</span>
                <span className="text-slate-500">Click to flip</span>
              </div>
            </div>

            {/* FSRS Rating Buttons (Again, Hard, Good, Easy) */}
            <div className="grid grid-cols-4 gap-3">
              <button
                onClick={() => handleNextCard("again")}
                className="py-3 px-4 rounded-[18px] bg-rose-500/10 hover:bg-rose-500/20 border border-rose-500/30 text-rose-400 font-bold text-xs flex flex-col items-center gap-1 transition-all"
              >
                <span>Again</span>
                <span className="text-[10px] opacity-70 font-mono">10 min</span>
              </button>
              <button
                onClick={() => handleNextCard("hard")}
                className="py-3 px-4 rounded-[18px] bg-amber-500/10 hover:bg-amber-500/20 border border-amber-500/30 text-amber-400 font-bold text-xs flex flex-col items-center gap-1 transition-all"
              >
                <span>Hard</span>
                <span className="text-[10px] opacity-70 font-mono">1.2d</span>
              </button>
              <button
                onClick={() => handleNextCard("good")}
                className="py-3 px-4 rounded-[18px] bg-emerald-500/10 hover:bg-emerald-500/20 border border-emerald-500/30 text-emerald-400 font-bold text-xs flex flex-col items-center gap-1 transition-all"
              >
                <span>Good</span>
                <span className="text-[10px] opacity-70 font-mono">3.5d</span>
              </button>
              <button
                onClick={() => handleNextCard("easy")}
                className="py-3 px-4 rounded-[18px] bg-cyan-500/10 hover:bg-cyan-500/20 border border-cyan-500/30 text-accent-cyan font-bold text-xs flex flex-col items-center gap-1 transition-all"
              >
                <span>Easy</span>
                <span className="text-[10px] opacity-70 font-mono">7.0d</span>
              </button>
            </div>
          </div>
        )}

        {/* Tab 2: Feynman Active Recall Loop */}
        {tab === "feynman" && (
          <div className="max-w-3xl mx-auto space-y-6">
            <div className="glass-card p-8 space-y-4">
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-accent-indigo text-xs font-bold uppercase tracking-wider">
                <Sparkles className="w-3.5 h-3.5" />
                <span>Active Recall Challenge</span>
              </div>
              <h3 className="text-2xl font-black text-white">
                Explain "Recursion Call Stack" to a 10-Year-Old Child
              </h3>
              <p className="text-xs text-slate-400 leading-relaxed">
                Use a simple real-world analogy. Avoid technical jargon. Explain how the function remembers where to return and when it stops.
              </p>

              <textarea
                value={explanation}
                onChange={(e) => setExplanation(e.target.value)}
                placeholder="Type your intuitive explanation here..."
                className="w-full h-36 p-4 rounded-[20px] bg-slate-900 border border-slate-800 text-slate-100 placeholder-slate-500 text-sm focus:outline-none focus:border-indigo-500/60 transition-colors resize-none"
              />

              <button
                onClick={handleEvaluateFeynman}
                disabled={isEvaluating || !explanation}
                className="w-full py-3.5 rounded-full bg-accent-indigo text-white font-bold text-sm hover:brightness-110 shadow-lg shadow-indigo-500/25 transition-all"
              >
                {isEvaluating ? "Analyzing Precision Gaps..." : "Submit Explanation for Evaluation"}
              </button>
            </div>

            {/* Precision Gap Evaluation Result */}
            {feynmanFeedback && (
              <div className="glass-card p-6 border border-emerald-500/30 bg-emerald-950/10 space-y-4 animate-in fade-in duration-300">
                <div className="flex items-center justify-between border-b border-slate-800/80 pb-3">
                  <div className="flex items-center gap-2">
                    <CheckCircle2 className="w-5 h-5 text-emerald-400" />
                    <h4 className="text-base font-black text-white">
                      Evaluation Result: {(feynmanFeedback.score * 100).toFixed(0)}% Mastery
                    </h4>
                  </div>
                  <span className="px-3 py-1 rounded-full bg-emerald-500/20 text-emerald-300 font-bold text-xs">
                    Concept Mastered
                  </span>
                </div>
                <p className="text-sm text-slate-200">{feynmanFeedback.feedback}</p>
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  );
}
