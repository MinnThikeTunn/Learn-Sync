import uuid
from datetime import datetime, timezone, timedelta
import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.schemas.fsrs import (
    FlashcardModel,
    ScheduleStage,
    CardState,
)
from backend.app.services.review_repository import InMemoryReviewAdapter
from backend.app.services.database import DatabaseService


@pytest.fixture
def test_user_id():
    return uuid.UUID("00000000-0000-0000-0000-000000000001")


def test_hybrid_review_session_endpoint(test_user_id, monkeypatch):
    """
    RED PHASE:
    Validates the public seam POST /api/v1/review/hybrid-session.
    Verifies that:
    1. A single review session payload with both blurting recall dump and feynman explanation is submitted.
    2. Response records recall_finished=True and feynman_finished=True.
    3. Due cards advance from Day 1 to Day 3 (+2 days in 2357 schedule).
    4. Evaluates both blurting accuracy and feynman intuition completeness.
    """
    from backend.app.api.v1 import endpoints

    folder_id = uuid.UUID("11111111-1111-1111-1111-111111111111")
    doc_id = uuid.UUID("22222222-2222-2222-2222-222222222222")

    adapter = InMemoryReviewAdapter()
    db = DatabaseService()

    # Create 3 Day 1 cards for this document
    now = datetime.now(timezone.utc)
    for i in range(3):
        adapter.create_card(
            user_id=test_user_id,
            folder_id=folder_id,
            document_id=doc_id,
            front=f"Front {i+1}",
            back=f"Back {i+1}",
            stage=ScheduleStage.DAY_1,
            due=now - timedelta(hours=1),
        )

    # Monkeypatch db service repository to use in-memory adapter
    monkeypatch.setattr(endpoints, "db_service", db)

    client = TestClient(app)
    payload = {
        "folder_id": str(folder_id),
        "document_id": str(doc_id),
        "file_name": "Operating_Systems_Concurrency.pdf",
        "topic": "Semaphores and Mutex Locks",
        "cards_reviewed": 3,
        "blurting_content": "A mutex lock provides mutual exclusion to a critical section. A semaphore is an integer counter initialized to N with wait and signal operations.",
        "blurting_duration_seconds": 36.0,
        "feynman_explanation": "Imagine a single bathroom key at a coffee shop. Only one person holds the key to enter, and they return it when done so the next person can go.",
        "target_audience": "child",
    }

    response = client.post(
        "/api/v1/review/hybrid-session",
        json=payload,
        headers={"X-Test-User-Id": str(test_user_id)},
    )

    assert response.status_code == 200, f"Expected 200 but got {response.status_code}: {response.text}"
    data = response.json()
    assert data["status"] == "success"
    assert data["recall_finished"] is True
    assert data["feynman_finished"] is True
    assert data["file_name"] == "Operating_Systems_Concurrency.pdf"
    assert data["cards_completed"] >= 3
    assert data["current_stage"] == "2357_day1"
    assert data["next_stage"] == "2357_day3"
    assert "next_review_due" in data
    assert "blurting_metrics" in data
    assert data["blurting_metrics"]["accuracy_score"] > 0
    assert "feynman_metrics" in data
    assert data["feynman_metrics"]["completeness_score"] > 0
    assert data["speed_words_per_minute"] > 0


