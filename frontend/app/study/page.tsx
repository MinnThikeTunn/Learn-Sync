"use client";

import { useState, useEffect, useRef } from "react";
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
  Search, 
  ArrowRight, 
  GraduationCap, 
  CheckCircle2, 
  Clock, 
  FileText, 
  FolderTree, 
  ChevronRight, 
  Filter, 
  Play, 
  BookMarked,
  HelpCircle,
  Zap,
  RotateCcw
} from "lucide-react";
import Link from "next/link";
import Navbar from "@/components/Navbar";
import MermaidRenderer from "@/components/MermaidRenderer";
import CodeSandbox from "@/components/CodeSandbox";
import AudioRecapPlayer from "@/components/AudioRecapPlayer";
import OnboardingModal from "@/components/OnboardingModal";
import { useAuth } from "@/context/AuthContext";

interface StudyDocument {
  id: string;
  file_name: string;
  topic: string;
  course_code: string;
  course_name: string;
  folder_id: string;
  folder_path: string;
  file_type: string;
  file_size_formatted: string;
  estimated_read_time: string;
  status: "unlearned" | "learned";
  citations_snippet: string;
  chunk_id: string;
  confidence_score: number;
  artifacts: {
    visual_free: string;
    visual_busy: string;
    auditory_free: { title: string; duration: number; transcript: string };
    auditory_busy: { title: string; duration: number; transcript: string };
    read_write_free: { title: string; section1: string; section2: string };
    read_write_busy: { title: string; bullets: string[] };
    kinesthetic_free: { code: string; testCases: string[]; language: string };
    kinesthetic_busy: { code: string; testCases: string[]; language: string };
  };
}

