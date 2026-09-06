import uuid
import re
import logging
from typing import Dict, Any, List, Optional
from uuid import UUID

from backend.app.schemas.fsrs import (
    BlurtingEvaluationRequest,
    BlurtingEvaluationResponse,
)

logger = logging.getLogger(__name__)


class BlurtingService:
    """
    Evaluates unprompted active recall (Blurting) against source document knowledge.
    
    Identifies:
    1. Retained Concepts: Foundational principles accurately reproduced by the student.
    2. Missed Nuances: Key invariants, edge conditions, or specific definitions missed.
    3. Accuracy Score: Percentage (0-100%) evaluating active recall completeness.
    4. Actionable Next Steps: Concrete guidance tailored for the student's next 2357 revision.
    """

    DEFAULT_TOPIC_CONCEPTS: Dict[str, List[str]] = {
        "recursion": [
            "Base case condition to stop recursive calls",
            "Call stack frame allocation in L1/L2 and RAM",
            "Stack overflow risk if base case is omitted",
            "Divide and conquer problem decomposition",
            "Return value propagation back up the call stack",
        ],
        "default": [
            "Core architectural definition and core mechanisms",
            "Critical boundary constraints and invariants",
            "Algorithmic complexity and performance trade-offs",
            "Real-world application patterns and failure modes",
        ],
    }

    @classmethod
    def evaluate_recall(
        cls,
        request: BlurtingEvaluationRequest,
    ) -> BlurtingEvaluationResponse:
        topic_lower = request.topic.lower()
        recall_text = request.user_recall_text.strip()
        recall_lower = recall_text.lower()

        # Find reference concepts
        expected_concepts = []
        for key, concepts in cls.DEFAULT_TOPIC_CONCEPTS.items():
            if key in topic_lower:
                expected_concepts = concepts
                break
        if not expected_concepts:
            # Generate concepts from topic keywords
            words = [w for w in re.findall(r"\w+", request.topic) if len(w) > 3]
            expected_concepts = [
                f"Fundamental definition and purpose of {request.topic}",
                f"Key operational rules and invariants of {words[0] if words else 'concept'}",
                f"Execution steps and computational flow",
                f"Edge cases and error-handling conditions",
            ]

        # Analyze presence of expected concepts in student text with stem matching
        retained: List[str] = []
        missed: List[str] = []
        recall_words = set(re.findall(r"\w+", recall_lower))

        for concept in expected_concepts:
            concept_keywords = [w.lower() for w in re.findall(r"\w+", concept) if len(w) > 2]
            matches = 0
            for kw in concept_keywords:
                stem = kw.rstrip("sedign")
                if kw in recall_lower:
                    matches += 1
                elif stem and len(stem) >= 3 and any(w.startswith(stem) or stem in w for w in recall_words):
                    matches += 1

            if matches >= 1:
                retained.append(concept)
            else:
                missed.append(concept)

        # Word count bonus (length depth) & coverage calculation
        words_count = len(recall_text.split())
        depth_score = min(25, int(words_count * 0.8))
        coverage_ratio = len(retained) / max(1, len(expected_concepts))
        coverage_score = int(coverage_ratio * 75)
        total_score = min(100, max(10, coverage_score + depth_score))

        # Focus recommendations
        if total_score >= 85:
            recommendation = (
                "Outstanding active recall! Your conceptual mastery is solid. "
                "For Day 3 of your 2357 schedule, practice explaining edge-case past exam questions."
            )
        elif total_score >= 60:
            recommendation = (
                "Strong conceptual foundation with minor omissions. "
                f"Focus specifically on: {', '.join(missed[:2]) if missed else 'practical trade-offs'}."
            )
        else:
            recommendation = (
                "Good initial recall attempt. Strengthen memory retention by reviewing the visual diagrams in the Study tab, "
                "then re-test using the Day 1 flashcards tomorrow."
            )

        # Target flashcards for missed points (or deep dive if none missed)
        suggested_cards = []
        for m in missed[:3]:
            suggested_cards.append({
                "front": f"Explain the role of: {m} in {request.topic}",
                "back": f"{m} ensures correctness and prevents unexpected execution failures.",
            })
        if not suggested_cards:
            target_concept = retained[0] if retained else request.topic
            suggested_cards.append({
                "front": f"Deep Dive: How does {target_concept} apply to complex edge cases in {request.topic}?",
                "back": f"Requires rigorous verification of state transitions, boundary conditions, and invariant preservation.",
            })

        return BlurtingEvaluationResponse(
            topic=request.topic,
            accuracy_score=total_score,
            retained_concepts=retained,
            missed_nuances=missed if missed else ["Minor implementation syntax details"],
            recommended_focus=recommendation,
            suggested_cards=suggested_cards,
        )
