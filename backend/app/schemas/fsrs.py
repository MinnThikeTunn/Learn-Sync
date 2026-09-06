import uuid
from datetime import datetime
from enum import IntEnum, Enum
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, ConfigDict, model_validator
from backend.app.schemas.workload import WorkloadMode


class Rating(IntEnum):
    AGAIN = 1
    HARD = 2
    GOOD = 3
    EASY = 4


class CardState(IntEnum):
    NEW = 0
    LEARNING = 1
    REVIEW = 2
    RELEARNING = 3


class ScheduleStage(str, Enum):
    DAY_1 = "2357_day1"
    DAY_3 = "2357_day3"
    DAY_5 = "2357_day5"
    DAY_7 = "2357_day7"
    GRADUATED_FSRS = "graduated_fsrs"


class FlashcardCreate(BaseModel):
    user_id: uuid.UUID
    folder_id: uuid.UUID
    kc_id: Optional[uuid.UUID] = None
    document_id: Optional[uuid.UUID] = None
    topic: Optional[str] = None
    stage: ScheduleStage = ScheduleStage.DAY_1
    front: str = Field(..., min_length=1, description="Front prompt/question of the card")
    back: str = Field(..., min_length=1, description="Back solution/explanation")


class FlashcardUpdate(BaseModel):
    front: Optional[str] = None
    back: Optional[str] = None
    stage: Optional[ScheduleStage] = None
    is_paused: Optional[bool] = None
    is_leech: Optional[bool] = None
    reset_lapses: Optional[bool] = False


class FlashcardModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    folder_id: uuid.UUID
    kc_id: Optional[uuid.UUID] = None
    document_id: Optional[uuid.UUID] = None
    topic: Optional[str] = None
    front: str
    back: str
    stage: ScheduleStage = ScheduleStage.DAY_1
    stability: float = Field(default=0.0, ge=0.0)
    difficulty: float = Field(default=0.0, ge=0.0, le=10.0)
    reps: int = Field(default=0, ge=0)
    lapses: int = Field(default=0, ge=0)
    state: CardState = CardState.NEW
    is_leech: bool = False
    is_paused: bool = False
    is_active_in_queue: bool = True
    due: datetime
    last_review: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class LeechQuarantineNotice(BaseModel):
    card_id: uuid.UUID
    folder_id: uuid.UUID
    lapses: int
    reason: str = "Card exceeded maximum failure threshold (>= 4 lapses)"
    quarantined_at: datetime
    suggested_action: str = "Card paused from review queue. Submit to LLM remediation."


class FlashcardReviewResponse(BaseModel):
    card: FlashcardModel
    stage: ScheduleStage
    scheduled_days: float
    elapsed_days: float
    retention_estimate: float
    target_retention: float
    interval_multiplier: float
    applied_mode: WorkloadMode
    is_graduated: bool = False
    is_leech_triggered: bool = False
    leech_notice: Optional[LeechQuarantineNotice] = None


class FlashcardReviewRequest(BaseModel):
    card_id: Optional[uuid.UUID] = None
    card: Optional[FlashcardModel] = None
    rating: Rating
    review_time: Optional[datetime] = None
    workload_mode: Optional[WorkloadMode] = None
    workload_score: Optional[float] = Field(default=None, ge=0.0, le=1.0)

    @model_validator(mode="after")
    def check_card_identifier(self) -> "FlashcardReviewRequest":
        if not self.card_id and not self.card:
            raise ValueError("Either 'card_id' or 'card' payload must be provided for review")
        if not self.card_id and self.card:
            self.card_id = self.card.id
        return self


class FlashcardRewriteRequest(BaseModel):
    card_id: uuid.UUID
    original_front: str
    original_back: str
    lapses: int
    kc_title: Optional[str] = None
    prompt_instructions: str


class FlashcardRewriteResponse(BaseModel):
    card_id: uuid.UUID
    simplified_front: str
    simplified_back: str
    key_takeaway: str
    mnemonics: Optional[str] = None


class ReviewLogModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    flashcard_id: uuid.UUID
    rating: Rating
    state: CardState
    stage: ScheduleStage = ScheduleStage.DAY_1
    elapsed_days: float
    scheduled_days: float
    review_time: datetime


# =====================================================================
# Study-to-Review Handoff & Blurting Schemas
# =====================================================================

class StudyCompletionRequest(BaseModel):
    folder_id: uuid.UUID
    topic: str
    document_id: Optional[uuid.UUID] = None
    learning_style: Optional[str] = "visual"


class StudyCompletionResponse(BaseModel):
    status: str = "success"
    topic: str
    folder_id: uuid.UUID
    cards_scheduled: int
    first_due_date: datetime
    stage: ScheduleStage = ScheduleStage.DAY_1
    message: str


class BlurtingEvaluationRequest(BaseModel):
    folder_id: Optional[uuid.UUID] = None
    topic: str
    user_recall_text: str = Field(..., min_length=5, description="Student unprompted recall dump")
    reference_content: Optional[str] = None


class BlurtingEvaluationResponse(BaseModel):
    topic: str
    accuracy_score: int = Field(..., ge=0, le=100, description="Overall recall score out of 100")
    retained_concepts: List[str] = Field(default_factory=list, description="Correctly recalled concepts")
    missed_nuances: List[str] = Field(default_factory=list, description="Important facts missed or forgotten")
    recommended_focus: str = Field(..., description="Actionable focus for the next 2357 revision")
    suggested_cards: List[Dict[str, str]] = Field(default_factory=list, description="Targeted flashcards for missed points")


# =====================================================================
# Anki-Style Deck Overview & File Completion Tracking Schemas
# =====================================================================

class FileReviewStats(BaseModel):
    document_id: Optional[uuid.UUID] = None
    file_name: str
    folder_id: uuid.UUID
    folder_path: str = "/root"
    course_code: Optional[str] = "General"
    course_name: Optional[str] = "Course Material"
    topic: Optional[str] = None
    total_cards: int = 0
    due_cards_count: int = 0
    new_cards_count: int = 0
    learning_cards_count: int = 0
    graduated_cards_count: int = 0
    leech_cards_count: int = 0
    completion_percentage: float = 0.0
    mastery_percentage: float = 0.0
    needs_review_today: bool = False
    finished_today: bool = False
    next_stage_label: Optional[str] = None
    status: str = "not_started"  # "needs_review" | "up_to_date" | "mastered" | "not_started"
    next_review_due: Optional[datetime] = None
    stage_breakdown: Dict[str, int] = Field(default_factory=dict)


class DeckOverviewResponse(BaseModel):
    total_files: int = 0
    files_needing_review: int = 0
    total_due_cards: int = 0
    total_graduated_cards: int = 0
    overall_completion_percentage: float = 0.0
    files: List[FileReviewStats] = Field(default_factory=list)


class DeckCompletionRequest(BaseModel):
    folder_id: uuid.UUID
    document_id: Optional[uuid.UUID] = None
    file_name: Optional[str] = None
    cards_reviewed: int = 0


class DeckCompletionResponse(BaseModel):
    status: str = "success"
    message: str
    file_name: str
    folder_id: uuid.UUID
    document_id: Optional[uuid.UUID] = None
    cards_completed: int
    completed_at: datetime
    current_stage: str
    next_stage: str
    next_review_due: datetime

