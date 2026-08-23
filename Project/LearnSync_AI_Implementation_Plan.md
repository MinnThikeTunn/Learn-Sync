# LearnSync AI: Detailed Software Implementation Plan
**Platform Stack:** **Supabase** (Database, Built-in Vector Engine, Auth, Storage, Realtime) + **FastAPI** (AI Compute Engine, Docling, FSRS) + **Next.js 15** (Perplexity Aesthetic)

---

## 1. Executive Architecture Overview

LearnSync AI operates entirely on **Supabase** as its single unified data and identity platform, combined with **FastAPI** for heavy AI/ML compute (Docling parsing, vector embedding generation, Bayesian Knowledge Tracing, and FSRS math) and **Next.js 15** for the client application.

```
+---------------------------------------------------------------------------------------+
|                                  NEXT.JS 15 FRONTEND                                  |
|  - Perplexity Aesthetic: rounded-[32px] cards, font-black headings, micro-animations  |
|  - Supabase SSR Client (@supabase/ssr) for Auth, Session & Realtime subscriptions     |
|  - Folder Tree Explorer, Workload Cockpit, Feynman Loop UI, Flashcard Deck           |
+-------------------------------------------+-------------------------------------------+
                     |                                      |
       FastAPI REST  | Bearer JWT (Supabase Auth)           | Supabase JS SDK
                     v                                      v
+-------------------------------------------+  +----------------------------------------+
|              FASTAPI BACKEND              |  |         SUPABASE CLOUD / PROJECT       |
|  (Compute, AI, Parsing & Math Engine)     |  |                                        |
|  - Docling Syllabus Ingestion & Chunking  |  |  [Supabase Auth]                       |
|  - Workload Engine (W(t) & Hysteresis)    |  |  - Google OAuth & Session Management   |
|  - Folder-Scoped RRF Vector Search Caller |  |  - Row Level Security (RLS) policies   |
|  - 4 Learning Styles Prompt Orchestrator  |  |                                        |
|  - Active Recall (Feynman Loop) Analyzer  |  |  [Supabase Database + Built-in Vector] |
|  - py-fsrs Scheduler & Leech Detector     |  |  - Tables: courses, folders, events    |
|  - B=MAP Burnout Guard Detector           |  |  - pgvector HNSW index on embeddings   |
|                                           |  |  - match_folder_chunks() RPC Function  |
+-------------------------------------------+  |                                        |
                     |                         |  [Supabase Storage]                    |
                     +------------------------>|  - "syllabi" bucket (PDF uploads)      |
                       supabase-py Client SDK  |  - "audio" bucket (30s recaps/podcasts)|
                                               |  - "course-materials" bucket           |
                                               +----------------------------------------+
```

---

## 2. Supabase Database Schema & Vector RPC

You configure these tables directly in your Supabase SQL Editor. Every table uses **Row Level Security (RLS)** so students can only access their own course files and cards.

### 2.1 Core Entities in Supabase
- `profiles`: Extends `auth.users` with student learning preferences.
- `courses`: Container for academic courses (e.g., CS101).
- `virtual_folders`: Hierarchical tree with materialized paths (e.g., `/CS101/Week_03_Recursion`).
- `documents`: Uploaded syllabus, slides, and notes linked to Supabase storage.
- `document_chunks`: 1536-dimensional vector embeddings with HNSW index for folder-scoped semantic retrieval.
- `events`: Deadlines parsed from syllabus, Google Calendar, Gmail, or entered manually.
- `workload_logs`: Historical record of rolling Workload Score $W(t)$ and mode states.
- `knowledge_components`: Curriculum units for Bayesian Knowledge Tracing (BKT).
- `student_kc_mastery`: Real-time probability of mastery $P(L_t)$ per component.
- `flashcards`: Spaced repetition cards tracked via `py-fsrs` with leech detection.
- `review_logs`: Telemetry logs of review ratings and retention timings.
- `burnout_triggers`: Low-barrier B=MAP 90-second micro-interventions.

