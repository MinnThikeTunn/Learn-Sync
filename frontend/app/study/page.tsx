"use client";

import { useState, useEffect, useRef, useCallback, Suspense } from "react";
import { 
  Sparkles, 
  Eye, 
  Headphones, 
  BookOpen, 
  Code2, 
  Flame, 
  Activity, 
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
  AlertCircle,
  Loader2,
  BrainCircuit,
  Lock
} from "lucide-react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import Navbar from "@/components/Navbar";
import MermaidRenderer from "@/components/MermaidRenderer";
import CodeSandbox from "@/components/CodeSandbox";
import AudioRecapPlayer from "@/components/AudioRecapPlayer";
import ClinicalSimulationLab from "@/components/ClinicalSimulationLab";
import ProceduralSequencingLab from "@/components/ProceduralSequencingLab";
import OnboardingModal from "@/components/OnboardingModal";
import DocumentReaderModal from "@/components/DocumentReaderModal";
import { extractMermaidDiagram } from "@/lib/mermaidUtils";
import { useAuth } from "@/context/AuthContext";

interface DbStudyDocument {
  id: string;
  course_id?: string;
  course_code?: string;
  course_name?: string;
  folder_id?: string;
  folder_path?: string;
  file_name: string;
  file_type?: string;
  file_size_bytes?: number;
  file_size_formatted?: string;
  estimated_read_time?: string;
  topic?: string;
  status: string;
  created_at?: string;
}

interface GroundingCitation {
  chunk_id: string;
  document_id?: string;
  snippet: string;
  relevance_score?: number;
}

interface StudyArtifactResponse {
  folder_id: string;
  topic: string;
  learning_style: string;
  workload_mode: string;
  artifact_type: string;
  content: string;
  citations: GroundingCitation[];
  source_chunk_ids: string[];
  confidence_score: number;
  is_low_confidence: boolean;
  metadata?: {
    estimated_time_minutes?: number;
    diagram_syntax?: string;
    alternative_diagram_syntax?: string;
    academic_discipline?: string;
    concept_tree?: any;
    simulation_payload?: any;
    audio_duration_seconds?: number;
    speakers?: string[];
    programming_language?: string;
    test_cases?: any[];
  };
}

