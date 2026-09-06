import uuid
import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient

from backend.app.schemas.fsrs import (
    Rating,
    CardState,
    ScheduleStage,
    FlashcardModel,
    StudyCompletionRequest,
    BlurtingEvaluationRequest,
    FlashcardReviewRequest,
)
from backend.app.schemas.feynman import (
    FeynmanPromptRequest,
    FeynmanPromptTarget,
    FeynmanEvaluationRequest,
)
from backend.app.schemas.workload import WorkloadMode
from backend.app.services.fsrs_engine import ReviewSessionEngine
from backend.app.services.review_repository import InMemoryReviewAdapter
from backend.app.services.blurting import BlurtingService
from backend.app.services.feynman import FeynmanService
from backend.app.main import app

client = TestClient(app)


# =====================================================================
# 1. Full Study-to-Review Lifecycle & 2357 Graduation Seam Tests
# =====================================================================

def test_full_study_to_review_lifecycle_graduation_and_leech():
    """
    Validates complete end-to-end learning lifecycle:
    1. Study-to-Review handoff provisions Day 1 cards
    2. Review progressing through 2357 schedule (Day 1 -> Day 3 -> Day 5 -> Day 7 -> Graduated FSRS)
    3. FSRS elastic retrievability scaling under Free vs Busy workload modes
    4. Leech quarantine triggering upon reaching 4 lapses
    """
    user_id = uuid.uuid4()
    folder_id = uuid.uuid4()
    doc_id = uuid.uuid4()
    topic = "Autonomous Agent Orchestration"

    adapter = InMemoryReviewAdapter()
    engine = ReviewSessionEngine(repository=adapter)

    # Step 1: Study-to-Review handoff
    handoff_res = engine.schedule_handoff(
        user_id=user_id,
        folder_id=folder_id,
        topic=topic,
        document_id=doc_id,
        learning_style="visual",
    )
    assert handoff_res.status == "success"
    assert handoff_res.cards_scheduled >= 3
    assert handoff_res.stage == ScheduleStage.DAY_1
    assert handoff_res.first_due_date > datetime.now(timezone.utc)

    # Step 2: Retrieve provisioned cards from adapter
    assert len(adapter.cards) >= 3
    target_card_id = list(adapter.cards.keys())[0]
    target_card = adapter.cards[target_card_id]
    assert target_card.stage == ScheduleStage.DAY_1

    # Step 3: Day 1 Review -> Rating: GOOD -> Advances to Day 3 (+2 days)
    rev_d1 = engine.submit_review(
        user_id=user_id,
        card_id=target_card_id,
        rating=Rating.GOOD,
        workload_mode=WorkloadMode.FREE,
    )
    assert rev_d1.stage == ScheduleStage.DAY_3
    assert rev_d1.scheduled_days == 2.0
    assert rev_d1.is_graduated is False
    assert rev_d1.applied_mode == WorkloadMode.FREE

    # Step 4: Day 3 Review -> Rating: GOOD -> Advances to Day 5 (+2 days)
    rev_d3 = engine.submit_review(
        user_id=user_id,
        card_id=target_card_id,
        rating=Rating.GOOD,
        workload_mode=WorkloadMode.FREE,
    )
    assert rev_d3.stage == ScheduleStage.DAY_5
    assert rev_d3.scheduled_days == 2.0
    assert rev_d3.is_graduated is False

    # Step 5: Day 5 Review -> Rating: EASY -> Advances to Day 7 (+2 days)
    rev_d5 = engine.submit_review(
        user_id=user_id,
        card_id=target_card_id,
        rating=Rating.EASY,
        workload_mode=WorkloadMode.FREE,
    )
    assert rev_d5.stage == ScheduleStage.DAY_7
    assert rev_d5.scheduled_days == 2.0
    assert rev_d5.is_graduated is False

    # Step 6: Day 7 Consolidation -> Rating: GOOD -> Graduates into continuous FSRS!
    rev_d7 = engine.submit_review(
        user_id=user_id,
        card_id=target_card_id,
        rating=Rating.GOOD,
        workload_mode=WorkloadMode.FREE,
    )
    assert rev_d7.stage == ScheduleStage.GRADUATED_FSRS
    assert rev_d7.is_graduated is True
    assert rev_d7.card.stability >= 14.0

    # Step 7: Continuous FSRS under Busy Mode (W(t) > 0.70)
    # Target retention drops to 0.80 and interval multiplier expands to 1.75x
    rev_fsrs_busy = engine.submit_review(
        user_id=user_id,
        card_id=target_card_id,
        rating=Rating.GOOD,
        workload_score=0.85,
    )
    assert rev_fsrs_busy.applied_mode == WorkloadMode.BUSY
    assert rev_fsrs_busy.target_retention == 0.80
    assert rev_fsrs_busy.interval_multiplier == 1.75
    assert rev_fsrs_busy.scheduled_days >= 10.0

    # Step 8: Repeated failures trigger Leech Quarantine (threshold = 4 lapses)
    # Fail card 4 times
    for i in range(4):
        rev_fail = engine.submit_review(
            user_id=user_id,
            card_id=target_card_id,
            rating=Rating.AGAIN,
            workload_mode=WorkloadMode.FREE,
        )

    assert rev_fail.card.lapses >= 4
    assert rev_fail.card.is_leech is True
    assert rev_fail.card.is_paused is True
    assert rev_fail.is_leech_triggered is True
    assert rev_fail.leech_notice is not None
    assert rev_fail.leech_notice.lapses >= 4

    # Verify adapter persisted quarantine state
    quarantined_card = adapter.get_card(target_card_id)
    assert quarantined_card.is_leech is True
    assert quarantined_card.is_paused is True


