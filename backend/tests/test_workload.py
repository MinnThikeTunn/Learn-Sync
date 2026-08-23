import math
import uuid
import pytest
from datetime import datetime, timedelta, timezone

from backend.app.schemas.workload import (
    EventItem,
    EventType,
    WorkloadCalculationRequest,
    WorkloadMode,
)
from backend.app.services.workload import WorkloadEngine
from backend.app.core.events import EventPublisher


def test_workload_hyperbolic_decay_single_exam():
    """
    Single exam (weight=3.0) 2.0 days away:
    contribution = 3.0 / (2.0 * 8.0) = 3.0 / 16.0 = 0.1875
    """
    ref_time = datetime(2026, 9, 1, 12, 0, tzinfo=timezone.utc)
    user_id = uuid.uuid4()
    events = [
        EventItem(
            user_id=user_id,
            title="Midterm Exam",
            event_type=EventType.EXAM,
            start_time=ref_time + timedelta(days=2.0),
        )
    ]

    score, raw_sum, count, active_events = WorkloadEngine.compute_workload_score(
        events=events,
        reference_time=ref_time,
        lookahead_days=3.0,
    )

    assert count == 1
    assert math.isclose(score, 0.1875, rel_tol=1e-4)
    assert math.isclose(raw_sum, 0.1875, rel_tol=1e-4)


def test_workload_imminent_event_clamping():
    """
    Imminent exam 0.1 days away (<= 0.25 days min clamp):
    d_e clamped to 0.25: contribution = 3.0 / (0.25 * 8.0) = 3.0 / 2.0 = 1.5 -> W(t) = min(1.0, 1.5) = 1.0
    """
    ref_time = datetime(2026, 9, 1, 12, 0, tzinfo=timezone.utc)
    user_id = uuid.uuid4()
    events = [
        EventItem(
            user_id=user_id,
            title="Imminent Exam",
            event_type=EventType.EXAM,
            start_time=ref_time + timedelta(hours=2.4),  # 0.1 days
        )
    ]

    score, raw_sum, count, _ = WorkloadEngine.compute_workload_score(
        events=events,
        reference_time=ref_time,
        lookahead_days=3.0,
    )

    assert count == 1
    assert score == 1.0
    assert math.isclose(raw_sum, 1.5, rel_tol=1e-4)


def test_workload_multi_event_density():
    """
    Two exams 1.0 day away:
    contribution = 3.0 / (1.0 * 8.0) + 3.0 / (1.0 * 8.0) = 0.375 + 0.375 = 0.75
    """
    ref_time = datetime(2026, 9, 1, 12, 0, tzinfo=timezone.utc)
    user_id = uuid.uuid4()
    events = [
        EventItem(
            user_id=user_id,
            title="Exam 1",
            event_type=EventType.EXAM,
            start_time=ref_time + timedelta(days=1.0),
        ),
        EventItem(
            user_id=user_id,
            title="Exam 2",
            event_type=EventType.EXAM,
            start_time=ref_time + timedelta(days=1.0),
        ),
    ]

    score, raw_sum, count, _ = WorkloadEngine.compute_workload_score(
        events=events,
        reference_time=ref_time,
        lookahead_days=3.0,
    )

    assert count == 2
    assert math.isclose(score, 0.75, rel_tol=1e-4)


def test_workload_excludes_past_and_completed_events():
    """Events in the past or flagged completed are excluded from W(t)."""
    ref_time = datetime(2026, 9, 1, 12, 0, tzinfo=timezone.utc)
    user_id = uuid.uuid4()
    events = [
        EventItem(
            user_id=user_id,
            title="Past Exam",
            event_type=EventType.EXAM,
            start_time=ref_time - timedelta(days=1.0),
        ),
        EventItem(
            user_id=user_id,
            title="Completed Assignment",
            event_type=EventType.ASSIGNMENT,
            start_time=ref_time + timedelta(days=1.0),
            is_completed=True,
        ),
        EventItem(
            user_id=user_id,
            title="Far Future Exam",
            event_type=EventType.EXAM,
            start_time=ref_time + timedelta(days=5.0),  # > 3 days
        ),
    ]

    score, raw_sum, count, _ = WorkloadEngine.compute_workload_score(
        events=events,
        reference_time=ref_time,
        lookahead_days=3.0,
    )

    assert count == 0
    assert score == 0.0


def test_hysteresis_state_machine_deadband_retention():
    """
    Schmitt Trigger Dead-band:
      - 0.55 < W(t) <= 0.70 retains previous_mode
    """
    # 1. Low workload -> Free mode
    mode, trans, spike = WorkloadEngine.evaluate_hysteresis(score=0.40, previous_mode=None)
    assert mode == WorkloadMode.FREE

    # 2. Score in dead-band (0.60) with previous_mode=FREE -> remains FREE
    mode, trans, spike = WorkloadEngine.evaluate_hysteresis(score=0.60, previous_mode=WorkloadMode.FREE)
    assert mode == WorkloadMode.FREE
    assert trans is False
    assert spike is False

    # 3. Score crosses high threshold (0.75) -> enters BUSY mode and triggers spike
    mode, trans, spike = WorkloadEngine.evaluate_hysteresis(score=0.75, previous_mode=WorkloadMode.FREE)
    assert mode == WorkloadMode.BUSY
    assert trans is True
    assert spike is True

    # 4. Score drops into dead-band (0.60) with previous_mode=BUSY -> remains BUSY
    mode, trans, spike = WorkloadEngine.evaluate_hysteresis(score=0.60, previous_mode=WorkloadMode.BUSY)
    assert mode == WorkloadMode.BUSY
    assert trans is False
    assert spike is False

    # 5. Score drops below 0.55 (0.50) -> transitions back to FREE mode
    mode, trans, spike = WorkloadEngine.evaluate_hysteresis(score=0.50, previous_mode=WorkloadMode.BUSY)
    assert mode == WorkloadMode.FREE
    assert trans is True
    assert spike is False


def test_event_publisher_memory_fallback():
    """Verify EventPublisher handles offline RabbitMQ via memory queue without throwing."""
    publisher = EventPublisher(rabbitmq_url="amqp://nonexistent:5672/")
    publisher.clear_in_memory_events()

    user_id = uuid.uuid4()
    ref_time = datetime(2026, 9, 1, 12, 0, tzinfo=timezone.utc)
    events = [
        EventItem(
            user_id=user_id,
            title="Heavy Final Exam",
            event_type=EventType.EXAM,
            start_time=ref_time + timedelta(hours=6),
        )
    ]

    req = WorkloadCalculationRequest(
        user_id=user_id,
        events=events,
        reference_time=ref_time,
        previous_mode=WorkloadMode.FREE,
    )

    response, spike_event = WorkloadEngine.evaluate(req)

    assert response.is_spike is True
    assert spike_event is not None

    published = publisher.publish_workload_spike(spike_event)
    assert published is False  # Offline RabbitMQ
    in_memory = publisher.get_in_memory_events()
    assert len(in_memory) == 1
    assert in_memory[0]["routing_key"] == "workload.spike.detected"
    assert in_memory[0]["payload"]["score"] == 1.0
