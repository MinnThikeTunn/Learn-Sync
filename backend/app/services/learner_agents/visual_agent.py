import re
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from backend.app.schemas.adaptive import (
    AcademicDiscipline,
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


class ConceptBranch(BaseModel):
    title: str = Field(..., description="Thematic branch category title")
    sub_branches: List[str] = Field(default_factory=list, description="2 to 3 concise sub-concepts or details from the document")


class ConceptTreeModel(BaseModel):
    root: str = Field(..., description="Root topic title")
    branches: List[ConceptBranch] = Field(default_factory=list, description="List of 3 to 4 categorized branches")
    leaf_descriptions: Dict[str, str] = Field(default_factory=dict, description="Detailed explanatory descriptions for each leaf concept")


class ProcessFlowSpec(BaseModel):
    phase1: str = Field(..., description="Initial foundation or trigger event")
    condition: str = Field(..., description="Critical evaluation or branching test")
    target_state: str = Field(..., description="Normal or target operational state")
    deviation: str = Field(..., description="Deviation, edge case, or anomaly state")
    optimal_outcome: str = Field(..., description="Final resolved or optimal mastery outcome")


class VisualLearnerAgent(BaseLearnerAgent):
    """
    Subagent specialized in Visual synthesis.
    Integrates real LLM concept extraction with deterministic Mermaid compilation:
    - Prompts LLM to extract genuine conceptual hierarchy directly from document chunks
    - Compiles structured trees into valid Mermaid mindmap syntax
    - Prompts LLM to extract sequential process flows (flowchart TD) with safe quoted labels
    - Syntax validation avoiding unquoted parentheses or reserved breaking characters
    """

    learning_style = LearningStyle.VISUAL
    name = "VisualLearnerAgent"

    @classmethod
    def compile_concept_tree_to_mermaid_mindmap(cls, concept_tree: Dict[str, Any]) -> str:
        """
        Compiles a structured concept tree into a deterministic Mermaid mindmap string.
        Adheres to mermaid-diagrams skill guidelines:
        - Root: ((Root Topic))
        - Branches with clean escaped tokens omitting reserved syntax breaking characters
        """
        def clean(label: str) -> str:
            cleaned = re.sub(r'[\(\)\[\]\"\{\}:;`]', '', str(label)).strip()
            return cleaned or "Concept"

        root_label = clean(concept_tree.get("root", "Core Concept"))
        lines = [
            "```mermaid",
            "mindmap",
            f"  root(({root_label}))",
        ]

        branches = concept_tree.get("branches", [])
        for branch in branches:
            if isinstance(branch, dict):
                b_title = branch.get("title", "Branch")
                sub_items = branch.get("sub_branches", [])
            else:
                b_title = getattr(branch, "title", "Branch")
                sub_items = getattr(branch, "sub_branches", [])

            branch_title = clean(b_title)
            lines.append(f"    {branch_title}")
            for sub in sub_items:
                sub_title = clean(sub)
                lines.append(f"      {sub_title}")

        lines.append("```")
        return "\n".join(lines)

    @classmethod
    def build_concept_tree(cls, discipline: AcademicDiscipline, topic: str) -> Dict[str, Any]:
        """Generates baseline discipline-tailored semantic concept tree fallback."""
        if discipline == AcademicDiscipline.MEDICINE:
            return {
                "root": topic,
                "branches": [
                    {"title": "Pathophysiology & Etiology", "sub_branches": ["Primary cellular mechanism", "Risk factors", "Trigger events"]},
                    {"title": "Diagnostic Triad & Biomarkers", "sub_branches": ["Presenting clinical signs", "Laboratory markers", "Diagnostic imaging criteria"]},
                    {"title": "Therapeutic Protocol", "sub_branches": ["First-line pharmacotherapy", "Interventional stabilization", "Post-acute monitoring"]},
                ],
                "leaf_descriptions": {
                    "Primary cellular mechanism": "Ischemia and hypoxia causing ATP depletion, membrane pump failure, and intracellular calcium overload.",
                    "Risk factors": "Atherosclerotic cardiovascular risk factors including hypertension, dyslipidemia, smoking, and diabetes mellitus.",
                    "Trigger events": "Fibrous cap disruption or erosion exposing thrombogenic lipid core and initiating platelet aggregation.",
                    "Presenting clinical signs": "Acute retrosternal chest tightness, radiation to left arm/jaw, diaphoresis, and impending doom sensation.",
                    "Laboratory markers": "High-sensitivity cardiac troponins showing characteristic rise and/or fall with serial kinetics.",
                    "Diagnostic imaging criteria": "Stat 12-lead ECG demonstrating ST elevation, new LBBB, or reciprocal ST depressions.",
                    "First-line pharmacotherapy": "Immediate dual antiplatelet therapy (aspirin + P2Y12 inhibitor) and parenteral anticoagulation.",
                    "Interventional stabilization": "Urgent coronary angiography with primary percutaneous coronary intervention (PCI).",
                    "Post-acute monitoring": "Continuous cardiac telemetry, post-reperfusion evaluation, and long-term secondary prevention.",
                }
            }
        elif discipline == AcademicDiscipline.LIFE_SCIENCES:
            return {
                "root": topic,
                "branches": [
                    {"title": "Upstream Signals", "sub_branches": ["Ligand-receptor binding", "Primary stimuli", "Membrane induction"]},
                    {"title": "Catalytic Machinery", "sub_branches": ["Secondary messengers", "Allosteric enzymes", "Rate-limiting step"]},
                    {"title": "Phenotypic Expression", "sub_branches": ["Transcription activation", "Metabolic flux", "Physiological feedback"]},
                ],
                "leaf_descriptions": {
                    "Ligand-receptor binding": "Extracellular signal molecule binds with high specificity to transmembrane receptor domain.",
                    "Primary stimuli": "Physiological or environmental trigger initiating signal transduction cascade.",
                    "Membrane induction": "Conformational shift altering membrane permeability or recruiting intracellular scaffolding proteins.",
                    "Secondary messengers": "Rapid intracellular amplification via cyclic AMP, IP3, DAG, or calcium ion flux.",
                    "Allosteric enzymes": "Regulatory catalysts whose activity is modulated by non-covalent binding of effector molecules.",
                    "Rate-limiting step": "The slowest, committed regulatory reaction determining overall pathway velocity.",
                    "Transcription activation": "Nuclear translocation of active transcription factors binding promoter response elements.",
                    "Metabolic flux": "Net substrate turnover and product formation through sequential enzymatic reactions.",
                    "Physiological feedback": "Negative feedback loops attenuating receptor sensitivity and restoring basal homeostasis.",
                }
            }
        elif discipline == AcademicDiscipline.LAW:
            return {
                "root": topic,
                "branches": [
                    {"title": "Statutory Foundations", "sub_branches": ["Core elements & definitions", "Legislative intent", "Jurisdictional rules"]},
                    {"title": "Judicial Precedents", "sub_branches": ["Landmark majority rulings", "Dissenting rationales", "Standard of scrutiny"]},
                    {"title": "Application & Defenses", "sub_branches": ["Affirmative defenses", "Evidentiary burdens", "Procedural remedies"]},
                ],
                "leaf_descriptions": {
                    "Core elements & definitions": "The mandatory legal prima facie elements required to establish an actionable claim.",
                    "Legislative intent": "Purpose and statutory context derived from committee reports, statutory preambles, and textual canons.",
                    "Jurisdictional rules": "Subject-matter and personal jurisdictional thresholds determining judicial authority.",
                    "Landmark majority rulings": "Binding appellate precedents establishing governing doctrine and analytical frameworks.",
                    "Dissenting rationales": "Persuasive minority arguments often paving the way for future doctrinal shifts.",
                    "Standard of scrutiny": "The level of judicial review applied to evaluate challenged state or private conduct.",
                    "Affirmative defenses": "Defenses asserted by respondent that defeat legal liability even if allegations are true.",
                    "Evidentiary burdens": "The burden of production and persuasion required under applicable evidentiary standards.",
                    "Procedural remedies": "Injunctions, interlocutory relief, declaratory judgments, or damages.",
                }
            }
        elif discipline == AcademicDiscipline.COMPUTER_SCIENCE:
            return {
                "root": topic,
                "branches": [
                    {"title": "Theoretical Foundations", "sub_branches": ["Data representation", "Time & space bounds", "State invariants"]},
                    {"title": "Algorithmic Pipeline", "sub_branches": ["Base condition check", "Transformation logic", "Termination guarantee"]},
                    {"title": "System Architecture", "sub_branches": ["Concurrency safety", "Memory management", "Production edge cases"]},
                ],
                "leaf_descriptions": {
                    "Data representation": "Structural in-memory layout and node pointers optimizing access patterns.",
                    "Time & space bounds": "Asymptotic worst, average, and amortized algorithmic upper bounds (Big-O notation).",
                    "State invariants": "Mathematical assertions guaranteed to hold true before and after each transformation.",
                    "Base condition check": "Terminating criteria preventing unbounded iteration or recursion stack overflow.",
                    "Transformation logic": "Core arithmetic, bitwise, or structural mutations processing input elements.",
                    "Termination guarantee": "Proof that algorithmic state strictly decreases toward the base condition.",
                    "Concurrency safety": "Thread-safe synchronizations preventing race conditions and deadlocks.",
                    "Memory management": "Heap allocations, stack lifetimes, cache locality, and garbage collection behavior.",
                    "Production edge cases": "Null pointer checks, empty containers, integer overflows, and boundary limits.",
                }
            }
        else:
            return {
                "root": topic,
                "branches": [
                    {"title": "Core Foundations", "sub_branches": ["Fundamental premise", "Historical context", "Primary terms"]},
                    {"title": "Key Mechanics", "sub_branches": ["Operational principles", "Interactions", "Boundary conditions"]},
                    {"title": "Real-World Impact", "sub_branches": ["Strategic applications", "Case studies", "Evaluation criteria"]},
                ],
                "leaf_descriptions": {
                    "Fundamental premise": "The central conceptual bedrock and underlying rationale of the domain concept.",
                    "Historical context": "Evolution and intellectual origins shaping modern interpretations and practices.",
                    "Primary terms": "Key vocabulary and operational definitions essential for domain literacy.",
                    "Operational principles": "How the core mechanisms execute under standard working conditions.",
                    "Interactions": "Causal feedback and relational dynamics between interrelated system components.",
                    "Boundary conditions": "Thresholds and constraints where standard assumptions no longer apply.",
                    "Strategic applications": "High-leverage practical uses and competitive or procedural advantages.",
                    "Case studies": "Documented real-world implementations demonstrating theoretical principles in practice.",
                    "Evaluation criteria": "Metrics and standards used to assess quality, efficiency, and efficacy.",
                }
            }

    def synthesize(self, context: AgentSynthesisContext) -> StudyArtifact:
        topic = context.topic
        discipline = context.discipline
        mode = context.workload_mode
        summary = context.context_summary

        # 1. Dynamically extract Concept Tree via real LLM prompting with document grounding
        concept_tree_prompt = (
            f"You are an expert curriculum architect for {discipline.value}.\n"
            f"Extract a structured conceptual hierarchy from these course chunks for topic '{topic}':\n"
            f"\"\"\"{summary[:1400]}\"\"\"\n\n"
            f"Requirements:\n"
            f"- root: '{topic}'\n"
            f"- branches: exactly 3 distinct categories representing major themes or mechanisms found in the text\n"
            f"- sub_branches: 2 to 3 concise, specific facts, biomarkers, or rules under each branch\n"
            f"- leaf_descriptions: a dictionary mapping each sub_branch name to a clear, 1-2 sentence educational explanation of how it works or its practical significance based on the text.\n"
            f"Ground your response strictly in the provided text."
        )

        def fallback_concept_tree() -> ConceptTreeModel:
            data = self.build_concept_tree(discipline, topic)
            return ConceptTreeModel.model_validate(data)

        concept_tree_model = self.generate_structured_json_with_fallback(
            prompt=concept_tree_prompt,
            schema=ConceptTreeModel,
            fallback_factory=fallback_concept_tree,
        )
        concept_tree = concept_tree_model.model_dump()
        mindmap_code = self.compile_concept_tree_to_mermaid_mindmap(concept_tree)

        # 2. Dynamically extract Sequential Process Flow via real LLM prompting
        flow_prompt = (
            f"Extract the sequential operational, algorithmic, or clinical process flow for '{topic}' from these chunks:\n"
            f"\"\"\"{summary[:1200]}\"\"\"\n\n"
            f"Provide:\n"
            f"- phase1: Initial foundation or trigger\n"
            f"- condition: Primary evaluation or diagnostic decision\n"
            f"- target_state: Normal or target state\n"
            f"- deviation: Anomaly or alternative branch\n"
            f"- optimal_outcome: Desired end outcome"
        )

        def fallback_flow() -> ProcessFlowSpec:
            return ProcessFlowSpec(
                phase1=f"Phase 1: {topic} Foundations",
                condition="Evaluation Condition",
                target_state="Target Execution State",
                deviation="Compensatory Adjustment",
                optimal_outcome="Optimal Outcome Reached",
            )

        flow_spec = self.generate_structured_json_with_fallback(
            prompt=flow_prompt,
            schema=ProcessFlowSpec,
            fallback_factory=fallback_flow,
        )

        def sanitize_label(text: str) -> str:
            clean = re.sub(r'["\n\r\{\}\(\)\[\]]', '', text).strip()
            return clean[:45] or "Process Step"

        process_flow_code = (
            f"```mermaid\n"
            f"flowchart TD\n"
            f"    A[\"{sanitize_label(topic)} Core Concept\"] --> B[\"{sanitize_label(flow_spec.phase1)}\"]\n"
            f"    B --> C{{\"{sanitize_label(flow_spec.condition)}\"}}\n"
            f"    C -->|Valid / Standard| D[\"{sanitize_label(flow_spec.target_state)}\"]\n"
            f"    C -->|Deviation / Anomaly| E[\"{sanitize_label(flow_spec.deviation)}\"]\n"
            f"    D --> F[\"{sanitize_label(flow_spec.optimal_outcome)}\"]\n"
            f"```"
        )

        if mode == WorkloadMode.FREE:
            content = (
                f"{mindmap_code}\n\n"
                f"### Conceptual Architecture & Taxonomy: {topic}\n"
                f"- **Domain Area**: {discipline.value.replace('_', ' ').title()}\n"
                f"- **Context Overview**: {summary[:280]}...\n\n"
                f"Use the interactive toolbar above to toggle between the **Semantic Mind Map** and the **Sequential Process Flow**."
            )
            metadata = StudyArtifactMetadata(
                diagram_syntax="mermaid",
                alternative_diagram_syntax=process_flow_code,
                academic_discipline=discipline,
                concept_tree=concept_tree,
                estimated_time_minutes=8.0,
            )
            art_type = StudyArtifactType.MIND_MAP
        else:  # Busy Mode: Rapid high-contrast visual cheat sheet
            content = (
                f"{mindmap_code}\n\n"
                f"**Quick Cheat-Sheet ({discipline.value.title()})**: 60-second high-yield visual summary for {topic}."
            )
            metadata = StudyArtifactMetadata(
                diagram_syntax="mermaid",
                academic_discipline=discipline,
                concept_tree=concept_tree,
                estimated_time_minutes=2.0,
            )
            art_type = StudyArtifactType.CHEAT_SHEET

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
