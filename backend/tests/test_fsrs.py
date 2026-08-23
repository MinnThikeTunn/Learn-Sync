import uuid
import pytest
from datetime import datetime, timezone
from backend.app.schemas.fsrs import (
    Rating,
    CardState,
    FlashcardModel,
)
from backend.app.schemas.workload import WorkloadMode
from backend.app.services.fsrs_engine import SpacedRepetitionService


@pytest.fixture
def new_flashcard():
    now = datetime(2026, 9, 1, 10, 0, tzinfo=timezone.utc)
    return FlashcardModel(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        folder_id=uuid.uuid4(),
        front="What is a base case in recursion?",
        back="The condition under which a recursive function returns without making further recursive calls.",
        stability=0.0,
        difficulty=0.0,
        reps=0,
        lapses=0,
        state=CardState.NEW,
        is_leech=False,
        is_paused=False,
        due=now,
        last_review=None,
    )


def test_fsrs_initial_ratings_progression(new_flashcard):
    """Graduating a new card with rating GOOD transitions it to REVIEW state with positive stability."""
    res_good = SpacedRepetitionService.process_review(
        card=new_flashcard,
        rating=Rating.GOOD,
        workload_mode=WorkloadMode.FREE,
    )
    assert res_good.card.state == CardState.REVIEW
    assert res_good.card.reps == 1
    assert res_good.card.stability > 2.0
    assert res_good.card.lapses == 0

    res_again = SpacedRepetitionService.process_review(
        card=new_flashcard,
        rating=Rating.AGAIN,
        workload_mode=WorkloadMode.FREE,
    )
    assert res_again.card.state == CardState.LEARNING
    assert res_again.card.lapses == 1


def test_dynamic_retention_free_mode_vs_busy_mode(new_flashcard):
    """
    Busy mode scales target retention to 80% and applies 1.75x interval multiplier,
    expanding scheduled review days.
    """
    review_time = datetime(2026, 9, 1, 10, 0, tzinfo=timezone.utc)

    # Initial graduation to get stability
    graduated = SpacedRepetitionService.process_review(
        card=new_flashcard,
        rating=Rating.GOOD,
        review_time=review_time,
        workload_mode=WorkloadMode.FREE,
    ).card

    # Free Mode subsequent review
    free_res = SpacedRepetitionService.process_review(
        card=graduated,
        rating=Rating.GOOD,
        review_time=review_time,
        workload_mode=WorkloadMode.FREE,
    )
    assert free_res.target_retention == 0.90
    assert free_res.interval_multiplier == 1.0

    # Busy Mode subsequent review
    busy_res = SpacedRepetitionService.process_review(
        card=graduated,
        rating=Rating.GOOD,
        review_time=review_time,
        workload_mode=WorkloadMode.BUSY,
    )
    assert busy_res.target_retention == 0.80
    assert busy_res.interval_multiplier == 1.75
    assert busy_res.scheduled_days > free_res.scheduled_days


def test_leech_detection_and_automatic_quarantine(new_flashcard):
    """A card with 3 lapses receiving another AGAIN rating reaches 4 lapses and is quarantined."""
    leech_candidate = new_flashcard.model_copy(
        update={
            "state": CardState.REVIEW,
            "stability": 2.0,
            "lapses": 3,
            "reps": 5,
        }
    )

    response = SpacedRepetitionService.process_review(
        card=leech_candidate,
        rating=Rating.AGAIN,
        workload_mode=WorkloadMode.FREE,
    )

    assert response.card.lapses == 4
    assert response.card.is_leech is True
    assert response.card.is_paused is True
    assert response.is_leech_triggered is True
    assert response.leech_notice is not None
    assert response.leech_notice.lapses == 4


def test_leech_rewrite_prompt_generation(new_flashcard):
    """Quarantined card produces structured LLM decomposition prompt."""
    quarantined = new_flashcard.model_copy(
        update={
            "is_leech": True,
            "is_paused": True,
            "lapses": 4,
        }
    )

    req = SpacedRepetitionService.generate_leech_rewrite_prompt(
        card=quarantined,
        kc_title="Recursion Call Stack"
    )

    assert req.lapses == 4
    assert "Recursion Call Stack" in req.prompt_instructions
    assert "Original Question" in req.prompt_instructions
