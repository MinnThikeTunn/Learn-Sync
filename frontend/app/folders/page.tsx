"use client";

import { useState, useEffect, useRef } from "react";
import { 
  FolderTree, 
  Folder, 
  FileText, 
  UploadCloud, 
  CheckCircle2, 
  ChevronRight, 
  ChevronDown, 
  Sparkles,
  Calendar,
  Layers,
  ArrowRight,
  Plus
} from "lucide-react";
import Link from "next/link";
import Navbar from "@/components/Navbar";
import { useAuth } from "@/context/AuthContext";

interface FolderItem {
  id: string;
  name: string;
  materialized_path: string;
  depth: number;
  course_code?: string;
  document_count?: number;
  children?: FolderItem[];
}

export default function VirtualFoldersPage() {
  const { user } = useAuth();
  const [selectedFolder, setSelectedFolder] = useState<string>("/CS101/Week_03_Recursion");
  const [isUploading, setIsUploading] = useState(false);
  const [stagedPreview, setStagedPreview] = useState<any>(null);
  const [folders, setFolders] = useState<FolderItem[]>([]);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const fallbackFolders: FolderItem[] = [
    {
      id: "root-cs101",
      name: "CS101",
      materialized_path: "/CS101",
      depth: 0,
      course_code: "CS101",
      document_count: 4,
      children: [
        {
          id: "cs101-w1",
          name: "Week_01_Foundations_of_Computation",
          materialized_path: "/CS101/Week_01_Foundations_of_Computation",
          depth: 1,
          course_code: "CS101",
          document_count: 2,
        },
        {
          id: "cs101-w2",
          name: "Week_02_Control_Flow_and_Functions",
          materialized_path: "/CS101/Week_02_Control_Flow_and_Functions",
          depth: 1,
          course_code: "CS101",
          document_count: 1,
        },
        {
          id: "cs101-w3",
          name: "Week_03_Recursion",
          materialized_path: "/CS101/Week_03_Recursion",
          depth: 1,
          course_code: "CS101",
          document_count: 3,
        },
      ],
    },
    {
      id: "root-cs204",
      name: "CS204",
      materialized_path: "/CS204",
      depth: 0,
      course_code: "CS204",
      document_count: 3,
      children: [
        {
          id: "cs204-w1",
          name: "Module_01_Graph_Representations",
          materialized_path: "/CS204/Module_01_Graph_Representations",
          depth: 1,
          course_code: "CS204",
          document_count: 2,
        },
        {
          id: "cs204-w2",
          name: "Module_02_Graph_Traversals",
          materialized_path: "/CS204/Module_02_Graph_Traversals",
          depth: 1,
          course_code: "CS204",
          document_count: 4,
        },
      ],
    },
  ];

  const fetchFoldersTree = async () => {
    try {
      const res = await fetch("http://localhost:8000/api/v1/folders/tree", {
        headers: { "X-Test-User-Id": user?.id || "00000000-0000-0000-0000-000000000001" },
      });
      if (res.ok) {
        const data = await res.json();
        if (data && data.length > 0) {
          // Group into hierarchical tree
          const roots = data.filter((f: any) => f.depth === 0);
          const tree = roots.map((root: any) => ({
            ...root,
            course_code: root.name,
            document_count: 3,
            children: data.filter((child: any) => child.depth > 0 && child.materialized_path.startsWith(root.materialized_path)),
          }));
          setFolders(tree.length > 0 ? tree : fallbackFolders);
          return;
        }
      }
    } catch (err) {
      console.warn("Could not fetch folders tree:", err);
    }
    setFolders(fallbackFolders);
  };

  useEffect(() => {
    fetchFoldersTree();
  }, [user]);

  const handleFileSelected = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setIsUploading(true);
    try {
      const formData = new FormData();
      formData.append("file", file);
      formData.append("course_id", "00000000-0000-0000-0000-000000000001");
      formData.append("user_id", user?.id || "00000000-0000-0000-0000-000000000001");

      const res = await fetch("http://localhost:8000/api/v1/syllabus/parse", {
        method: "POST",
        headers: {
          "X-Test-User-Id": user?.id || "00000000-0000-0000-0000-000000000001",
        },
        body: formData,
      });

      if (res.ok) {
        const data = await res.json();
        setStagedPreview({
          raw_data: data,
          course_code: data.syllabus?.course_code || "CS101",
          course_name: data.syllabus?.course_name || "Course Syllabus",
          confidence: data.syllabus?.confidence_score || 0.88,
          parser: data.syllabus?.parser_used || "Docling & Gemini Vision",
          extracted_modules: data.suggested_folders?.map((f: any) => f.name) || [],
          extracted_events: data.suggested_events || [],
        });
      }
    } catch (err) {
      console.error("Syllabus parsing failed:", err);
    } finally {
      setIsUploading(false);
    }
  };

  const handleCommitSyllabus = async () => {
    if (!stagedPreview || !stagedPreview.raw_data) return;
    try {
      await fetch("http://localhost:8000/api/v1/syllabus/commit?course_id=00000000-0000-0000-0000-000000000001", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-Test-User-Id": user?.id || "00000000-0000-0000-0000-000000000001",
        },
        body: JSON.stringify(stagedPreview.raw_data),
      });
      setStagedPreview(null);
      fetchFoldersTree();
    } catch (err) {
      console.error("Commit syllabus error:", err);
      setStagedPreview(null);
    }
  };

  return (
    <div className="min-h-screen flex flex-col bg-[#f8f9fb]">
      <Navbar />

      <main className="flex-1 max-w-7xl w-full mx-auto px-6 py-8 space-y-8">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4">
          <div>
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-brand-tertiary-container border border-brand-tertiary/40 text-xs font-bold text-brand-on-tertiary-container mb-2">
              <FolderTree className="w-3.5 h-3.5 text-brand-secondary" />
              <span>Hierarchical Resource Architecture</span>
            </div>
            <h1 className="text-4xl font-black text-brand-secondary tracking-tight">Virtual Folder Manager</h1>
            <p className="text-brand-on-surface-variant text-sm mt-1">
              Materialized course folders bound to academic weeks. RAG vector queries are strictly partitioned to eliminate cross-module context contamination.
            </p>
          </div>
        </div>

        {/* 2-Column Explorer */}
        <div className="grid grid-cols-1 md:grid-cols-12 gap-8">
          {/* Left Column: Interactive Folder Hierarchy Tree */}
          <div className="md:col-span-5 bg-white border border-brand-outline-variant rounded-[32px] p-6 shadow-elevation-md space-y-4">
            <div className="flex items-center justify-between border-b border-brand-outline-variant pb-3">
              <span className="text-xs font-bold uppercase tracking-wider text-brand-on-surface-variant">
                Course Virtual Folder Tree
              </span>
              <span className="text-xs font-mono text-brand-primary font-bold">
                {folders.length} Registered Courses
              </span>
            </div>

            <div className="space-y-3">
              {folders.map((course) => (
                <div key={course.id} className="space-y-1.5">
                  <div className="flex items-center justify-between p-2 rounded-xl bg-brand-surface-dim border border-brand-outline-variant font-bold text-xs text-brand-secondary">
                    <div className="flex items-center gap-2">
                      <Folder className="w-4 h-4 text-brand-primary" />
                      <span>{course.name}</span>
                    </div>
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-white border border-brand-outline-variant text-brand-on-surface-variant">
                      {course.children?.length || 0} modules
                    </span>
                  </div>

                  {/* Subfolders */}
                  <div className="pl-4 space-y-1 border-l-2 border-brand-outline-variant/60 ml-3">
                    {course.children?.map((sub) => {
                      const isSelected = selectedFolder === sub.materialized_path;
                      return (
                        <button
                          key={sub.id}
                          onClick={() => setSelectedFolder(sub.materialized_path)}
                          className={`w-full flex items-center justify-between p-2 rounded-xl text-xs font-mono transition-all text-left ${
                            isSelected
                              ? "bg-brand-primary text-white font-bold shadow-sm"
                              : "text-brand-on-surface-variant hover:bg-brand-surface-dim hover:text-brand-secondary"
                          }`}
                        >
                          <div className="flex items-center gap-2 truncate">
                            <ChevronRight className={`w-3 h-3 ${isSelected ? "text-white" : "text-brand-on-surface-variant"}`} />
                            <span className="truncate">{sub.name.replace(/_/g, " ")}</span>
                          </div>
                          <span className={`text-[10px] px-1.5 py-0.5 rounded ${isSelected ? "bg-white/20 text-white" : "bg-brand-surface-dim text-brand-on-surface-variant"}`}>
                            {sub.document_count || 1} docs
                          </span>
                        </button>
                      );
                    })}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Right Column: Selected Folder Inspector & Syllabus Ingestion */}
          <div className="md:col-span-7 space-y-6">
            {/* Active Folder Inspector Card */}
            <div className="bg-white border border-brand-outline-variant rounded-[32px] p-6 shadow-elevation-md space-y-4">
              <div className="flex items-center justify-between border-b border-brand-outline-variant pb-3">
                <div>
                  <span className="text-xs text-brand-on-surface-variant font-mono">Active Partition Scope</span>
                  <h3 className="text-xl font-black text-brand-secondary">{selectedFolder}</h3>
                </div>
                <Link
                  href={`/study?folder=${encodeURIComponent(selectedFolder)}&topic=${encodeURIComponent(selectedFolder.split("/").pop() || "Recursion")}`}
                  className="px-4 py-2 rounded-xl bg-brand-primary hover:bg-brand-primary/90 text-white text-xs font-bold transition-all shadow-sm flex items-center gap-1.5"
                >
                  <Sparkles className="w-3.5 h-3.5" />
                  <span>Synthesize Grounded Artifact</span>
                </Link>
              </div>

              <div className="text-xs text-brand-on-surface-variant space-y-2">
                <p>
                  Documents placed in this virtual folder are automatically chunked into 500-token blocks with 1536-dimensional HNSW indexed vectors.
                </p>
                <div className="p-3 rounded-2xl bg-brand-surface-dim border border-brand-outline-variant font-mono text-[11px]">
                  match_folder_chunks(query_embedding, query_text, p_folder_id, p_user_id)
                </div>
              </div>
            </div>

            {/* Syllabus Ingestion Dropzone */}
            <div className="bg-white border-2 border-dashed border-brand-outline-variant hover:border-brand-primary/50 shadow-elevation-sm transition-colors rounded-[32px] p-8 text-center relative">
              <input
                type="file"
                ref={fileInputRef}
                onChange={handleFileSelected}
                accept=".pdf,.txt"
                className="hidden"
              />
              <div className="max-w-md mx-auto space-y-3">
                <div className="w-12 h-12 rounded-[16px] bg-brand-primary/10 border border-brand-primary/20 flex items-center justify-center text-brand-primary mx-auto">
                  <UploadCloud className="w-6 h-6" />
                </div>
                <h3 className="text-lg font-black text-brand-secondary">Ingest Course Syllabus PDF</h3>
                <p className="text-xs text-brand-on-surface-variant leading-relaxed">
                  Upload your course syllabus PDF. IBM Docling TableFormer and Gemini 3 Flash structured vision will extract weekly modules, exam schedules, and grading weights to auto-create virtual folders.
                </p>

                <button
                  onClick={() => fileInputRef.current?.click()}
                  disabled={isUploading}
                  className="px-6 py-2.5 rounded-full bg-brand-secondary hover:bg-brand-secondary-container text-white text-xs font-bold transition-all shadow-sm disabled:opacity-50"
                >
                  {isUploading ? "Parsing Syllabus with Docling & Gemini..." : "Select Syllabus PDF File"}
                </button>
              </div>
            </div>

            {/* Staged Syllabus Preview Modal */}
            {stagedPreview && (
              <div className="bg-emerald-50/90 border border-emerald-300 shadow-elevation-md rounded-[32px] p-6 space-y-4 animate-fadeIn">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-emerald-200 pb-3">
                  <div className="flex items-center gap-2">
                    <CheckCircle2 className="w-5 h-5 text-emerald-600 flex-shrink-0" />
                    <div>
                      <h4 className="text-base font-black text-emerald-950">Syllabus Parsed Successfully</h4>
                      <p className="text-xs text-emerald-800">
                        {stagedPreview.course_code} ({stagedPreview.parser}, Confidence {(stagedPreview.confidence * 100).toFixed(0)}%)
                      </p>
                    </div>
                  </div>
                  <button
                    onClick={handleCommitSyllabus}
                    className="px-5 py-2 rounded-full bg-brand-secondary hover:bg-brand-secondary-container text-white font-bold text-xs shadow-sm transition-all"
                  >
                    Confirm & Materialize Folders
                  </button>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
                  <div>
                    <span className="font-bold text-emerald-950 block mb-2">Generated Virtual Folders:</span>
                    <ul className="space-y-1 font-mono text-emerald-900">
                      {stagedPreview.extracted_modules.map((m: string, i: number) => (
                        <li key={i} className="flex items-center gap-1.5 truncate">
                          <Folder className="w-3.5 h-3.5 text-brand-primary" />
                          <span>/{stagedPreview.course_code}/{m}</span>
                        </li>
                      ))}
                    </ul>
                  </div>

                  <div>
                    <span className="font-bold text-emerald-950 block mb-2">Detected Deadlines & Exams:</span>
                    <ul className="space-y-1 text-emerald-950">
                      {stagedPreview.extracted_events.map((e: any, i: number) => (
                        <li key={i} className="flex items-center justify-between p-2 rounded-xl bg-white border border-emerald-200">
                          <span className="font-medium">{e.title}</span>
                          <span className="font-mono font-bold text-amber-700">weight: {e.weight || 1.0}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
