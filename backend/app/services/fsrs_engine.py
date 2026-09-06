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
from backend.app.services.review_repository import ReviewRepository, supabase_review_adapter

logger = logging.getLogger(__name__)


class ReviewSessionEngine:
    """
    Review Session Module powered by the Hybrid 2357-FSRS Engine.
    
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

    def __init__(self, repository: Optional[ReviewRepository] = None):
        self.repository = repository or supabase_review_adapter

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

        # Determine if this is an unscheduled early practice or same-day rehearsal session
        is_early_practice = bool(
            (card.due and card.due > now + timedelta(minutes=5))
            or (card.last_review and (now - card.last_review).total_seconds() < 43200)
        )

        if current_stage != ScheduleStage.GRADUATED_FSRS:
            # ----------------------------------------------------
            # 2357 Early Acquisition Phase
            # ----------------------------------------------------
            if rating == Rating.AGAIN:
                if is_early_practice:
                    # Early rehearsal failure: keep current stage and preserve scheduled milestone date
                    next_stage = current_stage
                    next_lapses = card.lapses
                    next_reps = card.reps + 1
                    next_stability = max(0.5, card.stability * 0.8)
                    next_difficulty = min(10.0, card.difficulty + 0.5) if card.difficulty > 0 else 6.0
                    next_state = CardState.REVIEW
                    scheduled_days = max(0.1, (card.due - now).total_seconds() / 86400.0) if card.due and card.due > now else 0.25
                else:
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
                scheduled_days = max(0.1, (card.due - now).total_seconds() / 86400.0) if is_early_practice and card.due and card.due > now else 1.0 * interval_multiplier
            else:
                # GOOD or EASY
                next_lapses = card.lapses
                next_reps = card.reps + 1

                if is_early_practice:
                    # Early / same-day rehearsal: reinforce stability, but strictly DO NOT advance milestone stage!
                    next_stage = current_stage
                    next_stability = max(1.0, card.stability * (1.2 if rating == Rating.EASY else 1.05))
                    next_difficulty = card.difficulty
                    next_state = CardState.REVIEW
                    scheduled_days = max(0.1, (card.due - now).total_seconds() / 86400.0) if card.due and card.due > now else 1.0
                else:
                    # Official milestone review on/after due date: advance to next 2357 milestone or graduate!
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
            if is_early_practice and card.due and card.due > now:
                scheduled_days = max(0.1, (card.due - now).total_seconds() / 86400.0)

        if is_early_practice and card.due and card.due > now:
            next_due = card.due
        else:
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
            is_extra_practice=is_early_practice,
        )

    def submit_review(
        self,
        user_id: uuid.UUID,
        card_id: Optional[uuid.UUID] = None,
        rating: Rating = Rating.GOOD,
        card: Optional[FlashcardModel] = None,
        review_time: Optional[datetime] = None,
        workload_mode: Optional[WorkloadMode] = None,
        workload_score: Optional[float] = None,
    ) -> FlashcardReviewResponse:
        """
        Deep unified interface for reviewing a flashcard:
        1. Resolves card via parameter or persistence adapter
        2. Computes 2357 milestone or continuous FSRS transition with W(t) elasticity
        3. Identifies and isolates Leech cards (lapses >= 4)
        4. Persists updated card state via repository adapter
        5. Logs immutable review audit record via repository adapter
        """
        target_card = card
        if target_card is None and card_id is not None:
            target_card = self.repository.get_card(card_id)

        if target_card is None:
            raise ValueError(f"Flashcard '{card_id}' not found and no card model provided.")

        response = self.process_review(
            card=target_card,
            rating=rating,
            review_time=review_time,
            workload_mode=workload_mode,
            workload_score=workload_score,
        )

        try:
            self.repository.save_card_state(response.card, stage=response.stage)
            self.repository.log_review(
                user_id=user_id,
                flashcard_id=target_card.id,
                rating=int(rating),
                state=int(response.card.state),
                scheduled_days=response.scheduled_days,
                elapsed_days=response.elapsed_days,
            )
        except Exception as e:
            logger.warning(f"Persistence warning during review submit for card {target_card.id}: {e}")

        return response

    def schedule_handoff(
        self,
        user_id: uuid.UUID,
        folder_id: uuid.UUID,
        topic: str,
        document_id: Optional[uuid.UUID] = None,
        learning_style: str = "visual",
        force_regenerate: bool = False,
    ) -> StudyCompletionResponse:
        """
        Executes the Study-to-Review Handoff:
        - Finds or provisions candidate flashcards for the topic/document.
        - Prevents duplicate card creation across multiple visits/clicks.
        - Synthesizes comprehensive active-recall flashcards covering all key concepts.
        - Schedules Day 1 active recall review for tomorrow (+24 hours).
        """
        import re
        now = datetime.now(timezone.utc)
        first_due = now + timedelta(days=1)

        # 1. Fetch ALL existing cards for user & folder to check existence regardless of due date
        all_folder_cards = self.repository.get_all_cards(user_id=user_id, folder_id=folder_id)

        # Match cards for this document/topic
        matched_cards = []
        for c in all_folder_cards:
            c_doc = str(c.get("document_id") or "")
            c_topic = str(c.get("topic") or "").strip().lower()
            if document_id and c_doc == str(document_id):
                matched_cards.append(c)
            elif topic and c_topic == topic.strip().lower():
                matched_cards.append(c)

        # Deduplicate matched cards by front text
        seen_fronts = set()
        unique_cards = []
        for c in matched_cards:
            norm = re.sub(r"[^\w\s]", "", c.get("front", "").strip().lower())
            if norm and norm not in seen_fronts:
                seen_fronts.add(norm)
                unique_cards.append(c)

        # Helper to check if card is merely a generic template placeholder
        def _is_generic_stub(c):
            f = str(c.get("front") or "").lower()
            return (
                "primary definition and significance" in f
                or "common edge-case or failure mode" in f
                or "integrate with practical exam" in f
            )

        has_only_generic_stubs = bool(unique_cards and all(_is_generic_stub(c) for c in unique_cards))

        if not unique_cards or has_only_generic_stubs or force_regenerate:
            sample_prompts = []
            context_text = ""
            try:
                from backend.app.services.database import db_service
                from backend.app.services.llm import generate_text_with_fallback

                # Retrieve up to 50 chunks for complete document coverage
                chunks = db_service.get_document_chunks(
                    user_id=user_id,
                    folder_id=folder_id,
                    document_id=document_id,
                    limit=50,
                )
                context_text = "\n\n".join([c.get("content", "") for c in chunks if c.get("content")])

                if context_text:
                    prompt = f"""You are an expert curriculum designer and cognitive learning scientist.
