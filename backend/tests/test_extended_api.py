import pytest
from uuid import uuid4
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from backend.app.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_get_folders_tree_endpoint(client):
    user_id = str(uuid4())
    with patch("backend.app.services.database.db_service.get_virtual_folders") as mock_get:
        mock_get.return_value = [
            {"id": str(uuid4()), "name": "CS101", "materialized_path": "/CS101", "depth": 0, "parent_id": None},
            {"id": str(uuid4()), "name": "Week_01", "materialized_path": "/CS101/Week_01", "depth": 1, "parent_id": "root-1"},
        ]
        response = client.get("/api/v1/folders/tree", headers={"X-Test-User-Id": user_id})
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["materialized_path"] == "/CS101"


def test_google_oauth_url_endpoint(client):
    user_id = str(uuid4())
    response = client.get("/api/v1/oauth/google/url", headers={"X-Test-User-Id": user_id})
    assert response.status_code == 200
    data = response.json()
    assert "auth_url" in data
    assert "https://accounts.google.com/o/oauth2/v2/auth" in data["auth_url"]


def test_live_workload_endpoint(client):
    user_id = str(uuid4())
    from backend.app.schemas.workload import WorkloadScoreResponse, WorkloadMode
    from datetime import datetime, timezone
    with patch("backend.app.services.workload.WorkloadEngine.evaluate_user_workload") as mock_eval:
        mock_eval.return_value = WorkloadScoreResponse(
            user_id=user_id,
            score=0.45,
            current_mode=WorkloadMode.FREE,
            transition_detected=False,
            is_spike=False,
            lookahead_days=3.0,
            active_event_count=2,
            evaluated_at=datetime.now(timezone.utc),
            raw_sum=0.45,
        )

        response = client.get("/api/v1/workload/live", headers={"X-Test-User-Id": user_id})
        assert response.status_code == 200
        assert response.json()["score"] == 0.45


def test_flashcards_queue_endpoint(client):
    user_id = str(uuid4())
    with patch("backend.app.services.database.db_service.get_due_flashcards") as mock_get:
        mock_get.return_value = [
            {"id": str(uuid4()), "front": "What is recursion?", "back": "A function calling itself"}
        ]
        response = client.get("/api/v1/flashcards/due", headers={"X-Test-User-Id": user_id})
        assert response.status_code == 200
        assert len(response.json()) == 1
