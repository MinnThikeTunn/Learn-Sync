# LearnSync AI: Project Proposal (v2)

**The Context-Aware Adaptive Learning, Virtual Folder Resource Manager & Workload Co-Pilot**

---

## 1. Executive Summary & Core Value Proposition

Students face a persistent dilemma: they want to stay ahead in their courses and build relevant skills, but heavy academic workloads—assignments, quizzes, exams, and project deadlines—make consistent, deep learning feel impossible. Existing software fails to address both sides of this equation:

- **Learning Platforms** (Coursera, generic AI tutors) ignore the student's actual calendar, deadlines, and real-time stress levels.
- **Productivity & File Tools** (Notion, Drive, Todoist) track files or deadlines, but offer zero help with adaptive, grounded learning around those deadlines.

**LearnSync AI** bridges this gap. It combines a **Virtual Folder Resource Management System** with an **Event-Driven Workload Engine** and an **Adaptive Learning Engine**. On a heavy week, LearnSync automatically shrinks learning demands into 90-second micro-flashcards and audio recaps. On a light week, it delivers deep interactive walkthroughs and coding challenges. The system requires **zero ongoing maintenance**, adapting automatically to the student's actual schedule.

---

## 2. Research-Validated Pain Points

Synthesized from student discussions and educational data, LearnSync directly addresses five key friction points:

| # | Pain Area | How LearnSync Solves It |
|---|---|---|
| 1 | **LMS Friction & Missing Due-Dates** | Bypasses flawed LMS metadata via Docling PDF syllabus parsing and scoped Gmail change detection. |
| 2 | **The Cognitive Trilemma** | Balances academics, career prep, and well-being by automatically scaling study intensity down when deadlines cluster. |
| 3 | **Communication Breakdown & "Syllabus Drift"** | Consolidates syllabus shifts, unannounced quizzes, and exam changes into a single event feed. |
| 4 | **Productivity Tool Fatigue** | Built on a zero-maintenance constraint: requires no manual tagging or daily planner updates. |
| 5 | **Burnout & Doomscrolling Loops** | Replaces idle high-stress moments with B=MAP micro-tasks rather than passive scrolling. |

> *"LearnSync AI doesn't ask students to organize their learning — it's the one system that gets less demanding exactly when everything else gets more demanding."*

---

## 3. Virtual Folder Resource Management & Event-Driven Engine

### 3.1 Virtual Folder System
Instead of unorganized document dumps, LearnSync uses a familiar, nested folder system (e.g., `/CS101/Week_03_Recursion/` or `/Math201/Midterm_Prep/`).

- **Targeted RAG Scope:** When generating practice materials or flashcards, the vector database queries are strictly filtered by `course_id` or `folder_path`, drastically reducing retrieval latency and eliminating context cross-contamination.
- **Metadata Binding:** Each folder binds directly to a specific course module, enabling the system to know precisely which source files to draw from when an event approaches.

### 3.2 Event-Driven Workload Integration
Events—whether parsed automatically from syllabi, synced via Google Calendar, detected from Gmail, or added manually—act as system triggers:

1. **Event Parsing & Scoring:** Every test, assignment, or project is evaluated for its **weight** (e.g., 30% final exam vs. 2% assignment) and **urgency** (proximity in days).
2. **Folder Binding & Highlighting:** Upcoming events automatically flag their corresponding material folders as high-priority focus areas.
3. **Rolling Workload Score $W(t)$:** A 3-day lookahead score $W(t)$ is computed continuously from deadline density and event weights.

---

## 4. Personalized Adaptive Learning Engine

Personalized learning in LearnSync operates across two distinct dimensions:
- **Learning Style:** Determines the *representation format* of the content.
- **Workload Score $W(t)$:** Determines the *depth, length, and pacing* of the content.

```
                  ┌──────────────────────────────────────────────┐
                  │           User Learning Style                │
                  │  (Visual / Auditory / Read-Write / Kinesthetic) │
                  └──────────────────────┬───────────────────────┘
                                         │
                                         ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                             RAG Context Retrieval                               │
│            (Filtered by Virtual Folder Path + RRF Hybrid Search)                │
└────────────────────────────────────────┬────────────────────────────────────────┘
                                         │
                    ┌────────────────────┴────────────────────┐
                    ▼                                         ▼
         Free Mode (W(t) <= 0.55)                   Busy Mode (W(t) > 0.70)
   ┌──────────────────────────────────┐      ┌──────────────────────────────────┐
   │ Deep, comprehensive learning     │      │ Bite-sized, low-cognitive load   │
   │ • Visual: SVG/Mermaid diagrams    │      │ • Visual: Cheat-sheets/Infographics│
   │ • Auditory: Detailed Q&A / Podcast│      │ • Auditory: 30s Audio Recaps     │
   │ • Read/Write: In-depth guides     │      │ • Read/Write: Bullet summaries   │
   │ • Kinesthetic: Interactive code  │      │ • Kinesthetic: Bug-fix micro-tasks│
   └──────────────────────────────────┘      └──────────────────────────────────┘
```

### 4.1 The 4 Learning Styles Framework
During onboarding, students select their preferred primary style:

1. **Visual:**
   - *Free Mode:* Generates interactive Mermaid.js sequence diagrams, SVG flowcharts, and visual concept maps.
   - *Busy Mode:* Produces high-contrast cheat-sheets, visual hierarchy cards, and annotated key diagrams.
2. **Auditory / Conversational:**
   - *Free Mode:* Generates Socratic dialogue transcripts and long-form podcast-style explanations (via Text-to-Speech).
   - *Busy Mode:* Generates 30-second audio summaries and rapid verbal flashcard prompts.
