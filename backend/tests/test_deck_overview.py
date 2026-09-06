import uuid
from datetime import datetime, timezone, timedelta
import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.schemas.fsrs import (
    FlashcardModel,
    ScheduleStage,
    CardState,
    FileReviewStats,
    DeckOverviewResponse,
)
from backend.app.services.review_repository import InMemoryReviewAdapter
from backend.app.api.v1 import endpoints


@pytest.fixture
def test_user_id():
    return uuid.UUID("00000000-0000-0000-0000-000000000001")


@pytest.fixture
def sample_deck_cards(test_user_id):
    now = datetime.now(timezone.utc)
    folder_1 = uuid.UUID("11111111-1111-1111-1111-111111111111")
    folder_2 = uuid.UUID("22222222-2222-2222-2222-222222222222")

    return [
        # File 1 (folder_1): 3 cards total
        # Card 1: Overdue Day 3 card -> Needs review today
        FlashcardModel(
            id=uuid.uuid4(),
            user_id=test_user_id,
            folder_id=folder_1,
            front="Q1",
            back="A1",
            stage=ScheduleStage.DAY_3,
            due=now - timedelta(days=1),
            reps=2,
            stability=3.0,
            state=CardState.REVIEW,
        ),
        # Card 2: Upcoming Day 5 card -> Due in 2 days
        FlashcardModel(
            id=uuid.uuid4(),
            user_id=test_user_id,
            folder_id=folder_1,
            front="Q2",
            back="A2",
            stage=ScheduleStage.DAY_5,
            due=now + timedelta(days=2),
            reps=3,
            stability=5.0,
            state=CardState.REVIEW,
        ),
        # Card 3: Graduated card -> Mastered
        FlashcardModel(
            id=uuid.uuid4(),
            user_id=test_user_id,
            folder_id=folder_1,
            front="Q3",
            back="A3",
            stage=ScheduleStage.GRADUATED_FSRS,
            due=now + timedelta(days=14),
            reps=5,
            stability=14.0,
            state=CardState.REVIEW,
        ),
        # File 2 (folder_2): 2 cards total
        # Card 4: New Day 1 card -> not yet due (due tomorrow)
        FlashcardModel(
            id=uuid.uuid4(),
            user_id=test_user_id,
            folder_id=folder_2,
            front="Q4",
            back="A4",
            stage=ScheduleStage.DAY_1,
            due=now + timedelta(days=1),
            reps=0,
            stability=0.0,
            state=CardState.NEW,
        ),
        # Card 5: New Day 1 card -> not yet due (due tomorrow)
        FlashcardModel(
            id=uuid.uuid4(),
            user_id=test_user_id,
            folder_id=folder_2,
            front="Q5",
            back="A5",
            stage=ScheduleStage.DAY_1,
            due=now + timedelta(days=1),
            reps=0,
            stability=0.0,
            state=CardState.NEW,
        ),
    ]


def test_in_memory_repository_get_all_cards(sample_deck_cards, test_user_id):
    """Verifies that get_all_cards retrieves all cards regardless of due date."""
    adapter = InMemoryReviewAdapter(initial_cards=sample_deck_cards)
    cards = adapter.get_all_cards(user_id=test_user_id)
    assert len(cards) == 5


