import math
from typing import Any, Dict, List, Optional
from uuid import UUID
from backend.app.core.config import settings


class SupabaseVectorClient:
    """
    Client for interacting with Supabase database and vector RPC functions.
    Includes a reference implementation of Reciprocal Rank Fusion (RRF) matching 
    the PostgreSQL match_folder_chunks stored procedure.
    """

    def __init__(self, url: Optional[str] = None, key: Optional[str] = None):
        self.url = url or settings.SUPABASE_URL
        self.key = key or settings.SUPABASE_KEY
        self._client = None

    @property
    def client(self):
        if self._client is None:
            try:
                from supabase import create_client, ClientOptions
                options = ClientOptions(postgrest_client_timeout=3.0, storage_client_timeout=3.0)
                self._client = create_client(self.url, self.key, options=options)
            except Exception:
                try:
                    from supabase import create_client
                    self._client = create_client(self.url, self.key)
                except Exception:
                    self._client = None
        return self._client

    @staticmethod
    def cosine_similarity(v1: List[float], v2: List[float]) -> float:
        """Computes cosine similarity between two float vectors."""
        if not v1 or not v2 or len(v1) != len(v2):
            return 0.0
        dot_product = sum(a * b for a, b in zip(v1, v2))
        norm_a = math.sqrt(sum(a * a for a in v1))
        norm_b = math.sqrt(sum(b * b for b in v2))
        if norm_a == 0.0 or norm_b == 0.0:
            return 0.0
        return dot_product / (norm_a * norm_b)

    @staticmethod
    def trigram_similarity(text1: str, text2: str) -> float:
        """
        Computes 3-gram Jaccard/Dice similarity between text1 and text2,
        matching PostgreSQL pg_trgm similarity behavior.
        """
        def get_trigrams(s: str) -> set:
            s_pad = f"  {s.lower()} "
            return {s_pad[i:i+3] for i in range(len(s_pad) - 2)}

        tri1 = get_trigrams(text1)
        tri2 = get_trigrams(text2)
        if not tri1 or not tri2:
            return 0.0
        intersection = len(tri1 & tri2)
        union = len(tri1 | tri2)
        return intersection / union if union > 0 else 0.0

    @classmethod
    def reciprocal_rank_fusion(
        cls,
        chunks: List[Dict[str, Any]],
        query_embedding: List[float],
        query_text: str,
        match_count: int = 5,
        k: int = 60
    ) -> List[Dict[str, Any]]:
        """
        Executes Reciprocal Rank Fusion (RRF) over chunks:
        RRF_Score = 1 / (k + dense_rank) + 1 / (k + sparse_rank)
        """
        if not chunks:
            return []

        # 1. Dense Scoring
        scored_dense = []
        for c in chunks:
            sim = cls.cosine_similarity(c.get("embedding", []), query_embedding)
            scored_dense.append((c, sim))
        scored_dense.sort(key=lambda x: x[1], reverse=True)

        dense_rank_map = {}
        for rank_idx, (chunk, sim) in enumerate(scored_dense, start=1):
            dense_rank_map[chunk["id"]] = (rank_idx, sim)

        # 2. Sparse Scoring
        scored_sparse = []
        for c in chunks:
            sparse_sim = cls.trigram_similarity(c.get("content", ""), query_text)
            scored_sparse.append((c, sparse_sim))
        scored_sparse.sort(key=lambda x: x[1], reverse=True)

        sparse_rank_map = {}
        for rank_idx, (chunk, sim) in enumerate(scored_sparse, start=1):
            sparse_rank_map[chunk["id"]] = (rank_idx, sim)

        # 3. Combine with RRF
        fused_results = []
        for c in chunks:
            chunk_id = c["id"]
            dense_rank, dense_sim = dense_rank_map.get(chunk_id, (1000, 0.0))
            sparse_rank, sparse_sim = sparse_rank_map.get(chunk_id, (1000, 0.0))
            rrf_score = (1.0 / (k + dense_rank)) + (1.0 / (k + sparse_rank))
            fused_results.append({
                "id": chunk_id,
                "document_id": c.get("document_id"),
                "folder_id": c.get("folder_id"),
                "content": c.get("content"),
                "cosine_similarity": float(dense_sim),
                "sparse_score": float(sparse_sim),
                "rrf_score": float(rrf_score)
            })

        fused_results.sort(key=lambda x: x["rrf_score"], reverse=True)
        return fused_results[:match_count]

    def match_folder_chunks(
        self,
        query_embedding: List[float],
        query_text: str,
        folder_id: str,
        user_id: str,
        match_count: int = 5,
        k: int = 60
    ) -> List[Dict[str, Any]]:
        """
        Calls the PostgreSQL match_folder_chunks RPC on Supabase.
        """
        if self.client is not None:
            response = self.client.rpc(
                "match_folder_chunks",
                {
                    "query_embedding": query_embedding,
                    "query_text": query_text,
                    "p_folder_id": str(folder_id),
                    "p_user_id": str(user_id),
                    "match_count": match_count,
                    "k": k
                }
            ).execute()
            return response.data
        return []
