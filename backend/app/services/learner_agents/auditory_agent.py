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


class AuditoryLearnerAgent(BaseLearnerAgent):
    """
    Subagent specialized in Auditory synthesis.
    Generates:
    - Socratic dialogue scripts between Professor and Student
    - Rapid verbal recap podcasts
    Supports OpenRouter LLM enrichment with deterministic fallback.
    """

    learning_style = LearningStyle.AUDITORY
    name = "AuditoryLearnerAgent"

    def synthesize(self, context: AgentSynthesisContext) -> StudyArtifact:
        topic = context.topic
        discipline = context.discipline
        mode = context.workload_mode
        summary = context.context_summary

        if mode == WorkloadMode.FREE:
            prompt = (
                f"You are a master educator crafting an engaging Socratic dialogue about '{topic}' in the field of {discipline.value}.\n"
                f"Context summary: {summary[:400]}\n"
                f"Write an educational dialogue between 'Professor' and 'Student' demonstrating deep inquiry into the core principles."
            )

            def default_free_dialogue() -> str:
                return (
                    f"**Socratic Dialogue: Exploring {topic}**\n\n"
                    f"**Professor**: Let's examine how {topic} operates in {discipline.value.replace('_', ' ')}. What is the critical condition to consider?\n\n"
                    f"**Student**: The core requirement is verifying boundary conditions and fundamental principles before proceeding.\n\n"
                    f"**Professor**: Precisely. Notice how the source material emphasizes: '{summary[:120]}...'\n\n"
                    f"**Student**: That connects the theoretical premise directly to real-world outcomes."
                )

            content = self.generate_with_llm_or_fallback(prompt, default_free_dialogue)
            metadata = StudyArtifactMetadata(
                audio_duration_seconds=180,
                speakers=["Professor", "Student"],
                academic_discipline=discipline,
                estimated_time_minutes=5.0,
            )
            art_type = StudyArtifactType.AUDIO_SCRIPT
        else:  # Busy Mode: 30-Second Rapid Recap
            content = (
                f"**30-Second Rapid Recap: {topic}**\n"
                f"- Principle 1: Core foundational anchor in {discipline.value.title()}.\n"
                f"- Principle 2: Primary rule governing state changes.\n"
                f"- Principle 3: Critical pitfall tested in exam evaluations."
            )
            metadata = StudyArtifactMetadata(
                audio_duration_seconds=30,
                speakers=["Narrator"],
                academic_discipline=discipline,
                estimated_time_minutes=1.0,
            )
            art_type = StudyArtifactType.MICRO_RECAP

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
