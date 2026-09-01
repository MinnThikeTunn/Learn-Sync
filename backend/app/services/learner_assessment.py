from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class LearnerArchetype(BaseModel):
    name: str
    code: str
    badge_title: str
    description: str
    primary_format: str
    busy_mode_format: str
    recommended_artifacts: List[str]


class AssessmentResult(BaseModel):
    primary_style: str
    secondary_style: Optional[str] = None
    is_multimodal: bool = False
    archetype: LearnerArchetype
    scores: Dict[str, int]
    recommended_artifacts: List[str]
    system_prompt_directive: str


# 4 Contextual Micro-VARK Scenarios adapted from VARK v8.01 and BJ Fogg B=MAP
VARK_QUESTIONS: List[Dict[str, Any]] = [
    {
        "id": "q1_ingestion",
        "title": "Ingesting Complex Theory",
        "scenario": "When your professor introduces a brand-new, complex architecture or theory, how do you grasp it fastest?",
        "options": {
            "V": {
                "label": "Visual Architecture",
                "detail": "Flowcharts, sequence diagrams, and concept maps showing how components connect.",
                "style": "visual",
            },
            "A": {
                "label": "Conversational Dialogue",
                "detail": "Discussion, podcast-style breakdown, or Socratic step-by-step Q&A.",
                "style": "auditory",
            },
            "R": {
                "label": "Structured Documentation",
                "detail": "Hierarchical notes, formal definitions, code documentation, and bullet points.",
                "style": "read_write",
            },
            "K": {
                "label": "Hands-on Sandbox",
                "detail": "Jumping into an interactive code sandbox or lab and tinkering with parameters directly.",
                "style": "kinesthetic",
            },
        },
    },
    {
        "id": "q2_unblocking",
        "title": "Overcoming a Blocker",
        "scenario": "You're struggling with a difficult assignment problem late at night. What helps you unblock immediately?",
        "options": {
            "V": {
                "label": "Visual Trace",
                "detail": "An annotated diagram tracing the input-to-output state transitions.",
                "style": "visual",
            },
            "A": {
                "label": "Socratic Dialogue",
                "detail": "A targeted conversational prompt leading me to find where my logic broke down.",
                "style": "auditory",
            },
            "R": {
                "label": "Technical Walkthrough",
                "detail": "A detailed written guide with edge cases and algorithm annotations.",
                "style": "read_write",
            },
            "K": {
                "label": "Micro Bug-Fix Puzzle",
                "detail": "A minimal runnable reproduction snippet where I can fix failing unit tests.",
                "style": "kinesthetic",
            },
        },
    },
    {
        "id": "q3_crunch",
        "title": "15-Minute Exam Crunch",
        "scenario": "You have 15 minutes before an exam or quiz. Which study artifact gives you the quickest confidence boost?",
        "options": {
            "V": {
                "label": "Cheat Sheet Map",
                "detail": "A high-contrast visual cheat sheet with layout-coded formula relationships.",
                "style": "visual",
            },
            "A": {
                "label": "30s Audio Recap",
                "detail": "A high-yield 30-second audio summary I can listen to while walking to class.",
                "style": "auditory",
            },
            "R": {
                "label": "Core Primitives List",
                "detail": "A 1-page condensed list of core terms, formulas, and edge cases.",
                "style": "read_write",
            },
            "K": {
                "label": "Rapid-Fire Snippet Check",
                "detail": "3 rapid interactive snippet challenges verifying syntax and execution memory.",
                "style": "kinesthetic",
            },
        },
    },
    {
        "id": "q4_retention",
        "title": "Retention & Spaced Recall",
        "scenario": "When reviewing course materials weeks later, what makes the knowledge truly stick?",
        "options": {
            "V": {
                "label": "Spatial Mind Mapping",
                "detail": "Rebuilding a mental mind-map or visual hierarchy of the semester modules.",
                "style": "visual",
            },
            "A": {
                "label": "Explaining Out Loud",
                "detail": "Explaining the concept out loud in my own words and receiving verbal feedback.",
                "style": "auditory",
            },
            "R": {
                "label": "Self-Authored Summaries",
                "detail": "Rewriting notes in my own words and reviewing flashcard definitions.",
                "style": "read_write",
            },
            "K": {
                "label": "Building From Scratch",
                "detail": "Implementing a mini-project or solving practical test cases from scratch.",
                "style": "kinesthetic",
            },
        },
    },
]

