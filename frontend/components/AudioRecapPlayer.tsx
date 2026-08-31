"use client";

import React, { useState, useEffect, useRef } from "react";
import { Play, Pause, RotateCcw, Volume2, FastForward, Headphones } from "lucide-react";

interface AudioRecapPlayerProps {
  transcript: string;
  durationSeconds?: number;
  title?: string;
  className?: string;
}

export default function AudioRecapPlayer({
  transcript,
  durationSeconds = 60,
  title = "Socratic Dialogue Recap",
  className = "",
}: AudioRecapPlayerProps) {
  const [isPlaying, setIsPlaying] = useState(false);
  const [rate, setRate] = useState(1.0);
  const [supported, setSupported] = useState(true);
  const utteranceRef = useRef<SpeechSynthesisUtterance | null>(null);

  useEffect(() => {
    if (typeof window !== "undefined" && !("speechSynthesis" in window)) {
      setSupported(false);
    }
  }, []);

  const handlePlayPause = () => {
    if (typeof window === "undefined" || !("speechSynthesis" in window)) return;

    if (isPlaying) {
      window.speechSynthesis.cancel();
      setIsPlaying(false);
    } else {
      window.speechSynthesis.cancel();
      // Strip markdown and clean text for natural speech
      const cleanText = transcript
        .replace(/[#*`_\[\]]/g, "")
        .replace(/\b(Professor|Student):/g, "$1 says:")
        .trim();

      const utterance = new SpeechSynthesisUtterance(cleanText);
      utterance.rate = rate;
      utterance.onend = () => setIsPlaying(false);
      utterance.onerror = () => setIsPlaying(false);
      utteranceRef.current = utterance;

      window.speechSynthesis.speak(utterance);
      setIsPlaying(true);
    }
  };

  const handleRateChange = (newRate: number) => {
    setRate(newRate);
    if (isPlaying && typeof window !== "undefined") {
      window.speechSynthesis.cancel();
      setIsPlaying(false);
    }
  };

  const handleReset = () => {
    if (typeof window !== "undefined") {
      window.speechSynthesis.cancel();
    }
    setIsPlaying(false);
  };

  return (
    <div className={`rounded-[24px] bg-white border border-brand-outline-variant p-6 space-y-4 shadow-elevation-md ${className}`}>
      {/* Player Header */}
      <div className="flex items-center justify-between border-b border-brand-outline-variant/60 pb-3">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-full bg-brand-primary/10 flex items-center justify-center text-brand-primary">
            <Headphones className="w-4 h-4" />
          </div>
          <div>
            <h4 className="font-bold text-sm text-brand-secondary">{title}</h4>
            <p className="text-[11px] text-brand-on-surface-variant">
              Web Speech Synthesizer (~{durationSeconds}s duration)
            </p>
          </div>
        </div>

        {/* Speed Controls */}
        <div className="flex items-center gap-1 bg-brand-surface-dim rounded-full p-1 border border-brand-outline-variant/80 text-xs">
          {[1.0, 1.25, 1.5].map((r) => (
            <button
              key={r}
              onClick={() => handleRateChange(r)}
              className={`px-2 py-0.5 rounded-full text-[10px] font-bold transition-all ${
                rate === r ? "bg-brand-primary text-white" : "text-brand-on-surface-variant hover:text-brand-secondary"
              }`}
            >
              {r}x
            </button>
          ))}
        </div>
      </div>

      {/* Audio Playback Controls */}
      <div className="flex items-center gap-4 bg-brand-surface-dim p-4 rounded-[20px] border border-brand-outline-variant">
        <button
          onClick={handlePlayPause}
          className="w-12 h-12 rounded-full bg-brand-primary hover:bg-brand-primary/90 text-white flex items-center justify-center shadow-md transition-all active:scale-95"
          title={isPlaying ? "Pause" : "Play Audio"}
        >
          {isPlaying ? <Pause className="w-5 h-5" /> : <Play className="w-5 h-5 ml-0.5 fill-current" />}
        </button>

        <div className="flex-1 space-y-1.5">
          <div className="flex items-center justify-between text-xs font-mono text-brand-on-surface-variant">
            <span className="flex items-center gap-1.5">
              <Volume2 className={`w-3.5 h-3.5 ${isPlaying ? "text-brand-primary animate-pulse" : ""}`} />
              <span>{isPlaying ? "Speaking..." : "Ready to listen"}</span>
            </span>
            <span>{rate}x Speed</span>
          </div>
          <div className="w-full h-1.5 rounded-full bg-brand-outline-variant overflow-hidden">
            <div
              className={`h-full bg-brand-primary rounded-full transition-all duration-300 ${
                isPlaying ? "w-3/4 animate-pulse" : "w-0"
              }`}
            />
          </div>
        </div>

        <button
          onClick={handleReset}
          className="p-2 rounded-full hover:bg-white text-brand-on-surface-variant transition-all"
          title="Stop / Reset"
        >
          <RotateCcw className="w-4 h-4" />
        </button>
      </div>

      {/* Transcript Container */}
      <div className="p-4 rounded-[18px] bg-brand-surface-dim border border-brand-outline-variant text-xs leading-relaxed text-brand-secondary max-h-48 overflow-y-auto space-y-2 font-mono">
        <div className="font-bold text-[10px] text-brand-on-surface-variant uppercase tracking-wider mb-1">
          Full Audio Transcript:
        </div>
        <div className="whitespace-pre-wrap">{transcript}</div>
      </div>
    </div>
  );
}
