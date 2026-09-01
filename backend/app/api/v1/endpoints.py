import logging
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Query, Depends
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

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
    ScheduleStage,
    StudyCompletionRequest,
    StudyCompletionResponse,
    BlurtingEvaluationRequest,
    BlurtingEvaluationResponse,
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
from backend.app.services.blurting import BlurtingService
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
def evaluate_workload(
    request: WorkloadCalculationRequest,
    current_user: UUID = Depends(get_current_user),
):
    """Calculates rolling 3-day Workload Score W(t) and Schmitt hysteresis state."""
    response, spike_event = WorkloadEngine.evaluate(request)
    if spike_event:
        event_publisher.publish_workload_spike(spike_event)
    return response


@router.post("/artifacts/generate", response_model=StudyArtifact)
def generate_study_artifact(
    request: GenerateArtifactRequest,
    current_user: UUID = Depends(get_current_user),
):
    """Synthesizes grounded study artifact (4 learning styles x 2 workload modes)."""
    effective_user_id = request.user_id or current_user
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


@router.post("/study/complete-lesson", response_model=StudyCompletionResponse)
def complete_study_lesson_endpoint(
    request: StudyCompletionRequest,
    current_user: UUID = Depends(get_current_user),
):
    """Executes Study-to-Review Handoff: marks document learned and schedules Day 1 of 2357 Spaced Schedule."""
    from backend.app.services.database import db_service
    if request.document_id:
        try:
            db_service.mark_document_learned(user_id=current_user, document_id=request.document_id, is_learned=True)
        except Exception as e:
            logger.warning(f"Could not update document status to learned: {e}")

    return SpacedRepetitionService.complete_study_lesson(
        user_id=current_user,
        folder_id=request.folder_id,
        topic=request.topic,
        document_id=request.document_id,
        learning_style=request.learning_style or "visual",
    )


@router.get("/study/queue")
def get_study_unlearned_queue(
    course_id: Optional[UUID] = Query(None),
    current_user: UUID = Depends(get_current_user),
):
    """Retrieves all unlearned documents across student's virtual folders with enriched metadata."""
    from backend.app.services.database import db_service
    docs = db_service.get_documents(user_id=current_user, course_id=course_id)
    # Filter for documents not yet marked 'learned'
    unlearned = [d for d in docs if d.get("status") != "learned"]
    return unlearned


@router.post("/blurting/evaluate", response_model=BlurtingEvaluationResponse)
def evaluate_blurting_endpoint(
    request: BlurtingEvaluationRequest,
    current_user: UUID = Depends(get_current_user),
):
    """Evaluates student's unprompted recall against document knowledge components."""
    if not request.folder_id:
        request.folder_id = UUID("00000000-0000-0000-0000-000000000002")
    return BlurtingService.evaluate_recall(request)


@router.post("/flashcards/review", response_model=FlashcardReviewResponse)
def review_flashcard(
    request: FlashcardReviewRequest,
    current_user: UUID = Depends(get_current_user),
):
    """Processes Hybrid 2357-FSRS flashcard review with dynamic retention, graduation, and leech quarantine."""
    from backend.app.services.database import db_service
    card = request.card
    if not card:
        raise HTTPException(status_code=400, detail="Flashcard payload is required in 'card' field")

    response = SpacedRepetitionService.process_review(
        card=card,
        rating=request.rating,
        review_time=request.review_time,
        workload_mode=request.workload_mode,
        workload_score=request.workload_score,
    )

    try:
        db_service.update_flashcard_state(
            flashcard_id=card.id,
            stability=response.card.stability,
            difficulty=response.card.difficulty,
            due=response.card.due,
            lapses=response.card.lapses,
            is_leech=response.card.is_leech,
            is_paused=response.card.is_paused,
            stage=response.stage.value if response.stage else None,
        )
        db_service.log_review(
            user_id=current_user,
            flashcard_id=card.id,
            rating=int(request.rating),
            state=int(response.card.state),
            scheduled_days=response.scheduled_days,
            elapsed_days=response.elapsed_days,
        )
    except Exception as e:
        logger.warning(f"Failed to persist flashcard state to db: {e}")

    return response


@router.post("/feynman/prompt", response_model=FeynmanPromptResponse)
def get_feynman_prompt(
    request: FeynmanPromptRequest,
    current_user: UUID = Depends(get_current_user),
):
    """Generates active recall Feynman explanation prompt."""
    if not request.user_id:
        request.user_id = current_user
    if not request.folder_id:
        request.folder_id = UUID("00000000-0000-0000-0000-000000000002")
    return FeynmanService.generate_prompt(request)


