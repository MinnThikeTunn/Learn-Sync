import uuid
import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient

from backend.app.schemas.fsrs import (
    Rating,
    CardState,
    ScheduleStage,
    FlashcardModel,
)
from backend.app.schemas.workload import WorkloadMode
from backend.app.services.review_repository import InMemoryReviewAdapter
from backend.app.services.fsrs_engine import ReviewSessionEngine
from backend.app.main import app


@pytest.fixture
def sample_card():
    now = datetime(2026, 9, 1, 12, 0, tzinfo=timezone.utc)
    return FlashcardModel(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        folder_id=uuid.uuid4(),
        front="What is Bayesian Knowledge Tracing?",
        back="A hidden Markov model estimating latent knowledge probability from observed responses.",
        stage=ScheduleStage.DAY_1,
        stability=1.0,
        difficulty=5.0,
        reps=1,
        lapses=0,
        state=CardState.LEARNING,
        is_leech=False,
        is_paused=False,
        due=now,
    )


def test_in_memory_adapter_crud(sample_card):
    adapter = InMemoryReviewAdapter(initial_cards=[sample_card])
    
    # 1. Get card
    retrieved = adapter.get_card(sample_card.id)
    assert retrieved is not None
    assert retrieved.id == sample_card.id
    assert retrieved.front == sample_card.front

    # 2. Save card state
    updated_model = sample_card.model_copy(update={"stability": 3.5, "reps": 2})
    adapter.save_card_state(updated_model, stage=ScheduleStage.DAY_3)
    card_after = adapter.get_card(sample_card.id)
    assert card_after.stability == 3.5
    assert card_after.stage == ScheduleStage.DAY_3

    # 3. Log review
    log = adapter.log_review(
        user_id=sample_card.user_id,
        flashcard_id=sample_card.id,
        rating=int(Rating.GOOD),
        state=int(CardState.REVIEW),
        scheduled_days=2.0,
        elapsed_days=1.0,
    )
    assert log is not None
    assert len(adapter.review_logs) == 1
    assert adapter.review_logs[0]["rating"] == int(Rating.GOOD)


def test_review_session_engine_submit_review_by_id(sample_card):
    """Verifies that submit_review resolves the card by ID, updates state, and logs the review internally."""
    adapter = InMemoryReviewAdapter(initial_cards=[sample_card])
    engine = ReviewSessionEngine(repository=adapter)

    response = engine.submit_review(
        user_id=sample_card.user_id,
        card_id=sample_card.id,
        rating=Rating.GOOD,
        workload_mode=WorkloadMode.FREE,
    )

    assert response.card.id == sample_card.id
    assert response.stage == ScheduleStage.DAY_3
    assert response.scheduled_days == 2.0

    # Verify that adapter was automatically updated without caller needing to orchestrate
    persisted_card = adapter.get_card(sample_card.id)
    assert persisted_card.stage == ScheduleStage.DAY_3
    assert len(adapter.review_logs) == 1
    assert adapter.review_logs[0]["flashcard_id"] == str(sample_card.id)


def test_review_session_engine_leech_quarantine():
    """Verifies that reaching lapses >= 4 immediately isolates card as a Leech and pauses it in storage."""
    now = datetime.now(timezone.utc)
    difficult_card = FlashcardModel(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        folder_id=uuid.uuid4(),
        front="What is Schmitt Trigger Hysteresis?",
        back="Bi-stable switching preventing oscillation across dead-band intervals.",
        stage=ScheduleStage.DAY_1,
        stability=1.0,
        difficulty=8.0,
        reps=3,
        lapses=3,  # Next failure will reach 4
        state=CardState.LEARNING,
        is_leech=False,
        is_paused=False,
        due=now,
    )
    adapter = InMemoryReviewAdapter(initial_cards=[difficult_card])
    engine = ReviewSessionEngine(repository=adapter)

    response = engine.submit_review(
        user_id=difficult_card.user_id,
        card_id=difficult_card.id,
        rating=Rating.AGAIN,
    )

    assert response.is_leech_triggered is True
    assert response.card.is_leech is True
    assert response.card.is_paused is True
    assert response.card.lapses == 4
    assert response.leech_notice is not None

    # Check persistence in adapter
    persisted = adapter.get_card(difficult_card.id)
    assert persisted.is_leech is True
    assert persisted.is_paused is True


