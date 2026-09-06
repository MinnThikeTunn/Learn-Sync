"use client";

import { useState, useEffect, useCallback, useMemo, Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { 
  BrainCircuit, 
  Sparkles, 
  RotateCw, 
  CheckCircle2, 
  AlertTriangle, 
  Clock, 
  ShieldAlert,
  ArrowRight,
  Flame,
  Activity,
  Plus,
  RefreshCw,
  FileText,
  CalendarCheck,
  Check,
  Award,
  Zap,
  HelpCircle,
  FolderTree,
  BookOpen,
  Filter,
  Loader2,
  Layers,
  ArrowLeft,
  Calendar,
  TrendingUp,
  Play,
  CheckCircle,
  Timer
} from "lucide-react";
import Link from "next/link";
import Navbar from "@/components/Navbar";
import OnboardingModal from "@/components/OnboardingModal";
import { useAuth } from "@/context/AuthContext";

interface ReviewCard {
  id: string;
  front: string;
  back: string;
  stage: string;
  stability?: number;
  difficulty?: number;
  reps?: number;
  lapses?: number;
  is_leech?: boolean;
  folder_id?: string;
  folder_path?: string;
  folder?: string;
  document_id?: string;
  file_name?: string;
  topic?: string;
}

interface DbDocumentSummary {
  id: string;
  file_name: string;
  folder_id?: string;
  folder_path?: string;
  topic?: string;
  course_code?: string;
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
  stage_breakdown: {
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

function ReviewContent() {
  const { user } = useAuth();
  const searchParams = useSearchParams();
  const router = useRouter();

  // Query parameters from Study tab
  const folderIdParam = searchParams.get("folder_id") || "";
  const documentIdParam = searchParams.get("document_id") || "";
  const fileNameParam = searchParams.get("file_name") || "";
  const topicParam = searchParams.get("topic") || "";

  const [showOnboarding, setShowOnboarding] = useState(false);
  const [tab, setTab] = useState<"flashcards" | "blurting" | "feynman">("flashcards");
  
  // Flashcards Sub-View: Anki Decks Overview vs Active Card Player
  const [flashcardViewMode, setFlashcardViewMode] = useState<"decks" | "player">(
    fileNameParam ? "player" : "decks"
  );
  const [deckFilter, setDeckFilter] = useState<"all" | "needs_review" | "up_to_date" | "mastered">("all");

  const [cardIndex, setCardIndex] = useState(0);
  const [isFlipped, setIsFlipped] = useState(false);
  const [isLoadingCards, setIsLoadingCards] = useState(true);
  const [isAutoProvisioning, setIsAutoProvisioning] = useState(false);

  // Deck Overview stats from backend
  const [deckOverview, setDeckOverview] = useState<DeckOverviewResponse | null>(null);
  const [isLoadingOverview, setIsLoadingOverview] = useState(true);
  
  // Available database documents for filtering & switching
  const [dbDocuments, setDbDocuments] = useState<DbDocumentSummary[]>([]);
  const [selectedFileFilter, setSelectedFileFilter] = useState<string>(fileNameParam || "all");

  // Feynman states
  const [explanation, setExplanation] = useState("");
  const [concept, setConcept] = useState(topicParam || "Recursion & Base Cases");
  const [feynmanPrompt, setFeynmanPrompt] = useState(
    topicParam 
      ? `Explain the core concepts and invariants of ${topicParam} in plain, intuitive language.`
      : "Explain recursion as if you were teaching a 10-year-old child."
  );
  const [isEvaluating, setIsEvaluating] = useState(false);
  const [feynmanFeedback, setFeynmanFeedback] = useState<any>(null);

  // Blurting states
  const [blurtingTopic, setBlurtingTopic] = useState(topicParam || "Recursion & Call Stack Frames");
  const [blurtingText, setBlurtingText] = useState("");
  const [isEvaluatingBlurting, setIsEvaluatingBlurting] = useState(false);
  const [blurtingResult, setBlurtingResult] = useState<any>(null);

  const [cards, setCards] = useState<ReviewCard[]>([]);
  const [reviewedCardIds, setReviewedCardIds] = useState<Set<string>>(new Set());
  const [isRecordingFinished, setIsRecordingFinished] = useState(false);
  const [finishResult, setFinishResult] = useState<{
    status: string;
    message: string;
    file_name: string;
    cards_completed: number;
    current_stage?: string;
    next_stage?: string;
    next_review_due?: string;
  } | null>(null);

  // 1. Fetch Deck Overview from backend
  const fetchDeckOverview = useCallback(async () => {
    setIsLoadingOverview(true);
    try {
      const res = await fetch("http://localhost:8000/api/v1/flashcards/deck-overview", {
        headers: { "X-Test-User-Id": user?.id || "00000000-0000-0000-0000-000000000001" },
      });
      if (res.ok) {
        const data = await res.json();
        setDeckOverview(data);
      }
    } catch (err) {
      console.warn("Failed to fetch deck overview:", err);
    } finally {
      setIsLoadingOverview(false);
    }
  }, [user]);

  // 2. Fetch available documents from database queue
  useEffect(() => {
    const fetchDocuments = async () => {
      try {
        const res = await fetch("http://localhost:8000/api/v1/study/queue", {
          headers: { "X-Test-User-Id": user?.id || "00000000-0000-0000-0000-000000000001" },
        });
        if (res.ok) {
          const data = await res.json();
          if (Array.isArray(data)) {
            setDbDocuments(data);
          }
        }
      } catch (err) {
        console.warn("Could not load documents queue for review filtering:", err);
      }
    };
    fetchDocuments();
    fetchDeckOverview();
  }, [user, fetchDeckOverview]);

  // Update filter when query param changes
  useEffect(() => {
    if (fileNameParam) {
      setSelectedFileFilter(fileNameParam);
      setFlashcardViewMode("player");
    }
    if (topicParam) {
      setBlurtingTopic(topicParam);
      setConcept(topicParam);
      setFeynmanPrompt(`Explain the core concepts and invariants of ${topicParam} in plain, intuitive language.`);
    }
  }, [fileNameParam, topicParam]);

  // 3. Fetch due flashcards with folder/document context
  const fetchDueCards = useCallback(async () => {
    setIsLoadingCards(true);
    try {
      const params = new URLSearchParams();
      if (folderIdParam) params.append("folder_id", folderIdParam);
      if (documentIdParam) params.append("document_id", documentIdParam);
      params.append("include_immediate", "true");

      const res = await fetch(`http://localhost:8000/api/v1/flashcards/due?${params.toString()}`, {
        headers: { "X-Test-User-Id": user?.id || "00000000-0000-0000-0000-000000000001" },
      });

      if (res.ok) {
        const data = await res.json();
        if (Array.isArray(data) && data.length > 0) {
          const formatted: ReviewCard[] = data.map((c: any) => {
            const matchedDoc = dbDocuments.find(d => (c.document_id && d.id === c.document_id) || (c.folder_id && d.folder_id === c.folder_id));
            const resolvedFileName = c.file_name || matchedDoc?.file_name || ((documentIdParam && c.document_id === documentIdParam) ? fileNameParam : null) || (fileNameParam && !folderIdParam ? fileNameParam : null) || "Document";
            return {
              ...c,
              file_name: resolvedFileName,
              topic: c.topic || matchedDoc?.topic || topicParam || "Active Revision",
            };
          });
          setCards(formatted);
          setCardIndex(0);
          setReviewedCardIds(new Set());
        } else if (fileNameParam && (folderIdParam || documentIdParam)) {
          // Auto-provision if arriving directly from study tab for fresh doc
          autoProvisionFileCards();
        } else {
          // Fallback: fetch all due cards
          const allRes = await fetch("http://localhost:8000/api/v1/flashcards/due?include_immediate=true", {
            headers: { "X-Test-User-Id": user?.id || "00000000-0000-0000-0000-000000000001" },
          });
          if (allRes.ok) {
            const allData = await allRes.json();
            if (Array.isArray(allData) && allData.length > 0) {
              setCards(allData);
              setCardIndex(0);
              setReviewedCardIds(new Set());
            } else {
              setCards([]);
            }
          }
        }
      }
    } catch (err) {
      console.warn("Failed to load cards from backend:", err);
    } finally {
      setIsLoadingCards(false);
    }
  }, [folderIdParam, documentIdParam, fileNameParam, topicParam, user, dbDocuments]);

  // Auto-provision flashcards for newly completed document if queue returned empty
  const autoProvisionFileCards = async () => {
    setIsAutoProvisioning(true);
    try {
      const res = await fetch("http://localhost:8000/api/v1/study/complete-lesson", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-Test-User-Id": user?.id || "00000000-0000-0000-0000-000000000001",
        },
        body: JSON.stringify({
          folder_id: folderIdParam || "00000000-0000-0000-0000-000000000002",
          document_id: documentIdParam || undefined,
          topic: topicParam || fileNameParam.replace(/\.[^/.]+$/, "").replace(/_/g, " "),
          learning_style: "visual",
        }),
      });

      if (res.ok) {
        await fetchDueCards();
        await fetchDeckOverview();
      }
    } catch (err) {
      console.warn("Auto-provisioning failed:", err);
    } finally {
      setIsAutoProvisioning(false);
    }
  };

  useEffect(() => {
    fetchDueCards();
  }, [fetchDueCards]);

  // Filter cards by selected file
  const displayedCards = useMemo(() => {
    if (selectedFileFilter === "all") return cards;
    const cleanTarget = selectedFileFilter.toLowerCase().trim();
    const filtered = cards.filter(c => {
      if (!c.file_name) return false;
      const cleanName = c.file_name.toLowerCase().trim();
      return cleanName === cleanTarget || cleanName.replace(/\.[^/.]+$/, "") === cleanTarget.replace(/\.[^/.]+$/, "");
    });
    return filtered.length > 0 ? filtered : cards;
  }, [cards, selectedFileFilter]);

  const totalDueCount = displayedCards.length;
  const remainingCount = Math.max(0, totalDueCount - reviewedCardIds.size);
  const isSessionFinished = totalDueCount > 0 && reviewedCardIds.size >= totalDueCount;
  const currentCard = !isSessionFinished ? displayedCards[cardIndex] : null;

  // Active file & folder display
  const activeFileName = currentCard?.file_name || fileNameParam || (selectedFileFilter !== "all" ? selectedFileFilter : "Active Document");
  const activeFolderPath = currentCard?.folder_path || currentCard?.folder || (folderIdParam ? "/current-folder" : "/all-courses");
  const activeTopic = currentCard?.topic || topicParam || "Active Recall Revision";

  // Current file review stats from deck overview
  const activeFileStats = useMemo(() => {
    if (!deckOverview) return null;
    return deckOverview.files.find(f => f.file_name === activeFileName) || null;
  }, [deckOverview, activeFileName]);

  // Collect unique files present across cards and database
  const availableFiles = useMemo(() => {
    const fileSet = new Set<string>();
    cards.forEach(c => {
      if (c.file_name) fileSet.add(c.file_name);
    });
    dbDocuments.forEach(d => {
      if (d.file_name) fileSet.add(d.file_name);
    });
    if (deckOverview) {
      deckOverview.files.forEach(f => fileSet.add(f.file_name));
    }
    if (fileNameParam) fileSet.add(fileNameParam);
    return Array.from(fileSet);
  }, [cards, dbDocuments, deckOverview, fileNameParam]);

  // Filtered decks for Anki Decks Overview
  const filteredDecks = useMemo(() => {
    if (!deckOverview) return [];
    if (deckFilter === "all") return deckOverview.files;
    if (deckFilter === "needs_review") return deckOverview.files.filter(f => f.needs_review_today);
    if (deckFilter === "up_to_date") return deckOverview.files.filter(f => f.status === "up_to_date");
    if (deckFilter === "mastered") return deckOverview.files.filter(f => f.status === "mastered");
    return deckOverview.files;
  }, [deckOverview, deckFilter]);

  const getStageLabel = (stageStr: string) => {
    switch (stageStr) {
      case "2357_day1":
        return { label: "2357 • Day 1 (+1d)", color: "bg-amber-100 text-amber-800 border-amber-200" };
      case "2357_day3":
        return { label: "2357 • Day 3 (+2d)", color: "bg-blue-100 text-blue-800 border-blue-200" };
      case "2357_day5":
        return { label: "2357 • Day 5 (+2d)", color: "bg-purple-100 text-purple-800 border-purple-200" };
      case "2357_day7":
        return { label: "2357 • Day 7 (+2d)", color: "bg-indigo-100 text-indigo-800 border-indigo-200" };
      case "graduated_fsrs":
        return { label: "FSRS Graduated (Long-term)", color: "bg-emerald-100 text-emerald-800 border-emerald-200" };
      default:
        return { label: "2357 • Day 1 (+1d)", color: "bg-purple-100 text-purple-800 border-purple-200" };
    }
  };

  const handleRecordFinished = async () => {
    setIsRecordingFinished(true);
    try {
      const activeFolderId = currentCard?.folder_id || folderIdParam || activeFileStats?.folder_id || "00000000-0000-0000-0000-000000000002";
      const activeDocId = currentCard?.document_id || documentIdParam || activeFileStats?.document_id || undefined;
      const targetFileName = activeFileName || fileNameParam;

      const res = await fetch("http://localhost:8000/api/v1/flashcards/deck-complete", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-Test-User-Id": user?.id || "00000000-0000-0000-0000-000000000001",
        },
        body: JSON.stringify({
          folder_id: activeFolderId,
          document_id: activeDocId,
          file_name: targetFileName,
          cards_reviewed: Math.max(reviewedCardIds.size + 1, displayedCards.length),
        }),
      });

      if (res.ok) {
        const data = await res.json();
        setFinishResult(data);
        // Mark all cards in current deck as reviewed to show completion screen
        const allIds = new Set(displayedCards.map(c => c.id));
        setReviewedCardIds(allIds);
        await fetchDeckOverview();
      }
    } catch (err) {
      console.warn("Failed to record deck completion:", err);
    } finally {
      setIsRecordingFinished(false);
    }
  };

  const handleNextCard = async (ratingVal: number) => {
    if (!currentCard) return;

    try {
      if (currentCard.id && !currentCard.id.startsWith("c")) {
        await fetch("http://localhost:8000/api/v1/flashcards/review", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-Test-User-Id": user?.id || "00000000-0000-0000-0000-000000000001",
          },
          body: JSON.stringify({
            card_id: currentCard.id,
            rating: ratingVal,
            workload_mode: "free",
          }),
        });
      }
    } catch (err) {
      console.warn("Failed to persist card review:", err);
    }

    const updatedReviewed = new Set(reviewedCardIds).add(currentCard.id);
    setReviewedCardIds(updatedReviewed);
    setIsFlipped(false);

    if (cardIndex + 1 < displayedCards.length) {
      setCardIndex(prev => prev + 1);
    } else {
      // Completed last card in deck review! Auto-record completion for today & schedule 2nd day
      await handleRecordFinished();
    }
    // Refresh deck overview telemetry
    fetchDeckOverview();
  };

  // Keyboard shortcuts (Space to flip, 1-4 for ratings)
  useEffect(() => {
    if (tab !== "flashcards" || flashcardViewMode !== "player") return;

    const handleKeyDown = (e: KeyboardEvent) => {
      const target = e.target as HTMLElement;
      if (target.tagName === "INPUT" || target.tagName === "TEXTAREA" || target.isContentEditable) {
        return;
      }

      if (e.code === "Space") {
        e.preventDefault();
        setIsFlipped(prev => !prev);
      } else if (isFlipped) {
        if (e.key === "1") {
          e.preventDefault();
          handleNextCard(1);
        } else if (e.key === "2") {
          e.preventDefault();
          handleNextCard(2);
        } else if (e.key === "3") {
          e.preventDefault();
          handleNextCard(3);
        } else if (e.key === "4") {
          e.preventDefault();
          handleNextCard(4);
        }
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [tab, flashcardViewMode, isFlipped, currentCard]);

  // Start study on a specific file deck
  const handleSelectDeckForStudy = async (f: FileReviewStats) => {
    setSelectedFileFilter(f.file_name);
    setCardIndex(0);
    setReviewedCardIds(new Set());
    setFinishResult(null);
    setIsFlipped(false);
    setFlashcardViewMode("player");

    // Synchronize URL with active deck
    router.push(`/review?folder_id=${f.folder_id}&document_id=${f.document_id || ""}&file_name=${encodeURIComponent(f.file_name)}&topic=${encodeURIComponent(f.topic || f.file_name)}`);

    // Ensure due cards are fetched and mapped specifically for this deck
    try {
      const res = await fetch(`http://localhost:8000/api/v1/flashcards/due?folder_id=${f.folder_id}&include_immediate=true`, {
        headers: { "X-Test-User-Id": user?.id || "00000000-0000-0000-0000-000000000001" },
      });
      if (res.ok) {
        const data = await res.json();
        if (Array.isArray(data) && data.length > 0) {
          const formatted = data.map((c: any) => ({
            ...c,
            file_name: c.file_name || f.file_name,
            topic: c.topic || f.topic || "Active Revision",
          }));
          setCards(prev => {
            const existingMap = new Map(prev.map(p => [p.id, p]));
            formatted.forEach(fc => existingMap.set(fc.id, fc));
            return Array.from(existingMap.values());
          });
        }
      }
    } catch (err) {
      console.warn("Could not fetch cards for selected deck:", err);
    }
  };

  const handleEvaluateFeynman = async () => {
    setIsEvaluating(true);
    try {
      const res = await fetch("http://localhost:8000/api/v1/feynman/evaluate", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-Test-User-Id": user?.id || "00000000-0000-0000-0000-000000000001",
        },
        body: JSON.stringify({
          topic: concept,
          explanation: explanation,
          target_retention: 0.9,
        }),
      });

      if (res.ok) {
        const data = await res.json();
        setFeynmanFeedback(data);
      } else {
        throw new Error("Evaluation endpoint error");
      }
    } catch (err) {
      console.warn("Feynman evaluation error, fallback local:", err);
      setTimeout(() => {
        setFeynmanFeedback({
          completeness_score: 0.88,
          precision_score: 0.91,
          feedback: `Great conceptual grasp of ${concept}! You explained the fundamental intuition clearly. To make this complete, emphasize the edge-case invariants and state recovery steps.`,
          missing_concepts: ["Exact state transition invariant", "Graceful recovery handling"],
          remedial_cards_created: 1,
        });
      }, 500);
    } finally {
      setIsEvaluating(false);
    }
  };

  const handleEvaluateBlurting = async () => {
    setIsEvaluatingBlurting(true);
    try {
      const res = await fetch("http://localhost:8000/api/v1/blurting/evaluate", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-Test-User-Id": user?.id || "00000000-0000-0000-0000-000000000001",
        },
        body: JSON.stringify({
          folder_id: folderIdParam || "00000000-0000-0000-0000-000000000002",
          topic: blurtingTopic,
          user_recall_text: blurtingText,
        }),
      });

      if (res.ok) {
        const data = await res.json();
        setBlurtingResult(data);
      } else {
        throw new Error("Blurting evaluation failed");
      }
    } catch (err) {
      console.warn("Blurting evaluation error, fallback local:", err);
      setTimeout(() => {
        setBlurtingResult({
          topic: blurtingTopic,
          accuracy_score: 85,
          retained_concepts: [
            `Core definitions and architecture of ${blurtingTopic}`,
            "Baseline invariants and modular operation",
            "Execution pipeline workflow",
          ],
          missed_nuances: [
            "Edge-case boundary state handling",
            "Secondary optimization parameters",
          ],
          recommended_focus: `Strong retrieval performance for ${blurtingTopic}! Review the edge conditions for your Day 3 revision.`,
        });
      }, 600);
    } finally {
      setIsEvaluatingBlurting(false);
    }
  };

  const stageInfo = getStageLabel(currentCard?.stage || "2357_day1");

  return (
    <div className="min-h-screen flex flex-col bg-[#f8f9fb]">
      <Navbar onOpenOnboardingModal={() => setShowOnboarding(true)} />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 py-8 space-y-8">
        {/* Header & Mode Tabs */}
        <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4">
          <div className="space-y-1.5">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-brand-tertiary-container border border-brand-tertiary/40 text-xs font-bold text-brand-on-tertiary-container">
              <BrainCircuit className="w-3.5 h-3.5 text-brand-secondary" />
              <span>Cognitive Mastery & Active Spaced Revision</span>
            </div>
            <h1 className="text-3xl sm:text-4xl font-black text-brand-secondary tracking-tight">
              Anki Decks & 2357 Spaced Revision
            </h1>
            <p className="text-brand-on-surface-variant text-xs sm:text-sm max-w-2xl font-medium">
              Track file completion percentages and rehearse cards on the scientifically grounded 2357 Method (Days 1, 3, 5, 7) before graduating into long-term FSRS memory retention.
            </p>
          </div>

          {/* 3-Tab Mode Switcher */}
          <div className="flex items-center gap-1.5 p-1.5 rounded-full bg-brand-surface-dim border border-brand-outline-variant shadow-xs self-start sm:self-auto">
            <button
              onClick={() => setTab("flashcards")}
              className={`px-4 py-2 rounded-full text-xs font-bold transition-all cursor-pointer ${
                tab === "flashcards" ? "bg-[#3a10e5] text-white shadow-xs" : "text-brand-on-surface-variant hover:text-brand-secondary"
              }`}
            >
              2357 Flashcards
            </button>
            <button
              onClick={() => setTab("blurting")}
              className={`px-4 py-2 rounded-full text-xs font-bold transition-all cursor-pointer ${
                tab === "blurting" ? "bg-[#3a10e5] text-white shadow-xs" : "text-brand-on-surface-variant hover:text-brand-secondary"
              }`}
            >
              Blurting Scratchpad
            </button>
            <button
              onClick={() => setTab("feynman")}
              className={`px-4 py-2 rounded-full text-xs font-bold transition-all cursor-pointer ${
                tab === "feynman" ? "bg-[#3a10e5] text-white shadow-xs" : "text-brand-on-surface-variant hover:text-brand-secondary"
              }`}
            >
              Feynman Explainer
            </button>
          </div>
        </div>

        {/* Tab 1: 2357 & FSRS Spaced Repetition Flashcards (Anki Mode) */}
        {tab === "flashcards" && (
          <div className="space-y-6">

            {/* Sub-View Switcher: Decks Overview vs Rehearsal Player */}
            <div className="flex items-center justify-between border-b border-brand-outline-variant pb-3">
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setFlashcardViewMode("decks")}
                  className={`inline-flex items-center gap-2 px-4 py-2 rounded-full text-xs font-black transition-all cursor-pointer ${
                    flashcardViewMode === "decks"
                      ? "bg-[#3a10e5] text-white shadow-xs"
                      : "bg-white text-brand-on-surface-variant hover:text-brand-secondary border border-brand-outline-variant"
                  }`}
                >
                  <Layers className="w-3.5 h-3.5" />
                  <span>Anki Decks Overview ({deckOverview?.total_files || availableFiles.length})</span>
                </button>
                <button
                  onClick={() => setFlashcardViewMode("player")}
                  className={`inline-flex items-center gap-2 px-4 py-2 rounded-full text-xs font-black transition-all cursor-pointer ${
                    flashcardViewMode === "player"
                      ? "bg-[#3a10e5] text-white shadow-xs"
                      : "bg-white text-brand-on-surface-variant hover:text-brand-secondary border border-brand-outline-variant"
                  }`}
                >
                  <Play className="w-3.5 h-3.5" />
                  <span>Active Card Rehearsal ({activeFileName})</span>
                </button>
              </div>

              {flashcardViewMode === "player" && (
                <button
                  onClick={() => setFlashcardViewMode("decks")}
                  className="inline-flex items-center gap-1.5 text-xs font-bold text-[#3a10e5] hover:underline cursor-pointer"
                >
                  <ArrowLeft className="w-3.5 h-3.5" />
                  <span>Back to Decks</span>
                </button>
              )}
            </div>

            {/* ========================================================================= */}
            {/* SUB-VIEW A: ANKI DECKS OVERVIEW & FILE COMPLETION DASHBOARD */}
            {/* ========================================================================= */}
            {flashcardViewMode === "decks" && (
              <div className="space-y-6">
                
                {/* 4 Summary Metric Cards */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  {/* Metric 1: Tracked Decks */}
                  <div className="p-5 rounded-[28px] bg-white border border-brand-outline-variant shadow-xs space-y-2">
                    <div className="flex items-center justify-between text-brand-on-surface-variant">
                      <span className="text-xs font-mono font-medium">Tracked Decks</span>
                      <FileText className="w-4 h-4 text-purple-600" />
                    </div>
                    <div className="text-2xl sm:text-3xl font-black text-brand-secondary">
                      {deckOverview?.total_files || availableFiles.length}
                    </div>
                    <p className="text-[11px] text-brand-on-surface-variant font-medium">
                      Course files with active 2357 schedules
                    </p>
                  </div>

                  {/* Metric 2: Decks Due Today */}
                  <div className="p-5 rounded-[28px] bg-white border border-brand-outline-variant shadow-xs space-y-2">
                    <div className="flex items-center justify-between text-brand-on-surface-variant">
                      <span className="text-xs font-mono font-medium">Decks Due Today</span>
                      <Clock className="w-4 h-4 text-rose-600" />
                    </div>
                    <div className="text-2xl sm:text-3xl font-black text-rose-600 flex items-center gap-2">
                      <span>{deckOverview?.files_needing_review ?? 0}</span>
                      {(deckOverview?.files_needing_review ?? 0) > 0 && (
                        <span className="text-xs font-mono px-2 py-0.5 rounded-full bg-rose-50 text-rose-700 border border-rose-200">
                          Action Due
                        </span>
                      )}
                    </div>
                    <p className="text-[11px] text-brand-on-surface-variant font-medium">
                      Files requiring review on 2357 schedule
                    </p>
                  </div>

                  {/* Metric 3: Total Due Cards */}
                  <div className="p-5 rounded-[28px] bg-white border border-brand-outline-variant shadow-xs space-y-2">
                    <div className="flex items-center justify-between text-brand-on-surface-variant">
                      <span className="text-xs font-mono font-medium">Cards Due Now</span>
                      <Zap className="w-4 h-4 text-amber-600" />
                    </div>
                    <div className="text-2xl sm:text-3xl font-black text-brand-secondary">
                      {deckOverview?.total_due_cards ?? cards.length}
                    </div>
                    <p className="text-[11px] text-brand-on-surface-variant font-medium">
                      Pending active recall rehearsals
                    </p>
                  </div>

                  {/* Metric 4: Overall Completion % */}
                  <div className="p-5 rounded-[28px] bg-white border border-brand-outline-variant shadow-xs space-y-2">
                    <div className="flex items-center justify-between text-brand-on-surface-variant">
                      <span className="text-xs font-mono font-medium">2357 Retention Progress</span>
                      <TrendingUp className="w-4 h-4 text-emerald-600" />
                    </div>
                    <div className="text-2xl sm:text-3xl font-black text-emerald-600">
                      {deckOverview?.overall_completion_percentage?.toFixed(1) ?? "0.0"}%
                    </div>
                    <p className="text-[11px] text-brand-on-surface-variant font-medium">
                      Average memory progression score
                    </p>
                  </div>
                </div>

                {/* Filter Pills */}
                <div className="flex items-center justify-between gap-2 overflow-x-auto pb-1 text-xs">
                  <div className="flex items-center gap-2">
                    <span className="text-brand-on-surface-variant font-bold text-xs">Filter Decks:</span>
                    <button
                      onClick={() => setDeckFilter("all")}
                      className={`px-3 py-1.5 rounded-full font-bold transition-all cursor-pointer ${
                        deckFilter === "all"
                          ? "bg-[#3a10e5] text-white shadow-xs"
                          : "bg-white text-brand-on-surface-variant border border-brand-outline-variant hover:bg-brand-surface-dim"
                      }`}
                    >
                      All Decks ({deckOverview?.total_files || 0})
                    </button>
                    <button
                      onClick={() => setDeckFilter("needs_review")}
                      className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full font-bold transition-all cursor-pointer ${
                        deckFilter === "needs_review"
                          ? "bg-rose-600 text-white shadow-xs"
                          : "bg-white text-rose-700 border border-rose-200 hover:bg-rose-50"
                      }`}
                    >
                      <Clock className="w-3 h-3" />
                      <span>Due Today ({deckOverview?.files_needing_review || 0})</span>
                    </button>
                    <button
                      onClick={() => setDeckFilter("up_to_date")}
                      className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full font-bold transition-all cursor-pointer ${
                        deckFilter === "up_to_date"
                          ? "bg-blue-600 text-white shadow-xs"
                          : "bg-white text-blue-700 border border-blue-200 hover:bg-blue-50"
                      }`}
                    >
                      <CheckCircle className="w-3 h-3" />
                      <span>Up to Date</span>
                    </button>
                    <button
                      onClick={() => setDeckFilter("mastered")}
                      className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full font-bold transition-all cursor-pointer ${
                        deckFilter === "mastered"
                          ? "bg-emerald-600 text-white shadow-xs"
                          : "bg-white text-emerald-700 border border-emerald-200 hover:bg-emerald-50"
                      }`}
                    >
                      <Award className="w-3 h-3" />
                      <span>Mastered (100%)</span>
                    </button>
                  </div>

                  <button
                    onClick={fetchDeckOverview}
                    className="inline-flex items-center gap-1 px-3 py-1.5 rounded-full text-xs font-bold text-brand-secondary bg-white border border-brand-outline-variant hover:bg-brand-surface-dim cursor-pointer shadow-2xs"
                  >
                    <RefreshCw className={`w-3 h-3 ${isLoadingOverview ? "animate-spin" : ""}`} />
                    <span>Refresh Stats</span>
                  </button>
                </div>

                {/* Deck List Table / Grid */}
                {isLoadingOverview && !deckOverview ? (
                  <div className="p-12 text-center rounded-[32px] bg-white border border-brand-outline-variant shadow-xs space-y-3">
                    <Loader2 className="w-8 h-8 text-[#3a10e5] animate-spin mx-auto" />
                    <h3 className="text-base font-bold text-brand-secondary">
                      Loading Anki Decks & 2357 Progress...
                    </h3>
                  </div>
                ) : filteredDecks.length === 0 ? (
                  <div className="p-12 text-center rounded-[32px] bg-white border border-brand-outline-variant shadow-xs space-y-3">
                    <CheckCircle2 className="w-10 h-10 text-emerald-600 mx-auto" />
                    <h3 className="text-lg font-black text-brand-secondary">
                      No Decks Match Filter
                    </h3>
                    <p className="text-xs text-brand-on-surface-variant max-w-sm mx-auto font-medium">
                      All decks are currently up to date or completed.
                    </p>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {filteredDecks.map((deck) => {
                      const isDue = deck.needs_review_today;
                      return (
                        <div
                          key={deck.file_name}
                          className={`p-6 rounded-[28px] bg-white border transition-all hover:shadow-md ${
                            isDue
                              ? "border-rose-300 ring-1 ring-rose-200/60"
                              : "border-brand-outline-variant"
                          }`}
                        >
                          <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
                            
                            {/* Left: Deck Identity & Metadata */}
                            <div className="space-y-2 max-w-lg">
                              <div className="flex flex-wrap items-center gap-2">
                                <span className="text-[11px] font-mono px-2 py-0.5 rounded-full bg-purple-50 text-purple-700 border border-purple-200 font-bold">
                                  {deck.course_code || "General"}
                                </span>
                                <span className="text-[11px] font-mono text-brand-on-surface-variant flex items-center gap-1">
                                  <FolderTree className="w-3 h-3 text-brand-primary" />
                                  {deck.folder_path}
                                </span>
                              </div>

                              <div>
                                <h3 className="text-lg font-black text-brand-secondary tracking-tight">
                                  {deck.file_name}
                                </h3>
                                <p className="text-xs text-brand-on-surface-variant font-medium">
                                  Topic: {deck.topic || "Active Revision"}
                                </p>
                              </div>

                              {/* 2357 Schedule Urgency Signifier */}
                              <div className="pt-1">
                                {deck.finished_today ? (
                                  <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-50 text-emerald-800 border border-emerald-300 text-xs font-bold font-mono">
                                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                                    <span>Finished for Today • Second Review ({deck.next_stage_label || "Day 3"}) due on {deck.next_review_due ? new Date(deck.next_review_due).toLocaleDateString() : "next 2357 milestone"}</span>
                                  </div>
                                ) : isDue ? (
                                  <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-rose-50 text-rose-700 border border-rose-200 text-xs font-bold font-mono">
                                    <span className="w-2 h-2 rounded-full bg-rose-500 animate-pulse" />
                                    <span>2357 Method: {deck.due_cards_count} {deck.due_cards_count === 1 ? "card" : "cards"} due for review today</span>
                                  </div>
                                ) : deck.status === "mastered" ? (
                                  <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200 text-xs font-bold font-mono">
                                    <Award className="w-3.5 h-3.5 text-emerald-600" />
                                    <span>100% Mastered • Graduated into FSRS Retention</span>
                                  </div>
                                ) : deck.total_cards === 0 ? (
                                  <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-brand-surface-dim text-brand-on-surface-variant border border-brand-outline-variant text-xs font-medium font-mono">
                                    <Sparkles className="w-3.5 h-3.5 text-brand-primary" />
                                    <span>Cards ready to be generated</span>
                                  </div>
                                ) : (
                                  <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-blue-50 text-blue-700 border border-blue-200 text-xs font-bold font-mono">
                                    <CalendarCheck className="w-3.5 h-3.5 text-blue-600" />
                                    <span>Up to Date • Next review: {deck.next_review_due ? new Date(deck.next_review_due).toLocaleDateString() : "Upcoming 2357 milestone"}</span>
                                  </div>
                                )}
                              </div>
                            </div>

                            {/* Middle: Progress Bar & 2357 Stage Breakdown */}
                            <div className="space-y-2 lg:w-80">
                              <div className="flex items-center justify-between text-xs font-mono">
                                <span className="font-bold text-brand-secondary">
                                  Completion: {deck.completion_percentage}%
                                </span>
                                <span className="text-brand-on-surface-variant text-[11px]">
                                  Mastery: {deck.mastery_percentage}% Graduated
                                </span>
                              </div>

                              {/* Progress bar */}
                              <div className="w-full h-2.5 rounded-full bg-brand-surface-dim border border-brand-outline-variant/60 overflow-hidden">
                                <div
                                  className={`h-full rounded-full transition-all duration-500 ${
                                    deck.completion_percentage >= 100
                                      ? "bg-emerald-500"
                                      : isDue
                                      ? "bg-rose-500"
                                      : "bg-[#3a10e5]"
                                  }`}
                                  style={{ width: `${Math.min(100, Math.max(0, deck.completion_percentage))}%` }}
                                />
                              </div>

                              {/* 2357 Stage Milestone Distribution */}
                              <div className="flex items-center justify-between text-[10px] font-mono text-brand-on-surface-variant pt-1">
                                <span title="Day 1 initial recall (+1d)">D1: {deck.stage_breakdown.day_1 || 0}</span>
                                <span>•</span>
                                <span title="Day 3 second recall (+2d)">D3: {deck.stage_breakdown.day_3 || 0}</span>
                                <span>•</span>
                                <span title="Day 5 third recall (+2d)">D5: {deck.stage_breakdown.day_5 || 0}</span>
                                <span>•</span>
                                <span title="Day 7 consolidation (+2d)">D7: {deck.stage_breakdown.day_7 || 0}</span>
                                <span>•</span>
                                <span className="font-bold text-emerald-600" title="Graduated into FSRS long-term tracking">🎓 {deck.stage_breakdown.graduated || 0}</span>
                              </div>
                            </div>

                            {/* Right: Anki Color Counters & Action Button */}
                            <div className="flex flex-col sm:flex-row lg:flex-col items-start sm:items-center lg:items-end justify-between gap-3 shrink-0">
                              {/* Anki Iconic Badges: New, Learning, Due, Graduated */}
                              <div className="flex items-center gap-1.5 font-mono text-xs">
                                <span 
                                  title="New cards waiting at Day 1"
                                  className="px-2.5 py-1 rounded-full bg-blue-50 text-blue-700 border border-blue-200 font-bold"
                                >
                                  {deck.new_cards_count} New
                                </span>
                                <span 
                                  title="Cards learning in 2357 schedule"
                                  className="px-2.5 py-1 rounded-full bg-amber-50 text-amber-700 border border-amber-200 font-bold"
                                >
                                  {deck.learning_cards_count} Learning
                                </span>
                                <span 
                                  title="Cards currently due today"
                                  className={`px-2.5 py-1 rounded-full font-bold ${
                                    deck.due_cards_count > 0 
                                      ? "bg-rose-50 text-rose-700 border border-rose-200" 
                                      : "bg-gray-50 text-gray-400 border border-gray-200"
                                  }`}
                                >
                                  {deck.due_cards_count} Due
                                </span>
                              </div>

                              {/* Study Button */}
                              {deck.total_cards > 0 ? (
                                <button
                                  onClick={() => handleSelectDeckForStudy(deck)}
                                  className={`px-5 py-2 rounded-full text-xs font-black transition-all cursor-pointer flex items-center gap-2 shadow-xs ${
                                    deck.finished_today
                                      ? "bg-emerald-600 hover:bg-emerald-700 text-white"
                                      : isDue
                                      ? "bg-rose-600 hover:bg-rose-700 text-white"
                                      : "bg-[#3a10e5] hover:bg-[#2e0cb8] text-white"
                                  }`}
                                >
                                  {deck.finished_today ? (
                                    <>
                                      <CheckCircle className="w-3.5 h-3.5" />
                                      <span>Finished Today (Practice Again)</span>
                                    </>
                                  ) : (
                                    <>
                                      <Play className="w-3.5 h-3.5" />
                                      <span>
                                        {isDue ? `Review Due Deck (${deck.due_cards_count})` : "Study Deck"}
                                      </span>
                                    </>
                                  )}
                                </button>
                              ) : (
                                <button
                                  onClick={() => {
                                    setSelectedFileFilter(deck.file_name);
                                    setFlashcardViewMode("player");
                                    autoProvisionFileCards();
                                  }}
                                  className="px-5 py-2 rounded-full text-xs font-bold bg-brand-surface-dim hover:bg-white text-brand-secondary border border-brand-outline-variant transition-all cursor-pointer flex items-center gap-1.5"
                                >
                                  <Sparkles className="w-3.5 h-3.5 text-brand-primary" />
                                  <span>Generate 2357 Deck</span>
                                </button>
                              )}
                            </div>

                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            )}

            {/* ========================================================================= */}
            {/* SUB-VIEW B: ACTIVE FLASHCARD REHEARSAL PLAYER (ANKI RECALL MODE) */}
            {/* ========================================================================= */}
            {flashcardViewMode === "player" && (
              <div className="max-w-2xl mx-auto space-y-6">

                {/* File Switcher Filter Bar */}
                {availableFiles.length > 0 && (
                  <div className="flex items-center gap-2 overflow-x-auto pb-1 text-xs">
                    <div className="flex items-center gap-1.5 text-brand-on-surface-variant font-bold shrink-0 pr-1">
                      <Filter className="w-3.5 h-3.5" />
                      <span>Deck:</span>
                    </div>
                    <button
                      onClick={() => {
                        setSelectedFileFilter("all");
                        setCardIndex(0);
                        setReviewedCardIds(new Set());
                      }}
                      className={`px-3.5 py-1.5 rounded-full font-bold transition-all whitespace-nowrap cursor-pointer ${
                        selectedFileFilter === "all"
                          ? "bg-[#3a10e5] text-white shadow-xs"
                          : "bg-brand-surface-dim hover:bg-white text-brand-on-surface-variant hover:text-brand-secondary border border-brand-outline-variant"
                      }`}
                    >
                      All Files ({cards.length})
                    </button>
                    {availableFiles.map((fname) => {
                      const docCardsCount = cards.filter(c => c.file_name === fname).length;
                      const isSelected = selectedFileFilter === fname;
                      return (
                        <button
                          key={fname}
                          onClick={() => {
                            setSelectedFileFilter(fname);
                            setCardIndex(0);
                            setReviewedCardIds(new Set());
                          }}
                          className={`inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-full font-bold transition-all whitespace-nowrap cursor-pointer ${
                            isSelected
                              ? "bg-[#3a10e5] text-white shadow-xs"
                              : "bg-brand-surface-dim hover:bg-white text-brand-on-surface-variant hover:text-brand-secondary border border-brand-outline-variant"
                          }`}
                        >
                          <FileText className="w-3 h-3 shrink-0" />
                          <span className="truncate max-w-[180px]">{fname}</span>
                          {docCardsCount > 0 && (
                            <span className={`text-[10px] px-1.5 py-0.2 rounded-full font-mono ${
                              isSelected ? "bg-white/20 text-white" : "bg-brand-outline-variant/60 text-brand-secondary"
                            }`}>
                              {docCardsCount}
                            </span>
                          )}
                        </button>
                      );
                    })}
                  </div>
                )}

                {/* Active Document Header Card with Anki Telemetry */}
                <div className="p-5 sm:p-6 rounded-[28px] bg-white border border-brand-outline-variant shadow-xs space-y-4">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-2xl bg-[#3a10e5]/10 text-[#3a10e5] flex items-center justify-center shrink-0 shadow-2xs">
                        <FileText className="w-5 h-5" />
                      </div>
                      <div className="space-y-0.5">
                        <div className="flex flex-wrap items-center gap-2">
                          <span className="text-xs font-mono text-brand-on-surface-variant font-medium flex items-center gap-1">
                            <FolderTree className="w-3.5 h-3.5 text-brand-primary" />
                            {activeFolderPath}
                          </span>
                          <span className="text-brand-outline-variant">•</span>
                          <span className="text-xs font-bold text-brand-secondary flex items-center gap-1">
                            <FileText className="w-3.5 h-3.5 text-purple-600" />
                            {activeFileName}
                          </span>
                        </div>
                        <div className="text-sm sm:text-base font-black text-brand-secondary tracking-tight">
                          Topic: {activeTopic}
                        </div>
                      </div>
                    </div>

                    {/* Anki Card Counters: Remaining / Due */}
                    <div className="flex items-center gap-2 self-start sm:self-auto font-mono text-xs">
                      {activeFileStats && (
                        <span className="px-3 py-1 rounded-full bg-blue-50 text-blue-700 border border-blue-200 font-bold">
                          {activeFileStats.new_cards_count} New
                        </span>
                      )}
                      <div className="px-3.5 py-1.5 rounded-full bg-brand-surface-dim border border-brand-outline-variant font-bold text-brand-secondary shadow-2xs">
                        {remainingCount} cards left
                      </div>
                      <button
                        onClick={handleRecordFinished}
                        disabled={isRecordingFinished}
                        className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-full bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs shadow-xs transition-all cursor-pointer disabled:opacity-50"
                        title="Record deck as finished for today in database and schedule Day 3 (+2d)"
                      >
                        {isRecordingFinished ? (
                          <Loader2 className="w-3.5 h-3.5 animate-spin" />
                        ) : (
                          <CheckCircle className="w-3.5 h-3.5" />
                        )}
                        <span>I am Finished</span>
                      </button>
                    </div>
                  </div>

                  {/* File Completion Progress Bar */}
                  {activeFileStats && (
                    <div className="pt-2 border-t border-brand-outline-variant/60 space-y-1.5">
                      <div className="flex items-center justify-between text-xs font-mono text-brand-on-surface-variant">
                        <span>Deck 2357 Completion</span>
                        <span className="font-bold text-brand-secondary">
                          {activeFileStats.completion_percentage}% ({activeFileStats.graduated_cards_count} graduated)
                        </span>
                      </div>
                      <div className="w-full h-2 rounded-full bg-brand-surface-dim border border-brand-outline-variant/60 overflow-hidden">
                        <div 
                          className="h-full bg-emerald-500 rounded-full transition-all duration-300"
                          style={{ width: `${activeFileStats.completion_percentage}%` }}
                        />
                      </div>
                    </div>
                  )}

                  {/* 2357 Milestone Road Stepper */}
                  <div className="pt-2 border-t border-brand-outline-variant/60">
                    <div className="text-[11px] font-mono text-brand-on-surface-variant mb-1.5">
                      2357 Spaced Schedule Progression:
                    </div>
                    <div className="grid grid-cols-5 gap-1.5 text-center text-[10px] font-mono font-bold">
                      <div className={`p-1.5 rounded-xl border ${currentCard?.stage === "2357_day1" ? "bg-amber-100 border-amber-300 text-amber-900 ring-1 ring-amber-300" : "bg-brand-surface-dim border-brand-outline-variant text-brand-on-surface-variant"}`}>
                        Day 1 (+1d)
                      </div>
                      <div className={`p-1.5 rounded-xl border ${currentCard?.stage === "2357_day3" ? "bg-blue-100 border-blue-300 text-blue-900 ring-1 ring-blue-300" : "bg-brand-surface-dim border-brand-outline-variant text-brand-on-surface-variant"}`}>
                        Day 3 (+2d)
                      </div>
                      <div className={`p-1.5 rounded-xl border ${currentCard?.stage === "2357_day5" ? "bg-purple-100 border-purple-300 text-purple-900 ring-1 ring-purple-300" : "bg-brand-surface-dim border-brand-outline-variant text-brand-on-surface-variant"}`}>
                        Day 5 (+2d)
                      </div>
                      <div className={`p-1.5 rounded-xl border ${currentCard?.stage === "2357_day7" ? "bg-indigo-100 border-indigo-300 text-indigo-900 ring-1 ring-indigo-300" : "bg-brand-surface-dim border-brand-outline-variant text-brand-on-surface-variant"}`}>
                        Day 7 (+2d)
                      </div>
                      <div className={`p-1.5 rounded-xl border ${currentCard?.stage === "graduated_fsrs" ? "bg-emerald-100 border-emerald-300 text-emerald-900 ring-1 ring-emerald-300" : "bg-brand-surface-dim border-brand-outline-variant text-brand-on-surface-variant"}`}>
                        Graduated 🎓
                      </div>
                    </div>
                  </div>
                </div>

                {/* Session Progress Bar */}
                {totalDueCount > 0 && !isSessionFinished && (
                  <div className="space-y-1.5 px-1">
                    <div className="flex items-center justify-between text-xs font-mono text-brand-on-surface-variant">
                      <span>Card {reviewedCardIds.size + 1} of {totalDueCount}</span>
                      <span className="font-bold text-brand-secondary">
                        {Math.round((reviewedCardIds.size / totalDueCount) * 100)}% reviewed this session
                      </span>
                    </div>
                    <div className="w-full h-2 rounded-full bg-brand-surface-dim border border-brand-outline-variant/60 overflow-hidden">
                      <div 
                        className="h-full bg-[#3a10e5] rounded-full transition-all duration-300"
                        style={{ width: `${(reviewedCardIds.size / totalDueCount) * 100}%` }}
                      />
                    </div>
                  </div>
                )}

                {/* Loading / Provisioning State */}
                {isLoadingCards || isAutoProvisioning ? (
                  <div className="p-12 text-center rounded-[32px] bg-white border border-brand-outline-variant shadow-xs space-y-3">
                    <Loader2 className="w-8 h-8 text-[#3a10e5] animate-spin mx-auto" />
                    <h3 className="text-base font-bold text-brand-secondary">
                      {isAutoProvisioning ? `Generating 2357 Flashcards for ${activeFileName}...` : "Loading Active Recall Cards..."}
                    </h3>
                    <p className="text-xs text-brand-on-surface-variant font-medium">
                      Resolving 2357 spaced repetition schedule from database...
                    </p>
                  </div>
                ) : isSessionFinished ? (
                  /* Session Finished State */
                  <div className="p-8 sm:p-10 rounded-[32px] bg-white border border-emerald-200/80 shadow-md text-center space-y-6 animate-fadeIn">
                    <div className="w-16 h-16 rounded-full bg-emerald-100 text-emerald-700 flex items-center justify-center mx-auto shadow-sm">
                      <CheckCircle2 className="w-8 h-8" />
                    </div>
                    <div className="space-y-2">
                      <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-50 text-emerald-800 border border-emerald-300 text-xs font-bold font-mono">
                        <Check className="w-3.5 h-3.5 text-emerald-600" />
                        <span>Recorded in Database • Finished for Today</span>
                      </div>
                      <h2 className="text-2xl sm:text-3xl font-black text-brand-secondary tracking-tight">
                        Deck Rehearsal Finished for Today!
                      </h2>
                      <p className="text-xs sm:text-sm text-brand-on-surface-variant max-w-md mx-auto leading-relaxed font-medium">
                        {finishResult?.message || `You have completed all cards for ${activeFileName} today. The second review milestone (${activeFileStats?.next_stage_label || "Day 3"}) is scheduled for +2 days.`}
                      </p>
                    </div>

                    {/* Anki 2357 Schedule Timeline Tracker */}
                    <div className="p-4 rounded-2xl bg-brand-surface-dim border border-brand-outline-variant/80 max-w-lg mx-auto text-left space-y-3">
                      <div className="flex items-center justify-between text-xs font-mono text-brand-on-surface-variant font-bold">
                        <span className="flex items-center gap-1.5 text-emerald-700">
                          <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                          Day 1 Review: Finished Today
                        </span>
                        <span className="text-blue-700 font-black">
                          Second Review: Day 3 (+2d)
                        </span>
                      </div>
                      <div className="text-xs text-brand-secondary font-medium">
                        🗓️ <span className="font-bold">Next Review Date: </span>
                        {finishResult?.next_review_due 
                          ? new Date(finishResult.next_review_due).toLocaleDateString(undefined, { weekday: 'long', month: 'short', day: 'numeric', year: 'numeric' })
                          : "Scheduled in 2 days (Day 3)"}
                      </div>
                    </div>

                    <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 max-w-md mx-auto text-left font-mono text-xs">
                      <div className="p-3.5 rounded-2xl bg-brand-surface-dim border border-brand-outline-variant">
                        <div className="text-brand-on-surface-variant text-[11px]">Reviewed Today</div>
                        <div className="text-lg font-black text-brand-secondary mt-0.5">
                          {finishResult?.cards_completed || totalDueCount} Cards
                        </div>
                      </div>
                      <div className="p-3.5 rounded-2xl bg-brand-surface-dim border border-brand-outline-variant">
                        <div className="text-brand-on-surface-variant text-[11px]">Next Milestone</div>
                        <div className="text-lg font-black text-blue-600 mt-0.5">
                          {finishResult?.next_stage === "2357_day3" ? "Day 3 (+2d)" : (finishResult?.next_stage || "Day 3")}
                        </div>
                      </div>
                      <div className="p-3.5 rounded-2xl bg-brand-surface-dim border border-brand-outline-variant col-span-2 sm:col-span-1">
                        <div className="text-brand-on-surface-variant text-[11px]">Deck Status</div>
                        <div className="text-lg font-black text-emerald-600 mt-0.5">
                          Up to Date
                        </div>
                      </div>
                    </div>

                    <div className="flex flex-col sm:flex-row items-center justify-center gap-3 pt-2">
                      <button
                        onClick={() => {
                          setFinishResult(null);
                          setReviewedCardIds(new Set());
                          setCardIndex(0);
                        }}
                        className="w-full sm:w-auto px-5 py-2.5 rounded-full bg-brand-surface-dim hover:bg-gray-100 border border-brand-outline-variant text-brand-secondary text-xs font-bold transition-all cursor-pointer flex items-center justify-center gap-2 shadow-2xs"
                      >
                        <RefreshCw className="w-3.5 h-3.5" />
                        <span>Practice Deck Again</span>
                      </button>
                      <button
                        onClick={() => {
                          setFinishResult(null);
                          setFlashcardViewMode("decks");
                        }}
                        className="w-full sm:w-auto px-5 py-2.5 rounded-full bg-[#3a10e5] hover:bg-[#2e0cb8] text-white text-xs font-bold transition-all shadow-sm cursor-pointer flex items-center justify-center gap-2"
                      >
                        <Layers className="w-3.5 h-3.5" />
                        <span>Return to Decks Overview</span>
                      </button>
                    </div>
                  </div>
                ) : currentCard ? (
                  <>
                    {/* Leech Quarantine Banner */}
                    {currentCard?.is_leech && (
                      <div className="p-4 rounded-[24px] bg-amber-50 border border-amber-200 text-amber-900 text-xs flex items-center gap-3 shadow-2xs">
                        <ShieldAlert className="w-5 h-5 text-amber-600 shrink-0" />
                        <div>
                          <div className="font-bold">Leech Quarantine Alert (4+ Lapses)</div>
                          <p className="text-[11px] opacity-90 font-medium">
                            This concept has been missed 4+ times. It is flagged for atomic LLM simplification to prevent memory interference.
                          </p>
                        </div>
                      </div>
                    )}

                    {/* Flashcard Component */}
                    <div
                      onClick={() => setIsFlipped(!isFlipped)}
                      className="w-full min-h-[320px] p-8 rounded-[32px] bg-white border border-brand-outline-variant shadow-md hover:shadow-lg transition-all cursor-pointer flex flex-col justify-between select-none relative group"
                    >
                      <div className="flex items-center justify-between text-xs text-brand-on-surface-variant">
                        <div className="flex items-center gap-2">
                          <span className={`px-2.5 py-1 rounded-full border text-[11px] font-bold ${stageInfo.color}`}>
                            {stageInfo.label}
                          </span>
                          <span className="font-mono text-xs text-brand-on-surface-variant">
                            Card {reviewedCardIds.size + 1} of {totalDueCount}
                          </span>
                        </div>
                        <span className="px-2.5 py-1 rounded-full bg-brand-surface-dim border border-brand-outline-variant font-mono text-[11px] font-semibold">
                          {isFlipped ? "Answer (Back)" : "Prompt (Front - Space to Flip)"}
                        </span>
                      </div>

                      <div className="my-auto text-center py-8">
                        <p className="text-xl sm:text-2xl font-bold text-brand-secondary leading-relaxed">
                          {isFlipped ? currentCard?.back : currentCard?.front}
                        </p>
                      </div>

                      <div className="flex items-center justify-between text-xs text-brand-on-surface-variant font-mono pt-4 border-t border-brand-outline-variant/60">
                        <span className="flex items-center gap-1">
                          <Clock className="w-3.5 h-3.5 text-brand-primary" />
                          <span>Stability: {currentCard?.stability ? `${currentCard.stability.toFixed(1)}d` : "1.0d"}</span>
                        </span>
                        <span>Lapses: {currentCard?.lapses || 0}</span>
                      </div>
                    </div>

                    {/* 4-Grade Anki Rating Buttons with Keyboard Shortcuts */}
                    {isFlipped ? (
                      <div className="space-y-2">
                        <div className="grid grid-cols-4 gap-3 animate-fadeIn">
                          <button
                            onClick={() => handleNextCard(1)}
                            className="p-3.5 rounded-[20px] bg-rose-50 hover:bg-rose-100 border border-rose-200 text-rose-700 text-xs font-bold transition-all text-center cursor-pointer shadow-2xs"
                          >
                            <div className="text-sm font-black flex items-center justify-center gap-1">
                              <span>Again</span>
                              <span className="text-[10px] px-1.5 py-0.2 rounded bg-rose-200 text-rose-800">[1]</span>
                            </div>
                            <span className="text-[10px] opacity-80 font-mono mt-0.5 block">&lt; 6h (Reset)</span>
                          </button>
                          <button
                            onClick={() => handleNextCard(2)}
                            className="p-3.5 rounded-[20px] bg-amber-50 hover:bg-amber-100 border border-amber-200 text-amber-700 text-xs font-bold transition-all text-center cursor-pointer shadow-2xs"
                          >
                            <div className="text-sm font-black flex items-center justify-center gap-1">
                              <span>Hard</span>
                              <span className="text-[10px] px-1.5 py-0.2 rounded bg-amber-200 text-amber-800">[2]</span>
                            </div>
                            <span className="text-[10px] opacity-80 font-mono mt-0.5 block">1.0d (Stay)</span>
                          </button>
                          <button
                            onClick={() => handleNextCard(3)}
                            className="p-3.5 rounded-[20px] bg-blue-50 hover:bg-blue-100 border border-blue-200 text-blue-700 text-xs font-bold transition-all text-center shadow-xs cursor-pointer"
                          >
                            <div className="text-sm font-black flex items-center justify-center gap-1">
                              <span>Good</span>
                              <span className="text-[10px] px-1.5 py-0.2 rounded bg-blue-200 text-blue-800">[3]</span>
                            </div>
                            <span className="text-[10px] opacity-80 font-mono mt-0.5 block">+2.0d (Next 2357)</span>
                          </button>
                          <button
                            onClick={() => handleNextCard(4)}
                            className="p-3.5 rounded-[20px] bg-emerald-50 hover:bg-emerald-100 border border-emerald-200 text-emerald-700 text-xs font-bold transition-all text-center cursor-pointer shadow-2xs"
                          >
                            <div className="text-sm font-black flex items-center justify-center gap-1">
                              <span>Easy</span>
                              <span className="text-[10px] px-1.5 py-0.2 rounded bg-emerald-200 text-emerald-800">[4]</span>
                            </div>
                            <span className="text-[10px] opacity-80 font-mono mt-0.5 block">+3.0d (Fast)</span>
                          </button>
                        </div>
                        <p className="text-[11px] font-mono text-center text-brand-on-surface-variant">
                          Keyboard hotkeys: press <kbd className="px-1.5 py-0.5 bg-gray-100 rounded border text-gray-700">1</kbd>, <kbd className="px-1.5 py-0.5 bg-gray-100 rounded border text-gray-700">2</kbd>, <kbd className="px-1.5 py-0.5 bg-gray-100 rounded border text-gray-700">3</kbd>, or <kbd className="px-1.5 py-0.5 bg-gray-100 rounded border text-gray-700">4</kbd>
                        </p>
                      </div>
                    ) : (
                      <div className="text-center space-y-2">
                        <button
                          onClick={() => setIsFlipped(true)}
                          className="inline-flex items-center gap-2 px-6 py-2.5 rounded-full bg-[#3a10e5] hover:bg-[#2e0cb8] text-white text-xs font-bold transition-all shadow-sm cursor-pointer"
                        >
                          <RotateCw className="w-3.5 h-3.5" />
                          <span>Show Answer (or Press Space)</span>
                        </button>
                      </div>
                    )}
                  </>
                ) : (
                  /* Zero Due Cards Empty State */
                  <div className="p-10 rounded-[32px] bg-white border border-brand-outline-variant shadow-xs text-center space-y-4">
                    <div className="w-12 h-12 rounded-full bg-purple-50 text-[#3a10e5] flex items-center justify-center mx-auto">
                      <CheckCircle2 className="w-6 h-6 text-[#3a10e5]" />
                    </div>
                    <div className="space-y-1">
                      <h3 className="text-xl font-black text-brand-secondary">
                        No Due Reviews for {activeFileName}
                      </h3>
                      <p className="text-xs text-brand-on-surface-variant max-w-md mx-auto font-medium">
                        All cards for this deck are currently scheduled for future 2357 intervals.
                      </p>
                    </div>
                    <div className="flex items-center justify-center gap-3 pt-2">
                      <button
                        onClick={autoProvisionFileCards}
                        disabled={isAutoProvisioning}
                        className="inline-flex items-center gap-2 px-5 py-2.5 rounded-full bg-[#3a10e5] text-white text-xs font-bold shadow-xs hover:opacity-90 transition-all cursor-pointer disabled:opacity-50"
                      >
                        <Sparkles className="w-3.5 h-3.5" />
                        <span>Generate & Practice Cards Now</span>
                      </button>
                      <button
                        onClick={() => setFlashcardViewMode("decks")}
                        className="inline-flex items-center gap-2 px-5 py-2.5 rounded-full bg-brand-surface-dim border border-brand-outline-variant text-brand-secondary text-xs font-bold shadow-2xs hover:bg-white transition-all cursor-pointer"
                      >
                        <Layers className="w-3.5 h-3.5 text-brand-primary" />
                        <span>Return to Decks Overview</span>
                      </button>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {/* Tab 2: Blurting Scratchpad (Active Recall Technique) */}
        {tab === "blurting" && (
          <div className="max-w-3xl mx-auto space-y-6">
            <div className="p-8 rounded-[32px] bg-white border border-brand-outline-variant shadow-sm space-y-5">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div className="space-y-1">
                  <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-50 text-indigo-700 border border-indigo-200 text-xs font-bold">
                    <Zap className="w-3.5 h-3.5" />
                    <span>The Blurting Method (Unprompted Active Recall)</span>
                  </div>
                  <h3 className="text-2xl font-black text-brand-secondary">Memory Retrieval Scratchpad</h3>
                </div>
                <span className="text-xs font-mono text-brand-on-surface-variant px-3 py-1 rounded-full bg-brand-surface-dim border border-brand-outline-variant">
                  Topic: {blurtingTopic}
                </span>
              </div>

              <p className="text-xs text-brand-on-surface-variant leading-relaxed font-medium">
                Close your notes and write everything you can remember about <strong>{blurtingTopic}</strong>. Our semantic evaluation engine compares your recall against the source document to pinpoint conceptual coverage and missed nuances.
              </p>

              <textarea
                value={blurtingText}
                onChange={(e) => setBlurtingText(e.target.value)}
                rows={7}
                placeholder={`Type your unprompted memory recall for ${blurtingTopic} here... e.g., Core invariants, foundational formulas, state transitions, execution rules...`}
                className="w-full p-4 rounded-[20px] bg-brand-surface-dim border border-brand-outline-variant text-xs text-brand-secondary focus:outline-none focus:border-[#3a10e5] leading-relaxed transition-all font-medium"
              />

              <div className="flex justify-between items-center pt-2">
                <span className="text-xs text-brand-on-surface-variant font-mono">
                  {blurtingText.split(/\s+/).filter(Boolean).length} words
                </span>
                <button
                  onClick={handleEvaluateBlurting}
                  disabled={isEvaluatingBlurting || blurtingText.trim().length < 10}
                  className="px-6 py-3 rounded-[24px] bg-[#3a10e5] hover:opacity-90 text-white text-xs font-bold transition-all shadow-sm flex items-center gap-2 cursor-pointer disabled:opacity-50"
                >
                  <RefreshCw className={`w-3.5 h-3.5 ${isEvaluatingBlurting ? "animate-spin" : ""}`} />
                  <span>{isEvaluatingBlurting ? "Evaluating Recall Precision..." : "Evaluate Memory Recall"}</span>
                </button>
              </div>
            </div>

            {/* Blurting AI Evaluation Feedback */}
            {blurtingResult && (
              <div className="p-8 rounded-[32px] bg-white border border-brand-outline-variant shadow-md space-y-6 animate-fadeIn">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2.5">
                    <Award className="w-6 h-6 text-[#3a10e5]" />
                    <div>
                      <h4 className="font-black text-base text-brand-secondary">Blurting Analysis & Gap Report</h4>
                      <p className="text-xs text-brand-on-surface-variant">Evaluated against source document knowledge components</p>
                    </div>
                  </div>
                  <span className="text-sm font-black px-4 py-1.5 rounded-full bg-purple-50 text-purple-700 border border-purple-200">
                    Accuracy: {blurtingResult.accuracy_score}%
                  </span>
                </div>

                {/* Retained vs Missed Breakdown */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {/* Retained Concepts */}
                  <div className="p-5 rounded-[24px] bg-emerald-50/60 border border-emerald-200 space-y-2">
                    <div className="flex items-center gap-2 text-xs font-black text-emerald-800">
                      <Check className="w-4 h-4 text-emerald-600" />
                      <span>Retained Concepts ({blurtingResult.retained_concepts?.length || 0})</span>
                    </div>
                    <ul className="text-xs text-emerald-950 space-y-1.5 list-disc pl-4 font-medium">
                      {blurtingResult.retained_concepts?.map((c: string, idx: number) => (
                        <li key={idx}>{c}</li>
                      ))}
                    </ul>
                  </div>

                  {/* Missed Nuances */}
                  <div className="p-5 rounded-[24px] bg-amber-50/60 border border-amber-200 space-y-2">
                    <div className="flex items-center gap-2 text-xs font-black text-amber-800">
                      <AlertTriangle className="w-4 h-4 text-amber-600" />
                      <span>Missed Nuances ({blurtingResult.missed_nuances?.length || 0})</span>
                    </div>
                    <ul className="text-xs text-amber-950 space-y-1.5 list-disc pl-4 font-medium">
                      {blurtingResult.missed_nuances?.map((m: string, idx: number) => (
                        <li key={idx}>{m}</li>
                      ))}
                    </ul>
                  </div>
                </div>

                {/* 2357 Focus Recommendation */}
                <div className="p-4 rounded-[20px] bg-brand-surface-dim border border-brand-outline-variant space-y-1">
                  <span className="text-xs font-bold text-brand-secondary flex items-center gap-1.5">
                    <Sparkles className="w-3.5 h-3.5 text-[#3a10e5]" />
                    <span>2357 Schedule Recommendation:</span>
                  </span>
                  <p className="text-xs text-brand-on-surface-variant leading-relaxed font-medium">
                    {blurtingResult.recommended_focus}
                  </p>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Tab 3: Feynman Loop Active Recall Arena */}
        {tab === "feynman" && (
          <div className="max-w-3xl mx-auto space-y-6">
            <div className="p-8 rounded-[32px] bg-white border border-brand-outline-variant shadow-sm space-y-5">
              <div className="flex items-center justify-between">
                <span className="px-3 py-1 rounded-full bg-brand-primary/10 text-brand-primary text-xs font-mono font-bold">
                  The Feynman Challenge
                </span>
                <span className="text-xs font-mono text-brand-on-surface-variant">
                  File: {activeFileName}
                </span>
              </div>

              <div className="space-y-1">
                <h3 className="text-2xl font-black text-brand-secondary">{feynmanPrompt}</h3>
                <p className="text-xs text-brand-on-surface-variant font-medium">
                  Explain without technical jargon. Our precision-gap engine verifies your grounding against course documents.
                </p>
              </div>

              <textarea
                value={explanation}
                onChange={(e) => setExplanation(e.target.value)}
                rows={6}
                placeholder={`Type your plain-language analogy for ${concept} here... e.g. This mechanism works like a...`}
                className="w-full p-4 rounded-[20px] bg-brand-surface-dim border border-brand-outline-variant text-xs text-brand-secondary focus:outline-none focus:border-[#3a10e5] leading-relaxed font-medium"
              />

              <div className="flex justify-end">
                <button
                  onClick={handleEvaluateFeynman}
                  disabled={isEvaluating || !explanation.trim()}
                  className="px-6 py-3 rounded-[24px] bg-[#3a10e5] hover:opacity-90 text-white text-xs font-bold transition-all shadow-sm flex items-center gap-2 cursor-pointer disabled:opacity-50"
                >
                  <RefreshCw className={`w-3.5 h-3.5 ${isEvaluating ? "animate-spin" : ""}`} />
                  <span>{isEvaluating ? "Evaluating Precision Gaps..." : "Submit for Gap Analysis"}</span>
                </button>
              </div>
            </div>

            {/* Precision Gap Feedback */}
            {feynmanFeedback && (
              <div className="p-8 rounded-[32px] bg-white border border-brand-outline-variant shadow-md space-y-4 animate-fadeIn">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <CheckCircle2 className="w-5 h-5 text-emerald-600" />
                    <h4 className="font-bold text-sm text-brand-secondary">Precision-Gap Evaluation Results</h4>
                  </div>
                  <span className="text-xs font-mono font-bold px-3 py-1 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200">
                    Completeness: {Math.round((feynmanFeedback.completeness_score || 0.88) * 100)}%
                  </span>
                </div>

                <p className="text-xs text-brand-secondary leading-relaxed bg-brand-surface-dim p-4 rounded-[20px] border border-brand-outline-variant font-medium">
                  {feynmanFeedback.feedback}
                </p>

                {feynmanFeedback.missing_concepts && feynmanFeedback.missing_concepts.length > 0 && (
                  <div className="space-y-2">
                    <div className="text-xs font-bold text-amber-800">Identified Concept Gaps:</div>
                    <ul className="text-xs text-brand-on-surface-variant list-disc pl-5 space-y-1 font-medium">
                      {feynmanFeedback.missing_concepts.map((g: string, idx: number) => (
                        <li key={idx}>{g}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </main>

      <OnboardingModal
        isOpen={showOnboarding}
        onSave={() => setShowOnboarding(false)}
      />
    </div>
  );
}

export default function ReviewPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen flex flex-col bg-[#f8f9fb] items-center justify-center">
          <div className="flex items-center gap-3 text-brand-secondary font-bold text-sm">
            <Loader2 className="w-5 h-5 animate-spin text-[#3a10e5]" />
            <span>Loading Review State...</span>
          </div>
        </div>
      }
    >
      <ReviewContent />
    </Suspense>
  );
}