def test_database_service_deck_overview_calculation(sample_deck_cards, test_user_id, monkeypatch):
    """
    Verifies that get_deck_overview correlates documents and flashcards:
    - calculates total cards, due cards, 2357 stage distributions, and completion percentages.
    - detects files that need review today according to the 2357 method.
    """
    from backend.app.services.database import DatabaseService

    folder_1 = uuid.UUID("11111111-1111-1111-1111-111111111111")
    folder_2 = uuid.UUID("22222222-2222-2222-2222-222222222222")
    folder_3 = uuid.UUID("33333333-3333-3333-3333-333333333333")

    mock_docs = [
        {
            "id": str(uuid.uuid4()),
            "file_name": "Distributed_Systems_Lecture1.pdf",
            "folder_id": str(folder_1),
            "course_id": str(uuid.uuid4()),
            "status": "indexed",
        },
        {
            "id": str(uuid.uuid4()),
            "file_name": "Attention_Mechanisms.pdf",
            "folder_id": str(folder_2),
            "course_id": str(uuid.uuid4()),
            "status": "indexed",
        },
        {
            "id": str(uuid.uuid4()),
            "file_name": "Quantum_Computing_Overview.pdf",
            "folder_id": str(folder_3),
            "course_id": str(uuid.uuid4()),
            "status": "indexed",
        },
    ]

    mock_folders = [
        {"id": str(folder_1), "materialized_path": "/CS301/Lecture1", "name": "Lecture 1"},
        {"id": str(folder_2), "materialized_path": "/AI202/Attention", "name": "Attention"},
        {"id": str(folder_3), "materialized_path": "/PHY401/Quantum", "name": "Quantum"},
    ]

    db = DatabaseService()
    adapter = InMemoryReviewAdapter(initial_cards=sample_deck_cards)

    monkeypatch.setattr(db, "get_documents", lambda user_id: mock_docs)
    monkeypatch.setattr(db, "get_virtual_folders", lambda user_id: mock_folders)
    monkeypatch.setattr(db, "get_courses", lambda user_id: [])

    # File 1 & 2 are completed/learned documents with review cards
    # File 3 was just imported (status: indexed) and has NOT finished learning yet
    mock_docs[0]["status"] = "learned"
    mock_docs[1]["status"] = "learned"
    mock_docs[2]["status"] = "indexed"

    overview = db.get_deck_overview(user_id=test_user_id, repository=adapter)

    # Quantum_Computing_Overview.pdf has not finished learning, so it must NOT reach Review!
    assert overview["total_files"] == 2
    assert overview["files_needing_review"] == 1  # Only folder_1 has due card (Card 1)
    assert overview["total_due_cards"] == 1
    file_names = [f["file_name"] for f in overview["files"]]
    assert "Quantum_Computing_Overview.pdf" not in file_names
    assert "Distributed_Systems_Lecture1.pdf" in file_names
    assert "Attention_Mechanisms.pdf" in file_names

    # Check File 1
    f1 = next(f for f in overview["files"] if f["file_name"] == "Distributed_Systems_Lecture1.pdf")
    assert f1["total_cards"] == 3
    assert f1["due_cards_count"] == 1
    assert f1["needs_review_today"] is True
    assert f1["status"] == "needs_review"
    assert f1["graduated_cards_count"] == 1
    # Weighted 2357 progress: (Day3*0.4 + Day5*0.6 + Graduated*1.0) / 3 = (0.4 + 0.6 + 1.0)/3 = 66.7%
    assert 65.0 <= f1["completion_percentage"] <= 68.0
    assert f1["stage_breakdown"]["day_3"] == 1
    assert f1["stage_breakdown"]["day_5"] == 1
    assert f1["stage_breakdown"]["graduated"] == 1

    # Check File 2
    f2 = next(f for f in overview["files"] if f["file_name"] == "Attention_Mechanisms.pdf")
    assert f2["total_cards"] == 2
    assert f2["due_cards_count"] == 0
    assert f2["needs_review_today"] is False
    assert f2["status"] == "up_to_date"
    assert f2["stage_breakdown"]["day_1"] == 2


