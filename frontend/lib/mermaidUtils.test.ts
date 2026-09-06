import { describe, it, expect } from "vitest";
import { extractMermaidDiagram, sanitizeDiagramSyntax } from "./mermaidUtils";

describe("mermaidUtils", () => {
  it("extracts pure diagram code from mixed markdown artifact payload", () => {
    const mixedPayload = `\`\`\`mermaid
mindmap
  root((Cardiology ACS))
    Pathophysiology
      Plaque rupture
\`\`\`

### Conceptual Architecture & Taxonomy: Myocardial Infarction
- **Domain Area**: Medicine
- **Context Overview**: Emergency triage protocol...`;

    const { diagram, markdownBody } = extractMermaidDiagram(mixedPayload);
    expect(diagram).toBe(`mindmap\n  root((Cardiology ACS))\n    Pathophysiology\n      Plaque rupture`);
    expect(diagram).not.toContain("### Conceptual Architecture");
    expect(markdownBody).toContain("### Conceptual Architecture & Taxonomy: Myocardial Infarction");
    expect(markdownBody).toContain("- **Domain Area**: Medicine");
  });

  it("handles pure diagram code without markdown fences", () => {
    const raw = `flowchart TD\n    A["Start"] --> B["End"]`;
    const { diagram, markdownBody } = extractMermaidDiagram(raw);
    expect(diagram).toBe(raw);
    expect(markdownBody).toBe("");
  });

  it("handles empty or whitespace strings gracefully", () => {
    expect(extractMermaidDiagram("")).toEqual({ diagram: "", markdownBody: "" });
    expect(extractMermaidDiagram("   \n  ")).toEqual({ diagram: "", markdownBody: "" });
  });

  it("sanitizes stray markdown fences and windows line endings", () => {
    const raw = "```mermaid\r\nflowchart TD\r\n    A --> B\r\n```";
    const cleaned = sanitizeDiagramSyntax(raw);
    expect(cleaned).toBe("flowchart TD\n    A --> B");
    expect(cleaned).not.toContain("\r");
  });
});
