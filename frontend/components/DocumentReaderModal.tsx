"use client";

import React, { useState, useEffect, useRef } from "react";
import {
  X,
  BookOpen,
  FileText,
  Search,
  Download,
  Copy,
  Check,
  Sparkles,
  BrainCircuit,
  Maximize2,
  Minimize2,
  ZoomIn,
  ZoomOut,
  Clock,
  Layers,
  ChevronDown,
  ExternalLink,
  Loader2,
  AlertCircle,
} from "lucide-react";
import Link from "next/link";
import {
  calculateReadingStats,
  highlightSearchMatches,
  formatDocumentType,
  isPdfDocument,
} from "@/lib/documentReader";
import { useAuth } from "@/context/AuthContext";

export interface DocumentReaderModalProps {
  documentId: string;
  fileName: string;
  folderId?: string | null;
  folderPath?: string;
  topic?: string;
  onClose: () => void;
}

interface DocumentChunk {
  id?: string;
  chunk_index: number;
  content: string;
  token_count: number;
}

interface DocumentContentData {
  id: string;
  file_name: string;
  file_type: string;
  file_size_bytes: number;
  storage_path: string;
  status: string;
  signed_url?: string | null;
  raw_url: string;
  full_text: string;
  chunks: DocumentChunk[];
  total_chunks: number;
  total_words: number;
  estimated_read_time_minutes: number;
}