---

## 3. Monorepo Structure

```
learnSync/
├── backend/
│   ├── app/
│   │   ├── api/v1/                  # REST endpoints for courses, folders, workload, RAG, fsrs
│   │   ├── core/                    # Config, Supabase client, security/auth
│   │   ├── schemas/                 # Pydantic schemas for request/response validation
│   │   ├── services/                # Docling parser, W(t) engine, BKT, FSRS, RRF search
│   │   └── main.py                  # FastAPI application entrypoint
│   ├── pyproject.toml / requirements.txt
│   └── .env.example
├── frontend/
│   ├── app/                         # Next.js 15 App Router pages & layouts
│   ├── components/                  # Perplexity aesthetic UI components (rounded-[32px])
│   ├── lib/supabase/                # Supabase SSR client helpers
│   ├── tailwind.config.ts
│   └── package.json
├── supabase/
│   └── schema.sql                   # Complete SQL migrations and RPC definitions
└── Project/
    ├── LearnSync_AI_Project_Proposal_v2.md
    ├── LearnSync_AI_SRS.md
    ├── LearnSync_AI_Distributed_System_Paper.md
    └── LearnSync_AI_Implementation_Plan.md
```

---

## 4. 14-Week Development Roadmap (7 Slices)

| Phase | Weeks | Milestones & Deliverables |
|---|---|---|
| **Phase 1** | Weeks 1–2 | **Supabase Setup, Virtual Folder Tree & Docling Syllabus Ingestion**<br>• Setup Supabase project & SQL schema.<br>• FastAPI Docling PDF parser extracting weekly modules and exam dates into a staged preview.<br>• Next.js folder explorer with Perplexity aesthetic (`rounded-[32px]`). |
| **Phase 2** | Weeks 3–4 | **Event Store, Workload Engine $W(t)$ & Hysteresis State Machine**<br>• Event synchronization (Syllabus, Google Calendar OAuth, Manual).<br>• Hyperbolic $W(t)$ calculation with Schmitt Hysteresis ($W(t) > 0.70$ Busy, $W(t) < 0.55$ Free).<br>• Animated Workload Cockpit UI in Next.js. |
| **Phase 3** | Weeks 5–6 | **Supabase Built-in Vector Hybrid RRF Search & 4 Adaptive Learning Styles**<br>• Ingest course lecture notes into Supabase `document_chunks`.<br>• Call `match_folder_chunks` RPC for folder-scoped hybrid dense + sparse retrieval.<br>• Build style generator: Visual diagrams, Auditory recaps, Read/Write summaries, Kinesthetic code snippets. |
| **Phase 4** | Weeks 7–8 | **Active Recall (Feynman Loop) & Bayesian Knowledge Tracing (BKT)**<br>• Feynman prompt & precision-gap analysis comparing student explanation against Supabase source chunks.<br>• Auto-convert detected gaps into flashcards.<br>• Track concept mastery probability $P(L_t)$ per Knowledge Component. |
| **Phase 5** | Weeks 9–10 | **Elastic Spaced Repetition (`py-fsrs`) & Leech Detection**<br>• Dynamic retention targets ($90\%$ in Free Mode vs. $80\%$ in Busy Mode).<br>• Pareto 80/20 concept filter during Busy Mode.<br>• Leech quarantine ($\ge 4$ lapses) with LLM rewrites. |
| **Phase 6** | Weeks 11–12 | **Burnout Guard (B=MAP Micro-Tasks) & Event Notification**<br>• Detect 3+ major deadlines in 48h or 0 calendar slots.<br>• Suppress long study prompts and trigger 90-second B=MAP micro-tasks.<br>• Asynchronous notification flow via Supabase Realtime. |
| **Phase 7** | Weeks 13–14 | **Perplexity Design Polish & End-to-End Pilot Validation**<br>• Complete UI styling pass: font-black typography, Obsidian dark mode, Framer Motion animations.<br>• Pilot validation against real university course syllabi. |
