import io
from uuid import uuid4
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.services.database import db_service


def test_complete_course_folder_document_e2e():
    """End-to-end integration test verifying course, folder nesting, and document chunking flow."""
    client = TestClient(app)
    user_id = str(uuid4())
    course_id = str(uuid4())
    root_folder_id = str(uuid4())
    subfolder_id = str(uuid4())
    doc_id = str(uuid4())

    # Simulated in-memory database store for clean offline integration testing
    courses_store = []
    folders_store = []
    docs_store = []
    chunks_store = []

    def mock_create_course(user_id, name, code, term=None, color=None, description=None):
        c = {"id": course_id, "user_id": str(user_id), "name": name, "code": code, "term": term, "color": color, "description": description}
        courses_store.append(c)
        return c

    def mock_get_courses(user_id):
        return [c for c in courses_store if c["user_id"] == str(user_id)]

    def mock_create_folder(user_id, course_id, name, parent_id=None, parent_path="", parent_depth=0):
        fid = root_folder_id if parent_depth == 0 else subfolder_id
        path = f"{parent_path}/{name}" if parent_path else f"/{name}"
        f = {
            "id": fid,
            "user_id": str(user_id),
            "course_id": str(course_id),
            "name": name,
            "parent_id": str(parent_id) if parent_id else None,
            "materialized_path": path,
            "depth": parent_depth + (1 if parent_path else 0),
        }
        folders_store.append(f)
        return f

    def mock_get_folders(user_id, course_id=None):
        return [f for f in folders_store if f["user_id"] == str(user_id)]

    def mock_create_doc(user_id, course_id, file_name, storage_path, file_type, folder_id=None, file_size_bytes=0, status="pending", error_message=None):
        d = {
            "id": doc_id,
            "user_id": str(user_id),
            "course_id": str(course_id),
            "folder_id": str(folder_id) if folder_id else None,
            "file_name": file_name,
            "storage_path": storage_path,
            "file_type": file_type,
            "file_size_bytes": file_size_bytes,
            "status": status,
            "error_message": error_message,
        }
        docs_store.append(d)
        return d

    def mock_get_docs(user_id, folder_id=None, course_id=None):
        res = [d for d in docs_store if d["user_id"] == str(user_id)]
        if folder_id:
            res = [d for d in res if d["folder_id"] == str(folder_id)]
        return res

    def mock_create_chunks(chunks):
        chunks_store.extend(chunks)
        return chunks

    def mock_update_status(did, status, error_message=None):
        for d in docs_store:
            if d["id"] == str(did):
                d["status"] = status
        return None

    # Patch database service methods
    db_service.create_course = mock_create_course
    db_service.get_courses = mock_get_courses
    db_service.create_virtual_folder = mock_create_folder
    db_service.get_virtual_folders = mock_get_folders
    db_service.create_document = mock_create_doc
    db_service.get_documents = mock_get_docs
    db_service.create_document_chunks = mock_create_chunks
    db_service.update_document_status = mock_update_status

    headers = {"X-Test-User-Id": user_id}

    # Step 1: Create Course
    res_c = client.post(
        "/api/v1/courses",
        json={"name": "Distributed Systems", "code": "CS301", "term": "Fall 2026"},
        headers=headers,
    )
    assert res_c.status_code == 201
    assert res_c.json()["code"] == "CS301"

    # Step 2: Create Subfolder (e.g. Week 1)
    res_f = client.post(
        "/api/v1/folders",
        json={
            "course_id": course_id,
            "name": "Week_01_Raft",
            "parent_id": root_folder_id,
            "parent_path": "/CS301",
            "parent_depth": 0,
        },
        headers=headers,
    )
    assert res_f.status_code == 200
    assert res_f.json()["materialized_path"] == "/CS301/Week_01_Raft"

    # Step 3: Upload Document into Subfolder
    sample_notes = (
        b"Raft Consensus Protocol.\n"
        b"Leader election occurs when followers do not receive heartbeat AppendEntries RPCs.\n"
        b"A candidate requests votes from all peers and becomes leader upon majority quorum.\n"
    )
    res_up = client.post(
        "/api/v1/documents/upload",
        data={"course_id": course_id, "folder_id": subfolder_id},
        files={"file": ("raft_summary.txt", io.BytesIO(sample_notes), "text/plain")},
        headers=headers,
    )
    assert res_up.status_code == 201
    doc_res = res_up.json()
    assert doc_res["file_name"] == "raft_summary.txt"
    assert doc_res["status"] == "indexed"
    assert doc_res["chunks_created"] >= 1

    # Step 4: List Documents in Subfolder
    res_docs = client.get(
        f"/api/v1/documents?folder_id={subfolder_id}",
        headers=headers,
    )
    assert res_docs.status_code == 200
    retrieved = res_docs.json()
    assert len(retrieved) == 1
    assert retrieved[0]["file_name"] == "raft_summary.txt"

    # Step 5: Check chunks created with vector embeddings
    assert len(chunks_store) >= 1
    assert len(chunks_store[0]["embedding"]) == 1536
    assert chunks_store[0]["folder_id"] == subfolder_id
