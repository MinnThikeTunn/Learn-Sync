"use client";

import React, { useState } from "react";
import { 
  Activity, 
  Heart, 
  Thermometer, 
  Wind, 
  CheckCircle2, 
  AlertCircle, 
  ArrowRight, 
  RotateCcw, 
  Sparkles, 
  Stethoscope, 
  ShieldAlert,
  Clock
} from "lucide-react";

export interface InteractiveChoice {
  id: string;
  label: string;
  is_optimal: boolean;
  immediate_feedback: string;
  consequence_narrative?: string;
  vital_impact?: Record<string, string>;
}

export interface SimulationStep {
  step_number: number;
  title: string;
  prompt: string;
  vitals_or_state?: Record<string, string>;
  choices: InteractiveChoice[];
}

export interface KinestheticSimulationPayload {
  kinesthetic_type: string;
  academic_discipline?: string;
  scenario_title: string;
  context_brief: string;
  steps: SimulationStep[];
}

interface ClinicalSimulationLabProps {
  payload: KinestheticSimulationPayload;
  onComplete?: () => void;
  className?: string;
}

export default function ClinicalSimulationLab({
  payload,
  onComplete,
  className = "",
}: ClinicalSimulationLabProps) {
  const steps = payload.steps || [];
  const [currentStepIndex, setCurrentStepIndex] = useState(0);
  const [selectedChoiceId, setSelectedChoiceId] = useState<string | null>(null);
  const [activeVitals, setActiveVitals] = useState<Record<string, string>>(
    steps[0]?.vitals_or_state || {}
  );
  const [isFinished, setIsFinished] = useState(false);
  const [scoreHistory, setScoreHistory] = useState<boolean[]>([]);

  const currentStep = steps[currentStepIndex];
  const selectedChoice = currentStep?.choices.find((c) => c.id === selectedChoiceId);
  const isBusyMode = payload.kinesthetic_type === "critical_decision";

  const handleSelectChoice = (choice: InteractiveChoice) => {
    setSelectedChoiceId(choice.id);

    // Apply dynamic vital updates if present
    if (choice.vital_impact) {
      setActiveVitals((prev) => ({
        ...prev,
        ...choice.vital_impact,
      }));
    }
  };

  const handleNextStep = () => {
    if (selectedChoice) {
      const updatedHistory = [...scoreHistory, selectedChoice.is_optimal];
      setScoreHistory(updatedHistory);
    }

    if (currentStepIndex + 1 < steps.length) {
      const nextIdx = currentStepIndex + 1;
      setCurrentStepIndex(nextIdx);
      setSelectedChoiceId(null);
      if (steps[nextIdx].vitals_or_state) {
        setActiveVitals(steps[nextIdx].vitals_or_state!);
      }
    } else {
      setIsFinished(true);
      if (onComplete) {
        onComplete();
      }
    }
  };

  const handleReset = () => {
    setCurrentStepIndex(0);
    setSelectedChoiceId(null);
    setActiveVitals(steps[0]?.vitals_or_state || {});
    setIsFinished(false);
    setScoreHistory([]);
  };

  return (
    <div
      className={`rounded-[32px] bg-white border border-brand-outline-variant shadow-elevation-md p-6 sm:p-8 space-y-6 ${className}`}
    >
      {/* 1. Header & Context Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-brand-outline-variant gap-4">
        <div className="space-y-1">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-rose-50 border border-rose-200 text-xs font-bold text-rose-700">
            {isBusyMode ? (
              <>
                <Clock className="w-3.5 h-3.5 text-rose-600 animate-pulse" />
                <span>60-Second Critical Decision</span>
              </>
            ) : (
              <>
                <Stethoscope className="w-3.5 h-3.5 text-rose-600" />
                <span>
                  Clinical Case Simulation · {payload.academic_discipline?.replace(/_/g, " ").toUpperCase() || "MEDICINE"}
                </span>
              </>
            )}
          </div>
          <h3 className="text-xl sm:text-2xl font-black text-brand-secondary tracking-tight">
            {payload.scenario_title}
          </h3>
          <p className="text-xs text-brand-on-surface-variant font-medium max-w-2xl">
            {payload.context_brief}
          </p>
        </div>

        <div className="flex items-center gap-2 self-start sm:self-center">
          {!isBusyMode && steps.length > 1 && (
            <div className="px-3 py-1 rounded-full bg-brand-surface-dim border border-brand-outline-variant text-xs font-mono font-bold text-brand-secondary">
              Stage {currentStepIndex + 1} of {steps.length}
            </div>
          )}
          <button
            onClick={handleReset}
            className="flex items-center gap-1 px-3 py-1.5 rounded-full bg-brand-surface-dim hover:bg-brand-surface-variant text-brand-on-surface-variant transition-all text-xs font-bold cursor-pointer"
            title="Restart Case"
          >
            <RotateCcw className="w-3 h-3" />
            <span>Reset</span>
          </button>
        </div>
      </div>

      {/* 2. Patient Vitals HUD (if present) */}
      {Object.keys(activeVitals).length > 0 && (
        <div className="p-4 rounded-[24px] bg-slate-900 text-white shadow-sm border border-slate-800 space-y-2">
          <div className="flex items-center justify-between text-[11px] font-mono font-bold tracking-wider text-slate-400">
            <span className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              LIVE TELEMETRY / VITALS HUD
            </span>
            <span>BED 04 · ICU/ED</span>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-1">
            {activeVitals.BP && (
              <div className="p-3 rounded-xl bg-slate-800/80 border border-slate-700/80 space-y-0.5">
                <div className="flex items-center gap-1.5 text-rose-400 text-[10px] font-bold uppercase tracking-wider">
                  <Activity className="w-3 h-3" />
                  <span>Blood Pressure</span>
                </div>
                <div className="text-sm sm:text-base font-mono font-black text-slate-100">
                  {activeVitals.BP}
                </div>
              </div>
            )}

            {activeVitals.HR && (
              <div className="p-3 rounded-xl bg-slate-800/80 border border-slate-700/80 space-y-0.5">
                <div className="flex items-center gap-1.5 text-amber-400 text-[10px] font-bold uppercase tracking-wider">
                  <Heart className="w-3 h-3" />
                  <span>Heart Rate</span>
                </div>
                <div className="text-sm sm:text-base font-mono font-black text-slate-100">
                  {activeVitals.HR}
                </div>
              </div>
            )}

            {activeVitals.SpO2 && (
              <div className="p-3 rounded-xl bg-slate-800/80 border border-slate-700/80 space-y-0.5">
                <div className="flex items-center gap-1.5 text-cyan-400 text-[10px] font-bold uppercase tracking-wider">
                  <Wind className="w-3 h-3" />
                  <span>Oxygen (SpO2)</span>
                </div>
                <div className="text-sm sm:text-base font-mono font-black text-slate-100">
                  {activeVitals.SpO2}
                </div>
              </div>
            )}

            {activeVitals.Temp && (
              <div className="p-3 rounded-xl bg-slate-800/80 border border-slate-700/80 space-y-0.5">
                <div className="flex items-center gap-1.5 text-emerald-400 text-[10px] font-bold uppercase tracking-wider">
                  <Thermometer className="w-3 h-3" />
                  <span>Core Temp</span>
                </div>
                <div className="text-sm sm:text-base font-mono font-black text-slate-100">
                  {activeVitals.Temp}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* 3. Interactive Case Stage / Scenario Question */}
      {!isFinished && currentStep ? (
        <div className="space-y-5">
          <div className="p-5 rounded-[24px] bg-brand-surface-dim border border-brand-outline-variant/80 space-y-2">
            <div className="text-xs font-bold uppercase tracking-wider text-brand-primary">
              {currentStep.title}
            </div>
            <p className="text-sm font-semibold text-brand-secondary leading-relaxed">
              {currentStep.prompt}
            </p>
          </div>

          {/* Decision Choices */}
          <div className="space-y-3">
            <div className="text-xs font-bold text-brand-on-surface-variant uppercase tracking-wider pl-1">
              Select Immediate Clinical Intervention / Decision:
            </div>
            <div className="grid grid-cols-1 gap-2.5">
              {currentStep.choices.map((choice, idx) => {
                const isSelected = selectedChoiceId === choice.id;
                return (
                  <button
                    key={choice.id}
                    onClick={() => handleSelectChoice(choice)}
                    className={`w-full text-left p-4 rounded-[20px] border transition-all cursor-pointer flex items-start gap-3.5 group ${
                      isSelected
                        ? choice.is_optimal
                          ? "bg-emerald-50/80 border-2 border-emerald-600 shadow-sm"
                          : "bg-rose-50/80 border-2 border-rose-600 shadow-sm"
                        : "bg-white border-brand-outline-variant hover:border-brand-primary/40 hover:bg-brand-surface-dim/40"
                    }`}
                  >
                    <span
                      className={`w-6 h-6 rounded-full flex items-center justify-center shrink-0 font-bold text-xs mt-0.5 transition-all ${
                        isSelected
                          ? choice.is_optimal
                            ? "bg-emerald-600 text-white"
                            : "bg-rose-600 text-white"
                          : "bg-brand-surface-dim border border-brand-outline-variant text-brand-on-surface-variant group-hover:border-brand-primary"
                      }`}
                    >
                      {String.fromCharCode(65 + idx)}
                    </span>
                    <div className="space-y-1 flex-1">
                      <div className="text-xs sm:text-sm font-bold text-brand-secondary leading-snug">
                        {choice.label}
                      </div>
                    </div>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Feedback Drawer (Reveals immediately on selection) */}
          {selectedChoice && (
            <div
              className={`p-5 rounded-[24px] border transition-all animate-fadeIn space-y-3 ${
                selectedChoice.is_optimal
                  ? "bg-emerald-50/90 border-emerald-300 text-emerald-950"
                  : "bg-rose-50/90 border-rose-300 text-rose-950"
              }`}
            >
              <div className="flex items-center gap-2 font-black text-xs uppercase tracking-wider">
                {selectedChoice.is_optimal ? (
                  <>
                    <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                    <span>Evidence-Based Optimal Choice</span>
                  </>
                ) : (
                  <>
                    <AlertCircle className="w-4 h-4 text-rose-600" />
                    <span>Suboptimal / Counter-Indicated Decision</span>
                  </>
                )}
              </div>

              <p className="text-xs font-medium leading-relaxed">
                {selectedChoice.immediate_feedback}
              </p>

              {selectedChoice.consequence_narrative && (
                <div className="text-xs font-mono pt-2 border-t border-black/10 text-brand-secondary">
                  <strong>Outcome:</strong> {selectedChoice.consequence_narrative}
                </div>
              )}

              <div className="pt-2 flex justify-end">
                <button
                  onClick={handleNextStep}
                  className="px-5 py-2.5 rounded-full bg-brand-primary hover:bg-brand-primary/90 text-white font-bold text-xs shadow-sm flex items-center gap-2 cursor-pointer transition-all hover:scale-[1.02]"
                >
                  <span>{currentStepIndex + 1 < steps.length ? "Advance to Next Stage" : "Complete Case"}</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          )}
        </div>
      ) : (
        /* 4. Case Completion Celebration Card */
        <div className="p-8 rounded-[28px] bg-emerald-50 border border-emerald-200 text-center space-y-4">
          <div className="w-12 h-12 rounded-full bg-emerald-600 text-white flex items-center justify-center mx-auto shadow-sm">
            <Sparkles className="w-6 h-6" />
          </div>
          <div className="space-y-1">
            <h4 className="text-2xl font-black text-emerald-950 tracking-tight">
              Clinical Case Successfully Completed!
            </h4>
            <p className="text-xs text-emerald-800 font-medium max-w-md mx-auto">
              You applied active recall to diagnose and manage this simulation. Your knowledge component is primed for the Day 1 Spaced Review queue.
            </p>
          </div>
          <div className="pt-2 flex items-center justify-center gap-3">
            <button
              onClick={handleReset}
              className="px-5 py-2 rounded-full bg-white border border-emerald-300 text-emerald-900 font-bold text-xs hover:bg-emerald-100 transition-all cursor-pointer"
            >
              Replay Simulation
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