def test_api_deck_overview_endpoint(sample_deck_cards, test_user_id, monkeypatch):
    """Verifies GET /api/v1/flashcards/deck-overview returns valid DeckOverviewResponse schema."""
    from backend.app.services.database import db_service

    folder_1 = uuid.UUID("11111111-1111-1111-1111-111111111111")
    mock_docs = [
        {
            "id": str(uuid.uuid4()),
            "file_name": "Test_Doc.pdf",
            "folder_id": str(folder_1),
            "status": "indexed",
        }
    ]
    mock_folders = [
        {"id": str(folder_1), "materialized_path": "/CS101", "name": "CS101"}
    ]

    adapter = InMemoryReviewAdapter(initial_cards=sample_deck_cards)
    monkeypatch.setattr(db_service, "get_documents", lambda user_id: mock_docs)
    monkeypatch.setattr(db_service, "get_virtual_folders", lambda user_id: mock_folders)
    monkeypatch.setattr(db_service, "get_courses", lambda user_id: [])

    # Patch adapter in db_service
    monkeypatch.setattr(
        "backend.app.services.review_repository.supabase_review_adapter",
        adapter,
    )

    client = TestClient(app)
    response = client.get(
        "/api/v1/flashcards/deck-overview",
        headers={"X-Test-User-Id": str(test_user_id)},
    )
    assert response.status_code == 200
    data = response.json()
    assert "total_files" in data
    assert "files_needing_review" in data
    assert "files" in data
    assert len(data["files"]) >= 1
    assert data["files"][0]["file_name"] == "Test_Doc.pdf"


