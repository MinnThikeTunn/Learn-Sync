import uuid
import pytest
from backend.app.schemas.adaptive import (
    LearningStyle,
    StudyArtifactType,
)
from backend.app.schemas.workload import WorkloadMode
from backend.app.services.rag import AdaptiveLearningEngine


@pytest.fixture
def mock_chunks():
    f_id = uuid.uuid4()
    return [
        {
            "id": uuid.uuid4(),
            "document_id": uuid.uuid4(),
            "folder_id": f_id,
            "content": "Recursion relies on a call stack where each recursive call places a frame on memory.",
            "cosine_similarity": 0.92,
            "rrf_score": 0.032
        },
        {
            "id": uuid.uuid4(),
            "document_id": uuid.uuid4(),
            "folder_id": f_id,
            "content": "Base case condition terminates the recursion tree and prevents stack overflow errors.",
            "cosine_similarity": 0.88,
            "rrf_score": 0.029
        }
    ]


def test_visual_free_mode_generates_mermaid_diagram(mock_chunks):
    folder_id = uuid.uuid4()
    artifact = AdaptiveLearningEngine.generate_artifact(
        folder_id=folder_id,
        style=LearningStyle.VISUAL,
        mode=WorkloadMode.FREE,
        topic="Recursion",
        chunks=mock_chunks
    )

    assert artifact.artifact_type == StudyArtifactType.DIAGRAM
    assert artifact.metadata.diagram_syntax == "mermaid"
    assert "flowchart" in artifact.content
    assert artifact.confidence_score >= 0.80
    assert len(artifact.citations) == 2


def test_visual_busy_mode_generates_cheat_sheet(mock_chunks):
    folder_id = uuid.uuid4()
    artifact = AdaptiveLearningEngine.generate_artifact(
        folder_id=folder_id,
        style=LearningStyle.VISUAL,
        mode=WorkloadMode.BUSY,
        topic="Recursion",
        chunks=mock_chunks
    )

    assert artifact.artifact_type == StudyArtifactType.CHEAT_SHEET
    assert artifact.metadata.diagram_syntax == "mermaid"
    assert "graph LR" in artifact.content
    assert artifact.metadata.estimated_time_minutes <= 3.0


def test_auditory_free_mode_generates_socratic_script(mock_chunks):
    folder_id = uuid.uuid4()
    artifact = AdaptiveLearningEngine.generate_artifact(
        folder_id=folder_id,
        style=LearningStyle.AUDITORY,
        mode=WorkloadMode.FREE,
        topic="Recursion",
        chunks=mock_chunks
    )

    assert artifact.artifact_type == StudyArtifactType.AUDIO_SCRIPT
    assert len(artifact.metadata.speakers) >= 2
    assert "Professor" in artifact.metadata.speakers
    assert artifact.metadata.audio_duration_seconds >= 120


def test_auditory_busy_mode_generates_micro_recap(mock_chunks):
    folder_id = uuid.uuid4()
    artifact = AdaptiveLearningEngine.generate_artifact(
        folder_id=folder_id,
        style=LearningStyle.AUDITORY,
        mode=WorkloadMode.BUSY,
        topic="Recursion",
        chunks=mock_chunks
    )

    assert artifact.artifact_type == StudyArtifactType.MICRO_RECAP
    assert artifact.metadata.audio_duration_seconds == 30
    assert "Rapid Recap" in artifact.content


def test_read_write_free_mode_generates_comprehensive_notes(mock_chunks):
    folder_id = uuid.uuid4()
    artifact = AdaptiveLearningEngine.generate_artifact(
        folder_id=folder_id,
        style=LearningStyle.READ_WRITE,
        mode=WorkloadMode.FREE,
        topic="Recursion",
        chunks=mock_chunks
    )

    assert artifact.artifact_type == StudyArtifactType.SUMMARY_NOTE
    assert "# Comprehensive Study Guide" in artifact.content
    assert artifact.metadata.estimated_time_minutes >= 5.0


def test_read_write_busy_mode_generates_three_bullet_takeaways(mock_chunks):
    folder_id = uuid.uuid4()
    artifact = AdaptiveLearningEngine.generate_artifact(
        folder_id=folder_id,
        style=LearningStyle.READ_WRITE,
        mode=WorkloadMode.BUSY,
        topic="Recursion",
        chunks=mock_chunks
    )

    assert artifact.artifact_type == StudyArtifactType.SUMMARY_NOTE
    assert "3-Bullet Pareto Takeaways" in artifact.content
    assert "•" in artifact.content


def test_kinesthetic_free_mode_generates_code_lab(mock_chunks):
    folder_id = uuid.uuid4()
    artifact = AdaptiveLearningEngine.generate_artifact(
        folder_id=folder_id,
        style=LearningStyle.KINESTHETIC,
        mode=WorkloadMode.FREE,
        topic="Recursion",
        chunks=mock_chunks
    )

    assert artifact.artifact_type == StudyArtifactType.CODE_LAB
    assert artifact.metadata.programming_language == "python"
    assert len(artifact.metadata.test_cases) > 0
    assert "def solve_recursion" in artifact.content


def test_kinesthetic_busy_mode_generates_micro_snippet(mock_chunks):
    folder_id = uuid.uuid4()
    artifact = AdaptiveLearningEngine.generate_artifact(
        folder_id=folder_id,
        style=LearningStyle.KINESTHETIC,
        mode=WorkloadMode.BUSY,
        topic="Recursion",
        chunks=mock_chunks
    )

    assert artifact.artifact_type == StudyArtifactType.MICRO_SNIPPET
    assert artifact.metadata.estimated_time_minutes <= 2.0
    assert "Micro-Snippet Fix" in artifact.content


def test_empty_chunks_triggers_low_confidence():
    folder_id = uuid.uuid4()
    artifact = AdaptiveLearningEngine.generate_artifact(
        folder_id=folder_id,
        style=LearningStyle.VISUAL,
        mode=WorkloadMode.FREE,
        topic="Quantum Computing",
        chunks=[]
    )

    assert artifact.is_low_confidence is True
    assert artifact.confidence_score == 0.0
    assert artifact.warning_message is not None
    assert len(artifact.citations) == 0
