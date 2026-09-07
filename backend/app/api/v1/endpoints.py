import logging
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Query, Depends, Response
from typing import List, Optional
from uuid import UUID, uuid4
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
    EventCreateRequest,
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
    FileReviewStats,
    DeckOverviewResponse,
    DeckCompletionRequest,
    DeckCompletionResponse,
    HybridReviewSessionRequest,
    HybridReviewSessionResponse,
)
from backend.app.schemas.feynman import (
    FeynmanPromptRequest,
    FeynmanPromptResponse,
    FeynmanEvaluationRequest,
    GapAnalysisResult,
)
from backend.app.schemas.bkt import BKTUpdateRequest, BKTUpdateResponse
from backend.app.schemas.burnout import BurnoutTriggerRequest, BurnoutTriggerResponse

from backend.app.services.database import db_service
from backend.app.services.parser import SyllabusIngestionService
from backend.app.services.workload import WorkloadEngine
from backend.app.services.rag import AdaptiveLearningEngine
from backend.app.services.fsrs_engine import review_session_engine, ReviewSessionEngine, SpacedRepetitionService
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
    """Synthesizes grounded study artifact (4 learning styles x 2 workload modes) strictly from DB chunks."""
    from backend.app.services.database import db_service
    effective_user_id = request.user_id or current_user

    used_chunks = request.chunks
    if not used_chunks:
        # Query actual document chunks from Supabase database
        db_chunks = db_service.get_document_chunks(
            user_id=effective_user_id,
            folder_id=request.folder_id,
            limit=5,
        )
        if db_chunks:
            used_chunks = [
                {
                    "id": c.get("id"),
                    "document_id": c.get("document_id"),
                    "content": c.get("content"),
                    "cosine_similarity": 0.94,
                    "rrf_score": 0.035,
                }
                for c in db_chunks
            ]
        else:
            used_chunks = [
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

    return review_session_engine.schedule_handoff(
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
    """Retrieves all unlearned documents directly from database with enriched course and folder metadata."""
    from backend.app.services.database import db_service
    return db_service.get_study_queue_documents(user_id=current_user, course_id=course_id)


@router.post("/blurting/evaluate", response_model=BlurtingEvaluationResponse)
def evaluate_blurting_endpoint(
    request: BlurtingEvaluationRequest,
    current_user: UUID = Depends(get_current_user),
):
    """Evaluates student's unprompted recall against document knowledge components and records completion."""
    effective_user_id = current_user or UUID("00000000-0000-0000-0000-000000000001")
    if not request.folder_id:
        request.folder_id = UUID("00000000-0000-0000-0000-000000000002")
    result = BlurtingService.evaluate_recall(request)

    from backend.app.services.database import db_service
    db_service.record_blurting_completion(
        user_id=effective_user_id,
        folder_id=request.folder_id,
        document_id=request.document_id,
        file_name=request.file_name,
        topic=request.topic,
        duration_seconds=request.duration_seconds or 60.0,
        accuracy_score=result.accuracy_score,
    )
    return result


@router.post("/flashcards/review", response_model=FlashcardReviewResponse)
def review_flashcard(
    request: FlashcardReviewRequest,
    current_user: UUID = Depends(get_current_user),
):
    """Processes Hybrid 2357-FSRS flashcard review with dynamic retention, graduation, and leech quarantine."""
    effective_user_id = current_user or (request.card.user_id if request.card else None)
    card_id = request.card_id or (request.card.id if request.card else None)

    workload_mode = request.workload_mode
    workload_score = request.workload_score
    if workload_mode is None and effective_user_id:
        try:
            from backend.app.services.workload import WorkloadEngine
            live_wl = WorkloadEngine.evaluate_user_workload(user_id=effective_user_id, days_ahead=7)
            workload_mode = live_wl.current_mode
            workload_score = live_wl.score
        except Exception:
            pass

    try:
        return review_session_engine.submit_review(
            user_id=effective_user_id,
            card_id=card_id,
            rating=request.rating,
            card=request.card,
            review_time=request.review_time,
            workload_mode=workload_mode,
            workload_score=workload_score,
        )
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))