@router.post("/feynman/evaluate", response_model=GapAnalysisResult)
def evaluate_feynman_explanation(
    request: FeynmanEvaluationRequest,
    current_user: UUID = Depends(get_current_user),
):
    """Evaluates student explanation with precision-gap analysis and auto-generates remedial cards."""
    if not request.user_id:
        request.user_id = current_user
    if not request.folder_id:
        request.folder_id = UUID("00000000-0000-0000-0000-000000000002")
    return FeynmanService.evaluate_explanation(request)


@router.post("/bkt/update", response_model=BKTUpdateResponse)
def update_bkt_mastery(
    request: BKTUpdateRequest,
    current_user: UUID = Depends(get_current_user),
):
    """Updates Bayesian Knowledge Tracing posterior mastery state."""
    return BKTService.update_mastery(request)


@router.post("/burnout/check", response_model=BurnoutTriggerResponse)
def check_burnout_risk(
    request: BurnoutTriggerRequest,
    current_user: UUID = Depends(get_current_user),
):
    """Monitors acute 48h deadline clusters and triggers 90-second B=MAP micro-tasks."""
    return BurnoutGuardService.evaluate_burnout_risk(request)


# =====================================================================
# Extended Resource Management & Live Integrations
# =====================================================================

from backend.app.schemas.course import CourseCreate, CourseResponse


@router.get("/courses", response_model=List[CourseResponse])
def get_courses(
    current_user: UUID = Depends(get_current_user),
):
    """Retrieves all academic courses for the authenticated student."""
    from backend.app.services.database import db_service
    return db_service.get_courses(user_id=current_user)


@router.post("/courses", response_model=CourseResponse, status_code=201)
def create_course(
    course: CourseCreate,
    current_user: UUID = Depends(get_current_user),
):
    """Creates a new course and provisions its root virtual folder."""
    from backend.app.services.database import db_service
    created = db_service.create_course(
        user_id=current_user,
        name=course.name,
        code=course.code,
        term=course.term,
        color=course.color,
        description=course.description,
    )
    course_id = created.get("id")
    if course_id:
        try:
            db_service.create_virtual_folder(
                user_id=current_user,
                course_id=course_id,
                name=course.code,
                parent_id=None,
                parent_path="",
                parent_depth=0,
            )
        except Exception:
            pass
    return created


@router.delete("/courses/{course_id}")
def delete_course(
    course_id: UUID,
    current_user: UUID = Depends(get_current_user),
):
    """Deletes a course and all associated virtual folders, documents, and vector embeddings."""
    from backend.app.services.database import db_service
    success = db_service.delete_course(user_id=current_user, course_id=course_id)
    if not success:
        raise HTTPException(status_code=404, detail="Course not found or unauthorized")
    return {"status": "deleted", "id": str(course_id)}


@router.get("/folders")
@router.get("/folders/tree")
def get_folders_tree(
    course_id: Optional[UUID] = Query(None),
    current_user: UUID = Depends(get_current_user),
):
    """Retrieves full nested virtual folder hierarchy for the authenticated student."""
    from backend.app.services.database import db_service
    return db_service.get_virtual_folders(user_id=current_user, course_id=course_id)


class FolderCreateRequest(BaseModel):
    course_id: UUID
    name: str
    parent_id: Optional[UUID] = None
    parent_path: Optional[str] = ""
    parent_depth: Optional[int] = 0


@router.post("/folders")
def create_folder(
    request: FolderCreateRequest,
    current_user: UUID = Depends(get_current_user),
):
    """Creates a new nested virtual folder and computes materialized path."""
    from backend.app.services.database import db_service
    return db_service.create_virtual_folder(
        user_id=current_user,
        course_id=request.course_id,
        name=request.name,
        parent_id=request.parent_id,
        parent_path=request.parent_path or "",
        parent_depth=request.parent_depth or 0,
    )


@router.delete("/folders/{folder_id}")
def delete_folder(
    folder_id: UUID,
    current_user: UUID = Depends(get_current_user),
):
    """Deletes a virtual folder and all contained documents from Supabase storage and database."""
    from backend.app.services.database import db_service
    success = db_service.delete_virtual_folder(user_id=current_user, folder_id=folder_id)
    if not success:
        raise HTTPException(status_code=404, detail="Folder not found or unauthorized")
    return {"status": "deleted", "id": str(folder_id)}


from backend.app.schemas.document import DocumentResponse, DocumentUploadResponse


