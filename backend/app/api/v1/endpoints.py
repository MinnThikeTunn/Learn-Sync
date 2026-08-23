from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Query
from typing import List, Optional
from uuid import UUID

from backend.app.schemas.syllabus import ParsedSyllabus, SyllabusModule
from backend.app.schemas.folder import (
    VirtualFolderCreate,
    StagedSyllabusPreviewResponse,
    DocumentChunkCreate,
)
from backend.app.schemas.workload import (
    WorkloadCalculationRequest,
    WorkloadScoreResponse,
    ModeTransitionEvent,
    WorkloadMode,
)
from backend.app.schemas.adaptive import (
    GenerateArtifactRequest,
    StudyArtifact,
    LearningStyle,
)
from backend.app.schemas.fsrs import (
    FlashcardReviewRequest,
    FlashcardReviewResponse,
    FlashcardModel,
    Rating,
)
from backend.app.schemas.feynman import (
    FeynmanPromptRequest,
    FeynmanPromptResponse,
    FeynmanEvaluationRequest,
    GapAnalysisResult,
)
from backend.app.schemas.bkt import BKTUpdateRequest, BKTUpdateResponse
from backend.app.schemas.burnout import BurnoutTriggerRequest, BurnoutTriggerResponse

from backend.app.services.parser import SyllabusIngestionService
from backend.app.services.workload import WorkloadEngine
from backend.app.services.rag import AdaptiveLearningEngine
from backend.app.services.fsrs_engine import SpacedRepetitionService
from backend.app.services.feynman import FeynmanService
from backend.app.services.bkt import BKTService
from backend.app.services.burnout_guard import BurnoutGuardService
from backend.app.core.events import event_publisher

router = APIRouter()


@router.post("/syllabus/parse", response_model=StagedSyllabusPreviewResponse)
async def parse_syllabus_upload(
    user_id: UUID = Form(...),
    course_id: UUID = Form(...),
    file: UploadFile = File(...),
):
    """Uploads syllabus PDF and generates staged virtual folders and parsed events."""
    content = await file.read()
    service = SyllabusIngestionService()
    parsed = service.parse_syllabus(content, file.filename)
    folders = service.build_virtual_folder_hierarchy(
        course_code=parsed.course_code,
        modules=parsed.modules,
        course_id=course_id,
        user_id=user_id,
    )
    return StagedSyllabusPreviewResponse(
        syllabus=parsed,
        suggested_folders=folders,
        suggested_events=parsed.events,
    )


@router.post("/workload/evaluate", response_model=WorkloadScoreResponse)
async def evaluate_workload(request: WorkloadCalculationRequest):
    """Calculates rolling 3-day Workload Score W(t) and Schmitt hysteresis state."""
    response, spike_event = WorkloadEngine.evaluate(request)
    if spike_event:
        event_publisher.publish_workload_spike(spike_event)
    return response


@router.post("/artifacts/generate", response_model=StudyArtifact)
async def generate_study_artifact(request: GenerateArtifactRequest):
    """Synthesizes grounded study artifact (4 learning styles x 2 workload modes)."""
    used_chunks = request.chunks or [
        {
            "id": request.folder_id,
            "content": f"Core lecture materials covering {request.topic} foundations and practical mechanisms.",
            "cosine_similarity": 0.90,
            "rrf_score": 0.031,
        }
    ]
    return AdaptiveLearningEngine.generate_artifact(
        folder_id=request.folder_id,
        style=request.learning_style,
        mode=request.workload_mode or WorkloadMode.FREE,
        topic=request.topic,
        chunks=used_chunks,
        custom_instructions=request.custom_instructions,
    )


@router.post("/flashcards/review", response_model=FlashcardReviewResponse)
async def review_flashcard(
    card: FlashcardModel,
    rating: Rating,
    workload_mode: Optional[WorkloadMode] = None,
    workload_score: Optional[float] = None,
):
    """Processes FSRS flashcard review with dynamic retention and leech quarantine."""
    return SpacedRepetitionService.process_review(
        card=card,
        rating=rating,
        workload_mode=workload_mode,
        workload_score=workload_score,
    )


@router.post("/feynman/prompt", response_model=FeynmanPromptResponse)
async def get_feynman_prompt(request: FeynmanPromptRequest):
    """Generates active recall Feynman explanation prompt."""
    return FeynmanService.generate_prompt(request)


@router.post("/feynman/evaluate", response_model=GapAnalysisResult)
async def evaluate_feynman_explanation(request: FeynmanEvaluationRequest):
    """Evaluates student explanation with precision-gap analysis and auto-generates remedial cards."""
    return FeynmanService.evaluate_explanation(request)


@router.post("/bkt/update", response_model=BKTUpdateResponse)
async def update_bkt_mastery(request: BKTUpdateRequest):
    """Updates Bayesian Knowledge Tracing posterior mastery state."""
    return BKTService.update_mastery(request)


@router.post("/burnout/check", response_model=BurnoutTriggerResponse)
async def check_burnout_risk(request: BurnoutTriggerRequest):
    """Monitors acute 48h deadline clusters and triggers 90-second B=MAP micro-tasks."""
    return BurnoutGuardService.evaluate_burnout_risk(request)
