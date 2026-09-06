import uuid
from datetime import datetime, timezone, timedelta
from backend.app.schemas.fsrs import (
    FlashcardModel,
    ScheduleStage,
    CardState,
    Rating,
)
from backend.app.services.fsrs_engine import ReviewSessionEngine
from backend.app.services.review_repository import InMemoryReviewAdapter
from backend.app.services.database import DatabaseService


def test_practice_again_early_does_not_advance_milestone():
    """
    Verifies that reviewing an un-due card in early practice / rehearsal mode:
    - Retains its current milestone stage (e.g. DAY_3).
    - Preserves its exact future scheduled due date.
    - Flags is_extra_practice = True.
    """
    now = datetime.now(timezone.utc)
    future_due = now + timedelta(days=2)  # Day 3 due in 2 days

    card = FlashcardModel(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        folder_id=uuid.uuid4(),
        front="What is backpropagation?",
        back="Gradient calculation algorithm via chain rule.",
        stage=ScheduleStage.DAY_3,
        state=CardState.REVIEW,
        stability=3.0,
        difficulty=5.0,
        reps=2,
        lapses=0,
        due=future_due,
        last_review=now - timedelta(hours=1),
    )

    engine = ReviewSessionEngine(InMemoryReviewAdapter())
    resp = engine.process_review(card=card, rating=Rating.GOOD, review_time=now)

    # Must NOT advance to Day 5!
    assert resp.stage == ScheduleStage.DAY_3
    assert resp.is_extra_practice is True
    # Due date must be preserved to the future scheduled date
    assert resp.card.due == future_due


def test_due_review_on_exact_date_advances_milestone():
    """
    Verifies that reviewing when due <= now (the exact scheduled date arrives):
    - Advances from Day 3 to Day 5.
    - Sets new due date in +2 days.
    - is_extra_practice is False.
    """
    now = datetime.now(timezone.utc)
    past_due = now - timedelta(hours=1)  # Due now!

    card = FlashcardModel(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        folder_id=uuid.uuid4(),
        front="What is backpropagation?",
        back="Gradient calculation algorithm via chain rule.",
        stage=ScheduleStage.DAY_3,
        state=CardState.REVIEW,
        stability=3.0,
        difficulty=5.0,
        reps=2,
        lapses=0,
        due=past_due,
        last_review=now - timedelta(days=2),  # Reviewed 2 days ago
    )

    engine = ReviewSessionEngine(InMemoryReviewAdapter())
    resp = engine.process_review(card=card, rating=Rating.GOOD, review_time=now)

    # Must advance to Day 5!
    assert resp.stage == ScheduleStage.DAY_5
    assert resp.is_extra_practice is False
    assert resp.card.due > now


def test_hybrid_session_practice_again_preserves_milestones():
    """
    Verifies that calling record_hybrid_review_session when cards are already
    scheduled in future (practice again mode) preserves the stage and due date.
    """
    now = datetime.now(timezone.utc)
    user_id = uuid.uuid4()
    folder_id = uuid.uuid4()
    doc_id = uuid.uuid4()
    future_due = now + timedelta(days=2)

    repo = InMemoryReviewAdapter()
    c = repo.create_card(
        user_id=user_id,
        folder_id=folder_id,
        front="Concept A",
        back="Definition A",
        document_id=doc_id,
        stage=ScheduleStage.DAY_3,
        due=future_due,
    )
    # Set last review to 30 mins ago
    repo.raw_card_records[str(c["id"])]["last_review"] = (now - timedelta(minutes=30)).isoformat()

    db_service = DatabaseService()
    res = db_service.record_hybrid_review_session(
        user_id=user_id,
        folder_id=folder_id,
        document_id=doc_id,
        file_name="Deep_Learning.pdf",
        topic="Deep Learning",
        cards_reviewed=1,
        blurting_content="Deep Learning uses multi-layer neural networks to optimize objective loss functions.",
        blurting_duration_seconds=45.0,
        feynman_explanation="Deep learning teaches computers to learn patterns like a human brain using layers of simple rules.",
        target_audience="child",
        repository=repo,
    )

    assert res["status"] == "success"
    assert res["is_extra_practice"] is True
    assert "Extra practice completed" in res["message"]
    # Card in repo should still be DAY_3, not DAY_5
    saved_card = repo.get_card(c["id"])
    assert saved_card.stage == ScheduleStage.DAY_3