Extract comprehensive, atomic active-recall flashcards covering ALL distinct concepts, definitions, rules, specifications, parameters, formulas, and verification invariants present in the provided source document:

--- Source Document ---
{context_text[:12000]}
--- End Source Document ---

Topic: {topic}

Requirements:
1. Cover ALL distinct key concepts, identifiers, parameters, specifications, and rules from the document.
2. Every card must be atomic: a clear, specific question on the front and a concise, factual answer on the back.
3. No vague or generic questions. Quote exact values, codes, and names from the text where applicable.
4. Return STRICTLY a valid JSON list of objects:
[
  {{"front": "...", "back": "..."}}
]"""
                    raw = generate_text_with_fallback(prompt, max_tokens=1500)
                    import json
                    cleaned = re.sub(r"^```(?:json)?\s*", "", raw.strip(), flags=re.MULTILINE)
                    cleaned = re.sub(r"\s*```$", "", cleaned.strip(), flags=re.MULTILINE)
                    parsed = json.loads(cleaned)
                    if isinstance(parsed, list):
                        for p in parsed:
                            if isinstance(p, dict) and "front" in p and "back" in p:
                                sample_prompts.append((p["front"].strip(), p["back"].strip()))
            except Exception as e:
                logger.warning(f"LLM flashcard generation fallback to grounded concept extractor: {e}")

            # Grounded offline concept extractor fallback if LLM is unavailable or failed
            if not sample_prompts and context_text:
                sample_prompts = self.extract_grounded_concept_cards(context_text, topic)

            # Ultimate baseline fallback if no document chunks were available
            if not sample_prompts:
                sample_prompts = [
                    (
                        f"What is the primary definition and significance of {topic}?",
                        f"{topic} establishes the foundational conceptual architecture for this module, enabling modular and low-friction problem solving.",
                    ),
                    (
                        f"What is a common edge-case or failure mode in {topic}?",
                        f"Neglecting baseline invariants, improper state transitions, or unhandled boundary conditions.",
                    ),
                    (
                        f"How does {topic} integrate with practical exam scenarios?",
                        f"Requires active synthesis, recognizing pattern triggers, and applying step-by-step verification before execution.",
                    ),
                ]

            # If replacing generic stubs, purge the old generic cards from database
            if has_only_generic_stubs:
                for old_card in matched_cards:
                    cid = old_card.get("id")
                    if cid and hasattr(self.repository, "supabase") and self.repository.supabase and self.repository.supabase.client:
                        try:
                            self.repository.supabase.client.table("flashcards").delete().eq("id", str(cid)).execute()
                        except Exception as e:
                            logger.warning(f"Could not purge old generic stub card {cid}: {e}")

            created_count = 0
            for front, back in sample_prompts:
                norm_f = re.sub(r"[^\w\s]", "", front.strip().lower())
                if norm_f in seen_fronts and not has_only_generic_stubs:
                    continue
                seen_fronts.add(norm_f)
                self.repository.create_card(
                    user_id=user_id,
                    folder_id=folder_id,
                    front=front,
                    back=back,
                    document_id=document_id,
                    topic=topic,
                    stage=ScheduleStage.DAY_1,
                    due=first_due,
                )
                created_count += 1
            card_count = created_count or len(sample_prompts)
        else:
            # Cards already exist: update stage/due date without creating duplicates
            for card in unique_cards:
                cid = uuid.UUID(card["id"]) if isinstance(card["id"], str) else card["id"]
                self.repository.update_card_stage(
                    card_id=cid,
                    stage=ScheduleStage.DAY_1,
                    due=first_due,
                    is_active_in_queue=True,
                )
            card_count = len(unique_cards)

        return StudyCompletionResponse(
            status="success",
            topic=topic,
            folder_id=folder_id,
            cards_scheduled=card_count,
            first_due_date=first_due,
            stage=ScheduleStage.DAY_1,
            message=f"Lesson completed! {card_count} active recall cards scheduled for tomorrow (Day 1 of 2357).",
        )

    @staticmethod
    def extract_grounded_concept_cards(content: str, topic: str) -> List[Tuple[str, str]]:
        """
        Intelligent NLP/rule-based concept extractor running on raw document text.
        Extracts high-yield active-recall question-answer pairs directly from facts:
        - Key-Value pairs (e.g., 'PRISM ID: MW-9842-AX', 'FIDELITY: Grade A1')
        - Bulleted specifications (e.g., '- SOLAR RESONANCE: L: 0.85 C: 0.12 H: 75.5')
        - Definitional sentences ('is defined as', 'refers to', 'represents', 'consists of')
        - Verification signatures and checksums
        """
        import re
        cards: List[Tuple[str, str]] = []
        seen_fronts = set()

        def add_card(q: str, a: str):
            norm = re.sub(r"[^\w\s]", "", q.strip().lower())
            if norm and norm not in seen_fronts and a.strip():
                seen_fronts.add(norm)
                cards.append((q.strip(), a.strip()))

        lines = [line.strip() for line in content.splitlines() if line.strip()]

        # 1. Key-Value & Bullet points extraction
        for line in lines:
            kv_match = re.match(r"^[-*•]?\s*([A-Za-z0-9\s_\-\(\)\/]{3,40})\s*[:=]\s*(.+)$", line)
            if kv_match:
                raw_key = kv_match.group(1).strip()
                val = kv_match.group(2).strip()
                if raw_key.lower() in ("http", "https", "url", "page", "note"):
                    continue
                if len(val) >= 2:
                    if any(term in raw_key.lower() for term in ("spec", "resonance", "anchor", "spark", "color", "parameter")):
                        q = f"What are the parameters for '{raw_key}' in {topic}?"
                    elif any(term in raw_key.lower() for term in ("id", "checksum", "signature", "verified", "signatory", "fidelity", "name", "author")):
                        q = f"What is the recorded '{raw_key}' for {topic}?"
                    else:
                        q = f"What is the value or specification for '{raw_key}' in {topic}?"
                    add_card(q, val)

        # 2. Definitional sentences extraction
        sentences = re.split(r"(?<=[.!?])\s+", content)
        for sent in sentences:
            sent_clean = sent.strip()
            if len(sent_clean) < 20 or len(sent_clean) > 300:
                continue
            def_match = re.search(
                r"([A-Z][A-Za-z0-9\s_\-]{2,30})\s+(is defined as|refers to|represents|is characterized by|consists of)\s+([^.!?]+)",
                sent_clean,
                re.IGNORECASE,
            )
            if def_match:
                term = def_match.group(1).strip()
                verb = def_match.group(2).strip()
                definition = def_match.group(3).strip()
                q = f"How is '{term}' defined in the context of {topic}?"
                add_card(q, f"{term} {verb} {definition}.")

        # 3. Fallback if fewer than 3 cards were extracted
        if len(cards) < 3:
            words = [w for w in re.findall(r"\w+", topic) if len(w) > 3]
            key_term = words[0] if words else topic
            add_card(
                f"What is the primary operational role of {topic}?",
                f"Acts as the core architectural component for {topic}, establishing verified invariants and deterministic execution.",
            )
            add_card(
                f"What critical parameter or invariant must be maintained in {key_term}?",
                f"Adherence to standardized specifications, baseline state transitions, and strict boundary checks.",
            )

        return cards

    def get_due_cards(
        self,
        user_id: uuid.UUID,
        folder_id: Optional[uuid.UUID] = None,
        stage: Optional[str] = None,
        limit: int = 30,
    ) -> List[Dict[str, Any]]:
        """Queries active due flashcards via repository adapter."""
        return self.repository.get_due_cards(user_id=user_id, folder_id=folder_id, stage=stage, limit=limit)

    @classmethod
    def complete_study_lesson(
        cls,
        user_id: uuid.UUID,
        folder_id: uuid.UUID,
        topic: str,
        document_id: Optional[uuid.UUID] = None,
        learning_style: str = "visual",
    ) -> StudyCompletionResponse:
        """Legacy classmethod adapter delegating to review_session_engine.schedule_handoff."""
        return review_session_engine.schedule_handoff(
            user_id=user_id,
            folder_id=folder_id,
            topic=topic,
            document_id=document_id,
            learning_style=learning_style,
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


# Canonical singleton instances and backward-compatible aliases
review_session_engine = ReviewSessionEngine()
SpacedRepetitionService = ReviewSessionEngine

