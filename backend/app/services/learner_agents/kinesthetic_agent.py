from typing import List, Optional
from backend.app.schemas.adaptive import (
    AcademicDiscipline,
    InteractiveChoice,
    KinestheticSimulationPayload,
    LearningStyle,
    SequencingItem,
    SimulationStep,
    StudyArtifact,
    StudyArtifactMetadata,
    StudyArtifactType,
)
from backend.app.schemas.workload import WorkloadMode
from backend.app.services.learner_agents.base import (
    AgentSynthesisContext,
    BaseLearnerAgent,
)


class KinestheticLearnerAgent(BaseLearnerAgent):
    """
    Subagent specialized in Kinesthetic, tactile, and interactive simulations.
    Dispatches dynamic, LLM-generated simulations grounded in document chunks:
    - Medicine: 3-Stage Clinical Triage Simulation with live Vitals HUD
    - Life Sciences: Chronological Procedural Sequencing Lab
    - Law & Business: Strategic Decision Dilemmas & Rapid Objections
    - Computer Science: Interactive Code Labs & Micro-Snippets
    - Humanities & General: Dialectical Hypothesis Testing
    """

    learning_style = LearningStyle.KINESTHETIC
    name = "KinestheticLearnerAgent"

    def synthesize(self, context: AgentSynthesisContext) -> StudyArtifact:
        topic = context.topic
        discipline = context.discipline
        mode = context.workload_mode
        summary = context.context_summary

        if discipline == AcademicDiscipline.MEDICINE:
            if mode == WorkloadMode.FREE:
                prompt = (
                    f"You are an emergency medicine educator.\n"
                    f"Create an interactive 3-stage clinical triage simulation for topic '{topic}' using these chunks:\n"
                    f"\"\"\"{summary[:1400]}\"\"\"\n\n"
                    f"Requirements for KinestheticSimulationPayload:\n"
                    f"- kinesthetic_type: 'clinical_simulation'\n"
                    f"- academic_discipline: 'medicine'\n"
                    f"- scenario_title: 'Clinical Case Simulation: {topic}'\n"
                    f"- context_brief: realistic patient presentation (age, chief complaint, relevant history)\n"
                    f"- steps: exactly 3 SimulationStep items:\n"
                    f"  1. Stage 1: Presentation & Triage (acute vitals with BP, HR, SpO2, Temp; 2 InteractiveChoices with one optimal and one dangerous/suboptimal choice, immediate_feedback, and consequence_narrative)\n"
                    f"  2. Stage 2: Diagnostic Workup (confirmatory lab/imaging choices; updated vitals)\n"
                    f"  3. Stage 3: Definitive Management (guideline pharmacotherapy or intervention; stabilized vitals)"
                )

                def fallback_med_free() -> KinestheticSimulationPayload:
                    return KinestheticSimulationPayload(
                        kinesthetic_type="clinical_simulation",
                        academic_discipline=discipline,
                        scenario_title=f"Clinical Case Simulation: {topic}",
                        context_brief=f"A 58-year-old patient presents to the Emergency Department with acute clinical findings related to {topic}.",
                        steps=[
                            SimulationStep(
                                step_number=1,
                                title="Stage 1: Presentation & Triage",
                                prompt=f"Patient presents with acute symptoms concerning for {topic}. What is your immediate triage priority?",
                                vitals_or_state={"BP": "88/56 mmHg", "HR": "112 bpm", "SpO2": "92%", "Temp": "37.2°C"},
                                choices=[
                                    InteractiveChoice(
                                        id="med_s1_opt_a",
                                        label="Initiate supplemental oxygen, obtain IV access, and order stat 12-lead ECG",
                                        is_optimal=True,
                                        immediate_feedback="Optimal Action: Immediate stabilization and cardiac rhythm evaluation is paramount.",
                                        consequence_narrative="Patient SpO2 stabilizes to 97%; telemetry monitor is operational.",
                                        vital_impact={"SpO2": "97%", "HR": "104 bpm"}
                                    ),
                                    InteractiveChoice(
                                        id="med_s1_opt_b",
                                        label="Administer oral analgesics and discharge with outpatient follow-up",
                                        is_optimal=False,
                                        immediate_feedback="Dangerous Error: Premature discharge of an unstable patient with abnormal vitals.",
                                        consequence_narrative="Patient decompensates rapidly in the waiting area."
                                    ),
                                ]
                            ),
                            SimulationStep(
                                step_number=2,
                                title="Stage 2: Diagnostic Workup",
                                prompt=f"Initial labs return with elevated biomarkers for {topic}. Which confirmatory investigation is indicated?",
                                vitals_or_state={"BP": "94/62 mmHg", "HR": "98 bpm", "SpO2": "97%", "Temp": "37.1°C"},
                                choices=[
                                    InteractiveChoice(
                                        id="med_s2_opt_a",
                                        label="Order targeted imaging and urgent specialist consultation",
                                        is_optimal=True,
                                        immediate_feedback="Correct: High-sensitivity diagnostic evaluation confirms the primary pathology.",
                                        consequence_narrative="Diagnostic imaging confirms acute pathology; treatment protocol unlocked."
                                    ),
                                    InteractiveChoice(
                                        id="med_s2_opt_b",
                                        label="Order routine non-urgent ultrasound next week",
                                        is_optimal=False,
                                        immediate_feedback="Suboptimal: Acute findings mandate immediate same-day diagnostic confirmation."
                                    ),
                                ]
                            ),
                            SimulationStep(
                                step_number=3,
                                title="Stage 3: Definitive Management",
                                prompt=f"Pathology confirmed for {topic}. Select the evidence-based management protocol:",
                                vitals_or_state={"BP": "110/70 mmHg", "HR": "82 bpm", "SpO2": "99%", "Temp": "36.8°C"},
                                choices=[
                                    InteractiveChoice(
                                        id="med_s3_opt_a",
                                        label="Administer standard protocol intervention and admit to cardiac/intensive monitoring",
                                        is_optimal=True,
                                        immediate_feedback="Mastery Achieved: Guidelines-directed therapy resolved hemodynamic compromise.",
                                        consequence_narrative="Patient stabilized successfully. Case completed with full clinical recovery."
                                    ),
                                    InteractiveChoice(
                                        id="med_s3_opt_b",
                                        label="Prescribe broad-spectrum sedatives alone without treating root pathology",
                                        is_optimal=False,
                                        immediate_feedback="Critical Failure: Symptom suppression without resolving etiology causes recurrent collapse."
                                    ),
                                ]
                            ),
                        ]
                    )

                sim_payload = self.generate_structured_json_with_fallback(prompt, KinestheticSimulationPayload, fallback_med_free)

                # Ensure vitals_or_state and vital_impact are present for the live Vitals HUD
                if sim_payload.steps:
                    for s_idx, step in enumerate(sim_payload.steps):
                        if not step.vitals_or_state:
                            step.vitals_or_state = {"BP": "90/60 mmHg", "HR": "110 bpm", "SpO2": "93%", "Temp": "37.2°C"}
                        for c in step.choices:
                            if c.is_optimal and not c.vital_impact:
                                c.vital_impact = {"SpO2": "98%", "HR": "82 bpm", "BP": "118/76 mmHg"}

                content = (
                    f"### Clinical Case Simulation: {topic}\n\n"
                    f"**Patient Presentation**: {sim_payload.context_brief}\n\n"
                    f"Step through the 3-stage clinical progression below to stabilize and manage the patient."
                )
                metadata = StudyArtifactMetadata(
                    academic_discipline=discipline,
                    simulation_payload=sim_payload,
                    estimated_time_minutes=12.0
                )
                art_type = StudyArtifactType.CLINICAL_SIMULATION
            else:  # Busy Mode
                sim_payload = KinestheticSimulationPayload(
                    kinesthetic_type="critical_decision",
                    academic_discipline=discipline,
                    scenario_title=f"60-Second Critical Triage: {topic}",
                    context_brief="Emergency Decision Point: Time-critical intervention required.",
                    steps=[
                        SimulationStep(
                            step_number=1,
                            title="Emergency Call",
                            prompt=f"Acute clinical presentation of {topic}. What is the single most critical stat order?",
                            vitals_or_state={"BP": "80/50 mmHg", "HR": "128 bpm", "SpO2": "89%"},
                            choices=[
                                InteractiveChoice(
                                    id="crit_med_1",
                                    label="Administer immediate guideline antidote/stabilizer and call code team",
                                    is_optimal=True,
                                    immediate_feedback="Life-saving decision: Prompt intervention restored perfusion.",
                                ),
                                InteractiveChoice(
                                    id="crit_med_2",
                                    label="Wait 30 minutes for repeat vital signs check",
                                    is_optimal=False,
                                    immediate_feedback="Critical Delay: Failure to act leads to cardiac arrest.",
                                ),
                            ]
                        )
                    ]
                )
                content = f"### 60-Second Critical Decision: {topic}\n\nMake the urgent clinical call in under 60 seconds."
                metadata = StudyArtifactMetadata(
                    academic_discipline=discipline,
                    simulation_payload=sim_payload,
                    estimated_time_minutes=1.0
                )
                art_type = StudyArtifactType.CRITICAL_DECISION

        elif discipline == AcademicDiscipline.LIFE_SCIENCES:
            if mode == WorkloadMode.FREE:
                prompt = (
                    f"You are a molecular biology and biochemistry instructor.\n"
                    f"Extract the 4 sequential chronological stages of the pathway/mechanism for '{topic}' from these chunks:\n"
                    f"\"\"\"{summary[:1400]}\"\"\"\n\n"
                    f"Requirements for KinestheticSimulationPayload:\n"
                    f"- kinesthetic_type: 'procedural_sequencing'\n"
                    f"- academic_discipline: 'life_sciences'\n"
                    f"- scenario_title: 'Procedural Pathway Sequencing: {topic}'\n"
                    f"- context_brief: brief overview of the pathway to sequence\n"
                    f"- sequencing_items: exactly 4 SequencingItem entries with id, label, correct_order (1 to 4), and rationale"
                )

                def fallback_bio_free() -> KinestheticSimulationPayload:
                    return KinestheticSimulationPayload(
                        kinesthetic_type="procedural_sequencing",
                        academic_discipline=discipline,
                        scenario_title=f"Procedural Pathway Sequencing: {topic}",
                        context_brief=f"Order the sequential stages of the biological mechanism or experimental protocol for {topic}.",
                        sequencing_items=[
                            SequencingItem(id="seq_1", label="Receptor binding and signal initiation", correct_order=1, rationale="First event triggering cascade."),
                            SequencingItem(id="seq_2", label="Conformational activation of downstream enzyme", correct_order=2, rationale="Enzyme activation catalyzes second messenger."),
                            SequencingItem(id="seq_3", label="Second messenger amplification (cAMP/IP3)", correct_order=3, rationale="Amplifies intracellular signal."),
                            SequencingItem(id="seq_4", label="Cellular transcription and phenotypic response", correct_order=4, rationale="Final biological outcome."),
                        ]
                    )

                sim_payload = self.generate_structured_json_with_fallback(prompt, KinestheticSimulationPayload, fallback_bio_free)
                content = (
                    f"### Procedural Sequencing Lab: {topic}\n\n"
                    f"Reorder the scrambled mechanism stages into their true chronological order."
                )
                metadata = StudyArtifactMetadata(
                    academic_discipline=discipline,
                    simulation_payload=sim_payload,
                    estimated_time_minutes=8.0
                )
                art_type = StudyArtifactType.PROCEDURAL_SEQUENCING
            else:  # Busy Mode
                sim_payload = KinestheticSimulationPayload(
                    kinesthetic_type="critical_decision",
                    academic_discipline=discipline,
                    scenario_title=f"Rate-Limiting Checkpoint: {topic}",
                    context_brief="Identify the committed regulatory step in the pathway.",
                    steps=[
                        SimulationStep(
                            step_number=1,
                            title="Pathway Regulation",
                            prompt=f"In the {topic} pathway, which step represents the irreversible, rate-limiting control point?",
                            choices=[
                                InteractiveChoice(
                                    id="crit_bio_1",
                                    label="Primary kinase phosphorylation step subject to allosteric feedback",
                                    is_optimal=True,
                                    immediate_feedback="Correct! This committed step regulates total pathway flux.",
                                ),
                                InteractiveChoice(
                                    id="crit_bio_2",
                                    label="Equilibrium diffusion of inert co-products",
                                    is_optimal=False,
                                    immediate_feedback="Incorrect: Passive diffusion is non-regulatory.",
                                ),
                            ]
                        )
                    ]
                )
                content = f"### Rate-Limiting Checkpoint: {topic}\n\nIdentify the primary control mechanism."
                metadata = StudyArtifactMetadata(
                    academic_discipline=discipline,
                    simulation_payload=sim_payload,
                    estimated_time_minutes=1.0
                )
                art_type = StudyArtifactType.CRITICAL_DECISION

        elif discipline in (AcademicDiscipline.LAW, AcademicDiscipline.BUSINESS):
            if mode == WorkloadMode.FREE:
                prompt = (
                    f"You are a legal and strategic business case designer.\n"
                    f"Create an authentic strategic decision dilemma for '{topic}' from these chunks:\n"
                    f"\"\"\"{summary[:1400]}\"\"\"\n\n"
                    f"Requirements for KinestheticSimulationPayload:\n"
                    f"- kinesthetic_type: 'decision_dilemma'\n"
                    f"- academic_discipline: '{discipline.value}'\n"
                    f"- scenario_title: 'Decision Dilemma & Strategic Analysis: {topic}'\n"
                    f"- context_brief: realistic factual dispute or business strategic dilemma\n"
                    f"- steps: 1 to 2 SimulationStep items with prompt, and choices (optimal vs flawed with rationale)"
                )

                def fallback_law_free() -> KinestheticSimulationPayload:
                    return KinestheticSimulationPayload(
                        kinesthetic_type="decision_dilemma",
                        academic_discipline=discipline,
                        scenario_title=f"Decision Dilemma & Strategic Analysis: {topic}",
                        context_brief=f"Analyze the scenario dilemma regarding {topic} and choose the optimal legal/strategic course of action.",
                        steps=[
                            SimulationStep(
                                step_number=1,
                                title="Threshold Dilemma",
                                prompt=f"A conflict arises involving the core doctrine of {topic}. What is the legally sound or strategic first response?",
                                choices=[
                                    InteractiveChoice(
                                        id="dilemma_1",
                                        label="Invoke established binding precedent and seek immediate interlocutory relief",
                                        is_optimal=True,
                                        immediate_feedback="Strong Argument: Supported by controlling statutory and case authority.",
                                    ),
                                    InteractiveChoice(
                                        id="dilemma_2",
                                        label="Concede jurisdiction without asserting affirmative defenses",
                                        is_optimal=False,
                                        immediate_feedback="Fatal Error: Waives critical procedural protections.",
                                    ),
                                ]
                            )
                        ]
                    )

                sim_payload = self.generate_structured_json_with_fallback(prompt, KinestheticSimulationPayload, fallback_law_free)
                content = f"### Strategic Dilemma: {topic}\n\n{sim_payload.context_brief}"
                metadata = StudyArtifactMetadata(
                    academic_discipline=discipline,
                    simulation_payload=sim_payload,
                    estimated_time_minutes=10.0
                )
                art_type = StudyArtifactType.DECISION_DILEMMA
            else:  # Busy Mode
                sim_payload = KinestheticSimulationPayload(
                    kinesthetic_type="critical_decision",
                    academic_discipline=discipline,
                    scenario_title=f"Instant Objection Ruling: {topic}",
                    context_brief="Immediate judicial or negotiation call required.",
                    steps=[
                        SimulationStep(
                            step_number=1,
                            title="Rapid Call",
                            prompt=f"Opposing counsel attempts to introduce evidence violating the rule of {topic}. Your ruling:",
                            choices=[
                                InteractiveChoice(id="call_1", label="Sustained: Evidence is inadmissible under established doctrine.", is_optimal=True, immediate_feedback="Correct ruling: Precedent strictly bars introduction."),
                                InteractiveChoice(id="call_2", label="Overruled: Allow unrestricted introduction without scrutiny.", is_optimal=False, immediate_feedback="Incorrect: Reversible legal error."),
                            ]
                        )
                    ]
                )
                content = f"### Instant Ruling: {topic}\n\nMake the call in under 60 seconds."
                metadata = StudyArtifactMetadata(
                    academic_discipline=discipline,
                    simulation_payload=sim_payload,
                    estimated_time_minutes=1.0
                )
                art_type = StudyArtifactType.CRITICAL_DECISION

        elif discipline == AcademicDiscipline.COMPUTER_SCIENCE:
            if mode == WorkloadMode.FREE:
                func_name = f"solve_{topic.lower().replace(' ', '_')}"
                prompt = (
                    f"You are a software engineering tutor designing a coding lab.\n"
                    f"Create an interactive code lab for '{topic}' based on these chunks:\n"
                    f"\"\"\"{summary[:1400]}\"\"\"\n\n"
                    f"Requirements for KinestheticSimulationPayload:\n"
                    f"- kinesthetic_type: 'code_sandbox'\n"
                    f"- academic_discipline: 'computer_science'\n"
                    f"- scenario_title: 'Code Challenge: {topic}'\n"
                    f"- context_brief: problem statement and specifications\n"
                    f"- starter_code: python function stub with docstring\n"
                    f"- language: 'python'\n"
                    f"- test_cases: 1 to 2 sample inputs and expected outputs"
                )

                def fallback_cs_free() -> KinestheticSimulationPayload:
                    return KinestheticSimulationPayload(
                        kinesthetic_type="code_sandbox",
                        academic_discipline=discipline,
                        scenario_title=f"Code Challenge: {topic}",
                        context_brief="Write and test code directly in the browser sandbox.",
                        starter_code=f"def {func_name}(data: list[int]) -> int:\n    \"\"\"\n    Implement {topic} according to module specifications.\n    \"\"\"\n    # TODO: Implement base case and transformation\n    pass\n",
                        language="python",
                        test_cases=[{"input": [1, 2, 3], "expected": 6}]
                    )

                sim_payload = self.generate_structured_json_with_fallback(prompt, KinestheticSimulationPayload, fallback_cs_free)
                content = (
                    f"### Interactive Code Lab: {topic}\n\n"
                    f"```python\n"
                    f"{sim_payload.starter_code or f'def {func_name}(): pass'}\n"
                    f"```\n\n"
                    f"#### Specifications:\n"
                    f"{sim_payload.context_brief}"
                )
                metadata = StudyArtifactMetadata(
                    programming_language=sim_payload.language or "python",
                    academic_discipline=discipline,
                    simulation_payload=sim_payload,
                    test_cases=sim_payload.test_cases or [{"input": [1, 2, 3], "expected": 6}],
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
                sim_payload = KinestheticSimulationPayload(
                    kinesthetic_type="code_sandbox",
                    academic_discipline=discipline,
                    scenario_title=f"90-Second Bug Fix: {topic}",
                    context_brief="Repair the one-line syntax bug.",
                    starter_code="def fast_check(n: int) -> bool:\n    return n > 0 and (n & (n - 1)) == 0\n",
                    language="python"
                )
                metadata = StudyArtifactMetadata(
                    programming_language="python",
                    academic_discipline=discipline,
                    simulation_payload=sim_payload,
                    estimated_time_minutes=1.5
                )
                art_type = StudyArtifactType.MICRO_SNIPPET

        else:  # General / Humanities
            sim_payload = KinestheticSimulationPayload(
                kinesthetic_type="decision_dilemma",
                academic_discipline=discipline,
                scenario_title=f"Analytical Scenario Simulation: {topic}",
                context_brief=f"Analyze the scenario dilemma for {topic}.",
                steps=[
                    SimulationStep(
                        step_number=1,
                        title="Hypothesis Testing",
                        prompt=f"Given the primary thesis of {topic}, which argument withstands counter-factual evaluation?",
                        choices=[
                            InteractiveChoice(id="gen_1", label="The thesis grounded by empirical evidence and internal consistency", is_optimal=True, immediate_feedback="Well reasoned: Withstands rigorous criticism."),
                            InteractiveChoice(id="gen_2", label="An ungrounded assertion relying on circular definitions", is_optimal=False, immediate_feedback="Logical Fallacy: Fails dialectical scrutiny."),
                        ]
                    )
                ]
            )
            content = f"### Analytical Simulation: {topic}\n\nEvaluate the hypothesis and choose the evidence-based position."
            metadata = StudyArtifactMetadata(
                academic_discipline=discipline,
                simulation_payload=sim_payload,
                estimated_time_minutes=6.0
            )
            art_type = StudyArtifactType.DECISION_DILEMMA

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
            is_low_confidence=False
        )
