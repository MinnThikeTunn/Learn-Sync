import math
import uuid
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional, Tuple, List

from backend.app.schemas.fsrs import (
    Rating,
    CardState,
    ScheduleStage,
    FlashcardModel,
    FlashcardReviewRequest,
    FlashcardReviewResponse,
    LeechQuarantineNotice,
    FlashcardRewriteRequest,
    StudyCompletionRequest,
    StudyCompletionResponse,
)
from backend.app.schemas.workload import WorkloadMode
from backend.app.services.database import db_service

logger = logging.getLogger(__name__)


class SpacedRepetitionService:
    """
    Hybrid 2357-FSRS Spaced Repetition Service dynamically coupled to Workload Score W(t).
    
    Two-Phase Learning Cycle:
    1. Early Acquisition (2357 Method):
       - Day 0: Lesson completed in Study tab (Study-to-Review handoff).
       - Day 1 (Stage 1): Initial active recall (+1 day).
       - Day 3 (Stage 2): Second active recall (+2 days -> Day 3).
       - Day 5 (Stage 3): Third active recall (+2 days -> Day 5).
       - Day 7 (Stage 4): Consolidation test (+2 days -> Day 7).
    2. Long-term Retention (FSRS Graduation):
       - Upon passing Day 7 with Good/Easy, the card graduates into elastic FSRS tracking.
       - Free Mode (W(t) <= 0.55): Target retention Rc = 0.90, Multiplier = 1.0x
       - Busy Mode (W(t) > 0.70):  Target retention Rc = 0.80, Multiplier = 1.75x
    
    Leech Quarantine:
       - Threshold: lapses >= 4
       - Automatically isolates difficult cards for AI remediation.
    """

    LEECH_LAPSE_THRESHOLD: int = 4

    RETENTION_FREE_MODE: float = 0.90
    RETENTION_BUSY_MODE: float = 0.80

    MULTIPLIER_FREE_MODE: float = 1.0
    MULTIPLIER_BUSY_MODE: float = 1.75

    # 2357 Stage Progression Map
    NEXT_2357_STAGE: Dict[ScheduleStage, Tuple[ScheduleStage, float]] = {
        ScheduleStage.DAY_1: (ScheduleStage.DAY_3, 2.0),
        ScheduleStage.DAY_3: (ScheduleStage.DAY_5, 2.0),
        ScheduleStage.DAY_5: (ScheduleStage.DAY_7, 2.0),
        ScheduleStage.DAY_7: (ScheduleStage.GRADUATED_FSRS, 7.0),
    }

    @classmethod
    def resolve_workload_parameters(
        cls,
        mode: Optional[WorkloadMode] = None,
        workload_score: Optional[float] = None,
    ) -> Tuple[WorkloadMode, float, float]:
        """Determines effective WorkloadMode, target retention Rc, and interval multiplier."""
        if mode is None:
            if workload_score is not None:
                mode = WorkloadMode.BUSY if workload_score > 0.70 else WorkloadMode.FREE
            else:
                mode = WorkloadMode.FREE

        if mode == WorkloadMode.BUSY:
            return WorkloadMode.BUSY, cls.RETENTION_BUSY_MODE, cls.MULTIPLIER_BUSY_MODE
        return WorkloadMode.FREE, cls.RETENTION_FREE_MODE, cls.MULTIPLIER_FREE_MODE

    @classmethod
    def calculate_retrievability(cls, stability: float, elapsed_days: float) -> float:
        """Calculates retrievability R(S, delta_t) = exp(-ln(9) * delta_t / S)."""
        if stability <= 0.0 or elapsed_days <= 0.0:
            return 1.0
        return math.exp(-math.log(9) * (elapsed_days / stability))

    @classmethod
    def compute_fsrs_transition(
        cls,
        stability: float,
        difficulty: float,
        reps: int,
        lapses: int,
        state: CardState,
        rating: Rating,
        target_retention: float,
        interval_multiplier: float
    ) -> Tuple[float, float, int, int, CardState, float]:
        """Computes continuous FSRS metrics for graduated cards."""
        if state == CardState.NEW or stability <= 0.0:
            initial_stabilities = {
                Rating.AGAIN: 0.4,
                Rating.HARD: 1.2,
                Rating.GOOD: 3.0,
                Rating.EASY: 8.0
            }
            initial_difficulties = {
                Rating.AGAIN: 7.0,
                Rating.HARD: 6.0,
                Rating.GOOD: 5.0,
                Rating.EASY: 3.5
            }
            new_stability = initial_stabilities.get(rating, 2.5)
            new_difficulty = initial_difficulties.get(rating, 5.0)
            new_reps = 1
            new_lapses = 1 if rating == Rating.AGAIN else 0
            new_state = CardState.LEARNING if rating == Rating.AGAIN else CardState.REVIEW
        else:
            new_reps = reps + 1
            d_delta = {Rating.AGAIN: 1.5, Rating.HARD: 0.5, Rating.GOOD: -0.2, Rating.EASY: -1.0}[rating]
            new_difficulty = max(1.0, min(10.0, difficulty + d_delta))

            if rating == Rating.AGAIN:
                new_lapses = lapses + 1
                new_stability = max(0.3, stability * 0.35)
                new_state = CardState.RELEARNING
            else:
                new_lapses = lapses
                mult = {Rating.HARD: 1.2, Rating.GOOD: 2.2, Rating.EASY: 3.5}[rating]
                new_stability = stability * mult * (1.0 + (10.0 - new_difficulty) * 0.1)
                new_state = CardState.REVIEW

        base_days = max(1.0, new_stability * (math.log(target_retention) / math.log(0.9)))
        if rating == Rating.AGAIN:
            scheduled_days = 0.25
        else:
            scheduled_days = round(base_days * interval_multiplier, 2)

        return new_stability, new_difficulty, new_reps, new_lapses, new_state, scheduled_days

    @classmethod
    def process_review(
        cls,
        card: FlashcardModel,
        rating: Rating,
        review_time: Optional[datetime] = None,
        workload_mode: Optional[WorkloadMode] = None,
        workload_score: Optional[float] = None,
    ) -> FlashcardReviewResponse:
        """
        Executes a Hybrid 2357-FSRS transition:
        - In 2357 Stages: advances through Days 1, 3, 5, 7 on success.
        - Once Day 7 passes: graduates into continuous FSRS with W(t) scaling.
        - Evaluates Leech quarantine if lapses >= 4.
        """
        now = review_time or datetime.now(timezone.utc)
        if now.tzinfo is None:
            now = now.replace(tzinfo=timezone.utc)

        applied_mode, target_retention, interval_multiplier = cls.resolve_workload_parameters(
            mode=workload_mode, workload_score=workload_score
        )

        elapsed_days = (now - card.last_review).total_seconds() / 86400.0 if card.last_review else 0.0

        current_stage = card.stage or ScheduleStage.DAY_1
        is_graduated = False

        if current_stage != ScheduleStage.GRADUATED_FSRS:
            # ----------------------------------------------------
            # 2357 Early Acquisition Phase
            # ----------------------------------------------------
            if rating == Rating.AGAIN:
                next_stage = ScheduleStage.DAY_1
                next_lapses = card.lapses + 1
                next_reps = card.reps + 1
                next_stability = 0.5
                next_difficulty = min(10.0, card.difficulty + 1.0) if card.difficulty > 0 else 6.0
                next_state = CardState.LEARNING if card.state == CardState.NEW else CardState.RELEARNING
                scheduled_days = 0.25  # Review again in ~6 hours or next day
            elif rating == Rating.HARD:
                next_stage = current_stage  # Repeat current stage
                next_lapses = card.lapses
                next_reps = card.reps + 1
                next_stability = max(1.0, card.stability)
                next_difficulty = min(10.0, card.difficulty + 0.5) if card.difficulty > 0 else 5.5
                next_state = CardState.REVIEW
                scheduled_days = 1.0 * interval_multiplier
            else:
                # GOOD or EASY -> Advance to next 2357 stage or Graduate
                next_lapses = card.lapses
                next_reps = card.reps + 1
                next_stage_tuple = cls.NEXT_2357_STAGE.get(current_stage, (ScheduleStage.GRADUATED_FSRS, 7.0))
                next_stage, base_interval = next_stage_tuple
                
                if next_stage == ScheduleStage.GRADUATED_FSRS:
                    is_graduated = True
                    next_stability = 14.0 * (1.5 if rating == Rating.EASY else 1.0)
                    next_difficulty = max(1.0, card.difficulty - 0.5) if card.difficulty > 0 else 4.5
                    next_state = CardState.REVIEW
                    scheduled_days = round(base_interval * interval_multiplier, 2)
                else:
                    next_stability = float(base_interval) * 1.5
                    next_difficulty = max(1.0, card.difficulty - 0.2) if card.difficulty > 0 else 5.0
                    next_state = CardState.REVIEW
                    scheduled_days = round(base_interval * interval_multiplier, 2)
        else:
            # ----------------------------------------------------
            # Continuous FSRS Retention Phase
            # ----------------------------------------------------
            is_graduated = True
            next_stage = ScheduleStage.GRADUATED_FSRS
            (
                next_stability,
                next_difficulty,
                next_reps,
                next_lapses,
                next_state,
                scheduled_days
            ) = cls.compute_fsrs_transition(
                stability=card.stability,
                difficulty=card.difficulty,
                reps=card.reps,
                lapses=card.lapses,
                state=card.state,
                rating=rating,
                target_retention=target_retention,
                interval_multiplier=interval_multiplier
            )

        next_due = now + timedelta(days=scheduled_days)
        retention_est = cls.calculate_retrievability(next_stability, elapsed_days)

        is_leech_triggered = False
        leech_notice = None
        is_paused = card.is_paused
        is_leech = card.is_leech

        if next_lapses >= cls.LEECH_LAPSE_THRESHOLD:
            is_leech = True
            is_paused = True
            is_leech_triggered = True
            leech_notice = LeechQuarantineNotice(
                card_id=card.id,
                folder_id=card.folder_id,
                lapses=next_lapses,
                quarantined_at=now,
            )

        updated_card = card.model_copy(
            update={
                "stage": next_stage,
                "stability": round(next_stability, 3),
                "difficulty": round(next_difficulty, 3),
                "reps": next_reps,
                "lapses": next_lapses,
                "state": next_state,
                "due": next_due,
                "last_review": now,
                "is_leech": is_leech,
                "is_paused": is_paused,
                "updated_at": now,
            }
        )

        return FlashcardReviewResponse(
            card=updated_card,
            stage=next_stage,
            scheduled_days=scheduled_days,
            elapsed_days=round(elapsed_days, 2),
            retention_estimate=round(retention_est, 3),
            target_retention=target_retention,
            interval_multiplier=interval_multiplier,
            applied_mode=applied_mode,
            is_graduated=is_graduated,
            is_leech_triggered=is_leech_triggered,
            leech_notice=leech_notice,
        )

    @classmethod
    def complete_study_lesson(
        cls,
        user_id: uuid.UUID,
        folder_id: uuid.UUID,
        topic: str,
        document_id: Optional[uuid.UUID] = None,
        learning_style: str = "visual"
    ) -> StudyCompletionResponse:
        """
        Executes the Study-to-Review Handoff:
        - Finds or provisions candidate flashcards for the topic/document.
        - Schedules their Day 1 active recall review for tomorrow (+24 hours).
        """
        now = datetime.now(timezone.utc)
        first_due = now + timedelta(days=1)

        # Retrieve or auto-generate starter cards for the topic
        existing_cards = db_service.get_due_flashcards(user_id=user_id, folder_id=folder_id, limit=20)
        topic_cards = [c for c in existing_cards if c.get("topic") == topic]

        if not topic_cards:
            # Generate default high-yield concept cards
            sample_prompts = [
                (
                    f"What is the primary definition and significance of {topic}?",
                    f"{topic} establishes the foundational conceptual architecture for this module, enabling modular and low-friction problem solving.",
                ),
                (
                    f"What is a common edge-case or failure mode in {topic}?",
                    f"Neglecting baseline invariants, improper state transitions, or unhandled recursion termination conditions.",
                ),
                (
                    f"How does {topic} integrate with practical exam scenarios?",
                    f"Requires active synthesis, recognizing pattern triggers, and applying step-by-step verification before execution.",
                ),
            ]
            for front, back in sample_prompts:
                db_service.create_flashcard(
                    user_id=user_id,
                    folder_id=folder_id,
                    front=front,
                    back=back,
                    document_id=document_id,
                    topic=topic,
                    stage=ScheduleStage.DAY_1,
                    due=first_due,
                )
            card_count = len(sample_prompts)
        else:
            # Activate existing cards
            for card in topic_cards:
                db_service.update_flashcard_stage(
                    flashcard_id=uuid.UUID(card["id"]),
                    stage=ScheduleStage.DAY_1,
                    due=first_due,
                    is_active_in_queue=True
                )
            card_count = len(topic_cards)

        return StudyCompletionResponse(
            status="success",
            topic=topic,
            folder_id=folder_id,
            cards_scheduled=card_count,
            first_due_date=first_due,
            stage=ScheduleStage.DAY_1,
            message=f"Lesson completed! {card_count} active recall cards scheduled for tomorrow (Day 1 of 2357).",
        )

    @classmethod
    def generate_leech_rewrite_prompt(
        cls, card: FlashcardModel, kc_title: Optional[str] = None
    ) -> FlashcardRewriteRequest:
        """Constructs an LLM remediation request prompt to decompose and simplify a leech card."""
        instructions = (
            f"The student has failed this flashcard {card.lapses} times (Leech Threshold >= 4).\n"
            f"Original Question: {card.front}\n"
            f"Original Solution: {card.back}\n"
            f"{f'Knowledge Component Context: {kc_title}' if kc_title else ''}\n\n"
            "Task:\n"
            "1. Identify why this card is difficult (high cognitive load, ambiguity, multi-part answer).\n"
            "2. Break down the concept into an atomic, simplified question-answer pair.\n"
            "3. Provide an intuitive analogy or mnemonic."
        )
        return FlashcardRewriteRequest(
            card_id=card.id,
            original_front=card.front,
            original_back=card.back,
            lapses=card.lapses,
            kc_title=kc_title,
            prompt_instructions=instructions,
        )
