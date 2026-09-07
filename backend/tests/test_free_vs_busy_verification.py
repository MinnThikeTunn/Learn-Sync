import pytest
from datetime import datetime, timezone, timedelta
from uuid import uuid4

from backend.app.schemas.workload import (
    WorkloadMode,
    WorkloadCalculationRequest,
    EventItem,
    EventType,
    FREE_THRESHOLD,
    BUSY_THRESHOLD,
)
from backend.app.services.workload import WorkloadEngine
from backend.app.services.fsrs_engine import (
    SpacedRepetitionService,
    FlashcardModel,
    Rating,
    ScheduleStage,
    CardState,
)
from backend.app.services.learner_agents.base import AgentSynthesisContext
from backend.app.services.learner_agents.visual_agent import VisualLearnerAgent
from backend.app.services.learner_agents.auditory_agent import AuditoryLearnerAgent
from backend.app.services.learner_agents.read_write_agent import ReadWriteLearnerAgent
from backend.app.services.learner_agents.kinesthetic_agent import KinestheticLearnerAgent
from backend.app.schemas.adaptive import AcademicDiscipline
from backend.app.schemas.burnout import BurnoutTriggerRequest
from backend.app.services.burnout_guard import BurnoutGuardService


def test_schmitt_hysteresis_state_machine():
    """Verifies Schmitt Trigger Hysteresis thresholds and Dead-band retention."""
    # 1. Below 0.55 -> FREE
    mode, trans, spike = WorkloadEngine.evaluate_hysteresis(score=0.40, previous_mode=WorkloadMode.BUSY)
    assert mode == WorkloadMode.FREE
    assert trans is True

    # 2. Above 0.70 -> BUSY
    mode, trans, spike = WorkloadEngine.evaluate_hysteresis(score=0.75, previous_mode=WorkloadMode.FREE)
    assert mode == WorkloadMode.BUSY
    assert trans is True
    assert spike is True

    # 3. Dead-band 0.55 < W(t) <= 0.70 holds previous mode
    mode_from_free, trans1, _ = WorkloadEngine.evaluate_hysteresis(score=0.62, previous_mode=WorkloadMode.FREE)
    assert mode_from_free == WorkloadMode.FREE
    assert trans1 is False

    mode_from_busy, trans2, _ = WorkloadEngine.evaluate_hysteresis(score=0.62, previous_mode=WorkloadMode.BUSY)
    assert mode_from_busy == WorkloadMode.BUSY
    assert trans2 is False


def test_fsrs_workload_mode_interval_scaling():
    """Verifies that Busy Mode reduces target retention (90% -> 80%) and expands review intervals."""
    # Free Mode parameters
    mode_f, rc_f, mult_f = SpacedRepetitionService.resolve_workload_parameters(mode=WorkloadMode.FREE)
    assert rc_f == 0.90
    assert mult_f == 1.0

    # Busy Mode parameters
    mode_b, rc_b, mult_b = SpacedRepetitionService.resolve_workload_parameters(mode=WorkloadMode.BUSY)
    assert rc_b == 0.80
    assert mult_b == 1.75

    now = datetime(2026, 9, 7, 12, 0, tzinfo=timezone.utc)
    card = FlashcardModel(
        id=uuid4(),
        user_id=uuid4(),
        folder_id=uuid4(),
        front="Raft consensus leader election quorum",
        back="Majority of voting nodes: floor(N/2) + 1",
        stage=ScheduleStage.GRADUATED_FSRS,
        state=CardState.REVIEW,
        stability=6.0,
        difficulty=4.5,
        reps=4,
        lapses=0,
        due=now,
        last_review=now - timedelta(days=6),
    )

    # Process in Free Mode
    res_free = SpacedRepetitionService.process_review(
        card=card,
        rating=Rating.GOOD,
        review_time=now,
        workload_mode=WorkloadMode.FREE,
    )

    # Process in Busy Mode
    res_busy = SpacedRepetitionService.process_review(
        card=card,
        rating=Rating.GOOD,
        review_time=now,
        workload_mode=WorkloadMode.BUSY,
    )

    # Free Mode target retention = 0.90 -> base_days multiplier = ln(0.9)/ln(0.9) = 1.0
    # Busy Mode target retention = 0.80 -> base_days multiplier = ln(0.8)/ln(0.9) = 2.117
    # Plus interval_multiplier 1.75 -> Total Busy multiplier = 2.117 * 1.75 = 3.70x
    assert res_busy.scheduled_days > res_free.scheduled_days * 3.0
    assert res_busy.target_retention == 0.80
    assert res_free.target_retention == 0.90


