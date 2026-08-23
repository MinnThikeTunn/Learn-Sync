# 01: Supabase Backend Schema & Folder-Scoped Vector RPC Initialization

**What to build:**
Set up the complete Supabase PostgreSQL database schema with Row Level Security (RLS) policies and pgvector extensions. Implement the `match_folder_chunks` RPC function that performs folder-scoped Reciprocal Rank Fusion (RRF) combining dense cosine similarity and sparse trigram keyword matching.

**Blocked by:** None (can start immediately)

**Status:** done

- [x] Supabase schema initialized with all 11 core tables (`profiles`, `courses`, `virtual_folders`, `documents`, `document_chunks`, `events`, `workload_logs`, `knowledge_components`, `student_kc_mastery`, `flashcards`, `review_logs`, `burnout_triggers`).
- [x] RLS policies enabled ensuring complete tenant data isolation based on `auth.uid() = user_id`.
- [x] `pgvector` HNSW cosine vector index configured on `document_chunks (embedding vector_cosine_ops)`.
- [x] Stored procedure `match_folder_chunks` deployed and verified with RRF scoring ($k=60$) constrained by `folder_id` and `user_id`.
- [x] Integration tests verify table migrations and RPC function execution on dummy embeddings.
