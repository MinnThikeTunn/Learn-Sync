import math
import uuid
import pytest
from datetime import datetime, timedelta, timezone

from backend.app.schemas.bkt import BKTParameters, BKTUpdateRequest
from backend.app.services.bkt import BKTService
from backend.app.schemas.feynman import (
    FeynmanEvaluationRequest,
    FeynmanPromptRequest,
    FeynmanPromptTarget,
)
from backend.app.services.feynman import FeynmanService
from backend.app.schemas.burnout import BurnoutTriggerRequest
from backend.app.services.burnout_guard import BurnoutGuardService
from backend.app.schemas.workload import EventItem, EventType


# 1. BKT Tests
def test_bkt_initial_state_and_defaults():
    params = BKTService.DEFAULT_PARAMS
    assert params.p_l0 == 0.10
    assert params.p_transit == 0.15
    assert params.p_guess == 0.20
    assert params.p_slip == 0.10
    assert params.mastery_threshold == 0.85


def test_bkt_correct_observation_exact_math():
    """
    Prior P(L0) = 0.10, Obs = 1:
    Posterior = (0.10 * 0.90) / (0.09 + 0.90 * 0.20) = 0.09 / 0.27 = 1/3 ≈ 0.333333
    Updated = 1/3 + (2/3) * 0.15 = 1/3 + 0.10 = 13/30 ≈ 0.433333
    """
    req = BKTUpdateRequest(
        user_id=uuid.uuid4(),
        kc_id=uuid.uuid4(),
        is_correct=True,
        current_p_l=0.10,
    )
    res = BKTService.update_mastery(req)

    assert math.isclose(res.posterior_p_l, 1.0 / 3.0, rel_tol=1e-4)
    assert math.isclose(res.updated_p_l, 13.0 / 30.0, rel_tol=1e-4)
    assert res.is_mastered is False


def test_bkt_incorrect_observation_exact_math():
    """
    Prior P(L0) = 0.10, Obs = 0:
    Posterior = (0.10 * 0.10) / (0.01 + 0.90 * 0.80) = 0.01 / 0.73 = 1/73 ≈ 0.013699
    Updated = 1/73 + (72/73) * 0.15 = (1 + 10.8)/73 = 11.8/73 ≈ 0.161644
    """
    req = BKTUpdateRequest(
        user_id=uuid.uuid4(),
        kc_id=uuid.uuid4(),
        is_correct=False,
        current_p_l=0.10,
    )
    res = BKTService.update_mastery(req)

    assert math.isclose(res.posterior_p_l, 1.0 / 73.0, rel_tol=1e-4)
    assert math.isclose(res.updated_p_l, 11.8 / 73.0, rel_tol=1e-4)


def test_bkt_successive_mastery_convergence():
    """4 consecutive correct responses on an initial KC drive P(L) >= 0.85 (mastered)."""
    p_l = 0.10
    user_id = uuid.uuid4()
    kc_id = uuid.uuid4()

    for i in range(4):
        req = BKTUpdateRequest(user_id=user_id, kc_id=kc_id, is_correct=True, current_p_l=p_l)
        res = BKTService.update_mastery(req)
        p_l = res.updated_p_l

    assert p_l >= 0.85
    assert res.is_mastered is True


# 2. Feynman Active Recall Tests
def test_feynman_prompt_generation():
    req = FeynmanPromptRequest(
        user_id=uuid.uuid4(),
        folder_id=uuid.uuid4(),
        concept="Recursion Call Stack",
        target_audience=FeynmanPromptTarget.CHILD,
    )
    res = FeynmanService.generate_prompt(req)

    assert "10-year-old child" in res.prompt_text
    assert res.concept == "Recursion Call Stack"
    assert res.analogy_hint is not None


def test_feynman_gap_analysis_complete_explanation():
    user_id = uuid.uuid4()
    folder_id = uuid.uuid4()
    req = FeynmanEvaluationRequest(
        user_id=user_id,
        folder_id=folder_id,
        concept="Recursion",
        student_explanation=(
            "Recursion is when a function calls itself. It always checks a base case first "
            "so it knows when to terminate. Each recursive step pushes a call stack frame into memory, "
            "and once the base case is hit, the stack unwinds without infinite loop overflow."
        ),
    )
    res = FeynmanService.evaluate_explanation(req)

    assert res.completeness_score >= 0.80
    assert res.is_sufficient is True
    assert len(res.misconceptions) == 0


def test_feynman_gap_analysis_misconception_and_auto_flashcards():
    user_id = uuid.uuid4()
    folder_id = uuid.uuid4()
    req = FeynmanEvaluationRequest(
        user_id=user_id,
        folder_id=folder_id,
        concept="Recursion",
        student_explanation="Recursion is just a loop where an infinite loop is required and stored in hard drive permanently.",
        auto_generate_flashcards=True,
    )
    res = FeynmanService.evaluate_explanation(req)

    assert res.is_sufficient is False
    assert len(res.misconceptions) >= 1
    assert len(res.generated_flashcards) >= 1
    assert res.generated_flashcards[0].user_id == user_id


# 3. Burnout Guard Tests
def test_burnout_guard_acute_deadline_cluster_triggered():
    user_id = uuid.uuid4()
    ref_time = datetime(2026, 9, 1, 12, 0, tzinfo=timezone.utc)
    events = [
        EventItem(user_id=user_id, title="Exam 1", event_type=EventType.EXAM, start_time=ref_time + timedelta(hours=10)),
        EventItem(user_id=user_id, title="Project Due", event_type=EventType.PROJECT, start_time=ref_time + timedelta(hours=24)),
        EventItem(user_id=user_id, title="Assignment 3", event_type=EventType.ASSIGNMENT, start_time=ref_time + timedelta(hours=36)),
    ]

    req = BurnoutTriggerRequest(
        user_id=user_id,
        events=events,
        reference_time=ref_time,
        window_hours=48.0,
        deadline_threshold=3,
    )
    res = BurnoutGuardService.evaluate_burnout_risk(req)

    assert res.is_burnout_risk is True
    assert res.deadline_count_48h == 3
    assert res.micro_task is not None
    assert res.micro_task.duration_seconds == 90


def test_burnout_guard_zero_calendar_slots_triggered():
    user_id = uuid.uuid4()
    ref_time = datetime(2026, 9, 1, 12, 0, tzinfo=timezone.utc)
    req = BurnoutTriggerRequest(
        user_id=user_id,
        events=[],
        reference_time=ref_time,
        available_calendar_slots=0,
    )
    res = BurnoutGuardService.evaluate_burnout_risk(req)

    assert res.is_burnout_risk is True
    assert "Zero available calendar study blocks" in res.trigger_reason


def test_burnout_guard_calm_period_no_trigger():
    user_id = uuid.uuid4()
    ref_time = datetime(2026, 9, 1, 12, 0, tzinfo=timezone.utc)
    events = [
        EventItem(user_id=user_id, title="Quiz 1", event_type=EventType.QUIZ, start_time=ref_time + timedelta(hours=12), weight=0.5),
    ]
    req = BurnoutTriggerRequest(
        user_id=user_id,
        events=events,
        reference_time=ref_time,
        available_calendar_slots=4,
    )
    res = BurnoutGuardService.evaluate_burnout_risk(req)

    assert res.is_burnout_risk is False
    assert res.micro_task is None
