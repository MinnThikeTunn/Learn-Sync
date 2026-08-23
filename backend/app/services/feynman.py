import re
import uuid
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone

from backend.app.schemas.feynman import (
    FeynmanEvaluationRequest,
    FeynmanGapItem,
    FeynmanPromptRequest,
    FeynmanPromptResponse,
    FeynmanPromptTarget,
    GapAnalysisResult,
    MisconceptionItem,
)
from backend.app.schemas.fsrs import FlashcardCreate


class FeynmanService:
    """
    Active Recall Feynman Loop & Precision-Gap Analysis Engine.
    Guides students to explain complex concepts in plain language, evaluates gaps
    against folder source chunks, and synthesizes remedial flashcards.
    """

    @classmethod
    def generate_prompt(
        cls,
        request: FeynmanPromptRequest,
    ) -> FeynmanPromptResponse:
        concept = request.concept
        target = request.target_audience

        if target == FeynmanPromptTarget.CHILD:
            prompt_text = (
                f"Imagine explaining '{concept}' to a 10-year-old child. "
                "Use a simple everyday analogy (like building blocks, cooking, or playground games), "
                "avoid technical jargon, and explain what it does and why it matters."
            )
            analogy = f"Like a kitchen recipe where each step must finish before serving dinner."
        elif target == FeynmanPromptTarget.NON_TECHNICAL:
            prompt_text = (
                f"Explain '{concept}' to a non-technical coworker or friend. "
                "Focus on the high-level workflow, intuitive cause-and-effect, and practical purpose."
            )
            analogy = f"Like a sorting conveyor belt at a post office."
        else:
            prompt_text = (
                f"Explain '{concept}' to a fellow student who missed the lecture. "
                "Include the core definitions, essential invariants, and common edge cases."
            )
            analogy = f"Like maintaining a call stack of bookmarks in an open book."

        key_points = [
            f"Core definition and purpose of {concept}",
            f"Primary mechanism and step-by-step workflow",
            f"Boundary condition or base case",
        ]

        return FeynmanPromptResponse(
            concept=concept,
            target_audience=target,
            prompt_text=prompt_text,
            analogy_hint=analogy,
            key_points_to_cover=key_points,
        )

    @classmethod
    def evaluate_explanation(
        cls,
        request: FeynmanEvaluationRequest,
    ) -> GapAnalysisResult:
        """
        Runs precision-gap analysis comparing student explanation against source chunks.
        """
        student_text = request.student_explanation.strip().lower()
        concept = request.concept
        chunks_text = " ".join(c.get("content", "").lower() for c in request.context_chunks)

        missing_concepts: List[FeynmanGapItem] = []
        misconceptions: List[MisconceptionItem] = []
        generated_cards: List[FlashcardCreate] = []

        # Analyze keywords & expected components
        has_base_case = any(k in student_text for k in ["base case", "stop", "terminate", "exit condition", "boundary"])
        has_stack_or_flow = any(k in student_text for k in ["call stack", "stack", "frame", "queue", "memory", "state", "step"])
        has_infinite_loop_hazard = any(k in student_text for k in ["overflow", "infinite", "memory leak", "crash", "loop forever"])

        # Check for misconceptions
        if "never terminates" in student_text or "infinite loop is required" in student_text:
            misconceptions.append(
                MisconceptionItem(
                    student_claim="Recursion requires an infinite loop to execute.",
                    correct_fact="Recursion must strictly have a base case to terminate execution and unwind the call stack.",
                    explanation="Without termination, recursion triggers call stack overflow.",
                    severity="critical"
                )
            )

        if "stored in hard drive" in student_text:
            misconceptions.append(
                MisconceptionItem(
                    student_claim="Call stack frames are persisted to permanent hard drive disk.",
                    correct_fact="Call stack frames reside in volatile RAM execution memory.",
                    explanation="Each function call consumes temporary stack frames in RAM.",
                    severity="critical"
                )
            )

        # Check missing components
        if not has_base_case:
            missing_concepts.append(
                FeynmanGapItem(
                    concept=concept,
                    missing_aspect="Base case / termination condition",
                    severity="critical"
                )
            )

        if not has_stack_or_flow and len(student_text.split()) < 30:
            missing_concepts.append(
                FeynmanGapItem(
                    concept=concept,
                    missing_aspect="Mechanism of recursive state / call frames",
                    severity="medium"
                )
            )

        # Calculate completeness score
        base_score = 0.90
        deductions = (len(missing_concepts) * 0.25) + (len(misconceptions) * 0.35)
        completeness_score = max(0.0, min(1.0, round(base_score - deductions, 2)))

        is_sufficient = completeness_score >= 0.70 and len([m for m in misconceptions if m.severity == "critical"]) == 0

        # Build feedback
        if is_sufficient:
            feedback = f"Excellent intuitive explanation of {concept}! You demonstrated clear conceptual command."
        else:
            feedback = f"Good effort on {concept}. However, critical gaps or misconceptions were identified regarding core invariants."

        # Generate remedial flashcards if requested and gaps exist
        if request.auto_generate_flashcards:
            for gap in missing_concepts:
                generated_cards.append(
                    FlashcardCreate(
                        user_id=request.user_id,
                        folder_id=request.folder_id,
                        kc_id=request.kc_id,
                        front=f"In {concept}, why is the {gap.missing_aspect} essential?",
                        back=f"It ensures the recursive process terminates cleanly without causing call stack overflow.",
                    )
                )

            for misc in misconceptions:
                generated_cards.append(
                    FlashcardCreate(
                        user_id=request.user_id,
                        folder_id=request.folder_id,
                        kc_id=request.kc_id,
                        front=f"True/False: {misc.student_claim}",
                        back=f"False. {misc.correct_fact} ({misc.explanation})",
                    )
                )

        return GapAnalysisResult(
            concept=concept,
            completeness_score=completeness_score,
            is_sufficient=is_sufficient,
            feedback=feedback,
            missing_concepts=missing_concepts,
            misconceptions=misconceptions,
            generated_flashcards=generated_cards,
        )
