from datetime import datetime
from enum import Enum
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class WorkloadMode(str, Enum):
    FREE = "free"
    BUSY = "busy"
    HYSTERESIS_HOLD = "hysteresis_hold"


class EventType(str, Enum):
    EXAM = "exam"
    PROJECT = "project"
    ASSIGNMENT = "assignment"
    QUIZ = "quiz"
    LECTURE = "lecture"
    OTHER = "other"


EVENT_TYPE_WEIGHTS: dict[EventType, float] = {
    EventType.EXAM: 3.0,
    EventType.PROJECT: 2.5,
    EventType.ASSIGNMENT: 1.5,
    EventType.QUIZ: 1.0,
    EventType.LECTURE: 0.5,
    EventType.OTHER: 0.5,
}

NORMALIZATION_GAMMA: float = 8.0
LOOKAHEAD_DAYS_DEFAULT: float = 3.0
MIN_DISTANCE_DAYS: float = 0.25
FREE_THRESHOLD: float = 0.55
BUSY_THRESHOLD: float = 0.70


class EventItem(BaseModel):
    id: Optional[UUID] = None
    user_id: UUID
    title: str
    event_type: EventType = EventType.ASSIGNMENT
    start_time: datetime
    end_time: Optional[datetime] = None
    weight: Optional[float] = None
    is_completed: bool = False
    source: str = "manual"

    model_config = ConfigDict(from_attributes=True)

    @property
    def effective_weight(self) -> float:
        if self.weight is not None and self.weight > 0.0:
            return float(self.weight)
        return EVENT_TYPE_WEIGHTS.get(self.event_type, 1.0)


class WorkloadCalculationRequest(BaseModel):
    user_id: UUID
    events: List[EventItem]
    reference_time: Optional[datetime] = None
    previous_mode: Optional[WorkloadMode] = None
    lookahead_days: float = Field(default=LOOKAHEAD_DAYS_DEFAULT, ge=0.5, le=14.0)


class ModeTransitionEvent(BaseModel):
    event_id: UUID
    user_id: UUID
    timestamp: datetime
    event_name: str = "workload.spike.detected"
    score: float = Field(ge=0.0, le=1.0)
    current_mode: WorkloadMode
    previous_mode: Optional[WorkloadMode] = None
    active_event_count: int
    critical_events: List[str] = Field(default_factory=list)


class WorkloadScoreResponse(BaseModel):
    user_id: UUID
    score: float = Field(ge=0.0, le=1.0)
    current_mode: WorkloadMode
    previous_mode: Optional[WorkloadMode] = None
    transition_detected: bool
    is_spike: bool
    lookahead_days: float
    active_event_count: int
    critical_events: List[str] = Field(default_factory=list)
    evaluated_at: datetime
    raw_sum: float

    model_config = ConfigDict(from_attributes=True)


class WorkloadLogCreate(BaseModel):
    user_id: UUID
    score: float = Field(ge=0.0, le=1.0)
    mode: WorkloadMode
    lookahead_days: int = 3
    active_event_count: int = 0
    recorded_at: Optional[datetime] = None
