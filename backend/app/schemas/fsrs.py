import uuid
from datetime import datetime
from enum import IntEnum
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, ConfigDict
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


class FlashcardCreate(BaseModel):
    user_id: uuid.UUID
    folder_id: uuid.UUID
    kc_id: Optional[uuid.UUID] = None
    front: str = Field(..., min_length=1, description="Front prompt/question of the card")
    back: str = Field(..., min_length=1, description="Back solution/explanation")


class FlashcardUpdate(BaseModel):
    front: Optional[str] = None
    back: Optional[str] = None
    is_paused: Optional[bool] = None
    is_leech: Optional[bool] = None
    reset_lapses: Optional[bool] = False


class FlashcardModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    folder_id: uuid.UUID
    kc_id: Optional[uuid.UUID] = None
    front: str
    back: str
    stability: float = Field(default=0.0, ge=0.0)
    difficulty: float = Field(default=0.0, ge=0.0, le=10.0)
    reps: int = Field(default=0, ge=0)
    lapses: int = Field(default=0, ge=0)
    state: CardState = CardState.NEW
    is_leech: bool = False
    is_paused: bool = False
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
    scheduled_days: float
    elapsed_days: float
    retention_estimate: float
    target_retention: float
    interval_multiplier: float
    applied_mode: WorkloadMode
    is_leech_triggered: bool
    leech_notice: Optional[LeechQuarantineNotice] = None


class FlashcardReviewRequest(BaseModel):
    card_id: uuid.UUID
    rating: Rating
    review_time: Optional[datetime] = None
    workload_mode: Optional[WorkloadMode] = None
    workload_score: Optional[float] = Field(default=None, ge=0.0, le=1.0)


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
    elapsed_days: float
    scheduled_days: float
    review_time: datetime
