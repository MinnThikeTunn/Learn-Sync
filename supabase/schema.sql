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
    secondary_learning_style TEXT CHECK (secondary_learning_style IN ('visual', 'auditory', 'read_write', 'kinesthetic')),
    assessment_scores JSONB DEFAULT '{}'::jsonb,
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

-- Supporting Foreign Key & Query B-Tree Indexes
CREATE INDEX IF NOT EXISTS idx_courses_user ON public.courses(user_id);
CREATE INDEX IF NOT EXISTS idx_virtual_folders_user ON public.virtual_folders(user_id);
CREATE INDEX IF NOT EXISTS idx_virtual_folders_course ON public.virtual_folders(course_id);
CREATE INDEX IF NOT EXISTS idx_virtual_folders_parent ON public.virtual_folders(parent_id);
CREATE INDEX IF NOT EXISTS idx_documents_user ON public.documents(user_id);
CREATE INDEX IF NOT EXISTS idx_documents_course ON public.documents(course_id);
CREATE INDEX IF NOT EXISTS idx_documents_folder ON public.documents(folder_id);
CREATE INDEX IF NOT EXISTS idx_document_chunks_document ON public.document_chunks(document_id);
CREATE INDEX IF NOT EXISTS idx_document_chunks_folder ON public.document_chunks(folder_id);
CREATE INDEX IF NOT EXISTS idx_document_chunks_user ON public.document_chunks(user_id);
CREATE INDEX IF NOT EXISTS idx_events_user ON public.events(user_id);
CREATE INDEX IF NOT EXISTS idx_events_course ON public.events(course_id);
CREATE INDEX IF NOT EXISTS idx_events_user_time ON public.events(user_id, start_time);
CREATE INDEX IF NOT EXISTS idx_workload_logs_user ON public.workload_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_components_user ON public.knowledge_components(user_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_components_course ON public.knowledge_components(course_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_components_folder ON public.knowledge_components(folder_id);
CREATE INDEX IF NOT EXISTS idx_student_kc_mastery_kc ON public.student_kc_mastery(kc_id);
CREATE INDEX IF NOT EXISTS idx_flashcards_user_due ON public.flashcards(user_id, due);
CREATE INDEX IF NOT EXISTS idx_flashcards_folder ON public.flashcards(folder_id);
CREATE INDEX IF NOT EXISTS idx_flashcards_kc ON public.flashcards(kc_id);
CREATE INDEX IF NOT EXISTS idx_review_logs_user ON public.review_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_review_logs_flashcard ON public.review_logs(flashcard_id);
CREATE INDEX IF NOT EXISTS idx_burnout_triggers_user ON public.burnout_triggers(user_id);

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

-- Helper macro for standard user_id RLS policies (using (select auth.uid()) for InitPlan optimization)
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
            DROP POLICY IF EXISTS "Users can view their own %1$s" ON public.%1$I;
            CREATE POLICY "Users can view their own %1$s" 
            ON public.%1$I FOR SELECT USING ((select auth.uid()) = user_id);
            
            DROP POLICY IF EXISTS "Users can insert their own %1$s" ON public.%1$I;
            CREATE POLICY "Users can insert their own %1$s" 
            ON public.%1$I FOR INSERT WITH CHECK ((select auth.uid()) = user_id);
            
            DROP POLICY IF EXISTS "Users can update their own %1$s" ON public.%1$I;
            CREATE POLICY "Users can update their own %1$s" 
            ON public.%1$I FOR UPDATE USING ((select auth.uid()) = user_id) WITH CHECK ((select auth.uid()) = user_id);
            
            DROP POLICY IF EXISTS "Users can delete their own %1$s" ON public.%1$I;
            CREATE POLICY "Users can delete their own %1$s" 
            ON public.%1$I FOR DELETE USING ((select auth.uid()) = user_id);
        ', t);
    END LOOP;
END $$;

-- Profile RLS (id = (select auth.uid()))
DROP POLICY IF EXISTS "Users can view own profile" ON public.profiles;
CREATE POLICY "Users can view own profile" ON public.profiles FOR SELECT USING ((select auth.uid()) = id);

DROP POLICY IF EXISTS "Users can insert own profile" ON public.profiles;
CREATE POLICY "Users can insert own profile" ON public.profiles FOR INSERT WITH CHECK ((select auth.uid()) = id);

DROP POLICY IF EXISTS "Users can update own profile" ON public.profiles;
CREATE POLICY "Users can update own profile" ON public.profiles FOR UPDATE USING ((select auth.uid()) = id) WITH CHECK ((select auth.uid()) = id);

-- 4.1 Automatic Profile Provisioning Trigger on auth.users
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS trigger
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public, auth
AS $$
BEGIN
    INSERT INTO public.profiles (id, email, full_name, learning_style, target_retention, onboarding_completed)
    VALUES (
        NEW.id,
        NEW.email,
        COALESCE(NEW.raw_user_meta_data->>'full_name', NEW.raw_user_meta_data->>'name', split_part(NEW.email, '@', 1)),
        'read_write',
        0.90,
        FALSE
    )
    ON CONFLICT (id) DO NOTHING;
    RETURN NEW;
END;
$$;

REVOKE EXECUTE ON FUNCTION public.handle_new_user() FROM PUBLIC, anon, authenticated;

DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

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
SECURITY INVOKER
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
            dc.document_id,
            dc.folder_id,
            dc.content,
            similarity(dc.content, query_text)::REAL AS sparse_sim,
            ROW_NUMBER() OVER (ORDER BY similarity(dc.content, query_text) DESC) AS sparse_rank
        FROM public.document_chunks dc
        WHERE dc.folder_id = p_folder_id
          AND dc.user_id = p_user_id
        LIMIT match_count * 3
    )
    SELECT
        COALESCE(d.id, s.id) AS id,
        COALESCE(d.document_id, s.document_id) AS document_id,
        COALESCE(d.folder_id, s.folder_id) AS folder_id,
        COALESCE(d.content, s.content) AS content,
        COALESCE(d.cosine_sim, 0.0)::REAL AS cosine_similarity,
        COALESCE(s.sparse_sim, 0.0)::REAL AS sparse_score,
        (
            (1.0 / (k + COALESCE(d.dense_rank, 1000))) + 
            (1.0 / (k + COALESCE(s.sparse_rank, 1000)))
        )::REAL AS rrf_score
    FROM dense_search d
    FULL OUTER JOIN sparse_search s ON d.id = s.id
    ORDER BY rrf_score DESC
    LIMIT match_count;
END;
$$;

REVOKE EXECUTE ON FUNCTION public.match_folder_chunks(VECTOR(1536), TEXT, UUID, UUID, INTEGER, INTEGER) FROM anon;
GRANT EXECUTE ON FUNCTION public.match_folder_chunks(VECTOR(1536), TEXT, UUID, UUID, INTEGER, INTEGER) TO authenticated;

