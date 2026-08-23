"use client";

import { useState } from "react";
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
  ArrowRight
} from "lucide-react";
import Link from "next/link";
import Navbar from "@/components/Navbar";

interface FolderItem {
  id: string;
  name: string;
  materialized_path: string;
  depth: number;
  course_code: string;
  document_count: number;
  children?: FolderItem[];
}

export default function VirtualFoldersPage() {
  const [selectedFolder, setSelectedFolder] = useState<string>("/CS101/Week_03_Recursion");
  const [isUploading, setIsUploading] = useState(false);
  const [stagedPreview, setStagedPreview] = useState<any>(null);

  const sampleFolders: FolderItem[] = [
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
        {
          id: "cs101-w4",
          name: "Week_04_Trees_and_Call_Stack",
          materialized_path: "/CS101/Week_04_Trees_and_Call_Stack",
          depth: 1,
          course_code: "CS101",
          document_count: 2,
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

  const handleSimulateSyllabusUpload = () => {
    setIsUploading(true);
    setTimeout(() => {
      setIsUploading(false);
      setStagedPreview({
        course_code: "MATH204",
        course_name: "Linear Algebra & Vector Spaces",
        confidence: 0.94,
        parser: "IBM Docling TableFormer",
        extracted_modules: [
          "Week_01_Matrices_and_Gaussian_Elimination",
          "Week_02_Vector_Spaces_and_Subspaces",
          "Week_03_Linear_Independence_and_Bases",
          "Week_04_Eigenvalues_and_Diagonalization",
        ],
        extracted_events: [
          { title: "Midterm Examination", date: "Oct 20, 2026", weight: "3.0x" },
          { title: "Homework 1", date: "Sep 28, 2026", weight: "1.5x" },
        ],
      });
    }, 1500);
  };

  return (
    <div className="min-h-screen flex flex-col bg-obsidian-950">
      <Navbar />

      <main className="flex-1 max-w-7xl w-full mx-auto px-6 py-8 space-y-8">
        <div>
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-slate-900 border border-slate-800 text-xs font-semibold text-accent-cyan mb-2">
            <FolderTree className="w-3.5 h-3.5" />
            <span>Virtual Folder Resource Manager</span>
          </div>
          <h1 className="text-4xl font-black text-white tracking-tight">Virtual Folder Hierarchy</h1>
          <p className="text-slate-400 text-sm mt-1">
            Course materials are organized into materialized folder paths that scope hybrid RRF vector retrieval.
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Left: Materialized Folder Tree */}
          <div className="glass-card p-6 lg:col-span-1 space-y-4">
            <h3 className="text-base font-black text-white uppercase tracking-wider text-xs text-slate-400">Course Tree</h3>

            <div className="space-y-3">
              {sampleFolders.map((courseFolder) => (
                <div key={courseFolder.id} className="space-y-1">
                  <div 
                    onClick={() => setSelectedFolder(courseFolder.materialized_path)}
                    className={`flex items-center justify-between p-2.5 rounded-[16px] cursor-pointer transition-colors ${
                      selectedFolder === courseFolder.materialized_path ? "bg-slate-800 text-white font-bold" : "text-slate-300 hover:bg-slate-900"
                    }`}
                  >
                    <div className="flex items-center gap-2">
                      <Folder className="w-4 h-4 text-accent-cyan" />
                      <span className="text-sm font-black">{courseFolder.name}</span>
                    </div>
                    <span className="text-xs font-mono text-slate-500">{courseFolder.document_count} files</span>
                  </div>

                  <div className="pl-5 space-y-1 border-l border-slate-800 ml-3">
                    {courseFolder.children?.map((child) => (
                      <div
                        key={child.id}
                        onClick={() => setSelectedFolder(child.materialized_path)}
                        className={`flex items-center justify-between p-2 rounded-[14px] cursor-pointer text-xs transition-colors ${
                          selectedFolder === child.materialized_path
                            ? "bg-accent-cyan/10 border border-accent-cyan/30 text-accent-cyan font-bold"
                            : "text-slate-400 hover:text-slate-200 hover:bg-slate-900/60"
                        }`}
                      >
                        <span className="truncate max-w-[200px]">{child.name.replace(/_/g, " ")}</span>
                        <ChevronRight className="w-3.5 h-3.5 opacity-60 flex-shrink-0" />
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Center & Right: Folder Contents & Syllabus PDF Ingestion */}
          <div className="lg:col-span-2 space-y-6">
            {/* Active Folder Header Card */}
            <div className="glass-card p-6 flex items-center justify-between">
              <div>
                <span className="text-xs font-bold uppercase tracking-wider text-slate-400">Active Materialized Scope</span>
                <h2 className="text-2xl font-black text-white font-mono mt-0.5">{selectedFolder}</h2>
              </div>
              <Link
                href={`/study?folder=${encodeURIComponent(selectedFolder)}&topic=${encodeURIComponent(selectedFolder.split("/").pop() || "Topic")}`}
                className="px-4 py-2 rounded-full bg-accent-cyan text-obsidian-950 font-bold text-xs hover:brightness-110 shadow-md shadow-cyan-500/20 flex items-center gap-1.5 transition-all"
              >
                <Sparkles className="w-3.5 h-3.5" />
                <span>Synthesize Artifacts</span>
              </Link>
            </div>

            {/* Docling Syllabus PDF Uploader Dropzone */}
            <div className="glass-card p-8 border-2 border-dashed border-slate-800 hover:border-slate-700 transition-colors text-center relative">
              <div className="max-w-md mx-auto space-y-3">
                <div className="w-12 h-12 rounded-[18px] bg-accent-cyan/10 border border-accent-cyan/20 flex items-center justify-center text-accent-cyan mx-auto">
                  <UploadCloud className="w-6 h-6" />
                </div>
                <h3 className="text-lg font-black text-white">Ingest Course Syllabus PDF</h3>
                <p className="text-xs text-slate-400 leading-relaxed">
                  Upload your syllabus PDF. IBM Docling TableFormer will extract weekly modules, exam schedules, and grading weights to auto-create virtual folders.
                </p>

                <button
                  onClick={handleSimulateSyllabusUpload}
                  disabled={isUploading}
                  className="px-6 py-2.5 rounded-full bg-slate-900 hover:bg-slate-800 border border-slate-700 text-slate-200 text-xs font-bold transition-all"
                >
                  {isUploading ? "Docling Parsing Syllabus..." : "Select Syllabus PDF File"}
                </button>
              </div>
            </div>

            {/* Staged Syllabus Preview (Appears after parsing) */}
            {stagedPreview && (
              <div className="glass-card p-6 border border-emerald-500/30 bg-emerald-950/10 space-y-4 animate-in fade-in duration-300">
                <div className="flex items-center justify-between border-b border-slate-800/80 pb-3">
                  <div className="flex items-center gap-2">
                    <CheckCircle2 className="w-5 h-5 text-emerald-400" />
                    <div>
                      <h4 className="text-base font-black text-white">Syllabus Parsed Successfully</h4>
                      <p className="text-xs text-slate-400">
                        {stagedPreview.course_code} - {stagedPreview.course_name} ({stagedPreview.parser}, Confidence {(stagedPreview.confidence * 100).toFixed(0)}%)
                      </p>
                    </div>
                  </div>
                  <button
                    onClick={() => setStagedPreview(null)}
                    className="px-4 py-1.5 rounded-full bg-emerald-500 text-obsidian-950 font-bold text-xs hover:brightness-110"
                  >
                    Confirm & Materialize Folders
                  </button>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
                  <div>
                    <span className="font-bold text-slate-300 block mb-2">Generated Virtual Folders:</span>
                    <ul className="space-y-1 font-mono text-slate-400">
                      {stagedPreview.extracted_modules.map((m: string, i: number) => (
                        <li key={i} className="flex items-center gap-1.5 truncate">
                          <Folder className="w-3.5 h-3.5 text-accent-cyan" />
                          <span>/{stagedPreview.course_code}/{m}</span>
                        </li>
                      ))}
                    </ul>
                  </div>

                  <div>
                    <span className="font-bold text-slate-300 block mb-2">Detected Deadlines & Exams:</span>
                    <ul className="space-y-1 text-slate-300">
                      {stagedPreview.extracted_events.map((e: any, i: number) => (
                        <li key={i} className="flex items-center justify-between p-1.5 rounded bg-slate-900/60 border border-slate-800">
                          <span>{e.title}</span>
                          <span className="font-mono text-amber-400">{e.date}</span>
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
