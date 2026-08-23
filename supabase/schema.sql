-- =====================================================================
-- LearnSync AI: Supabase PostgreSQL Schema & Vector RPC
-- Platform: Supabase (PostgreSQL 15+ with pgvector & pg_trgm)
-- =====================================================================

-- 1. Enable Required Extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- 2. Core Tables Definitions

-- 2.1 Profiles (Extends auth.users with student learning preferences)
CREATE TABLE IF NOT EXISTS public.profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email TEXT UNIQUE NOT NULL,
    full_name TEXT,
    learning_style TEXT CHECK (learning_style IN ('visual', 'auditory', 'read_write', 'kinesthetic')) DEFAULT 'read_write',
    target_retention REAL DEFAULT 0.90 CHECK (target_retention > 0.0 AND target_retention <= 1.0),
    onboarding_completed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2.2 Courses (Container for academic courses)
CREATE TABLE IF NOT EXISTS public.courses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    code TEXT NOT NULL,
    term TEXT,
    color TEXT DEFAULT '#3b82f6',
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2.3 Virtual Folders (Hierarchical folder tree with materialized paths)
CREATE TABLE IF NOT EXISTS public.virtual_folders (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    course_id UUID NOT NULL REFERENCES public.courses(id) ON DELETE CASCADE,
    parent_id UUID REFERENCES public.virtual_folders(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    materialized_path TEXT NOT NULL,
    depth INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT uq_user_course_path UNIQUE (user_id, course_id, materialized_path)
);

-- 2.4 Documents (Uploaded syllabus, slides, and notes)
CREATE TABLE IF NOT EXISTS public.documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    course_id UUID NOT NULL REFERENCES public.courses(id) ON DELETE CASCADE,
    folder_id UUID REFERENCES public.virtual_folders(id) ON DELETE SET NULL,
    file_name TEXT NOT NULL,
    storage_path TEXT NOT NULL,
    file_type TEXT NOT NULL,
    file_size_bytes BIGINT DEFAULT 0,
    status TEXT CHECK (status IN ('pending', 'parsing', 'chunked', 'indexed', 'failed')) DEFAULT 'pending',
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2.5 Document Chunks (500-token blocks with 1536-dim vector embeddings)
CREATE TABLE IF NOT EXISTS public.document_chunks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    document_id UUID NOT NULL REFERENCES public.documents(id) ON DELETE CASCADE,
    folder_id UUID NOT NULL REFERENCES public.virtual_folders(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    token_count INTEGER NOT NULL DEFAULT 0,
    embedding VECTOR(1536),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2.6 Events (Deadlines, exams, and calendar events)
CREATE TABLE IF NOT EXISTS public.events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    course_id UUID REFERENCES public.courses(id) ON DELETE SET NULL,
    title TEXT NOT NULL,
    event_type TEXT CHECK (event_type IN ('exam', 'assignment', 'quiz', 'lecture', 'project', 'other')) DEFAULT 'assignment',
    start_time TIMESTAMPTZ NOT NULL,
    end_time TIMESTAMPTZ,
    weight REAL DEFAULT 1.0 CHECK (weight >= 0.0),
    is_completed BOOLEAN DEFAULT FALSE,
    source TEXT CHECK (source IN ('syllabus', 'google_calendar', 'manual')) DEFAULT 'manual',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2.7 Workload Logs (Rolling Workload Score W(t) and active mode telemetry)
CREATE TABLE IF NOT EXISTS public.workload_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    score REAL NOT NULL CHECK (score >= 0.0 AND score <= 1.0),
    mode TEXT NOT NULL CHECK (mode IN ('free', 'busy', 'hysteresis_hold')),
    lookahead_days INTEGER NOT NULL DEFAULT 3,
    active_event_count INTEGER NOT NULL DEFAULT 0,
    recorded_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2.8 Knowledge Components (Curriculum atomic units for BKT tracking)
CREATE TABLE IF NOT EXISTS public.knowledge_components (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    course_id UUID NOT NULL REFERENCES public.courses(id) ON DELETE CASCADE,
    folder_id UUID REFERENCES public.virtual_folders(id) ON DELETE SET NULL,
    name TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2.9 Student KC Mastery (Bayesian Knowledge Tracing real-time mastery states)
CREATE TABLE IF NOT EXISTS public.student_kc_mastery (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    kc_id UUID NOT NULL REFERENCES public.knowledge_components(id) ON DELETE CASCADE,
    p_l REAL NOT NULL DEFAULT 0.10 CHECK (p_l >= 0.0 AND p_l <= 1.0),
    p_transit REAL NOT NULL DEFAULT 0.15 CHECK (p_transit >= 0.0 AND p_transit <= 1.0),
    p_guess REAL NOT NULL DEFAULT 0.20 CHECK (p_guess >= 0.0 AND p_guess <= 1.0),
    p_slip REAL NOT NULL DEFAULT 0.10 CHECK (p_slip >= 0.0 AND p_slip <= 1.0),
    total_attempts INTEGER NOT NULL DEFAULT 0,
    correct_attempts INTEGER NOT NULL DEFAULT 0,
    last_updated_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT uq_user_kc UNIQUE (user_id, kc_id)
);

-- 2.10 Flashcards (Spaced repetition cards tracked via py-fsrs)
CREATE TABLE IF NOT EXISTS public.flashcards (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    folder_id UUID NOT NULL REFERENCES public.virtual_folders(id) ON DELETE CASCADE,
    kc_id UUID REFERENCES public.knowledge_components(id) ON DELETE SET NULL,
    front TEXT NOT NULL,
    back TEXT NOT NULL,
    stability REAL NOT NULL DEFAULT 0.0,
    difficulty REAL NOT NULL DEFAULT 0.0,
    reps INTEGER NOT NULL DEFAULT 0,
    lapses INTEGER NOT NULL DEFAULT 0,
    state INTEGER NOT NULL DEFAULT 0, -- 0=New, 1=Learning, 2=Review, 3=Relearning
    is_leech BOOLEAN NOT NULL DEFAULT FALSE,
    is_paused BOOLEAN NOT NULL DEFAULT FALSE,
    due TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_review TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2.11 Review Logs (Telemetry logs of review ratings and retention timings)
CREATE TABLE IF NOT EXISTS public.review_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    flashcard_id UUID NOT NULL REFERENCES public.flashcards(id) ON DELETE CASCADE,
    rating INTEGER NOT NULL CHECK (rating IN (1, 2, 3, 4)), -- 1=Again, 2=Hard, 3=Good, 4=Easy
    state INTEGER NOT NULL,
    elapsed_days REAL NOT NULL DEFAULT 0.0,
    scheduled_days REAL NOT NULL DEFAULT 0.0,
    review_time TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 2.12 Burnout Triggers (B=MAP 90-second micro-interventions)
CREATE TABLE IF NOT EXISTS public.burnout_triggers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    trigger_reason TEXT NOT NULL,
    micro_task_prompt TEXT NOT NULL,
    duration_seconds INTEGER NOT NULL DEFAULT 90,
    is_completed BOOLEAN NOT NULL DEFAULT FALSE,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- =====================================================================
-- 3. Indexes & Constraints
-- =====================================================================

-- HNSW Cosine vector index for fast semantic retrieval
CREATE INDEX IF NOT EXISTS idx_document_chunks_embedding_hnsw
ON public.document_chunks
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- Trigram GIN index on content for sparse lexical matching
CREATE INDEX IF NOT EXISTS idx_document_chunks_content_trgm
ON public.document_chunks
USING gin (content gin_trgm_ops);

-- Supporting B-Tree Indexes
CREATE INDEX IF NOT EXISTS idx_virtual_folders_course ON public.virtual_folders(course_id);
CREATE INDEX IF NOT EXISTS idx_virtual_folders_parent ON public.virtual_folders(parent_id);
CREATE INDEX IF NOT EXISTS idx_document_chunks_folder ON public.document_chunks(folder_id);
CREATE INDEX IF NOT EXISTS idx_document_chunks_user ON public.document_chunks(user_id);
CREATE INDEX IF NOT EXISTS idx_events_user_time ON public.events(user_id, start_time);
CREATE INDEX IF NOT EXISTS idx_flashcards_user_due ON public.flashcards(user_id, due);
CREATE INDEX IF NOT EXISTS idx_flashcards_folder ON public.flashcards(folder_id);

-- =====================================================================
-- 4. Row Level Security (RLS) Policies
-- =====================================================================

ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.courses ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.virtual_folders ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.document_chunks ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.events ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.workload_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.knowledge_components ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.student_kc_mastery ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.flashcards ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.review_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.burnout_triggers ENABLE ROW LEVEL SECURITY;

-- Helper macro for standard user_id RLS policies
DO $$
DECLARE
    t text;
BEGIN
    FOR t IN 
        SELECT unnest(ARRAY[
            'courses', 'virtual_folders', 'documents', 'document_chunks',
            'events', 'workload_logs', 'knowledge_components', 
            'student_kc_mastery', 'flashcards', 'review_logs', 'burnout_triggers'
        ])
    LOOP
        EXECUTE format('
            CREATE POLICY "Users can view their own %1$I" 
            ON public.%1$I FOR SELECT USING (auth.uid() = user_id);
            
            CREATE POLICY "Users can insert their own %1$I" 
            ON public.%1$I FOR INSERT WITH CHECK (auth.uid() = user_id);
            
            CREATE POLICY "Users can update their own %1$I" 
            ON public.%1$I FOR UPDATE USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);
            
            CREATE POLICY "Users can delete their own %1$I" 
            ON public.%1$I FOR DELETE USING (auth.uid() = user_id);
        ', t);
    END LOOP;
END $$;

-- Profile RLS (id = auth.uid())
CREATE POLICY "Users can view own profile" ON public.profiles FOR SELECT USING (auth.uid() = id);
CREATE POLICY "Users can insert own profile" ON public.profiles FOR INSERT WITH CHECK (auth.uid() = id);
CREATE POLICY "Users can update own profile" ON public.profiles FOR UPDATE USING (auth.uid() = id) WITH CHECK (auth.uid() = id);

-- =====================================================================
-- 5. Stored Procedure: Folder-Scoped Reciprocal Rank Fusion (RRF)
-- =====================================================================

CREATE OR REPLACE FUNCTION public.match_folder_chunks(
    query_embedding VECTOR(1536),
    query_text TEXT,
    p_folder_id UUID,
    p_user_id UUID,
    match_count INTEGER DEFAULT 5,
    k INTEGER DEFAULT 60
)
RETURNS TABLE (
    id UUID,
    document_id UUID,
    folder_id UUID,
    content TEXT,
    cosine_similarity REAL,
    sparse_score REAL,
    rrf_score REAL
)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public, extensions
AS $$
BEGIN
    RETURN QUERY
    WITH dense_search AS (
        SELECT 
            dc.id,
            dc.document_id,
            dc.folder_id,
            dc.content,
            (1.0 - (dc.embedding <=> query_embedding))::REAL AS cosine_sim,
            ROW_NUMBER() OVER (ORDER BY dc.embedding <=> query_embedding ASC) AS dense_rank
        FROM public.document_chunks dc
        WHERE dc.folder_id = p_folder_id
          AND dc.user_id = p_user_id
          AND dc.embedding IS NOT NULL
        LIMIT match_count * 3
    ),
    sparse_search AS (
        SELECT 
            dc.id,
            similarity(dc.content, query_text)::REAL AS sparse_sim,
            ROW_NUMBER() OVER (ORDER BY similarity(dc.content, query_text) DESC) AS sparse_rank
        FROM public.document_chunks dc
        WHERE dc.folder_id = p_folder_id
          AND dc.user_id = p_user_id
        LIMIT match_count * 3
    )
    SELECT
        d.id,
        d.document_id,
        d.folder_id,
        d.content,
        d.cosine_sim AS cosine_similarity,
        COALESCE(s.sparse_sim, 0.0)::REAL AS sparse_score,
        (
            (1.0 / (k + d.dense_rank)) + 
            (1.0 / (k + COALESCE(s.sparse_rank, 1000)))
        )::REAL AS rrf_score
    FROM dense_search d
    LEFT JOIN sparse_search s ON d.id = s.id
    ORDER BY rrf_score DESC
    LIMIT match_count;
END;
$$;
