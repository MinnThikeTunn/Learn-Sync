"use client";

import { useState, useEffect, useRef } from "react";
import { 
  FolderTree, 
  Folder, 
  FileText, 
  UploadCloud, 
  CheckCircle2, 
  ChevronRight, 
  Sparkles,
  Layers,
  Plus,
  BookOpen,
  Clock,
  X,
  FileCheck,
  AlertCircle,
  Trash2,
  BrainCircuit
} from "lucide-react";
import Link from "next/link";
import Navbar from "@/components/Navbar";
import OnboardingModal from "@/components/OnboardingModal";
import { useAuth } from "@/context/AuthContext";
import { getVisibleCourseFolders, formatFolderDisplayName } from "@/lib/virtualFolders";

interface CourseItem {
  id: string;
  name: string;
  code: string;
  term?: string;
  color?: string;
  description?: string;
}

interface VirtualFolder {
  id: string;
  course_id: string;
  name: string;
  materialized_path: string;
  depth: number;
  parent_id?: string | null;
  document_count?: number;
}

interface DocumentItem {
  id: string;
  file_name: string;
  file_type: string;
  file_size_bytes: number;
  status: string;
  created_at: string;
}

export default function VirtualFoldersPage() {
  const { user, session } = useAuth();
  const [showOnboarding, setShowOnboarding] = useState(false);
  
  // Data States
  const [courses, setCourses] = useState<CourseItem[]>([]);
  const [folders, setFolders] = useState<VirtualFolder[]>([]);
  const [selectedCourse, setSelectedCourse] = useState<CourseItem | null>(null);
  const [selectedFolder, setSelectedFolder] = useState<VirtualFolder | null>(null);
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  // Upload States
  const [isUploadingDoc, setIsUploadingDoc] = useState(false);
  const [isUploadingSyllabus, setIsUploadingSyllabus] = useState(false);
  const [stagedPreview, setStagedPreview] = useState<any>(null);
  const [uploadMessage, setUploadMessage] = useState<{ text: string; type: "success" | "error" } | null>(null);

  // Modal States
  const [showCourseModal, setShowCourseModal] = useState(false);
  const [showFolderModal, setShowFolderModal] = useState(false);
  const [newCourseCode, setNewCourseCode] = useState("");
  const [newCourseName, setNewCourseName] = useState("");
  const [newCourseTerm, setNewCourseTerm] = useState("Fall 2026");
  const [newFolderName, setNewFolderName] = useState("");

  // Submitting & Error States
  const [isSubmittingCourse, setIsSubmittingCourse] = useState(false);
  const [courseError, setCourseError] = useState<string | null>(null);
  const [isSubmittingFolder, setIsSubmittingFolder] = useState(false);
  const [folderError, setFolderError] = useState<string | null>(null);

  // Delete States
  const [deletingCourseId, setDeletingCourseId] = useState<string | null>(null);
  const [deletingFolderId, setDeletingFolderId] = useState<string | null>(null);
  const [deletingDocId, setDeletingDocId] = useState<string | null>(null);

  const docInputRef = useRef<HTMLInputElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

  const apiFetch = async (endpoint: string, options: RequestInit = {}) => {
    try {
      return await fetch(`${API_URL}${endpoint}`, options);
    } catch (err: any) {
      console.warn(`Network error fetching ${endpoint}:`, err);
      return new Response(
        JSON.stringify({ detail: "Backend server is unreachable. Please make sure the LearnSync backend is running on port 8000." }),
        {
          status: 503,
          statusText: "Service Unavailable",
          headers: { "Content-Type": "application/json" },
        }
      );
    }
  };

  const getHeaders = () => {
    const headers: Record<string, string> = {};
    if (session?.access_token) {
      headers["Authorization"] = `Bearer ${session.access_token}`;
    }
    const uid = user?.id || "00000000-0000-0000-0000-000000000001";
    headers["X-Test-User-Id"] = uid;
    return headers;
  };

  // Fetch Courses and Folders
  const loadData = async () => {
    setIsLoading(true);
    try {
      const headers = getHeaders();
      
      // 1. Fetch Courses
      const resCourses = await apiFetch("/courses", { headers });
      let loadedCourses: CourseItem[] = [];
      if (resCourses.ok) {
        loadedCourses = await resCourses.json();
        setCourses(loadedCourses);
      }

      // 2. Fetch Virtual Folders Tree
      const resFolders = await apiFetch("/folders/tree", { headers });
      if (resFolders.ok) {
        const loadedFolders: VirtualFolder[] = await resFolders.json();
        setFolders(loadedFolders);

        // Auto-select first course and folder if not selected
        if (loadedCourses.length > 0) {
          const currentCourse = selectedCourse && loadedCourses.find(c => c.id === selectedCourse.id) 
            ? selectedCourse 
            : loadedCourses[0];
          setSelectedCourse(currentCourse);

          const courseFolders = getVisibleCourseFolders(loadedFolders, currentCourse.id);
          if (courseFolders.length > 0) {
            const currentFolder = selectedFolder && courseFolders.find(f => f.id === selectedFolder.id)
              ? selectedFolder
              : courseFolders[0];
            setSelectedFolder(currentFolder);
            loadDocuments(currentFolder.id);
          } else {
            setSelectedFolder(null);
            setDocuments([]);
          }
        }
      }
    } catch (err) {
      console.warn("Failed to load courses/folders:", err);
    } finally {
      setIsLoading(false);
    }
  };

  // Fetch Documents for Folder
  const loadDocuments = async (folderId: string) => {
    try {
      const headers = getHeaders();
      const res = await apiFetch(`/documents?folder_id=${folderId}`, { headers });
      if (res.ok) {
        const data = await res.json();
        setDocuments(data);
      }
    } catch (err) {
      console.warn("Failed to load documents:", err);
    }
  };

  useEffect(() => {
    loadData();
  }, [user]);

  // When folder selection changes
  const handleSelectFolder = (folder: VirtualFolder) => {
    setSelectedFolder(folder);
    loadDocuments(folder.id);
  };

  // When course selection changes
  const handleSelectCourse = (course: CourseItem) => {
    setSelectedCourse(course);
    const courseFolders = getVisibleCourseFolders(folders, course.id);
    if (courseFolders.length > 0) {
      const currentFolder = selectedFolder && courseFolders.find(f => f.id === selectedFolder.id)
        ? selectedFolder
        : courseFolders[0];
      setSelectedFolder(currentFolder);
      loadDocuments(currentFolder.id);
    } else {
      setSelectedFolder(null);
      setDocuments([]);
    }
  };

  // Create Course Handler
  const handleCreateCourse = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newCourseCode.trim() || !newCourseName.trim()) return;

    setIsSubmittingCourse(true);
    setCourseError(null);
    try {
      const res = await apiFetch("/courses", {
        method: "POST",
        headers: {
          ...getHeaders(),
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          code: newCourseCode.trim().toUpperCase(),
          name: newCourseName.trim(),
          term: newCourseTerm.trim(),
          color: "#3b82f6",
        }),
      });

      if (res.ok) {
        const newCourse = await res.json();
        setShowCourseModal(false);
        setNewCourseCode("");
        setNewCourseName("");
        await loadData();
        setSelectedCourse(newCourse);
      } else {
        const errData = await res.json().catch(() => ({}));
        setCourseError(errData.detail || `Server returned status ${res.status}. Please check backend logs.`);
      }
    } catch (err: any) {
      console.error("Create course error:", err);
      setCourseError(err.message || "Failed to connect to backend server.");
    } finally {
      setIsSubmittingCourse(false);
    }
  };

  // Create Subfolder Handler
  const handleCreateFolder = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedCourse || !newFolderName.trim()) return;

    setIsSubmittingFolder(true);
    setFolderError(null);
    try {
      const parentFolder = selectedFolder && selectedFolder.course_id === selectedCourse.id ? selectedFolder : null;
      const parentPath = parentFolder ? parentFolder.materialized_path : `/${selectedCourse.code}`;
      const parentDepth = parentFolder ? parentFolder.depth : 0;

      const res = await apiFetch("/folders", {
        method: "POST",
        headers: {
          ...getHeaders(),
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          course_id: selectedCourse.id,
          name: newFolderName.trim().replace(/\s+/g, "_"),
          parent_id: parentFolder?.id || null,
          parent_path: parentPath,
          parent_depth: parentDepth,
        }),
      });

      if (res.ok) {
        const created = await res.json();
        setShowFolderModal(false);
        setNewFolderName("");
        await loadData();
        setSelectedFolder(created);
      } else {
        const errData = await res.json().catch(() => ({}));
        setFolderError(errData.detail || `Server returned status ${res.status}.`);
      }
    } catch (err: any) {
      console.error("Create subfolder error:", err);
      setFolderError(err.message || "Failed to connect to backend server.");
    } finally {
      setIsSubmittingFolder(false);
    }
  };

  // Document Upload Handler
  const handleDocumentSelected = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file || !selectedCourse) return;

    setIsUploadingDoc(true);
    setUploadMessage(null);
    try {
      const formData = new FormData();
      formData.append("file", file);
      formData.append("course_id", selectedCourse.id);
      if (selectedFolder) {
        formData.append("folder_id", selectedFolder.id);
      }

      const res = await apiFetch("/documents/upload", {
        method: "POST",
        headers: getHeaders(),
        body: formData,
      });

      if (res.ok) {
        const uploadedDoc = await res.json();
        setUploadMessage({
          text: `"${uploadedDoc.file_name}" uploaded and indexed into ${uploadedDoc.chunks_created} vector chunks!`,
          type: "success",
        });
        if (selectedFolder) {
          loadDocuments(selectedFolder.id);
        }
      } else {
        setUploadMessage({ text: "Failed to upload document to Supabase storage.", type: "error" });
      }
    } catch (err) {
      console.error("Upload error:", err);
      setUploadMessage({ text: "An error occurred during document upload.", type: "error" });
    } finally {
      setIsUploadingDoc(false);
      if (docInputRef.current) docInputRef.current.value = "";
    }
  };

  // Syllabus Ingestion Handler
  const handleSyllabusSelected = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const targetCourseId = selectedCourse?.id || "00000000-0000-0000-0000-000000000001";
    setIsUploadingSyllabus(true);
    try {
      const formData = new FormData();
      formData.append("file", file);
      formData.append("course_id", targetCourseId);
      formData.append("user_id", user?.id || "00000000-0000-0000-0000-000000000001");

      const res = await apiFetch("/syllabus/parse", {
        method: "POST",
        headers: getHeaders(),
        body: formData,
      });

      if (res.ok) {
        const data = await res.json();
        setStagedPreview({
          raw_data: data,
          course_code: data.syllabus?.course_code || selectedCourse?.code || "CS101",
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
      setIsUploadingSyllabus(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  // Commit Syllabus Handler
  const handleCommitSyllabus = async () => {
    if (!stagedPreview || !stagedPreview.raw_data) return;
    const targetCourseId = selectedCourse?.id || "00000000-0000-0000-0000-000000000001";
    try {
      await apiFetch(`/syllabus/commit?course_id=${targetCourseId}`, {
        method: "POST",
        headers: {
          ...getHeaders(),
          "Content-Type": "application/json",
        },
        body: JSON.stringify(stagedPreview.raw_data),
      });
      setStagedPreview(null);
      await loadData();
    } catch (err) {
      console.error("Commit syllabus error:", err);
      setStagedPreview(null);
    }
  };

  // Delete Course Handler
  const handleDeleteCourse = async (course: CourseItem) => {
    if (!confirm(`Are you sure you want to delete course "${course.code} - ${course.name}" and ALL its folders and documents from Supabase? This cannot be undone.`)) return;
    setDeletingCourseId(course.id);
    try {
      const res = await apiFetch(`/courses/${course.id}`, {
        method: "DELETE",
        headers: getHeaders(),
      });
      if (res.ok) {
        if (selectedCourse?.id === course.id) {
          setSelectedCourse(null);
          setSelectedFolder(null);
          setDocuments([]);
        }
        await loadData();
      } else {
        const err = await res.json().catch(() => ({}));
        alert(err.detail || "Failed to delete course.");
      }
    } catch (err: any) {
      console.error("Delete course error:", err);
      alert(err.message || "Failed to connect to backend server.");
    } finally {
      setDeletingCourseId(null);
    }
  };

  // Delete Folder Handler
  const handleDeleteFolder = async (folder: VirtualFolder) => {
    if (!confirm(`Are you sure you want to delete folder "${folder.name.replace(/_/g, " ")}" and all documents inside? This cannot be undone.`)) return;
    setDeletingFolderId(folder.id);
    try {
      const res = await apiFetch(`/folders/${folder.id}`, {
        method: "DELETE",
        headers: getHeaders(),
      });
      if (res.ok) {
        if (selectedFolder?.id === folder.id) {
          setSelectedFolder(null);
          setDocuments([]);
        }
        await loadData();
      } else {
        const err = await res.json().catch(() => ({}));
        alert(err.detail || "Failed to delete folder.");
      }
    } catch (err: any) {
      console.error("Delete folder error:", err);
      alert(err.message || "Failed to connect to backend server.");
    } finally {
      setDeletingFolderId(null);
    }
  };

  // Delete Document Handler
  const handleDeleteDocument = async (doc: DocumentItem) => {
    if (!confirm(`Are you sure you want to delete "${doc.file_name}" from Supabase? This will delete the file from storage and remove vector chunks.`)) return;
    setDeletingDocId(doc.id);
    try {
      const res = await apiFetch(`/documents/${doc.id}`, {
        method: "DELETE",
        headers: getHeaders(),
      });
      if (res.ok) {
        if (selectedFolder) {
          loadDocuments(selectedFolder.id);
        }
        setUploadMessage({ text: `"${doc.file_name}" deleted from Supabase storage and database.`, type: "success" });
      } else {
        const err = await res.json().catch(() => ({}));
        alert(err.detail || "Failed to delete document.");
      }
    } catch (err: any) {
      console.error("Delete document error:", err);
      alert(err.message || "Failed to connect to backend server.");
    } finally {
      setDeletingDocId(null);
    }
  };

  const activePath = selectedFolder?.materialized_path || (selectedCourse ? `/${selectedCourse.code}` : "/No Course Selected");
  const activeTopic = selectedFolder?.name ? selectedFolder.name.replace(/_/g, " ") : "Overview";

  return (
    <div className="min-h-screen flex flex-col bg-[#f8f9fb]">
      <Navbar onOpenOnboardingModal={() => setShowOnboarding(true)} />

      <main className="flex-1 max-w-7xl w-full mx-auto px-6 py-8 space-y-8">
        {/* Header with Actions */}
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

          <div className="flex items-center gap-3">
            <button
              onClick={() => setShowCourseModal(true)}
              className="px-4 py-2.5 rounded-full bg-brand-secondary hover:bg-brand-secondary-container text-white text-xs font-bold transition-all shadow-sm flex items-center gap-1.5"
            >
              <Plus className="w-4 h-4" />
              <span>Add Course</span>
            </button>
            {selectedCourse && (
              <button
                onClick={() => setShowFolderModal(true)}
                className="px-4 py-2.5 rounded-full bg-white border border-brand-outline-variant hover:bg-brand-surface-dim text-brand-secondary text-xs font-bold transition-all shadow-sm flex items-center gap-1.5"
              >
                <Folder className="w-4 h-4 text-brand-primary" />
                <span>Add Subfolder</span>
              </button>
            )}
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
                {courses.length} Courses
              </span>
            </div>

            {/* Empty State */}
            {courses.length === 0 && !isLoading && (
              <div className="py-12 px-4 text-center space-y-3">
                <div className="w-12 h-12 rounded-[16px] bg-brand-surface-dim border border-brand-outline-variant flex items-center justify-center text-brand-on-surface-variant mx-auto">
                  <BookOpen className="w-6 h-6" />
                </div>
                <h4 className="text-sm font-bold text-brand-secondary">No Courses Yet</h4>
                <p className="text-xs text-brand-on-surface-variant max-w-xs mx-auto">
                  Create your first course container or ingest a course syllabus to automatically populate folders and deadlines.
                </p>
                <button
                  onClick={() => setShowCourseModal(true)}
                  className="px-4 py-2 rounded-full bg-brand-primary text-white text-xs font-bold hover:bg-brand-primary/90 transition-all shadow-sm inline-flex items-center gap-1.5"
                >
                  <Plus className="w-3.5 h-3.5" />
                  <span>Create Course</span>
                </button>
              </div>
            )}

            {/* Course & Subfolders List */}
            <div className="space-y-4">
              {courses.map((course) => {
                const isCurrentCourse = selectedCourse?.id === course.id;
                const courseFolders = getVisibleCourseFolders(folders, course.id);

                return (
                  <div 
                    key={course.id} 
                    className={`p-3 rounded-2xl border transition-all ${
                      isCurrentCourse 
                        ? "bg-brand-surface-dim/40 border-brand-primary/40 shadow-sm" 
                        : "border-brand-outline-variant/60 hover:border-brand-outline-variant"
                    }`}
                  >
                    {/* Course Header */}
                    <div 
                      onClick={() => handleSelectCourse(course)}
                      className="flex items-center justify-between cursor-pointer group"
                    >
                      <div className="flex items-center gap-2.5">
                        <div 
                          className="w-3 h-3 rounded-full" 
                          style={{ backgroundColor: course.color || "#3b82f6" }} 
                        />
                        <span className="font-bold text-xs text-brand-secondary group-hover:text-brand-primary transition-colors">
                          {course.code}
                        </span>
                        <span className="text-xs text-brand-on-surface-variant truncate max-w-[160px]">
                          {course.name}
                        </span>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-white border border-brand-outline-variant text-brand-on-surface-variant">
                          {courseFolders.length} {courseFolders.length === 1 ? "folder" : "folders"}
                        </span>
                        <button
                          type="button"
                          onClick={(e) => {
                            e.stopPropagation();
                            handleDeleteCourse(course);
                          }}
                          disabled={deletingCourseId === course.id}
                          title={`Delete course ${course.code}`}
                          className="p-1 rounded-lg text-brand-on-surface-variant/50 hover:text-rose-600 hover:bg-rose-50 transition-colors"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </div>

                    {/* Subfolders Tree */}
                    {courseFolders.length > 0 && (
                      <div className="mt-2.5 pl-3.5 space-y-1 border-l-2 border-brand-outline-variant/70 ml-1.5">
                        {courseFolders.map((sub) => {
                          const isSelected = selectedFolder?.id === sub.id;
                          return (
                            <div
                              key={sub.id}
                              style={{ paddingLeft: sub.depth > 0 ? `${Math.min(sub.depth * 10, 30)}px` : undefined }}
                              className={`w-full flex items-center justify-between p-2 rounded-xl text-xs font-mono transition-all group ${
                                isSelected
                                  ? "bg-brand-primary text-white font-bold shadow-sm"
                                  : "text-brand-on-surface-variant hover:bg-white hover:text-brand-secondary"
                              }`}
                            >
                              <button
                                onClick={() => {
                                  setSelectedCourse(course);
                                  handleSelectFolder(sub);
                                }}
                                className="flex items-center gap-2 truncate flex-1 text-left"
                              >
                                <ChevronRight className={`w-3 h-3 flex-shrink-0 ${isSelected ? "text-white" : "text-brand-on-surface-variant"}`} />
                                <span className="truncate">{formatFolderDisplayName(sub, course.code)}</span>
                              </button>
                              <div className="flex items-center gap-1.5 flex-shrink-0">
                                <span className={`text-[10px] px-1.5 py-0.5 rounded ${isSelected ? "bg-white/20 text-white" : "bg-brand-surface-dim text-brand-on-surface-variant"}`}>
                                  /{sub.materialized_path.split("/").filter(Boolean).pop() || sub.name}
                                </span>
                                <button
                                  type="button"
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    handleDeleteFolder(sub);
                                  }}
                                  disabled={deletingFolderId === sub.id}
                                  title="Delete folder"
                                  className={`p-1 rounded-lg transition-colors ${
                                    isSelected
                                      ? "hover:bg-white/20 text-white/80 hover:text-white"
                                      : "text-brand-on-surface-variant/60 hover:text-rose-600 hover:bg-rose-50"
                                  }`}
                                >
                                  <Trash2 className="w-3.5 h-3.5" />
                                </button>
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>

          {/* Right Column: Selected Folder Inspector, Document Import & Storage */}
          <div className="md:col-span-7 space-y-6">
            {/* Active Folder Inspector Card */}
            <div className="bg-white border border-brand-outline-variant rounded-[32px] p-6 shadow-elevation-md space-y-5">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-brand-outline-variant pb-4">
                <div>
                  <span className="text-xs text-brand-on-surface-variant font-mono">Active Partition Scope</span>
                  <h3 className="text-xl font-black text-brand-secondary tracking-tight">{activePath}</h3>
                </div>
                <div className="flex items-center gap-2">
                  {selectedFolder && (
                    <button
                      onClick={() => handleDeleteFolder(selectedFolder)}
                      disabled={deletingFolderId === selectedFolder.id}
                      className="px-3 py-2 rounded-xl border border-rose-200 bg-rose-50 hover:bg-rose-100 text-rose-700 text-xs font-bold transition-all flex items-center gap-1.5"
                      title="Delete this folder"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                      <span>Delete Folder</span>
                    </button>
                  )}
                  {selectedFolder && (
                    <Link
                      href={`/study?folder=${encodeURIComponent(activePath)}&folder_id=${selectedFolder.id}${documents.length > 0 ? `&document_id=${documents[0].id}&file_name=${encodeURIComponent(documents[0].file_name)}` : ""}&topic=${encodeURIComponent(activeTopic)}`}
                      className="px-4 py-2 rounded-xl bg-brand-primary hover:bg-brand-primary/90 text-white text-xs font-bold transition-all shadow-sm flex items-center gap-1.5 cursor-pointer"
                    >
                      <Sparkles className="w-3.5 h-3.5" />
                      <span>Synthesize Grounded Artifact</span>
                    </Link>
                  )}
                </div>
              </div>

              {/* Upload Notification Message */}
              {uploadMessage && (
                <div className={`p-3 rounded-xl text-xs flex items-center gap-2 ${
                  uploadMessage.type === "success" 
                    ? "bg-emerald-50 text-emerald-800 border border-emerald-200" 
                    : "bg-rose-50 text-rose-800 border border-rose-200"
                }`}>
                  {uploadMessage.type === "success" ? <CheckCircle2 className="w-4 h-4 flex-shrink-0" /> : <AlertCircle className="w-4 h-4 flex-shrink-0" />}
                  <span>{uploadMessage.text}</span>
                </div>
              )}

              {/* Document List in Folder */}
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold uppercase tracking-wider text-brand-on-surface-variant">
                    Documents in Folder ({documents.length})
                  </span>
                  {selectedCourse && (
                    <button
                      onClick={() => docInputRef.current?.click()}
                      disabled={isUploadingDoc}
                      className="text-xs font-bold text-brand-primary hover:underline flex items-center gap-1"
                    >
                      <Plus className="w-3 h-3" />
                      <span>{isUploadingDoc ? "Indexing into Supabase..." : "Import Document"}</span>
                    </button>
                  )}
                </div>

                {/* Hidden Document Input */}
                <input
                  type="file"
                  ref={docInputRef}
                  onChange={handleDocumentSelected}
                  accept=".pdf,.txt,.md,.json"
                  className="hidden"
                />

                {documents.length === 0 ? (
                  <div className="p-6 rounded-2xl bg-brand-surface-dim/60 border border-brand-outline-variant text-center space-y-2">
                    <FileText className="w-6 h-6 text-brand-on-surface-variant mx-auto" />
                    <p className="text-xs text-brand-on-surface-variant">
                      No documents stored in this virtual folder yet.
                    </p>
                    {selectedCourse && (
                      <button
                        onClick={() => docInputRef.current?.click()}
                        disabled={isUploadingDoc}
                        className="px-4 py-1.5 rounded-full bg-brand-primary text-white text-xs font-bold hover:bg-brand-primary/90 transition-all shadow-sm inline-flex items-center gap-1"
                      >
                        <Plus className="w-3 h-3" />
                        <span>Upload PDF or Notes</span>
                      </button>
                    )}
                  </div>
                ) : (
                  <div className="space-y-2">
                    {documents.map((doc) => {
                      const docTopic = doc.file_name.replace(/\.[^/.]+$/, "").replace(/_/g, " ").replace(/-/g, " ");
                      return (
                        <div
                          key={doc.id}
                          className="p-3.5 rounded-2xl bg-white border border-brand-outline-variant hover:border-brand-primary/40 shadow-xs hover:shadow-sm transition-all flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs"
                        >
                          <div className="flex items-center gap-3 truncate min-w-0">
                            <div className="w-9 h-9 rounded-xl bg-brand-surface-dim border border-brand-outline-variant flex items-center justify-center flex-shrink-0">
                              <FileCheck className="w-4 h-4 text-brand-primary" />
                            </div>
                            <div className="truncate">
                              <h5 className="font-bold text-brand-secondary truncate text-xs">{doc.file_name}</h5>
                              <span className="text-[11px] text-brand-on-surface-variant font-mono">
                                {(doc.file_size_bytes / 1024).toFixed(1)} KB • {doc.file_type.split("/").pop()}
                              </span>
                            </div>
                          </div>

                          <div className="flex items-center gap-2 flex-shrink-0 self-end sm:self-center">
                            <span className={`px-2 py-0.5 rounded-full text-[10px] font-mono font-bold ${
                              doc.status === "indexed" 
                                ? "bg-emerald-100 text-emerald-800" 
                                : "bg-amber-100 text-amber-800"
                            }`}>
                              {doc.status}
                            </span>

                            <Link
                              href={`/study?document_id=${doc.id}&file_name=${encodeURIComponent(doc.file_name)}&folder_id=${selectedFolder?.id || ""}&folder=${encodeURIComponent(activePath)}&topic=${encodeURIComponent(docTopic)}`}
                              className="px-3 py-1.5 rounded-xl bg-brand-primary hover:bg-brand-primary/90 text-white font-bold text-[11px] transition-all flex items-center gap-1 shadow-xs cursor-pointer"
                              title={`Study and synthesize ${doc.file_name}`}
                            >
                              <Sparkles className="w-3 h-3" />
                              <span>Study</span>
                            </Link>

                            <Link
                              href={`/review?document_id=${doc.id}&file_name=${encodeURIComponent(doc.file_name)}&folder_id=${selectedFolder?.id || ""}&topic=${encodeURIComponent(docTopic)}`}
                              className="px-3 py-1.5 rounded-xl bg-purple-50 text-purple-700 hover:bg-purple-100 border border-purple-200 font-bold text-[11px] transition-all flex items-center gap-1 shadow-xs cursor-pointer"
                              title={`Review flashcard deck for ${doc.file_name}`}
                            >
                              <BrainCircuit className="w-3 h-3 text-[#3a10e5]" />
                              <span>Review</span>
                            </Link>

                            <button
                              type="button"
                              onClick={() => handleDeleteDocument(doc)}
                              disabled={deletingDocId === doc.id}
                              title="Delete document from Supabase"
                              className="p-1.5 rounded-lg text-brand-on-surface-variant hover:text-rose-600 hover:bg-rose-50 transition-colors"
                            >
                              <Trash2 className="w-3.5 h-3.5" />
                            </button>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>

              {/* RRF Scope Formula */}
              <div className="p-3 rounded-2xl bg-brand-surface-dim border border-brand-outline-variant font-mono text-[11px] text-brand-on-surface-variant flex items-center justify-between">
                <span>Partition Scope:</span>
                <span className="text-brand-primary font-bold">match_folder_chunks({selectedFolder?.id ? `'${selectedFolder.id}'` : "null"})</span>
              </div>
            </div>

            {/* Syllabus Ingestion Dropzone */}
            <div className="bg-white border-2 border-dashed border-brand-outline-variant hover:border-brand-primary/50 shadow-elevation-sm transition-colors rounded-[32px] p-8 text-center relative">
              <input
                type="file"
                ref={fileInputRef}
                onChange={handleSyllabusSelected}
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
                  disabled={isUploadingSyllabus}
                  className="px-6 py-2.5 rounded-full bg-brand-secondary hover:bg-brand-secondary-container text-white text-xs font-bold transition-all shadow-sm disabled:opacity-50"
                >
                  {isUploadingSyllabus ? "Parsing Syllabus with Docling & Gemini..." : "Select Syllabus PDF File"}
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

      {/* Modal: Create Course */}
      {showCourseModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4 animate-fadeIn">
          <div className="bg-white rounded-[32px] border border-brand-outline-variant shadow-elevation-lg max-w-md w-full p-6 space-y-5">
            <div className="flex items-center justify-between border-b border-brand-outline-variant pb-3">
              <div className="flex items-center gap-2">
                <BookOpen className="w-5 h-5 text-brand-primary" />
                <h3 className="text-lg font-black text-brand-secondary">Create Academic Course</h3>
              </div>
              <button 
                onClick={() => setShowCourseModal(false)}
                className="p-1.5 rounded-full hover:bg-brand-surface-dim text-brand-on-surface-variant"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleCreateCourse} className="space-y-4 text-xs">
              <div className="space-y-1.5">
                <label className="font-bold text-brand-secondary block">Course Code (e.g., CS101, CS301)</label>
                <input
                  type="text"
                  required
                  placeholder="CS101"
                  value={newCourseCode}
                  onChange={(e) => setNewCourseCode(e.target.value)}
                  className="w-full px-3.5 py-2.5 rounded-xl border border-brand-outline-variant bg-brand-surface-dim font-mono focus:outline-none focus:ring-2 focus:ring-brand-primary/20"
                />
              </div>

              <div className="space-y-1.5">
                <label className="font-bold text-brand-secondary block">Course Name</label>
                <input
                  type="text"
                  required
                  placeholder="Introductory Computer Science"
                  value={newCourseName}
                  onChange={(e) => setNewCourseName(e.target.value)}
                  className="w-full px-3.5 py-2.5 rounded-xl border border-brand-outline-variant bg-brand-surface-dim focus:outline-none focus:ring-2 focus:ring-brand-primary/20"
                />
              </div>

              <div className="space-y-1.5">
                <label className="font-bold text-brand-secondary block">Academic Term</label>
                <input
                  type="text"
                  placeholder="Fall 2026"
                  value={newCourseTerm}
                  onChange={(e) => setNewCourseTerm(e.target.value)}
                  className="w-full px-3.5 py-2.5 rounded-xl border border-brand-outline-variant bg-brand-surface-dim focus:outline-none focus:ring-2 focus:ring-brand-primary/20"
                />
              </div>

              {courseError && (
                <div className="p-3 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-center gap-2">
                  <AlertCircle className="w-4 h-4 flex-shrink-0" />
                  <span>{courseError}</span>
                </div>
              )}

              <div className="flex items-center justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowCourseModal(false)}
                  className="px-4 py-2 rounded-xl text-brand-on-surface-variant hover:bg-brand-surface-dim font-bold transition-all"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmittingCourse}
                  className="px-5 py-2 rounded-xl bg-brand-primary hover:bg-brand-primary/90 text-white font-bold transition-all shadow-sm disabled:opacity-50 flex items-center gap-2"
                >
                  {isSubmittingCourse ? "Creating Course..." : "Create Course"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal: Create Subfolder */}
      {showFolderModal && selectedCourse && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4 animate-fadeIn">
          <div className="bg-white rounded-[32px] border border-brand-outline-variant shadow-elevation-lg max-w-md w-full p-6 space-y-5">
            <div className="flex items-center justify-between border-b border-brand-outline-variant pb-3">
              <div className="flex items-center gap-2">
                <Folder className="w-5 h-5 text-brand-primary" />
                <h3 className="text-lg font-black text-brand-secondary">Add Subfolder to {selectedCourse.code}</h3>
              </div>
              <button 
                onClick={() => setShowFolderModal(false)}
                className="p-1.5 rounded-full hover:bg-brand-surface-dim text-brand-on-surface-variant"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleCreateFolder} className="space-y-4 text-xs">
              <div className="space-y-1.5">
                <label className="font-bold text-brand-secondary block">Subfolder Name (e.g. Week_01_Recursion, Module_02)</label>
                <input
                  type="text"
                  required
                  placeholder="Week_01_Foundations"
                  value={newFolderName}
                  onChange={(e) => setNewFolderName(e.target.value)}
                  className="w-full px-3.5 py-2.5 rounded-xl border border-brand-outline-variant bg-brand-surface-dim font-mono focus:outline-none focus:ring-2 focus:ring-brand-primary/20"
                />
              </div>

              <p className="text-[11px] text-brand-on-surface-variant font-mono">
                Materialized Path: /{selectedCourse.code}/{newFolderName.trim().replace(/\s+/g, "_") || "..."}
              </p>

              {folderError && (
                <div className="p-3 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-center gap-2">
                  <AlertCircle className="w-4 h-4 flex-shrink-0" />
                  <span>{folderError}</span>
                </div>
              )}

              <div className="flex items-center justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowFolderModal(false)}
                  className="px-4 py-2 rounded-xl text-brand-on-surface-variant hover:bg-brand-surface-dim font-bold transition-all"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmittingFolder}
                  className="px-5 py-2 rounded-xl bg-brand-primary hover:bg-brand-primary/90 text-white font-bold transition-all shadow-sm disabled:opacity-50 flex items-center gap-2"
                >
                  {isSubmittingFolder ? "Creating Folder..." : "Create Folder"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      <OnboardingModal
        isOpen={showOnboarding}
        onSave={() => setShowOnboarding(false)}
      />
    </div>
  );
}
