import pytest
from uuid import uuid4
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_post_event_and_evaluate_cockpit():
    """TDD test: POST /api/v1/events creates an event and reflects in live workload."""
    test_user_id = "00000000-0000-0000-0000-000000000001"
    headers = {"X-Test-User-Id": test_user_id}
    now = datetime.now(timezone.utc)
    
    event_payload = {
        "title": "CS401 Distributed Systems Final",
        "event_type": "exam",
        "start_time": (now + timedelta(days=1.5)).isoformat(),
        "weight": 3.0,
        "source": "manual",
    }
    
    # 1. Create event via POST /api/v1/events
    response = client.post("/api/v1/events", json=event_payload, headers=headers)
    assert response.status_code == 201, f"Expected 201 Created, got {response.status_code}: {response.text}"
    created_event = response.json()
    assert created_event["title"] == "CS401 Distributed Systems Final"
    assert created_event["weight"] == 3.0
    event_id = created_event["id"]
    
    # 2. Verify live workload recomputes with lookahead
    workload_res = client.get("/api/v1/workload/live?days_ahead=3", headers=headers)
    assert workload_res.status_code == 200
    wl_data = workload_res.json()
    assert wl_data["active_event_count"] >= 1
    assert wl_data["score"] > 0.0
    
    # 3. Delete event via DELETE /api/v1/events/{id}
    del_res = client.delete(f"/api/v1/events/{event_id}", headers=headers)
    assert del_res.status_code == 200


def test_seed_demo_events_endpoint():
    """TDD test: POST /api/v1/events/seed-demo triggers immediate workload recomputation."""
    test_user_id = "00000000-0000-0000-0000-000000000001"
    headers = {"X-Test-User-Id": test_user_id}
    
    res = client.post("/api/v1/events/seed-demo?scenario=busy", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["scenario"] == "busy"
    assert data["seeded_count"] >= 1
    assert data["workload"]["score"] > 0.55


def test_toggle_event_complete_endpoint():
    """TDD test: PATCH /api/v1/events/{id}/complete toggles completion state."""
    test_user_id = "00000000-0000-0000-0000-000000000001"
    headers = {"X-Test-User-Id": test_user_id}
    now = datetime.now(timezone.utc)
    
    # 1. Create event
    create_res = client.post("/api/v1/events", json={
        "title": "Temporary Assignment",
        "event_type": "assignment",
        "start_time": (now + timedelta(days=2.0)).isoformat(),
        "weight": 1.5,
    }, headers=headers)
    assert create_res.status_code == 201
    evt_id = create_res.json()["id"]
    
    # 2. Mark complete
    patch_res = client.patch(f"/api/v1/events/{evt_id}/complete?is_completed=true", headers=headers)
    assert patch_res.status_code == 200
    assert patch_res.json()["is_completed"] is True
    
    # 3. Clean up
    del_res = client.delete(f"/api/v1/events/{evt_id}", headers=headers)
    assert del_res.status_code == 200

