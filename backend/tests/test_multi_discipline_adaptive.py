import pytest
from uuid import uuid4

from backend.app.schemas.adaptive import (
    AcademicDiscipline,
    LearningStyle,
    StudyArtifactType,
    KinestheticSimulationPayload,
)
from backend.app.schemas.workload import WorkloadMode
from backend.app.services.rag import AdaptiveLearningEngine


def test_detect_academic_discipline():
    # 1. Medicine
    med_chunks = [
        {"content": "The patient presented to emergency with chest pain and elevated troponin biomarkers."},
        {"content": "12-lead ECG confirmed ST-elevation myocardial infarction requiring stat catheterization."}
    ]
    assert AdaptiveLearningEngine.detect_academic_discipline(med_chunks, "Cardiology") == AcademicDiscipline.MEDICINE

    # 2. Life Sciences
    bio_chunks = [
        {"content": "Glycolysis is a metabolic pathway catalyzed by hexokinase and phosphofructokinase enzymes."},
        {"content": "The cellular reaction converts glucose to pyruvate with net ATP and NADH yield."}
    ]
    assert AdaptiveLearningEngine.detect_academic_discipline(bio_chunks, "Cellular Respiration") == AcademicDiscipline.LIFE_SCIENCES

    # 3. Law
    law_chunks = [
        {"content": "The plaintiff established a prima facie case of negligence under tort liability doctrine."},
        {"content": "The appellate court ruled that the statute did not violate constitutional due process."}
    ]
    assert AdaptiveLearningEngine.detect_academic_discipline(law_chunks, "Tort Law") == AcademicDiscipline.LAW

    # 4. Computer Science
    cs_chunks = [
        {"content": "The binary search tree algorithm operates in O(log n) time complexity."},
        {"content": "Recursive functions must verify base condition to prevent stack overflow."}
    ]
    assert AdaptiveLearningEngine.detect_academic_discipline(cs_chunks, "Binary Search Tree") == AcademicDiscipline.COMPUTER_SCIENCE


def test_compile_concept_tree_to_mermaid_mindmap():
    tree = {
        "root": "Cardiology: ACS",
        "branches": [
            {
                "title": "Pathophysiology",
                "sub_branches": ["Plaque rupture", "Coronary thrombosis"]
            },
            {
                "title": "Workup",
                "sub_branches": ["12-lead ECG", "Cardiac biomarkers"]
            }
        ]
    }

    mindmap_code = AdaptiveLearningEngine.compile_concept_tree_to_mermaid_mindmap(tree)
    assert mindmap_code.startswith("```mermaid\nmindmap")
    assert "root((Cardiology ACS))" in mindmap_code  # Colons stripped for Mermaid safety
    assert "    Pathophysiology" in mindmap_code
    assert "      Plaque rupture" in mindmap_code
    assert "    Workup" in mindmap_code
    assert mindmap_code.endswith("```")


def test_visual_mindmap_artifact_synthesis():
    folder_id = uuid4()
    chunks = [
        {"id": uuid4(), "content": "Acute coronary syndrome involves myocardial ischemia with abnormal ECG findings.", "cosine_similarity": 0.88}
    ]

    # Free Mode -> MIND_MAP
    artifact = AdaptiveLearningEngine.generate_artifact(
        folder_id=folder_id,
        style=LearningStyle.VISUAL,
        mode=WorkloadMode.FREE,
        topic="Myocardial Infarction",
        chunks=chunks
    )

    assert artifact.artifact_type == StudyArtifactType.MIND_MAP
    assert "mindmap" in artifact.content
    assert artifact.metadata.diagram_syntax == "mermaid"
    assert artifact.metadata.alternative_diagram_syntax is not None
    assert "flowchart TD" in artifact.metadata.alternative_diagram_syntax
    assert artifact.metadata.concept_tree is not None
    assert artifact.metadata.academic_discipline == AcademicDiscipline.MEDICINE

    # Busy Mode -> CHEAT_SHEET
    busy_artifact = AdaptiveLearningEngine.generate_artifact(
        folder_id=folder_id,
        style=LearningStyle.VISUAL,
        mode=WorkloadMode.BUSY,
        topic="Myocardial Infarction",
        chunks=chunks
    )
    assert busy_artifact.artifact_type == StudyArtifactType.CHEAT_SHEET
    assert "mindmap" in busy_artifact.content


