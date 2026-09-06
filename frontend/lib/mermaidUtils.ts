/**
 * Utility functions for safely parsing, extracting, and sanitizing Mermaid diagram strings.
 */

export interface ExtractedMermaid {
  diagram: string;
  markdownBody: string;
}

/**
 * Extracts pure Mermaid diagram code from a raw string that may contain markdown code fences
 * and trailing markdown commentary.
 */
export function extractMermaidDiagram(raw: string): ExtractedMermaid {
  if (!raw) return { diagram: "", markdownBody: "" };

  const trimmed = raw.trim();

  // Match ```mermaid ... ``` or ``` ... ``` code blocks
  const fenceMatch = trimmed.match(/```(?:mermaid)?\s*([\s\S]*?)```/i);
  if (fenceMatch) {
    const diagram = fenceMatch[1].trim();
    // Everything before and after the fence is treated as markdown commentary
    const before = trimmed.slice(0, fenceMatch.index).trim();
    const after = trimmed.slice(fenceMatch.index! + fenceMatch[0].length).trim();
    const markdownBody = [before, after].filter(Boolean).join("\n\n");
    return { diagram, markdownBody };
  }

  // Check if string begins directly with a known Mermaid diagram keyword
  const validKeywords = [
    "flowchart",
    "graph",
    "mindmap",
    "sequencediagram",
    "classdiagram",
    "erdiagram",
    "statediagram",
    "gitgraph",
    "pie",
    "journey",
    "gantt",
    "c4context",
  ];

  const firstLine = trimmed.split("\n")[0].trim().toLowerCase();
  const startsWithKeyword = validKeywords.some((kw) => firstLine.startsWith(kw));

  if (startsWithKeyword) {
    return { diagram: trimmed, markdownBody: "" };
  }

  // Fallback: return as diagram
  return { diagram: trimmed, markdownBody: "" };
}

/**
 * Sanitizes diagram syntax to prevent common Mermaid 11.x parsing crashes.
 */
export function sanitizeDiagramSyntax(diagram: string): string {
  if (!diagram) return "";

  // Remove any remaining stray markdown fences
  let cleaned = diagram
    .replace(/^```(?:mermaid)?\s*/gim, "")
    .replace(/\s*```$/gim, "")
    .trim();

  // Strip carriage returns
  cleaned = cleaned.replace(/\r\n/g, "\n");

  return cleaned;
}