ARCHETYPES: Dict[str, LearnerArchetype] = {
    "visual": LearnerArchetype(
        name="Visual Architect",
        code="visual",
        badge_title="Spatial & Structural Thinker",
        description="Processes abstract concepts through visual hierarchies, sequence diagrams, and architecture maps.",
        primary_format="Interactive Mermaid.js flowcharts & SVG maps",
        busy_mode_format="High-contrast cheat-sheets & annotated cards",
        recommended_artifacts=["Mermaid Diagrams", "Concept Flowcharts", "Visual Hierarchy Sheets"],
    ),
    "auditory": LearnerArchetype(
        name="Socratic Inquirer",
        code="auditory",
        badge_title="Conversational & Dialogue Thinker",
        description="Thrives on verbal reasoning, podcast-style explanations, and interactive Socratic dialogue.",
        primary_format="Socratic dialogue scripts & long-form audio",
        busy_mode_format="30-second rapid audio recaps & verbal prompts",
        recommended_artifacts=["Socratic Audio Explanations", "Podcast Recaps", "Verbal Q&A"],
    ),
    "read_write": LearnerArchetype(
        name="Analytical Scribe",
        code="read_write",
        badge_title="Textual & Precision Thinker",
        description="Excels with comprehensive written prose, detailed markdown outlines, and formal definitions.",
        primary_format="Comprehensive Markdown study guides & notes",
        busy_mode_format="Condensed Pareto 80/20 bullet summaries & key terms",
        recommended_artifacts=["Comprehensive Study Guides", "Pareto Summaries", "Term Glossaries"],
    ),
    "kinesthetic": LearnerArchetype(
        name="Pragmatic Hacker",
        code="kinesthetic",
        badge_title="Hands-on & Experimental Thinker",
        description="Learns by direct manipulation, interactive code sandboxes, and tangible build exercises.",
        primary_format="Interactive code sandboxes & step-by-step labs",
        busy_mode_format="Micro bug-fix snippets & syntax challenges",
        recommended_artifacts=["Code Sandboxes", "Bug-fix Snippets", "Interactive Labs"],
    ),
}


class LearnerAssessmentAgent:
    """
    Sub-agent that evaluates onboarding learner assessments.
    Synthesizes answers into dominant archetypes and configures downstream RAG generation directives.
    """

    MAPPING = {
        "V": "visual",
        "A": "auditory",
        "R": "read_write",
        "K": "kinesthetic",
    }

    def evaluate_responses(self, responses: List[str]) -> AssessmentResult:
        scores: Dict[str, int] = {
            "visual": 0,
            "auditory": 0,
            "read_write": 0,
            "kinesthetic": 0,
        }

        # Tabulate valid responses
        for r in responses:
            upper_r = r.strip().upper()
            if upper_r in self.MAPPING:
                scores[self.MAPPING[upper_r]] += 1

        total_answered = sum(scores.values())
        if total_answered == 0:
            # Fallback to balanced analytical scribe / visual default
            primary = "read_write"
            secondary = "visual"
            is_multimodal = True
        else:
            # Rank descending by score with deterministic tie-breaker priority (visual -> read_write -> kinesthetic -> auditory)
            priority_order = {"visual": 3, "read_write": 2, "kinesthetic": 1, "auditory": 0}
            ranked = sorted(
                scores.items(),
                key=lambda item: (item[1], priority_order.get(item[0], 0)),
                reverse=True,
            )

            primary = ranked[0][0]
            top_score = ranked[0][1]
            second_score = ranked[1][1]

            is_multimodal = (top_score == second_score and top_score > 0)
            secondary = ranked[1][0] if second_score > 0 else None

        archetype = ARCHETYPES.get(primary, ARCHETYPES["read_write"])

        # Construct specific system prompt directive for adaptive RAG orchestrator
        prompt_directive = (
            f"ADAPTIVE LEARNING DIRECTIVE: Student primary cognitive style is '{archetype.name}' ({primary}). "
            f"When generating Free Mode artifacts, prioritize {archetype.primary_format}. "
            f"When in Busy Mode, prioritize {archetype.busy_mode_format}. "
            f"Recommended artifact types: {', '.join(archetype.recommended_artifacts)}."
        )

        return AssessmentResult(
            primary_style=primary,
            secondary_style=secondary,
            is_multimodal=is_multimodal,
            archetype=archetype,
            scores=scores,
            recommended_artifacts=archetype.recommended_artifacts,
            system_prompt_directive=prompt_directive,
        )


learner_assessment_agent = LearnerAssessmentAgent()