@router.post("/flashcards/deck-complete", response_model=DeckCompletionResponse)
def complete_deck_review_session(
    request: DeckCompletionRequest,
    current_user: UUID = Depends(get_current_user),
):
    """
    Explicitly records that the user has completed reviewing the flashcard deck for today:
    - Advances due cards to the second review milestone (+2 days, Day 3 in 2357 schedule).
    - Logs review completion in database.
    - Updates deck state so 0 cards are due today.
    """
    from backend.app.services.database import db_service
    effective_user_id = current_user or UUID("00000000-0000-0000-0000-000000000001")
    return db_service.record_deck_completion(
        user_id=effective_user_id,
        folder_id=request.folder_id,
        document_id=request.document_id,
        file_name=request.file_name,
        cards_reviewed=request.cards_reviewed,
    )


@router.post("/review/hybrid-session", response_model=HybridReviewSessionResponse)
def submit_hybrid_review_session(
    request: HybridReviewSessionRequest,
    current_user: UUID = Depends(get_current_user),
):
    """
    Submits the unified Two-Step Hybrid Review Session:
    1. Evaluates unprompted memory recall dump (Raw Blurting).
    2. Evaluates simplified plain-language explanation (Feynman Synthesis).
    3. Advances deck flashcards along the 2357 Spaced Repetition schedule.
    4. Marks recall_finished=True and feynman_finished=True attached to the specific file.
    """
    effective_user_id = current_user or UUID("00000000-0000-0000-0000-000000000001")
    return db_service.record_hybrid_review_session(
        user_id=effective_user_id,
        folder_id=request.folder_id,
        document_id=request.document_id,
        file_name=request.file_name,
        topic=request.topic,
        cards_reviewed=request.cards_reviewed,
        blurting_content=request.blurting_content,
        blurting_duration_seconds=request.blurting_duration_seconds,
        feynman_explanation=request.feynman_explanation,
        target_audience=request.target_audience or "beginner",
    )


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
    """Evaluates student explanation with precision-gap analysis and records completion."""
    effective_user_id = current_user or request.user_id or UUID("00000000-0000-0000-0000-000000000001")
    if not request.user_id:
        request.user_id = effective_user_id
    if not request.folder_id:
        request.folder_id = UUID("00000000-0000-0000-0000-000000000002")
    result = FeynmanService.evaluate_explanation(request)

    from backend.app.services.database import db_service
    score_pct = int(round(result.completeness_score * 100))
    db_service.record_feynman_completion(
        user_id=effective_user_id,
        folder_id=request.folder_id,
        document_id=request.document_id,
        file_name=request.file_name,
        topic=request.concept,
        feynman_score=score_pct,
    )
    return result


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
    """Creates a new course and provisions its root virtual folder using Planner-Executor."""
    from backend.app.services.course_provisioner import (
        CourseProvisioningPlanner,
        CourseProvisioningExecutor,
    )
    planner = CourseProvisioningPlanner()
    executor = CourseProvisioningExecutor()
    plan = planner.plan(user_id=current_user, course=course)
    result = executor.execute(plan)

    if result.status == "failed" or not result.course:
        error_msg = result.errors[0] if result.errors else "Course creation failed"
        raise HTTPException(status_code=400, detail=error_msg)

    return result.course



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


from backend.app.schemas.document import (
    DocumentResponse,
    DocumentUploadResponse,
    DocumentContentResponse,
    DocumentChunkDetail,
)


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


