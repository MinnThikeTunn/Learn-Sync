import math
import pytest
from backend.app.core.supabase import SupabaseVectorClient


def test_cosine_similarity_identical_vectors():
    """Identical vectors should have cosine similarity of 1.0."""
    v = [1.0, 2.0, 3.0]
    sim = SupabaseVectorClient.cosine_similarity(v, v)
    assert math.isclose(sim, 1.0, rel_tol=1e-5)


def test_cosine_similarity_orthogonal_vectors():
    """Orthogonal vectors should have cosine similarity of 0.0."""
    v1 = [1.0, 0.0, 0.0]
    v2 = [0.0, 1.0, 0.0]
    sim = SupabaseVectorClient.cosine_similarity(v1, v2)
    assert math.isclose(sim, 0.0, abs_tol=1e-5)


def test_trigram_similarity_exact_match():
    """Identical text strings should yield high trigram similarity."""
    text = "Recursion is a process where a function calls itself."
    sim = SupabaseVectorClient.trigram_similarity(text, text)
    assert math.isclose(sim, 1.0, rel_tol=1e-5)


def test_trigram_similarity_disjoint_text():
    """Completely disjoint text strings should have 0.0 trigram similarity."""
    text1 = "aaaa"
    text2 = "zzzz"
    sim = SupabaseVectorClient.trigram_similarity(text1, text2)
    assert sim == 0.0


def test_reciprocal_rank_fusion_ranking():
    """
    Verify that RRF combines dense and sparse ranks correctly with k=60:
    RRF = 1 / (60 + dense_rank) + 1 / (60 + sparse_rank)
    """
    dummy_chunks = [
        {
            "id": "c1",
            "document_id": "d1",
            "folder_id": "f1",
            "content": "Recursion base case and recursive step in Python.",
            "embedding": [0.9, 0.1, 0.0]
        },
        {
            "id": "c2",
            "document_id": "d1",
            "folder_id": "f1",
            "content": "Graph traversal using Breadth First Search.",
            "embedding": [0.1, 0.9, 0.0]
        },
        {
            "id": "c3",
            "document_id": "d1",
            "folder_id": "f1",
            "content": "Recursion and call stack overflow prevention.",
            "embedding": [0.85, 0.15, 0.0]
        }
    ]

    query_embedding = [1.0, 0.0, 0.0]
    query_text = "Recursion base case"

    results = SupabaseVectorClient.reciprocal_rank_fusion(
        chunks=dummy_chunks,
        query_embedding=query_embedding,
        query_text=query_text,
        match_count=3,
        k=60
    )

    assert len(results) == 3
    # c1 is rank 1 in both dense and sparse, so should have highest RRF score: 1/61 + 1/61 = 2/61 ≈ 0.03278
    top_result = results[0]
    assert top_result["id"] == "c1"
    expected_top_rrf = (1.0 / (60 + 1)) + (1.0 / (60 + 1))
    assert math.isclose(top_result["rrf_score"], expected_top_rrf, rel_tol=1e-3)
    assert results[0]["rrf_score"] > results[1]["rrf_score"] > results[2]["rrf_score"]
