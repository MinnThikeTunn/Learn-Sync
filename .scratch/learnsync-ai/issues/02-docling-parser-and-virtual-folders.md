# 02: Docling Syllabus Parser & Virtual Folder Ingestion Pipeline

**What to build:**
Build the automated syllabus ingestion service that extracts course weekly schedules, exam dates, and grading weights from uploaded syllabus PDFs using IBM Docling TableFormer with Gemini 3 Flash Vision-LLM fallback. Materialize the parsed week/module structure into hierarchical `virtual_folders` and chunk source documents for pgvector indexing in Supabase.

**Blocked by:**
- 01: Supabase Backend Schema & Folder-Scoped Vector RPC Initialization

**Status:** ready-for-agent

- [ ] Syllabus PDF parser service extracts assignment titles, dates, and weights via Docling TableFormer.
- [ ] Automatic fallback to Gemini 3 Flash Vision-LLM triggers if Docling confidence is below threshold or fails.
- [ ] Automatically stages course-bound nested `virtual_folders` (e.g., `/CS101/Week_03_Recursion`) from parsed modules.
- [ ] Text chunking pipeline chunks uploaded documents into 500-token blocks, generates 1536-dim embeddings, and persists to `document_chunks` in Supabase with `folder_id` partitioning.
- [ ] Automated tests verify end-to-end PDF parsing and folder creation on sample syllabus files.