def test_api_deck_complete_endpoint(test_user_id, monkeypatch):
    """Verifies POST /api/v1/flashcards/deck-complete advances due cards and records completion."""
    from backend.app.services.database import db_service

    folder_id = uuid.UUID("11111111-1111-1111-1111-111111111111")
    doc_id = uuid.UUID("33333333-3333-3333-3333-333333333333")

    client = TestClient(app)
    payload = {
        "folder_id": str(folder_id),
        "document_id": str(doc_id),
        "file_name": "Test_Doc.pdf",
        "cards_reviewed": 3,
    }

    response = client.post(
        "/api/v1/flashcards/deck-complete",
        json=payload,
        headers={"X-Test-User-Id": str(test_user_id)},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "Recorded" in data["message"]
    assert data["file_name"] == "Test_Doc.pdf"
    assert data["cards_completed"] >= 3
    assert data["next_stage"] == "2357_day3"
    assert "next_review_due" in data


def test_lifecycle_import_to_learning_then_review(test_user_id, monkeypatch):
    """
    Verifies the complete flow requested by user:
    1. Document imported: queued to learning tab, strictly NOT in review.
    2. Student finishes learning: triggers handoff, status -> 'learned', queues to review.
    3. Otherwise: never reaches review.
    """
    from backend.app.services.database import DatabaseService
    from backend.app.services.fsrs_engine import ReviewSessionEngine

    db = DatabaseService()
    adapter = InMemoryReviewAdapter()
    engine = ReviewSessionEngine(repository=adapter)

    folder_id = uuid.UUID("44444444-4444-4444-4444-444444444444")
    doc_id = uuid.UUID("55555555-5555-5555-5555-555555555555")

    mock_doc = {
        "id": str(doc_id),
        "file_name": "Bioinformatics_Algorithms.pdf",
        "folder_id": str(folder_id),
        "course_id": str(uuid.uuid4()),
        "status": "indexed",  # Freshly imported
    }
    docs_db = [mock_doc]

    monkeypatch.setattr(db, "get_documents", lambda user_id: docs_db)
    monkeypatch.setattr(db, "get_virtual_folders", lambda user_id: [{"id": str(folder_id), "materialized_path": "/BIO101/Week1", "name": "Week1"}])
    monkeypatch.setattr(db, "get_courses", lambda user_id: [])

    # STEP 1: Freshly imported document has NOT finished learning.
    # It must NOT reach review!
    overview_before = db.get_deck_overview(user_id=test_user_id, repository=adapter)
    assert overview_before["total_files"] == 0
    assert len(overview_before["files"]) == 0

    # STEP 2: Student starts and finishes learning (Study-to-Review Handoff).
    mock_doc["status"] = "learned"
    handoff_res = engine.schedule_handoff(
        user_id=test_user_id,
        folder_id=folder_id,
        topic="Bioinformatics Algorithms",
        document_id=doc_id,
    )
    assert handoff_res.status == "success"
    assert handoff_res.cards_scheduled == 3

    # STEP 3: Now that learning is finished, it reaches Review!
    overview_after = db.get_deck_overview(user_id=test_user_id, repository=adapter)
    assert overview_after["total_files"] == 1
    assert len(overview_after["files"]) == 1
    file_stat = overview_after["files"][0]
    assert file_stat["file_name"] == "Bioinformatics_Algorithms.pdf"
    assert file_stat["total_cards"] == 3
    assert file_stat["status"] in ("needs_review", "up_to_date")


def test_standalone_blurting_and_feynman_evaluation_records_completion_in_overview(test_user_id, monkeypatch):
    """
    Verifies that when a student uses standalone Blurting Scratchpad or Feynman Explainer:
    - POST /api/v1/blurting/evaluate marks recall_finished=True for that file in deck overview.
    - POST /api/v1/feynman/evaluate marks feynman_finished=True for that file in deck overview.
    """
    from backend.app.services.database import db_service
    from backend.app.services.blurting import BlurtingService
    from backend.app.services.feynman import FeynmanService
    from backend.app.schemas.feynman import GapAnalysisResult
    from backend.app.schemas.fsrs import BlurtingEvaluationResponse

    folder_id = uuid.UUID("77777777-7777-7777-7777-777777777777")
    doc_id = uuid.UUID("88888888-8888-8888-8888-888888888888")
    adapter = InMemoryReviewAdapter()

    # Pre-populate 1 card so file appears in overview
    card = FlashcardModel(
        id=uuid.uuid4(),
        user_id=test_user_id,
        folder_id=folder_id,
        document_id=doc_id,
        front="What is backprop?",
        back="Gradient calculation algorithm",
        stage=ScheduleStage.DAY_1,
        due=datetime.now(timezone.utc),
    )
    import backend.app.services.review_repository as rr
    adapter = InMemoryReviewAdapter(initial_cards=[card])
    monkeypatch.setattr(rr, "supabase_review_adapter", adapter)
    monkeypatch.setattr(db_service, "get_documents", lambda user_id: [
        {"id": str(doc_id), "file_name": "Backpropagation_Notes.pdf", "folder_id": str(folder_id), "status": "learned"}
    ])
    monkeypatch.setattr(db_service, "get_virtual_folders", lambda user_id: [
        {"id": str(folder_id), "materialized_path": "/CS340/Week2", "name": "Week2"}
    ])
    monkeypatch.setattr(db_service, "get_courses", lambda user_id: [])

    # Mock BlurtingService & FeynmanService evaluation
    monkeypatch.setattr(BlurtingService, "evaluate_recall", lambda req: BlurtingEvaluationResponse(
        topic=req.topic,
        accuracy_score=85,
        retained_concepts=["Derivatives", "Chain rule"],
        missed_nuances=[],
        recommended_focus="Good job",
    ))
    monkeypatch.setattr(FeynmanService, "evaluate_explanation", lambda req: GapAnalysisResult(
        concept=req.concept,
        completeness_score=0.92,
        is_sufficient=True,
        feedback="Clear intuition",
    ))

    client = TestClient(app)

    # 1. Initial state: neither is finished
    res_before = client.get("/api/v1/flashcards/deck-overview", headers={"X-Test-User-Id": str(test_user_id)})
    assert res_before.status_code == 200
    file_item = res_before.json()["files"][0]
    assert file_item["recall_finished"] is False
    assert file_item["feynman_finished"] is False

    # 2. Student completes standalone Blurting Scratchpad
    blurt_res = client.post(
        "/api/v1/blurting/evaluate",
        headers={"X-Test-User-Id": str(test_user_id)},
        json={
            "folder_id": str(folder_id),
            "document_id": str(doc_id),
            "file_name": "Backpropagation_Notes.pdf",
            "topic": "Backpropagation Notes",
            "user_recall_text": "Backpropagation uses the chain rule to calculate gradients backwards through layers.",
            "duration_seconds": 45.0,
        },
    )
    assert blurt_res.status_code == 200

    # Verify overview shows recall_finished = True
    res_after_blurt = client.get("/api/v1/flashcards/deck-overview", headers={"X-Test-User-Id": str(test_user_id)})
    file_item = res_after_blurt.json()["files"][0]
    assert file_item["recall_finished"] is True
    assert file_item["feynman_finished"] is False
    assert file_item["last_recall_seconds"] == 45.0

    # 3. Student completes standalone Feynman Explainer
    feyn_res = client.post(
        "/api/v1/feynman/evaluate",
        headers={"X-Test-User-Id": str(test_user_id)},
        json={
            "folder_id": str(folder_id),
            "document_id": str(doc_id),
            "file_name": "Backpropagation_Notes.pdf",
            "concept": "Backpropagation Notes",
            "student_explanation": "Imagine passing a message backwards to tell each person how much they contributed to a mistake.",
        },
    )
    assert feyn_res.status_code == 200

    # Verify overview now shows BOTH finished
    res_after_feyn = client.get("/api/v1/flashcards/deck-overview", headers={"X-Test-User-Id": str(test_user_id)})
    file_item = res_after_feyn.json()["files"][0]
    assert file_item["recall_finished"] is True
    assert file_item["feynman_finished"] is True
    assert file_item["last_feynman_score"] == 92
    assert file_item["last_blurting_accuracy"] == 85


def test_seventy_percent_threshold_enforcement_for_blurting_and_feynman(test_user_id, monkeypatch):
    """
    Verifies that:
    1. Standalone Blurting with accuracy < 70% leaves recall_finished=False.
    2. Standalone Feynman with completeness < 70% leaves feynman_finished=False.
    3. Re-attempting with score >= 70% flips recall_finished and feynman_finished to True.
    4. Deck overview accurately includes last_blurting_accuracy and last_feynman_score.
    """
    from backend.app.services.database import db_service
    from backend.app.services.blurting import BlurtingService
    from backend.app.services.feynman import FeynmanService
    from backend.app.schemas.feynman import GapAnalysisResult
    from backend.app.schemas.fsrs import BlurtingEvaluationResponse
    import backend.app.services.review_repository as rr

    folder_id = uuid.UUID("11111111-2222-3333-4444-555555555555")
    doc_id = uuid.UUID("22222222-3333-4444-5555-666666666666")

    card = FlashcardModel(
        id=uuid.uuid4(),
        user_id=test_user_id,
        folder_id=folder_id,
        document_id=doc_id,
        front="What is gradient descent?",
        back="Optimization algorithm",
        stage=ScheduleStage.DAY_1,
        due=datetime.now(timezone.utc),
    )
    adapter = InMemoryReviewAdapter(initial_cards=[card])
    monkeypatch.setattr(rr, "supabase_review_adapter", adapter)
    monkeypatch.setattr(db_service, "get_documents", lambda user_id: [
        {"id": str(doc_id), "file_name": "Optimization.pdf", "folder_id": str(folder_id), "status": "learned"}
    ])
    monkeypatch.setattr(db_service, "get_virtual_folders", lambda user_id: [
        {"id": str(folder_id), "materialized_path": "/Math/Optimization", "name": "Optimization"}
    ])
    monkeypatch.setattr(db_service, "get_courses", lambda user_id: [])

    # Mock low score for blurting: 55% (< 70%)
    monkeypatch.setattr(BlurtingService, "evaluate_recall", lambda req: BlurtingEvaluationResponse(
        topic=req.topic,
        accuracy_score=55,
        retained_concepts=["Basics"],
        missed_nuances=["Learning rate tuning", "Convergence criteria"],
        recommended_focus="Need deeper recall",
    ))
    # Mock low score for feynman: 0.50 (< 70%)
    monkeypatch.setattr(FeynmanService, "evaluate_explanation", lambda req: GapAnalysisResult(
        concept=req.concept,
        completeness_score=0.50,
        is_sufficient=False,
        feedback="Missing core intuition",
    ))

    client = TestClient(app)

    # 1. Blurting attempt with low score (55% < 70%)
    b_res = client.post(
        "/api/v1/blurting/evaluate",
        headers={"X-Test-User-Id": str(test_user_id)},
        json={
            "folder_id": str(folder_id),
            "document_id": str(doc_id),
            "file_name": "Optimization.pdf",
            "topic": "Optimization",
            "user_recall_text": "Gradient goes down.",
            "duration_seconds": 30.0,
        },
    )
    assert b_res.status_code == 200
    assert b_res.json()["accuracy_score"] == 55

    # Check deck overview: recall_finished MUST be False
    res = client.get("/api/v1/flashcards/deck-overview", headers={"X-Test-User-Id": str(test_user_id)})
    item = res.json()["files"][0]
    assert item["recall_finished"] is False
    assert item["last_blurting_accuracy"] == 55

    # 2. Feynman attempt with low score (50% < 70%)
    f_res = client.post(
        "/api/v1/feynman/evaluate",
        headers={"X-Test-User-Id": str(test_user_id)},
        json={
            "folder_id": str(folder_id),
            "document_id": str(doc_id),
            "file_name": "Optimization.pdf",
            "concept": "Optimization",
            "student_explanation": "Going down a hill.",
        },
    )
    assert f_res.status_code == 200

    # Check deck overview: feynman_finished MUST be False
    res = client.get("/api/v1/flashcards/deck-overview", headers={"X-Test-User-Id": str(test_user_id)})
    item = res.json()["files"][0]
    assert item["feynman_finished"] is False
    assert item["last_feynman_score"] == 50

    # 3. Student retries blurting and achieves >= 70% (78%)
    monkeypatch.setattr(BlurtingService, "evaluate_recall", lambda req: BlurtingEvaluationResponse(
        topic=req.topic,
        accuracy_score=78,
        retained_concepts=["Basics", "Learning rate tuning", "Convergence criteria"],
        missed_nuances=[],
        recommended_focus="Threshold met!",
    ))
    b_retry = client.post(
        "/api/v1/blurting/evaluate",
        headers={"X-Test-User-Id": str(test_user_id)},
        json={
            "folder_id": str(folder_id),
            "document_id": str(doc_id),
            "file_name": "Optimization.pdf",
            "topic": "Optimization",
            "user_recall_text": "Gradient descent computes the negative gradient vector to update parameters iteratively with a learning rate alpha.",
            "duration_seconds": 60.0,
        },
    )
    assert b_retry.status_code == 200
    assert b_retry.json()["accuracy_score"] == 78

    res = client.get("/api/v1/flashcards/deck-overview", headers={"X-Test-User-Id": str(test_user_id)})
    item = res.json()["files"][0]
    assert item["recall_finished"] is True
    assert item["last_blurting_accuracy"] == 78

    # 4. Student retries feynman and achieves >= 70% (85%)
    monkeypatch.setattr(FeynmanService, "evaluate_explanation", lambda req: GapAnalysisResult(
        concept=req.concept,
        completeness_score=0.85,
        is_sufficient=True,
        feedback="Clear intuition and sound analogy.",
    ))
    f_retry = client.post(
        "/api/v1/feynman/evaluate",
        headers={"X-Test-User-Id": str(test_user_id)},
        json={
            "folder_id": str(folder_id),
            "document_id": str(doc_id),
            "file_name": "Optimization.pdf",
            "concept": "Optimization",
            "student_explanation": "Imagine being blindfolded on a foggy mountain and feeling with your feet for the steepest downhill slope to reach the valley.",
        },
    )
    assert f_retry.status_code == 200

    res = client.get("/api/v1/flashcards/deck-overview", headers={"X-Test-User-Id": str(test_user_id)})
    item = res.json()["files"][0]
    assert item["recall_finished"] is True
    assert item["feynman_finished"] is True
    assert item["last_feynman_score"] == 85



