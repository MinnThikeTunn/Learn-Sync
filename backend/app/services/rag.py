import re
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID, uuid4
from datetime import datetime, timezone

from backend.app.schemas.adaptive import (
    AcademicDiscipline,
    LearningStyle,
    StudyArtifact,
    StudyArtifactMetadata,
    StudyArtifactType,
    GroundingCitation,
    KinestheticSimulationPayload,
    SimulationStep,
    InteractiveChoice,
    SequencingItem,
)
from backend.app.schemas.workload import WorkloadMode
from backend.app.services.learner_agents import (
    learner_agent_orchestrator,
    AgentSynthesisContext,
    VisualLearnerAgent,
)


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
    def detect_academic_discipline(
        cls,
        chunks: List[Dict[str, Any]],
        topic: str
    ) -> AcademicDiscipline:
        """
        Classifies course subject matter into academic disciplines from text chunks and topic.
        """
        text = (topic + " " + " ".join(c.get("content", "") for c in chunks)).lower()

        medical_kw = [
            "patient", "diagnosis", "symptom", "clinical", "disease", "treatment",
            "ecg", "vitals", "pharmacology", "dosage", "myocardial", "infarction",
            "cardiology", "neurology", "doctor", "nursing", "hospital", "biomarker",
            "troponin", "hypertension", "edema", "acute", "syndrome", "pathology",
            "anatomy", "physiology", "therapy", "cardiac", "stroke", "respiratory"
        ]
        bio_kw = [
            "enzyme", "metabolism", "cellular", "protein", "dna", "rna", "organism",
            "pathway", "reaction", "mitosis", "photosynthesis", "genetics", "substrate",
            "assay", "biology", "chemistry", "microbiology", "titration", "bacteria",
            "membrane", "molecule", "cellular respiration", "amino acid", "glycolysis"
        ]
        law_kw = [
            "statute", "precedent", "court", "plaintiff", "defendant", "liability",
            "tort", "contract", "constitutional", "jurisdiction", "doctrine", "clause",
            "appeal", "legal", "ruling", "judge", "amendment", "prosecution", "negligence"
        ]
        biz_kw = [
            "revenue", "margin", "ebitda", "market", "customer", "valuation",
            "equity", "asset", "financial", "economics", "pricing", "competitor",
            "balance sheet", "cash flow", "portfolio", "roi"
        ]
        cs_kw = [
            "code", "function", "algorithm", "class", "recursion", "complexity",
            "database", "array", "pointer", "syntax", "python", "compiler", "runtime",
            "binary", "tree", "graph", "sorting", "stack", "queue", "api", "software",
            "object-oriented", "data structure", "memory leak", "heap"
        ]

        scores = {
            AcademicDiscipline.MEDICINE: sum(1 for w in medical_kw if w in text),
            AcademicDiscipline.LIFE_SCIENCES: sum(1 for w in bio_kw if w in text),
            AcademicDiscipline.LAW: sum(1 for w in law_kw if w in text),
            AcademicDiscipline.BUSINESS: sum(1 for w in biz_kw if w in text),
            AcademicDiscipline.COMPUTER_SCIENCE: sum(1 for w in cs_kw if w in text),
        }

        best_discipline, max_score = max(scores.items(), key=lambda x: x[1])
        if max_score > 0:
            return best_discipline
        return AcademicDiscipline.GENERAL

    @classmethod
    def compile_concept_tree_to_mermaid_mindmap(cls, tree: Dict[str, Any]) -> str:
        """
        Deterministically compiles a hierarchical concept dictionary into 100% valid
        Mermaid mindmap syntax without risking LLM syntax hallucinations.
        """
        def clean(label: str) -> str:
            cleaned = re.sub(r'[\(\)\[\]\"\{\}:;`]', '', str(label)).strip()
            return cleaned or "Concept"

        root_label = clean(tree.get("root", "Core Concept"))
        lines = [
            "```mermaid",
            "mindmap",
            f"  root(({root_label}))",
        ]

        branches = tree.get("branches", [])
        for branch in branches:
            branch_title = clean(branch.get("title", "Branch"))
            lines.append(f"    {branch_title}")
            for sub in branch.get("sub_branches", []):
                sub_title = clean(sub)
                lines.append(f"      {sub_title}")

        lines.append("```")
        return "\n".join(lines)

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
        Synthesizes personalized study artifacts across multi-discipline modalities
        (Mind Maps for Visual, Universal Interactive Simulations for Kinesthetic,
        Socratic Podcasts for Auditory, and Comprehensive Notes for Read/Write).
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

        discipline = cls.detect_academic_discipline(chunks, topic)
        context_summary = " ".join(c.get("content", "") for c in chunks[:3])

        agent_context = AgentSynthesisContext(
            folder_id=folder_id,
            topic=topic,
            discipline=discipline,
            workload_mode=mode,
            context_summary=context_summary,
            citations=citations,
            source_chunk_ids=source_chunk_ids,
            confidence=confidence,
            learning_style=style,
        )

        return learner_agent_orchestrator.spawn_agent(style, agent_context)

    @classmethod
    def generate_all_artifacts(
        cls,
        folder_id: UUID,
        mode: WorkloadMode,
        topic: str,
        chunks: List[Dict[str, Any]],
        custom_instructions: Optional[str] = None
    ) -> Dict[LearningStyle, StudyArtifact]:
        """
        Multi-agent parallel fan-out: Spawns subagents for all 4 VARK modalities simultaneously
        via the LearnerAgentOrchestrator.
        """
        confidence, is_low = cls.evaluate_retrieval_confidence(chunks, topic)
        citations = cls.extract_citations(chunks, topic) if not is_low else []
        source_chunk_ids = [c.chunk_id for c in citations]

        if is_low:
            fallback_art = StudyArtifact(
                folder_id=folder_id,
                topic=topic,
                learning_style=LearningStyle.READ_WRITE,
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
            return {s: fallback_art for s in LearningStyle}

        discipline = cls.detect_academic_discipline(chunks, topic)
        context_summary = " ".join(c.get("content", "") for c in chunks[:3])

        agent_context = AgentSynthesisContext(
            folder_id=folder_id,
            topic=topic,
            discipline=discipline,
            workload_mode=mode,
            context_summary=context_summary,
            citations=citations,
            source_chunk_ids=source_chunk_ids,
            confidence=confidence,
        )

        return learner_agent_orchestrator.spawn_all_subagents(agent_context)
