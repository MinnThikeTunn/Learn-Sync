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
            query = self.supabase.client.table("document_chunks").select("*").eq("user_id", str(user_id))
            if document_id:
                query = query.eq("document_id", str(document_id))
            elif folder_id:
                query = query.eq("folder_id", str(folder_id))
            res = query.order("chunk_index").limit(limit).execute()
            return res.data or []
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

            next_stage_label = "Day 3 (Second Review)"
            if stage_counts["day_7"] > 0:
                next_stage_label = "FSRS Retention"
            elif stage_counts["day_5"] > 0:
                next_stage_label = "Day 7 (Consolidation)"
            elif stage_counts["day_3"] > 0:
                next_stage_label = "Day 5 (Third Review)"

            if total_cards == 0:
                status = "not_started"
            elif needs_review:
                status = "needs_review"
            elif graduated_cards == total_cards:
                status = "mastered"
            else:
                status = "up_to_date"

            next_due = min(upcoming_dues) if upcoming_dues else None

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

                next_stage_label = "Day 3 (Second Review)"
                if stage_counts["day_7"] > 0:
                    next_stage_label = "FSRS Retention"
                elif stage_counts["day_5"] > 0:
                    next_stage_label = "Day 7 (Consolidation)"
                elif stage_counts["day_3"] > 0:
                    next_stage_label = "Day 5 (Third Review)"

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
                if self.supabase.client:
                    test_cards = self.supabase.client.table("flashcards").select("id").eq("user_id", dev_uid).limit(1).execute().data
                    if test_cards:
                        effective_uid = UUID(dev_uid)
                        break

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
                    if due_val:
                        try:
                            due_dt = datetime.fromisoformat(due_val) if isinstance(due_val, str) else due_val
                            if due_dt.tzinfo is None:
                                due_dt = due_dt.replace(tzinfo=timezone.utc)
                            if due_dt > now + timedelta(days=1.0):
                                is_due = False
                                future_dues.append((due_dt, c_stage))
                            else:
                                is_due = True
                        except Exception:
                            is_due = True

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
                    if "day3" in card_stg:
                        next_stage = "2357_day3"
                    elif "day5" in card_stg:
                        next_stage = "2357_day5"
                    elif "day7" in card_stg:
                        next_stage = "2357_day7"
                    elif "graduated" in card_stg:
                        next_stage = "graduated_fsrs"
                    else:
                        next_stage = "2357_day3"

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

        return {
            "status": "success",
            "message": f"Recorded: Deck review finished for today! The second review milestone ({next_stage}) is scheduled for {next_due.strftime('%B %d, %Y')}.",
            "file_name": resolved_name,
            "folder_id": folder_id,
            "document_id": document_id,
            "cards_completed": max(cards_reviewed + cards_updated, len(cards) if "cards" in locals() and cards else 1),
            "completed_at": now,
            "current_stage": current_stage,
            "next_stage": next_stage,
            "next_review_due": next_due,
        }


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

