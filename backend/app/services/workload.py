from datetime import datetime, timezone
from typing import List, Optional, Tuple
from uuid import UUID, uuid4

from backend.app.schemas.workload import (
    BUSY_THRESHOLD,
    FREE_THRESHOLD,
    LOOKAHEAD_DAYS_DEFAULT,
    MIN_DISTANCE_DAYS,
    NORMALIZATION_GAMMA,
    EventItem,
    ModeTransitionEvent,
    WorkloadCalculationRequest,
    WorkloadMode,
    WorkloadScoreResponse,
)


class WorkloadEngine:
    """
    Continuous rolling 3-day lookahead Workload Score W(t) and Schmitt-trigger
    hysteresis state machine.
    """

    @staticmethod
    def calculate_event_decay(
        event: EventItem,
        reference_time: datetime,
        gamma: float = NORMALIZATION_GAMMA,
    ) -> Tuple[float, float]:
        """Calculates fractional days distance d_e(t) and hyperbolic decay contribution."""
        delta = event.start_time - reference_time
        d_e = delta.total_seconds() / 86400.0

        if d_e < 0.0:
            return d_e, 0.0  # Past event

        clamped_d_e = max(MIN_DISTANCE_DAYS, d_e)
        contribution = event.effective_weight / (clamped_d_e * gamma)
        return d_e, contribution

    @classmethod
    def compute_workload_score(
        cls,
        events: List[EventItem],
        reference_time: Optional[datetime] = None,
        lookahead_days: float = LOOKAHEAD_DAYS_DEFAULT,
        gamma: float = NORMALIZATION_GAMMA,
    ) -> Tuple[float, float, int, List[EventItem]]:
        """
        Computes W(t) = min(1.0, sum(w_e / (max(0.25, d_e(t)) * gamma))).
        Returns (score, raw_sum, active_event_count, active_events).
        """
        if reference_time is None:
            reference_time = datetime.now(timezone.utc)
        elif reference_time.tzinfo is None:
            reference_time = reference_time.replace(tzinfo=timezone.utc)

        raw_sum = 0.0
        active_events: List[EventItem] = []

        for event in events:
            if event.is_completed:
                continue

            event_time = event.start_time
            if event_time.tzinfo is None:
                event_time = event_time.replace(tzinfo=timezone.utc)
                event = event.model_copy(update={"start_time": event_time})

            d_e, contribution = cls.calculate_event_decay(event, reference_time, gamma)
            if 0.0 <= d_e <= lookahead_days:
                raw_sum += contribution
                active_events.append(event)

        score = min(1.0, max(0.0, raw_sum))
        return score, raw_sum, len(active_events), active_events

    @classmethod
    def evaluate_hysteresis(
        cls,
        score: float,
        previous_mode: Optional[WorkloadMode] = None,
    ) -> Tuple[WorkloadMode, bool, bool]:
        """
        Schmitt Trigger Logic:
          - score <= 0.55 -> FREE
          - score > 0.70  -> BUSY
          - 0.55 < score <= 0.70 -> Retain previous_mode (default FREE if None)

        Returns: (current_mode, transition_detected, is_spike)
        """
        if score <= FREE_THRESHOLD:
            new_mode = WorkloadMode.FREE
        elif score > BUSY_THRESHOLD:
            new_mode = WorkloadMode.BUSY
        else:
            # Dead-band 0.55 < W(t) <= 0.70: strictly retain prior state
            new_mode = previous_mode if previous_mode in (WorkloadMode.FREE, WorkloadMode.BUSY) else WorkloadMode.FREE

        transition_detected = (previous_mode is not None) and (new_mode != previous_mode)
        is_spike = (new_mode == WorkloadMode.BUSY) and (previous_mode != WorkloadMode.BUSY or previous_mode is None)

        return new_mode, transition_detected, is_spike

    @classmethod
    def evaluate(
        cls,
        request: WorkloadCalculationRequest,
    ) -> Tuple[WorkloadScoreResponse, Optional[ModeTransitionEvent]]:
        ref_time = request.reference_time or datetime.now(timezone.utc)
        if ref_time.tzinfo is None:
            ref_time = ref_time.replace(tzinfo=timezone.utc)

        score, raw_sum, count, active_events = cls.compute_workload_score(
            events=request.events,
            reference_time=ref_time,
            lookahead_days=request.lookahead_days,
        )

        current_mode, transition_detected, is_spike = cls.evaluate_hysteresis(
            score=score,
            previous_mode=request.previous_mode,
        )

        critical_titles = [e.title for e in active_events if e.effective_weight >= 1.5]
        if not critical_titles and active_events:
            critical_titles = [e.title for e in active_events[:3]]

        response = WorkloadScoreResponse(
            user_id=request.user_id,
            score=score,
            current_mode=current_mode,
            previous_mode=request.previous_mode,
            transition_detected=transition_detected,
            is_spike=is_spike,
            lookahead_days=request.lookahead_days,
            active_event_count=count,
            critical_events=critical_titles,
            evaluated_at=ref_time,
            raw_sum=raw_sum,
        )

        spike_event: Optional[ModeTransitionEvent] = None
        if is_spike:
            spike_event = ModeTransitionEvent(
                event_id=uuid4(),
                user_id=request.user_id,
                timestamp=ref_time,
                event_name="workload.spike.detected",
                score=score,
                current_mode=current_mode,
                previous_mode=request.previous_mode,
                active_event_count=count,
                critical_events=[e.title for e in active_events if e.effective_weight >= 2.0],
            )

        return response, spike_event

    @classmethod
    def evaluate_user_workload(
        cls,
        user_id: UUID,
        previous_mode: Optional[WorkloadMode] = None,
        days_ahead: int = 3,
    ) -> WorkloadScoreResponse:
        """
        Evaluates real-time workload for a student by querying their upcoming events
        from the database, computing W(t), evaluating Schmitt hysteresis, and recording the log.
        """
        from backend.app.services.database import db_service
        from backend.app.schemas.workload import EventType

        raw_events = db_service.get_upcoming_events(user_id=user_id, days_ahead=days_ahead)
        event_items: List[EventItem] = []
        for re in raw_events:
            try:
                st = datetime.fromisoformat(re["start_time"]) if isinstance(re["start_time"], str) else re["start_time"]
                etype = EventType(re.get("event_type", "assignment"))
                event_items.append(
                    EventItem(
                        id=UUID(re["id"]) if isinstance(re.get("id"), str) else re.get("id"),
                        user_id=user_id,
                        title=re.get("title", "Academic Event"),
                        event_type=etype,
                        start_time=st,
                        weight=re.get("weight"),
                        is_completed=re.get("is_completed", False),
                    )
                )
            except Exception:
                continue

        req = WorkloadCalculationRequest(
            user_id=user_id,
            events=event_items,
            lookahead_days=float(days_ahead),
            previous_mode=previous_mode,
        )

        response, spike = cls.evaluate(req)

        # Persist workload log to Supabase
        db_service.record_workload_log(
            user_id=user_id,
            score=response.score,
            mode=response.current_mode.value,
            lookahead_days=days_ahead,
            active_event_count=response.active_event_count,
        )

        return response