# =====================================================================
# 2. Blurting Active Recall Evaluation Verification
# =====================================================================

def test_blurting_service_comprehensive_evaluation():
    """
    Verifies Blurting semantic recall:
    1. High-accuracy recall with expected foundational concepts
    2. Low-accuracy recall identifying omitted invariants
    3. Auto-generation of targeted remedial flashcards
    """
    topic = "Recursion & Call Stack Frames"

    # High coverage recall
    req_good = BlurtingEvaluationRequest(
        topic=topic,
        user_recall_text=(
            "Recursion is when a function calls itself. It requires a base case to terminate execution "
            "and avoid call stack overflow errors. Call stack frames are dynamically allocated in memory, "
            "and return values are propagated back up the stack as each frame resolves."
        ),
    )
    res_good = BlurtingService.evaluate_recall(req_good)
    assert res_good.accuracy_score >= 80
    assert len(res_good.retained_concepts) >= 3
    assert "revis" in res_good.recommended_focus.lower() or "exam" in res_good.recommended_focus.lower()

    # Low coverage recall with critical omissions
    req_poor = BlurtingEvaluationRequest(
        topic=topic,
        user_recall_text="It loops and loops without stopping.",
    )
    res_poor = BlurtingService.evaluate_recall(req_poor)
    assert res_poor.accuracy_score < 50
    assert len(res_poor.missed_nuances) > 0


# =====================================================================
# 3. Feynman Explainer & Precision-Gap Analysis Verification
# =====================================================================

def test_feynman_service_audience_prompts_and_gap_evaluation():
    """
    Verifies Feynman multi-audience prompts and precision-gap analysis.
    """
    concept = "Reciprocal Rank Fusion"

    # Audience Prompt: Child
    p_child = FeynmanService.generate_prompt(
        FeynmanPromptRequest(
            concept=concept,
            target_audience=FeynmanPromptTarget.CHILD,
        )
    )
    assert "10-year-old child" in p_child.prompt_text
    assert p_child.analogy_hint is not None

    # Audience Prompt: Non-Technical
    p_nontech = FeynmanService.generate_prompt(
        FeynmanPromptRequest(
            concept=concept,
            target_audience=FeynmanPromptTarget.NON_TECHNICAL,
        )
    )
    assert "non-technical" in p_nontech.prompt_text.lower()

    # Gap Analysis with Misconception & Auto-Flashcard generation
    gap_req = FeynmanEvaluationRequest(
        concept="Recursion",
        student_explanation="It is just an infinite loop is required and stored in hard drive permanently.",
        auto_generate_flashcards=True,
    )
    gap_res = FeynmanService.evaluate_explanation(gap_req)
    assert gap_res.is_sufficient is False
    assert gap_res.completeness_score < 0.60
    assert len(gap_res.misconceptions) >= 1
    assert any("infinite loop" in m.student_claim.lower() for m in gap_res.misconceptions)
    assert len(gap_res.generated_flashcards) >= 1
    assert "terminat" in gap_res.generated_flashcards[0].back.lower() or "overflow" in gap_res.generated_flashcards[0].back.lower()


