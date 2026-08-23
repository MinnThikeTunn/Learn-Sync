from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional
from uuid import UUID, uuid4
from pydantic import BaseModel, ConfigDict, Field

from backend.app.schemas.workload import EventItem


class BMAPActionType(str, Enum):
    ONE_SENTENCE_SUMMARY = "one_sentence_summary"
    SINGLE_FLASHCARD = "single_flashcard"
    FORMULA_CHECK = "formula_check"
    KEYWORD_MATCH = "keyword_match"
    BREATHING_PAUSE = "breathing_pause"


class BMAPMicroTask(BaseModel):
    """
    90-second ultra-low barrier task structured by Fogg's Behavior Model (B=MAP):
    High Motivation + High Ability (Low Friction) + Timely Prompt.
    """
    id: UUID = Field(default_factory=uuid4)
    user_id: UUID
    title: str = Field(..., min_length=2)
    prompt: str = Field(..., min_length=5, description="Friction-free 90-second prompt")
    action_type: BMAPActionType = BMAPActionType.SINGLE_FLASHCARD
    duration_seconds: int = Field(default=90, ge=30, le=180)
    target_folder_id: Optional[UUID] = None
    target_kc_id: Optional[UUID] = None
    is_completed: bool = False
    completed_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = ConfigDict(from_attributes=True)


class BurnoutTriggerRequest(BaseModel):
    user_id: UUID
    events: List[EventItem]
    reference_time: Optional[datetime] = None
    window_hours: float = Field(default=48.0, ge=12.0, le=72.0)
    deadline_threshold: int = Field(default=3, ge=2, description="Major events threshold in 48h")
    available_calendar_slots: Optional[int] = Field(default=None, ge=0)


class BurnoutTriggerResponse(BaseModel):
    user_id: UUID
    is_burnout_risk: bool
    trigger_reason: Optional[str] = None
    deadline_count_48h: int
    free_slots_48h: int
    micro_task: Optional[BMAPMicroTask] = None
    published_to_event_bus: bool = False
    evaluated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
