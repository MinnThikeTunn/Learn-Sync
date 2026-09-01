import os
import pytest

SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "supabase", "schema.sql")


def test_schema_file_exists():
    """Verify that the schema.sql file exists and is populated."""
    assert os.path.exists(SCHEMA_PATH), f"Schema file not found at {SCHEMA_PATH}"
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        content = f.read()
    assert len(content) > 500, "Schema file is suspiciously empty"


def test_schema_contains_all_core_tables():
    """Verify all 12 core database tables are declared in schema.sql."""
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    expected_tables = [
        "profiles",
        "courses",
        "virtual_folders",
        "documents",
        "document_chunks",
        "events",
        "workload_logs",
        "knowledge_components",
        "student_kc_mastery",
        "flashcards",
        "review_logs",
        "burnout_triggers"
    ]

    for table in expected_tables:
        assert f"CREATE TABLE IF NOT EXISTS public.{table}" in content, f"Table public.{table} missing from schema"

    assert "secondary_learning_style TEXT CHECK" in content
    assert "assessment_scores JSONB" in content


def test_schema_extensions_and_indexes():
    """Verify pgvector, pg_trgm, uuid-ossp extensions and HNSW/GIN indexes are declared."""
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    assert 'CREATE EXTENSION IF NOT EXISTS "uuid-ossp"' in content
    assert 'CREATE EXTENSION IF NOT EXISTS "vector"' in content
    assert 'CREATE EXTENSION IF NOT EXISTS "pg_trgm"' in content
    assert "USING hnsw (embedding vector_cosine_ops)" in content
    assert "USING gin (content gin_trgm_ops)" in content


def test_schema_rls_enabled_and_policies():
    """Verify Row Level Security (RLS) is enabled and user_id isolation policies are configured."""
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    tables = [
        "profiles", "courses", "virtual_folders", "documents", "document_chunks",
        "events", "workload_logs", "knowledge_components", "student_kc_mastery",
        "flashcards", "review_logs", "burnout_triggers"
    ]

    for table in tables:
        assert f"ALTER TABLE public.{table} ENABLE ROW LEVEL SECURITY;" in content

    assert "auth.uid() = user_id" in content or "(select auth.uid()) = user_id" in content
    assert "auth.uid() = id" in content or "(select auth.uid()) = id" in content  # For profiles


def test_schema_match_folder_chunks_rpc_defined():
    """Verify stored procedure match_folder_chunks is declared with RRF ranking."""
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    assert "CREATE OR REPLACE FUNCTION public.match_folder_chunks" in content
    assert "query_embedding VECTOR(1536)" in content
    assert "query_text TEXT" in content
    assert "p_folder_id UUID" in content
    assert "p_user_id UUID" in content
    assert "k INTEGER DEFAULT 60" in content
    assert "cosine_similarity" in content
    assert "rrf_score" in content