export default function DocumentReaderModal({
  documentId,
  fileName,
  folderId,
  folderPath,
  topic,
  onClose,
}: DocumentReaderModalProps) {
  const { session } = useAuth();
  const [data, setData] = useState<DocumentContentData | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // View & Reading Settings
  const [viewMode, setViewMode] = useState<"reader" | "pdf">("reader");
  const [fontSize, setFontSize] = useState<"sm" | "base" | "lg">("base");
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [copied, setCopied] = useState<boolean>(false);
  const [selectedChunkIndex, setSelectedChunkIndex] = useState<number | null>(null);
  const [isFullscreen, setIsFullscreen] = useState<boolean>(false);

  const modalRef = useRef<HTMLDivElement>(null);
  const searchInputRef = useRef<HTMLInputElement>(null);
  const readerContentRef = useRef<HTMLDivElement>(null);

  const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

  // Fetch document content
  useEffect(() => {
    let isMounted = true;
    const fetchContent = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const headers: Record<string, string> = {};
        if (session?.access_token) {
          headers["Authorization"] = `Bearer ${session.access_token}`;
        }
        // Fallback test user id
        headers["X-Test-User-Id"] = "00000000-0000-0000-0000-000000000001";

        const res = await fetch(`${API_URL}/documents/${documentId}/content`, {
          headers,
        });

        if (!res.ok) {
          throw new Error(`Failed to load document (${res.status} ${res.statusText})`);
        }

        const json: DocumentContentData = await res.json();
        if (isMounted) {
          setData(json);
          // If it's a PDF, default to PDF viewer mode if desired, or keep reader mode
          if (isPdfDocument(json.file_type, json.file_name)) {
            setViewMode("reader"); // start with clean distraction-free reader mode, allow toggle
          }
        }
      } catch (err: any) {
        if (isMounted) {
          console.error("Error fetching document content:", err);
          setError(err.message || "Failed to load document content");
        }
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    };

    fetchContent();

    return () => {
      isMounted = false;
    };
  }, [documentId, session?.access_token, API_URL]);

  // Handle ESC key to dismiss
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        onClose();
      }
      if ((e.metaKey || e.ctrlKey) && e.key === "f") {
        e.preventDefault();
        searchInputRef.current?.focus();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [onClose]);

  // Copy full text
  const handleCopyText = async () => {
    if (!data?.full_text) return;
    try {
      await navigator.clipboard.writeText(data.full_text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.warn("Failed to copy text:", err);
    }
  };

  const isPdf = isPdfDocument(data?.file_type || "", data?.file_name || fileName);
  const rawUrl = data?.signed_url || `${API_URL}/documents/${documentId}/raw`;

  // Search highlighting
  const searchResult = highlightSearchMatches(data?.full_text || "", searchQuery);

  const fontSizeClass = {
    sm: "text-sm leading-relaxed",
    base: "text-base leading-relaxed",
    lg: "text-lg leading-loose",
  }[fontSize];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-brand-secondary/60 backdrop-blur-sm p-3 sm:p-6 animate-fadeIn">
      {/* Click outside backdrop to close */}
      <div className="absolute inset-0" onClick={onClose} />

      <div
        ref={modalRef}
        className={`relative bg-white border border-brand-outline-variant shadow-elevation-2xl rounded-[32px] w-full flex flex-col overflow-hidden transition-all duration-300 z-10 ${
          isFullscreen ? "h-[98vh] max-w-[98vw]" : "h-[90vh] max-w-5xl"
        }`}
      >
        {/* Header Bar */}
        <header className="px-6 py-4 border-b border-brand-outline-variant bg-white flex flex-col sm:flex-row sm:items-center justify-between gap-3 flex-shrink-0">
          <div className="flex items-center gap-3 min-w-0">
            <div className="w-10 h-10 rounded-2xl bg-brand-primary/10 border border-brand-primary/20 flex items-center justify-center flex-shrink-0 text-brand-primary">
              {isPdf ? <FileText className="w-5 h-5 text-purple-600" /> : <BookOpen className="w-5 h-5 text-brand-primary" />}
            </div>
            <div className="min-w-0">
              <div className="flex items-center gap-2">
                <span className="text-[10px] font-mono uppercase font-bold tracking-wider text-brand-primary bg-brand-primary/10 px-2 py-0.5 rounded-md">
                  {formatDocumentType(data?.file_type, data?.file_name || fileName)}
                </span>
                {data && (
                  <span className="text-[10px] font-mono text-brand-on-surface-variant">
                    {(data.file_size_bytes / 1024).toFixed(1)} KB
                  </span>
                )}
                {data && (
                  <span className="text-[10px] font-mono text-brand-on-surface-variant hidden md:inline-flex items-center gap-1">
                    <Clock className="w-3 h-3" /> {data.estimated_read_time_minutes} min read
                  </span>
                )}
              </div>
              <h3 className="text-base sm:text-lg font-black text-brand-secondary tracking-tight truncate max-w-xl">
                {data?.file_name || fileName}
              </h3>
            </div>
          </div>

          {/* Action & Control Bar */}
          <div className="flex items-center gap-2 flex-wrap sm:flex-nowrap">
            {/* View Mode Toggle (If PDF) */}
            {isPdf && (
              <div className="flex items-center bg-brand-surface-dim border border-brand-outline-variant rounded-xl p-0.5 text-xs font-bold">
                <button
                  type="button"
                  onClick={() => setViewMode("reader")}
                  className={`px-3 py-1.5 rounded-lg flex items-center gap-1.5 transition-all ${
                    viewMode === "reader"
                      ? "bg-white text-brand-secondary shadow-xs"
                      : "text-brand-on-surface-variant hover:text-brand-secondary"
                  }`}
                >
                  <BookOpen className="w-3.5 h-3.5" />
                  <span>Reader Mode</span>
                </button>
                <button
                  type="button"
                  onClick={() => setViewMode("pdf")}
                  className={`px-3 py-1.5 rounded-lg flex items-center gap-1.5 transition-all ${
                    viewMode === "pdf"
                      ? "bg-white text-brand-secondary shadow-xs"
                      : "text-brand-on-surface-variant hover:text-brand-secondary"
                  }`}
                >
                  <FileText className="w-3.5 h-3.5" />
                  <span>Original PDF</span>
                </button>
              </div>
            )}

            {/* Font Size Adjuster (in Reader Mode) */}
            {viewMode === "reader" && (
              <div className="hidden sm:flex items-center bg-brand-surface-dim border border-brand-outline-variant rounded-xl px-1 py-0.5 text-xs font-bold">
                <button
                  type="button"
                  onClick={() => setFontSize("sm")}
                  className={`px-2 py-1 rounded-md ${fontSize === "sm" ? "bg-white shadow-2xs text-brand-primary" : "text-brand-on-surface-variant"}`}
                  title="Small Font"
                >
                  A-
                </button>
                <button
                  type="button"
                  onClick={() => setFontSize("base")}
                  className={`px-2 py-1 rounded-md ${fontSize === "base" ? "bg-white shadow-2xs text-brand-primary" : "text-brand-on-surface-variant"}`}
                  title="Medium Font"
                >
                  A
                </button>
                <button
                  type="button"
                  onClick={() => setFontSize("lg")}
                  className={`px-2 py-1 rounded-md ${fontSize === "lg" ? "bg-white shadow-2xs text-brand-primary" : "text-brand-on-surface-variant"}`}
                  title="Large Font"
                >
                  A+
                </button>
              </div>
            )}

            {/* Copy Button */}
            {data?.full_text && (
              <button
                type="button"
                onClick={handleCopyText}
                className="p-2 rounded-xl border border-brand-outline-variant bg-white hover:bg-brand-surface-dim text-brand-secondary text-xs transition-colors"
                title="Copy Full Text"
              >
                {copied ? <Check className="w-4 h-4 text-emerald-600" /> : <Copy className="w-4 h-4" />}
              </button>
            )}

            {/* Download Raw File Button */}
            <a
              href={rawUrl}
              download={data?.file_name || fileName}
              target="_blank"
              rel="noopener noreferrer"
              className="p-2 rounded-xl border border-brand-outline-variant bg-white hover:bg-brand-surface-dim text-brand-secondary text-xs transition-colors"
              title="Download or Open Raw File"
            >
              <Download className="w-4 h-4" />
            </a>

            {/* Fullscreen Toggle */}
            <button
              type="button"
              onClick={() => setIsFullscreen(!isFullscreen)}
              className="hidden md:flex p-2 rounded-xl border border-brand-outline-variant bg-white hover:bg-brand-surface-dim text-brand-secondary text-xs transition-colors"
              title={isFullscreen ? "Exit Fullscreen" : "Fullscreen View"}
            >
              {isFullscreen ? <Minimize2 className="w-4 h-4" /> : <Maximize2 className="w-4 h-4" />}
            </button>

            {/* Close Button */}
            <button
              type="button"
              onClick={onClose}
              className="p-2 rounded-xl border border-brand-outline-variant bg-brand-surface-dim hover:bg-rose-50 hover:text-rose-600 text-brand-secondary text-xs transition-colors"
              title="Close Reader (Esc)"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </header>

        {/* Reader Sub-Toolbar (Search & Chunk selector) */}
        {viewMode === "reader" && (
          <div className="px-6 py-2.5 bg-brand-surface-dim/70 border-b border-brand-outline-variant flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs">
            {/* Live Document Search */}
            <div className="relative flex-1 max-w-md">
              <Search className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-brand-on-surface-variant" />
              <input
                ref={searchInputRef}
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search in document... (Ctrl+F)"
                className="w-full pl-8 pr-16 py-1.5 rounded-xl bg-white border border-brand-outline-variant text-xs text-brand-secondary focus:outline-none focus:ring-1 focus:ring-brand-primary placeholder:text-brand-on-surface-variant/60"
              />
              {searchQuery && (
                <span className="absolute right-3 top-1/2 -translate-y-1/2 text-[10px] font-mono text-brand-on-surface-variant">
                  {searchResult.matchCount} {searchResult.matchCount === 1 ? "match" : "matches"}
                </span>
              )}
            </div>

            {/* Quick Stats & Chunk count */}
            <div className="flex items-center gap-3 text-brand-on-surface-variant font-mono text-[11px]">
              {data && (
                <span>
                  <strong>{data.total_words}</strong> words • <strong>{data.total_chunks}</strong> vector chunks
                </span>
              )}
              {data?.chunks && data.chunks.length > 1 && (
                <div className="flex items-center gap-1">
                  <Layers className="w-3 h-3 text-brand-primary" />
                  <select
                    value={selectedChunkIndex !== null ? selectedChunkIndex : ""}
                    onChange={(e) => {
                      const val = e.target.value;
                      if (val === "") {
                        setSelectedChunkIndex(null);
                      } else {
                        setSelectedChunkIndex(Number(val));
                      }
                    }}
                    className="bg-white border border-brand-outline-variant rounded-lg px-2 py-1 text-xs text-brand-secondary font-sans focus:outline-none"
                  >
                    <option value="">Full Document (All Chunks)</option>
                    {data.chunks.map((c, i) => (
                      <option key={i} value={c.chunk_index}>
                        Section #{c.chunk_index + 1} ({c.token_count} tokens)
                      </option>
                    ))}
                  </select>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Content Body */}
        <div className="flex-1 overflow-hidden relative bg-white">
          {isLoading ? (
            <div className="absolute inset-0 flex flex-col items-center justify-center gap-3 text-brand-on-surface-variant">
              <Loader2 className="w-8 h-8 animate-spin text-brand-primary" />
              <p className="text-xs font-bold tracking-tight">Extracting document content and chunks...</p>
            </div>
          ) : error ? (
            <div className="p-8 max-w-lg mx-auto text-center space-y-4 my-auto h-full flex flex-col justify-center items-center">
              <div className="w-12 h-12 rounded-2xl bg-rose-50 border border-rose-200 text-rose-600 flex items-center justify-center mx-auto">
                <AlertCircle className="w-6 h-6" />
              </div>
              <h4 className="text-base font-black text-brand-secondary">Unable to Load Document</h4>
              <p className="text-xs text-brand-on-surface-variant">{error}</p>
              <div className="flex items-center gap-2">
                <a
                  href={rawUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="px-4 py-2 rounded-xl bg-brand-primary text-white text-xs font-bold hover:bg-brand-primary/90 transition-all flex items-center gap-1.5"
                >
                  <ExternalLink className="w-3.5 h-3.5" />
                  <span>Open Raw File Directly</span>
                </a>
                <button
                  type="button"
                  onClick={onClose}
                  className="px-4 py-2 rounded-xl border border-brand-outline-variant bg-white text-xs font-bold text-brand-secondary"
                >
                  Close
                </button>
              </div>
            </div>
          ) : viewMode === "pdf" ? (
            /* Native PDF Viewer inside iframe */
            <div className="w-full h-full p-2 bg-brand-surface-dim/40 flex flex-col">
              <iframe
                src={`${rawUrl}#toolbar=1&navpanes=1`}
                className="w-full h-full border-0 rounded-2xl bg-white shadow-inner"
                title={data?.file_name || "PDF Document"}
              />
            </div>
          ) : (
            /* Reader Mode: Distraction-Free Typography with Search Highlighting */
            <div
              ref={readerContentRef}
              className="w-full h-full overflow-y-auto px-6 sm:px-12 py-8 space-y-6"
            >
              <div className="max-w-3xl mx-auto space-y-6">
                {/* Header Summary Card */}
                <div className="p-4 rounded-2xl bg-brand-surface-dim border border-brand-outline-variant flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs">
                  <div>
                    <span className="text-[11px] text-brand-on-surface-variant font-mono">Document Partition</span>
                    <p className="font-bold text-brand-secondary">{folderPath || "/root"}</p>
                  </div>
                  {topic && (
                    <div>
                      <span className="text-[11px] text-brand-on-surface-variant font-mono">Assigned Concept</span>
                      <p className="font-bold text-brand-primary">{topic}</p>
                    </div>
                  )}
                  <div className="flex items-center gap-2">
                    <span className="px-2.5 py-1 rounded-full bg-emerald-50 text-emerald-800 border border-emerald-200 font-mono text-[10px] font-bold">
                      {data?.status === "learned" ? "Learned • Active Review" : "Ready for Learning"}
                    </span>
                  </div>
                </div>

                {/* Document Chunks or Filtered Chunk View */}
                {selectedChunkIndex !== null && data?.chunks ? (
                  /* Single Chunk View */
                  <div className="space-y-3">
                    <div className="flex items-center justify-between text-xs border-b border-brand-outline-variant pb-2">
                      <span className="font-bold text-brand-secondary">
                        Section #{selectedChunkIndex + 1}
                      </span>
                      <button
                        type="button"
                        onClick={() => setSelectedChunkIndex(null)}
                        className="text-xs font-bold text-brand-primary hover:underline"
                      >
                        Show All Sections
                      </button>
                    </div>
                    <div className={`font-serif text-brand-secondary ${fontSizeClass} whitespace-pre-wrap leading-relaxed select-text bg-brand-surface-dim/30 p-6 rounded-2xl border border-brand-outline-variant`}>
                      {data.chunks.find((c) => c.chunk_index === selectedChunkIndex)?.content || "Section not found."}
                    </div>
                  </div>
                ) : (
                  /* Full Document Text */
                  <article className={`text-brand-secondary select-text space-y-4 ${fontSizeClass}`}>
                    {searchQuery.trim() ? (
                      <div className="whitespace-pre-wrap font-serif">
                        {searchResult.segments.map((seg, idx) =>
                          seg.isMatch ? (
                            <mark
                              key={idx}
                              className="bg-amber-200 text-amber-950 font-bold px-1 py-0.5 rounded"
                            >
                              {seg.text}
                            </mark>
                          ) : (
                            <span key={idx}>{seg.text}</span>
                          )
                        )}
                      </div>
                    ) : (
                      <div className="whitespace-pre-wrap font-serif leading-relaxed text-brand-secondary/90">
                        {data?.full_text || "No text content could be extracted from this document."}
                      </div>
                    )}
                  </article>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Footer Quick Action Seam */}
        <footer className="px-6 py-3 border-t border-brand-outline-variant bg-white flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs flex-shrink-0">
          <div className="text-brand-on-surface-variant font-mono text-[11px] truncate">
            <span>LearnSync Document Seam • </span>
            <span className="text-brand-secondary font-bold">{data?.total_chunks || 0} vectorized chunks</span>
          </div>

          <div className="flex items-center gap-2">
            <Link
              href={`/study?document_id=${documentId}&file_name=${encodeURIComponent(data?.file_name || fileName)}&folder_id=${folderId || ""}&folder=${encodeURIComponent(folderPath || "")}&topic=${encodeURIComponent(topic || "")}`}
              onClick={onClose}
              className="px-4 py-2 rounded-xl bg-brand-primary hover:bg-brand-primary/90 text-white font-bold text-xs transition-all shadow-xs flex items-center gap-1.5 cursor-pointer"
            >
              <Sparkles className="w-3.5 h-3.5" />
              <span>Study in Learning Mode</span>
            </Link>

            <Link
              href={`/review?document_id=${documentId}&file_name=${encodeURIComponent(data?.file_name || fileName)}&folder_id=${folderId || ""}&topic=${encodeURIComponent(topic || "")}`}
              onClick={onClose}
              className="px-4 py-2 rounded-xl bg-purple-50 text-purple-700 hover:bg-purple-100 border border-purple-200 font-bold text-xs transition-all flex items-center gap-1.5 shadow-xs cursor-pointer"
            >
              <BrainCircuit className="w-3.5 h-3.5 text-[#3a10e5]" />
              <span>Review Flashcards</span>
            </Link>

            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 rounded-xl border border-brand-outline-variant bg-white hover:bg-brand-surface-dim text-brand-secondary font-bold text-xs transition-all"
            >
              Done Reading
            </button>
          </div>
        </footer>
      </div>
    </div>
  );
}