const INITIAL_QUEUE_DOCUMENTS: StudyDocument[] = [
  {
    id: "doc-raft-01",
    file_name: "Raft_Consensus_Paper.pdf",
    topic: "Raft Consensus & Leader Election",
    course_code: "CS301",
    course_name: "Distributed Systems",
    folder_id: "00000000-0000-0000-0000-000000000002",
    folder_path: "/CS301/consensus/raft-paxos",
    file_type: "PDF",
    file_size_formatted: "1.05 MB",
    estimated_read_time: "8 min synthesis",
    status: "unlearned",
    chunk_id: "chk-raft-01",
    citations_snippet: "[Chunk #4021] 'Raft decomposes consensus into leader election, log replication, and safety invariants...'",
    confidence_score: 0.94,
    artifacts: {
      visual_free: `flowchart TD\n    A["Follower State"] -->|"Election Timeout Elapsed"| B["Candidate State: Increment Term"]\n    B --> C["Vote for Self & Broadcast RequestVote RPC"]\n    C --> D{"Majority Votes Received?"}\n    D -->|"Yes (Quorum >= n/2 + 1)"| E["Leader State Established"]\n    D -->|"No / Split Vote"| B\n    E --> F["Send Periodic AppendEntries Heartbeats"]\n    F --> G["Maintain Authority & Replicate Logs"]`,
      visual_busy: `graph LR\n    Follower["1. Follower (Heartbeat Timeout)"] --> Candidate["2. Candidate (RequestVote RPC)"]\n    Candidate --> Leader["3. Leader (AppendEntries Heartbeat)"]`,
      auditory_free: {
        title: "Socratic Dialogue: Raft Leader Election & Quorum Safety",
        duration: 180,
        transcript: "Professor: Why does Raft require randomized election timeouts between 150ms and 300ms?\n\nStudent: Without randomization, multiple followers timeout simultaneously, causing split votes where nobody gains a majority quorum.\n\nProfessor: Exactly. The randomized jitter ensures one node reliably becomes candidate first and collects majority votes before others timeout."
      },
      auditory_busy: {
        title: "30-Second Rapid Recap: Raft Consensus Invariants",
        duration: 30,
        transcript: "Rapid Recap:\nAnchor 1: Leaders send empty AppendEntries heartbeats to suppress new elections.\nAnchor 2: Quorum requires strict majority (floor(N/2) + 1).\nAnchor 3: Higher term numbers unconditionally override obsolete leaders."
      },
      read_write_free: {
        title: "1. Conceptual Foundations of Raft Consensus",
        section1: "Raft is an understandable consensus algorithm designed for state machine replication across unreliable networks. A node resides in one of three mutually exclusive states: Follower, Candidate, or Leader.",
        section2: "2. Log Replication & Safety Invariants\nIf a leader commits an entry, that entry is guaranteed present in the logs of all future leaders for terms >= currentTerm."
      },
      read_write_busy: {
        title: "3-Bullet Pareto Takeaways",
        bullets: [
          "Leader Election: Randomized timer avoids split-vote deadlocks.",
          "Log Matching: If two logs contain an entry with same index and term, they are identical up to that index.",
          "Exam Rule: Only candidate with most up-to-date log can receive majority quorum votes."
        ]
      },
      kinesthetic_free: {
        code: `def handle_election_timeout(current_term: int, voted_for: str, candidate_id: str) -> dict:\n    # Transition to candidate and vote for self:\n    new_term = current_term + 1\n    votes = 1\n    return {\n        "term": new_term,\n        "voted_for": candidate_id,\n        "votes_count": votes,\n        "state": "CANDIDATE"\n    }\n\n# Assertion verification:\nres = handle_election_timeout(1, None, "Node_A")\nassert res["term"] == 2\nassert res["voted_for"] == "Node_A"\nassert res["state"] == "CANDIDATE"`,
        testCases: ["handle_election_timeout(1, None, 'Node_A')['votes_count'] == 1", "handle_election_timeout(3, 'Node_B', 'Node_B')['term'] == 4"],
        language: "python"
      },
      kinesthetic_busy: {
        code: `# 60-Second Snippet: Quorum Checker\ndef is_majority_quorum(votes: int, total_nodes: int) -> bool:\n    return votes >= (total_nodes // 2) + 1\n\nassert is_majority_quorum(3, 5) is True\nassert is_majority_quorum(2, 5) is False`,
        testCases: ["is_majority_quorum(3, 5) == True", "is_majority_quorum(2, 5) == False"],
        language: "python"
      }
    }
  },
  {
    id: "doc-recursion-02",
    file_name: "Recursion_Call_Stack_Deep_Dive.pdf",
    topic: "Recursion & Call Stack Frames",
    course_code: "CS101",
    course_name: "Algorithms & Problem Solving",
    folder_id: "00000000-0000-0000-0000-000000000001",
    folder_path: "/CS101/Week_03_Recursion",
    file_type: "PDF",
    file_size_formatted: "620 KB",
    estimated_read_time: "5 min synthesis",
    status: "unlearned",
    chunk_id: "chk-rec-01",
    citations_snippet: "[Chunk #3902] 'Recursion relies on a call stack where each recursive call places an activation record on volatile memory...'",
    confidence_score: 0.96,
    artifacts: {
      visual_free: `flowchart TD\n    A["solve_recursion(n)"] --> B{"Is n == 0? (Base Case)"}\n    B -->|Yes| C["Return 1 (Unwind Stack)"]\n    B -->|No| D["Push Call Stack Frame"]\n    D --> E["solve_recursion(n - 1)"]\n    E --> A\n    C --> F["Multiply result * n"]\n    F --> G["Final Computation Complete"]`,
      visual_busy: `graph LR\n    BaseCase["1. Base Case: if n <= 0 return"] --> Step["2. Recursive Call: f(n-1)"]\n    Step --> Memory["3. Bounded Stack (O(n) RAM)"]`,
      auditory_free: {
        title: "Socratic Dialogue: Call Stack Allocation & Base Cases",
        duration: 180,
        transcript: "Professor: When we inspect recursion, what prevents the program from consuming all memory?\n\nStudent: The base case acts as the boundary. When reached, execution halts and returns.\n\nProfessor: Exactly. Each call adds a stack frame. Without the base case, we get a stack overflow."
      },
      auditory_busy: {
        title: "30-Second Rapid Recap: Recursion Memory Dynamics",
        duration: 30,
        transcript: "Rapid Recap:\nAnchor 1: Always define base case first before recursive call.\nAnchor 2: Stack depth equals recursion tree height.\nAnchor 3: Tail-recursion can be optimized into iterative loops."
      },
      read_write_free: {
        title: "1. Conceptual Overview of Recursion",
        section1: "Recursion is a programming paradigm where a function solves a problem by calling smaller sub-instances of itself until reaching an explicit base case.",
        section2: "2. Call Stack Memory Dynamics\nEach invocation allocates a stack frame containing local variables and return address in volatile memory."
      },
      read_write_busy: {
        title: "3-Bullet Pareto Takeaways",
        bullets: [
          "Base Case: Guard condition preventing infinite stack growth.",
          "Space Complexity: O(N) memory overhead on the call stack.",
          "Exam Rule: Identify the sub-problem state parameters immediately."
        ]
      },
      kinesthetic_free: {
        code: `def fibonacci_recursive(n: int) -> int:\n    # Base case:\n    if n <= 1:\n        return n\n    # Recursive call:\n    return fibonacci_recursive(n - 1) + fibonacci_recursive(n - 2)\n\n# Assertion tests:\nassert fibonacci_recursive(0) == 0\nassert fibonacci_recursive(5) == 5\nassert fibonacci_recursive(6) == 8`,
        testCases: ["fibonacci_recursive(5) == 5", "fibonacci_recursive(6) == 8"],
        language: "python"
      },
      kinesthetic_busy: {
        code: `# 90-Second Micro-Snippet Fix: Missing base case guard\ndef is_power_of_two(n: int) -> bool:\n    return n > 0 and (n & (n - 1)) == 0\n\nassert is_power_of_two(16) is True\nassert is_power_of_two(18) is False`,
        testCases: ["is_power_of_two(16) == True", "is_power_of_two(18) == False"],
        language: "python"
      }
    }
  },
  {
    id: "doc-attn-03",
    file_name: "Attention_Is_All_You_Need.pdf",
    topic: "Scaled Dot-Product Attention & Transformers",
    course_code: "CS340",
    course_name: "Deep Learning & Neural Architectures",
    folder_id: "00000000-0000-0000-0000-000000000003",
    folder_path: "/CS340/transformers/attention",
    file_type: "PDF",
    file_size_formatted: "2.14 MB",
    estimated_read_time: "7 min synthesis",
    status: "unlearned",
    chunk_id: "chk-attn-01",
    citations_snippet: "[Chunk #5109] 'Attention(Q, K, V) = softmax(Q K^T / sqrt(d_k)) V allows sequence modeling without recurrence...'",
    confidence_score: 0.98,
    artifacts: {
      visual_free: `flowchart TD\n    Q["Queries (Q)"] --> M["MatMul (Q * K^T)"]\n    K["Keys (K)"] --> M\n    M --> S["Scale: Divide by sqrt(d_k)"]\n    S --> Mask["Optional Mask (Causal Decoding)"]\n    Mask --> Softmax["Softmax Probability Weights"]\n    Softmax --> VMat["MatMul with Values (V)"]\n    V["Values (V)"] --> VMat\n    VMat --> Out["Contextualized Attention Output"]`,
      visual_busy: `graph LR\n    Input["1. Query & Key Product"] --> Scale["2. Scale / sqrt(d_k) + Softmax"]\n    Scale --> Output["3. Weighted Value Output"]`,
      auditory_free: {
        title: "Socratic Dialogue: Why Scale by Square Root of d_k?",
        duration: 180,
        transcript: "Professor: When key dimension d_k is large, why must we divide the dot product by sqrt(d_k)?\n\nStudent: Large dot products produce large values in the softmax function, pushing gradients into regions with extremely small derivatives.\n\nProfessor: Exactly. The square-root scaling prevents gradient vanishing during backpropagation."
      },
      auditory_busy: {
        title: "30-Second Rapid Recap: Transformer Self-Attention",
        duration: 30,
        transcript: "Rapid Recap:\nAnchor 1: Self-attention replaces recurrent RNN sequential bottlenecks with parallel matrix products.\nAnchor 2: Multi-head attention allows attending to information from different representation subspaces.\nAnchor 3: Positional encoding injects word order into permutation-invariant attention."
      },
      read_write_free: {
        title: "1. Mathematical Formulation of Self-Attention",
        section1: "Scaled dot-product attention computes compatibility between queries and keys, mapping them to weighted value representations with O(N^2) sequence memory complexity.",
        section2: "2. Multi-Head Attention Subspaces\nInstead of performing single attention function with d_model dimensions, Multi-Head projects queries, keys, and values h times with learned linear projections."
      },
      read_write_busy: {
        title: "3-Bullet Pareto Takeaways",
        bullets: [
          "Formula: Attention(Q,K,V) = softmax((Q K^T) / sqrt(d_k)) V.",
          "Complexity: Quadratic O(N^2 * d) time/space with respect to sequence length N.",
          "Exam Rule: Self-attention is permutation-invariant without explicit Positional Encodings."
        ]
      },
      kinesthetic_free: {
        code: `import math\n\ndef scaled_dot_product_attention_sim(q_val: float, k_val: float, v_val: float, d_k: int = 64) -> float:\n    # Compute dot product and scale:\n    dot = q_val * k_val\n    scaled = dot / math.sqrt(d_k)\n    # Softmax weight approximation:\n    weight = 1.0 / (1.0 + math.exp(-scaled))\n    return round(weight * v_val, 4)\n\n# Verification test:\nout = scaled_dot_product_attention_sim(2.0, 4.0, 10.0, 64)\nassert out > 0.0\nassert out <= 10.0`,
        testCases: ["scaled_dot_product_attention_sim(2.0, 4.0, 10.0, 64) > 5.0", "scaled_dot_product_attention_sim(0.0, 0.0, 10.0, 64) == 5.0"],
        language: "python"
      },
      kinesthetic_busy: {
        code: `# 60-Second Attention Weight Normalizer\ndef attention_scale_factor(d_k: int) -> float:\n    import math\n    return 1.0 / math.sqrt(d_k)\n\nassert round(attention_scale_factor(64), 4) == 0.1250`,
        testCases: ["round(attention_scale_factor(64), 4) == 0.1250"],
        language: "python"
      }
    }
  },
  {
    id: "doc-paxos-04",
    file_name: "Paxos_Made_Moderately_Complex.pdf",
    topic: "Paxos Consensus & Two-Phase Invariants",
    course_code: "CS301",
    course_name: "Distributed Systems",
    folder_id: "00000000-0000-0000-0000-000000000002",
    folder_path: "/CS301/consensus/raft-paxos",
    file_type: "PDF",
    file_size_formatted: "845 KB",
    estimated_read_time: "6 min synthesis",
    status: "unlearned",
    chunk_id: "chk-paxos-01",
    citations_snippet: "[Chunk #4120] 'Paxos achieves agreement through Phase 1 Prepare-Promise and Phase 2 Propose-Accept protocol rounds...'",
    confidence_score: 0.91,
    artifacts: {
      visual_free: `flowchart TD\n    P["Proposer: Choose Proposal Number N"] --> P1["Send Prepare(N) to Acceptors"]\n    P1 --> A1{"Phase 1: Promise Majority?"}\n    A1 -->|Yes| P2["Send Accept(N, V) with highest promised value"]\n    A1 -->|No| P["Backoff & Retry with higher N"]\n    P2 --> A2{"Phase 2: Accepted by Majority?"}\n    A2 -->|Yes| L["Consensus Value V Decided & Committed"]\n    A2 -->|No| P`,
      visual_busy: `graph LR\n    Phase1["1. Prepare(N) -> Promise"] --> Phase2["2. Accept(N, V) -> Accepted"]\n    Phase2 --> Commit["3. Value Decided"]`,
      auditory_free: {
        title: "Socratic Dialogue: Paxos Phase 1 Prepare Guarantees",
        duration: 180,
        transcript: "Professor: What guarantee does an Acceptor give when replying with a Promise(N)?\n\nStudent: The Acceptor promises never to accept any future proposal with a number smaller than N.\n\nProfessor: Exactly. And it also reports the highest-numbered proposal it has already accepted, preserving committed state."
      },
      auditory_busy: {
        title: "30-Second Rapid Recap: Paxos Dual Phases",
        duration: 30,
        transcript: "Rapid Recap:\nAnchor 1: Phase 1 establishes proposal leadership and learns past accepted values.\nAnchor 2: Phase 2 commits the chosen value across majority acceptors.\nAnchor 3: Dueling proposers can cause livelock without randomized backoff."
      },
      read_write_free: {
        title: "1. Paxos Protocol Dynamics",
        section1: "Single-decree Paxos guarantees safety in asynchronous networks where messages can be delayed or dropped but not corrupted.",
        section2: "2. Majority Quorum Overlap\nAny two majorities of acceptors share at least one common acceptor, ensuring that accepted values are never overwritten."
      },
      read_write_busy: {
        title: "3-Bullet Pareto Takeaways",
        bullets: [
          "Phase 1 (Prepare): Reserve proposal slot and collect previously accepted values.",
          "Phase 2 (Accept): Propose value to majority quorum.",
          "Exam Rule: Quorum intersection guarantees safety even with f node failures in 2f+1 cluster."
        ]
      },
      kinesthetic_free: {
        code: `def can_accept_proposal(promised_n: int, incoming_n: int) -> bool:\n    # Acceptor only accepts if incoming proposal >= promised proposal\n    return incoming_n >= promised_n\n\nassert can_accept_proposal(promised_n=10, incoming_n=12) is True\nassert can_accept_proposal(promised_n=10, incoming_n=8) is False`,
        testCases: ["can_accept_proposal(10, 12) == True", "can_accept_proposal(10, 8) == False"],
        language: "python"
      },
      kinesthetic_busy: {
        code: `# Quorum overlap validator\ndef has_quorum_overlap(total_nodes: int, quorum_a: int, quorum_b: int) -> bool:\n    return (quorum_a + quorum_b) > total_nodes\n\nassert has_quorum_overlap(5, 3, 3) is True`,
        testCases: ["has_quorum_overlap(5, 3, 3) == True"],
        language: "python"
      }
    }
  }
];

