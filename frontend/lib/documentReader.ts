/**
 * Document Reader Utility Functions for LearnSync
 * Provides pure functions for reading stats, search indexing, and type formatting.
 */

export interface ReadingStats {
  wordCount: number;
  characterCount: number;
  estimatedMinutes: number;
}

export interface SearchSegment {
  text: string;
  isMatch: boolean;
}

export interface SearchResult {
  matchCount: number;
  segments: SearchSegment[];
}

/**
 * Calculates reading statistics based on standard 200 WPM speed.
 */
export function calculateReadingStats(text: string): ReadingStats {
  if (!text || !text.trim()) {
    return { wordCount: 0, characterCount: 0, estimatedMinutes: 1 };
  }

  const cleanText = text.trim();
  const words = cleanText.split(/\s+/).filter(Boolean);
  const wordCount = words.length;
  const characterCount = cleanText.length;
  const estimatedMinutes = Math.max(1, Math.round(wordCount / 200));

  return {
    wordCount,
    characterCount,
    estimatedMinutes,
  };
}

/**
 * Determines whether a file is a PDF based on MIME type or filename extension.
 */
export function isPdfDocument(mimeType: string = "", fileName: string = ""): boolean {
  const lowerMime = (mimeType || "").toLowerCase();
  const lowerName = (fileName || "").toLowerCase();
  return lowerMime.includes("pdf") || lowerName.endsWith(".pdf");
}

/**
 * Returns a human-friendly label for document formats.
 */
export function formatDocumentType(mimeType: string = "", fileName: string = ""): string {
  const lowerName = (fileName || "").toLowerCase();
  const lowerMime = (mimeType || "").toLowerCase();

  if (lowerMime.includes("pdf") || lowerName.endsWith(".pdf")) {
    return "PDF Document";
  }
  if (lowerMime.includes("markdown") || lowerName.endsWith(".md")) {
    return "Markdown Notes";
  }
  if (lowerMime.includes("json") || lowerName.endsWith(".json")) {
    return "JSON Document";
  }
  return "Text Document";
}

/**
 * Splits document text into matched and non-matched segments for highlighting.
 */
export function highlightSearchMatches(text: string, query: string): SearchResult {
  if (!text) {
    return { matchCount: 0, segments: [] };
  }
  if (!query || !query.trim()) {
    return {
      matchCount: 0,
      segments: [{ text, isMatch: false }],
    };
  }

  const trimmedQuery = query.trim();
  const escapedQuery = trimmedQuery.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  const regex = new RegExp(`(${escapedQuery})`, "gi");

  const parts = text.split(regex);
  const segments: SearchSegment[] = [];
  let matchCount = 0;

  for (const part of parts) {
    if (!part) continue;
    if (part.toLowerCase() === trimmedQuery.toLowerCase()) {
      segments.push({ text: part, isMatch: true });
      matchCount++;
    } else {
      segments.push({ text: part, isMatch: false });
    }
  }

  return {
    matchCount,
    segments,
  };
}