def test_vark_agents_synthesize_free_vs_busy():
    """Verifies that all 4 VARK learner agents adapt their output structure between Free and Busy mode."""
    context_free = AgentSynthesisContext(
        folder_id=uuid4(),
        topic="Distributed Consensus Algorithms",
        discipline=AcademicDiscipline.COMPUTER_SCIENCE,
        workload_mode=WorkloadMode.FREE,
        context_summary="Paxos and Raft provide consensus across unreliable nodes using state machine replication.",
        source_chunk_ids=[],
        citations=[],
        confidence=0.95,
    )

    context_busy = AgentSynthesisContext(
        folder_id=context_free.folder_id,
        topic="Distributed Consensus Algorithms",
        discipline=AcademicDiscipline.COMPUTER_SCIENCE,
        workload_mode=WorkloadMode.BUSY,
        context_summary=context_free.context_summary,
        source_chunk_ids=[],
        citations=[],
        confidence=0.95,
    )

    # 1. Visual Agent
    visual = VisualLearnerAgent()
    vis_free = visual.synthesize(context_free)
    vis_busy = visual.synthesize(context_busy)
    assert vis_free.artifact_type.value == "mind_map"
    assert vis_free.metadata.estimated_time_minutes >= 8.0
    assert vis_free.metadata.alternative_diagram_syntax is not None
    assert vis_busy.artifact_type.value == "cheat_sheet"
    assert vis_busy.metadata.estimated_time_minutes <= 2.5

    # 2. Auditory Agent
    auditory = AuditoryLearnerAgent()
    aud_free = auditory.synthesize(context_free)
    aud_busy = auditory.synthesize(context_busy)
    assert aud_free.artifact_type.value == "audio_script"
    assert aud_free.metadata.estimated_time_minutes >= 5.0
    assert aud_busy.artifact_type.value == "micro_recap"
    assert aud_busy.metadata.estimated_time_minutes <= 1.5

    # 3. Read/Write Agent
    read_write = ReadWriteLearnerAgent()
    rw_free = read_write.synthesize(context_free)
    rw_busy = read_write.synthesize(context_busy)
    assert rw_free.metadata.estimated_time_minutes >= 10.0
    assert "Conceptual Framework" in rw_free.content
    assert rw_busy.metadata.estimated_time_minutes <= 2.5
    assert "Pareto" in rw_busy.content

    # 4. Kinesthetic Agent
    med_context_free = AgentSynthesisContext(
        folder_id=uuid4(),
        topic="Acute Myocardial Infarction",
        discipline=AcademicDiscipline.MEDICINE,
        workload_mode=WorkloadMode.FREE,
        context_summary="STEMI triage requires urgent ECG, ASA, heparin, and catheterization within 90 minutes.",
        source_chunk_ids=[],
        citations=[],
        confidence=0.95,
    )
    med_context_busy = AgentSynthesisContext(
        folder_id=med_context_free.folder_id,
        topic="Acute Myocardial Infarction",
        discipline=AcademicDiscipline.MEDICINE,
        workload_mode=WorkloadMode.BUSY,
        context_summary=med_context_free.context_summary,
        source_chunk_ids=[],
        citations=[],
        confidence=0.95,
    )

    kinesthetic = KinestheticLearnerAgent()
    kin_free = kinesthetic.synthesize(med_context_free)
    kin_busy = kinesthetic.synthesize(med_context_busy)
    assert kin_free.metadata.estimated_time_minutes >= 10.0
    assert len(kin_free.metadata.simulation_payload.steps) == 3
    assert kin_busy.metadata.estimated_time_minutes <= 2.0
    assert kin_busy.metadata.simulation_payload.kinesthetic_type == "critical_decision"


def test_burnout_guard_triggers():
    """Verifies that Burnout Guard triggers B=MAP 90-second micro-tasks when acute deadline clusters occur."""
    now = datetime.now(timezone.utc)
    user_id = uuid4()

    # Heavy cluster: 2 major exams in next 48h
    events_busy = [
        EventItem(
            id=uuid4(),
            user_id=user_id,
            title="CS301 Distributed Systems Midterm Exam",
            event_type=EventType.EXAM,
            start_time=now + timedelta(hours=18),
            weight=3.0,
            is_completed=False,
        ),
        EventItem(
            id=uuid4(),
            user_id=user_id,
            title="CS401 Distributed Systems Final",
            event_type=EventType.EXAM,
            start_time=now + timedelta(hours=36),
            weight=3.0,
            is_completed=False,
        ),
    ]

    req_busy = BurnoutTriggerRequest(
        user_id=user_id,
        events=events_busy,
        window_hours=48,
        deadline_threshold=2,
        available_calendar_slots=0,
    )
    resp_busy = BurnoutGuardService.evaluate_burnout_risk(req_busy)
    assert resp_busy.is_burnout_risk is True
    assert resp_busy.micro_task is not None
    assert resp_busy.micro_task.duration_seconds == 90
    assert resp_busy.micro_task.title == "90-Second Reset & Single Concept Anchor"

    # Calm state: 0 upcoming events in next 48h
    req_calm = BurnoutTriggerRequest(
        user_id=user_id,
        events=[],
        window_hours=48,
        deadline_threshold=2,
        available_calendar_slots=3,
    )
    resp_calm = BurnoutGuardService.evaluate_burnout_risk(req_calm)
    assert resp_calm.is_burnout_risk is False
    assert resp_calm.micro_task is None
