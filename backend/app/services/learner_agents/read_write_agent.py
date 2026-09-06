from backend.app.schemas.adaptive import (
    LearningStyle,
    StudyArtifact,
    StudyArtifactMetadata,
    StudyArtifactType,
)
from backend.app.schemas.workload import WorkloadMode
from backend.app.services.learner_agents.base import (
    AgentSynthesisContext,
    BaseLearnerAgent,
)


class ReadWriteLearnerAgent(BaseLearnerAgent):
    """
    Subagent specialized in Read/Write text-based synthesis.
    Generates:
    - In-depth, structured markdown study guides with conceptual frameworks
    - 3-Bullet Pareto high-yield summaries
    Supports OpenRouter LLM enrichment with deterministic fallback.
    """

    learning_style = LearningStyle.READ_WRITE
    name = "ReadWriteLearnerAgent"

    def synthesize(self, context: AgentSynthesisContext) -> StudyArtifact:
        topic = context.topic
        discipline = context.discipline
        mode = context.workload_mode
        summary = context.context_summary

        if mode == WorkloadMode.FREE:
            prompt = (
                f"You are an academic researcher crafting a comprehensive study guide on '{topic}' for {discipline.value}.\n"
                f"Context: {summary[:500]}\n"
                f"Write a structured guide with 3 sections: 1. Conceptual Framework & Grounding, 2. Theoretical Formulation & Mechanics, 3. Practical Implications & Edge Cases."
            )

            def default_free_guide() -> str:
                return (
                    f"# Comprehensive Study Guide: {topic}\n\n"
                    f"**Discipline**: {discipline.value.replace('_', ' ').title()}\n\n"
                    f"## 1. Conceptual Framework & Grounding\n"
                    f"{summary[:350]}...\n\n"
                    f"## 2. Theoretical Formulation & Mechanics\n"
                    f"The underlying mechanics follow formal domain constraints with structured invariants.\n\n"
                    f"## 3. Practical Implications & Edge Cases\n"
                    f"Key considerations when applying {topic} under examination and clinical/field conditions."
                )

            content = self.generate_with_llm_or_fallback(prompt, default_free_guide)
            metadata = StudyArtifactMetadata(
                academic_discipline=discipline,
                estimated_time_minutes=10.0,
            )
            art_type = StudyArtifactType.SUMMARY_NOTE
        else:  # Busy Mode: 3-Bullet Pareto Takeaways
            content = (
                f"### 3-Bullet Pareto Takeaways: {topic}\n"
                f"• **Definition**: Core primitive principle in {discipline.value.replace('_', ' ')}.\n"
                f"• **Key Invariant**: Uncompromising rule or formula governing {topic}.\n"
                f"• **High-Yield Exam Focus**: Critical trap or misconception to avoid."
            )
            metadata = StudyArtifactMetadata(
                academic_discipline=discipline,
                estimated_time_minutes=2.0,
            )
            art_type = StudyArtifactType.SUMMARY_NOTE

        return StudyArtifact(
            folder_id=context.folder_id,
            topic=topic,
            learning_style=self.learning_style,
            workload_mode=mode,
            artifact_type=art_type,
            content=content,
            metadata=metadata,
            citations=context.citations,
            source_chunk_ids=context.source_chunk_ids,
            confidence_score=context.confidence,
            is_low_confidence=False,
        )