def test_hybrid_review_session_advances_2357_and_records_on_file(test_user_id, monkeypatch):
    """
    RED PHASE:
    Validates that recording the hybrid review session attaches to the file
    and updates get_deck_overview to indicate recall_finished=True and feynman_finished=True.
    """
    from backend.app.services.database import DatabaseService

    db = DatabaseService()
    adapter = InMemoryReviewAdapter()

    folder_id = uuid.UUID("33333333-3333-3333-3333-333333333333")
    doc_id = uuid.UUID("44444444-4444-4444-4444-444444444444")
    now = datetime.now(timezone.utc)

    card = adapter.create_card(
        user_id=test_user_id,
        folder_id=folder_id,
        document_id=doc_id,
        front="What is a Deadlock?",
        back="A situation where processes are blocked waiting on each other.",
        stage=ScheduleStage.DAY_1,
        due=now - timedelta(hours=2),
    )

    docs_db = [{
        "id": str(doc_id),
        "file_name": "Deadlocks_and_Livelocks.pdf",
        "folder_id": str(folder_id),
        "course_id": str(uuid.uuid4()),
        "status": "learned",
    }]

    monkeypatch.setattr(db, "get_documents", lambda user_id: docs_db)
    monkeypatch.setattr(db, "get_virtual_folders", lambda user_id: [{"id": str(folder_id), "materialized_path": "/CS101", "name": "CS101"}])
    monkeypatch.setattr(db, "get_courses", lambda user_id: [])

    # Before hybrid session: card is due today
    overview_before = db.get_deck_overview(user_id=test_user_id, repository=adapter)
    assert overview_before["total_files"] == 1
    assert overview_before["files"][0]["due_cards_count"] == 1
    assert overview_before["files"][0].get("recall_finished") is not True
    assert overview_before["files"][0].get("feynman_finished") is not True

    # Record hybrid session
    res = db.record_hybrid_review_session(
        user_id=test_user_id,
        folder_id=folder_id,
        document_id=doc_id,
        file_name="Deadlocks_and_Livelocks.pdf",
        topic="Deadlocks and Livelocks",
        cards_reviewed=1,
        blurting_content="Deadlocks happen when four Coffman conditions hold: mutual exclusion, hold and wait, no preemption, and circular wait.",
        blurting_duration_seconds=25.0,
        feynman_explanation="Think of four cars arriving at a four-way stop at the same time, each waiting for the car on the right to go first. Nobody moves.",
        target_audience="child",
        repository=adapter,
    )

    assert res["status"] == "success"
    assert res["recall_finished"] is True
    assert res["feynman_finished"] is True
    assert res["next_stage"] == "2357_day3"

    # After hybrid session: due cards count is 0, recall_finished and feynman_finished are True
    overview_after = db.get_deck_overview(user_id=test_user_id, repository=adapter)
    f_stat = overview_after["files"][0]
    assert f_stat["recall_finished"] is True
    assert f_stat["feynman_finished"] is True
    assert f_stat["finished_today"] is True


def test_card_review_does_not_double_advance_or_skip_stages_to_graduated(test_user_id, monkeypatch):
    """
    PHASE 1 FEEDBACK LOOP:
    Verifies that:
    1. Rating cards individually in flashcard review advances Day 1 -> Day 3 (+2d).
    2. Submitting hybrid review session does NOT double-advance already-advanced cards from Day 3 to Day 5.
    3. Re-practicing cards on the same day does NOT advance 2357 stage repeatedly into Graduated.
    """
    from backend.app.services.fsrs_engine import ReviewSessionEngine
    from backend.app.schemas.fsrs import Rating

    folder_id = uuid.UUID("33333333-3333-3333-3333-333333333333")
    doc_id = uuid.UUID("44444444-4444-4444-4444-444444444444")
    now = datetime.now(timezone.utc)

    adapter = InMemoryReviewAdapter()
    engine = ReviewSessionEngine(repository=adapter)
    db = DatabaseService()

    # Create 3 Day 1 cards
    card_ids = []
    for i in range(3):
        c = adapter.create_card(
            user_id=test_user_id,
            folder_id=folder_id,
            document_id=doc_id,
            front=f"Card {i+1}",
            back=f"Answer {i+1}",
            stage=ScheduleStage.DAY_1,
            due=now - timedelta(hours=1),
        )
        card_ids.append(c["id"])

    # Step 1: User rates all 3 cards in the review session
    for cid in card_ids:
        res = engine.submit_review(user_id=test_user_id, card_id=cid, rating=Rating.GOOD)
        # Each card should be at Day 3 (+2 days)
        assert res.stage == ScheduleStage.DAY_3

    # Step 2: User reaches Step 1 Blurting -> Step 2 Feynman -> Submits hybrid review session
    session_res = db.record_hybrid_review_session(
        user_id=test_user_id,
        folder_id=folder_id,
        document_id=doc_id,
        file_name="Attention_Mechanisms.pdf",
        topic="Attention Mechanisms",
        cards_reviewed=3,
        blurting_content="Self attention maps query and key matrices to values.",
        blurting_duration_seconds=30.0,
        feynman_explanation="Imagine a spotlight highlighting the most important words in a sentence.",
        repository=adapter,
    )

    # The cards must NOT have been double-advanced to Day 5! They must remain at Day 3!
    updated_cards = adapter.get_all_cards(user_id=test_user_id, folder_id=folder_id)
    for c in updated_cards:
        assert c["stage"] == ScheduleStage.DAY_3, f"Expected DAY_3 but got {c['stage']} (Double advancement occurred!)"

    # Step 3: Same-day practice: if user practices the deck again today, it must NOT skip Day 3/5/7 into Graduated!
    first_cid = card_ids[0]
    res_repeat = engine.submit_review(user_id=test_user_id, card_id=first_cid, rating=Rating.GOOD)
    # Same-day review must preserve DAY_3, not jump to DAY_5 or Graduated!
    assert res_repeat.stage == ScheduleStage.DAY_3, f"Expected DAY_3 on same-day review but got {res_repeat.stage}"

