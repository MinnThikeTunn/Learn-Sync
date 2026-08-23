import math
import uuid
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional, Tuple, List

from backend.app.schemas.fsrs import (
    Rating,
    CardState,
    FlashcardModel,
    FlashcardReviewRequest,
    FlashcardReviewResponse,
    LeechQuarantineNotice,
    FlashcardRewriteRequest,
)
from backend.app.schemas.workload import WorkloadMode

logger = logging.getLogger(__name__)


class SpacedRepetitionService:
    """
    Elastic Spaced Repetition Service (FSRS) dynamically coupled to Workload Score W(t).
    
    Coupling Parameters:
    - Free Mode (W(t) <= 0.55): Target retention Rc = 0.90, Interval Multiplier = 1.0x
    - Busy Mode (W(t) > 0.70):  Target retention Rc = 0.80, Interval Multiplier = 1.75x
    
    Leech Quarantine:
    - Threshold: lapses >= 4
    - Pauses card and triggers LLM rewrite prompt generation.
    """

    LEECH_LAPSE_THRESHOLD: int = 4

    RETENTION_FREE_MODE: float = 0.90
    RETENTION_BUSY_MODE: float = 0.80

    MULTIPLIER_FREE_MODE: float = 1.0
    MULTIPLIER_BUSY_MODE: float = 1.75

    @classmethod
    def resolve_workload_parameters(
        cls,
        mode: Optional[WorkloadMode] = None,
        workload_score: Optional[float] = None,
    ) -> Tuple[WorkloadMode, float, float]:
        """
        Determines the effective WorkloadMode, target retention Rc, and interval multiplier.
        """
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
        """
        Calculates retrievability R(S, delta_t) = exp(-ln(9) * delta_t / S).
        """
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
        """
        Computes the updated FSRS metrics (stability, difficulty, reps, lapses, state, scheduled_days).
        """
        # Initial parameters if new card
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
            # Adjust difficulty: rating 1 increases D, rating 4 decreases D
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

        # Compute interval in days: I = S * (ln(Rc) / ln(0.9)) * multiplier
        base_days = max(1.0, new_stability * (math.log(target_retention) / math.log(0.9)))
        if rating == Rating.AGAIN:
            scheduled_days = 0.25  # ~6 hours for again
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
        Executes an FSRS scheduling transition with workload-adaptive target retention & interval scaling,
        and evaluates leech quarantine conditions.
        """
        now = review_time or datetime.now(timezone.utc)
        if now.tzinfo is None:
            now = now.replace(tzinfo=timezone.utc)

        applied_mode, target_retention, interval_multiplier = cls.resolve_workload_parameters(
            mode=workload_mode, workload_score=workload_score
        )

        elapsed_days = (now - card.last_review).total_seconds() / 86400.0 if card.last_review else 0.0

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
            scheduled_days=scheduled_days,
            elapsed_days=round(elapsed_days, 2),
            retention_estimate=round(retention_est, 3),
            target_retention=target_retention,
            interval_multiplier=interval_multiplier,
            applied_mode=applied_mode,
            is_leech_triggered=is_leech_triggered,
            leech_notice=leech_notice,
        )

    @classmethod
    def generate_leech_rewrite_prompt(
        cls, card: FlashcardModel, kc_title: Optional[str] = None
    ) -> FlashcardRewriteRequest:
        """
        Constructs an LLM remediation request prompt to decompose and simplify a leech card.
        """
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
