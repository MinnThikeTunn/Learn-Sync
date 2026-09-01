from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4
from pydantic import BaseModel, ConfigDict, Field

from backend.app.schemas.fsrs import FlashcardCreate


class FeynmanPromptTarget(str, Enum):
    CHILD = "child"
    PEER_BEGINNER = "peer_beginner"
    NON_TECHNICAL = "non_technical"


class FeynmanPromptRequest(BaseModel):
    user_id: Optional[UUID] = None
    folder_id: Optional[UUID] = None
    concept: str = Field(..., min_length=2, description="Target concept to explain")
    kc_id: Optional[UUID] = None
    target_audience: FeynmanPromptTarget = FeynmanPromptTarget.CHILD
    context_chunks: List[Dict[str, Any]] = Field(default_factory=list)


class FeynmanPromptResponse(BaseModel):
    concept: str
    target_audience: FeynmanPromptTarget
    prompt_text: str = Field(..., description="Active recall prompt challenging student to explain simply")
    analogy_hint: Optional[str] = None
    key_points_to_cover: List[str] = Field(default_factory=list)


class FeynmanGapItem(BaseModel):
    concept: str
    missing_aspect: str
    severity: str = Field(default="medium", description="minor | medium | critical")
    source_chunk_id: Optional[UUID] = None


class MisconceptionItem(BaseModel):
    student_claim: str
    correct_fact: str
    explanation: str
    severity: str = Field(default="critical", description="minor | moderate | critical")


class RemedialFlashcardCandidate(BaseModel):
    front: str = Field(..., min_length=1, description="Targeted question addressing gap/misconception")
    back: str = Field(..., min_length=1, description="Clear, bite-sized corrective explanation")
    kc_id: Optional[UUID] = None
    folder_id: Optional[UUID] = None


class GapAnalysisResult(BaseModel):
    concept: str
    completeness_score: float = Field(..., ge=0.0, le=1.0, description="0.0 = complete failure, 1.0 = thorough explanation")
    is_sufficient: bool = Field(..., description="True if completeness >= 0.70 and no critical misconceptions")
    feedback: str = Field(..., description="Actionable pedagogical critique")
    missing_concepts: List[FeynmanGapItem] = Field(default_factory=list)
    misconceptions: List[MisconceptionItem] = Field(default_factory=list)
    generated_flashcards: List[FlashcardCreate] = Field(default_factory=list)
    evaluated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = ConfigDict(from_attributes=True)


class FeynmanEvaluationRequest(BaseModel):
    user_id: Optional[UUID] = None
    folder_id: Optional[UUID] = None
    concept: str = Field(..., min_length=2)
    student_explanation: str = Field(..., min_length=5, description="Student's plain-language explanation")
    kc_id: Optional[UUID] = None
    context_chunks: List[Dict[str, Any]] = Field(default_factory=list)
    auto_generate_flashcards: bool = True
