# LearnSync AI - Sequence Diagram

This document models the end-to-end operational sequence of **LearnSync AI**, capturing the interactions across ingestion, workload scoring, grounded hybrid RAG generation, active recall (Feynman Loop), and elastic spaced repetition (FSRS) with **Supabase (PostgreSQL 16 + pgvector + RLS)**.

```mermaid
sequenceDiagram
    autonumber
    actor Student
    participant UI as Frontend Client (React / Next.js)
    participant Ingestion as Ingestion Service (Docling / GCal / Gmail)
    participant Workload as Workload & Hysteresis Engine
    participant Adaptive as Adaptive Learning Engine
    participant RAG as Grounded RAG (RRF Search)
    participant FSRS as Elastic FSRS Scheduler
    participant Supabase as Supabase (PostgreSQL 16 + pgvector + RLS)

    %% ========================================================
    %% 1. Ingestion & Workload Score W(t) Computation
    %% ========================================================
    rect rgb(240, 249, 255)
        Note over Student, Supabase: 1. Event Ingestion & Workload Score W(t) Evaluation
        Ingestion->>Supabase: Ingest syllabus schedule, GCal events & Gmail deadline shifts
        Supabase-->>Workload: Trigger deadline update event
        Workload->>Supabase: Fetch 3-day rolling lookahead deadlines & weights
        Workload->>Workload: Compute Workload Score W(t) in [0.0, 1.0]
        
        alt W(t) > 0.70 (High Workload Threshold)
            Workload->>Workload: Transition to BUSY_MODE
        else W(t) <= 0.55 (Low Workload Threshold)
            Workload->>Workload: Transition to FREE_MODE
        else 0.55 < W(t) <= 0.70 (Hysteresis Dead-Band)
            Workload->>Workload: Retain active mode (prevent rapid oscillation)
        end
        
        Workload->>Supabase: Persist W(t) log & mode transition (workload_logs)
        Workload-->>UI: Push live mode state (Free Mode / Busy Mode)
    end

    %% ========================================================
    %% 2. Context-Aware Grounded RAG Generation
    %% ========================================================
    rect rgb(240, 253, 244)
        Note over Student, Supabase: 2. Folder-Scoped Hybrid RAG Generation
        Student->>UI: Request study module for selected Virtual Folder
        UI->>Adaptive: Request study content (folder_id, LearningStyle, activeMode)
        
        Adaptive->>RAG: Query folder scope (query_text, folder_id)
        RAG->>Supabase: Execute match_folder_chunks RPC (RRF dense <=> + sparse %)
        Supabase-->>RAG: Return top-K folder-scoped document chunks
        RAG-->>Adaptive: Grounded source context
        
        alt Active Mode == FREE_MODE (W(t) <= 0.55)
            Adaptive->>Adaptive: Synthesize comprehensive artifacts (Mermaid diagrams, Socratic podcasts, code labs)
        else Active Mode == BUSY_MODE (W(t) > 0.70)
            Adaptive->>Adaptive: Apply Pareto 80/20 filter (generate cheat-sheets, 30s audio recaps, micro-tasks)
        end
        
        Adaptive-->>UI: Deliver personalized study artifact
        UI-->>Student: Render interactive view tailored to learning style & mode
    end

    %% ========================================================
    %% 3. Active Recall & Feynman Loop
    %% ========================================================
    rect rgb(254, 249, 195)
        Note over Student, Supabase: 3. Active Recall & Feynman Loop Gap Analysis
        UI->>Student: Prompt plain-language Feynman explanation
        Student->>UI: Submit conceptual explanation in own words
        UI->>Adaptive: Evaluate explanation against folder source material
        Adaptive->>Adaptive: Precision-Gap analysis (detect missing concepts & misconceptions)
        Adaptive->>Supabase: Spawn new localized flashcards targeted at detected gaps
        Adaptive-->>UI: Display gap feedback & reinforcement prompt
    end

    %% ========================================================
    %% 4. Elastic Spaced Repetition (py-fsrs) & Leech Protection
    %% ========================================================
    rect rgb(253, 242, 248)
        Note over Student, Supabase: 4. Elastic Spaced Repetition (FSRS) & Leech Handling
        Student->>UI: Submit flashcard rating (Again, Hard, Good, Easy)
        UI->>FSRS: Submit review outcome (card_id, rating, activeMode)
        
        alt Active Mode == BUSY_MODE
            FSRS->>FSRS: Lower target retention R_c to 80% (expand intervals by 1.75x)
        else Active Mode == FREE_MODE
            FSRS->>FSRS: Standard retention target R_c = 90%
        end
        
        FSRS->>Supabase: Update card stability, difficulty & due_date (flashcards)
        FSRS->>Supabase: Insert review log record (review_logs)
        
        alt Card failure_count >= 4
            FSRS->>Supabase: Flag card as Leech and pause from active review queue
            FSRS-->>UI: Notify leech detected -> propose LLM card simplification
        end
        
        FSRS-->>UI: Return updated review deck status
    end
```

## Sequence Workflow Analysis

1. **Continuous Workload Evaluation**: When events shift, the [Workload Engine](file:///D:/learnSync/CONTEXT.md#L7-L10) computes $W(t)$ and navigates the [Hysteresis Dead-Band](file:///D:/learnSync/CONTEXT.md#L19-L22) ($0.55 < W(t) \le 0.70$) without jarring transitions.
2. **Folder-Scoped Hybrid [RRF Search](file:///D:/learnSync/CONTEXT.md#L39-L42)**: RAG searches are scoped to the active [Virtual Folder](file:///D:/learnSync/CONTEXT.md#L23-L26), querying Supabase via the `match_folder_chunks` RPC function combining dense cosine similarity (`vector_cosine_ops`) with trigram sparse matching (`pg_trgm`).
3. **The Feynman Active Recall Loop**: Student explanations are compared against the source corpus to identify precision gaps and automatically construct targeted flashcards.
4. **Elastic Spaced Repetition**: Flashcard reviews dynamically scale retention targets and interval multipliers based on active workload modes, automatically pausing chronic failures via [Leech Detection](file:///D:/learnSync/CONTEXT.md#L31-L34).
