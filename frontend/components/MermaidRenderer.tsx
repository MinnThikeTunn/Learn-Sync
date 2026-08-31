"use client";

import React, { useEffect, useRef, useState } from "react";
import { Copy, Check, RefreshCw, ZoomIn, ZoomOut } from "lucide-react";

interface MermaidRendererProps {
  chart: string;
  className?: string;
}

export default function MermaidRenderer({ chart, className = "" }: MermaidRendererProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [svgContent, setSvgContent] = useState<string>("");
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const [zoom, setZoom] = useState(1.0);

  useEffect(() => {
    let isMounted = true;

    async function renderMermaid() {
      try {
        setError(null);
        // Clean chart code if it was wrapped in markdown fences
        const cleaned = chart
          .replace(/^```(?:mermaid)?\s*/i, "")
          .replace(/\s*```$/i, "")
          .trim();

        if (!cleaned) {
          if (isMounted) setSvgContent("");
          return;
        }

        // Dynamically import mermaid to keep SSR bundles lightweight
        // @ts-ignore
        const mermaid = (await import("mermaid")).default;
        mermaid.initialize({
          startOnLoad: false,
          theme: "neutral",
          securityLevel: "loose",
          fontFamily: "Inter, sans-serif",
        });

        const id = `mermaid-${Math.random().toString(36).substring(2, 9)}`;
        const { svg } = await mermaid.render(id, cleaned);
        if (isMounted) {
          setSvgContent(svg);
        }
      } catch (err: any) {
        console.warn("Mermaid render fallback:", err);
        if (isMounted) {
          setError(err?.message || "Failed to render visual diagram");
        }
      }
    }

    renderMermaid();

    return () => {
      isMounted = false;
    };
  }, [chart]);

  const handleCopy = () => {
    navigator.clipboard.writeText(chart);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className={`relative rounded-[24px] bg-white border border-brand-outline-variant p-4 overflow-hidden ${className}`}>
      {/* Action Toolbar */}
      <div className="flex items-center justify-between pb-3 border-b border-brand-outline-variant/60 text-xs text-brand-on-surface-variant font-mono">
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-brand-primary" />
          <span className="font-semibold uppercase tracking-wider">Visual Interactive Map</span>
        </div>
        <div className="flex items-center gap-1.5">
          <button
            onClick={() => setZoom((z) => Math.max(0.6, z - 0.1))}
            className="p-1.5 rounded-lg hover:bg-brand-surface-dim transition-all text-brand-on-surface-variant"
            title="Zoom Out"
          >
            <ZoomOut className="w-3.5 h-3.5" />
          </button>
          <span className="text-[10px] font-bold px-1">{Math.round(zoom * 100)}%</span>
          <button
            onClick={() => setZoom((z) => Math.min(1.8, z + 0.1))}
            className="p-1.5 rounded-lg hover:bg-brand-surface-dim transition-all text-brand-on-surface-variant"
            title="Zoom In"
          >
            <ZoomIn className="w-3.5 h-3.5" />
          </button>
          <div className="h-3 w-[1px] bg-brand-outline-variant mx-1" />
          <button
            onClick={handleCopy}
            className="flex items-center gap-1 px-2.5 py-1 rounded-lg hover:bg-brand-surface-dim transition-all font-sans font-semibold text-brand-secondary"
            title="Copy Diagram Syntax"
          >
            {copied ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5" />}
            <span>{copied ? "Copied" : "Copy"}</span>
          </button>
        </div>
      </div>

      {/* Render Area */}
      <div className="p-4 flex items-center justify-center overflow-x-auto min-h-[160px]">
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
          <div
            ref={containerRef}
            style={{ transform: `scale(${zoom})`, transformOrigin: "top center", transition: "transform 0.15s ease" }}
            className="w-full flex justify-center py-2"
            dangerouslySetInnerHTML={{ __html: svgContent }}
          />
        ) : (
          <div className="text-xs text-brand-on-surface-variant font-mono animate-pulse">
            Rendering interactive diagram...
          </div>
        )}
      </div>
    </div>
  );
}
