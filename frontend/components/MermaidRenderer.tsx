"use client";

import React, { useEffect, useRef, useState } from "react";
import { Copy, Check, RefreshCw, ZoomIn, ZoomOut, AlertTriangle, Sparkles, BookOpen, ChevronRight, X, Compass } from "lucide-react";
import { extractMermaidDiagram, sanitizeDiagramSyntax } from "@/lib/mermaidUtils";

export interface ConceptBranch {
  title: string;
  sub_branches: string[];
}

export interface ConceptTreeData {
  root?: string;
  branches?: ConceptBranch[];
  leaf_descriptions?: Record<string, string>;
}

interface MermaidRendererProps {
  chart: string;
  alternativeChart?: string;
  conceptTree?: ConceptTreeData;
  className?: string;
}

export default function MermaidRenderer({
  chart,
  alternativeChart,
  conceptTree,
  className = "",
}: MermaidRendererProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [activeView, setActiveView] = useState<"primary" | "alternative">("primary");
  const [svgContent, setSvgContent] = useState<string>("");
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const [zoom, setZoom] = useState(1.0);
  const [selectedLeaf, setSelectedLeaf] = useState<{
    label: string;
    branchTitle?: string;
    description: string;
  } | null>(null);

  const activeChart = activeView === "primary" ? chart : alternativeChart || chart;

  useEffect(() => {
    let isMounted = true;

    async function renderMermaid() {
      // Clean up any stray error divs injected into the body by previous mermaid failures
      if (typeof document !== "undefined") {
        document.querySelectorAll('[id^="dmermaid-"]').forEach((el) => el.remove());
      }

      try {
        setError(null);

        // Extract pure diagram syntax, stripping away any markdown commentary
        const { diagram } = extractMermaidDiagram(activeChart);
        const cleaned = sanitizeDiagramSyntax(diagram);

        if (!cleaned) {
          if (isMounted) setSvgContent("");
          return;
        }

        // Dynamically import mermaid to keep SSR bundles lightweight
        // @ts-ignore
        const mermaid = (await import("mermaid")).default;
        mermaid.initialize({
          startOnLoad: false,
          suppressErrorRendering: true, // Prevents Mermaid from injecting ugly "Syntax error" DIVs into document.body
          theme: "neutral",
          securityLevel: "loose",
          fontFamily: "Inter, sans-serif",
        });

        const id = `mermaid-${Math.random().toString(36).substring(2, 9)}`;

        try {
          const { svg } = await mermaid.render(id, cleaned);
          if (isMounted) {
            setSvgContent(svg);
          }
        } catch (primaryErr: any) {
          // If primary diagram fails (e.g. strict mindmap syntax) and an alternative is available, try the alternative
          if (activeView === "primary" && alternativeChart) {
            console.warn("Primary diagram render failed, falling back to sequential process flow:", primaryErr);
            const { diagram: altDiagram } = extractMermaidDiagram(alternativeChart);
            const altCleaned = sanitizeDiagramSyntax(altDiagram);
            const altId = `mermaid-alt-${Math.random().toString(36).substring(2, 9)}`;
            const { svg: altSvg } = await mermaid.render(altId, altCleaned);
            if (isMounted) {
              setSvgContent(altSvg);
              setActiveView("alternative");
              return;
            }
          }
          throw primaryErr;
        }
      } catch (err: any) {
        console.warn("Mermaid render error:", err);
        if (isMounted) {
          setError(err?.message || "Syntax error rendering diagram");
        }
      } finally {
        // Guarantee no leaked Mermaid error SVGs remain in the body
        if (typeof document !== "undefined") {
          document.querySelectorAll('[id^="dmermaid-"]').forEach((el) => el.remove());
        }
      }
    }

    renderMermaid();

    return () => {
      isMounted = false;
      if (typeof document !== "undefined") {
        document.querySelectorAll('[id^="dmermaid-"]').forEach((el) => el.remove());
      }
    };
  }, [activeChart, activeView, alternativeChart]);

  const handleCopy = () => {
    navigator.clipboard.writeText(activeChart);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  // Helper to lookup leaf description given any label or text fragment
  const findLeafDetail = (rawText: string) => {
    if (!conceptTree) return null;
    const cleanQuery = rawText.replace(/[\(\)\[\]\"\{\}:;`]/g, "").trim().toLowerCase();
    if (!cleanQuery) return null;

    const descriptions = conceptTree.leaf_descriptions || {};
    const branches = conceptTree.branches || [];

    // 1. Direct or partial match in leaf_descriptions
    for (const [leafName, desc] of Object.entries(descriptions)) {
      const cleanLeaf = leafName.toLowerCase();
      if (cleanLeaf === cleanQuery || cleanLeaf.includes(cleanQuery) || cleanQuery.includes(cleanLeaf)) {
        // Find which branch this leaf belongs to
        const parentBranch = branches.find((b) =>
          b.sub_branches?.some((sub) => sub.toLowerCase() === cleanLeaf || cleanLeaf.includes(sub.toLowerCase()))
        );
        return {
          label: leafName,
          branchTitle: parentBranch?.title,
          description: desc,
        };
      }
    }

    // 2. Direct match in branches or sub_branches
    for (const branch of branches) {
      for (const sub of branch.sub_branches || []) {
        if (sub.toLowerCase() === cleanQuery || sub.toLowerCase().includes(cleanQuery) || cleanQuery.includes(sub.toLowerCase())) {
          return {
            label: sub,
            branchTitle: branch.title,
            description: descriptions[sub] || `Key foundational concept underpinning ${branch.title}. Essential for understanding ${conceptTree.root || "the topic"}.`,
          };
        }
      }
      if (branch.title.toLowerCase() === cleanQuery || branch.title.toLowerCase().includes(cleanQuery)) {
        return {
          label: branch.title,
          branchTitle: "Primary Conceptual Pillar",
          description: `Major structural theme of ${conceptTree.root || "the topic"} containing ${branch.sub_branches?.length || 0} core component concepts.`,
        };
      }
    }

    return null;
  };

  // Attach SVG click listener to catch mindmap node clicks directly
  const handleSvgClick = (e: React.MouseEvent<HTMLDivElement>) => {
    const target = e.target as HTMLElement | SVGElement;
    if (!target) return;

    // Mindmap nodes in mermaid are wrapped in <g class="mindmap-node ..."> or have text elements
    const closestGroup = target.closest("g.mindmap-node, g.node, g");
    const textContent = closestGroup?.textContent || target.textContent;

    if (textContent) {
      const detail = findLeafDetail(textContent);
      if (detail) {
        setSelectedLeaf(detail);
      }
    }
  };

  return (
    <div className={`relative rounded-[32px] bg-white border border-brand-outline-variant p-6 shadow-sm overflow-hidden transition-all ${className}`}>
      {/* Action Toolbar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-brand-outline-variant/60 text-xs text-brand-on-surface-variant font-mono gap-2">
        <div className="flex items-center gap-2">
          <span className="w-2.5 h-2.5 rounded-full bg-brand-primary animate-pulse" />
          <span className="font-bold uppercase tracking-wider text-brand-secondary">
            {activeView === "primary" ? "Interactive Mind Map" : "Sequential Process Flow"}
          </span>

          {alternativeChart && (
            <div className="ml-2 inline-flex items-center p-0.5 rounded-full bg-brand-surface-dim border border-brand-outline-variant">
              <button
                onClick={() => setActiveView("primary")}
                className={`px-3 py-1 rounded-full text-[11px] font-sans font-bold transition-all cursor-pointer ${
                  activeView === "primary"
                    ? "bg-brand-primary text-white shadow-xs"
                    : "text-brand-on-surface-variant hover:text-brand-secondary"
                }`}
              >
                Mind Map
              </button>
              <button
                onClick={() => setActiveView("alternative")}
                className={`px-3 py-1 rounded-full text-[11px] font-sans font-bold transition-all cursor-pointer ${
                  activeView === "alternative"
                    ? "bg-brand-primary text-white shadow-xs"
                    : "text-brand-on-surface-variant hover:text-brand-secondary"
                }`}
              >
                Process Flow
              </button>
            </div>
          )}
        </div>
        <div className="flex items-center gap-1.5 self-end sm:self-center">
          <button
            onClick={() => setZoom((z) => Math.max(0.6, z - 0.1))}
            className="p-1.5 rounded-lg hover:bg-brand-surface-dim transition-all text-brand-on-surface-variant cursor-pointer"
            title="Zoom Out"
          >
            <ZoomOut className="w-3.5 h-3.5" />
          </button>
          <span className="text-[10px] font-bold px-1">{Math.round(zoom * 100)}%</span>
          <button
            onClick={() => setZoom((z) => Math.min(1.8, z + 0.1))}
            className="p-1.5 rounded-lg hover:bg-brand-surface-dim transition-all text-brand-on-surface-variant cursor-pointer"
            title="Zoom In"
          >
            <ZoomIn className="w-3.5 h-3.5" />
          </button>
          <div className="h-3 w-[1px] bg-brand-outline-variant mx-1" />
          <button
            onClick={handleCopy}
            className="flex items-center gap-1 px-2.5 py-1 rounded-lg hover:bg-brand-surface-dim transition-all font-sans font-semibold text-brand-secondary cursor-pointer"
            title="Copy Diagram Syntax"
          >
            {copied ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5" />}
            <span>{copied ? "Copied" : "Copy"}</span>
          </button>
        </div>
      </div>

      {/* Diagram Render Area with cursor-pointer for nodes */}
      <div className="p-4 flex flex-col items-center justify-center overflow-x-auto min-h-[220px]">
        {error ? (
          <div className="text-left w-full space-y-2">
            <div className="text-xs text-amber-700 bg-amber-50 p-2.5 rounded-xl border border-amber-200">
              Displaying formatted syntax preview:
            </div>
            <pre className="font-mono text-xs text-brand-secondary bg-brand-surface-dim p-4 rounded-xl overflow-x-auto">
              {chart}
            </pre>
          </div>
        ) : svgContent ? (
          <div className="w-full flex flex-col items-center">
            <div
              ref={containerRef}
              onClick={handleSvgClick}
              style={{
                transform: `scale(${zoom})`,
                transformOrigin: "top center",
                transition: "transform 0.15s ease",
              }}
              className="w-full flex justify-center py-2 cursor-pointer select-none [&_.mindmap-node]:cursor-pointer [&_.mindmap-node:hover]:opacity-80 [&_.node]:cursor-pointer [&_text]:cursor-pointer"
              dangerouslySetInnerHTML={{ __html: svgContent }}
            />
            {activeView === "primary" && (
              <p className="text-[11px] font-medium text-brand-on-surface-variant/70 mt-2 flex items-center gap-1.5">
                <Sparkles className="w-3.5 h-3.5 text-brand-primary" />
                Click any leaf or branch in the diagram (or the concept pills below) to inspect detailed explanations.
              </p>
            )}
          </div>
        ) : (
          <div className="text-xs text-brand-on-surface-variant font-mono animate-pulse">
            Rendering interactive diagram...
          </div>
        )}
      </div>

      {/* Selected Leaf Detail Card (Perplexity Aesthetic rounded-[32px]) */}
      {selectedLeaf && (
        <div className="mt-4 rounded-[28px] bg-brand-surface-dim/70 border border-brand-primary/20 p-5 sm:p-6 space-y-3 relative animate-in fade-in slide-in-from-top-2 duration-200 shadow-sm">
          <div className="flex items-start justify-between gap-3">
            <div className="space-y-1">
              <div className="flex items-center gap-2 flex-wrap">
                <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-brand-primary/10 text-brand-primary">
                  <BookOpen className="w-3 h-3" />
                  Concept Leaf
                </span>
                {selectedLeaf.branchTitle && (
                  <span className="inline-flex items-center gap-1 text-[11px] font-medium text-brand-on-surface-variant">
                    <ChevronRight className="w-3 h-3" />
                    {selectedLeaf.branchTitle}
                  </span>
                )}
              </div>
              <h4 className="text-base sm:text-lg font-black text-brand-secondary tracking-tight">
                {selectedLeaf.label}
              </h4>
            </div>
            <button
              onClick={() => setSelectedLeaf(null)}
              className="p-1.5 rounded-full hover:bg-brand-surface text-brand-on-surface-variant transition-colors cursor-pointer"
              title="Close description"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
          <p className="text-sm text-brand-secondary/90 leading-relaxed font-medium bg-white/80 p-4 rounded-[20px] border border-brand-outline-variant/40">
            {selectedLeaf.description}
          </p>
        </div>
      )}

      {/* Interactive Concept Explorer Pills */}
      {conceptTree?.branches && conceptTree.branches.length > 0 && (
        <div className="mt-5 pt-4 border-t border-brand-outline-variant/50 space-y-3">
          <div className="flex items-center gap-2 text-xs font-bold text-brand-secondary">
            <Compass className="w-3.5 h-3.5 text-brand-primary" />
            <span>Interactive Concept Explorer</span>
          </div>

          <div className="space-y-2.5">
            {conceptTree.branches.map((branch, idx) => (
              <div key={idx} className="flex flex-col sm:flex-row sm:items-baseline gap-2 text-xs">
                <span className="font-bold text-brand-on-surface-variant min-w-[140px] shrink-0">
                  {branch.title}:
                </span>
                <div className="flex flex-wrap gap-1.5">
                  {branch.sub_branches?.map((leaf, leafIdx) => {
                    const isSelected = selectedLeaf?.label.toLowerCase() === leaf.toLowerCase();
                    return (
                      <button
                        key={leafIdx}
                        onClick={() => {
                          const detail = findLeafDetail(leaf);
                          if (detail) {
                            setSelectedLeaf(detail);
                          }
                        }}
                        className={`px-3 py-1 rounded-full text-[11px] font-medium transition-all cursor-pointer border ${
                          isSelected
                            ? "bg-brand-primary text-white border-brand-primary shadow-xs"
                            : "bg-white text-brand-secondary border-brand-outline-variant hover:border-brand-primary/60 hover:bg-brand-surface-dim"
                        }`}
                      >
                        {leaf}
                      </button>
                    );
                  })}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

