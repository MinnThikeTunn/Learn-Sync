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
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-brand-secondary/40 backdrop-blur-md animate-in fade-in duration-200">
      <div className="bg-white max-w-xl w-full p-8 border border-brand-outline-variant shadow-elevation-lg rounded-[32px] relative">
        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute top-6 right-6 p-2 rounded-full text-brand-on-surface-variant hover:text-brand-secondary hover:bg-brand-surface-dim transition-colors"
        >
          <X className="w-5 h-5" />
        </button>

        {/* Header with Icon & Timer */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-[18px] bg-brand-tertiary-container border border-brand-tertiary/40 flex items-center justify-center text-brand-on-tertiary-container">
              <ShieldAlert className="w-6 h-6 text-brand-secondary" />
            </div>
            <div>
              <span className="text-xs font-bold uppercase tracking-wider text-amber-700">Burnout Guard Active</span>
              <h3 className="text-xl font-black text-brand-secondary">{title}</h3>
            </div>
          </div>

          <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-brand-surface-dim border border-brand-outline-variant text-brand-secondary font-mono text-sm font-bold">
            <Clock className="w-4 h-4 text-amber-600" />
            <span>{secondsRemaining}s</span>
          </div>
        </div>

        {/* Prompt Body */}
        <div className="p-4 rounded-[20px] bg-brand-surface-dim border border-brand-outline-variant text-sm text-brand-secondary leading-relaxed mb-6">
          <p>{prompt}</p>
        </div>

        {/* Micro-task Input Area */}
        <div className="space-y-4">
          <textarea
            value={userResponse}
            onChange={(e) => setUserResponse(e.target.value)}
            placeholder="Type your quick 1-sentence concept takeaway or answer here..."
            className="w-full h-24 p-4 rounded-[16px] bg-white border border-brand-outline-variant text-brand-secondary placeholder:text-brand-on-surface-variant/50 text-sm focus:outline-none focus:border-brand-primary focus:ring-2 focus:ring-brand-primary/10 transition-colors resize-none"
          />

          <button
            onClick={handleComplete}
            disabled={isCompleted}
            className={`w-full py-3.5 px-6 rounded-md font-bold text-sm flex items-center justify-center gap-2 transition-all duration-150 ${
              isCompleted
                ? "bg-emerald-600 text-white font-black scale-95"
                : "bg-brand-tertiary hover:bg-brand-tertiary-dim text-brand-on-tertiary shadow-cta-glow"
            }`}
          >
            {isCompleted ? (
              <>
                <CheckCircle2 className="w-5 h-5 text-white" />
                <span>Micro-Task Completed! Resuming Free Session...</span>
              </>
            ) : (
              <>
                <Sparkles className="w-5 h-5 text-brand-secondary" />
                <span>Complete 90s Micro-Task</span>
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
