# Subagent Orchestrator Review: Virtual Folder Document Reader

**Target Feature**: Document Reader Pop-Up (PDF & Text Viewer) for Virtual Folders (`/folders`)
**Date**: 2026-09-06

---

## 1. Marty Cagan (`pm_orchestrator`) – Product Discovery & Value
- **Core Value**: Students uploading course slides, notes, and syllabus PDFs currently have no direct preview without jumping into the full AI study flow. A zero-friction reader pop-up allows instantaneous reading and reference directly inside their folder structure.
- **Outcome**: Drastically lowers cognitive friction; empowers students to inspect documents before triggering computationally intensive AI synthesis.

---

## 2. Don Norman (`ux_designer_specialist`) – Cognitive Load & Affordances
- **Affordances & Signifiers**:
  - Make both the document row/title and an explicit `<BookOpen />` **"Read"** action clickable. Clicking the file name must feel natural with hover highlighting.
  - Esc key, backdrop click, and explicit close (X) button must all immediately dismiss the reader.
  - Clear tabs between **Reader Mode** (distraction-free typography with font-scale controls) and **PDF / Original Mode** (native browser PDF engine).
  - Search bar inside the reader with highlighted occurrences and match counters.

---

## 3. Troy Hunt (`security_architect_specialist`) – Pragmatic Security & OWASP
- **Access Control & IDOR Prevention**:
  - `GET /documents/{document_id}/content` and `/documents/{document_id}/raw` must strictly enforce user ownership (`eq("user_id", str(current_user))`).
  - File streaming headers must sanitize the filename in `Content-Disposition` to prevent header injection.
  - Signed URLs generated for Supabase storage must be time-limited (1 hour max).

---

## 4. Addy Osmani & Dan Abramov (`frontend_architect_specialist`) – Architecture & Performance
- **Bundle & State Architecture**:
  - Zero bloated external PDF parser libraries in the frontend bundle. Utilize native browser PDF streaming in an `iframe` with fallback text reader.
  - Reader state should remain cleanly encapsulated in `DocumentReaderModal.tsx`.
  - Virtual folder list in `/folders/page.tsx` simply passes the selected document item to open the modal.

---

## 5. James Bach (`qa_edgecase_specialist`) – Boundary Conditions & Stress Cases
- **Key Failure Modes to Guard**:
  1. **Storage Offline / Unsynced**: If Supabase storage is unreachable, fallback cleanly to concatenated `document_chunks` so the student can still read the entire text!
  2. **Zero or Missing Chunks**: Display graceful empty state message instead of crashing.
  3. **Large Files**: Support documents with 50+ chunks without pagination truncation (fetch all chunks with high limit).
  4. **Filename Escaping**: Unicode, spaces, and punctuation in filenames must not break links or headers.

---

## 6. Linus Torvalds / John Carmack (`ultimate_judge`) – Technical Score & Directive
- **Verdict**: 94/100.
- **Directive**: "Cut the fluff. Don't pull in a 5MB PDF.js bundle when modern browsers already have hardware-accelerated PDF engines built into `iframe`. Combine that with a clean, fast markdown/text reader powered by existing vector chunks. Implement test-first: red test for the backend content and streaming endpoints, red test for frontend reader parsing, make them green."
