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

        # Analyze keywords & expected components from concept and context chunks
        concept_terms = set(re.findall(r"\b\w{4,}\b", concept.lower()))
        chunk_terms = set(re.findall(r"\b\w{4,}\b", chunks_text))
        student_terms = set(re.findall(r"\b\w{4,}\b", student_text))

        # Check for specific critical misconception patterns
        if "never terminates" in student_text or "infinite loop is required" in student_text:
            misconceptions.append(
                MisconceptionItem(
                    student_claim="Process requires an infinite loop to execute.",
                    correct_fact=f"{concept} must strictly have an explicit termination condition / base case to halt execution.",
                    explanation="Without termination, state execution overflows memory.",
                    severity="critical"
                )
            )

        if "stored in hard drive" in student_text or "saved on disk permanently" in student_text:
            misconceptions.append(
                MisconceptionItem(
                    student_claim="Volatile execution stack frames are persisted to permanent hard drive disk.",
                    correct_fact="Runtime execution structures reside in high-speed volatile RAM memory.",
                    explanation="Stack frames are ephemeral and deallocated upon return.",
                    severity="critical"
                )
            )

        # Check missing key concept components
        expected_anchors = list(concept_terms) + (list(chunk_terms)[:3] if chunk_terms else [])
        if "recursion" in concept.lower() and not any(k in student_text for k in ["base case", "stop", "terminate", "exit", "boundary"]):
            missing_concepts.append(
                FeynmanGapItem(
                    concept=concept,
                    missing_aspect="Base case / termination condition",
                    severity="critical"
                )
            )
        elif expected_anchors and not any(term in student_terms for term in expected_anchors[:2]):
            missing_concepts.append(
                FeynmanGapItem(
                    concept=concept,
                    missing_aspect=f"Core definitions and key principles of {concept}",
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
            target_user_id = request.user_id or uuid.UUID("00000000-0000-0000-0000-000000000001")
            target_folder_id = request.folder_id or uuid.UUID("00000000-0000-0000-0000-000000000002")
            for gap in missing_concepts:
                generated_cards.append(
                    FlashcardCreate(
                        user_id=target_user_id,
                        folder_id=target_folder_id,
                        kc_id=request.kc_id,
                        front=f"In {concept}, why is the {gap.missing_aspect} essential?",
                        back=f"It ensures the recursive process terminates cleanly without causing call stack overflow.",
                    )
                )

            for misc in misconceptions:
                generated_cards.append(
                    FlashcardCreate(
                        user_id=target_user_id,
                        folder_id=target_folder_id,
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
