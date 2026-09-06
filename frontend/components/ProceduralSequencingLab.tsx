"use client";

import React, { useState } from "react";
import { 
  ArrowUp, 
  ArrowDown, 
  CheckCircle2, 
  XCircle, 
  RotateCcw, 
  Sparkles, 
  Dna, 
  Check
} from "lucide-react";

export interface SequencingItem {
  id: string;
  label: string;
  correct_order: number;
  rationale?: string;
}

export interface ProceduralSequencingLabProps {
  scenarioTitle: string;
  contextBrief: string;
  items: SequencingItem[];
  onComplete?: () => void;
  className?: string;
}

export default function ProceduralSequencingLab({
  scenarioTitle,
  contextBrief,
  items: initialItems,
  onComplete,
  className = "",
}: ProceduralSequencingLabProps) {
  // Scramble items initially
  const [items, setItems] = useState<SequencingItem[]>(() => {
    // Deterministic or pseudo-shuffle so it doesn't start in solved order
    const copy = [...initialItems];
    return copy.reverse();
  });

  const [hasVerified, setHasVerified] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);

  const handleMoveUp = (index: number) => {
    if (index === 0) return;
    setHasVerified(false);
    const updated = [...items];
    const temp = updated[index];
    updated[index] = updated[index - 1];
    updated[index - 1] = temp;
    setItems(updated);
  };

  const handleMoveDown = (index: number) => {
    if (index === items.length - 1) return;
    setHasVerified(false);
    const updated = [...items];
    const temp = updated[index];
    updated[index] = updated[index + 1];
    updated[index + 1] = temp;
    setItems(updated);
  };

  const handleVerify = () => {
    setHasVerified(true);
    const allCorrect = items.every((item, idx) => item.correct_order === idx + 1);
    setIsSuccess(allCorrect);
    if (allCorrect && onComplete) {
      onComplete();
    }
  };

  const handleReset = () => {
    setItems([...initialItems].reverse());
    setHasVerified(false);
    setIsSuccess(false);
  };

  return (
    <div
      className={`rounded-[32px] bg-white border border-brand-outline-variant shadow-elevation-md p-6 sm:p-8 space-y-6 ${className}`}
    >
      {/* 1. Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-brand-outline-variant gap-4">
        <div className="space-y-1">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-50 border border-emerald-200 text-xs font-bold text-emerald-700">
            <Dna className="w-3.5 h-3.5 text-emerald-600" />
            <span>Procedural Pathway Sequencing Lab</span>
          </div>
          <h3 className="text-xl sm:text-2xl font-black text-brand-secondary tracking-tight">
            {scenarioTitle}
          </h3>
          <p className="text-xs text-brand-on-surface-variant font-medium max-w-2xl">
            {contextBrief}
          </p>
        </div>

        <button
          onClick={handleReset}
          className="flex items-center gap-1 self-start sm:self-center px-3 py-1.5 rounded-full bg-brand-surface-dim hover:bg-brand-surface-variant text-brand-on-surface-variant transition-all text-xs font-bold cursor-pointer"
        >
          <RotateCcw className="w-3 h-3" />
          <span>Reset Order</span>
        </button>
      </div>

      {/* 2. Interactive Steps List */}
      <div className="space-y-3">
        <div className="flex items-center justify-between text-xs font-bold text-brand-on-surface-variant uppercase tracking-wider pl-1">
          <span>Arrange steps into correct biological / procedural order:</span>
          <span>{items.length} Stages</span>
        </div>

        <div className="space-y-2.5">
          {items.map((item, idx) => {
            const isCorrectPosition = item.correct_order === idx + 1;
            return (
              <div
                key={item.id}
                className={`p-4 rounded-[20px] border transition-all flex items-center justify-between gap-4 ${
                  hasVerified
                    ? isCorrectPosition
                      ? "bg-emerald-50/80 border-2 border-emerald-500 shadow-xs"
                      : "bg-rose-50/80 border-2 border-rose-400 shadow-xs"
                    : "bg-white border-brand-outline-variant hover:border-brand-primary/40 shadow-xs"
                }`}
              >
                <div className="flex items-center gap-3.5 flex-1 min-w-0">
                  <span
                    className={`w-7 h-7 rounded-full flex items-center justify-center shrink-0 font-bold text-xs ${
                      hasVerified
                        ? isCorrectPosition
                          ? "bg-emerald-600 text-white"
                          : "bg-rose-600 text-white"
                        : "bg-brand-surface-dim border border-brand-outline-variant text-brand-secondary"
                    }`}
                  >
                    {idx + 1}
                  </span>
                  <div className="space-y-0.5 min-w-0">
                    <div className="text-xs sm:text-sm font-bold text-brand-secondary leading-snug">
                      {item.label}
                    </div>
                    {hasVerified && item.rationale && (
                      <p className="text-[11px] text-brand-on-surface-variant font-medium">
                        {item.rationale}
                      </p>
                    )}
                  </div>
                </div>

                {/* Move Controls */}
                <div className="flex items-center gap-1 shrink-0">
                  <button
                    onClick={() => handleMoveUp(idx)}
                    disabled={idx === 0}
                    className="p-1.5 rounded-lg border border-brand-outline-variant bg-brand-surface-dim hover:bg-brand-surface-variant text-brand-secondary transition-all disabled:opacity-30 cursor-pointer"
                    title="Move Step Up"
                  >
                    <ArrowUp className="w-3.5 h-3.5" />
                  </button>
                  <button
                    onClick={() => handleMoveDown(idx)}
                    disabled={idx === items.length - 1}
                    className="p-1.5 rounded-lg border border-brand-outline-variant bg-brand-surface-dim hover:bg-brand-surface-variant text-brand-secondary transition-all disabled:opacity-30 cursor-pointer"
                    title="Move Step Down"
                  >
                    <ArrowDown className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* 3. Actions & Verification Banner */}
      <div className="pt-2 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        {hasVerified && (
          <div
            className={`flex items-center gap-2 text-xs font-bold px-4 py-2 rounded-full ${
              isSuccess
                ? "bg-emerald-100 text-emerald-900 border border-emerald-300"
                : "bg-amber-100 text-amber-900 border border-amber-300"
            }`}
          >
            {isSuccess ? (
              <>
                <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                <span>Perfect! All {items.length} steps sequenced correctly.</span>
              </>
            ) : (
              <>
                <XCircle className="w-4 h-4 text-amber-700" />
                <span>Some steps are out of order. Adjust and re-verify.</span>
              </>
            )}
          </div>
        )}

        <button
          onClick={handleVerify}
          className="ml-auto px-6 py-2.5 rounded-full bg-brand-primary hover:bg-brand-primary/90 text-white font-bold text-xs shadow-sm flex items-center gap-2 cursor-pointer transition-all hover:scale-[1.02]"
        >
          <Check className="w-4 h-4" />
          <span>Verify Protocol Sequence</span>
        </button>
      </div>
    </div>
  );
}