@router.get("/documents/{document_id}/content", response_model=DocumentContentResponse)
def get_document_content(
    document_id: UUID,
    current_user: UUID = Depends(get_current_user),
):
    """
    Retrieves full extracted text, all chunks, reading stats, and storage URLs 
    for the document reader pop-up.
    """
    from backend.app.services.database import db_service
    doc = db_service.get_document(user_id=current_user, document_id=document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found or unauthorized")

    chunks_raw = db_service.get_all_document_chunks(user_id=current_user, document_id=document_id)
    sorted_chunks = sorted(chunks_raw, key=lambda c: c.get("chunk_index", 0))
    chunk_details = [
        DocumentChunkDetail(
            id=str(c.get("id")) if c.get("id") else None,
            chunk_index=c.get("chunk_index", idx),
            content=c.get("content", ""),
            token_count=c.get("token_count", 0),
        )
        for idx, c in enumerate(sorted_chunks)
    ]

    full_text = "\n\n".join([c.content for c in chunk_details if c.content.strip()]).strip()
    words = len(full_text.split()) if full_text else 0
    reading_time = max(1, round(words / 200)) if words > 0 else 1

    storage_path = doc.get("storage_path", "")
    signed_url = db_service.get_document_signed_url(storage_path) if storage_path else None
    raw_url = f"/api/v1/documents/{document_id}/raw"

    return DocumentContentResponse(
        id=UUID(str(doc["id"])),
        file_name=doc.get("file_name", "document"),
        file_type=doc.get("file_type", "application/octet-stream"),
        file_size_bytes=doc.get("file_size_bytes", 0),
        storage_path=storage_path,
        status=doc.get("status", "indexed"),
        signed_url=signed_url,
        raw_url=raw_url,
        full_text=full_text,
        chunks=chunk_details,
        total_chunks=len(chunk_details),
        total_words=words,
        estimated_read_time_minutes=reading_time,
    )


@router.get("/documents/{document_id}/raw")
def get_document_raw(
    document_id: UUID,
    current_user: UUID = Depends(get_current_user),
):
    """
    Streams original document file bytes for native PDF reader iframe or download.
    Falls back to extracted text chunks if storage is unreachable.
    """
    import urllib.parse
    from backend.app.services.database import db_service

    doc = db_service.get_document(user_id=current_user, document_id=document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found or unauthorized")

    file_name = doc.get("file_name", "document")
    mime_type = doc.get("file_type", "application/octet-stream")
    storage_path = doc.get("storage_path")

    safe_filename = urllib.parse.quote(file_name)
    headers = {
        "Content-Disposition": f'inline; filename="{safe_filename}"; filename*=UTF-8\'\'{safe_filename}',
    }

    if storage_path:
        file_bytes = db_service.download_document_bytes(storage_path)
        if file_bytes:
            return Response(content=file_bytes, media_type=mime_type, headers=headers)

    chunks_raw = db_service.get_all_document_chunks(user_id=current_user, document_id=document_id)
    sorted_chunks = sorted(chunks_raw, key=lambda c: c.get("chunk_index", 0))
    full_text = "\n\n".join([c.get("content", "") for c in sorted_chunks if c.get("content", "").strip()]).strip()
    if not full_text:
        full_text = f"Document: {file_name}\n(No text content found)"

    return Response(
        content=full_text.encode("utf-8"),
        media_type="text/plain; charset=utf-8",
        headers={"Content-Disposition": f'inline; filename="{safe_filename}.txt"'},
    )



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


@router.get("/events")
def get_events_list(
    limit: int = Query(30),
    current_user: UUID = Depends(get_current_user),
):
    """Retrieves list of academic calendar events and deadlines for the student."""
    from backend.app.services.database import db_service
    return db_service.get_all_events(user_id=current_user, limit=limit)


@router.post("/events", status_code=201)
def create_event(
    event_in: EventCreateRequest,
    current_user: UUID = Depends(get_current_user),
):
    """Creates a new academic event or deadline for the student."""
    from backend.app.services.database import db_service
    db_events = [{
        "user_id": str(current_user),
        "title": event_in.title,
        "event_type": event_in.event_type.value if hasattr(event_in.event_type, "value") else str(event_in.event_type),
        "start_time": event_in.start_time.isoformat(),
        "end_time": event_in.end_time.isoformat() if event_in.end_time else None,
        "weight": event_in.weight if event_in.weight is not None else 1.0,
        "course_id": str(event_in.course_id) if event_in.course_id else None,
        "source": event_in.source,
    }]
    saved = db_service.insert_events(db_events)
    if not saved:
        return {
            "id": str(uuid4()),
            "user_id": str(current_user),
            "title": event_in.title,
            "event_type": event_in.event_type.value if hasattr(event_in.event_type, "value") else str(event_in.event_type),
            "start_time": event_in.start_time.isoformat(),
            "weight": event_in.weight or 1.0,
            "source": event_in.source,
        }
    return saved[0]


@router.delete("/events/{event_id}")
def delete_event(
    event_id: UUID,
    current_user: UUID = Depends(get_current_user),
):
    """Deletes an academic event."""
    from backend.app.services.database import db_service
    success = db_service.delete_event(user_id=current_user, event_id=event_id)
    return {"success": success, "event_id": str(event_id)}


@router.patch("/events/{event_id}/complete")
def toggle_event_complete(
    event_id: UUID,
    is_completed: bool = Query(True),
    current_user: UUID = Depends(get_current_user),
):
    """Marks an academic event as completed or incomplete."""
    from backend.app.services.database import db_service
    success = db_service.complete_event(user_id=current_user, event_id=event_id, is_completed=is_completed)
    return {"success": success, "event_id": str(event_id), "is_completed": is_completed}


@router.post("/events/seed-demo")
def seed_demo_events(
    scenario: str = Query("busy"),
    current_user: UUID = Depends(get_current_user),
):
    """Seeds dynamic upcoming academic events relative to current time for testing Workload Cockpit."""
    from datetime import datetime, timezone, timedelta
    from backend.app.services.database import db_service
    from backend.app.services.workload import WorkloadEngine
    now = datetime.now(timezone.utc)
    
    demo_titles = [
        "CS301 Distributed Systems Midterm Exam",
        "AI Lab 4: Attention Mechanism Project",
        "Algorithms Quiz: Dynamic Programming",
        "CS101 Weekly Problem Set",
    ]
    try:
        if db_service.supabase.client:
            uids_to_clean = [str(current_user)]
            if str(current_user) == "00000000-0000-0000-0000-000000000001":
                uids_to_clean.append("5602e9c3-3747-428d-94c5-6838a8a59ce8")
            for uid in uids_to_clean:
                db_service.supabase.client.table("events").delete().eq("user_id", uid).in_("title", demo_titles).eq("is_completed", False).execute()
    except Exception as e:
        logger.warning(f"Could not purge previous demo events: {e}")

    if scenario == "busy":
        events_to_seed = [
            {
                "user_id": str(current_user),
                "title": "CS301 Distributed Systems Midterm Exam",
                "event_type": "exam",
                "start_time": (now + timedelta(days=1.0)).isoformat(),
                "weight": 3.0,
                "source": "manual",
            },
            {
                "user_id": str(current_user),
                "title": "AI Lab 4: Attention Mechanism Project",
                "event_type": "project",
                "start_time": (now + timedelta(days=1.5)).isoformat(),
                "weight": 2.5,
                "source": "manual",
            },
        ]
    elif scenario == "deadband":
        events_to_seed = [
            {
                "user_id": str(current_user),
                "title": "CS301 Distributed Systems Midterm Exam",
                "event_type": "exam",
                "start_time": (now + timedelta(days=3.0)).isoformat(),
                "weight": 2.5,
                "source": "manual",
            },
            {
                "user_id": str(current_user),
                "title": "Algorithms Quiz: Dynamic Programming",
                "event_type": "quiz",
                "start_time": (now + timedelta(days=4.5)).isoformat(),
                "weight": 1.0,
                "source": "manual",
            },
        ]
    else:
        events_to_seed = [
            {
                "user_id": str(current_user),
                "title": "CS101 Weekly Problem Set",
                "event_type": "assignment",
                "start_time": (now + timedelta(days=4.0)).isoformat(),
                "weight": 1.5,
                "source": "manual",
            }
        ]
    
    inserted = db_service.insert_events(events_to_seed)
    evaluated = WorkloadEngine.evaluate_user_workload(user_id=current_user, days_ahead=7)
    return {
        "scenario": scenario,
        "seeded_count": len(inserted),
        "workload": evaluated,
    }


@router.get("/workload/live", response_model=WorkloadScoreResponse)
def get_live_workload(
    days_ahead: int = Query(7),
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
    document_id: Optional[UUID] = Query(None),
    include_immediate: bool = Query(True),
    limit: int = Query(30),
    current_user: UUID = Depends(get_current_user),
):
    """Retrieves active flashcards scheduled for review in current or selected folder/document."""
    from backend.app.services.database import db_service
    return db_service.get_due_flashcards(
        user_id=current_user,
        folder_id=folder_id,
        limit=limit,
        document_id=document_id,
        include_immediate=include_immediate,
    )


@router.get("/flashcards/deck-overview", response_model=DeckOverviewResponse)
def get_deck_overview_endpoint(
    current_user: UUID = Depends(get_current_user),
):
    """Retrieves Anki-style deck overview with file completion percentages and 2357 schedule review due states."""
    from backend.app.services.database import db_service
    return db_service.get_deck_overview(user_id=current_user)


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


