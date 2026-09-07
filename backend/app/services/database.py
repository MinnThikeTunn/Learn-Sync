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

    def get_student_kc_mastery(self, user_id: UUID, kc_id: UUID) -> Optional[Dict[str, Any]]:
        """Read one BKT state row for an atomic, locked mastery update."""
        if not self.supabase.client:
            return None
        try:
            res = (
                self.supabase.client.table("student_kc_mastery")
                .select("*")
                .eq("user_id", str(user_id))
                .eq("kc_id", str(kc_id))
                .limit(1)
                .execute()
            )
            return res.data[0] if res.data else None
        except Exception as exc:
            logger.warning("Failed to read BKT mastery state: %s", exc)
            return None

    def upsert_student_kc_mastery(self, state: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Persist the latest BKT state with the database uniqueness constraint."""
        if not self.supabase.client:
            return None
        try:
            res = self.supabase.client.table("student_kc_mastery").upsert(
                state, on_conflict="user_id,kc_id"
            ).execute()
            return res.data[0] if res.data else None
        except Exception as exc:
            logger.warning("Failed to persist BKT mastery state: %s", exc)
            return None
        self._hybrid_sessions: Dict[Any, Dict[str, Any]] = {}

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
            courses = res.data or []
            if not courses and str(user_id) == "00000000-0000-0000-0000-000000000001":
                for dev_uid in ["5602e9c3-3747-428d-94c5-6838a8a59ce8", "0ac178f0-f5b7-4d96-a8b0-b77f8b60c5c6"]:
                    try:
                        fb_res = (
                            self.supabase.client.table("courses")
                            .select("*")
                            .eq("user_id", dev_uid)
                            .order("created_at")
                            .execute()
                        )
                        if fb_res.data:
                            return fb_res.data
                    except Exception:
                        pass
            return courses
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
            folders = res.data or []
            if not folders and str(user_id) == "00000000-0000-0000-0000-000000000001":
                for dev_uid in ["5602e9c3-3747-428d-94c5-6838a8a59ce8", "0ac178f0-f5b7-4d96-a8b0-b77f8b60c5c6"]:
                    try:
                        fb_q = self.supabase.client.table("virtual_folders").select("*").eq("user_id", dev_uid)
                        if course_id:
                            fb_q = fb_q.eq("course_id", str(course_id))
                        fb_res = fb_q.order("materialized_path").execute()
                        if fb_res.data:
                            return fb_res.data
                    except Exception:
                        pass
            return folders
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

    def get_document(self, user_id: UUID, document_id: UUID) -> Optional[Dict[str, Any]]:
        if not self.supabase.client:
            return None
        try:
            res = (
                self.supabase.client.table("documents")
                .select("*")
                .eq("id", str(document_id))
                .eq("user_id", str(user_id))
                .execute()
            )
            data = res.data or []
            if not data and str(user_id) == "00000000-0000-0000-0000-000000000001":
                fb_res = (
                    self.supabase.client.table("documents")
                    .select("*")
                    .eq("id", str(document_id))
                    .execute()
                )
                data = fb_res.data or []
            return data[0] if data else None
        except Exception as e:
            logger.warning(f"Failed to fetch document {document_id}: {e}")
            return None


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

    def get_study_queue_documents(
        self,
        user_id: UUID,
        course_id: Optional[UUID] = None,
    ) -> List[Dict[str, Any]]:
        if not self.supabase.client:
            return []
        try:
            query = self.supabase.client.table("documents").select("*").eq("user_id", str(user_id)).neq("status", "learned")
            if course_id:
                query = query.eq("course_id", str(course_id))
            res = query.order("created_at", desc=True).execute()
            docs = res.data or []

            # Dev fallback for test UUID if empty
            if not docs and str(user_id) == "00000000-0000-0000-0000-000000000001":
                for dev_uid in ["5602e9c3-3747-428d-94c5-6838a8a59ce8", "0ac178f0-f5b7-4d96-a8b0-b77f8b60c5c6"]:
                    try:
                        fb_q = self.supabase.client.table("documents").select("*").eq("user_id", dev_uid).neq("status", "learned")
                        if course_id:
                            fb_q = fb_q.eq("course_id", str(course_id))
                        fb_res = fb_q.order("created_at", desc=True).execute()
                        if fb_res.data:
                            docs = fb_res.data
                            user_id = UUID(dev_uid)
                            break
                    except Exception:
                        pass
            
            courses_list = self.get_courses(user_id)
            courses_map = {c["id"]: c for c in courses_list}
            folders_list = self.get_virtual_folders(user_id)
            folders_map = {f["id"]: f for f in folders_list}
            
            enriched = []
            for d in docs:
                c = courses_map.get(d.get("course_id"), {})
                f = folders_map.get(d.get("folder_id"), {})
                file_size_bytes = d.get("file_size_bytes", 0)
                size_str = f"{round(file_size_bytes / (1024 * 1024), 2)} MB" if file_size_bytes >= 1024 * 1024 else f"{round(file_size_bytes / 1024)} KB"
                raw_topic = d.get("file_name", "").rsplit(".", 1)[0].replace("_", " ").replace("-", " ")
                enriched.append({
                    **d,
                    "course_code": c.get("code", "General"),
                    "course_name": c.get("name", "Course Material"),
                    "folder_path": f.get("materialized_path", "/root"),
                    "topic": raw_topic,
                    "file_size_formatted": size_str,
                    "estimated_read_time": f"{max(3, min(12, int(file_size_bytes / 150000) or 5))} min synthesis",
                })
            return enriched
        except Exception as e:
            logger.warning(f"Failed to fetch study queue documents: {e}")
            return []

    def get_document_chunks(
        self,
        user_id: UUID,
        folder_id: Optional[UUID] = None,
        document_id: Optional[UUID] = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        if not self.supabase.client:
            return []
        try:
            query = self.supabase.client.table("document_chunks").select("*")
            if user_id:
                query = query.eq("user_id", str(user_id))
            if document_id:
                query = query.eq("document_id", str(document_id))
            elif folder_id:
                query = query.eq("folder_id", str(folder_id))
            res = query.order("chunk_index").limit(limit).execute()
            data = res.data or []
            if not data and (document_id or folder_id):
                fb_query = self.supabase.client.table("document_chunks").select("*")
                if document_id:
                    fb_query = fb_query.eq("document_id", str(document_id))
                elif folder_id:
                    fb_query = fb_query.eq("folder_id", str(folder_id))
                fb_res = fb_query.order("chunk_index").limit(limit).execute()
                data = fb_res.data or []
            return data
        except Exception as e:
            logger.warning(f"Failed to fetch document chunks: {e}")
            return []

    def create_document_chunks(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if not chunks or not self.supabase.client:
            return []
        try:
            res = self.supabase.client.table("document_chunks").insert(chunks).execute()
            return res.data or []
        except Exception as e:
            logger.warning(f"Failed to create document chunks: {e}")
            return []

    def get_all_document_chunks(self, user_id: UUID, document_id: UUID) -> List[Dict[str, Any]]:
        return self.get_document_chunks(user_id=user_id, document_id=document_id, limit=2000)

    def get_document_signed_url(self, storage_path: str, expires_in: int = 3600) -> Optional[str]:
        if not self.supabase.client or not storage_path:
            return None
        try:
            res = self.supabase.client.storage.from_("documents").create_signed_url(storage_path, expires_in=expires_in)
            if isinstance(res, dict):
                return res.get("signedURL") or res.get("signedUrl")
            elif isinstance(res, str):
                return res
            return None
        except Exception as e:
            logger.warning(f"Failed to create signed URL for {storage_path}: {e}")
            return None

    def download_document_bytes(self, storage_path: str) -> Optional[bytes]:
        if not self.supabase.client or not storage_path:
            return None
        try:
            return self.supabase.client.storage.from_("documents").download(storage_path)
        except Exception as e:
            logger.warning(f"Failed to download document bytes for {storage_path}: {e}")
            return None


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
        mapped_events = []
        for e in events:
            item = dict(e)
            if str(item.get("user_id")) == "00000000-0000-0000-0000-000000000001":
                item["user_id"] = "5602e9c3-3747-428d-94c5-6838a8a59ce8"
            mapped_events.append(item)
        try:
            res = self.supabase.client.table("events").insert(mapped_events).execute()
            return res.data or []
        except Exception as e:
            logger.warning(f"Failed to insert events: {e}")
            return []

    def get_upcoming_events(self, user_id: UUID, days_ahead: int = 7) -> List[Dict[str, Any]]:
        if not self.supabase.client:
            return []
        target_uid = "5602e9c3-3747-428d-94c5-6838a8a59ce8" if str(user_id) == "00000000-0000-0000-0000-000000000001" else str(user_id)
        now = datetime.now(timezone.utc)
        horizon = now + timedelta(days=days_ahead)
        try:
            res = (
                self.supabase.client.table("events")
                .select("*")
                .eq("user_id", target_uid)
                .gte("start_time", now.isoformat())
                .lte("start_time", horizon.isoformat())
                .order("start_time")
                .execute()
            )
            return res.data or []
        except Exception as e:
            logger.warning(f"Failed to fetch upcoming events: {e}")
            return []

    def get_all_events(self, user_id: UUID, limit: int = 30) -> List[Dict[str, Any]]:
        """Retrieves user events with active (uncompleted) events first, ordered chronologically."""
        if not self.supabase.client:
            return []
        target_uid = "5602e9c3-3747-428d-94c5-6838a8a59ce8" if str(user_id) == "00000000-0000-0000-0000-000000000001" else str(user_id)
        try:
            res = (
                self.supabase.client.table("events")
                .select("*")
                .eq("user_id", target_uid)
                .order("is_completed", desc=False)
                .order("start_time", desc=False)
                .limit(limit)
                .execute()
            )
            return res.data or []
        except Exception as e:
            logger.warning(f"Failed to fetch all events: {e}")
            return []

    def delete_event(self, user_id: UUID, event_id: UUID) -> bool:
        if not self.supabase.client:
            return False
        try:
            self.supabase.client.table("events").delete().eq("id", str(event_id)).execute()
            return True
        except Exception as e:
            logger.warning(f"Failed to delete event {event_id}: {e}")
            return False

    def complete_event(self, user_id: UUID, event_id: UUID, is_completed: bool = True) -> bool:
        if not self.supabase.client:
            return False
        try:
            self.supabase.client.table("events").update({"is_completed": is_completed}).eq("id", str(event_id)).execute()
            return True
        except Exception as e:
            logger.warning(f"Failed to update complete state for event {event_id}: {e}")
            return False

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
        """Delegates flashcard provisioning to the Review Session persistence adapter."""
        from backend.app.services.review_repository import supabase_review_adapter
        from backend.app.schemas.fsrs import ScheduleStage
        stage_enum = ScheduleStage(stage) if stage in [s.value for s in ScheduleStage] else ScheduleStage.DAY_1
        return supabase_review_adapter.create_card(
            user_id=user_id,
            folder_id=folder_id,
            front=front,
            back=back,
            document_id=document_id,
            topic=topic,
            stage=stage_enum,
            due=due,
        )

    def get_due_flashcards(
        self,
        user_id: UUID,
        folder_id: Optional[UUID] = None,
        stage: Optional[str] = None,
        limit: int = 30,
        document_id: Optional[UUID] = None,
        include_immediate: bool = True,
    ) -> List[Dict[str, Any]]:
        """Delegates due cards query to the Review Session persistence adapter and enriches with folder and document metadata."""
        from backend.app.services.review_repository import supabase_review_adapter
        cards = supabase_review_adapter.get_due_cards(
            user_id=user_id,
            folder_id=folder_id,
            stage=stage,
            limit=limit,
            include_immediate=include_immediate,
            document_id=document_id,
        )

        # Fallback to active dev users if default test UUID has no cards
        if not cards and str(user_id) == "00000000-0000-0000-0000-000000000001":
            for dev_uid in ["5602e9c3-3747-428d-94c5-6838a8a59ce8", "0ac178f0-f5b7-4d96-a8b0-b77f8b60c5c6"]:
                try:
                    fallback_cards = supabase_review_adapter.get_due_cards(
                        user_id=UUID(dev_uid),
                        folder_id=folder_id,
                        stage=stage,
                        limit=limit,
                        include_immediate=include_immediate,
                        document_id=document_id,
                    )
                    if fallback_cards:
                        cards = fallback_cards
                        user_id = UUID(dev_uid)
                        break
                except Exception:
                    pass

        if not cards:
            return []

        try:
            folder_ids = list({str(c.get("folder_id")) for c in cards if c.get("folder_id")})
            if folder_id:
                folder_ids.append(str(folder_id))

            folders = self.get_virtual_folders(user_id)
            folders_map = {str(f["id"]): f.get("materialized_path", "/root") for f in folders}
            docs = self.get_documents(user_id)
            docs_by_id = {str(d["id"]): d.get("file_name") for d in docs}
            # Fallback map of documents by folder_id
            docs_by_folder = {}
            for d in docs:
                if d.get("folder_id") and str(d["folder_id"]) not in docs_by_folder:
                    docs_by_folder[str(d["folder_id"])] = d.get("file_name")

            # Knowledge component name mapping
            kcs_map = {}
            kcs_by_folder = {}
            if self.supabase.client:
                try:
                    kc_res = self.supabase.client.table("knowledge_components").select("id, folder_id, name").execute()
                    if kc_res.data:
                        for k in kc_res.data:
                            kcs_map[str(k["id"])] = k["name"]
                            if k.get("folder_id") and str(k["folder_id"]) not in kcs_by_folder:
                                kcs_by_folder[str(k["folder_id"])] = k["name"]
                except Exception:
                    pass

                # Direct database lookup across documents table for all card folder_ids
                if folder_ids:
                    try:
                        doc_res = self.supabase.client.table("documents").select("id, folder_id, file_name").in_("folder_id", folder_ids).execute()
                        for d in (doc_res.data or []):
                            docs_by_id[str(d["id"])] = d.get("file_name")
                            if str(d.get("folder_id")) not in docs_by_folder:
                                docs_by_folder[str(d["folder_id"])] = d.get("file_name")
                    except Exception:
                        pass

                    try:
                        vf_res = self.supabase.client.table("virtual_folders").select("id, materialized_path, name").in_("id", folder_ids).execute()
                        for f in (vf_res.data or []):
                            folders_map[str(f["id"])] = f.get("materialized_path") or f.get("name") or "/root"
                    except Exception:
                        pass

                if document_id:
                    try:
                        single_doc = self.supabase.client.table("documents").select("id, folder_id, file_name").eq("id", str(document_id)).execute()
                        if single_doc.data:
                            docs_by_id[str(document_id)] = single_doc.data[0].get("file_name")
                            if single_doc.data[0].get("folder_id"):
                                docs_by_folder[str(single_doc.data[0]["folder_id"])] = single_doc.data[0].get("file_name")
                    except Exception:
                        pass

            enriched = []
            for c in cards:
                fid = str(c.get("folder_id") or "")
                did = str(c.get("document_id") or "")
                kid = str(c.get("kc_id") or "")

                # 1. Resolve folder path
                fpath = folders_map.get(fid) or c.get("folder_path") or c.get("folder") or "/root"

                # 2. Resolve true file name: by document_id, then by folder_id, then card's own field
                fname = docs_by_id.get(did) or docs_by_folder.get(fid) or c.get("file_name")
                if not fname and document_id and str(document_id) in docs_by_id:
                    fname = docs_by_id[str(document_id)]
                if not fname:
                    last_segment = fpath.strip("/").split("/")[-1] if fpath != "/root" else "Course Document"
                    fname = f"{last_segment.replace('_', ' ').replace('-', ' ').title()}.pdf"

                # 3. Resolve true topic name: from KC table, or card's own topic, or file name stem
                resolved_topic = c.get("topic") or kcs_map.get(kid) or kcs_by_folder.get(fid)
                if not resolved_topic or resolved_topic == "Active Revision":
                    if kid in kcs_map:
                        resolved_topic = kcs_map[kid]
                    elif fid in kcs_by_folder:
                        resolved_topic = kcs_by_folder[fid]
                    elif fname:
                        resolved_topic = fname.rsplit(".", 1)[0].replace("_", " ").replace("-", " ")
                    else:
                        resolved_topic = "Core Concept Active Recall"

                enriched.append({
                    **c,
                    "folder_path": fpath,
                    "file_name": fname,
                    "topic": resolved_topic,
                })
            return enriched
        except Exception as e:
            logger.warning(f"Failed to enrich due flashcards metadata: {e}")
            return cards

    def get_deck_overview(
        self,
        user_id: UUID,
        repository: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """
        Aggregates Anki-style deck statistics for all user files/documents:
        - Calculates exact card counts (Total, New, Learning, Due, Graduated).
        - Computes 2357 stage breakdown and weighted completion percentages.
        - Flags files requiring active review today according to the 2357 spaced schedule.
        """
        from datetime import datetime, timezone
        from collections import defaultdict
        now = datetime.now(timezone.utc)

        if repository is None:
            from backend.app.services.review_repository import supabase_review_adapter
            repository = supabase_review_adapter

        # 1. Fetch metadata
        docs = self.get_documents(user_id=user_id)
        folders = self.get_virtual_folders(user_id=user_id)
        courses = self.get_courses(user_id=user_id)

        folders_map = {str(f["id"]): f for f in folders}
        courses_map = {str(c["id"]): c for c in courses}

        # 2. Fetch all cards
        all_cards = repository.get_all_cards(user_id=user_id)

        # Fallback for dev/demo when user_id is the default test UUID and has no documents
        if not docs and not all_cards and str(user_id) == "00000000-0000-0000-0000-000000000001":
            for dev_uid in ["5602e9c3-3747-428d-94c5-6838a8a59ce8", "0ac178f0-f5b7-4d96-a8b0-b77f8b60c5c6"]:
                try:
                    effective_uid = UUID(dev_uid)
                    fb_cards = repository.get_all_cards(user_id=effective_uid)
                    if fb_cards:
                        all_cards = fb_cards
                        docs = self.get_documents(user_id=effective_uid)
                        folders = self.get_virtual_folders(user_id=effective_uid)
                        courses = self.get_courses(user_id=effective_uid)
                        folders_map = {str(f["id"]): f for f in folders}
                        courses_map = {str(c["id"]): c for c in courses}
                        break
                except Exception:
                    pass

        cards_by_folder = defaultdict(list)
        cards_by_doc = defaultdict(list)
        for c in all_cards:
            fid = str(c.get("folder_id") or "")
            did = str(c.get("document_id") or "")
            if did:
                cards_by_doc[did].append(c)
            if fid:
                cards_by_folder[fid].append(c)

        files_stats = []
        covered_folders = set()

        # 3. Process registered documents
        for d in docs:
            doc_id = str(d.get("id") or "")
            fid = str(d.get("folder_id") or "")
            if fid:
                covered_folders.add(fid)

            # Match cards: by document_id first, then folder_id
            matched_cards = cards_by_doc.get(doc_id) or cards_by_folder.get(fid) or []

            # A document only reaches Review once learning is finished (status == 'learned') or review cards exist
            if d.get("status") != "learned" and not matched_cards:
                continue

            f_info = folders_map.get(fid, {})
            c_info = courses_map.get(str(d.get("course_id") or f_info.get("course_id") or ""), {})

            folder_path = f_info.get("materialized_path") or f_info.get("name") or "/root"
            file_name = d.get("file_name") or "Course Document"
            raw_topic = file_name.rsplit(".", 1)[0].replace("_", " ").replace("-", " ")

            # Calculate metrics for this document's cards
            total_cards = len(matched_cards)
            due_cards = 0
            new_cards = 0
            learning_cards = 0
            graduated_cards = 0
            leech_cards = 0
            stage_counts = {"day_1": 0, "day_3": 0, "day_5": 0, "day_7": 0, "graduated": 0}
            weighted_score = 0.0
            upcoming_dues = []

            for c in matched_cards:
                # Stage resolution
                raw_stg = str(c.get("stage") or "2357_day1")
                if "day1" in raw_stg or "day_1" in raw_stg:
                    stg_key = "day_1"
                    card_weight = 0.2
                elif "day3" in raw_stg or "day_3" in raw_stg:
                    stg_key = "day_3"
                    card_weight = 0.4
                elif "day5" in raw_stg or "day_5" in raw_stg:
                    stg_key = "day_5"
                    card_weight = 0.6
                elif "day7" in raw_stg or "day_7" in raw_stg:
                    stg_key = "day_7"
                    card_weight = 0.8
                elif "graduated" in raw_stg or float(c.get("stability") or 0.0) >= 7.0:
                    stg_key = "graduated"
                    card_weight = 1.0
                else:
                    stg_key = "day_1"
                    card_weight = 0.2

                stage_counts[stg_key] += 1
                weighted_score += card_weight

                # State & counters
                reps = int(c.get("reps") or 0)
                stab = float(c.get("stability") or 0.0)
                state = int(c.get("state") or 0)
                if c.get("is_leech"):
                    leech_cards += 1

                if stg_key == "graduated":
                    graduated_cards += 1
                elif reps == 0 and stab == 0.0 and state == 0:
                    new_cards += 1
                else:
                    learning_cards += 1

                # Due check
                due_val = c.get("due")
                if isinstance(due_val, str):
                    try:
                        due_dt = datetime.fromisoformat(due_val)
                    except Exception:
                        due_dt = now
                elif isinstance(due_val, datetime):
                    due_dt = due_val
                else:
                    due_dt = now

                if due_dt.tzinfo is None:
                    due_dt = due_dt.replace(tzinfo=timezone.utc)

                if due_dt <= now:
                    due_cards += 1
                else:
                    upcoming_dues.append(due_dt)

            completion_pct = round((weighted_score / total_cards * 100.0), 1) if total_cards > 0 else 0.0
            mastery_pct = round((graduated_cards / total_cards * 100.0), 1) if total_cards > 0 else 0.0
            needs_review = due_cards > 0

            # Calculate if finished today (all due cards cleared and reviewed today)
            finished_today = False
            if total_cards > 0 and due_cards == 0:
                for c in matched_cards:
                    lr = c.get("last_review")
                    if lr:
                        try:
                            lr_dt = datetime.fromisoformat(lr) if isinstance(lr, str) else lr
                            if lr_dt.tzinfo is None:
                                lr_dt = lr_dt.replace(tzinfo=timezone.utc)
                            if (now - lr_dt).total_seconds() < 86400:
                                finished_today = True
                                break
                        except Exception:
                            pass

            if stage_counts.get("day_1", 0) > 0:
                next_stage_label = "Day 1 (First Review)"
            elif stage_counts.get("day_3", 0) > 0:
                next_stage_label = "Day 3 (Second Review)"
            elif stage_counts.get("day_5", 0) > 0:
                next_stage_label = "Day 5 (Third Review)"
            elif stage_counts.get("day_7", 0) > 0:
                next_stage_label = "Day 7 (Consolidation)"
            elif graduated_cards == total_cards and total_cards > 0:
                next_stage_label = "FSRS Retention"
            else:
                next_stage_label = "Day 1 (First Review)"

            if total_cards == 0:
                status = "not_started"
            elif needs_review:
                status = "needs_review"
            elif graduated_cards == total_cards:
                status = "mastered"
            else:
                status = "up_to_date"

            next_due = min(upcoming_dues) if upcoming_dues else None

            # Check if hybrid review session was completed for this file
            hybrid_rec = None
            if hasattr(self, "_hybrid_sessions"):
                hybrid_rec = (
                    self._hybrid_sessions.get((str(user_id), str(doc_id)))
                    or self._hybrid_sessions.get((str(user_id), file_name))
                    or self._hybrid_sessions.get((str(user_id), raw_topic))
                    or self._hybrid_sessions.get((str(user_id), raw_topic.lower().strip()))
                    or self._hybrid_sessions.get((str(user_id), str(fid)))
                )
            recall_done = bool(hybrid_rec and hybrid_rec.get("recall_finished") and (hybrid_rec.get("blurting_accuracy") or 0) >= 70)
            feynman_done = bool(hybrid_rec and hybrid_rec.get("feynman_finished") and (hybrid_rec.get("feynman_score") or 0) >= 70)
            last_sec = hybrid_rec.get("blurting_duration_seconds") if hybrid_rec else None
            last_acc = hybrid_rec.get("blurting_accuracy") if hybrid_rec else None
            last_fey = hybrid_rec.get("feynman_score") if hybrid_rec else None

            if hybrid_rec:
                finished_today = True

            files_stats.append({
                "document_id": doc_id,
                "file_name": file_name,
                "folder_id": fid,
                "folder_path": folder_path,
                "course_code": c_info.get("code", "General"),
                "course_name": c_info.get("name", "Course Material"),
                "topic": raw_topic,
                "total_cards": total_cards,
                "due_cards_count": due_cards,
                "new_cards_count": new_cards,
                "learning_cards_count": learning_cards,
                "graduated_cards_count": graduated_cards,
                "leech_cards_count": leech_cards,
                "completion_percentage": completion_pct,
                "mastery_percentage": mastery_pct,
                "needs_review_today": needs_review,
                "finished_today": finished_today,
                "next_stage_label": next_stage_label,
                "status": "up_to_date" if finished_today and not needs_review else status,
                "next_review_due": next_due.isoformat() if next_due else None,
                "stage_breakdown": stage_counts,
                "recall_finished": recall_done,
                "feynman_finished": feynman_done,
                "last_recall_seconds": last_sec,
                "last_blurting_accuracy": last_acc,
                "last_feynman_score": last_fey,
            })

        # 4. Check for orphan cards in folders without docs
        for fid, fcards in cards_by_folder.items():
            if fid not in covered_folders and fcards:
                f_info = folders_map.get(fid, {})
                c_info = courses_map.get(str(f_info.get("course_id") or ""), {})
                fpath = f_info.get("materialized_path") or f_info.get("name") or "/root"
                fname = fpath.strip("/").split("/")[-1] if fpath != "/root" else "Course Document"
                if not fname.endswith((".pdf", ".md", ".txt")):
                    fname += ".pdf"
                
                total_cards = len(fcards)
                due_cards = 0
                new_cards = 0
                learning_cards = 0
                graduated_cards = 0
                leech_cards = 0
                stage_counts = {"day_1": 0, "day_3": 0, "day_5": 0, "day_7": 0, "graduated": 0}
                weighted_score = 0.0
                upcoming_dues = []

                for c in fcards:
                    raw_stg = str(c.get("stage") or "2357_day1")
                    if "day1" in raw_stg:
                        stg_key = "day_1"; card_weight = 0.2
                    elif "day3" in raw_stg:
                        stg_key = "day_3"; card_weight = 0.4
                    elif "day5" in raw_stg:
                        stg_key = "day_5"; card_weight = 0.6
                    elif "day7" in raw_stg:
                        stg_key = "day_7"; card_weight = 0.8
                    elif "graduated" in raw_stg or float(c.get("stability") or 0.0) >= 7.0:
                        stg_key = "graduated"; card_weight = 1.0
                    else:
                        stg_key = "day_1"; card_weight = 0.2

                    stage_counts[stg_key] += 1
                    weighted_score += card_weight

                    reps = int(c.get("reps") or 0)
                    stab = float(c.get("stability") or 0.0)
                    state = int(c.get("state") or 0)
                    if c.get("is_leech"):
                        leech_cards += 1
                    if stg_key == "graduated":
                        graduated_cards += 1
                    elif reps == 0 and stab == 0.0 and state == 0:
                        new_cards += 1
                    else:
                        learning_cards += 1

                    due_val = c.get("due")
                    if isinstance(due_val, str):
                        try:
                            due_dt = datetime.fromisoformat(due_val)
                        except Exception:
                            due_dt = now
                    elif isinstance(due_val, datetime):
                        due_dt = due_val
                    else:
                        due_dt = now

                    if due_dt.tzinfo is None:
                        due_dt = due_dt.replace(tzinfo=timezone.utc)

                    if due_dt <= now:
                        due_cards += 1
                    else:
                        upcoming_dues.append(due_dt)

                completion_pct = round((weighted_score / total_cards * 100.0), 1) if total_cards > 0 else 0.0
                mastery_pct = round((graduated_cards / total_cards * 100.0), 1) if total_cards > 0 else 0.0
                needs_review = due_cards > 0
                status = "needs_review" if needs_review else ("mastered" if graduated_cards == total_cards else "up_to_date")
                next_due = min(upcoming_dues) if upcoming_dues else None

                finished_today = False
                if total_cards > 0 and due_cards == 0:
                    for c in fcards:
                        lr = c.get("last_review")
                        if lr:
                            try:
                                lr_dt = datetime.fromisoformat(lr) if isinstance(lr, str) else lr
                                if lr_dt.tzinfo is None:
                                    lr_dt = lr_dt.replace(tzinfo=timezone.utc)
                                if (now - lr_dt).total_seconds() < 86400:
                                    finished_today = True
                                    break
                            except Exception:
                                pass

                if stage_counts.get("day_1", 0) > 0:
                    next_stage_label = "Day 1 (First Review)"
                elif stage_counts.get("day_3", 0) > 0:
                    next_stage_label = "Day 3 (Second Review)"
                elif stage_counts.get("day_5", 0) > 0:
                    next_stage_label = "Day 5 (Third Review)"
                elif stage_counts.get("day_7", 0) > 0:
                    next_stage_label = "Day 7 (Consolidation)"
                elif graduated_cards == total_cards and total_cards > 0:
                    next_stage_label = "FSRS Retention"
                else:
                    next_stage_label = "Day 1 (First Review)"

                # Check if hybrid review session was completed for this orphan folder/file
                orphan_rec = None
                if hasattr(self, "_hybrid_sessions"):
                    orphan_topic = fname.rsplit(".", 1)[0].replace("_", " ")
                    orphan_rec = (
                        self._hybrid_sessions.get((str(user_id), fname))
                        or self._hybrid_sessions.get((str(user_id), orphan_topic))
                        or self._hybrid_sessions.get((str(user_id), orphan_topic.lower().strip()))
                        or self._hybrid_sessions.get((str(user_id), str(fid)))
                    )
                orphan_recall = bool(orphan_rec and orphan_rec.get("recall_finished") and (orphan_rec.get("blurting_accuracy") or 0) >= 70)
                orphan_feynman = bool(orphan_rec and orphan_rec.get("feynman_finished") and (orphan_rec.get("feynman_score") or 0) >= 70)
                orphan_sec = orphan_rec.get("blurting_duration_seconds") if orphan_rec else None
                orphan_acc = orphan_rec.get("blurting_accuracy") if orphan_rec else None
                orphan_fey = orphan_rec.get("feynman_score") if orphan_rec else None

                if orphan_rec:
                    finished_today = True

                files_stats.append({
                    "document_id": None,
                    "file_name": fname,
                    "folder_id": fid,
                    "folder_path": fpath,
                    "course_code": c_info.get("code", "General"),
                    "course_name": c_info.get("name", "Course Material"),
                    "topic": fname.rsplit(".", 1)[0].replace("_", " "),
                    "total_cards": total_cards,
                    "due_cards_count": due_cards,
                    "new_cards_count": new_cards,
                    "learning_cards_count": learning_cards,
                    "graduated_cards_count": graduated_cards,
                    "leech_cards_count": leech_cards,
                    "completion_percentage": completion_pct,
                    "mastery_percentage": mastery_pct,
                    "needs_review_today": needs_review,
                    "finished_today": finished_today,
                    "next_stage_label": next_stage_label,
                    "status": "up_to_date" if finished_today and not needs_review else status,
                    "next_review_due": next_due.isoformat() if next_due else None,
                    "stage_breakdown": stage_counts,
                    "recall_finished": orphan_recall,
                    "feynman_finished": orphan_feynman,
                    "last_recall_seconds": orphan_sec,
                    "last_blurting_accuracy": orphan_acc,
                    "last_feynman_score": orphan_fey,
                })

        # Summary totals
        total_files = len(files_stats)
        files_needing_review = sum(1 for f in files_stats if f["needs_review_today"])
        total_due_cards = sum(f["due_cards_count"] for f in files_stats)
        total_graduated = sum(f["graduated_cards_count"] for f in files_stats)
        total_all_cards = sum(f["total_cards"] for f in files_stats)

        overall_completion = (
            round((sum(f["completion_percentage"] * f["total_cards"] for f in files_stats) / total_all_cards), 1)
            if total_all_cards > 0
            else 0.0
        )

        return {
            "total_files": total_files,
            "files_needing_review": files_needing_review,
            "total_due_cards": total_due_cards,
            "total_graduated_cards": total_graduated,
            "overall_completion_percentage": overall_completion,
            "files": files_stats,
        }

    def record_deck_completion(
        self,
        user_id: UUID,
        folder_id: UUID,
        document_id: Optional[UUID] = None,
        file_name: Optional[str] = None,
        cards_reviewed: int = 0,
    ) -> Dict[str, Any]:
        """
        Explicitly records that the user has completed reviewing a flashcard deck for today:
        - Advances all due cards in that deck to the next 2357 milestone (+2 days, Day 3 in 2357 schedule).
        - Saves card stage and due date in Supabase.
        - Returns confirmation message and scheduled next review milestone.
        """
        from datetime import datetime, timezone, timedelta
        now = datetime.now(timezone.utc)

        effective_uid = user_id
        if str(user_id) == "00000000-0000-0000-0000-000000000001":
            for dev_uid in ["5602e9c3-3747-428d-94c5-6838a8a59ce8", "0ac178f0-f5b7-4d96-a8b0-b77f8b60c5c6"]:
                try:
                    if self.supabase.client:
                        test_cards = self.supabase.client.table("flashcards").select("id").eq("user_id", dev_uid).limit(1).execute().data
                        if test_cards:
                            effective_uid = UUID(dev_uid)
                            break
                except Exception:
                    pass

        cards_updated = 0
        next_due = now + timedelta(days=2)
        next_stage = "2357_day3"
        current_stage = "2357_day1"

        if self.supabase.client:
            try:
                cards = []
                if document_id:
                    cards = self.supabase.client.table("flashcards").select("*").eq("user_id", str(effective_uid)).eq("document_id", str(document_id)).execute().data or []
                if not cards and folder_id:
                    cards = self.supabase.client.table("flashcards").select("*").eq("user_id", str(effective_uid)).eq("folder_id", str(folder_id)).execute().data or []
                if not cards and not document_id and not folder_id:
                    cards = self.supabase.client.table("flashcards").select("*").eq("user_id", str(effective_uid)).execute().data or []

                future_dues = []
                for c in cards:
                    c_stage = str(c.get("stage") or "2357_day1")
                    current_stage = c_stage

                    due_val = c.get("due")
                    is_due = True
                    due_dt = None
                    if due_val:
                        try:
                            due_dt = datetime.fromisoformat(due_val) if isinstance(due_val, str) else due_val
                            if due_dt.tzinfo is None:
                                due_dt = due_dt.replace(tzinfo=timezone.utc)
                            if due_dt > now + timedelta(minutes=5):
                                is_due = False
                                future_dues.append((due_dt, c_stage))
                            else:
                                is_due = True
                        except Exception:
                            is_due = True

                    # Also check last_review (if reviewed within last 12 hours, do not re-advance on same day)
                    lr = c.get("last_review")
                    if lr:
                        try:
                            lr_dt = datetime.fromisoformat(lr) if isinstance(lr, str) else lr
                            if lr_dt.tzinfo is None:
                                lr_dt = lr_dt.replace(tzinfo=timezone.utc)
                            if (now - lr_dt).total_seconds() < 43200:
                                is_due = False
                                if due_dt and (due_dt, c_stage) not in future_dues:
                                    future_dues.append((due_dt, c_stage))
                        except Exception:
                            pass

                    if is_due:
                        # Advance this due card to the next 2357 milestone
                        if "day1" in c_stage or "day_1" in c_stage:
                            n_stage = "2357_day3"
                            n_days = 2.0
                        elif "day3" in c_stage or "day_3" in c_stage:
                            n_stage = "2357_day5"
                            n_days = 2.0
                        elif "day5" in c_stage or "day_5" in c_stage:
                            n_stage = "2357_day7"
                            n_days = 2.0
                        elif "day7" in c_stage or "day_7" in c_stage:
                            n_stage = "graduated_fsrs"
                            n_days = 7.0
                        else:
                            n_stage = "graduated_fsrs"
                            n_days = 14.0

                        next_stage = n_stage
                        card_next_due = now + timedelta(days=n_days)
                        next_due = card_next_due

                        upd = {
                            "stage": n_stage,
                            "due": card_next_due.isoformat(),
                            "last_review": now.isoformat(),
                            "reps": int(c.get("reps") or 0) + 1,
                            "state": 2,
                            "updated_at": now.isoformat(),
                        }
                        self.supabase.client.table("flashcards").update(upd).eq("id", c["id"]).execute()
                        cards_updated += 1

                        try:
                            self.supabase.client.table("review_logs").insert({
                                "user_id": str(effective_uid),
                                "flashcard_id": c["id"],
                                "rating": 3,
                                "state": 2,
                                "scheduled_days": n_days,
                                "elapsed_days": 1.0,
                                "review_time": now.isoformat(),
                            }).execute()
                        except Exception:
                            pass

                if cards_updated == 0 and future_dues:
                    future_dues.sort(key=lambda x: x[0])
                    next_due = future_dues[0][0]
                    card_stg = str(future_dues[0][1] or "")
                    if "day1" in card_stg:
                        next_stage = "2357_day1"
                    elif "day3" in card_stg:
                        next_stage = "2357_day3"
                    elif "day5" in card_stg:
                        next_stage = "2357_day5"
                    elif "day7" in card_stg:
                        next_stage = "2357_day7"
                    elif "graduated" in card_stg:
                        next_stage = "graduated_fsrs"
                    else:
                        next_stage = card_stg

            except Exception as e:
                logger.warning(f"Error in record_deck_completion: {e}")

        resolved_name = file_name or "Active Document"
        if not file_name and document_id:
            try:
                d = self.get_document(user_id=effective_uid, document_id=document_id)
                if d:
                    resolved_name = d.get("file_name", resolved_name)
            except Exception:
                pass

        stage_label_map = {
            "2357_day1": "Day 1 (First Review)",
            "2357_day3": "Day 3 (Second Review)",
            "2357_day5": "Day 5 (Third Review)",
            "2357_day7": "Day 7 (Consolidation)",
            "graduated_fsrs": "FSRS Retention",
        }
        display_label = stage_label_map.get(next_stage, next_stage)

        if cards_updated == 0:
            is_extra_practice = True
            msg = f"Recorded: Extra practice complete! Your scheduled milestone ({display_label}) remains set for {next_due.strftime('%B %d, %Y')}. Review on that exact date to advance to the next step."
        else:
            is_extra_practice = False
            msg = f"Recorded: Deck review finished for today! The next review milestone ({display_label}) is scheduled for {next_due.strftime('%B %d, %Y')}."

        return {
            "status": "success",
            "message": msg,
            "file_name": resolved_name,
            "folder_id": folder_id,
            "document_id": document_id,
            "cards_completed": max(cards_reviewed + cards_updated, len(cards) if "cards" in locals() and cards else 1),
            "completed_at": now,
            "current_stage": current_stage,
            "next_stage": next_stage,
            "next_review_due": next_due,
            "is_extra_practice": is_extra_practice,
        }

    def record_hybrid_review_session(
        self,
        user_id: UUID,
        folder_id: UUID,
        document_id: Optional[UUID] = None,
        file_name: Optional[str] = None,
        topic: Optional[str] = None,
        cards_reviewed: int = 0,
        blurting_content: str = "",
        blurting_duration_seconds: float = 0.0,
        feynman_explanation: str = "",
        target_audience: str = "beginner",
        repository: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """
        Records the unified Two-Step Hybrid Review Session:
        1. Runs Blurting memory recall precision analysis.
        2. Runs Feynman conceptual simplification & gap analysis.
        3. Advances due cards for this deck in the 2357 spaced repetition schedule (Day 1 -> Day 3, etc.).
        4. Marks recall_finished=True and feynman_finished=True attached to the specific file.
        """
        from datetime import datetime, timezone, timedelta
        import uuid
        from backend.app.schemas.fsrs import BlurtingEvaluationRequest, ScheduleStage
        from backend.app.services.blurting import BlurtingService
        from backend.app.services.feynman import FeynmanService
        from backend.app.schemas.feynman import FeynmanEvaluationRequest, FeynmanPromptTarget

        now = datetime.now(timezone.utc)
        resolved_name = file_name or "Active Document"
        resolved_topic = topic or (file_name.rsplit(".", 1)[0].replace("_", " ") if file_name else "General Topic")

        # 1. Evaluate Blurting recall
        blurting_eval = BlurtingService.evaluate_recall(
            BlurtingEvaluationRequest(
                topic=resolved_topic,
                user_recall_text=blurting_content,
            )
        )

        # 2. Evaluate Feynman explanation
        target_aud_enum = FeynmanPromptTarget.CHILD
        if target_audience == "non_technical":
            target_aud_enum = FeynmanPromptTarget.NON_TECHNICAL
        elif target_audience in ["peer", "peer_beginner"]:
            target_aud_enum = FeynmanPromptTarget.PEER_BEGINNER

        feynman_eval = FeynmanService.evaluate_explanation(
            FeynmanEvaluationRequest(
                concept=resolved_topic,
                student_explanation=feynman_explanation,
                target_audience=target_aud_enum,
            )
        )

        # 3. Advance cards in 2357 schedule
        next_due = now + timedelta(days=2)
        current_stage = "2357_day1"
        next_stage = "2357_day3"
        cards_updated = 0

        if repository is not None:
            all_cards = repository.get_all_cards(user_id=user_id, folder_id=folder_id)
            for c in all_cards:
                c_doc = str(c.get("document_id") or "")
                c_fold = str(c.get("folder_id") or "")
                if (document_id and c_doc == str(document_id)) or (not document_id and folder_id and c_fold == str(folder_id)):
                    c_stage = str(c.get("stage") or "2357_day1")
                    current_stage = c_stage

                    # Check if card was already advanced / reviewed in this session
                    c_due = c.get("due")
                    c_due_dt = None
                    if c_due:
                        try:
                            c_due_dt = datetime.fromisoformat(c_due) if isinstance(c_due, str) else c_due
                            if c_due_dt.tzinfo is None:
                                c_due_dt = c_due_dt.replace(tzinfo=timezone.utc)
                        except Exception:
                            pass

                    c_last = c.get("last_review")
                    already_reviewed = False
                    if c_last:
                        try:
                            l_dt = datetime.fromisoformat(c_last) if isinstance(c_last, str) else c_last
                            if l_dt.tzinfo is None:
                                l_dt = l_dt.replace(tzinfo=timezone.utc)
                            if (now - l_dt).total_seconds() < 43200:
                                already_reviewed = True
                        except Exception:
                            pass

                    # If card was already reviewed today or due is in future, preserve its scheduled stage!
                    if already_reviewed or (c_due_dt and c_due_dt > now + timedelta(minutes=5)):
                        next_stage = c_stage
                        if c_due_dt:
                            next_due = c_due_dt
                        continue

                    if "day1" in c_stage or "day_1" in c_stage:
                        n_stage = ScheduleStage.DAY_3
                        n_days = 2.0
                    elif "day3" in c_stage or "day_3" in c_stage:
                        n_stage = ScheduleStage.DAY_5
                        n_days = 2.0
                    elif "day5" in c_stage or "day_5" in c_stage:
                        n_stage = ScheduleStage.DAY_7
                        n_days = 2.0
                    else:
                        n_stage = ScheduleStage.GRADUATED_FSRS
                        n_days = 7.0
                    next_stage = n_stage.value
                    card_due = now + timedelta(days=n_days)
                    next_due = card_due
                    repository.update_card_stage(card_id=c["id"], stage=n_stage, due=card_due)
                    cards_updated += 1
            is_extra_practice = bool(cards_updated == 0)
        else:
            # Standard path: call record_deck_completion to advance in Supabase
            deck_res = self.record_deck_completion(
                user_id=user_id,
                folder_id=folder_id,
                document_id=document_id,
                file_name=file_name,
                cards_reviewed=cards_reviewed,
            )
            current_stage = deck_res.get("current_stage", "2357_day1")
            next_stage = deck_res.get("next_stage", "2357_day3")
            next_due = deck_res.get("next_review_due", next_due)
            cards_updated = deck_res.get("cards_completed", cards_reviewed)
            is_extra_practice = bool(deck_res.get("is_extra_practice", False))
            if not file_name:
                resolved_name = deck_res.get("file_name", resolved_name)

        # 4. Words per minute calculation
        word_count = len(blurting_content.split())
        wpm = round((word_count / max(blurting_duration_seconds, 1.0)) * 60.0, 1)

        # 5. Persist hybrid session record attached to file
        feynman_pct = int(round(feynman_eval.completeness_score * 100)) if feynman_eval.completeness_score <= 1.0 else int(round(feynman_eval.completeness_score))
        recall_passed = bool(blurting_eval.accuracy_score >= 70)
        feynman_passed = bool(feynman_pct >= 70 and getattr(feynman_eval, "is_sufficient", True))

        session_id = str(uuid.uuid4())
        session_data = {
            "session_id": session_id,
            "user_id": str(user_id),
            "folder_id": str(folder_id),
            "document_id": str(document_id) if document_id else None,
            "file_name": resolved_name,
            "topic": resolved_topic,
            "recall_finished": recall_passed,
            "feynman_finished": feynman_passed,
            "blurting_duration_seconds": blurting_duration_seconds,
            "blurting_wpm": wpm,
            "blurting_accuracy": blurting_eval.accuracy_score,
            "feynman_score": feynman_pct,
            "completed_at": now.isoformat(),
            "next_stage": next_stage,
            "next_review_due": next_due.isoformat() if hasattr(next_due, "isoformat") else str(next_due),
            "is_extra_practice": is_extra_practice,
        }
        if not hasattr(self, "_hybrid_sessions"):
            self._hybrid_sessions = {}

        if document_id:
            self._hybrid_sessions[(str(user_id), str(document_id))] = session_data
        if resolved_name:
            self._hybrid_sessions[(str(user_id), resolved_name)] = session_data
        if folder_id:
            self._hybrid_sessions[(str(user_id), str(folder_id))] = session_data

        feynman_dict = feynman_eval.model_dump() if hasattr(feynman_eval, "model_dump") else feynman_eval

        stage_label_map = {
            "2357_day1": "Day 1 (First Review)",
            "2357_day3": "Day 3 (Second Review)",
            "2357_day5": "Day 5 (Third Review)",
            "2357_day7": "Day 7 (Consolidation)",
            "graduated_fsrs": "FSRS Retention",
        }
        display_label = stage_label_map.get(next_stage, next_stage)
        due_str = next_due.strftime('%B %d, %Y') if hasattr(next_due, "strftime") else str(next_due)

        if is_extra_practice:
            session_msg = f"Extra practice completed! Your scheduled milestone ({display_label}) remains set for {due_str}. Review on that exact date to advance."
        else:
            session_msg = f"Recorded 2357 Day Review completion, Active Recall Dump, and Feynman Synthesis for {resolved_name}."

        return {
            "status": "success",
            "session_id": session_id,
            "file_name": resolved_name,
            "folder_id": folder_id,
            "document_id": document_id,
            "cards_completed": max(cards_reviewed, cards_updated),
            "completed_at": now,
            "current_stage": current_stage,
            "next_stage": next_stage,
            "next_review_due": next_due,
            "is_extra_practice": is_extra_practice,
            "recall_finished": recall_passed,
            "feynman_finished": feynman_passed,
            "blurting_metrics": blurting_eval,
            "feynman_metrics": feynman_dict,
            "speed_words_per_minute": wpm,
            "message": session_msg,
        }

    def record_blurting_completion(
        self,
        user_id: UUID,
        folder_id: Optional[UUID] = None,
        document_id: Optional[UUID] = None,
        file_name: Optional[str] = None,
        topic: Optional[str] = None,
        duration_seconds: float = 60.0,
        accuracy_score: int = 0,
    ) -> None:
        """Records standalone Blurting Scratchpad completion attached to file/topic."""
        if not hasattr(self, "_hybrid_sessions"):
            self._hybrid_sessions = {}

        keys_to_update = []
        uid_str = str(user_id)
        if document_id:
            keys_to_update.append((uid_str, str(document_id)))
        if file_name:
            keys_to_update.append((uid_str, file_name))
        if topic:
            keys_to_update.append((uid_str, topic))
            keys_to_update.append((uid_str, topic.lower().strip()))
        if folder_id:
            keys_to_update.append((uid_str, str(folder_id)))

        existing_data = {}
        for k in keys_to_update:
            if k in self._hybrid_sessions:
                existing_data = self._hybrid_sessions[k].copy()
                break

        existing_data.update({
            "user_id": uid_str,
            "folder_id": str(folder_id) if folder_id else existing_data.get("folder_id"),
            "document_id": str(document_id) if document_id else existing_data.get("document_id"),
            "file_name": file_name or existing_data.get("file_name"),
            "topic": topic or existing_data.get("topic"),
            "recall_finished": bool(accuracy_score >= 70),
            "blurting_duration_seconds": duration_seconds,
            "blurting_accuracy": accuracy_score,
            "feynman_finished": existing_data.get("feynman_finished", False),
            "feynman_score": existing_data.get("feynman_score"),
        })

        for k in keys_to_update:
            self._hybrid_sessions[k] = existing_data

    def record_feynman_completion(
        self,
        user_id: UUID,
        folder_id: Optional[UUID] = None,
        document_id: Optional[UUID] = None,
        file_name: Optional[str] = None,
        topic: Optional[str] = None,
        feynman_score: int = 0,
    ) -> None:
        """Records standalone Feynman Explainer completion attached to file/topic."""
        if not hasattr(self, "_hybrid_sessions"):
            self._hybrid_sessions = {}

        keys_to_update = []
        uid_str = str(user_id)
        if document_id:
            keys_to_update.append((uid_str, str(document_id)))
        if file_name:
            keys_to_update.append((uid_str, file_name))
        if topic:
            keys_to_update.append((uid_str, topic))
            keys_to_update.append((uid_str, topic.lower().strip()))
        if folder_id:
            keys_to_update.append((uid_str, str(folder_id)))

        existing_data = {}
        for k in keys_to_update:
            if k in self._hybrid_sessions:
                existing_data = self._hybrid_sessions[k].copy()
                break

        existing_data.update({
            "user_id": uid_str,
            "folder_id": str(folder_id) if folder_id else existing_data.get("folder_id"),
            "document_id": str(document_id) if document_id else existing_data.get("document_id"),
            "file_name": file_name or existing_data.get("file_name"),
            "topic": topic or existing_data.get("topic"),
            "feynman_finished": bool(feynman_score >= 70),
            "feynman_score": feynman_score,
            "recall_finished": existing_data.get("recall_finished", False),
            "blurting_duration_seconds": existing_data.get("blurting_duration_seconds"),
            "blurting_accuracy": existing_data.get("blurting_accuracy"),
        })

        for k in keys_to_update:
            self._hybrid_sessions[k] = existing_data


    def update_flashcard_stage(
        self,
        flashcard_id: UUID,
        stage: str,
        due: datetime,
        is_active_in_queue: bool = True
    ) -> Optional[Dict[str, Any]]:
        """Delegates stage update to the Review Session persistence adapter."""
        from backend.app.services.review_repository import supabase_review_adapter
        from backend.app.schemas.fsrs import ScheduleStage
        stage_enum = ScheduleStage(stage) if stage in [s.value for s in ScheduleStage] else ScheduleStage.DAY_1
        return supabase_review_adapter.update_card_stage(
            card_id=flashcard_id,
            stage=stage_enum,
            due=due,
            is_active_in_queue=is_active_in_queue,
        )

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
        """Legacy helper: persists updated state attributes directly to flashcards table."""
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
        """Delegates review logging to the Review Session persistence adapter."""
        from backend.app.services.review_repository import supabase_review_adapter
        return supabase_review_adapter.log_review(
            user_id=user_id,
            flashcard_id=flashcard_id,
            rating=rating,
            state=state,
            scheduled_days=scheduled_days,
            elapsed_days=elapsed_days,
        )

    def record_workload_log(
        self,
        user_id: UUID,
        score: float,
        mode: str,
        lookahead_days: int = 7,
        active_event_count: int = 0
    ) -> Optional[Dict[str, Any]]:
        if not self.supabase.client:
            return None
        target_uid = "5602e9c3-3747-428d-94c5-6838a8a59ce8" if str(user_id) == "00000000-0000-0000-0000-000000000001" else str(user_id)
        try:
            res = self.supabase.client.table("workload_logs").insert({
                "user_id": target_uid,
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

