import re
from typing import Any, Dict, List, Optional
from uuid import UUID
from datetime import datetime, timezone, timedelta
from backend.app.core.supabase import SupabaseVectorClient


class DatabaseService:
    """
    Central repository service interfacing with Supabase tables:
    - virtual_folders
    - documents & document_chunks
    - events & workload_logs
    - flashcards & review_logs
    - knowledge_components & student_kc_mastery
    """

    def __init__(self, supabase_client: Optional[SupabaseVectorClient] = None):
        self.supabase = supabase_client or SupabaseVectorClient()

    @staticmethod
    def calculate_materialized_path(parent_path: str, folder_name: str) -> str:
        clean_name = re.sub(r"[^\w\-_]", "_", folder_name.strip())
        parent_clean = parent_path.rstrip("/") if parent_path else ""
        return f"{parent_clean}/{clean_name}"

    def create_virtual_folder(
        self,
        user_id: UUID,
        course_id: UUID,
        name: str,
        parent_id: Optional[UUID] = None,
        parent_path: str = "",
        parent_depth: int = 0
    ) -> Dict[str, Any]:
        materialized_path = self.calculate_materialized_path(parent_path, name)
        depth = parent_depth + 1 if parent_path else 0

        record = {
            "user_id": str(user_id),
            "course_id": str(course_id),
            "name": name,
            "parent_id": str(parent_id) if parent_id else None,
            "materialized_path": materialized_path,
            "depth": depth,
        }

        if self.supabase.client:
            res = self.supabase.client.table("virtual_folders").insert(record).execute()
            if res.data and len(res.data) > 0:
                return res.data[0]
        return record

    def get_virtual_folders(self, user_id: UUID, course_id: Optional[UUID] = None) -> List[Dict[str, Any]]:
        if not self.supabase.client:
            return []
        query = self.supabase.client.table("virtual_folders").select("*").eq("user_id", str(user_id))
        if course_id:
            query = query.eq("course_id", str(course_id))
        res = query.order("materialized_path").execute()
        return res.data or []

    def insert_events(self, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if not events or not self.supabase.client:
            return []
        res = self.supabase.client.table("events").insert(events).execute()
        return res.data or []

    def get_upcoming_events(self, user_id: UUID, days_ahead: int = 3) -> List[Dict[str, Any]]:
        if not self.supabase.client:
            return []
        now = datetime.now(timezone.utc)
        horizon = now + timedelta(days=days_ahead)
        res = (
            self.supabase.client.table("events")
            .select("*")
            .eq("user_id", str(user_id))
            .gte("start_time", now.isoformat())
            .lte("start_time", horizon.isoformat())
            .order("start_time")
            .execute()
        )
        return res.data or []

    def get_due_flashcards(
        self,
        user_id: UUID,
        folder_id: Optional[UUID] = None,
        limit: int = 30
    ) -> List[Dict[str, Any]]:
        if not self.supabase.client:
            return []
        now = datetime.now(timezone.utc)
        query = (
            self.supabase.client.table("flashcards")
            .select("*")
            .eq("user_id", str(user_id))
            .lte("due", now.isoformat())
            .eq("is_paused", False)
        )
        if folder_id:
            query = query.eq("folder_id", str(folder_id))
        res = query.order("due").limit(limit).execute()
        return res.data or []

    def update_flashcard_state(
        self,
        flashcard_id: UUID,
        stability: float,
        difficulty: float,
        due: datetime,
        lapses: int,
        is_leech: bool,
        is_paused: bool = False
    ) -> Optional[Dict[str, Any]]:
        if not self.supabase.client:
            return None
        res = (
            self.supabase.client.table("flashcards")
            .update({
                "stability": stability,
                "difficulty": difficulty,
                "due": due.isoformat(),
                "lapses": lapses,
                "is_leech": is_leech,
                "is_paused": is_paused,
                "updated_at": datetime.now(timezone.utc).isoformat(),
            })
            .eq("id", str(flashcard_id))
            .execute()
        )
        return res.data[0] if res.data else None

    def log_review(
        self,
        user_id: UUID,
        flashcard_id: UUID,
        rating: int,
        state: int,
        scheduled_days: float,
        elapsed_days: float = 0.0
    ) -> Optional[Dict[str, Any]]:
        if not self.supabase.client:
            return None
        res = self.supabase.client.table("review_logs").insert({
            "user_id": str(user_id),
            "flashcard_id": str(flashcard_id),
            "rating": rating,
            "state": state,
            "scheduled_days": scheduled_days,
            "elapsed_days": elapsed_days,
            "review_time": datetime.now(timezone.utc).isoformat(),
        }).execute()
        return res.data[0] if res.data else None

    def record_workload_log(
        self,
        user_id: UUID,
        score: float,
        mode: str,
        lookahead_days: int = 3,
        active_event_count: int = 0
    ) -> Optional[Dict[str, Any]]:
        if not self.supabase.client:
            return None
        res = self.supabase.client.table("workload_logs").insert({
            "user_id": str(user_id),
            "score": score,
            "mode": mode,
            "lookahead_days": lookahead_days,
            "active_event_count": active_event_count,
            "recorded_at": datetime.now(timezone.utc).isoformat(),
        }).execute()
        return res.data[0] if res.data else None


db_service = DatabaseService()
