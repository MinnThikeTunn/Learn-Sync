import pytest
from uuid import uuid4
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.services.learner_assessment import (
    LearnerAssessmentAgent,
    LearnerArchetype,
    AssessmentResult,
    VARK_QUESTIONS,
)


def test_vark_questions_structure():
    """Verify that exactly 4 scenario questions exist with V, A, R, K options."""
    assert len(VARK_QUESTIONS) == 4
    for q in VARK_QUESTIONS:
        assert "id" in q
        assert "title" in q
        assert "scenario" in q
        assert "options" in q
        assert set(q["options"].keys()) == {"V", "A", "R", "K"}


def test_evaluate_unanimous_visual():
    """Verify unanimous Visual choices produce 'visual' primary with 'Visual Architect' archetype."""
    agent = LearnerAssessmentAgent()
    result = agent.evaluate_responses(["V", "V", "V", "V"])

    assert isinstance(result, AssessmentResult)
    assert result.primary_style == "visual"
    assert result.secondary_style is None
    assert result.is_multimodal is False
    assert result.archetype.name == "Visual Architect"
    assert result.scores == {"visual": 4, "auditory": 0, "read_write": 0, "kinesthetic": 0}


def test_evaluate_balanced_with_secondary():
    """Verify mixed response evaluates dominant primary and distinct secondary style."""
    agent = LearnerAssessmentAgent()
    # 2 Kinesthetic, 1 Read/Write, 1 Auditory
    result = agent.evaluate_responses(["K", "K", "R", "A"])

    assert result.primary_style == "kinesthetic"
    assert result.secondary_style in ("read_write", "auditory")
    assert result.is_multimodal is False
    assert result.archetype.name == "Pragmatic Hacker"
    assert result.scores["kinesthetic"] == 2


def test_evaluate_multimodal_tie():
    """Verify 2-2 tie triggers is_multimodal flag and resolves primary/secondary deterministically."""
    agent = LearnerAssessmentAgent()
    # 2 Visual, 2 Kinesthetic
    result = agent.evaluate_responses(["V", "K", "V", "K"])

    assert result.is_multimodal is True
    assert set([result.primary_style, result.secondary_style]) == {"visual", "kinesthetic"}
    assert result.scores["visual"] == 2
    assert result.scores["kinesthetic"] == 2


def test_evaluate_empty_or_invalid_fallback():
    """Verify invalid or empty responses gracefully fall back to default read_write/visual style."""
    agent = LearnerAssessmentAgent()
    result = agent.evaluate_responses([])

    assert result.primary_style == "read_write"
    assert result.is_multimodal is True
    assert result.archetype.name == "Analytical Scribe"


@patch("backend.app.services.database.SupabaseVectorClient")
def test_save_learning_style_in_database(mock_client_cls):
    """Verify DatabaseService persists learner assessment and profile updates to Supabase."""
    from backend.app.services.database import DatabaseService

    mock_instance = MagicMock()
    mock_table = MagicMock()
    mock_instance.client.table.return_value = mock_table
    mock_client_cls.return_value = mock_instance

    user_id = uuid4()
    mock_table.update.return_value.eq.return_value.execute.return_value.data = [{
        "id": str(user_id),
        "learning_style": "visual",
        "secondary_learning_style": "kinesthetic",
        "onboarding_completed": True,
    }]

    db = DatabaseService(supabase_client=mock_instance)
    res = db.save_learning_style_assessment(
        user_id=user_id,
        primary_style="visual",
        secondary_style="kinesthetic",
        scores={"visual": 3, "kinesthetic": 1, "auditory": 0, "read_write": 0},
    )

    assert res is not None
    assert res["learning_style"] == "visual"
    mock_table.update.assert_called_once()


def test_onboarding_assessment_api_endpoint():
    """Verify POST /api/v1/onboarding/assessment accepts responses and returns evaluated archetype."""
    client = TestClient(app)
    test_user_id = str(uuid4())

    with patch("backend.app.services.database.db_service.save_learning_style_assessment") as mock_save:
        mock_save.return_value = {
            "id": test_user_id,
            "learning_style": "visual",
            "secondary_learning_style": None,
            "onboarding_completed": True,
        }

        payload = {
            "responses": ["V", "V", "V", "V"],
        }
        res = client.post(
            "/api/v1/onboarding/assessment",
            json=payload,
            headers={"X-Test-User-Id": test_user_id},
        )

        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "success"
        assert data["assessment"]["primary_style"] == "visual"
        assert data["assessment"]["archetype"]["name"] == "Visual Architect"
        assert "recommended_artifacts" in data["assessment"]
