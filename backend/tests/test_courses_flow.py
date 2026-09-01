import pytest
from uuid import uuid4
from fastapi.testclient import TestClient
from unittest.mock import patch
from backend.app.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_create_and_get_courses(client):
    user_id = str(uuid4())
    course_data = {
        "name": "Distributed Systems",
        "code": "CS301",
        "term": "Fall 2026",
        "color": "#3b82f6",
        "description": "Consensus, replication, and fault tolerance."
    }

    mock_course = {
        "id": str(uuid4()),
        "user_id": user_id,
        "name": "Distributed Systems",
        "code": "CS301",
        "term": "Fall 2026",
        "color": "#3b82f6",
        "description": "Consensus, replication, and fault tolerance.",
        "created_at": "2026-09-01T00:00:00Z"
    }

    with patch("backend.app.services.database.db_service.create_course") as mock_create, \
         patch("backend.app.services.database.db_service.get_courses") as mock_get:
        mock_create.return_value = mock_course
        mock_get.return_value = [mock_course]

        # 1. Test POST /api/v1/courses
        res_post = client.post(
            "/api/v1/courses",
            json=course_data,
            headers={"X-Test-User-Id": user_id}
        )
        assert res_post.status_code == 201
        assert res_post.json()["code"] == "CS301"

        # 2. Test GET /api/v1/courses
        res_get = client.get(
            "/api/v1/courses",
            headers={"X-Test-User-Id": user_id}
        )
        assert res_get.status_code == 200
        data = res_get.json()
        assert len(data) == 1
        assert data[0]["name"] == "Distributed Systems"


def test_delete_course_flow(client):
    user_id = str(uuid4())
    course_id = str(uuid4())

    with patch("backend.app.services.database.db_service.delete_course") as mock_delete:
        mock_delete.return_value = True

        res = client.delete(
            f"/api/v1/courses/{course_id}",
            headers={"X-Test-User-Id": user_id},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "deleted"
        assert data["id"] == course_id
        mock_delete.assert_called_once()