# =====================================================================
# 4. FastAPI Endpoints Verification for Review Ecosystem
# =====================================================================

def test_fastapi_review_endpoints_integration():
    """
    Verifies REST endpoints for the complete review suite:
    - POST /api/v1/study/complete-lesson
    - POST /api/v1/blurting/evaluate
    - POST /api/v1/feynman/prompt
    - POST /api/v1/feynman/evaluate
    - POST /api/v1/flashcards/review
    """
    user_id = str(uuid.uuid4())
    folder_id = str(uuid.uuid4())

    # 1. Handoff Endpoint
    res_handoff = client.post(
        "/api/v1/study/complete-lesson",
        json={
            "folder_id": folder_id,
            "topic": "Bayesian Knowledge Tracing",
            "learning_style": "visual",
        },
        headers={"X-Test-User-Id": user_id},
    )
    assert res_handoff.status_code == 200
    h_data = res_handoff.json()
    assert h_data["status"] == "success"
    assert h_data["stage"] == "2357_day1"

    # 2. Blurting Endpoint
    res_blurting = client.post(
        "/api/v1/blurting/evaluate",
        json={
            "folder_id": folder_id,
            "topic": "Bayesian Knowledge Tracing",
            "user_recall_text": "BKT tracks student latent knowledge state over discrete practice opportunities.",
        },
        headers={"X-Test-User-Id": user_id},
    )
    assert res_blurting.status_code == 200
    b_data = res_blurting.json()
    assert "accuracy_score" in b_data
    assert "retained_concepts" in b_data

    # 3. Feynman Prompt Endpoint
    res_feynman_p = client.post(
        "/api/v1/feynman/prompt",
        json={
            "concept": "Bayesian Knowledge Tracing",
            "target_audience": "child",
        },
        headers={"X-Test-User-Id": user_id},
    )
    assert res_feynman_p.status_code == 200
    fp_data = res_feynman_p.json()
    assert "prompt_text" in fp_data
    assert "analogy_hint" in fp_data

    # 4. Feynman Evaluate Endpoint
    res_feynman_e = client.post(
        "/api/v1/feynman/evaluate",
        json={
            "concept": "Recursion",
            "student_explanation": "Recursion requires a base case to terminate execution without stack overflow.",
            "auto_generate_flashcards": True,
        },
        headers={"X-Test-User-Id": user_id},
    )
    assert res_feynman_e.status_code == 200
    fe_data = res_feynman_e.json()
    assert fe_data["completeness_score"] >= 0.70

    # 5. Flashcard Review Endpoint
    card_model = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "folder_id": folder_id,
        "front": "What is BKT?",
        "back": "Bayesian Knowledge Tracing",
        "stage": "2357_day1",
        "stability": 0.0,
        "difficulty": 0.0,
        "reps": 0,
        "lapses": 0,
        "state": 0,
        "is_leech": False,
        "is_paused": False,
        "is_active_in_queue": True,
        "due": datetime.now(timezone.utc).isoformat(),
    }
    res_review = client.post(
        "/api/v1/flashcards/review",
        json={
            "card": card_model,
            "rating": 3,  # GOOD
            "workload_mode": "free",
        },
        headers={"X-Test-User-Id": user_id},
    )
    assert res_review.status_code == 200
    r_data = res_review.json()
    assert r_data["stage"] == "2357_day3"
    assert r_data["scheduled_days"] == 2.0
