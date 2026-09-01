import pytest
import io
from uuid import uuid4
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from backend.app.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_document_upload_and_listing_flow(client):
    user_id = str(uuid4())
    course_id = str(uuid4())
    folder_id = str(uuid4())

    fake_file_content = b"Introduction to Distributed Consensus and the Raft Algorithm. Raft decomposes consensus into leader election, log replication, and safety."
    file_name = "raft_intro.txt"

    mock_doc = {
        "id": str(uuid4()),
        "user_id": user_id,
        "course_id": course_id,
        "folder_id": folder_id,
        "file_name": file_name,
        "storage_path": f"{user_id}/{course_id}/{folder_id}/{file_name}",
        "file_type": "text/plain",
        "file_size_bytes": len(fake_file_content),
        "status": "indexed",
        "error_message": None,
        "created_at": "2026-09-01T00:00:00Z",
    }

    with patch("backend.app.services.document_processor.document_service.process_and_store_document") as mock_process, \
         patch("backend.app.services.database.db_service.get_documents") as mock_get_docs:
        mock_process.return_value = (mock_doc, 1)  # (doc, chunk_count)
        mock_get_docs.return_value = [mock_doc]

        # 1. Upload document
        res_upload = client.post(
            "/api/v1/documents/upload",
            data={"course_id": course_id, "folder_id": folder_id},
            files={"file": (file_name, io.BytesIO(fake_file_content), "text/plain")},
            headers={"X-Test-User-Id": user_id},
        )
        assert res_upload.status_code == 201
        data = res_upload.json()
        assert data["file_name"] == file_name
        assert data["status"] == "indexed"
        assert data["chunks_created"] == 1

        # 2. Get documents in folder
        res_list = client.get(
            f"/api/v1/documents?folder_id={folder_id}&course_id={course_id}",
            headers={"X-Test-User-Id": user_id},
        )
        assert res_list.status_code == 200
        docs = res_list.json()
        assert len(docs) == 1
        assert docs[0]["file_name"] == file_name


def test_delete_document_flow(client):
    user_id = str(uuid4())
    doc_id = str(uuid4())

    with patch("backend.app.services.database.db_service.delete_document") as mock_delete:
        mock_delete.return_value = True

        res = client.delete(
            f"/api/v1/documents/{doc_id}",
            headers={"X-Test-User-Id": user_id},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "deleted"
        assert data["id"] == doc_id
        mock_delete.assert_called_once()