def test_medical_clinical_simulation_synthesis():
    folder_id = uuid4()
    chunks = [
        {"id": uuid4(), "content": "Patient triage protocol in emergency cardiology for myocardial infarction.", "cosine_similarity": 0.90}
    ]

    # Free Mode -> CLINICAL_SIMULATION
    artifact = AdaptiveLearningEngine.generate_artifact(
        folder_id=folder_id,
        style=LearningStyle.KINESTHETIC,
        mode=WorkloadMode.FREE,
        topic="Myocardial Infarction",
        chunks=chunks
    )

    assert artifact.artifact_type == StudyArtifactType.CLINICAL_SIMULATION
    sim: KinestheticSimulationPayload = artifact.metadata.simulation_payload
    assert sim is not None
    assert sim.kinesthetic_type == "clinical_simulation"
    assert sim.academic_discipline == AcademicDiscipline.MEDICINE
    assert len(sim.steps) == 3
    assert sim.steps[0].title == "Stage 1: Presentation & Triage"
    assert sim.steps[0].vitals_or_state is not None
    assert "BP" in sim.steps[0].vitals_or_state
    assert any(choice.is_optimal for choice in sim.steps[0].choices)
    assert any(choice.vital_impact is not None for choice in sim.steps[0].choices)

    # Busy Mode -> CRITICAL_DECISION
    busy_artifact = AdaptiveLearningEngine.generate_artifact(
        folder_id=folder_id,
        style=LearningStyle.KINESTHETIC,
        mode=WorkloadMode.BUSY,
        topic="Myocardial Infarction",
        chunks=chunks
    )
    assert busy_artifact.artifact_type == StudyArtifactType.CRITICAL_DECISION
    busy_sim: KinestheticSimulationPayload = busy_artifact.metadata.simulation_payload
    assert busy_sim.kinesthetic_type == "critical_decision"
    assert len(busy_sim.steps) == 1


def test_life_sciences_procedural_sequencing_synthesis():
    folder_id = uuid4()
    chunks = [
        {"id": uuid4(), "content": "Enzyme kinetics in glycolysis pathway with rate limiting metabolic reaction.", "cosine_similarity": 0.85}
    ]

    artifact = AdaptiveLearningEngine.generate_artifact(
        folder_id=folder_id,
        style=LearningStyle.KINESTHETIC,
        mode=WorkloadMode.FREE,
        topic="Glycolysis Pathway",
        chunks=chunks
    )

    assert artifact.artifact_type == StudyArtifactType.PROCEDURAL_SEQUENCING
    sim: KinestheticSimulationPayload = artifact.metadata.simulation_payload
    assert sim.kinesthetic_type == "procedural_sequencing"
    assert sim.academic_discipline == AcademicDiscipline.LIFE_SCIENCES
    assert len(sim.sequencing_items) >= 4
    assert [item.correct_order for item in sim.sequencing_items] == [1, 2, 3, 4]


def test_cs_code_lab_backward_compatibility():
    folder_id = uuid4()
    chunks = [
        {"id": uuid4(), "content": "Implementation of recursive binary search algorithm in python with time complexity bounds.", "cosine_similarity": 0.92}
    ]

    artifact = AdaptiveLearningEngine.generate_artifact(
        folder_id=folder_id,
        style=LearningStyle.KINESTHETIC,
        mode=WorkloadMode.FREE,
        topic="Binary Search",
        chunks=chunks
    )

    assert artifact.artifact_type == StudyArtifactType.CODE_LAB
    assert artifact.metadata.programming_language == "python"
    assert artifact.metadata.simulation_payload.kinesthetic_type == "code_sandbox"
    assert "def " in artifact.content
    assert "binary_search" in artifact.content.lower()
