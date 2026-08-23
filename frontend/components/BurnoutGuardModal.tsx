"use client";

import { useState, useEffect } from "react";
import { ShieldAlert, CheckCircle2, Clock, X, Sparkles } from "lucide-react";

interface BurnoutGuardModalProps {
  isOpen: boolean;
  onClose: () => void;
  title?: string;
  prompt?: string;
  durationSeconds?: number;
}

export default function BurnoutGuardModal({
  isOpen,
  onClose,
  title = "90-Second Reset & Single Concept Anchor",
  prompt = "You have an acute deadline cluster ahead. Let's execute a frictionless 90-second micro-task: summarize the core invariant of your next exam topic in 1 sentence, then take a deep breath.",
  durationSeconds = 90,
}: BurnoutGuardModalProps) {
  const [secondsRemaining, setSecondsRemaining] = useState(durationSeconds);
  const [isCompleted, setIsCompleted] = useState(false);
  const [userResponse, setUserResponse] = useState("");

  useEffect(() => {
    if (!isOpen || isCompleted) return;
    const timer = setInterval(() => {
      setSecondsRemaining((prev) => {
        if (prev <= 1) {
          clearInterval(timer);
          return 0;
        }
        return prev - 1;
      });
    }, 1000);
    return () => clearInterval(timer);
  }, [isOpen, isCompleted]);

  if (!isOpen) return null;

  const handleComplete = () => {
    setIsCompleted(true);
    setTimeout(() => {
      onClose();
      setIsCompleted(false);
      setSecondsRemaining(durationSeconds);
      setUserResponse("");
    }, 1200);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-obsidian-950/80 backdrop-blur-md animate-in fade-in duration-200">
      <div className="glass-card max-w-xl w-full p-8 border border-amber-500/40 shadow-2xl shadow-amber-500/10 relative">
        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute top-6 right-6 p-2 rounded-full text-slate-400 hover:text-white hover:bg-slate-800/60 transition-colors"
        >
          <X className="w-5 h-5" />
        </button>

        {/* Header with Icon & Timer */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-[18px] bg-amber-500/20 border border-amber-500/40 flex items-center justify-center text-amber-400">
              <ShieldAlert className="w-6 h-6" />
            </div>
            <div>
              <span className="text-xs font-bold uppercase tracking-wider text-amber-400">Burnout Guard Active</span>
              <h3 className="text-xl font-black text-white">{title}</h3>
            </div>
          </div>

          <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-slate-900 border border-slate-800 text-amber-300 font-mono text-sm font-bold">
            <Clock className="w-4 h-4" />
            <span>{secondsRemaining}s</span>
          </div>
        </div>

        {/* Prompt Body */}
        <div className="p-4 rounded-[20px] bg-obsidian-950/80 border border-slate-800 text-sm text-slate-200 leading-relaxed mb-6">
          <p>{prompt}</p>
        </div>

        {/* Micro-task Input Area */}
        <div className="space-y-4">
          <textarea
            value={userResponse}
            onChange={(e) => setUserResponse(e.target.value)}
            placeholder="Type your quick 1-sentence concept takeaway or answer here..."
            className="w-full h-24 p-4 rounded-[20px] bg-slate-900/90 border border-slate-800 text-slate-100 placeholder-slate-500 text-sm focus:outline-none focus:border-amber-500/60 transition-colors resize-none"
          />

          <button
            onClick={handleComplete}
            disabled={isCompleted}
            className={`w-full py-3.5 px-6 rounded-full font-bold text-sm flex items-center justify-center gap-2 transition-all duration-200 ${
              isCompleted
                ? "bg-emerald-500 text-obsidian-950 font-black scale-95"
                : "bg-gradient-to-r from-amber-500 to-orange-500 text-obsidian-950 hover:brightness-110 shadow-lg shadow-amber-500/20"
            }`}
          >
            {isCompleted ? (
              <>
                <CheckCircle2 className="w-5 h-5" />
                <span>Micro-Task Completed! Resuming Free Session...</span>
              </>
            ) : (
              <>
                <Sparkles className="w-5 h-5" />
                <span>Complete 90s Micro-Task</span>
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
