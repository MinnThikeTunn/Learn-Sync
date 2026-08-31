from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Query, Depends
from typing import List, Optional
from uuid import UUID

from backend.app.core.auth import get_current_user
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
    course_id: UUID = Form(...),
    file: UploadFile = File(...),
    user_id: Optional[UUID] = Form(None),
    current_user: UUID = Depends(get_current_user),
):
    """Uploads syllabus PDF and generates staged virtual folders and parsed events."""
    effective_user_id = current_user or user_id
    content = await file.read()
    service = SyllabusIngestionService()
    parsed = service.parse_syllabus(content, file.filename)
    folders = service.build_virtual_folder_hierarchy(
        course_code=parsed.course_code,
        modules=parsed.modules,
        course_id=course_id,
        user_id=effective_user_id,
    )
    return StagedSyllabusPreviewResponse(
        syllabus=parsed,
        suggested_folders=folders,
        suggested_events=parsed.events,
    )


@router.post("/workload/evaluate", response_model=WorkloadScoreResponse)
async def evaluate_workload(
    request: WorkloadCalculationRequest,
    current_user: UUID = Depends(get_current_user),
):
    """Calculates rolling 3-day Workload Score W(t) and Schmitt hysteresis state."""
    response, spike_event = WorkloadEngine.evaluate(request)
    if spike_event:
        event_publisher.publish_workload_spike(spike_event)
    return response


@router.post("/artifacts/generate", response_model=StudyArtifact)
async def generate_study_artifact(
    request: GenerateArtifactRequest,
    current_user: UUID = Depends(get_current_user),
):
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
    current_user: UUID = Depends(get_current_user),
):
    """Processes FSRS flashcard review with dynamic retention and leech quarantine."""
    return SpacedRepetitionService.process_review(
        card=card,
        rating=rating,
        workload_mode=workload_mode,
        workload_score=workload_score,
    )


@router.post("/feynman/prompt", response_model=FeynmanPromptResponse)
async def get_feynman_prompt(
    request: FeynmanPromptRequest,
    current_user: UUID = Depends(get_current_user),
):
    """Generates active recall Feynman explanation prompt."""
    return FeynmanService.generate_prompt(request)


@router.post("/feynman/evaluate", response_model=GapAnalysisResult)
async def evaluate_feynman_explanation(
    request: FeynmanEvaluationRequest,
    current_user: UUID = Depends(get_current_user),
):
    """Evaluates student explanation with precision-gap analysis and auto-generates remedial cards."""
    return FeynmanService.evaluate_explanation(request)


@router.post("/bkt/update", response_model=BKTUpdateResponse)
async def update_bkt_mastery(
    request: BKTUpdateRequest,
    current_user: UUID = Depends(get_current_user),
):
    """Updates Bayesian Knowledge Tracing posterior mastery state."""
    return BKTService.update_mastery(request)


@router.post("/burnout/check", response_model=BurnoutTriggerResponse)
async def check_burnout_risk(
    request: BurnoutTriggerRequest,
    current_user: UUID = Depends(get_current_user),
):
    """Monitors acute 48h deadline clusters and triggers 90-second B=MAP micro-tasks."""
    return BurnoutGuardService.evaluate_burnout_risk(request)


# =====================================================================
# Extended Resource Management & Live Integrations
# =====================================================================

@router.get("/folders/tree")
async def get_folders_tree(
    course_id: Optional[UUID] = Query(None),
    current_user: UUID = Depends(get_current_user),
):
    """Retrieves full nested virtual folder hierarchy for the authenticated student."""
    from backend.app.services.database import db_service
    return db_service.get_virtual_folders(user_id=current_user, course_id=course_id)


@router.post("/folders")
async def create_folder(
    course_id: UUID = Form(...),
    name: str = Form(...),
    parent_path: str = Form(""),
    parent_depth: int = Form(0),
    current_user: UUID = Depends(get_current_user),
):
    """Creates a new nested virtual folder and computes materialized path."""
    from backend.app.services.database import db_service
    return db_service.create_virtual_folder(
        user_id=current_user,
        course_id=course_id,
        name=name,
        parent_path=parent_path,
        parent_depth=parent_depth,
    )


@router.get("/oauth/google/url")
async def get_google_oauth_url(
    current_user: UUID = Depends(get_current_user),
):
    """Generates official Google OAuth 2.0 Authorization URL for Calendar & Gmail access."""
    from backend.app.services.calendar_sync import google_sync_service
    url = google_sync_service.get_oauth_url(user_id=current_user)
    return {"auth_url": url}


@router.post("/oauth/google/sync")
async def sync_google_calendar(
    access_token: str = Form(...),
    days_ahead: int = Form(14),
    current_user: UUID = Depends(get_current_user),
):
    """Synchronizes upcoming deadlines from Google Calendar API into Supabase events store."""
    from backend.app.services.calendar_sync import google_sync_service
    from backend.app.services.database import db_service
    from datetime import datetime, timezone, timedelta

    now = datetime.now(timezone.utc)
    future = now + timedelta(days=days_ahead)
    events = google_sync_service.fetch_calendar_events(
        access_token=access_token,
        time_min=now,
        time_max=future,
    )

    db_events = []
    for evt in events:
        db_events.append({
            "user_id": str(current_user),
            "title": evt["title"],
            "event_type": evt["event_type"],
            "start_time": evt["start_time"],
            "end_time": evt.get("end_time"),
            "weight": evt["weight"],
            "source": "google_calendar",
        })

    saved = db_service.insert_events(db_events)
    return {"synced_count": len(saved), "events": saved}


@router.get("/workload/live", response_model=WorkloadScoreResponse)
async def get_live_workload(
    days_ahead: int = Query(3),
    previous_mode: Optional[WorkloadMode] = Query(None),
    current_user: UUID = Depends(get_current_user),
):
    """Calculates live rolling Workload Score W(t) and mode from user's Supabase events."""
    return WorkloadEngine.evaluate_user_workload(
        user_id=current_user,
        previous_mode=previous_mode,
        days_ahead=days_ahead,
    )


@router.get("/flashcards/due")
async def get_due_flashcards_queue(
    folder_id: Optional[UUID] = Query(None),
    limit: int = Query(30),
    current_user: UUID = Depends(get_current_user),
):
    """Retrieves active flashcards scheduled for review in current or selected folder."""
    from backend.app.services.database import db_service
    return db_service.get_due_flashcards(user_id=current_user, folder_id=folder_id, limit=limit)


@router.post("/syllabus/commit")
async def commit_staged_syllabus(
    course_id: UUID,
    staged: StagedSyllabusPreviewResponse,
    current_user: UUID = Depends(get_current_user),
):
    """Commits staged virtual folders and parsed exam deadlines to the database."""
    from backend.app.services.database import db_service

    created_folders = []
    for f in staged.suggested_folders:
        folder_res = db_service.create_virtual_folder(
            user_id=current_user,
            course_id=course_id,
            name=f.name,
            parent_id=f.parent_id,
            parent_path=f.materialized_path.rsplit("/", 1)[0] if "/" in f.materialized_path else "",
            parent_depth=f.depth,
        )
        created_folders.append(folder_res)

    events_to_save = []
    for e in staged.suggested_events:
        events_to_save.append({
            "user_id": str(current_user),
            "course_id": str(course_id),
            "title": e.title,
            "event_type": e.event_type.value,
            "start_time": e.start_time.isoformat(),
            "weight": e.weight,
            "source": "syllabus",
        })

    saved_events = db_service.insert_events(events_to_save)

    return {
        "committed_folders": len(created_folders),
        "committed_events": len(saved_events),
    }