@router.post("/documents/upload", response_model=DocumentUploadResponse, status_code=201)
async def upload_document(
    course_id: str = Form(...),
    folder_id: Optional[str] = Form(None),
    file: UploadFile = File(...),
    current_user: UUID = Depends(get_current_user),
):
    """Uploads document file to Supabase Storage, creates records, and chunks into pgvector."""
    from backend.app.services.document_processor import document_service
    file_bytes = await file.read()
    mime_type = file.content_type or "application/octet-stream"
    course_uuid = UUID(course_id)
    folder_uuid = UUID(folder_id) if folder_id and folder_id.strip() and folder_id.lower() not in ("null", "undefined") else None
    doc_record, chunks_created = document_service.process_and_store_document(
        user_id=current_user,
        course_id=course_uuid,
        folder_id=folder_uuid,
        file_name=file.filename or "document.txt",
        file_bytes=file_bytes,
        mime_type=mime_type,
    )
    doc_record["chunks_created"] = chunks_created
    return doc_record


@router.get("/documents", response_model=List[DocumentResponse])
def list_documents(
    course_id: Optional[UUID] = Query(None),
    folder_id: Optional[UUID] = Query(None),
    current_user: UUID = Depends(get_current_user),
):
    """Retrieves uploaded documents filtered by folder and/or course."""
    from backend.app.services.database import db_service
    return db_service.get_documents(user_id=current_user, folder_id=folder_id, course_id=course_id)


@router.delete("/documents/{document_id}")
def delete_document(
    document_id: UUID,
    current_user: UUID = Depends(get_current_user),
):
    """Deletes a document from Supabase storage, database, and chunk vector embeddings."""
    from backend.app.services.database import db_service
    success = db_service.delete_document(user_id=current_user, document_id=document_id)
    if not success:
        raise HTTPException(status_code=404, detail="Document not found or unauthorized")
    return {"status": "deleted", "id": str(document_id)}


@router.get("/oauth/google/url")
def get_google_oauth_url(
    current_user: UUID = Depends(get_current_user),
):
    """Generates official Google OAuth 2.0 Authorization URL for Calendar & Gmail access."""
    from backend.app.services.calendar_sync import google_sync_service
    url = google_sync_service.get_oauth_url(user_id=current_user)
    return {"auth_url": url}


@router.post("/oauth/google/sync")
def sync_google_calendar(
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
def get_live_workload(
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
def get_due_flashcards_queue(
    folder_id: Optional[UUID] = Query(None),
    limit: int = Query(30),
    current_user: UUID = Depends(get_current_user),
):
    """Retrieves active flashcards scheduled for review in current or selected folder."""
    from backend.app.services.database import db_service
    return db_service.get_due_flashcards(user_id=current_user, folder_id=folder_id, limit=limit)


@router.post("/syllabus/commit")
def commit_staged_syllabus(
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


from pydantic import BaseModel, Field


class OnboardingAssessmentSubmitRequest(BaseModel):
    responses: List[str] = Field(..., description="List of 4 answers ('V', 'A', 'R', or 'K')")


@router.get("/onboarding/questions")
def get_onboarding_questions():
    """Returns the 4 Micro-VARK situational questions for onboarding assessment."""
    from backend.app.services.learner_assessment import VARK_QUESTIONS
    return {"questions": VARK_QUESTIONS}


@router.get("/onboarding/status")
def get_onboarding_status(
    current_user: UUID = Depends(get_current_user),
):
    """Checks whether the student has completed onboarding and their diagnosed learning style."""
    from backend.app.services.database import db_service
    profile = db_service.get_user_learning_style(user_id=current_user)
    if not profile:
        return {
            "onboarding_completed": False,
            "learning_style": None,
            "secondary_learning_style": None,
        }
    return {
        "onboarding_completed": profile.get("onboarding_completed", False),
        "learning_style": profile.get("learning_style"),
        "secondary_learning_style": profile.get("secondary_learning_style"),
        "assessment_scores": profile.get("assessment_scores"),
    }


@router.post("/onboarding/assessment")
def submit_onboarding_assessment(
    request: OnboardingAssessmentSubmitRequest,
    current_user: UUID = Depends(get_current_user),
):
    """Evaluates student Micro-VARK responses, assigns cognitive archetype, and saves to profile."""
    from backend.app.services.learner_assessment import learner_assessment_agent
    from backend.app.services.database import db_service

    result = learner_assessment_agent.evaluate_responses(request.responses)

    updated_profile = db_service.save_learning_style_assessment(
        user_id=current_user,
        primary_style=result.primary_style,
        secondary_style=result.secondary_style,
        scores=result.scores,
    )

    return {
        "status": "success",
        "assessment": result.model_dump(),
        "profile": updated_profile,
    }


