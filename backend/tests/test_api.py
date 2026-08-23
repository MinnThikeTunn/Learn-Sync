import uuid
import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timezone

from backend.app.main import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_workload_evaluate_endpoint():
    user_id = str(uuid.uuid4())
    payload = {
        "user_id": user_id,
        "events": [
            {
                "user_id": user_id,
                "title": "Algorithms Exam",
                "event_type": "exam",
                "start_time": "2026-09-02T10:00:00Z",
            }
        ],
        "reference_time": "2026-09-01T10:00:00Z",
        "previous_mode": "free",
    }
    response = client.post("/api/v1/workload/evaluate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "score" in data
    assert data["current_mode"] in ("free", "busy")


def test_artifact_generate_endpoint():
    folder_id = str(uuid.uuid4())
    user_id = str(uuid.uuid4())
    payload = {
        "folder_id": folder_id,
        "user_id": user_id,
        "topic": "Dynamic Programming",
        "learning_style": "visual",
        "workload_mode": "free",
    }
    response = client.post("/api/v1/artifacts/generate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["artifact_type"] == "diagram"
    assert "flowchart" in data["content"]


def test_bkt_update_endpoint():
    user_id = str(uuid.uuid4())
    kc_id = str(uuid.uuid4())
    payload = {
        "user_id": user_id,
        "kc_id": kc_id,
        "is_correct": True,
        "current_p_l": 0.10,
    }
    response = client.post("/api/v1/bkt/update", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["updated_p_l"] > 0.10


def test_burnout_check_endpoint():
    user_id = str(uuid.uuid4())
    payload = {
        "user_id": user_id,
        "events": [],
        "available_calendar_slots": 0,
    }
    response = client.post("/api/v1/burnout/check", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["is_burnout_risk"] is True
    assert data["micro_task"] is not None
