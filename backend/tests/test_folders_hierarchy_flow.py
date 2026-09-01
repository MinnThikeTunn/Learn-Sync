import pytest
from uuid import uuid4
from fastapi.testclient import TestClient
from unittest.mock import patch
from backend.app.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_create_and_nest_subfolder(client):
    user_id = str(uuid4())
    course_id = str(uuid4())
    root_folder_id = str(uuid4())

    root_folder = {
        "id": root_folder_id,
        "user_id": user_id,
        "course_id": course_id,
        "name": "CS101",
        "materialized_path": "/CS101",
        "depth": 0,
        "parent_id": None,
    }

    subfolder = {
        "id": str(uuid4()),
        "user_id": user_id,
        "course_id": course_id,
        "name": "Week_01_Recursion",
        "materialized_path": "/CS101/Week_01_Recursion",
        "depth": 1,
        "parent_id": root_folder_id,
    }

    with patch("backend.app.services.database.db_service.create_virtual_folder") as mock_create, \
         patch("backend.app.services.database.db_service.get_virtual_folders") as mock_get:
        mock_create.return_value = subfolder
        mock_get.return_value = [root_folder, subfolder]

        # 1. Create subfolder with JSON payload
        res = client.post(
            "/api/v1/folders",
            json={
                "course_id": course_id,
                "name": "Week_01_Recursion",
                "parent_id": root_folder_id,
                "parent_path": "/CS101",
                "parent_depth": 0,
            },
            headers={"X-Test-User-Id": user_id},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["materialized_path"] == "/CS101/Week_01_Recursion"
        assert data["depth"] == 1

        # 2. Get tree
        res_tree = client.get(
            f"/api/v1/folders/tree?course_id={course_id}",
            headers={"X-Test-User-Id": user_id},
        )
        assert res_tree.status_code == 200
        tree_data = res_tree.json()
        assert len(tree_data) == 2


def test_delete_folder_flow(client):
    user_id = str(uuid4())
    folder_id = str(uuid4())

    with patch("backend.app.services.database.db_service.delete_virtual_folder") as mock_delete:
        mock_delete.return_value = True

        res = client.delete(
            f"/api/v1/folders/{folder_id}",
            headers={"X-Test-User-Id": user_id},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "deleted"
        assert data["id"] == folder_id
        mock_delete.assert_called_once()
