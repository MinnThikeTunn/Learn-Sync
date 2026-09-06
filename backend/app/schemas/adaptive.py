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


class AcademicDiscipline(str, Enum):
    MEDICINE = "medicine"
    LIFE_SCIENCES = "life_sciences"
    LAW = "law"
    BUSINESS = "business"
    HUMANITIES = "humanities"
    COMPUTER_SCIENCE = "computer_science"
    GENERAL = "general"


class StudyArtifactType(str, Enum):
    DIAGRAM = "diagram"
    MIND_MAP = "mind_map"
    AUDIO_SCRIPT = "audio_script"
    SUMMARY_NOTE = "summary_note"
    CODE_LAB = "code_lab"
    CLINICAL_SIMULATION = "clinical_simulation"
    PROCEDURAL_SEQUENCING = "procedural_sequencing"
    DECISION_DILEMMA = "decision_dilemma"
    CRITICAL_DECISION = "critical_decision"
    CHEAT_SHEET = "cheat_sheet"
    MICRO_RECAP = "micro_recap"
    MICRO_SNIPPET = "micro_snippet"


class InteractiveChoice(BaseModel):
    """An actionable decision choice in an interactive simulation."""
    id: str
    label: str
    is_optimal: bool
    immediate_feedback: str
    consequence_narrative: Optional[str] = None
    vital_impact: Optional[Dict[str, str]] = None


class SimulationStep(BaseModel):
    """A single decision step in a progressive clinical or analytical simulation."""
    step_number: int
    title: str
    prompt: str
    vitals_or_state: Optional[Dict[str, str]] = Field(
        default=None,
        description="Clinical vitals (BP, HR, SpO2, Temp) or scenario state parameters"
    )
    choices: List[InteractiveChoice] = Field(default_factory=list)


class SequencingItem(BaseModel):
    """A protocol, pathway, or procedural step to be sequenced."""
    id: str
    label: str
    correct_order: int
    rationale: Optional[str] = None


class KinestheticSimulationPayload(BaseModel):
    """Polymorphic data structure backing the multi-discipline simulation lab."""
    kinesthetic_type: str = Field(..., description="clinical_simulation | procedural_sequencing | decision_dilemma | code_sandbox | critical_decision")
    academic_discipline: AcademicDiscipline = Field(default=AcademicDiscipline.GENERAL)
    scenario_title: str
    context_brief: str
    steps: List[SimulationStep] = Field(default_factory=list)
    sequencing_items: List[SequencingItem] = Field(default_factory=list)
    starter_code: Optional[str] = None
    language: Optional[str] = None
    test_cases: Optional[List[Dict[str, Any]]] = None


class GroundingCitation(BaseModel):
    """Specific chunk citation linking generated material to source documents."""
    chunk_id: UUID
    document_id: Optional[UUID] = None
    snippet: str = Field(..., description="Verbatim source sentence or key fragment from chunk")
    relevance_score: float = Field(default=1.0, ge=0.0, le=1.0)


class StudyArtifactMetadata(BaseModel):
    """Multimodal rendering instructions and execution metadata."""
    diagram_syntax: Optional[str] = Field(None, description="Mermaid, PlantUML, or Graphviz syntax (e.g. 'mermaid')")
    alternative_diagram_syntax: Optional[str] = Field(None, description="Alternative diagram syntax for dual-view toggle (e.g. flowchart vs mindmap)")
    academic_discipline: Optional[AcademicDiscipline] = Field(None, description="Discipline domain of the topic/document")
    concept_tree: Optional[Dict[str, Any]] = Field(None, description="Structured hierarchical concept tree backing the mind map")
    simulation_payload: Optional[KinestheticSimulationPayload] = Field(None, description="Detailed payload for interactive simulation labs")
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
    user_id: Optional[UUID] = None
    topic: str
    learning_style: LearningStyle
    workload_mode: Optional[WorkloadMode] = WorkloadMode.FREE
    custom_instructions: Optional[str] = None
    chunks: Optional[List[Dict[str, Any]]] = None

