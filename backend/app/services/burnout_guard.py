import logging
from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import uuid4

from backend.app.core.events import event_publisher
from backend.app.schemas.burnout import (
    BMAPActionType,
    BMAPMicroTask,
    BurnoutTriggerRequest,
    BurnoutTriggerResponse,
)
from backend.app.schemas.workload import EventItem, EventType

logger = logging.getLogger(__name__)


class BurnoutGuardService:
    """
    Burnout Guard & B=MAP (Behavior = Motivation + Ability + Prompt) Intervention Service.
    Detects acute deadline clusters and emits 90-second micro-tasks to safeguard student cognitive well-being.
    """

    @classmethod
    def evaluate_burnout_risk(
        cls,
        request: BurnoutTriggerRequest,
    ) -> BurnoutTriggerResponse:
        ref_time = request.reference_time or datetime.now(timezone.utc)
        if ref_time.tzinfo is None:
            ref_time = ref_time.replace(tzinfo=timezone.utc)

        window_end = ref_time + timedelta(hours=request.window_hours)

        # Filter active major events in 48h window
        upcoming_major_events = []
        for e in request.events:
            if e.is_completed:
                continue
            e_time = e.start_time
            if e_time.tzinfo is None:
                e_time = e_time.replace(tzinfo=timezone.utc)
            if ref_time <= e_time <= window_end:
                if e.event_type in (EventType.EXAM, EventType.PROJECT, EventType.ASSIGNMENT) or (e.weight and e.weight >= 1.5):
                    upcoming_major_events.append(e)

        deadline_count = len(upcoming_major_events)
        free_slots = request.available_calendar_slots if request.available_calendar_slots is not None else 2

        is_risk = False
        trigger_reason = None

        if deadline_count >= request.deadline_threshold:
            is_risk = True
            trigger_reason = f"Acute deadline cluster: {deadline_count} major deadlines due within 48 hours."
        elif free_slots == 0:
            is_risk = True
            trigger_reason = "Zero available calendar study blocks in the next 48 hours."

        micro_task: Optional[BMAPMicroTask] = None
        published = False

        if is_risk:
            # Generate 90-second low barrier B=MAP micro-task
            micro_task = BMAPMicroTask(
                id=uuid4(),
                user_id=request.user_id,
                title="90-Second Reset & Single Concept Anchor",
                prompt=(
                    "You have a heavy deadline cluster ahead. Let's do a 90-second micro-check: "
                    "Review 1 core flashcard or write 1 sentence summarizing your primary concept, then take a deep breath."
                ),
                action_type=BMAPActionType.SINGLE_FLASHCARD,
                duration_seconds=90,
            )

        return BurnoutTriggerResponse(
            user_id=request.user_id,
            is_burnout_risk=is_risk,
            trigger_reason=trigger_reason,
            deadline_count_48h=deadline_count,
            free_slots_48h=free_slots,
            micro_task=micro_task,
            published_to_event_bus=published,
            evaluated_at=ref_time,
        )
