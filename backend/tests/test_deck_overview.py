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

    # Pass the adapter to get_deck_overview
    overview = db.get_deck_overview(user_id=test_user_id, repository=adapter)

    assert overview["total_files"] == 3
    assert overview["files_needing_review"] == 1  # Only folder_1 has due card (Card 1)
    assert overview["total_due_cards"] == 1

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

    # Check File 3 (no flashcards generated yet)
    f3 = next(f for f in overview["files"] if f["file_name"] == "Quantum_Computing_Overview.pdf")
    assert f3["total_cards"] == 0
    assert f3["due_cards_count"] == 0
    assert f3["completion_percentage"] == 0.0
    assert f3["status"] == "not_started"


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

