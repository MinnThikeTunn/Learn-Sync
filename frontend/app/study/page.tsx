"use client";

import { useState } from "react";
import { 
  Sparkles, 
  Eye, 
  Headphones, 
  BookOpen, 
  Code2, 
  Check, 
  Copy, 
  Flame, 
  Activity, 
  Layers, 
  Quote,
  RefreshCw,
  Search
} from "lucide-react";
import Navbar from "@/components/Navbar";
import MermaidRenderer from "@/components/MermaidRenderer";
import CodeSandbox from "@/components/CodeSandbox";
import AudioRecapPlayer from "@/components/AudioRecapPlayer";

export default function StudyArtifactPage() {
  const [learningStyle, setLearningStyle] = useState<"visual" | "auditory" | "read_write" | "kinesthetic">("visual");
  const [workloadMode, setWorkloadMode] = useState<"free" | "busy">("free");
  const [topic, setTopic] = useState("Recursion & Call Stack Frames");
  const [isGenerating, setIsGenerating] = useState(false);
  const [generatedArtifact, setGeneratedArtifact] = useState<any>(null);
  const [copied, setCopied] = useState(false);

  const handleGenerate = async () => {
    setIsGenerating(true);
    try {
      const res = await fetch("http://localhost:8000/api/v1/artifacts/generate", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-Test-User-Id": "00000000-0000-0000-0000-000000000001",
        },
        body: JSON.stringify({
          folder_id: "00000000-0000-0000-0000-000000000002",
          topic: topic,
          learning_style: learningStyle,
          workload_mode: workloadMode,
          custom_instructions: "Tailor deeply to academic exam preparation.",
        }),
      });

      if (res.ok) {
        const data = await res.json();
        setGeneratedArtifact(data);
      }
    } catch (err) {
      console.warn("Artifact API call error, using local template:", err);
    } finally {
      setIsGenerating(false);
    }
  };

  const handleCopy = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="min-h-screen flex flex-col bg-[#f8f9fb]">
      <Navbar learningStyle={learningStyle} activeMode={workloadMode} />

      <main className="flex-1 max-w-7xl w-full mx-auto px-6 py-8 space-y-8">
        {/* Header & Controls */}
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-6">
          <div>
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-brand-tertiary-container border border-brand-tertiary/40 text-xs font-bold text-brand-on-tertiary-container mb-2">
              <Sparkles className="w-3.5 h-3.5 text-brand-secondary" />
              <span>Grounded Multimodal Synthesis (4 Styles x 2 Modes)</span>
            </div>
            <h1 className="text-4xl font-black text-brand-secondary tracking-tight">{topic}</h1>
            <p className="text-brand-on-surface-variant text-sm font-mono mt-1">Scoped to: /CS101/Week_03_Recursion</p>
          </div>

          {/* Mode Switcher */}
          <div className="flex items-center gap-2 p-1.5 rounded-full bg-brand-surface-dim border border-brand-outline-variant shadow-sm">
            <button
              onClick={() => {
                setWorkloadMode("free");
                setGeneratedArtifact(null);
              }}
              className={`flex items-center gap-1.5 px-4 py-1.5 rounded-full text-xs font-bold transition-all ${
                workloadMode === "free" ? "bg-emerald-600 text-white font-black shadow-sm" : "text-brand-on-surface-variant hover:text-brand-secondary"
              }`}
            >
              <Activity className="w-3.5 h-3.5" />
              <span>Free Mode (Deep)</span>
            </button>
            <button
              onClick={() => {
                setWorkloadMode("busy");
                setGeneratedArtifact(null);
              }}
              className={`flex items-center gap-1.5 px-4 py-1.5 rounded-full text-xs font-bold transition-all ${
                workloadMode === "busy" ? "bg-rose-600 text-white font-black shadow-sm" : "text-brand-on-surface-variant hover:text-brand-secondary"
              }`}
            >
              <Flame className="w-3.5 h-3.5" />
              <span>Busy Mode (80/20)</span>
            </button>
          </div>
        </div>

        {/* Dynamic Topic Prompt Bar */}
        <div className="p-4 rounded-[28px] bg-white border border-brand-outline-variant shadow-sm flex flex-col sm:flex-row items-center gap-3">
          <div className="relative flex-1 w-full">
            <Search className="w-4 h-4 text-brand-on-surface-variant absolute left-4 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              placeholder="Enter concept or topic e.g. Dynamic Programming, Graph Dijkstra..."
              className="w-full pl-11 pr-4 py-2.5 rounded-2xl bg-brand-surface-dim border border-brand-outline-variant text-xs text-brand-secondary focus:outline-none focus:border-brand-primary font-medium"
            />
          </div>
          <button
            onClick={handleGenerate}
            disabled={isGenerating}
            className="w-full sm:w-auto px-6 py-2.5 rounded-2xl bg-brand-primary hover:bg-brand-primary/90 text-white text-xs font-bold transition-all shadow-sm flex items-center justify-center gap-2 disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isGenerating ? "animate-spin" : ""}`} />
            <span>{isGenerating ? "Synthesizing..." : "Synthesize Grounded Artifact"}</span>
          </button>
        </div>

        {/* 4 Learning Styles Switcher Tabs */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {[
            { id: "visual", label: "Visual (Mermaid)", icon: Eye, color: "text-brand-primary" },
            { id: "auditory", label: "Auditory (Podcast/Script)", icon: Headphones, color: "text-brand-primary" },
            { id: "read_write", label: "Read / Write (Notes)", icon: BookOpen, color: "text-brand-primary" },
            { id: "kinesthetic", label: "Kinesthetic (Code Lab)", icon: Code2, color: "text-brand-primary" },
          ].map((tab) => {
            const Icon = tab.icon;
            const isSelected = learningStyle === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => {
                  setLearningStyle(tab.id as any);
                  setGeneratedArtifact(null);
                }}
                className={`p-4 rounded-[20px] flex items-center gap-3 border transition-all text-left shadow-sm ${
                  isSelected
                    ? "bg-white border-2 border-brand-primary shadow-elevation-md text-brand-secondary"
                    : "bg-white/70 border-brand-outline-variant text-brand-on-surface-variant hover:border-brand-primary/40 hover:bg-white"
                }`}
              >
                <Icon className={`w-5 h-5 ${tab.color}`} />
                <span className="text-xs font-bold">{tab.label}</span>
              </button>
            );
          })}
        </div>

        {/* Multimodal Artifact Container (Perplexity Aesthetic rounded-[32px]) */}
        <div className="bg-white border border-brand-outline-variant shadow-elevation-md rounded-[32px] p-8 space-y-6 relative">
          <div className="flex items-center justify-between border-b border-brand-outline-variant pb-4">
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-brand-primary animate-pulse" />
              <span className="text-xs font-bold uppercase tracking-wider text-brand-on-surface-variant">
                {learningStyle.toUpperCase()} ARTIFACT ({workloadMode.toUpperCase()} MODE)
              </span>
            </div>
            <div className="flex items-center gap-3 text-xs font-mono text-brand-on-surface-variant">
              <span>Grounding Confidence: {generatedArtifact?.confidence_score ? Math.round(generatedArtifact.confidence_score * 100) : 92}%</span>
            </div>
          </div>

          {/* 1. Visual Mode Artifact */}
          {learningStyle === "visual" && (
            <div className="space-y-4">
              <MermaidRenderer
                chart={
                  generatedArtifact?.content ||
                  (workloadMode === "free"
                    ? `flowchart TD\n    A["solve_recursion(n)"] --> B{"Is n == 0? (Base Case)"}\n    B -->|Yes| C["Return 1 (Unwind Stack)"]\n    B -->|No| D["Push Call Stack Frame"]\n    D --> E["solve_recursion(n - 1)"]\n    E --> A\n    C --> F["Multiply result * n"]\n    F --> G["Final Computation Complete"]`
                    : `graph LR\n    BaseCase["1. Base Case: if n <= 0 return"] --> Step["2. Recursive Call: f(n-1)"]\n    Step --> Memory["3. Bounded Stack (O(n) RAM)"]`)
                }
              />
            </div>
          )}

          {/* 2. Auditory Mode Artifact */}
          {learningStyle === "auditory" && (
            <div className="space-y-4">
              <AudioRecapPlayer
                title={workloadMode === "free" ? "Socratic Audio Dialogue (3 min)" : "30-Second Rapid Recap Script"}
                durationSeconds={workloadMode === "free" ? 180 : 30}
                transcript={
                  generatedArtifact?.content ||
                  (workloadMode === "free"
                    ? "Professor: When we inspect recursion, what prevents the program from consuming all memory?\n\nStudent: The base case acts as the boundary. When reached, execution halts and returns.\n\nProfessor: Exactly. Each call adds a stack frame. Without the base case, we get a stack overflow."
                    : "Rapid Recap:\nAnchor 1: Always define base case first before recursive call.\nAnchor 2: Stack depth equals recursion tree height.\nAnchor 3: Tail-recursion can be optimized into iterative loops.")
                }
              />
            </div>
          )}

          {/* 3. Read/Write Mode Artifact */}
          {learningStyle === "read_write" && (
            <div className="space-y-4">
              {workloadMode === "free" ? (
                <div className="p-6 rounded-[20px] bg-brand-surface-dim border border-brand-outline-variant text-sm text-brand-secondary leading-relaxed space-y-4">
                  <h3 className="text-xl font-black text-brand-secondary">1. Conceptual Overview of {topic}</h3>
                  <p>Recursion is a programming paradigm where a function solves a problem by calling a smaller sub-instance of itself until reaching an explicit base case.</p>
                  <h3 className="text-xl font-black text-brand-secondary">2. Call Stack Memory Dynamics</h3>
                  <p>Each invocation allocates a stack frame containing local variables and return address in volatile memory.</p>
                </div>
              ) : (
                <div className="p-6 rounded-[20px] bg-brand-surface-dim border border-brand-outline-variant text-sm text-brand-secondary space-y-3">
                  <h4 className="font-black text-brand-secondary text-base">3-Bullet Pareto Takeaways</h4>
                  <p className="text-brand-secondary">• <strong>Base Case:</strong> Guard condition preventing infinite stack growth.</p>
                  <p className="text-brand-secondary">• <strong>Space Complexity:</strong> O(N) memory overhead on the call stack.</p>
                  <p className="text-brand-secondary">• <strong>Exam Rule:</strong> Identify the sub-problem state parameters immediately.</p>
                </div>
              )}
            </div>
          )}

          {/* 4. Kinesthetic Mode Artifact */}
          {learningStyle === "kinesthetic" && (
            <div className="space-y-4">
              <CodeSandbox
                initialCode={
                  generatedArtifact?.content ||
                  (workloadMode === "free"
                    ? `def fibonacci_recursive(n: int) -> int:\n    # Base case:\n    if n <= 1:\n        return n\n    # Recursive call:\n    return fibonacci_recursive(n - 1) + fibonacci_recursive(n - 2)\n\n# Assertion tests:\nassert fibonacci_recursive(0) == 0\nassert fibonacci_recursive(5) == 5\nassert fibonacci_recursive(6) == 8`
                    : `# 90-Second Micro-Snippet Fix: Missing base case guard\ndef is_power_of_two(n: int) -> bool:\n    return n > 0 and (n & (n - 1)) == 0\n\nassert is_power_of_two(16) is True\nassert is_power_of_two(18) is False`)
                }
                testCases={["fibonacci_recursive(5) == 5", "fibonacci_recursive(6) == 8"]}
                language="python"
              />
            </div>
          )}

          {/* Grounding Citations Section */}
          <div className="pt-4 border-t border-brand-outline-variant space-y-2">
            <span className="text-xs font-bold uppercase tracking-wider text-brand-on-surface-variant flex items-center gap-1.5">
              <Quote className="w-3.5 h-3.5 text-brand-primary" />
              <span>Grounded Source Citations (Virtual Folder Partitioned RRF)</span>
            </span>
            <div className="p-3 rounded-[14px] bg-brand-surface-dim border border-brand-outline-variant text-xs text-brand-on-surface-variant font-mono truncate">
              [Chunk #3902] "Recursion relies on a call stack where each recursive call places a frame on memory..."
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