export default function StudyArtifactPage() {
  const { profile, setLearningStyle: setGlobalLearningStyle } = useAuth();
  
  // Document Queue State
  const [documents, setDocuments] = useState<StudyDocument[]>(INITIAL_QUEUE_DOCUMENTS);
  const [selectedDocId, setSelectedDocId] = useState<string>(INITIAL_QUEUE_DOCUMENTS[0].id);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedCourseFilter, setSelectedCourseFilter] = useState<string>("all");
  
  // Active Study & Learning State
  const [learningStyle, setLearningStyle] = useState<"visual" | "auditory" | "read_write" | "kinesthetic">(
    profile?.learning_style || "visual"
  );
  const [workloadMode, setWorkloadMode] = useState<"free" | "busy">("free");
  const [customTopic, setCustomTopic] = useState("");
  const [isGenerating, setIsGenerating] = useState(false);
  const [generatedArtifact, setGeneratedArtifact] = useState<any>(null);
  const [copied, setCopied] = useState(false);
  const [showOnboarding, setShowOnboarding] = useState(false);

  // Lesson Completion & Spaced Repetition Handoff State
  const [isCompleting, setIsCompleting] = useState(false);
  const [completedDocIds, setCompletedDocIds] = useState<Set<string>>(new Set());
  const [handoffSuccessDoc, setHandoffSuccessDoc] = useState<StudyDocument | null>(null);

  const learningWorkspaceRef = useRef<HTMLDivElement>(null);

  // Active Document resolution
  const activeDocument = documents.find(d => d.id === selectedDocId) || documents[0];
  const activeTopic = customTopic.trim() || activeDocument?.topic || "Multimodal Synthesis";

  useEffect(() => {
    if (profile?.learning_style) {
      setLearningStyle(profile.learning_style);
    }
  }, [profile?.learning_style]);

  // Fetch live documents from backend if available, merging with rich templates
  useEffect(() => {
    const fetchQueue = async () => {
      try {
        const res = await fetch("http://localhost:8000/api/v1/study/queue", {
          headers: { "X-Test-User-Id": "00000000-0000-0000-0000-000000000001" },
        });
        if (res.ok) {
          const liveDocs = await res.json();
          if (Array.isArray(liveDocs) && liveDocs.length > 0) {
            // Merge with local rich artifact templates
            const merged = INITIAL_QUEUE_DOCUMENTS.map(item => {
              const liveMatch = liveDocs.find((ld: any) => ld.file_name === item.file_name || ld.id === item.id);
              if (liveMatch && liveMatch.status === "learned") {
                return { ...item, status: "learned" as const };
              }
              return item;
            });
            setDocuments(merged);
          }
        }
      } catch (err) {
        console.warn("Using local queue fallback:", err);
      }
    };
    fetchQueue();
  }, []);

  // Filter documents in the unlearned queue
  const unlearnedDocs = documents.filter(d => !completedDocIds.has(d.id) && d.status !== "learned");
  const filteredQueue = unlearnedDocs.filter(d => {
    const matchesSearch = d.file_name.toLowerCase().includes(searchQuery.toLowerCase()) || 
                          d.topic.toLowerCase().includes(searchQuery.toLowerCase()) ||
                          d.course_code.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesCourse = selectedCourseFilter === "all" || d.course_code === selectedCourseFilter;
    return matchesSearch && matchesCourse;
  });

  const availableCourses = Array.from(new Set(unlearnedDocs.map(d => d.course_code)));

  const handleSelectDocument = (doc: StudyDocument) => {
    setSelectedDocId(doc.id);
    setCustomTopic("");
    setGeneratedArtifact(null);
    setHandoffSuccessDoc(null);

    // Smoothly scroll to the Full Learning Mode workspace
    setTimeout(() => {
      learningWorkspaceRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
    }, 50);
  };

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
          folder_id: activeDocument.folder_id,
          topic: activeTopic,
          learning_style: learningStyle,
          workload_mode: workloadMode,
          custom_instructions: "Tailor deeply to academic exam preparation and grounded synthesis.",
        }),
      });

      if (res.ok) {
        const data = await res.json();
        setGeneratedArtifact(data);
      }
    } catch (err) {
      console.warn("Artifact API call error, using grounded template:", err);
    } finally {
      setIsGenerating(false);
    }
  };

  const handleCompleteLessonAndHandoff = async () => {
    setIsCompleting(true);
    try {
      const res = await fetch("http://localhost:8000/api/v1/study/complete-lesson", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-Test-User-Id": "00000000-0000-0000-0000-000000000001",
        },
        body: JSON.stringify({
          folder_id: activeDocument.folder_id,
          document_id: activeDocument.id.startsWith("doc-") ? undefined : activeDocument.id,
          topic: activeTopic,
          learning_style: learningStyle,
        }),
      });

      // Update completed state
      setCompletedDocIds(prev => new Set(prev).add(activeDocument.id));
      setHandoffSuccessDoc(activeDocument);
    } catch (err) {
      console.warn("Handoff API error, fallback local update:", err);
      setCompletedDocIds(prev => new Set(prev).add(activeDocument.id));
      setHandoffSuccessDoc(activeDocument);
    } finally {
      setIsCompleting(false);
    }
  };

  const handleCopy = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleStudyNextDocument = () => {
    const remaining = documents.filter(d => !completedDocIds.has(d.id) && d.id !== activeDocument.id && d.status !== "learned");
    if (remaining.length > 0) {
      handleSelectDocument(remaining[0]);
    } else {
      setHandoffSuccessDoc(null);
    }
  };

  return (
    <div className="min-h-screen flex flex-col bg-[#f8f9fb]">
      <Navbar 
        learningStyle={learningStyle} 
        activeMode={workloadMode} 
        onOpenOnboardingModal={() => setShowOnboarding(true)}
      />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 py-8 space-y-8">
        
        {/* ===================================================================== */}
        {/* 1. UNLEARNED DOCUMENTS QUEUE (Replaces Solidify Long-Term Memory Tag) */}
        {/* ===================================================================== */}
        <section className="bg-white border border-brand-outline-variant shadow-sm rounded-[32px] p-6 sm:p-8 space-y-6 transition-all duration-300">
          <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
            <div className="space-y-1.5">
              <div className="inline-flex items-center gap-2 px-3.5 py-1 rounded-full bg-purple-50 text-purple-700 border border-purple-200 text-xs font-bold shadow-xs">
                <BookOpen className="w-3.5 h-3.5 text-purple-600" />
                <span>Study Queue · Docs To Learn</span>
                <span className="w-1.5 h-1.5 rounded-full bg-purple-600 animate-pulse" />
              </div>
              <h2 className="text-2xl sm:text-3xl font-black text-brand-secondary tracking-tight">
                Unlearned Documents Queue
              </h2>
              <p className="text-xs sm:text-sm text-brand-on-surface-variant max-w-2xl font-medium">
                Select any document below to launch the <strong>Full Learning Mode</strong> workspace. Synthesize concepts across 4 sensory styles, absorb grounded lecture notes, and hand off to Review upon completion.
              </p>
            </div>

            {/* Queue Statistics Pill */}
            <div className="flex items-center gap-3">
              <div className="flex items-center gap-2.5 px-4 py-2 rounded-[20px] bg-brand-surface-dim border border-brand-outline-variant text-xs font-bold text-brand-secondary shadow-xs">
                <span className="w-2.5 h-2.5 rounded-full bg-amber-500 animate-ping" />
                <span>{unlearnedDocs.length} Documents Pending</span>
              </div>
            </div>
          </div>

          {/* Search & Course Filter Controls */}
          <div className="flex flex-col sm:flex-row items-center gap-3 pt-2">
            <div className="relative flex-1 w-full">
              <Search className="w-4 h-4 text-brand-on-surface-variant absolute left-4 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search unlearned documents by title, topic, or course code..."
                className="w-full pl-11 pr-4 py-2.5 rounded-2xl bg-brand-surface-dim border border-brand-outline-variant text-xs text-brand-secondary focus:outline-none focus:border-brand-primary font-medium transition-all"
              />
            </div>

            {/* Course Filter Pills */}
            <div className="flex items-center gap-1.5 overflow-x-auto w-full sm:w-auto pb-1 sm:pb-0">
              <button
                onClick={() => setSelectedCourseFilter("all")}
                className={`px-3.5 py-2 rounded-full text-xs font-bold transition-all whitespace-nowrap cursor-pointer ${
                  selectedCourseFilter === "all"
                    ? "bg-[#3a10e5] text-white shadow-xs"
                    : "bg-brand-surface-dim text-brand-on-surface-variant hover:text-brand-secondary border border-brand-outline-variant"
                }`}
              >
                All Courses ({unlearnedDocs.length})
              </button>
              {availableCourses.map((code) => (
                <button
                  key={code}
                  onClick={() => setSelectedCourseFilter(code)}
                  className={`px-3.5 py-2 rounded-full text-xs font-bold transition-all whitespace-nowrap cursor-pointer ${
                    selectedCourseFilter === code
                      ? "bg-[#3a10e5] text-white shadow-xs"
                      : "bg-brand-surface-dim text-brand-on-surface-variant hover:text-brand-secondary border border-brand-outline-variant"
                  }`}
                >
                  {code}
                </button>
              ))}
            </div>
          </div>

          {/* Queue Grid of Unlearned Documents */}
          {filteredQueue.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-1">
              {filteredQueue.map((doc) => {
                const isSelected = activeDocument.id === doc.id;
                return (
                  <div
                    key={doc.id}
                    onClick={() => handleSelectDocument(doc)}
                    className={`group relative p-5 rounded-[24px] border transition-all duration-200 cursor-pointer text-left flex flex-col justify-between gap-4 ${
                      isSelected
                        ? "bg-purple-50/50 border-2 border-[#3a10e5] shadow-elevation-md ring-2 ring-[#3a10e5]/10"
                        : "bg-brand-surface-dim/70 hover:bg-white border-brand-outline-variant hover:border-brand-primary/40 hover:shadow-elevation-sm"
                    }`}
                  >
                    <div className="space-y-2">
                      <div className="flex items-center justify-between gap-2">
                        <div className="flex items-center gap-2">
                          <span className="px-2.5 py-0.5 rounded-md bg-[#3a10e5]/10 text-[#3a10e5] text-[11px] font-black tracking-tight uppercase">
                            {doc.course_code}
                          </span>
                          <span className="text-[11px] font-medium text-brand-on-surface-variant truncate max-w-[180px]">
                            {doc.course_name}
                          </span>
                        </div>
                        <span className="inline-flex items-center gap-1 text-[10px] font-bold uppercase tracking-wider text-amber-700 bg-amber-100/80 px-2 py-0.5 rounded-full">
                          <span className="w-1.5 h-1.5 rounded-full bg-amber-500 animate-pulse" />
                          Ready To Learn
                        </span>
                      </div>

                      <div>
                        <h3 className="text-base font-black text-brand-secondary tracking-tight group-hover:text-[#3a10e5] transition-colors flex items-center gap-2">
                          <FileText className="w-4 h-4 text-purple-600 shrink-0" />
                          <span className="truncate">{doc.file_name}</span>
                        </h3>
                        <p className="text-xs text-brand-on-surface-variant line-clamp-1 mt-0.5 font-medium">
                          Topic: <strong className="text-brand-secondary">{doc.topic}</strong>
                        </p>
                      </div>
                    </div>

                    <div className="pt-3 border-t border-brand-outline-variant/60 flex items-center justify-between gap-2 text-xs">
                      <div className="flex items-center gap-3 text-brand-on-surface-variant font-mono text-[11px]">
                        <span className="flex items-center gap-1">
                          <Clock className="w-3.5 h-3.5 text-brand-on-surface-variant" />
                          {doc.estimated_read_time}
                        </span>
                        <span>•</span>
                        <span>{doc.file_size_formatted}</span>
                      </div>

                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleSelectDocument(doc);
                        }}
                        className={`inline-flex items-center gap-1 px-3.5 py-1.5 rounded-xl text-xs font-bold transition-all shadow-xs ${
                          isSelected
                            ? "bg-[#3a10e5] text-white"
                            : "bg-white text-brand-secondary group-hover:bg-[#3a10e5] group-hover:text-white border border-brand-outline-variant group-hover:border-transparent"
                        }`}
                      >
                        <span>{isSelected ? "Active Workspace" : "Start Learning"}</span>
                        <ArrowRight className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            /* Empty Queue Celebration State */
            <div className="p-10 rounded-[24px] bg-emerald-50/60 border border-emerald-200 text-center space-y-3">
              <div className="w-12 h-12 rounded-full bg-emerald-100 text-emerald-700 flex items-center justify-center mx-auto shadow-xs">
                <CheckCircle2 className="w-6 h-6 text-emerald-600" />
              </div>
              <h3 className="text-xl font-black text-brand-secondary">
                All Documents Synthesized & Learned!
              </h3>
              <p className="text-xs sm:text-sm text-brand-on-surface-variant max-w-md mx-auto">
                Your unlearned documents queue is completely clear. All lessons have been absorbed and handed off to Spaced Repetition for active recall retention.
              </p>
              <div className="flex items-center justify-center gap-3 pt-2">
                <Link
                  href="/review"
                  className="inline-flex items-center gap-2 px-5 py-2.5 rounded-[20px] bg-[#3a10e5] text-white text-xs font-bold shadow-sm hover:opacity-90 transition-all cursor-pointer"
                >
                  <span>Go to Review Tab</span>
                  <ArrowRight className="w-4 h-4" />
                </Link>
                <Link
                  href="/folders"
                  className="inline-flex items-center gap-2 px-5 py-2.5 rounded-[20px] bg-white text-brand-secondary border border-brand-outline-variant text-xs font-bold shadow-xs hover:bg-brand-surface-dim transition-all cursor-pointer"
                >
                  <FolderTree className="w-4 h-4 text-brand-primary" />
                  <span>Upload More Documents</span>
                </Link>
              </div>
            </div>
          )}
        </section>


        {/* ===================================================================== */}
        {/* 2. FULL LEARNING MODE WORKSPACE (Appears upon selecting a document)  */}
        {/* ===================================================================== */}
        <div ref={learningWorkspaceRef} className="space-y-6 scroll-mt-20">
          
          {/* Active Document Header & Mode Controls */}
          <div className="flex flex-col md:flex-row md:items-end justify-between gap-6">
            <div className="space-y-1">
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-brand-tertiary-container border border-brand-tertiary/40 text-xs font-bold text-brand-on-tertiary-container">
                <Sparkles className="w-3.5 h-3.5 text-brand-secondary" />
                <span>Full Learning Mode · Multimodal Grounded Synthesis</span>
              </div>
              <h1 className="text-3xl sm:text-4xl font-black text-brand-secondary tracking-tight">
                {activeTopic}
              </h1>
              <div className="flex items-center gap-3 text-xs text-brand-on-surface-variant font-mono mt-1">
                <span className="px-2 py-0.5 rounded bg-brand-surface-dim border border-brand-outline-variant font-bold text-brand-secondary">
                  {activeDocument.course_code}
                </span>
                <span>Scoped to: {activeDocument.folder_path}</span>
                <span>•</span>
                <span className="text-purple-700 font-semibold">{activeDocument.file_name}</span>
              </div>
            </div>

            {/* Workload Mode Switcher (Free vs Busy) */}
            <div className="flex items-center gap-2 p-1.5 rounded-full bg-brand-surface-dim border border-brand-outline-variant shadow-sm shrink-0">
              <button
                onClick={() => {
                  setWorkloadMode("free");
                  setGeneratedArtifact(null);
                }}
                className={`flex items-center gap-1.5 px-4 py-1.5 rounded-full text-xs font-bold transition-all cursor-pointer ${
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
                className={`flex items-center gap-1.5 px-4 py-1.5 rounded-full text-xs font-bold transition-all cursor-pointer ${
                  workloadMode === "busy" ? "bg-rose-600 text-white font-black shadow-sm" : "text-brand-on-surface-variant hover:text-brand-secondary"
                }`}
              >
                <Flame className="w-3.5 h-3.5" />
                <span>Busy Mode (80/20)</span>
              </button>
            </div>
          </div>

          {/* Quick Document Switcher Bar */}
          <div className="p-3.5 rounded-[22px] bg-white border border-brand-outline-variant shadow-xs flex items-center justify-between gap-3 overflow-x-auto">
            <div className="flex items-center gap-2 shrink-0">
              <span className="text-xs font-bold text-brand-on-surface-variant uppercase tracking-wider pl-2">
                Active Doc:
              </span>
              <span className="text-xs font-black text-[#3a10e5] bg-purple-50 px-3 py-1 rounded-full border border-purple-200 truncate max-w-[220px]">
                {activeDocument.file_name}
              </span>
            </div>

            <div className="flex items-center gap-1.5 shrink-0">
              <span className="text-xs text-brand-on-surface-variant font-medium mr-1">Switch doc:</span>
              {documents.map((d) => (
                <button
                  key={d.id}
                  onClick={() => handleSelectDocument(d)}
                  className={`px-3 py-1 rounded-full text-xs font-bold transition-all cursor-pointer ${
                    activeDocument.id === d.id
                      ? "bg-brand-secondary text-white shadow-xs"
                      : "bg-brand-surface-dim text-brand-on-surface-variant hover:text-brand-secondary hover:bg-brand-surface-variant"
                  }`}
                >
                  {d.course_code}: {d.file_name.split(".")[0].slice(0, 14)}...
                </button>
              ))}
            </div>
          </div>

          {/* Dynamic Topic Prompt & Synthesis Bar */}
          <div className="p-4 rounded-[28px] bg-white border border-brand-outline-variant shadow-sm flex flex-col sm:flex-row items-center gap-3">
            <div className="relative flex-1 w-full">
              <Search className="w-4 h-4 text-brand-on-surface-variant absolute left-4 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                value={customTopic}
                onChange={(e) => setCustomTopic(e.target.value)}
                placeholder={`Customize topic prompt (default: "${activeDocument.topic}")...`}
                className="w-full pl-11 pr-4 py-2.5 rounded-2xl bg-brand-surface-dim border border-brand-outline-variant text-xs text-brand-secondary focus:outline-none focus:border-brand-primary font-medium"
              />
            </div>
            <button
              onClick={handleGenerate}
              disabled={isGenerating}
              className="w-full sm:w-auto px-6 py-2.5 rounded-2xl bg-brand-primary hover:bg-brand-primary/90 text-white text-xs font-bold transition-all shadow-sm flex items-center justify-center gap-2 disabled:opacity-50 cursor-pointer"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${isGenerating ? "animate-spin" : ""}`} />
              <span>{isGenerating ? "Synthesizing Grounded Artifact..." : "Re-Synthesize Document"}</span>
            </button>
          </div>

          {/* 4 Learning Styles Switcher Tabs */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            {[
              { id: "visual", label: "Visual (Mermaid Diagram)", icon: Eye, color: "text-brand-primary" },
              { id: "auditory", label: "Auditory (Podcast/Recap)", icon: Headphones, color: "text-brand-primary" },
              { id: "read_write", label: "Read / Write (Notes)", icon: BookOpen, color: "text-brand-primary" },
              { id: "kinesthetic", label: "Kinesthetic (Code Lab)", icon: Code2, color: "text-brand-primary" },
            ].map((tab) => {
              const Icon = tab.icon;
              const isSelected = learningStyle === tab.id;
              return (
                <button
                  key={tab.id}
                  onClick={async () => {
                    setLearningStyle(tab.id as any);
                    await setGlobalLearningStyle(tab.id as any);
                    setGeneratedArtifact(null);
                  }}
                  className={`p-4 rounded-[20px] flex items-center gap-3 border transition-all text-left shadow-sm cursor-pointer ${
                    isSelected
                      ? "bg-white border-2 border-brand-primary shadow-elevation-md text-brand-secondary scale-[1.01]"
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
          <div className="bg-white border border-brand-outline-variant shadow-elevation-md rounded-[32px] p-6 sm:p-8 space-y-6 relative">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between border-b border-brand-outline-variant pb-4 gap-2">
              <div className="flex items-center gap-2.5">
                <span className="w-2.5 h-2.5 rounded-full bg-brand-primary animate-pulse" />
                <span className="text-xs font-bold uppercase tracking-wider text-brand-on-surface-variant">
                  {learningStyle.toUpperCase()} ARTIFACT ({workloadMode.toUpperCase()} MODE)
                </span>
                <span className="text-[11px] font-bold text-purple-700 bg-purple-50 px-2.5 py-0.5 rounded-full border border-purple-200">
                  {activeDocument.file_name}
                </span>
              </div>
              <div className="flex items-center gap-3 text-xs font-mono text-brand-on-surface-variant">
                <span>Grounding Confidence: {generatedArtifact?.confidence_score ? Math.round(generatedArtifact.confidence_score * 100) : Math.round(activeDocument.confidence_score * 100)}%</span>
              </div>
            </div>

            {/* 1. Visual Mode Artifact */}
            {learningStyle === "visual" && (
              <div className="space-y-4">
                <MermaidRenderer
                  chart={
                    generatedArtifact?.content ||
                    (workloadMode === "free"
                      ? activeDocument.artifacts.visual_free
                      : activeDocument.artifacts.visual_busy)
                  }
                />
              </div>
            )}

            {/* 2. Auditory Mode Artifact */}
            {learningStyle === "auditory" && (
              <div className="space-y-4">
                <AudioRecapPlayer
                  title={
                    workloadMode === "free"
                      ? activeDocument.artifacts.auditory_free.title
                      : activeDocument.artifacts.auditory_busy.title
                  }
                  durationSeconds={
                    workloadMode === "free"
                      ? activeDocument.artifacts.auditory_free.duration
                      : activeDocument.artifacts.auditory_busy.duration
                  }
                  transcript={
                    generatedArtifact?.content ||
                    (workloadMode === "free"
                      ? activeDocument.artifacts.auditory_free.transcript
                      : activeDocument.artifacts.auditory_busy.transcript)
                  }
                />
              </div>
            )}

            {/* 3. Read/Write Mode Artifact */}
            {learningStyle === "read_write" && (
              <div className="space-y-4">
                {workloadMode === "free" ? (
                  <div className="p-6 rounded-[20px] bg-brand-surface-dim border border-brand-outline-variant text-sm text-brand-secondary leading-relaxed space-y-4">
                    <h3 className="text-xl font-black text-brand-secondary">{activeDocument.artifacts.read_write_free.title}</h3>
                    <p>{activeDocument.artifacts.read_write_free.section1}</p>
                    <p className="whitespace-pre-line">{activeDocument.artifacts.read_write_free.section2}</p>
                  </div>
                ) : (
                  <div className="p-6 rounded-[20px] bg-brand-surface-dim border border-brand-outline-variant text-sm text-brand-secondary space-y-3">
                    <h4 className="font-black text-brand-secondary text-base">{activeDocument.artifacts.read_write_busy.title}</h4>
                    {activeDocument.artifacts.read_write_busy.bullets.map((bullet, idx) => (
                      <p key={idx} className="text-brand-secondary">• {bullet}</p>
                    ))}
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
                      ? activeDocument.artifacts.kinesthetic_free.code
                      : activeDocument.artifacts.kinesthetic_busy.code)
                  }
                  testCases={
                    workloadMode === "free"
                      ? activeDocument.artifacts.kinesthetic_free.testCases
                      : activeDocument.artifacts.kinesthetic_busy.testCases
                  }
                  language="python"
                />
              </div>
            )}

            {/* Grounding Citations Section */}
            <div className="pt-4 border-t border-brand-outline-variant space-y-2">
              <span className="text-xs font-bold uppercase tracking-wider text-brand-on-surface-variant flex items-center gap-1.5">
                <Quote className="w-3.5 h-3.5 text-brand-primary" />
                <span>Grounded Source Citations ({activeDocument.course_code} RRF Hybrid Index)</span>
              </span>
              <div className="p-3.5 rounded-[16px] bg-brand-surface-dim border border-brand-outline-variant text-xs text-brand-secondary font-mono truncate">
                {activeDocument.citations_snippet}
              </div>
            </div>
          </div>

          {/* ===================================================================== */}
          {/* 3. STUDY-TO-REVIEW HANDOFF COMPLETION BANNER                          */}
          {/* ===================================================================== */}
          <div className="p-6 sm:p-8 rounded-[32px] bg-gradient-to-r from-purple-50 via-indigo-50/50 to-white border border-purple-200 shadow-sm space-y-4">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
              <div className="space-y-1.5">
                <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-purple-100/80 text-purple-800 text-xs font-bold">
                  <GraduationCap className="w-3.5 h-3.5 text-purple-700" />
                  <span>Finish Learning & Handoff</span>
                </div>
                <h3 className="text-xl sm:text-2xl font-black text-brand-secondary tracking-tight">
                  Done Learning This Document?
                </h3>
                <p className="text-xs sm:text-sm text-brand-on-surface-variant max-w-2xl font-medium">
                  Mark this lesson completed to clear <strong>{activeDocument.file_name}</strong> from your unlearned queue and hand off to the Review tab for Day 1 active recall spaced repetition.
                </p>
              </div>

              {/* Completion & Handoff Action */}
              <div className="flex flex-col sm:flex-row items-center gap-3">
                {completedDocIds.has(activeDocument.id) ? (
                  <div className="flex flex-wrap items-center gap-3">
                    <div className="inline-flex items-center gap-2 px-4 py-2.5 rounded-[20px] bg-emerald-50 text-emerald-700 border border-emerald-200 text-xs font-bold">
                      <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                      <span>Learned & Handed Off to Review</span>
                    </div>
                    <Link
                      href="/review"
                      className="inline-flex items-center gap-2 px-5 py-2.5 rounded-[20px] bg-[#3a10e5] text-white text-xs font-bold shadow-sm hover:opacity-90 transition-all cursor-pointer"
                    >
                      <span>Go to Review Tab</span>
                      <ArrowRight className="w-4 h-4" />
                    </Link>
                    {unlearnedDocs.length > 0 && (
                      <button
                        onClick={handleStudyNextDocument}
                        className="inline-flex items-center gap-2 px-4 py-2.5 rounded-[20px] bg-white text-brand-secondary border border-brand-outline-variant text-xs font-bold shadow-xs hover:bg-brand-surface-dim transition-all cursor-pointer"
                      >
                        <span>Study Next Doc</span>
                        <ChevronRight className="w-3.5 h-3.5" />
                      </button>
                    )}
                  </div>
                ) : (
                  <button
                    onClick={handleCompleteLessonAndHandoff}
                    disabled={isCompleting}
                    className="inline-flex items-center gap-2 px-6 py-3 rounded-[24px] bg-[#3a10e5] text-white text-xs sm:text-sm font-bold shadow-md hover:shadow-lg hover:scale-[1.02] active:scale-[0.98] transition-all cursor-pointer disabled:opacity-50"
                  >
                    <GraduationCap className="w-4 h-4" />
                    <span>{isCompleting ? "Handoff to Review..." : "Complete Learning & Hand Off to Review"}</span>
                  </button>
                )}
              </div>
            </div>
          </div>

        </div>

      </main>

      <OnboardingModal
        isOpen={showOnboarding}
        onSave={(newStyle) => {
          setLearningStyle(newStyle);
          setShowOnboarding(false);
        }}
      />
    </div>
  );
}