def test_review_session_engine_workload_elasticity(sample_card):
    """Verifies that Busy Mode applies 1.75x interval expansion directly through submit_review."""
    adapter_free = InMemoryReviewAdapter(initial_cards=[sample_card])
    engine_free = ReviewSessionEngine(repository=adapter_free)
    res_free = engine_free.submit_review(
        user_id=sample_card.user_id,
        card_id=sample_card.id,
        rating=Rating.GOOD,
        workload_score=0.30,  # Free Mode
    )

    sample_card_busy = sample_card.model_copy()
    adapter_busy = InMemoryReviewAdapter(initial_cards=[sample_card_busy])
    engine_busy = ReviewSessionEngine(repository=adapter_busy)
    res_busy = engine_busy.submit_review(
        user_id=sample_card_busy.user_id,
        card_id=sample_card_busy.id,
        rating=Rating.GOOD,
        workload_score=0.85,  # Busy Mode
    )

    assert res_busy.interval_multiplier == 1.75
    assert res_busy.scheduled_days > res_free.scheduled_days


def test_study_to_review_handoff_scheduling():
    """Verifies that schedule_handoff creates Day 1 candidate cards when none exist."""
    user_id = uuid.uuid4()
    folder_id = uuid.uuid4()
    adapter = InMemoryReviewAdapter()
    engine = ReviewSessionEngine(repository=adapter)

    handoff_res = engine.schedule_handoff(
        user_id=user_id,
        folder_id=folder_id,
        topic="Consensus Algorithms",
    )

    assert handoff_res.status == "success"
    assert handoff_res.cards_scheduled == 3
    assert handoff_res.stage == ScheduleStage.DAY_1

    # Cards should now exist in adapter
    due_cards = adapter.get_due_cards(user_id=user_id, folder_id=folder_id, limit=10)
    # They are scheduled for tomorrow (+1 day), so not due immediately
    assert len(adapter.cards) == 3


def test_api_review_endpoint_with_id_only(sample_card, monkeypatch):
    """Verifies POST /api/v1/flashcards/review with { card_id, rating } payload against the deep module."""
    client = TestClient(app)
    adapter = InMemoryReviewAdapter(initial_cards=[sample_card])
    test_engine = ReviewSessionEngine(repository=adapter)

    from backend.app.api.v1 import endpoints
    monkeypatch.setattr(endpoints, "review_session_engine", test_engine)

    payload = {
        "card_id": str(sample_card.id),
        "rating": int(Rating.GOOD),
        "workload_mode": "free",
    }

    res = client.post(
        "/api/v1/flashcards/review",
        json=payload,
        headers={"X-Test-User-Id": str(sample_card.user_id)},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["card"]["id"] == str(sample_card.id)
    assert data["stage"] == "2357_day3"
    assert len(adapter.review_logs) == 1


def test_api_review_endpoint_with_full_card_payload(sample_card, monkeypatch):
    """Verifies backward compatibility when caller provides the full { card, rating } payload."""
    client = TestClient(app)
    adapter = InMemoryReviewAdapter(initial_cards=[sample_card])
    test_engine = ReviewSessionEngine(repository=adapter)

    from backend.app.api.v1 import endpoints
    monkeypatch.setattr(endpoints, "review_session_engine", test_engine)

    payload = {
        "card": sample_card.model_dump(mode="json"),
        "rating": int(Rating.EASY),
        "workload_mode": "busy",
    }

    res = client.post(
        "/api/v1/flashcards/review",
        json=payload,
        headers={"X-Test-User-Id": str(sample_card.user_id)},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["card"]["id"] == str(sample_card.id)
    assert data["interval_multiplier"] == 1.75
