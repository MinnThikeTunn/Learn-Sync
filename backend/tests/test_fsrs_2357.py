import uuid
import pytest
from datetime import datetime, timezone
from backend.app.schemas.fsrs import (
    Rating,
    CardState,
    ScheduleStage,
    FlashcardModel,
    StudyCompletionRequest,
    BlurtingEvaluationRequest,
)
from backend.app.schemas.workload import WorkloadMode
from backend.app.services.fsrs_engine import SpacedRepetitionService
from backend.app.services.blurting import BlurtingService


@pytest.fixture
def fresh_2357_card():
    now = datetime(2026, 9, 1, 10, 0, tzinfo=timezone.utc)
    return FlashcardModel(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        folder_id=uuid.uuid4(),
        topic="Recursion & Call Stack Frames",
        front="What is a base case in recursion?",
        back="The condition that terminates recursion and prevents call stack overflow.",
        stage=ScheduleStage.DAY_1,
        stability=0.0,
        difficulty=0.0,
        reps=0,
        lapses=0,
        state=CardState.NEW,
        is_leech=False,
        is_paused=False,
        is_active_in_queue=True,
        due=now,
        last_review=None,
    )


def test_2357_stage_graduation_flow(fresh_2357_card):
    """
    Tests that a card correctly advances through the 2357 milestones:
    Day 1 -> Day 3 -> Day 5 -> Day 7 -> Graduated FSRS.
    """
    # Step 1: Review at Day 1 with GOOD -> Advances to Day 3
    res_d1 = SpacedRepetitionService.process_review(
        card=fresh_2357_card,
        rating=Rating.GOOD,
        workload_mode=WorkloadMode.FREE,
    )
    assert res_d1.stage == ScheduleStage.DAY_3
    assert res_d1.scheduled_days == 2.0
    assert res_d1.is_graduated is False

    # Step 2: Review at Day 3 with GOOD -> Advances to Day 5
    res_d3 = SpacedRepetitionService.process_review(
        card=res_d1.card,
        rating=Rating.GOOD,
        workload_mode=WorkloadMode.FREE,
    )
    assert res_d3.stage == ScheduleStage.DAY_5
    assert res_d3.scheduled_days == 2.0
    assert res_d3.is_graduated is False

    # Step 3: Review at Day 5 with EASY -> Advances to Day 7
    res_d5 = SpacedRepetitionService.process_review(
        card=res_d3.card,
        rating=Rating.EASY,
        workload_mode=WorkloadMode.FREE,
    )
    assert res_d5.stage == ScheduleStage.DAY_7
    assert res_d5.scheduled_days == 2.0
    assert res_d5.is_graduated is False

    # Step 4: Review at Day 7 with GOOD -> Graduates to continuous FSRS!
    res_d7 = SpacedRepetitionService.process_review(
        card=res_d5.card,
        rating=Rating.GOOD,
        workload_mode=WorkloadMode.FREE,
    )
    assert res_d7.stage == ScheduleStage.GRADUATED_FSRS
    assert res_d7.is_graduated is True
    assert res_d7.card.stability >= 14.0


def test_2357_lapse_resets_to_day1(fresh_2357_card):
    """Failing a card at Day 5 resets it back to Day 1 with a lapse penalty."""
    day5_card = fresh_2357_card.model_copy(
        update={
            "stage": ScheduleStage.DAY_5,
            "reps": 3,
            "lapses": 0,
        }
    )

    res = SpacedRepetitionService.process_review(
        card=day5_card,
        rating=Rating.AGAIN,
        workload_mode=WorkloadMode.FREE,
    )
    assert res.stage == ScheduleStage.DAY_1
    assert res.card.lapses == 1
    assert res.scheduled_days == 0.25


def test_2357_hard_repeats_current_stage(fresh_2357_card):
    """Marking a card HARD at Day 3 keeps it at Day 3 for reinforced practice."""
    day3_card = fresh_2357_card.model_copy(
        update={
            "stage": ScheduleStage.DAY_3,
            "reps": 1,
            "lapses": 0,
        }
    )

    res = SpacedRepetitionService.process_review(
        card=day3_card,
        rating=Rating.HARD,
        workload_mode=WorkloadMode.FREE,
    )
    assert res.stage == ScheduleStage.DAY_3
    assert res.scheduled_days == 1.0


def test_study_to_review_lesson_completion():
    """Completing a study lesson schedules Day 1 of the 2357 cycle."""
    user_id = uuid.uuid4()
    folder_id = uuid.uuid4()
    topic = "Recursion & Call Stack Frames"

    res = SpacedRepetitionService.complete_study_lesson(
        user_id=user_id,
        folder_id=folder_id,
        topic=topic,
    )

    assert res.status == "success"
    assert res.topic == topic
    assert res.cards_scheduled >= 3
    assert res.stage == ScheduleStage.DAY_1
    assert res.first_due_date is not None


def test_blurting_active_recall_evaluation():
    """Blurting evaluation identifies retained concepts, missed points, and computes score."""
    req = BlurtingEvaluationRequest(
        folder_id=uuid.uuid4(),
        topic="Recursion & Call Stack Frames",
        user_recall_text=(
            "Recursion requires a base case to stop execution and prevent stack overflow. "
            "Call stack frames are allocated in memory to store return addresses and local variables."
        ),
    )

    eval_result = BlurtingService.evaluate_recall(req)

    assert eval_result.topic == req.topic
    assert eval_result.accuracy_score >= 60
    assert len(eval_result.retained_concepts) >= 2
    assert len(eval_result.suggested_cards) > 0
    assert eval_result.recommended_focus is not None
