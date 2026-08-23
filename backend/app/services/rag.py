from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID, uuid4
from datetime import datetime, timezone

from backend.app.schemas.adaptive import (
    LearningStyle,
    StudyArtifact,
    StudyArtifactMetadata,
    StudyArtifactType,
    GroundingCitation,
)
from backend.app.schemas.workload import WorkloadMode


class AdaptiveLearningEngine:
    """
    Synthesizes grounded study artifacts tailored to a student's LearningStyle
    and current WorkloadMode (Free Mode vs Busy Mode).
    """

    MIN_CONFIDENCE_THRESHOLD: float = 0.25
    MIN_CHUNKS_REQUIRED: int = 1

    @classmethod
    def evaluate_retrieval_confidence(
        cls,
        chunks: List[Dict[str, Any]],
        topic: str
    ) -> Tuple[float, bool]:
        """
        Calculates grounding confidence score based on chunk availability,
        cosine similarity, and RRF scores.
        Returns (confidence_score, is_low_confidence).
        """
        if not chunks or len(chunks) < cls.MIN_CHUNKS_REQUIRED:
            return 0.0, True

        sim_scores = [
            float(c.get("cosine_similarity", c.get("rrf_score", 0.5)))
            for c in chunks
        ]
        avg_score = sum(sim_scores) / len(sim_scores) if sim_scores else 0.0
        confidence = max(0.0, min(1.0, avg_score if avg_score <= 1.0 else avg_score * 30.0))
        is_low = confidence < cls.MIN_CONFIDENCE_THRESHOLD
        return round(confidence, 4), is_low

    @classmethod
    def extract_citations(
        cls,
        chunks: List[Dict[str, Any]],
        topic: str
    ) -> List[GroundingCitation]:
        """
        Builds GroundingCitation objects from retrieved chunks.
        """
        citations = []
        for chunk in chunks:
            content = chunk.get("content", "")
            snippet = content[:150] + "..." if len(content) > 150 else content
            chunk_id = chunk["id"] if isinstance(chunk["id"], UUID) else UUID(str(chunk["id"]))
            doc_id = chunk.get("document_id")
            if doc_id and not isinstance(doc_id, UUID):
                doc_id = UUID(str(doc_id))

            citations.append(
                GroundingCitation(
                    chunk_id=chunk_id,
                    document_id=doc_id,
                    snippet=snippet,
                    relevance_score=float(chunk.get("cosine_similarity", 1.0)),
                )
            )
        return citations

    @classmethod
    def generate_artifact(
        cls,
        folder_id: UUID,
        style: LearningStyle,
        mode: WorkloadMode,
        topic: str,
        chunks: List[Dict[str, Any]],
        custom_instructions: Optional[str] = None
    ) -> StudyArtifact:
        """
        Synthesizes personalized study artifacts across the 8 matrix combinations (4 styles x 2 modes).
        """
        confidence, is_low = cls.evaluate_retrieval_confidence(chunks, topic)
        citations = cls.extract_citations(chunks, topic) if not is_low else []
        source_chunk_ids = [c.chunk_id for c in citations]

        if is_low:
            return StudyArtifact(
                folder_id=folder_id,
                topic=topic,
                learning_style=style,
                workload_mode=mode,
                artifact_type=StudyArtifactType.SUMMARY_NOTE,
                content=f"Insufficient course material found in this folder for topic '{topic}'. Please upload course documents.",
                metadata=StudyArtifactMetadata(estimated_time_minutes=1.0),
                citations=[],
                source_chunk_ids=[],
                confidence_score=confidence,
                is_low_confidence=True,
                warning_message="Retrieval confidence below threshold. Unsupported facts omitted to prevent hallucinations."
            )

        context_summary = " ".join(c.get("content", "") for c in chunks[:3])

        # 1. Visual Style
        if style == LearningStyle.VISUAL:
            if mode == WorkloadMode.FREE:
                content = (
                    f"```mermaid\n"
                    f"flowchart TD\n"
                    f"    A[\"{topic} Core Concept\"] --> B[\"Step 1: Base Foundations\"]\n"
                    f"    B --> C{{\"Evaluation Condition\"}}\n"
                    f"    C -->|Valid| D[\"Process Execution\"]\n"
                    f"    C -->|Recursive Step| B\n"
                    f"    D --> E[\"Mastery State Reached\"]\n"
                    f"```\n\n"
                    f"### Visual Flow Breakdown for {topic}\n"
                    f"- Context: {context_summary[:200]}..."
                )
                metadata = StudyArtifactMetadata(
                    diagram_syntax="mermaid",
                    estimated_time_minutes=8.0
                )
                art_type = StudyArtifactType.DIAGRAM
            else:  # Busy Mode
                content = (
                    f"```mermaid\n"
                    f"graph LR\n"
                    f"    A[\"{topic} Quick Spec\"] --> B[\"Key Primitive\"]\n"
                    f"    B --> C[\"Result: 80/20 Outcome\"]\n"
                    f"```\n\n"
                    f"**Quick Cheat-Sheet**: Core primitive rule for {topic} in under 60 seconds."
                )
                metadata = StudyArtifactMetadata(
                    diagram_syntax="mermaid",
                    estimated_time_minutes=2.0
                )
                art_type = StudyArtifactType.CHEAT_SHEET

        # 2. Auditory Style
        elif style == LearningStyle.AUDITORY:
            if mode == WorkloadMode.FREE:
                content = (
                    f"**Socratic Dialogue: Exploring {topic}**\n\n"
                    f"**Professor**: Let's examine how {topic} operates. What happens when the input boundary is reached?\n\n"
                    f"**Student**: The system must check the base case before making the next recursive call to avoid stack overflow.\n\n"
                    f"**Professor**: Exactly. Notice how the source material notes: '{context_summary[:100]}...'\n\n"
                    f"**Student**: So every branch terminates safely with bounded memory."
                )
                metadata = StudyArtifactMetadata(
                    audio_duration_seconds=180,
                    speakers=["Professor", "Student"],
                    estimated_time_minutes=5.0
                )
                art_type = StudyArtifactType.AUDIO_SCRIPT
            else:  # Busy Mode
                content = (
                    f"**30-Second Rapid Recap: {topic}**\n"
                    f"- Rule 1: High-yield anchor for {topic}.\n"
                    f"- Rule 2: Memory boundary constraint.\n"
                    f"- Rule 3: Typical exam pitfall to avoid."
                )
                metadata = StudyArtifactMetadata(
                    audio_duration_seconds=30,
                    speakers=["Narrator"],
                    estimated_time_minutes=1.0
                )
                art_type = StudyArtifactType.MICRO_RECAP

        # 3. Read/Write Style
        elif style == LearningStyle.READ_WRITE:
            if mode == WorkloadMode.FREE:
                content = (
                    f"# Comprehensive Study Guide: {topic}\n\n"
                    f"## 1. Conceptual Overview\n"
                    f"{context_summary[:300]}...\n\n"
                    f"## 2. Mathematical & Algorithmic Formulation\n"
                    f"The underlying mechanics follow formal state transitions with bounded invariants.\n\n"
                    f"## 3. Practical Implications & Edge Cases\n"
                    f"Key considerations when applying {topic} under production constraints."
                )
                metadata = StudyArtifactMetadata(estimated_time_minutes=10.0)
                art_type = StudyArtifactType.SUMMARY_NOTE
            else:  # Busy Mode
                content = (
                    f"### 3-Bullet Pareto Takeaways: {topic}\n"
                    f"• **Definition**: Core primitive principle derived from course materials.\n"
                    f"• **Key Formula/Rule**: Direct invariant governing {topic}.\n"
                    f"• **Exam Focus**: Primary pitfall tested in upcoming assessments."
                )
                metadata = StudyArtifactMetadata(estimated_time_minutes=2.0)
                art_type = StudyArtifactType.SUMMARY_NOTE

        # 4. Kinesthetic Style
        elif style == LearningStyle.KINESTHETIC:
            if mode == WorkloadMode.FREE:
                content = (
                    f"### Interactive Code Lab: {topic}\n\n"
                    f"```python\n"
                    f"def solve_{topic.lower().replace(' ', '_')}(data: list[int]) -> int:\n"
                    f"    \"\"\"\n"
                    f"    Implement {topic} according to module specifications.\n"
                    f"    \"\"\"\n"
                    f"    # TODO: Implement base case and transformation\n"
                    f"    pass\n"
                    f"```\n\n"
                    f"#### Test Cases:\n"
                    f"Run `pytest` against test suite to verify your implementation."
                )
                metadata = StudyArtifactMetadata(
                    programming_language="python",
                    test_cases=[{"input": [1, 2, 3], "expected": 6}],
                    estimated_time_minutes=15.0
                )
                art_type = StudyArtifactType.CODE_LAB
            else:  # Busy Mode
                content = (
                    f"### 90-Second Micro-Snippet Fix: {topic}\n\n"
                    f"```python\n"
                    f"# Fix the 1-line bug in {topic} logic:\n"
                    f"def fast_check(n: int) -> bool:\n"
                    f"    return n > 0 and (n & (n - 1)) == 0  # Is power of 2\n"
                    f"```"
                )
                metadata = StudyArtifactMetadata(
                    programming_language="python",
                    estimated_time_minutes=1.5
                )
                art_type = StudyArtifactType.MICRO_SNIPPET

        return StudyArtifact(
            folder_id=folder_id,
            topic=topic,
            learning_style=style,
            workload_mode=mode,
            artifact_type=art_type,
            content=content,
            metadata=metadata,
            citations=citations,
            source_chunk_ids=source_chunk_ids,
            confidence_score=confidence,
            is_low_confidence=False
        )
