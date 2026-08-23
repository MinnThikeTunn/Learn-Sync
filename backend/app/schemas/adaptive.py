from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4
from pydantic import BaseModel, ConfigDict, Field

from backend.app.schemas.workload import WorkloadMode


class LearningStyle(str, Enum):
    VISUAL = "visual"
    AUDITORY = "auditory"
    READ_WRITE = "read_write"
    KINESTHETIC = "kinesthetic"


class StudyArtifactType(str, Enum):
    DIAGRAM = "diagram"
    AUDIO_SCRIPT = "audio_script"
    SUMMARY_NOTE = "summary_note"
    CODE_LAB = "code_lab"
    CHEAT_SHEET = "cheat_sheet"
    MICRO_RECAP = "micro_recap"
    MICRO_SNIPPET = "micro_snippet"


class GroundingCitation(BaseModel):
    """Specific chunk citation linking generated material to source documents."""
    chunk_id: UUID
    document_id: Optional[UUID] = None
    snippet: str = Field(..., description="Verbatim source sentence or key fragment from chunk")
    relevance_score: float = Field(default=1.0, ge=0.0, le=1.0)


class StudyArtifactMetadata(BaseModel):
    """Multimodal rendering instructions and execution metadata."""
    diagram_syntax: Optional[str] = Field(None, description="Mermaid, PlantUML, or Graphviz syntax (e.g. 'mermaid')")
    audio_duration_seconds: Optional[int] = Field(None, description="Estimated audio read time in seconds")
    speakers: Optional[List[str]] = Field(default_factory=list, description="Dialogue speakers for Socratic audio transcripts")
    programming_language: Optional[str] = Field(None, description="Programming language for code sandboxes (e.g. 'python')")
    test_cases: Optional[List[Dict[str, Any]]] = Field(default_factory=list, description="Automated unit test specs for code labs")
    estimated_time_minutes: float = Field(default=5.0, description="Estimated student engagement duration")
    token_usage: Optional[int] = Field(None, description="LLM token count used during synthesis")

    model_config = ConfigDict(extra="allow")


class StudyArtifact(BaseModel):
    """Synthesized grounded study artifact tailored by learning style and workload mode."""
    id: UUID = Field(default_factory=uuid4)
    folder_id: UUID
    topic: str
    learning_style: LearningStyle
    workload_mode: WorkloadMode
    artifact_type: StudyArtifactType
    content: str = Field(..., description="Main synthesized artifact payload (Markdown, Mermaid, Code, Dialogue)")
    metadata: StudyArtifactMetadata = Field(default_factory=StudyArtifactMetadata)
    citations: List[GroundingCitation] = Field(default_factory=list)
    source_chunk_ids: List[UUID] = Field(default_factory=list)
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Grounding confidence based on chunk relevance")
    is_low_confidence: bool = Field(default=False, description="Flagged true when chunks are scarce or poorly matched")
    warning_message: Optional[str] = Field(None, description="Notification when confidence is below threshold")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = ConfigDict(from_attributes=True)


class GenerateArtifactRequest(BaseModel):
    """API request payload for study artifact synthesis."""
    folder_id: UUID
    user_id: UUID
    topic: str
    learning_style: LearningStyle
    workload_mode: Optional[WorkloadMode] = WorkloadMode.FREE
    custom_instructions: Optional[str] = None
