import io
import pytest
from uuid import uuid4
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from backend.app.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_get_document_content_and_reading_metadata(client):
    user_id = str(uuid4())
    doc_id = str(uuid4())
    course_id = str(uuid4())
    folder_id = str(uuid4())

    mock_doc = {
        "id": doc_id,
        "user_id": user_id,
        "course_id": course_id,
        "folder_id": folder_id,
        "file_name": "distributed_systems_lecture1.pdf",
        "storage_path": f"{user_id}/{course_id}/{folder_id}/distributed_systems_lecture1.pdf",
        "file_type": "application/pdf",
        "file_size_bytes": 204800,
        "status": "indexed",
        "error_message": None,
        "created_at": "2026-09-01T00:00:00Z",
    }

    mock_chunks = [
        {
            "id": str(uuid4()),
            "document_id": doc_id,
            "chunk_index": 0,
            "content": "Chapter 1: System Models and Assumptions. Synchronous vs Asynchronous distributed environments.",
            "token_count": 14,
        },
        {
            "id": str(uuid4()),
            "document_id": doc_id,
            "chunk_index": 1,
            "content": "Chapter 2: Failure Detectors and Heartbeats. Crash-stop vs Byzantine failure modes.",
            "token_count": 13,
        }
    ]

    with patch("backend.app.services.database.db_service.get_document") as mock_get_doc, \
         patch("backend.app.services.database.db_service.get_all_document_chunks") as mock_get_chunks, \
         patch("backend.app.services.database.db_service.get_document_signed_url") as mock_get_signed_url:
        
        mock_get_doc.return_value = mock_doc
        mock_get_chunks.return_value = mock_chunks
        mock_get_signed_url.return_value = "https://mock-supabase.co/storage/v1/object/sign/documents/mock.pdf"

        res = client.get(
            f"/api/v1/documents/{doc_id}/content",
            headers={"X-Test-User-Id": user_id},
        )

        assert res.status_code == 200
        data = res.json()
        assert data["id"] == doc_id
        assert data["file_name"] == "distributed_systems_lecture1.pdf"
        assert data["file_type"] == "application/pdf"
        assert data["total_chunks"] == 2
        assert "Chapter 1" in data["full_text"]
        assert "Chapter 2" in data["full_text"]
        assert len(data["chunks"]) == 2
        assert data["total_words"] > 0
        assert data["estimated_read_time_minutes"] >= 1
        assert data["signed_url"] == "https://mock-supabase.co/storage/v1/object/sign/documents/mock.pdf"
        assert f"/api/v1/documents/{doc_id}/raw" in data["raw_url"]


def test_get_document_raw_streaming_from_storage(client):
    user_id = str(uuid4())
    doc_id = str(uuid4())

    mock_doc = {
        "id": doc_id,
        "user_id": user_id,
        "file_name": "lecture_notes.pdf",
        "storage_path": f"{user_id}/course/lecture_notes.pdf",
        "file_type": "application/pdf",
        "file_size_bytes": 14,
        "status": "indexed",
    }
    fake_pdf_bytes = b"%PDF-1.4 mock content"

    with patch("backend.app.services.database.db_service.get_document") as mock_get_doc, \
         patch("backend.app.services.database.db_service.download_document_bytes") as mock_download:
        
        mock_get_doc.return_value = mock_doc
        mock_download.return_value = fake_pdf_bytes

        res = client.get(
            f"/api/v1/documents/{doc_id}/raw",
            headers={"X-Test-User-Id": user_id},
        )

        assert res.status_code == 200
        assert res.content == fake_pdf_bytes
        assert "application/pdf" in res.headers["content-type"]
        assert "inline" in res.headers["content-disposition"]


def test_get_document_content_not_found(client):
    user_id = str(uuid4())
    doc_id = str(uuid4())

    with patch("backend.app.services.database.db_service.get_document") as mock_get_doc:
        mock_get_doc.return_value = None

        res = client.get(
            f"/api/v1/documents/{doc_id}/content",
            headers={"X-Test-User-Id": user_id},
        )
        assert res.status_code == 404
