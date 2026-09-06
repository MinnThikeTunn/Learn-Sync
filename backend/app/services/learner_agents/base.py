from abc import ABC, abstractmethod
from typing import Callable, List, Optional, Type, TypeVar
from pydantic import BaseModel, Field

from backend.app.core.config import settings
from uuid import UUID
from backend.app.schemas.adaptive import (
    AcademicDiscipline,
    GroundingCitation,
    LearningStyle,
    StudyArtifact,
)
from backend.app.schemas.workload import WorkloadMode
from backend.app.services.llm import (
    OpenRouterUnavailableError,
    llm_service,
    openrouter_service,
)

SchemaT = TypeVar("SchemaT", bound=BaseModel)


class AgentSynthesisContext(BaseModel):
    """Execution context provided to each spawned learner subagent."""
    folder_id: UUID
    topic: str
    discipline: AcademicDiscipline
    workload_mode: WorkloadMode
    context_summary: str
    citations: List[GroundingCitation] = Field(default_factory=list)
    source_chunk_ids: List[UUID] = Field(default_factory=list)
    confidence: float = 0.95
    learning_style: Optional[LearningStyle] = None


class BaseLearnerAgent(ABC):
    """
    Abstract base class for autonomous learner subagents.
    Each subagent specializes in a specific VARK learning style modality.
    """

    learning_style: LearningStyle
    name: str

    def __init__(self, name: Optional[str] = None):
        if name:
            self.name = name

    def generate_with_llm_or_fallback(
        self,
        prompt: str,
        fallback_factory: Callable[[], str],
        max_tokens: Optional[int] = None,
    ) -> str:
        """
        Attempts synthesis via configured LLM provider:
        1. OpenRouter (Free Tier) if LLM_PROVIDER == 'openrouter' and key is configured
        2. Gemini Flash if LLM_PROVIDER == 'gemini' and key is configured
        3. Deterministic Grounded Template Fallback if zero-key or API error occurs
        """
        provider = (settings.LLM_PROVIDER or "openrouter").lower()

        if provider == "openrouter" and openrouter_service.is_configured():
            try:
                return openrouter_service.generate_text(prompt, max_tokens=max_tokens)
            except OpenRouterUnavailableError:
                pass
            except Exception:
                pass

        if settings.GEMINI_API_KEY:
            try:
                return llm_service.generate_text(prompt, max_tokens=max_tokens)
            except Exception:
                pass

        # Zero-Key or API failure fallback: deterministic grounded synthesis
        return fallback_factory()

    def generate_structured_json_with_fallback(
        self,
        prompt: str,
        schema: Type[SchemaT],
        fallback_factory: Callable[[], SchemaT],
    ) -> SchemaT:
        """
        Attempts structured JSON synthesis via configured LLM provider:
        1. OpenRouter (Free Tier) if LLM_PROVIDER == 'openrouter' and key is configured
        2. Gemini Flash if LLM_PROVIDER == 'gemini' and key is configured
        3. Deterministic Grounded Fallback if zero-key or API error occurs
        """
        provider = (settings.LLM_PROVIDER or "openrouter").lower()

        if provider == "openrouter" and openrouter_service.is_configured():
            try:
                return openrouter_service.generate_structured_json(prompt, schema)
            except Exception:
                pass

        if settings.GEMINI_API_KEY:
            try:
                return llm_service.generate_structured_json(prompt, schema)
            except Exception:
                pass

        return fallback_factory()

    @abstractmethod
    def synthesize(self, context: AgentSynthesisContext) -> StudyArtifact:
        """Synthesizes a modality-tailored StudyArtifact from the given context."""
        pass
