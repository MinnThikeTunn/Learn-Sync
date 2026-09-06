from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Type
import copy

from backend.app.schemas.adaptive import (
    LearningStyle,
    StudyArtifact,
)
from backend.app.services.learner_agents.base import (
    AgentSynthesisContext,
    BaseLearnerAgent,
)
from backend.app.services.learner_agents.visual_agent import VisualLearnerAgent
from backend.app.services.learner_agents.auditory_agent import AuditoryLearnerAgent
from backend.app.services.learner_agents.read_write_agent import ReadWriteLearnerAgent
from backend.app.services.learner_agents.kinesthetic_agent import KinestheticLearnerAgent


class LearnerAgentOrchestrator:
    """
    Agent Orchestrator implementing the Spawn-Multi-Subagent Pattern.
    Coordinates specialized autonomous subagents across all VARK modalities:
    - VisualLearnerAgent: Mind maps and flowcharts (mermaid-diagrams compliant)
    - AuditoryLearnerAgent: Socratic dialogue and rapid verbal recaps
    - ReadWriteLearnerAgent: Structured markdown study guides and Pareto takeaways
    - KinestheticLearnerAgent: Multi-discipline interactive simulations

    Capabilities:
    1. Single subagent targeted spawning: spawn_agent(style, context)
    2. Parallel multi-subagent concurrent fan-out: spawn_all_subagents(context)
    """

    def __init__(self):
        self._registry: Dict[LearningStyle, Type[BaseLearnerAgent]] = {
            LearningStyle.VISUAL: VisualLearnerAgent,
            LearningStyle.AUDITORY: AuditoryLearnerAgent,
            LearningStyle.READ_WRITE: ReadWriteLearnerAgent,
            LearningStyle.KINESTHETIC: KinestheticLearnerAgent,
        }

    def get_registered_agents(self) -> List[str]:
        """Returns list of registered subagent names."""
        return [cls.name for cls in self._registry.values()]

    def spawn_agent(
        self,
        style: LearningStyle,
        context: AgentSynthesisContext,
    ) -> StudyArtifact:
        """
        Spawns a single dedicated learner subagent for the requested modality
        and executes its synthesis workflow.
        """
        agent_cls = self._registry.get(style)
        if not agent_cls:
            raise ValueError(f"No subagent registered for learning style '{style}'")

        # Spawn subagent instance
        subagent = agent_cls()
        # Ensure context carries target style
        context.learning_style = style
        # Execute subagent synthesis
        artifact = subagent.synthesize(context)
        return artifact

    def spawn_all_subagents(
        self,
        context: AgentSynthesisContext,
        max_workers: int = 4,
    ) -> Dict[LearningStyle, StudyArtifact]:
        """
        Spawns and executes all specialized subagents concurrently using a
        thread-pool fan-out pattern.
        Returns a dictionary mapping LearningStyle to generated StudyArtifact.
        """
        results: Dict[LearningStyle, StudyArtifact] = {}
        futures_map = {}

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            for style in self._registry.keys():
                # Provide a deepcopy of context so subagents do not mutate shared state
                ctx_copy = copy.deepcopy(context)
                ctx_copy.learning_style = style
                future = executor.submit(self.spawn_agent, style, ctx_copy)
                futures_map[future] = style

            for future in as_completed(futures_map):
                style = futures_map[future]
                try:
                    artifact = future.result()
                    results[style] = artifact
                except Exception as e:
                    # In case of subagent failure, propagate or log
                    raise RuntimeError(
                        f"Subagent for style '{style}' failed execution: {str(e)}"
                    ) from e

        return results


# Global singleton orchestrator
learner_agent_orchestrator = LearnerAgentOrchestrator()
