"use client";

import { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import { 
  FolderTree, 
  Sparkles, 
  BrainCircuit, 
  ArrowRight, 
  BookOpen, 
  Calendar, 
  Clock, 
  Flame, 
  Layers, 
  CheckCircle,
  TrendingUp,
  ShieldAlert,
  ShieldCheck,
  RefreshCw,
  Plus,
  FileText,
  Activity,
  Award,
  GraduationCap,
  ExternalLink,
  ChevronRight,
  Loader2
} from "lucide-react";

import Navbar from "@/components/Navbar";
import WorkloadGauge from "@/components/WorkloadGauge";
import BurnoutGuardModal from "@/components/BurnoutGuardModal";
import OnboardingModal from "@/components/OnboardingModal";
import ManualEventModal from "@/components/ManualEventModal";
import DocumentReaderModal from "@/components/DocumentReaderModal";
import { useAuth } from "@/context/AuthContext";
import { createClient } from "@/lib/supabase/client";

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

interface FileReviewStats {
  document_id?: string;
  file_name: string;
  folder_id: string;
  folder_path: string;
  course_code?: string;
  course_name?: string;
  topic?: string;
  total_cards: number;
  due_cards_count: number;
  new_cards_count: number;
  learning_cards_count: number;
  graduated_cards_count: number;
  leech_cards_count: number;
  completion_percentage: number;
  mastery_percentage: number;
  needs_review_today: boolean;
  finished_today?: boolean;
  next_stage_label?: string;
  status: "needs_review" | "up_to_date" | "mastered" | "not_started";
  next_review_due?: string | null;
  recall_finished?: boolean;
  feynman_finished?: boolean;
  stage_breakdown?: {
    day_1?: number;
    day_3?: number;
    day_5?: number;
    day_7?: number;
    graduated?: number;
  };
}

interface DeckOverviewResponse {
  total_files: number;
  files_needing_review: number;
  total_due_cards: number;
  total_graduated_cards: number;
  overall_completion_percentage: number;
  files: FileReviewStats[];
}

interface CourseItem {
  id: string;
  name: string;
  code: string;
  term?: string;
  color?: string;
  description?: string;
}

interface AcademicEventItem {
  id: string;
  title: string;
  event_type: string;
  start_time: string;
  end_time?: string | null;
  weight?: number;
  source?: string;
  course_id?: string | null;
}

export default function DashboardPage() {
  const { user, profile, session } = useAuth();

  // Workload & Engine States
  const [workloadScore, setWorkloadScore] = useState<number>(0.0);
  const [activeMode, setActiveMode] = useState<"free" | "busy" | "hysteresis_hold">("free");
  const [activeEventCount, setActiveEventCount] = useState<number>(0);
  const [criticalEvents, setCriticalEvents] = useState<string[]>([]);
  const [learningStyle, setLearningStyle] = useState(profile?.learning_style || "read_write");

  // Real Database Data States
  const [deckOverview, setDeckOverview] = useState<DeckOverviewResponse | null>(null);
  const [studyQueue, setStudyQueue] = useState<DbStudyDocument[]>([]);
  const [courses, setCourses] = useState<CourseItem[]>([]);
  const [events, setEvents] = useState<AcademicEventItem[]>([]);
  
  // UI & Modal States
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isRefreshing, setIsRefreshing] = useState<boolean>(false);
  const [showBurnoutModal, setShowBurnoutModal] = useState<boolean>(false);
  const [showOnboarding, setShowOnboarding] = useState<boolean>(false);
  const [showEventModal, setShowEventModal] = useState<boolean>(false);
  const [readingDoc, setReadingDoc] = useState<{
    id: string;
    fileName: string;
    folderId?: string;
    folderPath?: string;
    topic?: string;
  } | null>(null);

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

  // Master fetch strictly for real data
  const fetchAllRealData = useCallback(async () => {
    setIsRefreshing(true);
    const headers = getHeaders();

    try {
      // 1. Fetch live workload calculation
      const workloadPromise = fetch(`${API_URL}/workload/live`, { headers })
        .then((res) => (res.ok ? res.json() : null))
        .catch(() => null);

      // 2. Fetch deck overview
      const deckPromise = fetch(`${API_URL}/flashcards/deck-overview`, { headers })
        .then((res) => (res.ok ? res.json() : null))
        .catch(() => null);

      // 3. Fetch study queue
      const queuePromise = fetch(`${API_URL}/study/queue`, { headers })
        .then((res) => (res.ok ? res.json() : null))
        .catch(() => null);

      // 4. Fetch academic courses
      const coursesPromise = fetch(`${API_URL}/courses`, { headers })
        .then((res) => (res.ok ? res.json() : null))
        .catch(() => null);

      // 5. Fetch calendar events
      const eventsPromise = fetch(`${API_URL}/events`, { headers })
        .then((res) => (res.ok ? res.json() : null))
        .catch(async () => {
          // Fallback to direct client Supabase query if needed
          try {
            const supabase = createClient();
            const { data } = await supabase
              .from("events")
              .select("*")
              .order("start_time", { ascending: false })
              .limit(10);
            return data || [];
          } catch {
            return [];
          }
        });

      const [workloadData, deckData, queueData, coursesData, eventsData] = await Promise.all([
        workloadPromise,
        deckPromise,
        queuePromise,
        coursesPromise,
        eventsPromise,
      ]);

      if (workloadData) {
        setWorkloadScore(typeof workloadData.score === "number" ? workloadData.score : 0.0);
        setActiveMode(workloadData.current_mode || "free");
        setActiveEventCount(workloadData.active_event_count || 0);
        if (Array.isArray(workloadData.critical_events)) {
          setCriticalEvents(workloadData.critical_events);
        }
      }

      if (deckData) {
        setDeckOverview(deckData);
      }

      if (Array.isArray(queueData)) {
        setStudyQueue(queueData);
      }

      if (Array.isArray(coursesData)) {
        setCourses(coursesData);
      }

      if (Array.isArray(eventsData)) {
        setEvents(eventsData);
        // If critical_events was empty, populate from upcoming event titles
        if (!workloadData?.critical_events || workloadData.critical_events.length === 0) {
          const nowIso = new Date().toISOString();
          const upcoming = eventsData
            .filter((e: any) => e.start_time >= nowIso)
            .slice(0, 3)
            .map((e: any) => e.title);
          if (upcoming.length > 0) {
            setCriticalEvents(upcoming);
          }
        }
      }
    } catch (err) {
      console.warn("Could not synchronize live dashboard data:", err);
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  }, [API_URL, getHeaders]);

  useEffect(() => {
    if (profile) {
      if (profile.learning_style) {
        setLearningStyle(profile.learning_style);
      }
      if (profile.onboarding_completed === false || !profile.learning_style) {
        setShowOnboarding(true);
      }
    } else {
      if (typeof window !== "undefined") {
        const completed = localStorage.getItem("learnsync_onboarding_completed");
        const cachedStyle = localStorage.getItem("learnsync_learning_style");
        if (completed !== "true" || !cachedStyle) {
          setShowOnboarding(true);
        } else {
          setLearningStyle(cachedStyle as any);
        }
      }
    }
    fetchAllRealData();
  }, [profile, fetchAllRealData]);

  const handleConnectGoogle = async () => {
    try {
      const res = await fetch(`${API_URL}/oauth/google/url`, {
        headers: getHeaders(),
      });
      if (res.ok) {
        const data = await res.json();
        if (data.auth_url) {
          window.open(data.auth_url, "_blank");
        }
      }
    } catch (err) {
      console.error("Google OAuth URL error:", err);
    }
  };

  const getStyleDisplayName = (style: string) => {
    switch (style) {
      case "visual":
        return "Visual Architect";
      case "auditory":
        return "Auditory Socratic";
      case "read_write":
        return "Read/Write Pragmatist";
      case "kinesthetic":
        return "Kinesthetic Lab";
      default:
        return "Adaptive Learner";
    }
  };

  // Format event date nicely
  const formatEventDate = (isoString: string) => {
    try {
      const d = new Date(isoString);
      return d.toLocaleDateString("en-US", {
        month: "short",
        day: "numeric",
        hour: "numeric",
        minute: "2-digit",
      });
    } catch {
      return isoString;
    }
  };

  return (
    <div className="min-h-screen flex flex-col bg-[#f8f9fb]">
      <Navbar
        workloadScore={workloadScore}
        activeMode={activeMode}
        learningStyle={learningStyle}
        onOpenBurnoutModal={() => setShowBurnoutModal(true)}
        onOpenOnboardingModal={() => setShowOnboarding(true)}
      />

      <main className="flex-1 max-w-7xl w-full mx-auto px-6 py-8 space-y-8">
        {/* Top Hero Command Section */}
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
          <div>
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-brand-tertiary-container border border-brand-tertiary/40 text-xs font-bold text-brand-on-tertiary-container mb-2">
              <span className="w-2 h-2 rounded-full bg-brand-tertiary-dim animate-pulse" />
              <span>
                {profile?.full_name ? `Student: ${profile.full_name}` : "Workspace Connected"}
              </span>
              <span className="text-brand-on-tertiary-container/60 font-mono text-[10px]">
                • {getStyleDisplayName(learningStyle)}
              </span>
            </div>
            <h1 className="text-4xl font-black text-brand-secondary tracking-tight">
              Adaptive Study Cockpit
            </h1>
            <p className="text-brand-on-surface-variant text-sm mt-1 max-w-2xl">
              Real-time cognitive workload monitor, materialized virtual folder repository, and 2357 spaced repetition active recall engine.
            </p>
          </div>

          <div className="flex items-center flex-wrap gap-2.5">
            <button
              onClick={() => setShowEventModal(true)}
              className="px-4 py-2.5 rounded-[18px] bg-brand-primary text-white text-xs font-bold transition-all shadow-sm hover:bg-brand-primary/90 flex items-center gap-1.5"
            >
              <Plus className="w-3.5 h-3.5" />
              <span>Add Deadline</span>
            </button>
            <button
              onClick={handleConnectGoogle}
              className="px-4 py-2.5 rounded-[18px] bg-white hover:bg-brand-surface-dim border border-brand-outline-variant text-xs font-bold text-brand-secondary transition-all shadow-sm flex items-center gap-1.5"
            >
              <Calendar className="w-3.5 h-3.5 text-brand-on-surface-variant" />
              <span>Sync Calendar</span>
            </button>
            <button
              onClick={() => setShowOnboarding(true)}
              className="px-4 py-2.5 rounded-[18px] bg-white hover:bg-brand-surface-dim border border-brand-outline-variant text-xs font-bold text-brand-secondary transition-all shadow-sm flex items-center gap-1.5"
            >
              <span>Change Style</span>
            </button>
            <button
              onClick={fetchAllRealData}
              disabled={isRefreshing}
              title="Refresh live data from database"
              className="p-2.5 rounded-[18px] bg-white hover:bg-brand-surface-dim border border-brand-outline-variant text-brand-secondary transition-all shadow-sm flex items-center justify-center disabled:opacity-50"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${isRefreshing ? "animate-spin text-brand-primary" : ""}`} />
            </button>
          </div>
        </div>

        {/* Real Workload Cockpit Gauge Card */}
        <WorkloadGauge
          score={workloadScore}
          mode={activeMode}
          activeEventCount={activeEventCount}
          criticalEvents={criticalEvents}
        />

        {/* 3 Interactive Quick Action Modules (rounded-[32px]) */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Virtual Folders Hub */}
          <Link 
            href="/folders" 
            className="bg-white border border-brand-outline-variant shadow-elevation-sm hover:shadow-elevation-md rounded-[32px] p-7 group block transition-all duration-200"
          >
            <div className="flex items-center justify-between mb-4">
              <div className="w-12 h-12 rounded-[16px] bg-brand-primary/10 border border-brand-primary/20 flex items-center justify-center text-brand-primary group-hover:scale-105 transition-transform duration-150">
                <FolderTree className="w-6 h-6" />
              </div>
              <span className="text-xs font-mono font-bold px-2.5 py-1 rounded-full bg-brand-surface-dim border border-brand-outline-variant text-brand-secondary">
                {courses.length} {courses.length === 1 ? "Course" : "Courses"}
              </span>
            </div>
            <h3 className="text-xl font-black text-brand-secondary mb-2 flex items-center justify-between">
              <span>Virtual Folders</span>
              <ArrowRight className="w-4 h-4 text-brand-on-surface-variant group-hover:text-brand-primary group-hover:translate-x-1 transition-all" />
            </h3>
            <p className="text-xs text-brand-on-surface-variant leading-relaxed">
              Explore course material mapped to materialized week paths, upload lecture notes, and read papers via the distraction-free PDF viewer.
            </p>
          </Link>

          {/* Multimodal Study Engine */}
          <Link 
            href="/study" 
            className="bg-white border border-brand-outline-variant shadow-elevation-sm hover:shadow-elevation-md rounded-[32px] p-7 group block transition-all duration-200"
          >
            <div className="flex items-center justify-between mb-4">
              <div className="w-12 h-12 rounded-[16px] bg-brand-primary/10 border border-brand-primary/20 flex items-center justify-center text-brand-primary group-hover:scale-105 transition-transform duration-150">
                <Sparkles className="w-6 h-6" />
              </div>
              <span className="text-xs font-mono font-bold px-2.5 py-1 rounded-full bg-brand-surface-dim border border-brand-outline-variant text-brand-secondary">
                {studyQueue.length} In Queue
              </span>
            </div>
            <h3 className="text-xl font-black text-brand-secondary mb-2 flex items-center justify-between">
              <span>Multimodal Study</span>
              <ArrowRight className="w-4 h-4 text-brand-on-surface-variant group-hover:text-brand-primary group-hover:translate-x-1 transition-all" />
            </h3>
            <p className="text-xs text-brand-on-surface-variant leading-relaxed">
              Generate grounded Mermaid diagrams, Socratic dialogue scripts, code labs, and Pareto cheat-sheets tailored to your VARK archetype.
            </p>
          </Link>

          {/* Spaced Repetition & Feynman Loop */}
          <Link 
            href="/review" 
            className="bg-white border border-brand-outline-variant shadow-elevation-sm hover:shadow-elevation-md rounded-[32px] p-7 group block transition-all duration-200"
          >
            <div className="flex items-center justify-between mb-4">
              <div className="w-12 h-12 rounded-[16px] bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-600 group-hover:scale-105 transition-transform duration-150">
                <BrainCircuit className="w-6 h-6" />
              </div>
              <span className={`text-xs font-mono font-bold px-2.5 py-1 rounded-full border ${
                (deckOverview?.total_due_cards || 0) > 0
                  ? "bg-rose-50 text-rose-700 border-rose-200"
                  : "bg-emerald-50 text-emerald-700 border-emerald-200"
              }`}>
                {deckOverview?.total_due_cards || 0} Due Today
              </span>
            </div>
            <h3 className="text-xl font-black text-brand-secondary mb-2 flex items-center justify-between">
              <span>Review & Feynman</span>
              <ArrowRight className="w-4 h-4 text-brand-on-surface-variant group-hover:text-emerald-600 group-hover:translate-x-1 transition-all" />
            </h3>
            <p className="text-xs text-brand-on-surface-variant leading-relaxed">
              Adaptive 2357 schedule flashcard deck with raw memory recall blurting and Feynman plain-language precision gap analysis.
            </p>
          </Link>
        </div>

        {/* Section 1: Active 2357 Spaced Repetition Decks (Real Data) */}
        <div className="bg-white border border-brand-outline-variant shadow-elevation-sm rounded-[32px] p-8 space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-brand-outline-variant pb-4">
            <div>
              <div className="flex items-center gap-2.5">
                <div className="w-2.5 h-2.5 rounded-full bg-emerald-500" />
                <h2 className="text-2xl font-black text-brand-secondary tracking-tight">
                  Active Spaced Repetition Decks
                </h2>
              </div>
              <p className="text-xs text-brand-on-surface-variant mt-1">
                Real documents that reached Review state. Tracked along the 2357 schedule (Day 1 → Day 3 → Day 5 → Day 7 → Graduated).
              </p>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-mono font-bold px-3 py-1 rounded-full bg-brand-surface-dim border border-brand-outline-variant text-brand-secondary">
                Overall Retention: {deckOverview?.overall_completion_percentage ?? 0}%
              </span>
              <Link 
                href="/review"
                className="text-xs font-bold text-brand-primary hover:underline flex items-center gap-1"
              >
                <span>Full Review Hub</span>
                <ChevronRight className="w-3.5 h-3.5" />
              </Link>
            </div>
          </div>

          {isLoading ? (
            <div className="py-12 flex flex-col items-center justify-center text-center">
              <Loader2 className="w-6 h-6 text-brand-primary animate-spin mb-2" />
              <p className="text-xs text-brand-on-surface-variant">Loading spaced repetition deck overview...</p>
            </div>
          ) : !deckOverview || deckOverview.files.length === 0 ? (
            <div className="py-10 text-center rounded-[24px] bg-brand-surface-dim border border-brand-outline-variant p-6">
              <BookOpen className="w-8 h-8 text-brand-on-surface-variant mx-auto mb-2 opacity-50" />
              <h4 className="text-sm font-bold text-brand-secondary">No Flashcard Decks in Review Yet</h4>
              <p className="text-xs text-brand-on-surface-variant max-w-md mx-auto mt-1">
                Complete a lesson in Multimodal Study to hand off documents into the 2357 spaced repetition schedule.
              </p>
              <Link 
                href="/study"
                className="inline-flex items-center gap-1.5 px-4 py-2 mt-4 rounded-[16px] bg-brand-primary text-white text-xs font-bold shadow-sm"
              >
                <Sparkles className="w-3.5 h-3.5" />
                <span>Go to Study Queue</span>
              </Link>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {deckOverview.files.map((file) => {
                const masteryPct = Math.round(file.mastery_percentage || file.completion_percentage || 0);
                const isDueToday = file.needs_review_today || file.due_cards_count > 0;
                return (
                  <div 
                    key={file.document_id || file.file_name} 
                    className="bg-brand-surface-dim/40 border border-brand-outline-variant hover:border-brand-primary/40 rounded-[24px] p-6 space-y-4 transition-all duration-200"
                  >
                    <div className="flex items-center justify-between">
                      <span className="px-2.5 py-0.5 rounded-full bg-white border border-brand-outline-variant text-[11px] font-mono font-bold text-brand-primary">
                        {file.course_code || "ACADEMIC"}
                      </span>
                      <span className={`text-[11px] font-bold px-2.5 py-0.5 rounded-full border ${
                        isDueToday 
                          ? "bg-rose-50 text-rose-700 border-rose-200"
                          : file.finished_today
                          ? "bg-emerald-50 text-emerald-700 border-emerald-200"
                          : "bg-blue-50 text-blue-700 border-blue-200"
                      }`}>
                        {isDueToday 
                          ? `${file.due_cards_count} Due Today` 
                          : file.finished_today 
                          ? "Reviewed Today" 
                          : "Up to Date"}
                      </span>
                    </div>

                    <div>
                      <h3 
                        onClick={() => setReadingDoc({
                          id: file.document_id || "",
                          fileName: file.file_name,
                          folderId: file.folder_id,
                          folderPath: file.folder_path,
                          topic: file.topic,
                        })}
                        className="text-base font-black text-brand-secondary tracking-tight truncate cursor-pointer hover:text-brand-primary transition-colors"
                        title={file.file_name}
                      >
                        {file.file_name}
                      </h3>
                      <p className="text-xs text-brand-on-surface-variant font-mono mt-0.5 truncate">
                        {file.folder_path || "/material"}
                      </p>
                    </div>

                    {/* Schedule Stage & BKT Mastery Meter */}
                    <div className="space-y-1.5">
                      <div className="flex items-center justify-between text-xs">
                        <span className="text-brand-on-surface-variant font-medium">
                          {file.next_stage_label || "2357 Schedule"}
                        </span>
                        <span className="font-mono font-bold text-brand-secondary">{masteryPct}%</span>
                      </div>
                      <div className="w-full h-2 bg-brand-surface-container-highest rounded-full overflow-hidden">
                        <div
                          className={`h-full rounded-full transition-all duration-500 ${
                            masteryPct >= 85 ? "bg-emerald-500" : masteryPct >= 40 ? "bg-brand-primary" : "bg-brand-tertiary-dim"
                          }`}
                          style={{ width: `${Math.max(8, masteryPct)}%` }}
                        />
                      </div>
                    </div>

                    {/* Action Seams: Read PDF, Review Cards */}
                    <div className="pt-3 border-t border-brand-outline-variant flex items-center justify-between gap-2">
                      <button
                        onClick={() => setReadingDoc({
                          id: file.document_id || "",
                          fileName: file.file_name,
                          folderId: file.folder_id,
                          folderPath: file.folder_path,
                          topic: file.topic,
                        })}
                        className="px-3 py-1.5 rounded-[14px] bg-white hover:bg-brand-surface-dim border border-brand-outline-variant text-xs font-bold text-brand-secondary transition-all flex items-center gap-1.5 shadow-sm"
                        title="Read complete document content"
                      >
                        <BookOpen className="w-3.5 h-3.5 text-brand-primary" />
                        <span>Read</span>
                      </button>

                      <Link
                        href={`/review?document_id=${file.document_id || ""}&file_name=${encodeURIComponent(file.file_name)}`}
                        className={`px-3.5 py-1.5 rounded-[14px] text-xs font-bold transition-all shadow-sm flex items-center gap-1.5 ${
                          isDueToday
                            ? "bg-brand-primary hover:bg-brand-primary/90 text-white"
                            : "bg-brand-surface-dim hover:bg-brand-outline-variant/50 text-brand-secondary border border-brand-outline-variant"
                        }`}
                      >
                        <BrainCircuit className="w-3.5 h-3.5" />
                        <span>{isDueToday ? "Review Now" : "Open Deck"}</span>
                      </Link>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Section 2: Real Study Queue & Document Ingestion (Real Data) */}
        <div className="bg-white border border-brand-outline-variant shadow-elevation-sm rounded-[32px] p-8 space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-brand-outline-variant pb-4">
            <div>
              <div className="flex items-center gap-2.5">
                <div className="w-2.5 h-2.5 rounded-full bg-brand-primary" />
                <h2 className="text-2xl font-black text-brand-secondary tracking-tight">
                  Unlearned Course Materials
                </h2>
              </div>
              <p className="text-xs text-brand-on-surface-variant mt-1">
                Real documents in your repository waiting for Multimodal Synthesis (Socratic scripts, flowcharts, code sandboxes).
              </p>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-mono font-bold px-3 py-1 rounded-full bg-brand-surface-dim border border-brand-outline-variant text-brand-secondary">
                {studyQueue.length} Ready to Learn
              </span>
              <Link 
                href="/study"
                className="text-xs font-bold text-brand-primary hover:underline flex items-center gap-1"
              >
                <span>Study Workspace</span>
                <ChevronRight className="w-3.5 h-3.5" />
              </Link>
            </div>
          </div>

          {isLoading ? (
            <div className="py-12 flex flex-col items-center justify-center text-center">
              <Loader2 className="w-6 h-6 text-brand-primary animate-spin mb-2" />
              <p className="text-xs text-brand-on-surface-variant">Loading study queue documents...</p>
            </div>
          ) : studyQueue.length === 0 ? (
            <div className="py-10 text-center rounded-[24px] bg-brand-surface-dim border border-brand-outline-variant p-6">
              <CheckCircle className="w-8 h-8 text-emerald-500 mx-auto mb-2 opacity-80" />
              <h4 className="text-sm font-bold text-brand-secondary">All Uploaded Materials Learned!</h4>
              <p className="text-xs text-brand-on-surface-variant max-w-md mx-auto mt-1">
                You have synthesized all available documents. Upload new lecture slides or PDFs in Virtual Folders to continue.
              </p>
              <Link 
                href="/folders"
                className="inline-flex items-center gap-1.5 px-4 py-2 mt-4 rounded-[16px] bg-brand-primary text-white text-xs font-bold shadow-sm"
              >
                <FolderTree className="w-3.5 h-3.5" />
                <span>Manage Virtual Folders</span>
              </Link>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {studyQueue.slice(0, 6).map((doc) => (
                <div 
                  key={doc.id}
                  className="bg-brand-surface-dim/40 border border-brand-outline-variant hover:border-brand-primary/40 rounded-[24px] p-6 space-y-4 transition-all duration-200"
                >
                  <div className="flex items-center justify-between">
                    <span className="px-2.5 py-0.5 rounded-full bg-white border border-brand-outline-variant text-[11px] font-mono font-bold text-brand-primary">
                      {doc.course_code || "STUDY"}
                    </span>
                    <span className="text-xs text-brand-on-surface-variant font-medium flex items-center gap-1">
                      <Clock className="w-3.5 h-3.5" />
                      {doc.estimated_read_time || "5 min read"}
                    </span>
                  </div>

                  <div>
                    <h3 
                      onClick={() => setReadingDoc({
                        id: doc.id,
                        fileName: doc.file_name,
                        folderId: doc.folder_id,
                        folderPath: doc.folder_path,
                        topic: doc.topic,
                      })}
                      className="text-base font-black text-brand-secondary tracking-tight truncate cursor-pointer hover:text-brand-primary transition-colors"
                      title={doc.file_name}
                    >
                      {doc.file_name}
                    </h3>
                    <p className="text-xs text-brand-on-surface-variant font-mono mt-0.5 truncate">
                      {doc.folder_path || doc.course_name || "/unfiled"}
                    </p>
                  </div>

                  <div className="pt-3 border-t border-brand-outline-variant flex items-center justify-between gap-2">
                    <button
                      onClick={() => setReadingDoc({
                        id: doc.id,
                        fileName: doc.file_name,
                        folderId: doc.folder_id,
                        folderPath: doc.folder_path,
                        topic: doc.topic,
                      })}
                      className="px-3 py-1.5 rounded-[14px] bg-white hover:bg-brand-surface-dim border border-brand-outline-variant text-xs font-bold text-brand-secondary transition-all flex items-center gap-1.5 shadow-sm"
                    >
                      <BookOpen className="w-3.5 h-3.5 text-brand-primary" />
                      <span>Read File</span>
                    </button>

                    <Link
                      href={`/study?document_id=${doc.id}&file_name=${encodeURIComponent(doc.file_name)}`}
                      className="px-3.5 py-1.5 rounded-[14px] bg-brand-primary hover:bg-brand-primary/90 text-white text-xs font-bold transition-all shadow-sm flex items-center gap-1.5"
                    >
                      <Sparkles className="w-3.5 h-3.5" />
                      <span>Synthesize</span>
                    </Link>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Section 3: Live Academic Deadlines & Calendar Timeline (Real Data) */}
        <div className="bg-white border border-brand-outline-variant shadow-elevation-sm rounded-[32px] p-8 space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-brand-outline-variant pb-4">
            <div>
              <div className="flex items-center gap-2.5">
                <Calendar className="w-5 h-5 text-brand-primary" />
                <h2 className="text-2xl font-black text-brand-secondary tracking-tight">
                  Academic Schedule & Deadlines
                </h2>
              </div>
              <p className="text-xs text-brand-on-surface-variant mt-1">
                Real deadlines synchronized from course syllabi, manual entries, and Google Calendar.
              </p>
            </div>
            <button
              onClick={() => setShowEventModal(true)}
              className="px-3.5 py-1.5 rounded-[16px] bg-brand-surface-dim hover:bg-brand-outline-variant/50 border border-brand-outline-variant text-xs font-bold text-brand-secondary transition-all flex items-center gap-1.5 shadow-sm"
            >
              <Plus className="w-3.5 h-3.5 text-brand-primary" />
              <span>+ Add Event</span>
            </button>
          </div>

          {events.length === 0 ? (
            <div className="py-8 text-center rounded-[24px] bg-brand-surface-dim border border-brand-outline-variant p-6">
              <Calendar className="w-8 h-8 text-brand-on-surface-variant mx-auto mb-2 opacity-50" />
              <h4 className="text-sm font-bold text-brand-secondary">No Deadlines Scheduled</h4>
              <p className="text-xs text-brand-on-surface-variant max-w-sm mx-auto mt-1">
                Add an upcoming exam, project submission, or quiz to allow the Schmitt Hysteresis Workload Engine to automatically protect your cognitive bandwidth.
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {events.slice(0, 6).map((evt) => {
                const isExam = evt.event_type?.toLowerCase().includes("exam");
                const isQuiz = evt.event_type?.toLowerCase().includes("quiz");
                return (
                  <div
                    key={evt.id}
                    className="p-4 rounded-[20px] bg-brand-surface-dim/50 border border-brand-outline-variant flex items-start justify-between gap-3"
                  >
                    <div className="space-y-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider ${
                          isExam 
                            ? "bg-rose-100 text-rose-800"
                            : isQuiz
                            ? "bg-amber-100 text-amber-800"
                            : "bg-blue-100 text-blue-800"
                        }`}>
                          {evt.event_type || "assignment"}
                        </span>
                        {evt.weight && (
                          <span className="text-[10px] font-mono text-brand-on-surface-variant">
                            weight: {evt.weight}x
                          </span>
                        )}
                      </div>
                      <h4 className="text-sm font-bold text-brand-secondary tracking-tight truncate" title={evt.title}>
                        {evt.title}
                      </h4>
                      <p className="text-xs text-brand-on-surface-variant flex items-center gap-1">
                        <Clock className="w-3 h-3" />
                        <span>{formatEventDate(evt.start_time)}</span>
                      </p>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </main>

      {/* Pop-Up Modal: Real Document Reader */}
      {readingDoc && (
        <DocumentReaderModal
          documentId={readingDoc.id}
          fileName={readingDoc.fileName}
          folderId={readingDoc.folderId}
          folderPath={readingDoc.folderPath}
          topic={readingDoc.topic}
          onClose={() => setReadingDoc(null)}
        />
      )}

      {/* Manual Deadline Creation Modal */}
      <ManualEventModal
        isOpen={showEventModal}
        onClose={() => setShowEventModal(false)}
        onEventCreated={fetchAllRealData}
        userId={user?.id}
      />

      {/* Burnout Guard Modal */}
      <BurnoutGuardModal
        isOpen={showBurnoutModal}
        onClose={() => setShowBurnoutModal(false)}
      />

      {/* Onboarding Style Modal */}
      <OnboardingModal
        isOpen={showOnboarding}
        onSave={(style) => {
          setLearningStyle(style);
          setShowOnboarding(false);
        }}
      />
    </div>
  );
}