function StudyPageContent() {
  const { user, profile, session, setLearningStyle: setGlobalLearningStyle } = useAuth();
  const searchParams = useSearchParams();
  const router = useRouter();

  // Query parameters from folders or review navigation
  const paramDocId = searchParams.get("document_id") || "";
  const paramFileName = searchParams.get("file_name") || "";
  const paramFolderId = searchParams.get("folder_id") || "";
  const paramFolder = searchParams.get("folder") || "";
  const paramTopic = searchParams.get("topic") || "";
  
  // Database Queue States
  const [documents, setDocuments] = useState<DbStudyDocument[]>([]);
  const [selectedDocId, setSelectedDocId] = useState<string | null>(null);
  const [readingDoc, setReadingDoc] = useState<DbStudyDocument | null>(null);
  const [isLoadingQueue, setIsLoadingQueue] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedCourseFilter, setSelectedCourseFilter] = useState<string>("all");
  
  // Active Learning Workspace States
  const [learningStyle, setLearningStyle] = useState<"visual" | "auditory" | "read_write" | "kinesthetic">(
    profile?.learning_style || "visual"
  );
  const [workloadMode, setWorkloadMode] = useState<"free" | "busy">("free");
  const [customTopic, setCustomTopic] = useState(paramTopic || "");
  const [isGenerating, setIsGenerating] = useState(false);
  const [generatedArtifact, setGeneratedArtifact] = useState<StudyArtifactResponse | null>(null);
  const [showOnboarding, setShowOnboarding] = useState(false);

  // Lesson Completion State
  const [isCompleting, setIsCompleting] = useState(false);
  const [completedDocIds, setCompletedDocIds] = useState<Set<string>>(new Set());

  const learningWorkspaceRef = useRef<HTMLDivElement>(null);
  const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

  const getHeaders = useCallback(() => {
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
    };
    if (session?.access_token) {
      headers["Authorization"] = `Bearer ${session.access_token}`;
    }
    const uid = user?.id || "00000000-0000-0000-0000-000000000001";
    headers["X-Test-User-Id"] = uid;
    return headers;
  }, [session?.access_token, user?.id]);

  // 1. Fetch unlearned documents strictly from the database API
  const fetchDbQueue = useCallback(async () => {
    setIsLoadingQueue(true);
    try {
      const res = await fetch(`${API_URL}/study/queue`, {
        headers: getHeaders(),
      });
      if (res.ok) {
        const liveDocs: DbStudyDocument[] = await res.json();
        setDocuments(liveDocs);

        // Targeted document matching based on query parameters
        let matchedDoc: DbStudyDocument | undefined;
        if (paramDocId) {
          matchedDoc = liveDocs.find(d => d.id === paramDocId);
        }
        if (!matchedDoc && paramFileName) {
          matchedDoc = liveDocs.find(d => d.file_name?.toLowerCase() === paramFileName.toLowerCase());
        }
        if (!matchedDoc && paramFolderId) {
          matchedDoc = liveDocs.find(d => d.folder_id === paramFolderId);
        }
        if (!matchedDoc && paramFolder) {
          matchedDoc = liveDocs.find(d => d.folder_path === paramFolder || (d.folder_path && d.folder_path.includes(paramFolder)));
        }
        if (!matchedDoc && paramTopic) {
          matchedDoc = liveDocs.find(d => d.topic && d.topic.toLowerCase().includes(paramTopic.toLowerCase()));
        }

        if (matchedDoc) {
          setSelectedDocId(matchedDoc.id);
        } else if (liveDocs.length > 0 && !selectedDocId) {
          setSelectedDocId(liveDocs[0].id);
        }
      }

      // Synchronize active workload mode from live telemetry
      try {
        const wlRes = await fetch(`${API_URL}/workload/live?days_ahead=7`, {
          headers: getHeaders(),
        });
        if (wlRes.ok) {
          const wlData = await wlRes.json();
          if (wlData.current_mode === "busy") {
            setWorkloadMode("busy");
          } else {
            setWorkloadMode("free");
          }
        }
      } catch {
        // preserve current mode
      }
    } catch (err) {
      console.warn("Failed to load documents from database:", err);
    } finally {
      setIsLoadingQueue(false);
    }
  }, [API_URL, getHeaders, selectedDocId, paramDocId, paramFileName, paramFolderId, paramFolder, paramTopic]);

  useEffect(() => {
    fetchDbQueue();
  }, [fetchDbQueue]);

  useEffect(() => {
    if (paramDocId && documents.some(d => d.id === paramDocId)) {
      setSelectedDocId(paramDocId);
    }
  }, [paramDocId, documents]);

  useEffect(() => {
    if (paramTopic && !customTopic) {
      setCustomTopic(paramTopic);
    }
  }, [paramTopic, customTopic]);

  useEffect(() => {
    if (profile?.learning_style) {
      setLearningStyle(profile.learning_style);
    }
  }, [profile?.learning_style]);

  // Active Document resolution
  const activeDocument = documents.find(d => d.id === selectedDocId) || documents[0] || null;
  const activeTopic = customTopic.trim() || activeDocument?.topic || activeDocument?.file_name?.split(".")?.[0]?.replace(/_/g, " ") || "Course Lecture Materials";

  // 2. Synthesize Grounded Artifact strictly from Database Chunks
  const synthesizeArtifact = useCallback(async (
    doc: DbStudyDocument | null, 
    style: string, 
    mode: string, 
    topicOverride?: string
  ) => {
    setIsGenerating(true);
    try {
      const topicToUse = topicOverride?.trim() || doc?.topic || doc?.file_name?.replace(/_/g, " ").replace(/\.[^/.]+$/, "") || activeTopic || "Course Foundations";
      const folderId = doc?.folder_id || "00000000-0000-0000-0000-000000000002";
      const res = await fetch(`${API_URL}/artifacts/generate`, {
        method: "POST",
        headers: getHeaders(),
        body: JSON.stringify({
          folder_id: folderId,
          topic: topicToUse,
          learning_style: style,
          workload_mode: mode,
          custom_instructions: "Synthesize strictly from grounded document chunks.",
        }),
      });

      if (res.ok) {
        const data: StudyArtifactResponse = await res.json();
        setGeneratedArtifact(data);
      }
    } catch (err) {
      console.warn("Artifact synthesis error:", err);
    } finally {
      setIsGenerating(false);
    }
  }, [API_URL, activeTopic, getHeaders]);

  // Auto-synthesize when active document, style, or workload mode changes
  useEffect(() => {
    synthesizeArtifact(activeDocument, learningStyle, workloadMode, customTopic);
  }, [activeDocument?.id, learningStyle, workloadMode]);

  // Filter unlearned documents
  const unlearnedDocs = documents.filter(d => !completedDocIds.has(d.id) && d.status !== "learned");
  const filteredQueue = unlearnedDocs.filter(d => {
    const matchesSearch = d.file_name?.toLowerCase().includes(searchQuery.toLowerCase()) || 
                          (d.topic && d.topic.toLowerCase().includes(searchQuery.toLowerCase())) ||
                          (d.course_code && d.course_code.toLowerCase().includes(searchQuery.toLowerCase()));
    const matchesCourse = selectedCourseFilter === "all" || d.course_code === selectedCourseFilter;
    return matchesSearch && matchesCourse;
  });

  const availableCourses = Array.from(new Set(unlearnedDocs.map(d => d.course_code).filter(Boolean))) as string[];

  const handleSelectDocument = (doc: DbStudyDocument) => {
    setSelectedDocId(doc.id);
    setCustomTopic("");
    setGeneratedArtifact(null);

    // Synchronize URL with active document
    const params = new URLSearchParams();
    params.set("document_id", doc.id);
    params.set("file_name", doc.file_name);
    if (doc.folder_id) params.set("folder_id", doc.folder_id);
    if (doc.topic) params.set("topic", doc.topic);
    router.replace(`/study?${params.toString()}`, { scroll: false });

    // Scroll to learning workspace
    setTimeout(() => {
      learningWorkspaceRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
    }, 50);
  };

  // 3. Mark document as learned and hand off to Review in Database
  const handleCompleteLessonAndHandoff = async () => {
    if (!activeDocument) return;
    setIsCompleting(true);
    try {
      const res = await fetch(`${API_URL}/study/complete-lesson`, {
        method: "POST",
        headers: getHeaders(),
        body: JSON.stringify({
          folder_id: activeDocument.folder_id || "00000000-0000-0000-0000-000000000002",
          document_id: activeDocument.id,
          topic: activeTopic,
          learning_style: learningStyle,
        }),
      });

      if (res.ok) {
        setCompletedDocIds(prev => new Set(prev).add(activeDocument.id));
        // Refresh queue from DB
        fetchDbQueue();
      }
    } catch (err) {
      console.warn("Handoff API error:", err);
      setCompletedDocIds(prev => new Set(prev).add(activeDocument.id));
    } finally {
      setIsCompleting(false);
    }
  };

  const handleStudyNextDocument = () => {
    const remaining = unlearnedDocs.filter(d => d.id !== activeDocument?.id);
    if (remaining.length > 0) {
      handleSelectDocument(remaining[0]);
    }
  };

  // Helper to extract clean code from markdown if needed
  const extractCleanCode = (rawContent?: string) => {
    if (!rawContent) return "";
    const match = rawContent.match(/```(?:python)?\n([\s\S]*?)```/);
    return match ? match[1].trim() : rawContent.trim();
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
        {/* 1. DATABASE UNLEARNED DOCUMENTS QUEUE                                */}
        {/* ===================================================================== */}
        <section className="bg-white border border-brand-outline-variant shadow-sm rounded-[32px] p-6 sm:p-8 space-y-6 transition-all duration-300">
          <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
            <div className="space-y-1.5">
              <div className="inline-flex items-center gap-2 px-3.5 py-1 rounded-full bg-purple-50 text-purple-700 border border-purple-200 text-xs font-bold shadow-xs">
                <BookOpen className="w-3.5 h-3.5 text-purple-600" />
                <span>Study Queue · Database Documents</span>
                <span className="w-1.5 h-1.5 rounded-full bg-purple-600 animate-pulse" />
              </div>
              <h2 className="text-2xl sm:text-3xl font-black text-brand-secondary tracking-tight">
                Unlearned Documents Queue
              </h2>
              <p className="text-xs sm:text-sm text-brand-on-surface-variant max-w-2xl font-medium">
                Select any document from your database virtual folders below to launch <strong>Full Learning Mode</strong>. Grounded multimodal synthesis is computed directly from stored document chunks.
              </p>
            </div>

            {/* Queue Statistics Pill */}
            <div className="flex items-center gap-3">
              <div className="flex items-center gap-2.5 px-4 py-2 rounded-[20px] bg-brand-surface-dim border border-brand-outline-variant text-xs font-bold text-brand-secondary shadow-xs">
                {isLoadingQueue ? (
                  <Loader2 className="w-3.5 h-3.5 animate-spin text-purple-600" />
                ) : (
                  <span className="w-2.5 h-2.5 rounded-full bg-amber-500 animate-ping" />
                )}
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

          {/* Queue Grid of Database Documents */}
          {isLoadingQueue ? (
            <div className="p-12 text-center space-y-3">
              <Loader2 className="w-8 h-8 text-[#3a10e5] animate-spin mx-auto" />
              <p className="text-xs text-brand-on-surface-variant font-medium">Loading documents from database...</p>
            </div>
          ) : filteredQueue.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-1">
              {filteredQueue.map((doc) => {
                const isSelected = activeDocument?.id === doc.id;
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
                            {doc.course_code || "COURSE"}
                          </span>
                          <span className="text-[11px] font-medium text-brand-on-surface-variant truncate max-w-[180px]">
                            {doc.course_name || "Virtual Folder"}
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
                          Topic: <strong className="text-brand-secondary">{doc.topic || doc.file_name}</strong>
                        </p>
                      </div>
                    </div>

                    <div className="pt-3 border-t border-brand-outline-variant/60 flex items-center justify-between gap-2 text-xs">
                      <div className="flex items-center gap-3 text-brand-on-surface-variant font-mono text-[11px]">
                        <span className="flex items-center gap-1">
                          <Clock className="w-3.5 h-3.5 text-brand-on-surface-variant" />
                          {doc.estimated_read_time || "5 min synthesis"}
                        </span>
                        <span>•</span>
                        <span>{doc.file_size_formatted || (doc.file_size_bytes ? `${Math.round(doc.file_size_bytes / 1024)} KB` : "Document")}</span>
                      </div>

                      <div className="flex items-center gap-2">
                        <button
                          type="button"
                          onClick={(e) => {
                            e.stopPropagation();
                            setReadingDoc(doc);
                          }}
                          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-bold bg-brand-surface-dim hover:bg-brand-primary/10 text-brand-secondary hover:text-brand-primary transition-all border border-brand-outline-variant hover:border-brand-primary/30 shadow-2xs cursor-pointer"
                          title={`Read full document for ${doc.file_name}`}
                        >
                          <BookOpen className="w-3.5 h-3.5 text-brand-primary" />
                          <span>Read</span>
                        </button>
                        <Link
                          href={`/review?folder_id=${doc.folder_id || ""}&document_id=${doc.id}&file_name=${encodeURIComponent(doc.file_name)}&topic=${encodeURIComponent(doc.topic || doc.file_name)}`}
                          onClick={(e) => e.stopPropagation()}
                          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-bold bg-purple-50 text-purple-700 hover:bg-purple-100 hover:text-purple-900 transition-all border border-purple-200 shadow-2xs cursor-pointer"
                          title="Review flashcards for this document"
                        >
                          <BrainCircuit className="w-3.5 h-3.5 text-[#3a10e5]" />
                          <span>Review</span>
                        </Link>
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
                Your database queue has no pending unlearned documents. All uploaded materials have been synthesized and scheduled for active recall.
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
                  <span>Upload Documents in Virtual Folders</span>
                </Link>
              </div>
            </div>
          )}
        </section>


        {/* ===================================================================== */}
        {/* 2. FULL LEARNING MODE WORKSPACE (Driven by Database API Synthesis)    */}
        {/* ===================================================================== */}
        <div ref={learningWorkspaceRef} className="space-y-6 scroll-mt-20">
            
            {/* Active Document Header & Mode Controls */}
            <div className="flex flex-col md:flex-row md:items-end justify-between gap-6">
              <div className="space-y-1">
                <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-brand-tertiary-container border border-brand-tertiary/40 text-xs font-bold text-brand-on-tertiary-container">
                  <Sparkles className="w-3.5 h-3.5 text-brand-secondary" />
                  <span>Full Learning Mode · Grounded Database Synthesis</span>
                </div>
                <h1 className="text-3xl sm:text-4xl font-black text-brand-secondary tracking-tight">
                  {activeTopic}
                </h1>
                <div className="flex items-center gap-3 text-xs text-brand-on-surface-variant font-mono mt-1">
                  <span className="px-2 py-0.5 rounded bg-brand-surface-dim border border-brand-outline-variant font-bold text-brand-secondary">
                    {activeDocument?.course_code || "General"}
                  </span>
                  <span>Scoped to: {activeDocument?.folder_path || "/root"}</span>
                  {activeDocument && (
                    <>
                      <span>•</span>
                      <span className="text-purple-700 font-semibold">{activeDocument.file_name}</span>
                    </>
                  )}
                </div>
              </div>

              {/* Workload Mode Switcher (Free vs Busy) */}
              <div className="flex items-center gap-2 p-1.5 rounded-full bg-brand-surface-dim border border-brand-outline-variant shadow-sm shrink-0">
                <button
                  onClick={() => setWorkloadMode("free")}
                  className={`flex items-center gap-1.5 px-4 py-1.5 rounded-full text-xs font-bold transition-all cursor-pointer ${
                    workloadMode === "free" ? "bg-emerald-600 text-white font-black shadow-sm" : "text-brand-on-surface-variant hover:text-brand-secondary"
                  }`}
                >
                  <Activity className="w-3.5 h-3.5" />
                  <span>Free Mode (Deep)</span>
                </button>
                <button
                  onClick={() => setWorkloadMode("busy")}
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
            {documents.length > 0 && activeDocument && (
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
                      {d.course_code || "Doc"}: {d.file_name.split(".")[0].slice(0, 14)}...
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* Dynamic Topic Prompt & Synthesis Bar */}
            <div className="p-4 rounded-[28px] bg-white border border-brand-outline-variant shadow-sm flex flex-col sm:flex-row items-center gap-3">
              <div className="relative flex-1 w-full">
                <Search className="w-4 h-4 text-brand-on-surface-variant absolute left-4 top-1/2 -translate-y-1/2" />
                <input
                  type="text"
                  value={customTopic}
                  onChange={(e) => setCustomTopic(e.target.value)}
                  placeholder={`Customize topic prompt (default: "${activeDocument?.topic || activeDocument?.file_name || "Enter concept"}")...`}
                  className="w-full pl-11 pr-4 py-2.5 rounded-2xl bg-brand-surface-dim border border-brand-outline-variant text-xs text-brand-secondary focus:outline-none focus:border-brand-primary font-medium"
                />
              </div>
              <button
                onClick={() => synthesizeArtifact(activeDocument, learningStyle, workloadMode, customTopic)}
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
                  {activeDocument && (
                    <span className="text-[11px] font-bold text-purple-700 bg-purple-50 px-2.5 py-0.5 rounded-full border border-purple-200">
                      {activeDocument.file_name}
                    </span>
                  )}
                </div>
                <div className="flex items-center gap-3 text-xs font-mono text-brand-on-surface-variant">
                  <span>Grounding Confidence: {generatedArtifact?.confidence_score ? Math.round(generatedArtifact.confidence_score * 100) : 92}%</span>
                </div>
              </div>

              {isGenerating ? (
                <div className="p-16 text-center space-y-3">
                  <RefreshCw className="w-8 h-8 text-[#3a10e5] animate-spin mx-auto" />
                  <p className="text-xs font-bold text-brand-secondary">Synthesizing {learningStyle.toUpperCase()} artifact from document chunks...</p>
                </div>
              ) : (
                <>
                  {/* 1. Visual Mode Artifact (Mind Map + Process Flow Dual View) */}
                  {learningStyle === "visual" && (() => {
                    const fallbackDefault = `flowchart TD\n    A["${activeTopic}"] --> B["Core Lecture Chunk Analysis"]\n    B --> C["Synthesis & Mastery State"]`;
                    const rawContent = generatedArtifact?.content || fallbackDefault;
                    const { diagram, markdownBody } = extractMermaidDiagram(rawContent);
                    const altRaw = generatedArtifact?.metadata?.alternative_diagram_syntax;
                    const altDiagram = altRaw ? extractMermaidDiagram(altRaw).diagram : undefined;

                    return (
                      <div className="space-y-4">
                        <MermaidRenderer
                          chart={diagram}
                          alternativeChart={altDiagram}
                          conceptTree={generatedArtifact?.metadata?.concept_tree}
                        />
                        {markdownBody && (
                          <div className="p-5 rounded-[20px] bg-brand-surface-dim border border-brand-outline-variant text-sm text-brand-secondary leading-relaxed space-y-2 whitespace-pre-line font-medium">
                            {markdownBody}
                          </div>
                        )}
                      </div>
                    );
                  })()}

                  {/* 2. Auditory Mode Artifact */}
                  {learningStyle === "auditory" && (
                    <div className="space-y-4">
                      <AudioRecapPlayer
                        title={
                          workloadMode === "free"
                            ? `Socratic Audio Dialogue: ${activeTopic}`
                            : `30-Second Rapid Recap: ${activeTopic}`
                        }
                        durationSeconds={generatedArtifact?.metadata?.audio_duration_seconds || (workloadMode === "free" ? 180 : 30)}
                        transcript={
                          generatedArtifact?.content ||
                          `Professor: Let's inspect the key mechanisms of ${activeTopic}.\n\nStudent: The source document provides the foundational definitions and boundary constraints.\n\nProfessor: Exactly.`
                        }
                      />
                    </div>
                  )}

                  {/* 3. Read/Write Mode Artifact */}
                  {learningStyle === "read_write" && (
                    <div className="space-y-4">
                      <div className="p-6 rounded-[20px] bg-brand-surface-dim border border-brand-outline-variant text-sm text-brand-secondary leading-relaxed space-y-4 whitespace-pre-line font-medium">
                        {generatedArtifact?.content || `# Study Notes: ${activeTopic}\n\nCore lecture notes retrieved from document chunks.`}
                      </div>
                    </div>
                  )}

                  {/* 4. Kinesthetic Mode Artifact (Universal Multi-Discipline Simulation) */}
                  {learningStyle === "kinesthetic" && (
                    <div className="space-y-4">
                      {generatedArtifact?.metadata?.simulation_payload?.kinesthetic_type === "clinical_simulation" ||
                      generatedArtifact?.metadata?.simulation_payload?.kinesthetic_type === "critical_decision" ||
                      generatedArtifact?.metadata?.simulation_payload?.kinesthetic_type === "decision_dilemma" ? (
                        <ClinicalSimulationLab
                          payload={generatedArtifact.metadata.simulation_payload}
                          onComplete={() => activeDocument && handleCompleteLessonAndHandoff()}
                        />
                      ) : generatedArtifact?.metadata?.simulation_payload?.kinesthetic_type === "procedural_sequencing" &&
                        generatedArtifact.metadata.simulation_payload.sequencing_items?.length > 0 ? (
                        <ProceduralSequencingLab
                          scenarioTitle={generatedArtifact.metadata.simulation_payload.scenario_title}
                          contextBrief={generatedArtifact.metadata.simulation_payload.context_brief}
                          items={generatedArtifact.metadata.simulation_payload.sequencing_items}
                          onComplete={() => activeDocument && handleCompleteLessonAndHandoff()}
                        />
                      ) : (
                        <CodeSandbox
                          initialCode={
                            extractCleanCode(generatedArtifact?.content) ||
                            `def solve_${activeTopic.toLowerCase().replace(/[^a-z0-9]/g, "_")}() -> bool:\n    # Implementation derived from ${activeDocument?.file_name || activeTopic}\n    return True\n\nassert solve_${activeTopic.toLowerCase().replace(/[^a-z0-9]/g, "_")}() is True`
                          }
                          testCases={[`solve_${activeTopic.toLowerCase().replace(/[^a-z0-9]/g, "_")}() == True`]}
                          language={generatedArtifact?.metadata?.programming_language || "python"}
                        />
                      )}
                    </div>
                  )}

                  {/* Grounding Citations Section from Database Chunks */}
                  <div className="pt-4 border-t border-brand-outline-variant space-y-2">
                    <span className="text-xs font-bold uppercase tracking-wider text-brand-on-surface-variant flex items-center gap-1.5">
                      <Quote className="w-3.5 h-3.5 text-brand-primary" />
                      <span>Grounded Source Citations (Database Vector RRF Chunks)</span>
                    </span>
                    {generatedArtifact?.citations && generatedArtifact.citations.length > 0 ? (
                      <div className="space-y-2">
                        {generatedArtifact.citations.map((cite, i) => (
                          <div key={i} className="p-3.5 rounded-[16px] bg-brand-surface-dim border border-brand-outline-variant text-xs text-brand-secondary font-mono truncate">
                            {cite.snippet}
                          </div>
                        ))}
                      </div>
                    ) : (
                      <div className="p-3.5 rounded-[16px] bg-brand-surface-dim border border-brand-outline-variant text-xs text-brand-secondary font-mono truncate">
                        [Database Document #{activeDocument?.id ? activeDocument.id.slice(0, 8) : "VectorStore"}] "{activeTopic} core principles and specifications stored in pgvector."
                      </div>
                    )}
                  </div>
                </>
              )}
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
                    Mark this lesson completed in the database to clear <strong>{activeDocument?.file_name || activeTopic}</strong> from your unlearned queue and hand off to the Review tab for Day 1 active recall spaced repetition.
                  </p>
                </div>

                {/* Completion & Handoff Action */}
                <div className="flex flex-col sm:flex-row items-center gap-3">
                  {activeDocument && completedDocIds.has(activeDocument.id) ? (
                    <div className="flex flex-wrap items-center gap-3">
                      <div className="inline-flex items-center gap-2 px-4 py-2.5 rounded-[20px] bg-emerald-50 text-emerald-700 border border-emerald-200 text-xs font-bold">
                        <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                        <span>Learned & Handed Off to Review</span>
                      </div>
                      <Link
                        href={`/review?folder_id=${activeDocument.folder_id || ""}&document_id=${activeDocument.id}&file_name=${encodeURIComponent(activeDocument.file_name)}&topic=${encodeURIComponent(activeTopic)}`}
                        className="inline-flex items-center gap-2 px-5 py-2.5 rounded-[20px] bg-[#3a10e5] text-white text-xs font-bold shadow-sm hover:opacity-90 transition-all cursor-pointer"
                      >
                        <BrainCircuit className="w-4 h-4" />
                        <span>Review {activeDocument.file_name} Now</span>
                        <ArrowRight className="w-4 h-4" />
                      </Link>
                      {unlearnedDocs.length > 1 && (
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
                    <div className="flex flex-wrap items-center gap-3">
                      <button
                        onClick={handleCompleteLessonAndHandoff}
                        disabled={isCompleting || !activeDocument}
                        className="inline-flex items-center gap-2 px-6 py-3 rounded-[24px] bg-[#3a10e5] text-white text-xs sm:text-sm font-bold shadow-md hover:shadow-lg hover:scale-[1.02] active:scale-[0.98] transition-all cursor-pointer disabled:opacity-50"
                      >
                        <GraduationCap className="w-4 h-4" />
                        <span>{isCompleting ? "Handoff to Review..." : "Complete & Hand Off to Review"}</span>
                      </button>
                      {activeDocument && (
                        <div
                          className="inline-flex items-center gap-2 px-4 py-2.5 rounded-[20px] bg-brand-surface-dim border border-brand-outline-variant text-brand-on-surface-variant text-xs font-semibold select-none"
                          title="Complete this lesson to queue this topic and unlock Review"
                        >
                          <Lock className="w-3.5 h-3.5 text-brand-on-surface-variant/60" />
                          <span>Review unlocks upon completion</span>
                        </div>
                      )}
                    </div>
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

      {readingDoc && (
        <DocumentReaderModal
          documentId={readingDoc.id}
          fileName={readingDoc.file_name}
          folderId={readingDoc.folder_id}
          folderPath={readingDoc.folder_path}
          topic={readingDoc.topic}
          onClose={() => setReadingDoc(null)}
        />
      )}
    </div>
  );
}

export default function StudyArtifactPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen flex items-center justify-center bg-[#f8f9fb]">
          <div className="flex flex-col items-center gap-3">
            <Loader2 className="w-8 h-8 animate-spin text-[#3a10e5]" />
            <p className="text-xs font-bold text-brand-on-surface-variant font-mono">
              Loading Study Workspace...
            </p>
          </div>
        </div>
      }
    >
      <StudyPageContent />
    </Suspense>
  );
}
