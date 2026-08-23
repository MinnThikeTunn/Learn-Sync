"use client";

import { useState } from "react";
import { 
  Sparkles, 
  Eye, 
  Headphones, 
  BookOpen, 
  Code2, 
  Play, 
  Check, 
  Copy, 
  Flame, 
  Activity,
  Layers,
  Quote
} from "lucide-react";
import Navbar from "@/components/Navbar";

export default function StudyArtifactPage() {
  const [learningStyle, setLearningStyle] = useState<"visual" | "auditory" | "read_write" | "kinesthetic">("visual");
  const [workloadMode, setWorkloadMode] = useState<"free" | "busy">("free");
  const [topic, setTopic] = useState("Recursion & Call Stack Frames");
  const [copied, setCopied] = useState(false);

  const handleCopy = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="min-h-screen flex flex-col bg-obsidian-950">
      <Navbar learningStyle={learningStyle} activeMode={workloadMode} />

      <main className="flex-1 max-w-7xl w-full mx-auto px-6 py-8 space-y-8">
        {/* Header & Controls */}
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-6">
          <div>
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-slate-900 border border-slate-800 text-xs font-semibold text-accent-indigo mb-2">
              <Sparkles className="w-3.5 h-3.5" />
              <span>Grounded Multimodal Synthesis (4 Styles x 2 Modes)</span>
            </div>
            <h1 className="text-4xl font-black text-white tracking-tight">{topic}</h1>
            <p className="text-slate-400 text-sm font-mono mt-1">Scoped to: /CS101/Week_03_Recursion</p>
          </div>

          {/* Mode Switcher */}
          <div className="flex items-center gap-2 p-1.5 rounded-full bg-obsidian-900 border border-slate-800">
            <button
              onClick={() => setWorkloadMode("free")}
              className={`flex items-center gap-1.5 px-4 py-1.5 rounded-full text-xs font-bold transition-all ${
                workloadMode === "free" ? "bg-emerald-500 text-obsidian-950 font-black shadow" : "text-slate-400 hover:text-white"
              }`}
            >
              <Activity className="w-3.5 h-3.5" />
              <span>Free Mode (Deep)</span>
            </button>
            <button
              onClick={() => setWorkloadMode("busy")}
              className={`flex items-center gap-1.5 px-4 py-1.5 rounded-full text-xs font-bold transition-all ${
                workloadMode === "busy" ? "bg-rose-500 text-white font-black shadow" : "text-slate-400 hover:text-white"
              }`}
            >
              <Flame className="w-3.5 h-3.5" />
              <span>Busy Mode (80/20)</span>
            </button>
          </div>
        </div>

        {/* 4 Learning Styles Switcher Tabs */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {[
            { id: "visual", label: "Visual (Mermaid)", icon: Eye, color: "text-accent-cyan" },
            { id: "auditory", label: "Auditory (Podcast/Script)", icon: Headphones, color: "text-purple-400" },
            { id: "read_write", label: "Read / Write (Notes)", icon: BookOpen, color: "text-emerald-400" },
            { id: "kinesthetic", label: "Kinesthetic (Code Lab)", icon: Code2, color: "text-amber-400" },
          ].map((tab) => {
            const Icon = tab.icon;
            const isSelected = learningStyle === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setLearningStyle(tab.id as any)}
                className={`p-4 rounded-[20px] flex items-center gap-3 border transition-all text-left ${
                  isSelected
                    ? "bg-slate-900/90 border-slate-600 shadow-lg text-white"
                    : "bg-obsidian-950/60 border-slate-800 text-slate-400 hover:border-slate-700 hover:text-slate-200"
                }`}
              >
                <Icon className={`w-5 h-5 ${tab.color}`} />
                <span className="text-xs font-bold">{tab.label}</span>
              </button>
            );
          })}
        </div>

        {/* Multimodal Artifact Container (Perplexity Aesthetic rounded-[32px]) */}
        <div className="glass-card p-8 space-y-6 relative">
          <div className="flex items-center justify-between border-b border-slate-800/80 pb-4">
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-accent-cyan animate-pulse" />
              <span className="text-xs font-bold uppercase tracking-wider text-slate-400">
                {learningStyle.toUpperCase()} ARTIFACT ({workloadMode.toUpperCase()} MODE)
              </span>
            </div>
            <div className="flex items-center gap-3 text-xs font-mono text-slate-400">
              <span>Grounding Confidence: 92%</span>
            </div>
          </div>

          {/* 1. Visual Mode Artifact */}
          {learningStyle === "visual" && (
            <div className="space-y-4">
              {workloadMode === "free" ? (
                <div className="p-6 rounded-[24px] bg-obsidian-950 border border-slate-800 font-mono text-xs text-cyan-300 overflow-x-auto">
                  <div className="text-slate-400 mb-2">// Interactive Mermaid Sequence & Flow</div>
                  <pre className="text-sm text-cyan-200 leading-relaxed">{`flowchart TD
    A["solve_recursion(n)"] --> B{"Is n == 0? (Base Case)"}
    B -->|Yes| C["Return 1 (Unwind Stack)"]
    B -->|No| D["Push Call Stack Frame"]
    D --> E["solve_recursion(n - 1)"]
    E --> A
    C --> F["Multiply result * n"]
    F --> G["Final Computation Complete"]`}</pre>
                </div>
              ) : (
                <div className="p-6 rounded-[24px] bg-obsidian-950 border border-slate-800 font-mono text-xs text-cyan-300">
                  <div className="text-slate-400 mb-2">// 60-Second Core Primitive Cheat-Sheet</div>
                  <pre className="text-sm text-cyan-200">{`graph LR
    BaseCase["1. Base Case: if n <= 0 return"] --> Step["2. Recursive Call: f(n-1)"]
    Step --> Memory["3. Bounded Stack (O(n) RAM)"]`}</pre>
                </div>
              )}
            </div>
          )}

          {/* 2. Auditory Mode Artifact */}
          {learningStyle === "auditory" && (
            <div className="space-y-4">
              {workloadMode === "free" ? (
                <div className="space-y-4">
                  <div className="p-4 rounded-[20px] bg-slate-900 border border-slate-800 flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <button className="w-10 h-10 rounded-full bg-accent-indigo flex items-center justify-center text-white shadow-lg">
                        <Play className="w-5 h-5 ml-0.5" />
                      </button>
                      <div>
                        <h4 className="font-bold text-sm text-white">Socratic Audio Dialogue (3 min)</h4>
                        <p className="text-xs text-slate-400">Professor & Student: Why recursion terminates</p>
                      </div>
                    </div>
                    <span className="text-xs font-mono text-indigo-300">0:00 / 3:12</span>
                  </div>

                  <div className="p-6 rounded-[24px] bg-obsidian-950 border border-slate-800 text-sm space-y-3 leading-relaxed text-slate-200">
                    <p><strong className="text-accent-indigo">Professor:</strong> When we inspect recursion, what prevents the program from consuming all memory?</p>
                    <p><strong className="text-cyan-400">Student:</strong> The base case acts as the boundary. When reached, execution halts and returns.</p>
                    <p><strong className="text-accent-indigo">Professor:</strong> Exactly. Each call adds a stack frame. Without the base case, we get a stack overflow.</p>
                  </div>
                </div>
              ) : (
                <div className="p-6 rounded-[24px] bg-obsidian-950 border border-slate-800 space-y-3 text-sm text-slate-200">
                  <span className="text-xs font-extrabold uppercase text-rose-400 font-mono">30-Second Rapid Recap Script</span>
                  <ul className="space-y-2 list-disc pl-5">
                    <li><strong>Anchor 1:</strong> Always define base case first before recursive call.</li>
                    <li><strong>Anchor 2:</strong> Stack depth equals recursion tree height.</li>
                    <li><strong>Anchor 3:</strong> Tail-recursion can be optimized into iterative loops.</li>
                  </ul>
                </div>
              )}
            </div>
          )}

          {/* 3. Read/Write Mode Artifact */}
          {learningStyle === "read_write" && (
            <div className="space-y-4">
              {workloadMode === "free" ? (
                <div className="p-6 rounded-[24px] bg-obsidian-950 border border-slate-800 text-sm text-slate-200 leading-relaxed space-y-4">
                  <h3 className="text-xl font-black text-white">1. Conceptual Overview of Recursion</h3>
                  <p>Recursion is a programming paradigm where a function solves a problem by calling a smaller sub-instance of itself until reaching an explicit base case.</p>
                  <h3 className="text-xl font-black text-white">2. Call Stack Memory Dynamics</h3>
                  <p>Each invocation allocates a stack frame containing local variables and return address in volatile memory.</p>
                </div>
              ) : (
                <div className="p-6 rounded-[24px] bg-obsidian-950 border border-slate-800 text-sm text-slate-200 space-y-3">
                  <h4 className="font-black text-white text-base">3-Bullet Pareto Takeaways</h4>
                  <p className="text-slate-300">• <strong>Base Case:</strong> Guard condition preventing infinite stack growth.</p>
                  <p className="text-slate-300">• <strong>Space Complexity:</strong> O(N) memory overhead on the call stack.</p>
                  <p className="text-slate-300">• <strong>Exam Rule:</strong> Identify the sub-problem state parameters immediately.</p>
                </div>
              )}
            </div>
          )}

          {/* 4. Kinesthetic Mode Artifact */}
          {learningStyle === "kinesthetic" && (
            <div className="space-y-4">
              {workloadMode === "free" ? (
                <div className="p-6 rounded-[24px] bg-obsidian-950 border border-slate-800 space-y-3 font-mono text-xs text-amber-300">
                  <div className="text-slate-400">// Interactive Code Lab Challenge</div>
                  <pre className="text-sm text-slate-100">{`def fibonacci_recursive(n: int) -> int:
    # TODO: Implement base case
    if n <= 1:
        return n
    # TODO: Recursive call
    return fibonacci_recursive(n - 1) + fibonacci_recursive(n - 2)

# Automated Test Suite:
assert fibonacci_recursive(0) == 0
assert fibonacci_recursive(5) == 5
assert fibonacci_recursive(6) == 8`}</pre>
                </div>
              ) : (
                <div className="p-6 rounded-[24px] bg-obsidian-950 border border-slate-800 font-mono text-xs text-amber-300 space-y-2">
                  <span className="text-slate-400 block">// 90-Second Micro-Snippet Fix</span>
                  <pre className="text-sm text-slate-100">{`# Bug Fix: Missing base case check
def is_power_of_two(n: int) -> bool:
    return n > 0 and (n & (n - 1)) == 0`}</pre>
                </div>
              )}
            </div>
          )}

          {/* Grounding Citations Section */}
          <div className="pt-4 border-t border-slate-800/80 space-y-2">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
              <Quote className="w-3.5 h-3.5 text-accent-cyan" />
              <span>Grounded Source Citations</span>
            </span>
            <div className="p-3 rounded-[16px] bg-slate-900/60 border border-slate-800 text-xs text-slate-400 font-mono truncate">
              [Chunk #3902] "Recursion relies on a call stack where each recursive call places a frame on memory..."
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
