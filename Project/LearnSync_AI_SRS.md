# Software Requirements Specification

# LearnSync AI

*The Context-Aware Adaptive Learning, Virtual Folder Resource Manager & Workload Co-Pilot*

**Document Version:** 1.0
**Prepared:** August 9, 2026
**Status:** Draft — Derived from Project Proposal v2

---

## Revision History

| Version | Date | Description | Author |
|---|---|---|---|
| 0.1 | — | Initial Project Proposal (v2) drafted | Project Team |
| 1.0 | 2026-08-09 | First Software Requirements Specification derived from Proposal v2 | Project Team |

---

## Table of Contents

1. [Introduction](#1-introduction)
   1.1 [Purpose](#11-purpose)
   1.2 [Scope](#12-scope)
   1.3 [Definitions, Acronyms, and Abbreviations](#13-definitions-acronyms-and-abbreviations)
   1.4 [References](#14-references)
   1.5 [Document Overview](#15-document-overview)
2. [Overall Description](#2-overall-description)
   2.1 [Product Perspective](#21-product-perspective)
   2.2 [Product Functions (Summary)](#22-product-functions-summary)
   2.3 [User Characteristics](#23-user-characteristics)
   2.4 [Design and Implementation Constraints](#24-design-and-implementation-constraints)
   2.5 [Assumptions and Dependencies](#25-assumptions-and-dependencies)
3. [System Features and Functional Requirements](#3-system-features-and-functional-requirements)
   3.1 [Virtual Folder Resource Management (FR-1)](#31-virtual-folder-resource-management-fr-1)
   3.2 [Event-Driven Workload Engine (FR-2)](#32-event-driven-workload-engine-fr-2)
   3.3 [Personalized Adaptive Learning Engine (FR-3)](#33-personalized-adaptive-learning-engine-fr-3)
   3.4 [Grounded RAG Retrieval (FR-4)](#34-grounded-rag-retrieval-fr-4)
   3.5 [Active Recall — The Feynman Loop (FR-5)](#35-active-recall--the-feynman-loop-fr-5)
   3.6 [Elastic Spaced Repetition — FSRS + Workload Coupling (FR-6)](#36-elastic-spaced-repetition--fsrs--workload-coupling-fr-6)
   3.7 [Hysteresis Mode Switching (FR-7)](#37-hysteresis-mode-switching-fr-7)
   3.8 [Leech Detection (FR-8)](#38-leech-detection-fr-8)
   3.9 [Burnout Guard — B=MAP Micro-Tasks (FR-9)](#39-burnout-guard--bmap-micro-tasks-fr-9)
4. [External Interface Requirements](#4-external-interface-requirements)
5. [Non-Functional Requirements](#5-non-functional-requirements)
6. [Data Requirements](#6-data-requirements)
7. [System Architecture Summary](#7-system-architecture-summary)
   [Appendix A: Requirements Traceability Matrix](#appendix-a-requirements-traceability-matrix)
   [Appendix B: Open Items for Stakeholder Review](#appendix-b-open-items-for-stakeholder-review)

---

## 1. Introduction

### 1.1 Purpose

This Software Requirements Specification (SRS) defines the functional and non-functional requirements for LearnSync AI, a system that unifies virtual folder-based resource management, an event-driven academic workload engine, and a personalized adaptive learning engine. This document translates the goals and mechanisms described in the LearnSync AI Project Proposal (v2) into verifiable requirements intended to guide design, implementation, testing, and acceptance.

The intended audience includes the development team, QA engineers, project stakeholders, and academic partners evaluating the system for pilot deployment.

### 1.2 Scope

LearnSync AI is a web-based application that helps students manage academic resources and adapt their learning intensity to their real-time workload. The system will:

- Organize course materials into a nested virtual folder hierarchy bound to course modules.
- Parse syllabi and monitor Google Calendar and scoped Gmail messages to build and maintain an event/deadline feed.
- Compute a continuous rolling Workload Score, W(t), from event weight and urgency.
- Generate learning content whose format matches the student's preferred learning style and whose depth adapts to W(t) ("Free Mode" vs. "Busy Mode").
- Ground all generated content in the student's own course materials using hybrid retrieval-augmented generation (RAG).
- Schedule spaced-repetition review using an elastic FSRS implementation coupled to W(t).
- Detect high-stress conditions and intervene with low-barrier "B=MAP" micro-tasks to reduce burnout and doomscrolling.

Out of scope for this version: grade-book/LMS write-back, native mobile applications, third-party tutor marketplaces, and support for calendar or email providers other than Google Calendar and Gmail.

### 1.3 Definitions, Acronyms, and Abbreviations

| Term | Definition |
|---|---|
| W(t) | Rolling Workload Score at time t; a 3-day lookahead score computed from deadline density and event weights. |
| Free Mode | Learning content mode active when W(t) ≤ 0.55; delivers deep, comprehensive content. |
| Busy Mode | Learning content mode active when W(t) > 0.70; delivers bite-sized, low-cognitive-load content. |
| Hysteresis Band | The 0.55–0.70 W(t) range in which the current mode is retained to prevent rapid toggling ("flicker"). |
| RAG | Retrieval-Augmented Generation — grounding LLM output in retrieved source documents. |
| RRF | Reciprocal Rank Fusion — a hybrid search technique combining dense vector and sparse (BM25) rankings. |
| FSRS | Free Spaced Repetition Scheduler; implemented via the `py-fsrs` library. |
| Leech | A flashcard failed 4 or more times, flagged for pause, simplification, or rewrite. |
| B=MAP | BJ Fogg's Behavior Model: Behavior = Motivation × Ability × Prompt. |
| Virtual Folder | A logical, nested organizational unit (e.g., `/CS101/Week_03_Recursion/`) bound to a course module. |
| Docling | IBM Research's document parsing library (TableFormer model) used to parse syllabus PDFs. |
| Burnout Guard | Rule-based monitoring layer that detects high-risk workload conditions and issues micro-prompts. |

### 1.4 References

- LearnSync AI: Project Proposal (v2) — source document for this specification.
- IEEE Std 830-1998 — IEEE Recommended Practice for Software Requirements Specifications (structural reference).
- `py-fsrs` library documentation (Free Spaced Repetition Scheduler).
- Docling (IBM Research) documentation.
- Google Calendar API and Gmail API documentation.
- BJ Fogg, "Tiny Habits" / Fogg Behavior Model (B=MAP).

### 1.5 Document Overview

Section 2 describes the product at a high level, including its context, functions, users, and constraints. Section 3 specifies detailed functional requirements grouped by subsystem. Section 4 specifies external interface requirements. Section 5 specifies non-functional (quality) requirements. Section 6 specifies data requirements. Section 7 summarizes the target system architecture. Appendices provide a requirements traceability matrix against the development roadmap and a list of open items for stakeholder review.

---

## 2. Overall Description

### 2.1 Product Perspective

LearnSync AI is a new, self-contained system that integrates capabilities currently split across two categories of existing tools:

- **Learning platforms** (e.g., Coursera, generic AI tutors), which deliver content but are blind to the student's calendar, deadlines, and stress level.
- **Productivity and file tools** (e.g., Notion, Google Drive, Todoist), which track files or deadlines but provide no adaptive, grounded learning support.

LearnSync AI sits between these categories, using calendar, email, and syllabus signals as first-class inputs that directly drive the depth, format, and pacing of generated learning content. The system is designed around a zero-maintenance constraint: after initial onboarding and account connection, the system should require no manual tagging, filing, or daily planner upkeep from the student.

### 2.2 Product Functions (Summary)

- Virtual folder resource management scoped to course/module for organizing source material.
- Automated event ingestion from syllabus PDFs, Google Calendar, and scoped Gmail monitoring.
- Continuous computation of a rolling Workload Score, W(t), with hysteresis-based mode switching.
- Adaptive, style-specific content generation across four learning styles and two workload modes.
- Grounded RAG retrieval using hybrid dense + sparse (RRF) search, scoped by virtual folder.
- Active-recall "Feynman Loop" practice with automated gap detection.
- Elastic, W(t)-coupled spaced-repetition scheduling (FSRS) with leech detection and Pareto filtering.
- Burnout Guard monitoring with B=MAP micro-task interventions.

### 2.3 User Characteristics

| User Class | Description |
|---|---|
| Primary User — Student | College or university student managing multiple concurrent courses; connects Google Calendar and Gmail, uploads/organizes course material, and consumes adaptive learning content. Assumed to be a non-technical end user. |
| Secondary User — Pilot Coordinator / Instructor (Phase 7) | Reviews aggregate, de-identified telemetry during the university pilot to assess engagement and effectiveness. Does not access individual student content or accounts. |
| System Administrator | Manages deployment, API credentials/quotas (Google, Docling, Vision-LLM), and monitors system health. |

### 2.4 Design and Implementation Constraints

- Backend must be implemented in Python 3.11+ using the FastAPI framework.
- Structured data (events, weights, scores, virtual folders) and unstructured vector embeddings must be stored in Supabase (PostgreSQL 16 with pgvector and Row Level Security).
- Spaced repetition must use the `py-fsrs` library rather than a custom-built scheduler.
- Syllabus parsing must use Docling (TableFormer model) with a Vision-LLM fallback (Gemini 3 Flash) for low-confidence or non-standard layouts.
- Frontend must be implemented in React / Next.js with Tailwind CSS.
- Gmail access must be scoped (least-privilege, read-only where feasible) and limited to deadline-change detection.
- The system must operate under a zero-maintenance design constraint — no feature may require recurring manual tagging to function correctly.

### 2.5 Assumptions and Dependencies

- Students have an active Google account and are willing to grant Calendar and Gmail OAuth scopes.
- Course syllabi are available as parseable PDFs (or scanned documents suitable for Vision-LLM fallback).
- Third-party API availability and quotas (Google Calendar API, Gmail API, Gemini 3 Flash) remain stable through development and pilot phases.
- The `py-fsrs` library's default algorithm produces acceptable retention estimates without requiring a custom scheduling model.
- Pilot testing (Phase 7) will have access to a cohort of real university students under appropriate consent/IRB-equivalent processes.

---

## 3. System Features and Functional Requirements

Requirements are grouped by subsystem, matching the architecture in Section 7. Each requirement is uniquely identified for traceability (see Appendix A) and is written as a verifiable "shall" statement. Priority is expressed as **Essential** (must be present for a viable release), **High**, or **Medium**.

### 3.1 Virtual Folder Resource Management (FR-1)

Provides the nested, course-scoped organizational structure that all other subsystems bind to.

| ID | Requirement | Priority |
|---|---|---|
| FR-1.1 | The system shall allow creation of a nested virtual folder hierarchy (e.g., `/CS101/Week_03_Recursion/`) independent of underlying physical file storage. | Essential |
| FR-1.2 | The system shall bind each virtual folder to a specific course and course module via metadata (course_id, module_id). | Essential |
| FR-1.3 | The system shall automatically create virtual folders from parsed syllabus module/week structure. | High |
| FR-1.4 | The system shall allow the student to manually create, rename, move, or delete virtual folders without breaking existing metadata bindings. | High |
| FR-1.5 | The system shall restrict retrieval-augmented generation (RAG) queries to the course_id and/or folder_path scope selected or implied by the active study context. | Essential |
| FR-1.6 | The system shall allow a student to upload source files (PDFs, notes, slides) directly into a target virtual folder. | Essential |

### 3.2 Event-Driven Workload Engine (FR-2)

Ingests deadlines from multiple sources and converts them into a continuously updated workload signal.

| ID | Requirement | Priority |
|---|---|---|
| FR-2.1 | The system shall extract assignments, quizzes, exams, and project deadlines from syllabus PDFs using Docling, with Vision-LLM fallback for low-confidence parses. | Essential |
| FR-2.2 | The system shall synchronize events from a student's connected Google Calendar via OAuth. | Essential |
| FR-2.3 | The system shall monitor scoped Gmail messages for deadline changes (e.g., postponed exams, added quizzes) and propose corresponding event updates. | High |
| FR-2.4 | The system shall allow students to manually create, edit, or delete events. | Essential |
| FR-2.5 | The system shall assign each event a weight (e.g., percentage of final grade) and an urgency value (days until due). | Essential |
| FR-2.6 | The system shall automatically flag the virtual folder(s) bound to an upcoming event as a high-priority focus area. | High |
| FR-2.7 | The system shall continuously compute a rolling 3-day lookahead Workload Score, W(t), from deadline density and event weights. | Essential |
| FR-2.8 | The system shall recompute W(t) whenever an event is added, edited, removed, or its due date changes, and at minimum once per day. | High |
| FR-2.9 | The system shall persist a historical log of W(t) values and the events contributing to each computation, for analytics and auditability. | Medium |
| FR-2.10 | The system shall present a consolidated event feed merging syllabus-parsed, calendar-synced, Gmail-detected, and manually entered events, with duplicate detection across sources. | High |

### 3.3 Personalized Adaptive Learning Engine (FR-3)

Selects content representation (learning style) and content depth (workload mode) for every generated study artifact.

| ID | Requirement | Priority |
|---|---|---|
| FR-3.1 | The system shall capture the student's primary learning style (Visual, Auditory/Conversational, Read/Write, or Kinesthetic/Hands-on) during onboarding. | Essential |
| FR-3.2 | The system shall allow the student to change their selected learning style at any time from account settings. | Medium |
| FR-3.3 | The system shall operate in Free Mode when W(t) ≤ 0.55, generating deep, comprehensive content. | Essential |
| FR-3.4 | The system shall operate in Busy Mode when W(t) > 0.70, generating bite-sized, low-cognitive-load content. | Essential |
| FR-3.5 | In Free Mode, the system shall generate: interactive diagrams (Visual), Socratic dialogue / long-form podcast-style audio (Auditory), structured study guides (Read/Write), and interactive code sandboxes / build guides (Kinesthetic), according to the student's selected style. | High |
| FR-3.6 | In Busy Mode, the system shall generate: high-contrast cheat-sheets (Visual), 30-second audio recaps (Auditory), bulleted summaries (Read/Write), and micro bug-fix / rapid-fire snippet challenges (Kinesthetic), according to the student's selected style. | High |
| FR-3.7 | The system shall apply the hysteresis rule defined in FR-7 to determine mode when W(t) falls within the 0.55–0.70 band. | Essential |

### 3.4 Grounded RAG Retrieval (FR-4)

Ensures generated content is factually grounded in the student's own course material.

| ID | Requirement | Priority |
|---|---|---|
| FR-4.1 | The system shall store structured data (users, courses, virtual folders, dates, event weights, scores) in Supabase relational tables with Row Level Security (RLS). | Essential |
| FR-4.2 | The system shall store unstructured source files (PDFs, notes) as vector embeddings directly in Supabase using the pgvector extension (1536-dim HNSW index), tagged and partitioned with user_id and folder_id. | Essential |
| FR-4.3 | The system shall retrieve context using Reciprocal Rank Fusion (RRF), combining dense vector similarity and sparse BM25 keyword ranking. | High |
| FR-4.4 | The system shall restrict retrieval candidates to the active virtual folder scope before ranking. | Essential |
| FR-4.5 | The system shall ground generated explanations, flashcards, and summaries in retrieved source passages and shall avoid presenting ungrounded content as authoritative. | Essential |
| FR-4.6 | The system shall indicate to the student when a request cannot be adequately grounded in available source material (insufficient retrieval confidence). | Medium |

### 3.5 Active Recall — The Feynman Loop (FR-5)

| ID | Requirement | Priority |
|---|---|---|
| FR-5.1 | The system shall convert source material from the selected folder into plain-language analogies as an ingestion step. | High |
| FR-5.2 | The system shall prompt the student to explain a concept back in their own words. | High |
| FR-5.3 | The system shall perform automated precision-gap analysis comparing the student's explanation against source material to detect missing or incorrect concepts. | High |
| FR-5.4 | The system shall automatically convert detected gaps into new, folder-scoped spaced-repetition cards. | High |

### 3.6 Elastic Spaced Repetition — FSRS + Workload Coupling (FR-6)

| ID | Requirement | Priority |
|---|---|---|
| FR-6.1 | The system shall schedule flashcard reviews using the `py-fsrs` (Free Spaced Repetition Scheduler) library. | Essential |
| FR-6.2 | While in Busy Mode, the system shall lower the target retention (R꜀) to 80% and expand review intervals by approximately 1.75x relative to Free Mode defaults. | High |
| FR-6.3 | The system shall design Busy Mode scheduling parameters to reduce the average number of daily card reviews by up to 45% relative to Free Mode, and shall log actual review counts to validate this target. | Medium |
| FR-6.4 | While in Busy Mode, the system shall apply Pareto 80/20 filtering to restrict presented study content to the top 20% "core primitive" concepts associated with upcoming events. | High |
| FR-6.5 | The system shall restore standard (non-reduced) retention targets and full content scope upon exiting Busy Mode. | High |

### 3.7 Hysteresis Mode Switching (FR-7)

| ID | Requirement | Priority |
|---|---|---|
| FR-7.1 | The system shall enter Busy Mode only when W(t) exceeds 0.70. | Essential |
| FR-7.2 | The system shall exit Busy Mode only when W(t) falls below 0.55. | Essential |
| FR-7.3 | The system shall retain the currently active mode without switching while 0.55 ≤ W(t) ≤ 0.70 (the hysteresis / dead band). | Essential |
| FR-7.4 | The system shall log every Free↔Busy mode transition with a timestamp and the triggering W(t) value. | Medium |

### 3.8 Leech Detection (FR-8)

| ID | Requirement | Priority |
|---|---|---|
| FR-8.1 | The system shall flag any flashcard failed 4 or more times as a "leech." | High |
| FR-8.2 | The system shall automatically pause leech cards from the standard review queue. | High |
| FR-8.3 | The system shall offer an LLM-simplified or rewritten version of a leech card in place of the original. | High |
| FR-8.4 | The system shall allow the student to manually resume, permanently delete, or reset the failure count of a leech card. | Medium |

### 3.9 Burnout Guard — B=MAP Micro-Tasks (FR-9)

| ID | Requirement | Priority |
|---|---|---|
| FR-9.1 | The system shall monitor event and calendar data for high-risk conditions, including 3 or more major deadlines within a 48-hour window and zero free calendar slots for 2 or more consecutive days. | High |
| FR-9.2 | When a high-risk condition is detected, the system shall issue a low-barrier micro-task prompt (e.g., a single 90-second exercise) in place of a full study session, following the B=MAP behavior model. | High |
| FR-9.3 | The system shall suppress full-length study session prompts while an active high-risk condition persists. | Medium |
| FR-9.4 | The system shall log Burnout Guard triggers and the student's response/engagement for later telemetry review. | Medium |

---

## 4. External Interface Requirements

### 4.1 User Interfaces

- A responsive web application (React / Next.js, Tailwind CSS) providing: onboarding & learning-style selection, virtual folder browser, event feed / calendar view, adaptive study dashboard, flashcard review UI, and Burnout Guard prompts.
- The UI shall support Markdown rendering, inline SVG/Mermaid diagrams, and interactive code blocks.
- The UI shall visually distinguish Free Mode and Busy Mode states so the student understands why content depth has changed.

### 4.2 Hardware Interfaces

No dedicated hardware is required. The system shall run on standard client devices (desktop or laptop browsers) supported by the target React/Next.js browser matrix; server-side components run on standard cloud compute.

### 4.3 Software Interfaces

| Interface | Purpose |
|---|---|
| Google Calendar API (OAuth 2.0) | Two-way event sync for deadlines and free/busy calendar slots. |
| Gmail API (scoped) | Read-only, scoped monitoring for deadline-change notifications from instructors/LMS. |
| Docling (IBM Research, TableFormer) | Primary syllabus PDF parsing, including tabular schedule extraction. |
| Vision-LLM Fallback (Gemini 3 Flash) | Fallback parsing for syllabi that Docling cannot confidently structure. |
| Supabase (PostgreSQL 16 + pgvector) | Unified backend database: relational storage (profiles, courses, folders, events, logs) and folder-scoped vector search via built-in RPC & HNSW index. |
| `py-fsrs` | Spaced-repetition scheduling engine. |
| Text-to-Speech engine | Generation of Auditory-style audio recaps and podcast-style explanations. |

### 4.4 Communication Interfaces

- All client–server communication shall use HTTPS/TLS.
- OAuth 2.0 shall be used for Google Calendar and Gmail authorization; tokens shall be stored encrypted and refreshed automatically.
- The backend shall expose a versioned REST (or equivalent) API consumed by the FastAPI-driven Next.js frontend.

---

## 5. Non-Functional Requirements

### 5.1 Performance

| ID | Requirement | Priority |
|---|---|---|
| NFR-1.1 | Folder-scoped RAG retrieval (RRF hybrid search) shall return ranked candidates within 2 seconds for a typical course-sized corpus. | High |
| NFR-1.2 | W(t) shall be recomputed and reflected in the UI within 5 seconds of a triggering event change. | Medium |
| NFR-1.3 | Micro-content generation (Busy Mode cheat-sheets, 30-second recaps) shall complete within 5 seconds of request under normal load. | Medium |

### 5.2 Security & Privacy

| ID | Requirement | Priority |
|---|---|---|
| NFR-2.1 | Google Calendar and Gmail access shall request the minimum OAuth scopes necessary for event sync and deadline-change detection. | Essential |
| NFR-2.2 | All student data (source documents, embeddings, event data, OAuth tokens) shall be encrypted at rest and in transit. | Essential |
| NFR-2.3 | Gmail content shall be processed only for deadline-change detection and shall not be permanently stored beyond what is required to reflect detected event changes. | High |
| NFR-2.4 | The system shall isolate each student's virtual folders, embeddings, and events from other students at the data-access layer. | Essential |
| NFR-2.5 | Aggregate telemetry shared with pilot coordinators/instructors (Section 2.3) shall be de-identified. | High |

### 5.3 Reliability & Availability

| ID | Requirement | Priority |
|---|---|---|
| NFR-3.1 | The system shall degrade gracefully to Docling-only parsing (with a manual-entry fallback) if the Vision-LLM fallback service is unavailable. | Medium |
| NFR-3.2 | Loss of Gmail or Calendar API connectivity shall not block core functionality (folder browsing, manual events, spaced repetition); affected features shall fail gracefully with a visible status indicator. | High |
| NFR-3.3 | The production system shall target 99.5% monthly uptime for core study and review features. | Medium |

### 5.4 Usability

| ID | Requirement | Priority |
|---|---|---|
| NFR-4.1 | A new student shall be able to complete onboarding (learning-style selection, Google account connection, first syllabus upload) in under 5 minutes. | High |
| NFR-4.2 | The system shall require no recurring manual tagging or planner maintenance to keep folders, events, and W(t) current (zero-maintenance constraint). | Essential |
| NFR-4.3 | Mode transitions (Free ↔ Busy) and their cause shall be explained to the student in plain language within the UI. | Medium |

### 5.5 Maintainability

| ID | Requirement | Priority |
|---|---|---|
| NFR-5.1 | The backend shall be organized into independently testable modules corresponding to Sections 3.1–3.9 (folders, events/workload, adaptive engine, RAG, Feynman loop, FSRS, hysteresis, leech detection, burnout guard). | Medium |
| NFR-5.2 | All external API integrations (Google, Docling, Vision-LLM, TTS) shall be isolated behind internal service interfaces to allow provider substitution with minimal impact on core logic. | Medium |

### 5.6 Scalability

| ID | Requirement | Priority |
|---|---|---|
| NFR-6.1 | The data model and vector storage shall support multi-tenant use across many students and courses without cross-contamination of retrieval scope (see FR-1.5, FR-4.4). | High |
| NFR-6.2 | The architecture shall support horizontal scaling of the FastAPI backend and vector database to accommodate pilot-scale concurrent usage (Phase 7). | Medium |

---

## 6. Data Requirements

The following core entities shall be represented in the data model. This list is descriptive, not exhaustive of implementation-level schema detail.

| Entity | Key Attributes / Notes |
|---|---|
| User | Student profile, authentication identity, selected learning style, connected OAuth accounts. |
| Course | Course identifier, name, term; parent of the virtual folder hierarchy for that course. |
| VirtualFolder | Hierarchical path, parent folder reference, bound course_id/module_id, high-priority flag. |
| SourceDocument | Uploaded/parsed file metadata, folder_path binding, parsed text, vector embedding references. |
| Event | Type (assignment/quiz/exam/project), weight, due date, source (syllabus/calendar/Gmail/manual), bound folder(s). |
| WorkloadScoreLog | Timestamped W(t) values, contributing events, and resulting mode (Free/Busy). |
| Flashcard | Content, associated folder/gap origin, FSRS scheduling state, leech flag, failure count. |
| ReviewLog | Per-review outcome, timestamp, retention estimate, applied mode (Free/Busy) at time of review. |
| BurnoutTrigger | Trigger condition, timestamp, prompt issued, student response/engagement. |

---

## 7. System Architecture Summary

The following stack components, carried forward from the Project Proposal, constrain and inform the requirements above:

| Layer | Component |
|---|---|
| Backend Framework | FastAPI (Python 3.11+) |
| Database & Vector Storage | Supabase (PostgreSQL 16 with pgvector & RLS for folder-scoped RRF hybrid search) |
| Syllabus Parsing | Docling (IBM Research TableFormer model) with Vision-LLM fallback (Gemini 3 Flash) |
| Spaced Repetition | `py-fsrs` wrapper library |
| Frontend | React / Next.js with Tailwind CSS; Markdown, SVG, and interactive code block rendering |

Data flow: Docling syllabus parsing, Google Calendar sync, and scoped Gmail monitoring all feed the Deadline/Event Store inside Supabase, which is also linked to the Virtual Folder tables. The Workload Engine consumes the Event Store to compute W(t), which in turn drives the FSRS Scheduler (elastic retention) and the Burnout Guard (B=MAP redirects). The folder-scoped Supabase Vector Store (RPC) and the Workload Engine jointly feed the Adaptive Dashboard & UI.

```
[ Docling Syllabus Parser ]   [ Google Calendar Sync ]   [ Gmail API (Scoped) ]
            │                            │                          │
            ▼                            ▼                          ▼
[ Supabase Virtual Folders ] ─► [ Supabase Events & Deadlines ] ◄───┘
                                         │
                                         ▼
                             [ Workload Engine: W(t) ]
                                         │
                           ┌─────────────┴─────────────┐
                           ▼                           ▼
[ Supabase pgvector RPC (RRF) ]   [ FSRS Scheduler ]   [ Burnout Guard ]
   (Folder-scoped Hybrid Search)   (Elastic Retention)   (B=MAP Redirect)
            │                            │                     │
            └────────────────────────────┼─────────────────────┘
                                         ▼
                            [ Adaptive Dashboard & UI ]
```

---

## Appendix A: Requirements Traceability Matrix

Maps each functional requirement group to the corresponding development roadmap phase from the Project Proposal (Section 7).

| Requirement Group | Roadmap Phase | Weeks |
|---|---|---|
| FR-1 Virtual Folder Resource Management | Phase 1 | 1–2 |
| FR-2 Event-Driven Workload Engine (parsing, calendar, W(t) core) | Phase 1–2 | 1–4 |
| FR-7 Hysteresis Mode Switching | Phase 2 | 3–4 |
| FR-3 Adaptive Learning Engine | Phase 3 | 5–6 |
| FR-4 Grounded RAG Retrieval | Phase 3 | 5–6 |
| FR-2.3 Scoped Gmail deadline-change detection | Phase 4 | 7–8 |
| FR-6 Elastic Spaced Repetition (FSRS) | Phase 5 | 9–10 |
| FR-8 Leech Detection | Phase 5 | 9–10 |
| FR-9 Burnout Guard (B=MAP) | Phase 6 | 11–12 |
| FR-5 Active Recall / Feynman Loop | Phase 6 | 11–12 |
| All groups — validation | Phase 7 (User Testing) | 13–14 |

---

## Appendix B: Open Items for Stakeholder Review

- Confirm precise Gmail retention policy for detected deadline-change messages (NFR-2.3).
- Confirm target concurrent-user count for Phase 7 pilot to finalize scalability targets (NFR-6.2).
- Confirm whether instructor-facing telemetry (Section 2.3) requires a dedicated dashboard or a static report.
- Confirm acceptable behavior when Docling and Vision-LLM fallback both fail to parse a syllabus (manual entry vs. blocked onboarding).
- Confirm the definitive formula/weighting used to compute W(t) beyond "deadline density and event weights" (currently descriptive in the Proposal, needs a precise specification for implementation).
