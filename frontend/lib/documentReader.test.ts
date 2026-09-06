import { describe, it, expect } from "vitest";
import {
  calculateReadingStats,
  highlightSearchMatches,
  formatDocumentType,
  isPdfDocument,
} from "./documentReader";

describe("Document Reader Utilities (TDD Seam)", () => {
  it("computes accurate reading stats for document chunks and text", () => {
    const sampleText = "Distributed systems require consensus algorithms like Paxos and Raft to ensure safety and liveness across network partitions.";
    const stats = calculateReadingStats(sampleText);

    expect(stats.wordCount).toBe(17);
    expect(stats.characterCount).toBe(sampleText.length);
    expect(stats.estimatedMinutes).toBe(1); // rounded up to at least 1 min
  });

  it("identifies PDF documents accurately from mime type or extension", () => {
    expect(isPdfDocument("application/pdf", "syllabus.pdf")).toBe(true);
    expect(isPdfDocument("application/octet-stream", "lecture_slides.PDF")).toBe(true);
    expect(isPdfDocument("text/plain", "notes.txt")).toBe(false);
    expect(isPdfDocument("text/markdown", "readme.md")).toBe(false);
  });

  it("formats human-readable document types", () => {
    expect(formatDocumentType("application/pdf", "syllabus.pdf")).toBe("PDF Document");
    expect(formatDocumentType("text/markdown", "notes.md")).toBe("Markdown Notes");
    expect(formatDocumentType("text/plain", "log.txt")).toBe("Text Document");
    expect(formatDocumentType("application/json", "schema.json")).toBe("JSON Document");
  });

  it("finds and counts search query occurrences within document text", () => {
    const text = "Raft is a consensus algorithm. Raft is designed to be easy to understand. raft ensures consistency.";
    const search = highlightSearchMatches(text, "raft");

    expect(search.matchCount).toBe(3);
    expect(search.segments.length).toBeGreaterThan(1);
  });
});