3. **Read / Write:**
   - *Free Mode:* Generates structured, comprehensive study guides, detailed technical prose, and formatted markdown notes.
   - *Busy Mode:* Generates concise bulleted summaries, core definitions, and key-term lists.
4. **Kinesthetic / Hands-on:**
   - *Free Mode:* Generates full interactive code sandboxes, step-by-step build guides, and real-world implementation labs.
   - *Busy Mode:* Generates micro-code bug fixes, syntax rapid-fire challenges, and targeted snippet cards.

### 4.2 Grounded RAG Retrieval (RRF Hybrid Search)
To prevent hallucinations on technical coursework:
- **Structured Data (Dates, Weights):** Stored in PostgreSQL relational tables.
- **Unstructured Files (PDFs, Notes):** Filtered by virtual folder path and retrieved using **Reciprocal Rank Fusion (RRF)**, combining dense vector embeddings with sparse BM25 keyword matching:
$$	ext{RRF\_Score} = \sum_{m \in M} rac{1}{60 + 	ext{rank}_m}$$

### 4.3 Active Recall: The Feynman Loop
1. **Ingest:** Converts source material from the selected folder into plain-language analogies.
2. **Recall:** Prompts the student to explain concepts back in their own words.
3. **Evaluate:** Automated precision-gap analysis compares student input against source files to detect missing concepts or misunderstandings.
4. **Reinforce:** Targeted gaps are immediately converted into localized spaced-repetition cards.

---

## 5. Workload Relief Mechanisms & Spaced Repetition

### 5.1 Elastic Spaced Repetition (FSRS + Workload Coupling)
LearnSync integrates the **Free Spaced Repetition Scheduler (`py-fsrs`)**, dynamically linking review schedules to the workload score $W(t)$:

- **Busy Mode ($W(t) > 0.70$):** Target retention $R_d$ lowers to 80%, expanding review intervals by ~1.75x. This reduces daily card reviews by up to **45%** during midterm or finals weeks.
- **Pareto 80/20 Filtering:** In Busy Mode, study content is automatically filtered to focus strictly on the top 20% "core primitive" concepts required for upcoming tests.

### 5.2 Hysteresis Protection
To eliminate "flicker" (rapid toggling between Busy and Free modes when $W(t)$ hovers near the boundary):
- **Enter Busy Mode:** Requires $W(t) > 0.70$.
- **Exit Busy Mode:** Requires $W(t) < 0.55$.

### 5.3 Leech Detection
Cards failed repeatedly (4+ times) are flagged as "leeches." Instead of overwhelming the student with repeated failures during high-stress periods, leeches are automatically paused, simplified, or rewritten by the LLM.

### 5.4 Burnout Guard (B=MAP Micro-Tasks)
A rule-based monitoring layer detects high-risk conditions (e.g., 3+ major deadlines in 48 hours or zero free calendar slots for 2+ consecutive days).

Following BJ Fogg's behavior model ($B = MAP$), when motivation is depleted during peak stress, LearnSync lowers the cognitive barrier by issuing micro-prompts:
> *"Don't study for an hour today. Just complete this single 90-second code snippet."*

This prevents students from falling into guilt-driven doomscrolling loops when they feel too overwhelmed to start a full study session.

---

## 6. Technical Architecture

```
[ Docling Syllabus Parser ]   [ Google Calendar Sync ]   [ Gmail API (Scoped) ]
            │                            │                          │
            ▼                            ▼                          ▼
[ Virtual Folder DB ] ──────► [ Deadline / Event Store ] ◄──────────┘
 (PostgreSQL Hierarchy)                  │
            │                            ▼
            │               [ Workload Engine: W(t) ]
            │                            │
            │              ┌─────────────┴─────────────┐
            ▼              ▼                           ▼
[ Vector DB (Qdrant/PgVector) ]   [ FSRS Scheduler ]   [ Burnout Guard ]
  (Folder-scoped RRF Search)       (Elastic Retention)   (B=MAP Redirect)
            │                            │                     │
            └────────────────────────────┼─────────────────────┘
                                         ▼
                           [ Adaptive Dashboard & UI ]
```

### Stack Components:
- **Backend Framework:** FastAPI (Python 3.11+)
- **Database:** PostgreSQL with `pgvector` or Qdrant for vector retrieval; hierarchical table structure for Virtual Folders.
- **Parsing Engine:** Docling (IBM Research TableFormer model) with Vision-LLM fallback (Gemini 3 Flash).
- **Spaced Repetition:** `py-fsrs` wrapper library.
- **Frontend:** React / Next.js with Tailwind CSS, supporting Markdown rendering, SVG diagrams, and interactive code blocks.

---

## 7. Development Roadmap (14-Week Plan)

| Phase | Weeks | Deliverables |
|---|---|---|
| **Phase 1** | Weeks 1–2 | Virtual Folder DB schema + Docling syllabus PDF parser & folder-scoped vector embedding pipeline. |
| **Phase 2** | Weeks 3–4 | Google Calendar OAuth integration, event creation UI, and $W(t)$ workload calculation engine with hysteresis. |
| **Phase 3** | Weeks 5–6 | RAG generation pipeline supporting 4 learning styles (Visual, Auditory, Read/Write, Kinesthetic) + RRF hybrid search. |
| **Phase 4** | Weeks 7–8 | Scoped Gmail deadline change detection & manual event manager. |
| **Phase 5** | Weeks 9–10 | `py-fsrs` spaced repetition integration coupled with $W(t)$ + Leech detection algorithm. |
| **Phase 6** | Weeks 11–12 | Burnout Guard trigger rules + B=MAP micro-task UI & Feynman Loop feedback module. |
| **Phase 7** | Weeks 13–14 | User testing with real university students, parsing edge-case refinement, and telemetry analytics. |
