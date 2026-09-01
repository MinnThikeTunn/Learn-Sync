import logging
import re
from typing import Any, Dict, List, Optional
from uuid import UUID
from datetime import datetime, timezone, timedelta
from backend.app.core.supabase import SupabaseVectorClient

logger = logging.getLogger(__name__)


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

    def create_course(
        self,
        user_id: UUID,
        name: str,
        code: str,
        term: Optional[str] = None,
        color: Optional[str] = "#3b82f6",
        description: Optional[str] = None,
    ) -> Dict[str, Any]:
        record = {
            "user_id": str(user_id),
            "name": name,
            "code": code,
            "term": term,
            "color": color or "#3b82f6",
            "description": description,
        }
        if self.supabase.client:
            try:
                res = self.supabase.client.table("courses").insert(record).execute()
                if res.data and len(res.data) > 0:
                    return res.data[0]
            except Exception as e:
                logger.warning(f"Failed to create course in Supabase: {e}")
        record["id"] = str(UUID(int=0))
        return record

    def get_courses(self, user_id: UUID) -> List[Dict[str, Any]]:
        if not self.supabase.client:
            return []
        try:
            res = (
                self.supabase.client.table("courses")
                .select("*")
                .eq("user_id", str(user_id))
                .order("created_at")
                .execute()
            )
            return res.data or []
        except Exception as e:
            logger.warning(f"Failed to fetch courses from Supabase: {e}")
            return []

    def delete_course(self, user_id: UUID, course_id: UUID) -> bool:
        if not self.supabase.client:
            return False
        try:
            docs_res = (
                self.supabase.client.table("documents")
                .select("id, storage_path")
                .eq("user_id", str(user_id))
                .eq("course_id", str(course_id))
                .execute()
            )
            if docs_res.data:
                paths = [d["storage_path"] for d in docs_res.data if d.get("storage_path")]
                if paths:
                    try:
                        self.supabase.client.storage.from_("documents").remove(paths)
                    except Exception as e:
                        logger.warning(f"Failed to remove course files from storage: {e}")
            self.supabase.client.table("courses").delete().eq("id", str(course_id)).eq("user_id", str(user_id)).execute()
            return True
        except Exception as e:
            logger.warning(f"Failed to delete course {course_id}: {e}")
            return False

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
            try:
                res = self.supabase.client.table("virtual_folders").insert(record).execute()
                if res.data and len(res.data) > 0:
                    return res.data[0]
            except Exception as e:
                logger.warning(f"Failed to create virtual folder in Supabase: {e}")
        return record

    def get_virtual_folders(self, user_id: UUID, course_id: Optional[UUID] = None) -> List[Dict[str, Any]]:
        if not self.supabase.client:
            return []
        try:
            query = self.supabase.client.table("virtual_folders").select("*").eq("user_id", str(user_id))
            if course_id:
                query = query.eq("course_id", str(course_id))
            res = query.order("materialized_path").execute()
            return res.data or []
        except Exception as e:
            logger.warning(f"Failed to fetch virtual folders: {e}")
            return []

    def create_document(
        self,
        user_id: UUID,
        course_id: UUID,
        file_name: str,
        storage_path: str,
        file_type: str,
        folder_id: Optional[UUID] = None,
        file_size_bytes: int = 0,
        status: str = "pending",
        error_message: Optional[str] = None,
    ) -> Dict[str, Any]:
        record = {
            "user_id": str(user_id),
            "course_id": str(course_id),
            "folder_id": str(folder_id) if folder_id else None,
            "file_name": file_name,
            "storage_path": storage_path,
            "file_type": file_type,
            "file_size_bytes": file_size_bytes,
            "status": status,
            "error_message": error_message,
        }
        if self.supabase.client:
            try:
                res = self.supabase.client.table("documents").insert(record).execute()
                if res.data and len(res.data) > 0:
                    return res.data[0]
            except Exception as e:
                logger.warning(f"Failed to create document record: {e}")
        record["id"] = str(UUID(int=0))
        return record

    def get_documents(
        self,
        user_id: UUID,
        folder_id: Optional[UUID] = None,
        course_id: Optional[UUID] = None,
    ) -> List[Dict[str, Any]]:
        if not self.supabase.client:
            return []
        try:
            query = self.supabase.client.table("documents").select("*").eq("user_id", str(user_id))
            if folder_id:
                query = query.eq("folder_id", str(folder_id))
            if course_id:
                query = query.eq("course_id", str(course_id))
            res = query.order("created_at", desc=True).execute()
            return res.data or []
        except Exception as e:
            logger.warning(f"Failed to fetch documents: {e}")
            return []

    def update_document_status(
        self,
        doc_id: UUID,
        status: str,
        error_message: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        if not self.supabase.client:
            return None
        try:
            payload = {"status": status, "updated_at": datetime.now(timezone.utc).isoformat()}
            if error_message is not None:
                payload["error_message"] = error_message
            res = self.supabase.client.table("documents").update(payload).eq("id", str(doc_id)).execute()
            return res.data[0] if res.data else None
        except Exception as e:
            logger.warning(f"Failed to update document status: {e}")
            return None

    def mark_document_learned(
        self,
        user_id: UUID,
        document_id: UUID,
        is_learned: bool = True,
    ) -> Optional[Dict[str, Any]]:
        if not self.supabase.client:
            return None
        try:
            payload = {
                "status": "learned" if is_learned else "indexed",
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
            res = self.supabase.client.table("documents").update(payload).eq("id", str(document_id)).eq("user_id", str(user_id)).execute()
            return res.data[0] if res.data else None
        except Exception as e:
            logger.warning(f"Failed to mark document learned: {e}")
            return None

    def create_document_chunks(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if not chunks or not self.supabase.client:
            return []
        try:
            res = self.supabase.client.table("document_chunks").insert(chunks).execute()
            return res.data or []
        except Exception as e:
            logger.warning(f"Failed to create document chunks: {e}")
            return []

    def delete_document(self, user_id: UUID, document_id: UUID) -> bool:
        if not self.supabase.client:
            return False
        try:
            doc_res = (
                self.supabase.client.table("documents")
                .select("storage_path")
                .eq("id", str(document_id))
                .eq("user_id", str(user_id))
                .execute()
            )
            if not doc_res.data:
                return False
            storage_path = doc_res.data[0].get("storage_path")
            if storage_path:
                try:
                    self.supabase.client.storage.from_("documents").remove([storage_path])
                except Exception as e:
                    logger.warning(f"Failed to remove file {storage_path} from storage: {e}")
            self.supabase.client.table("documents").delete().eq("id", str(document_id)).eq("user_id", str(user_id)).execute()
            return True
        except Exception as e:
            logger.warning(f"Failed to delete document {document_id}: {e}")
            return False

    def delete_virtual_folder(self, user_id: UUID, folder_id: UUID) -> bool:
        if not self.supabase.client:
            return False
        try:
            folder_res = (
                self.supabase.client.table("virtual_folders")
                .select("id, materialized_path, depth")
                .eq("id", str(folder_id))
                .eq("user_id", str(user_id))
                .execute()
            )
            if not folder_res.data:
                return False
            
            docs_res = (
                self.supabase.client.table("documents")
                .select("id, storage_path")
                .eq("user_id", str(user_id))
                .eq("folder_id", str(folder_id))
                .execute()
            )
            if docs_res.data:
                paths = [d["storage_path"] for d in docs_res.data if d.get("storage_path")]
                if paths:
                    try:
                        self.supabase.client.storage.from_("documents").remove(paths)
                    except Exception as e:
                        logger.warning(f"Failed to delete folder documents from storage: {e}")
                doc_ids = [d["id"] for d in docs_res.data]
                self.supabase.client.table("documents").delete().in_("id", doc_ids).execute()

            self.supabase.client.table("virtual_folders").delete().eq("id", str(folder_id)).eq("user_id", str(user_id)).execute()
            return True
        except Exception as e:
            logger.warning(f"Failed to delete virtual folder {folder_id}: {e}")
            return False

    def insert_events(self, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if not events or not self.supabase.client:
            return []
        try:
            res = self.supabase.client.table("events").insert(events).execute()
            return res.data or []
        except Exception as e:
            logger.warning(f"Failed to insert events: {e}")
            return []

    def get_upcoming_events(self, user_id: UUID, days_ahead: int = 3) -> List[Dict[str, Any]]:
        if not self.supabase.client:
            return []
        now = datetime.now(timezone.utc)
        horizon = now + timedelta(days=days_ahead)
        try:
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
        except Exception as e:
            logger.warning(f"Failed to fetch upcoming events: {e}")
            return []

    def create_flashcard(
        self,
        user_id: UUID,
        folder_id: UUID,
        front: str,
        back: str,
        document_id: Optional[UUID] = None,
        topic: Optional[str] = None,
        stage: str = "2357_day1",
        due: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        now = datetime.now(timezone.utc)
        record = {
            "user_id": str(user_id),
            "folder_id": str(folder_id),
            "front": front,
            "back": back,
            "stability": 0.0,
            "difficulty": 0.0,
            "reps": 0,
            "lapses": 0,
            "state": 0,
            "is_leech": False,
            "is_paused": False,
            "due": (due or (now + timedelta(days=1))).isoformat(),
        }
        if self.supabase.client:
            try:
                res = self.supabase.client.table("flashcards").insert(record).execute()
                if res.data and len(res.data) > 0:
                    out = res.data[0]
                    out["stage"] = stage
                    out["topic"] = topic
                    out["document_id"] = str(document_id) if document_id else None
                    return out
            except Exception as e:
                logger.warning(f"Flashcard insert fallback: {e}")
        import uuid as _uuid
        record["id"] = str(_uuid.uuid4())
        record["stage"] = stage
        record["topic"] = topic
        record["document_id"] = str(document_id) if document_id else None
        return record

    def get_due_flashcards(
        self,
        user_id: UUID,
        folder_id: Optional[UUID] = None,
        stage: Optional[str] = None,
        limit: int = 30
    ) -> List[Dict[str, Any]]:
        if not self.supabase.client:
            return []
        now = datetime.now(timezone.utc)
        try:
            query = (
                self.supabase.client.table("flashcards")
                .select("*")
                .eq("user_id", str(user_id))
                .lte("due", now.isoformat())
                .eq("is_paused", False)
            )
            if folder_id:
                query = query.eq("folder_id", str(folder_id))
            if stage:
                query = query.eq("stage", stage)
            res = query.order("due").limit(limit).execute()
            return res.data or []
        except Exception as e:
            logger.warning(f"Failed to fetch due flashcards: {e}")
            return []

    def update_flashcard_stage(
        self,
        flashcard_id: UUID,
        stage: str,
        due: datetime,
        is_active_in_queue: bool = True
    ) -> Optional[Dict[str, Any]]:
        if not self.supabase.client:
            return None
        try:
            res = (
                self.supabase.client.table("flashcards")
                .update({
                    "stage": stage,
                    "due": due.isoformat(),
                    "is_active_in_queue": is_active_in_queue,
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                })
                .eq("id", str(flashcard_id))
                .execute()
            )
            return res.data[0] if res.data else None
        except Exception as e:
            logger.warning(f"Failed to update flashcard stage: {e}")
            return None

    def update_flashcard_state(
        self,
        flashcard_id: UUID,
        stability: float,
        difficulty: float,
        due: datetime,
        lapses: int,
        is_leech: bool,
        is_paused: bool = False,
        stage: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        if not self.supabase.client:
            return None
        try:
            update_dict = {
                "stability": stability,
                "difficulty": difficulty,
                "due": due.isoformat(),
                "lapses": lapses,
                "is_leech": is_leech,
                "is_paused": is_paused,
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
            if stage:
                update_dict["stage"] = stage
            res = (
                self.supabase.client.table("flashcards")
                .update(update_dict)
                .eq("id", str(flashcard_id))
                .execute()
            )
            return res.data[0] if res.data else None
        except Exception as e:
            logger.warning(f"Failed to update flashcard state: {e}")
            return None

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
        try:
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
        except Exception as e:
            logger.warning(f"Failed to log review: {e}")
            return None

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
        try:
            res = self.supabase.client.table("workload_logs").insert({
                "user_id": str(user_id),
                "score": score,
                "mode": mode,
                "lookahead_days": lookahead_days,
                "active_event_count": active_event_count,
                "recorded_at": datetime.now(timezone.utc).isoformat(),
            }).execute()
            return res.data[0] if res.data else None
        except Exception as e:
            logger.warning(f"Failed to record workload log: {e}")
            return None

    def save_learning_style_assessment(
        self,
        user_id: UUID,
        primary_style: str,
        secondary_style: Optional[str] = None,
        scores: Optional[Dict[str, int]] = None,
    ) -> Optional[Dict[str, Any]]:
        """Persists evaluated learner style, secondary style, and assessment scores to profiles."""
        if not self.supabase.client:
            return None
        update_data = {
            "learning_style": primary_style,
            "secondary_learning_style": secondary_style,
            "onboarding_completed": True,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        if scores is not None:
            update_data["assessment_scores"] = scores

        try:
            res = (
                self.supabase.client.table("profiles")
                .update(update_data)
                .eq("id", str(user_id))
                .execute()
            )
            return res.data[0] if res.data else None
        except Exception as e:
            logger.warning(f"Failed to save learning style assessment: {e}")
            return None

    def get_user_learning_style(self, user_id: UUID) -> Optional[Dict[str, Any]]:
        """Queries the current user's profile to verify learning style existence."""
        if not self.supabase.client:
            return None
        try:
            res = (
                self.supabase.client.table("profiles")
                .select("id, learning_style, secondary_learning_style, onboarding_completed, assessment_scores")
                .eq("id", str(user_id))
                .execute()
            )
            return res.data[0] if res.data else None
        except Exception as e:
            logger.warning(f"Failed to get user learning style: {e}")
            return None


db_service = DatabaseService()

