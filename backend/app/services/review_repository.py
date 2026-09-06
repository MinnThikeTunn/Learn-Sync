import abc
import logging
import uuid
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional
from uuid import UUID

from backend.app.schemas.fsrs import FlashcardModel, ScheduleStage, CardState
from backend.app.core.supabase import SupabaseVectorClient

logger = logging.getLogger(__name__)


class ReviewRepository(abc.ABC):
    """
    Persistence seam interface for the Review Session module.
    Callers and domain logic cross this seam to read and record flashcard states
    and historical review logs.
    """

    @abc.abstractmethod
    def get_card(self, card_id: UUID) -> Optional[FlashcardModel]:
        """Retrieves a flashcard by its unique identifier."""
        raise NotImplementedError

    @abc.abstractmethod
    def save_card_state(
        self,
        card: FlashcardModel,
        stage: Optional[ScheduleStage] = None,
    ) -> FlashcardModel:
        """Persists updated memory stability, difficulty, due timestamp, lapses, and leech status."""
        raise NotImplementedError

    @abc.abstractmethod
    def log_review(
        self,
        user_id: UUID,
        flashcard_id: UUID,
        rating: int,
        state: int,
        scheduled_days: float,
        elapsed_days: float = 0.0,
    ) -> Optional[Dict[str, Any]]:
        """Inserts an immutable historical review audit entry."""
        raise NotImplementedError

    @abc.abstractmethod
    def get_due_cards(
        self,
        user_id: UUID,
        folder_id: Optional[UUID] = None,
        stage: Optional[str] = None,
        limit: int = 30,
    ) -> List[Dict[str, Any]]:
        """Retrieves active flashcards scheduled for review in the active folder or stage."""
        raise NotImplementedError

    @abc.abstractmethod
    def create_card(
        self,
        user_id: UUID,
        folder_id: UUID,
        front: str,
        back: str,
        document_id: Optional[UUID] = None,
        topic: Optional[str] = None,
        stage: ScheduleStage = ScheduleStage.DAY_1,
        due: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Provisions a new candidate flashcard into the initial review schedule."""
        raise NotImplementedError

    @abc.abstractmethod
    def update_card_stage(
        self,
        card_id: UUID,
        stage: ScheduleStage,
        due: datetime,
        is_active_in_queue: bool = True,
    ) -> Optional[Dict[str, Any]]:
        """Updates the 2357 milestone stage and due date for an active card."""
        raise NotImplementedError

    @abc.abstractmethod
    def get_all_cards(
        self,
        user_id: UUID,
        folder_id: Optional[UUID] = None,
    ) -> List[Dict[str, Any]]:
        """Retrieves all flashcards belonging to the user/folder regardless of due status."""
        raise NotImplementedError


class SupabaseReviewAdapter(ReviewRepository):
    """
    Production adapter satisfying ReviewRepository against Supabase PostgreSQL tables:
    - flashcards
    - review_logs
    """

    def __init__(self, supabase_client: Optional[SupabaseVectorClient] = None):
        self.supabase = supabase_client or SupabaseVectorClient()

    def get_card(self, card_id: UUID) -> Optional[FlashcardModel]:
        if not self.supabase.client:
            return None
        try:
            res = (
                self.supabase.client.table("flashcards")
                .select("*")
                .eq("id", str(card_id))
                .execute()
            )
            if res.data and len(res.data) > 0:
                raw = res.data[0]
                # Normalize string dates
                due = datetime.fromisoformat(raw["due"]) if isinstance(raw.get("due"), str) else raw.get("due")
                last_rev = datetime.fromisoformat(raw["last_review"]) if isinstance(raw.get("last_review"), str) else raw.get("last_review")
                raw["due"] = due
                raw["last_review"] = last_rev
                if "stage" not in raw or not raw["stage"]:
                    raw["stage"] = ScheduleStage.DAY_1
                return FlashcardModel.model_validate(raw)
            return None
        except Exception as e:
            logger.warning(f"Failed to fetch flashcard {card_id} from Supabase: {e}")
            return None

    def save_card_state(
        self,
        card: FlashcardModel,
        stage: Optional[ScheduleStage] = None,
    ) -> FlashcardModel:
        if not self.supabase.client:
            return card
        try:
            stage_val = stage.value if stage else (card.stage.value if card.stage else "2357_day1")
            update_dict = {
                "stability": card.stability,
                "difficulty": card.difficulty,
                "reps": card.reps,
                "lapses": card.lapses,
                "state": int(card.state),
                "due": card.due.isoformat() if card.due else datetime.now(timezone.utc).isoformat(),
                "last_review": card.last_review.isoformat() if card.last_review else datetime.now(timezone.utc).isoformat(),
                "is_leech": card.is_leech,
                "is_paused": card.is_paused,
                "stage": stage_val,
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
            self.supabase.client.table("flashcards").update(update_dict).eq("id", str(card.id)).execute()
            return card
        except Exception as e:
            logger.warning(f"Failed to persist flashcard {card.id} state to Supabase: {e}")
            return card

    def log_review(
        self,
        user_id: UUID,
        flashcard_id: UUID,
        rating: int,
        state: int,
        scheduled_days: float,
        elapsed_days: float = 0.0,
    ) -> Optional[Dict[str, Any]]:
        if not self.supabase.client:
            return None
        try:
            res = (
                self.supabase.client.table("review_logs")
                .insert({
                    "user_id": str(user_id),
                    "flashcard_id": str(flashcard_id),
                    "rating": rating,
                    "state": state,
                    "scheduled_days": scheduled_days,
                    "elapsed_days": elapsed_days,
                    "review_time": datetime.now(timezone.utc).isoformat(),
                })
                .execute()
            )
            return res.data[0] if res.data else None
        except Exception as e:
            logger.warning(f"Failed to log review for card {flashcard_id}: {e}")
            return None

    def get_due_cards(
        self,
        user_id: UUID,
        folder_id: Optional[UUID] = None,
        stage: Optional[str] = None,
        limit: int = 30,
        include_immediate: bool = False,
        document_id: Optional[UUID] = None,
    ) -> List[Dict[str, Any]]:
        if not self.supabase.client:
            return []
        now = datetime.now(timezone.utc)
        try:
            query = (
                self.supabase.client.table("flashcards")
                .select("*")
                .eq("is_paused", False)
            )
            if user_id:
                query = query.eq("user_id", str(user_id))

            # When reviewing a specific folder or when immediate review is requested, allow cards scheduled for today/tomorrow
            if not include_immediate and not folder_id and not document_id:
                query = query.lte("due", now.isoformat())
            elif not include_immediate and (folder_id or document_id):
                query = query.lte("due", (now + timedelta(days=1, hours=2)).isoformat())

            if folder_id:
                query = query.eq("folder_id", str(folder_id))
            if stage:
                query = query.eq("stage", stage)
            res = query.order("due").limit(limit).execute()
            data = res.data or []

            # If user_id returned 0 cards but folder_id was requested, check by folder_id directly
            if not data and folder_id and user_id:
                fb_query = (
                    self.supabase.client.table("flashcards")
                    .select("*")
                    .eq("folder_id", str(folder_id))
                    .eq("is_paused", False)
                )
                if not include_immediate and not document_id:
                    fb_query = fb_query.lte("due", (now + timedelta(days=1, hours=2)).isoformat())
                if stage:
                    fb_query = fb_query.eq("stage", stage)
                fb_res = fb_query.order("due").limit(limit).execute()
                data = fb_res.data or []

            return data
        except Exception as e:
            logger.warning(f"Failed to fetch due flashcards from Supabase: {e}")
            return []

    def create_card(
        self,
        user_id: UUID,
        folder_id: UUID,
        front: str,
        back: str,
        document_id: Optional[UUID] = None,
        topic: Optional[str] = None,
        stage: ScheduleStage = ScheduleStage.DAY_1,
        due: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        now = datetime.now(timezone.utc)
        stage_str = stage.value if isinstance(stage, ScheduleStage) else str(stage)
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
                    out["stage"] = stage_str
                    out["topic"] = topic
                    out["document_id"] = str(document_id) if document_id else None
                    return out
            except Exception as e:
                logger.warning(f"Supabase flashcard insert fallback: {e}")
        record["id"] = str(uuid.uuid4())
        record["stage"] = stage_str
        record["topic"] = topic
        record["document_id"] = str(document_id) if document_id else None
        return record

    def update_card_stage(
        self,
        card_id: UUID,
        stage: ScheduleStage,
        due: datetime,
        is_active_in_queue: bool = True,
    ) -> Optional[Dict[str, Any]]:
        if not self.supabase.client:
            return None
        try:
            stage_str = stage.value if isinstance(stage, ScheduleStage) else str(stage)
            res = (
                self.supabase.client.table("flashcards")
                .update({
                    "stage": stage_str,
                    "due": due.isoformat(),
                    "is_active_in_queue": is_active_in_queue,
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                })
                .eq("id", str(card_id))
                .execute()
            )
            return res.data[0] if res.data else None
        except Exception as e:
            logger.warning(f"Failed to update flashcard stage in Supabase: {e}")
            return None

    def get_all_cards(
        self,
        user_id: UUID,
        folder_id: Optional[UUID] = None,
    ) -> List[Dict[str, Any]]:
        if not self.supabase.client:
            return []
        try:
            query = self.supabase.client.table("flashcards").select("*").eq("is_paused", False)
            if user_id:
                query = query.eq("user_id", str(user_id))
            if folder_id:
                query = query.eq("folder_id", str(folder_id))
            res = query.order("created_at", desc=False).execute()
            return res.data or []
        except Exception as e:
            logger.warning(f"Failed to fetch all cards from Supabase: {e}")
            return []


class InMemoryReviewAdapter(ReviewRepository):
    """
    In-memory adapter satisfying ReviewRepository for deterministic, network-isolated unit testing.
    """

    def __init__(self, initial_cards: Optional[List[FlashcardModel]] = None):
        self.cards: Dict[UUID, FlashcardModel] = {}
        self.raw_card_records: Dict[str, Dict[str, Any]] = {}
        self.review_logs: List[Dict[str, Any]] = []
        if initial_cards:
            for c in initial_cards:
                self.cards[c.id] = c.model_copy()
                self.raw_card_records[str(c.id)] = c.model_dump(mode="json")

    def get_card(self, card_id: UUID) -> Optional[FlashcardModel]:
        card = self.cards.get(card_id)
        return card.model_copy() if card else None

    def save_card_state(
        self,
        card: FlashcardModel,
        stage: Optional[ScheduleStage] = None,
    ) -> FlashcardModel:
        if stage:
            card = card.model_copy(update={"stage": stage})
        self.cards[card.id] = card.model_copy()
        self.raw_card_records[str(card.id)] = card.model_dump(mode="json")
        return card

    def log_review(
        self,
        user_id: UUID,
        flashcard_id: UUID,
        rating: int,
        state: int,
        scheduled_days: float,
        elapsed_days: float = 0.0,
    ) -> Optional[Dict[str, Any]]:
        entry = {
            "id": str(uuid.uuid4()),
            "user_id": str(user_id),
            "flashcard_id": str(flashcard_id),
            "rating": rating,
            "state": state,
            "scheduled_days": scheduled_days,
            "elapsed_days": elapsed_days,
            "review_time": datetime.now(timezone.utc).isoformat(),
        }
        self.review_logs.append(entry)
        return entry

    def get_due_cards(
        self,
        user_id: UUID,
        folder_id: Optional[UUID] = None,
        stage: Optional[str] = None,
        limit: int = 30,
    ) -> List[Dict[str, Any]]:
        now = datetime.now(timezone.utc)
        results = []
        for cid, raw in self.raw_card_records.items():
            if str(raw.get("user_id")) != str(user_id):
                continue
            if raw.get("is_paused"):
                continue
            if folder_id and str(raw.get("folder_id")) != str(folder_id):
                continue
            if stage and raw.get("stage") != stage:
                continue
            due_dt = raw.get("due")
            if isinstance(due_dt, str):
                due_dt = datetime.fromisoformat(due_dt)
            if due_dt and due_dt <= now:
                results.append(raw)
            if len(results) >= limit:
                break
        return results

    def create_card(
        self,
        user_id: UUID,
        folder_id: UUID,
        front: str,
        back: str,
        document_id: Optional[UUID] = None,
        topic: Optional[str] = None,
        stage: ScheduleStage = ScheduleStage.DAY_1,
        due: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        now = datetime.now(timezone.utc)
        new_id = uuid.uuid4()
        due_date = due or (now + timedelta(days=1))
        model = FlashcardModel(
            id=new_id,
            user_id=user_id,
            folder_id=folder_id,
            document_id=document_id,
            topic=topic,
            front=front,
            back=back,
            stage=stage,
            stability=0.0,
            difficulty=0.0,
            reps=0,
            lapses=0,
            state=CardState.NEW,
            is_leech=False,
            is_paused=False,
            due=due_date,
            created_at=now,
            updated_at=now,
        )
        self.cards[new_id] = model
        record = model.model_dump(mode="json")
        self.raw_card_records[str(new_id)] = record
        return record

    def update_card_stage(
        self,
        card_id: UUID,
        stage: ScheduleStage,
        due: datetime,
        is_active_in_queue: bool = True,
    ) -> Optional[Dict[str, Any]]:
        if card_id in self.cards:
            updated = self.cards[card_id].model_copy(
                update={"stage": stage, "due": due, "is_active_in_queue": is_active_in_queue}
            )
            self.cards[card_id] = updated
            self.raw_card_records[str(card_id)] = updated.model_dump(mode="json")
            return self.raw_card_records[str(card_id)]
        return None

    def get_all_cards(
        self,
        user_id: UUID,
        folder_id: Optional[UUID] = None,
    ) -> List[Dict[str, Any]]:
        results = []
        for cid, raw in self.raw_card_records.items():
            if str(raw.get("user_id")) != str(user_id):
                continue
            if raw.get("is_paused"):
                continue
            if folder_id and str(raw.get("folder_id")) != str(folder_id):
                continue
            results.append(raw)
        return results


# Default singleton adapter instance
supabase_review_adapter = SupabaseReviewAdapter()
