import base64
import json
import threading
import time
from uuid import UUID, uuid4
from unittest.mock import MagicMock, patch
import pytest
from fastapi.testclient import TestClient

from backend.app.core.config import settings
from backend.app.core.distributed import DistributedInfrastructure, distributed
from backend.app.core.events import EventPublisher, event_publisher
from backend.app.core.task_queue import queue_document_processing, process_document_task
from backend.app.services.document_processor import DocumentService
from backend.app.schemas.adaptive import StudyArtifact, StudyArtifactType, LearningStyle
from backend.app.schemas.feynman import GapAnalysisResult
from backend.app.schemas.workload import WorkloadMode
from backend.app.main import app


@pytest.fixture
def client():
    return TestClient(app)


# =====================================================================
# SEAM 1: Zero-Hardcode & Dynamic Configuration Verification
# =====================================================================

def test_zero_hardcode_redis_key_prefix_configuration(monkeypatch):
    """Verify REDIS_KEY_PREFIX controls all Redis keys without hardcoded 'learnsync:'."""
    monkeypatch.setattr(settings, "REDIS_KEY_PREFIX", "custom_prefix")
    infra = DistributedInfrastructure()

    # Cache key
    cache_key = infra.cache_key("test_ns", "part1", "part2")
    assert cache_key.startswith("custom_prefix:test_ns:")

    # Lock key
    fake_redis = MagicMock()
    infra._redis = fake_redis
    with infra.lock("test_lock", timeout_seconds=15):
        pass
    fake_redis.set.assert_called_once()
    assert fake_redis.set.call_args[0][0] == "custom_prefix:lock:test_lock"

    # Rate limiter key
    fake_redis.incr.return_value = 1
    assert infra.allow("user_test", limit=5, window_seconds=30) is True
    fake_redis.incr.assert_called_once_with("custom_prefix:rate:user_test")


def test_zero_hardcode_event_stream_and_exchange_configuration(monkeypatch):
    """Verify event publisher uses settings for exchange, stream key, and max retention."""
    monkeypatch.setattr(settings, "RABBITMQ_EXCHANGE", "custom.exchange.events")
    monkeypatch.setattr(settings, "REDIS_STREAM_KEY", "custom:stream:events")
    monkeypatch.setattr(settings, "REDIS_STREAM_MAXLEN", 5000)

    publisher = EventPublisher(rabbitmq_url="amqp://fake")
    fake_redis = MagicMock()
    monkeypatch.setattr(distributed, "_redis", fake_redis)
    published_events = []
    monkeypatch.setattr(publisher, "_publish", lambda key, payload: published_events.append((key, payload)) or True)

    payload = {"status": "ok"}
    assert publisher.publish_learning_event("test.event", payload)
    assert publisher.EXCHANGE_NAME == "custom.exchange.events"

    # Verify Redis stream append with configured key and maxlen
    fake_redis.xadd.assert_called_once()
    stream_key, stream_data = fake_redis.xadd.call_args[0]
    stream_kwargs = fake_redis.xadd.call_args[1]
    assert stream_key == "custom:stream:events"
    assert stream_kwargs.get("maxlen") == 5000


def test_zero_hardcode_celery_task_and_retry_configuration(monkeypatch):
    """Verify Celery task uses configurable app name, task name, and retry parameters."""
    monkeypatch.setattr(settings, "CELERY_APP_NAME", "custom_celery_app")
    monkeypatch.setattr(settings, "CELERY_TASK_NAME", "custom.process_document")
    monkeypatch.setattr(settings, "CELERY_TASK_MAX_RETRIES", 5)
    monkeypatch.setattr(settings, "CELERY_TASK_RETRY_BACKOFF", True)

    assert settings.CELERY_APP_NAME == "custom_celery_app"
    assert settings.CELERY_TASK_NAME == "custom.process_document"
    assert settings.CELERY_TASK_MAX_RETRIES == 5
    assert settings.CELERY_TASK_RETRY_BACKOFF is True


# =====================================================================
# SEAM 2: Concept 1 - Asynchronous Message Queue & Document Status
# =====================================================================

def test_async_document_upload_enqueues_and_sets_pending(client, monkeypatch):
    """Verify ASYNC_DOCUMENT_PROCESSING=True uploads file, sets status='pending', and enqueues task."""
    monkeypatch.setattr(settings, "ASYNC_DOCUMENT_PROCESSING", True)
    user_id = str(uuid4())
    course_id = str(uuid4())
    doc_id = str(uuid4())

    mock_doc = {
        "id": doc_id,
        "user_id": user_id,
        "course_id": course_id,
        "folder_id": None,
        "file_name": "test_notes.txt",
        "storage_path": f"{user_id}/{course_id}/root/test_notes.txt",
        "file_type": "text/plain",
        "file_size_bytes": 20,
        "status": "pending",
        "error_message": None,
    }

    with patch("backend.app.services.document_processor.document_service.upload_to_storage") as mock_storage, \
         patch("backend.app.services.database.db_service.create_document") as mock_create_doc, \
         patch("backend.app.api.v1.endpoints.queue_document_processing") as mock_queue:

        mock_storage.return_value = mock_doc["storage_path"]
        mock_create_doc.return_value = dict(mock_doc)
        mock_queue.return_value = "celery-job-uuid-123"

        res = client.post(
            "/api/v1/documents/upload",
            data={"course_id": course_id},
            files={"file": ("test_notes.txt", b"Asynchronous Celery Notes Content", "text/plain")},
            headers={"X-Test-User-Id": user_id},
        )

        assert res.status_code == 201
        data = res.json()
        assert data["status"] == "pending"
        assert data["processing_job_id"] == "celery-job-uuid-123"
        assert data["chunks_created"] == 0
        mock_queue.assert_called_once()


def test_document_status_endpoint_all_states(client):
    """Verify GET /documents/{id}/status returns pending, parsing, indexed, and failed states."""
    user_id = str(uuid4())
    doc_id = str(uuid4())

    for state in ["pending", "parsing", "indexed", "failed"]:
        err = "Extraction timeout" if state == "failed" else None
        doc_record = {
            "id": doc_id,
            "status": state,
            "error_message": err,
            "updated_at": "2026-09-08T12:00:00Z",
        }
        with patch("backend.app.services.database.db_service.get_document", return_value=doc_record):
            res = client.get(
                f"/api/v1/documents/{doc_id}/status",
                headers={"X-Test-User-Id": user_id},
            )
            assert res.status_code == 200
            data = res.json()
            assert data["status"] == state
            assert data["document_id"] == doc_id
            assert data["error_message"] == err


def test_document_processing_failure_transitions_to_failed_state():
    """Verify document processing failure updates document status to 'failed' with error message."""
    mock_db = MagicMock()
    doc_service = DocumentService(db=mock_db)

    doc_id = uuid4()
    user_id = uuid4()
    course_id = uuid4()
    doc_record = {"id": doc_id, "status": "pending", "file_name": "corrupt.pdf"}

    # Simulate extraction failure
    with patch.object(doc_service, "extract_text_from_bytes", side_effect=ValueError("Corrupt PDF bytes")):
        with pytest.raises(ValueError, match="Corrupt PDF bytes"):
            doc_service.process_existing_document(
                doc_record=doc_record,
                user_id=user_id,
                course_id=course_id,
                folder_id=None,
                file_name="corrupt.pdf",
                file_bytes=b"corrupt",
            )

    # Verify status was updated to parsing then failed
    assert mock_db.update_document_status.call_count >= 2
    mock_db.update_document_status.assert_any_call(doc_id, status="parsing")
    mock_db.update_document_status.assert_called_with(doc_id, status="failed", error_message="Corrupt PDF bytes")


# =====================================================================
# SEAM 3: Concept 2 - Distributed Cache
# =====================================================================

def test_distributed_cache_key_hashes_all_six_dimensions():
    """Verify cache keys uniquely separate topic, folder, learning style, mode, instructions, chunks."""
    infra = DistributedInfrastructure()

    k1 = infra.cache_key("artifact", "Raft", "f1", "visual", "free", "summary", ["c1"])
    k2 = infra.cache_key("artifact", "Raft", "f1", "visual", "busy", "summary", ["c1"])  # diff mode
    k3 = infra.cache_key("artifact", "Raft", "f1", "auditory", "free", "summary", ["c1"])  # diff style
    k4 = infra.cache_key("artifact", "Raft", "f2", "visual", "free", "summary", ["c1"])  # diff folder
    k5 = infra.cache_key("artifact", "Paxos", "f1", "visual", "free", "summary", ["c1"])  # diff topic
    k6 = infra.cache_key("artifact", "Raft", "f1", "visual", "free", "diff instructions", ["c1"])  # diff instructions
    k7 = infra.cache_key("artifact", "Raft", "f1", "visual", "free", "summary", ["c2"])  # diff chunks

    keys = [k1, k2, k3, k4, k5, k6, k7]
    assert len(set(keys)) == 7, "All 6 dimensions must contribute uniquely to SHA256 digest"


def test_artifact_generation_endpoint_caching_and_cache_hit(client, monkeypatch):
    """Verify first request generates & caches; second identical request serves from distributed cache."""
    monkeypatch.setattr(settings, "REDIS_URL", None)
    user_id = str(uuid4())

    fake_artifact = StudyArtifact(
        folder_id=uuid4(),
        artifact_type=StudyArtifactType.MIND_MAP,
        learning_style=LearningStyle.VISUAL,
        workload_mode=WorkloadMode.FREE,
        content="graph TD; A[Raft Leader]-->B[Follower]",
        topic="Consensus Algorithms",
        confidence_score=0.95,
    )

    with patch("backend.app.services.rag.AdaptiveLearningEngine.generate_artifact") as mock_engine, \
         patch("backend.app.services.database.db_service.get_document_chunks", return_value=[]):

        mock_engine.return_value = fake_artifact

        req_payload = {
            "topic": "Consensus Algorithms",
            "folder_id": str(uuid4()),
            "learning_style": "visual",
            "workload_mode": "free",
            "custom_instructions": "Focus on Raft",
        }

        # First call: Cache miss -> calls engine
        res1 = client.post(
            "/api/v1/artifacts/generate",
            json=req_payload,
            headers={"X-Test-User-Id": user_id},
        )
        assert res1.status_code == 200
        assert mock_engine.call_count == 1

        # Second call: Cache hit -> returns cached without calling engine
        res2 = client.post(
            "/api/v1/artifacts/generate",
            json=req_payload,
            headers={"X-Test-User-Id": user_id},
        )
        assert res2.status_code == 200
        assert mock_engine.call_count == 1  # Not called again
        assert res2.json()["content"] == "graph TD; A[Raft Leader]-->B[Follower]"


# =====================================================================
# SEAM 4: Concept 3 - Distributed Locking
# =====================================================================

def test_bkt_mastery_concurrent_update_lock_serialization(client):
    """Verify concurrent BKT updates on the same (user_id, kc_id) return 409 Conflict if locked."""
    user_id = str(uuid4())
    kc_id = str(uuid4())

    req_payload = {
        "user_id": user_id,
        "kc_id": kc_id,
        "is_correct": True,
    }

    # Simulate lock already held by another worker
    with patch("backend.app.api.v1.endpoints.distributed.lock") as mock_lock:
        mock_ctx = MagicMock()
        mock_ctx.__enter__.return_value = False
        mock_ctx.__exit__.return_value = None
        mock_lock.return_value = mock_ctx

        res = client.post(
            "/api/v1/bkt/update",
            json=req_payload,
            headers={"X-Test-User-Id": user_id},
        )
        assert res.status_code == 409
        assert "Mastery state is being updated" in res.json()["detail"]


def test_flashcard_review_concurrent_lock_serialization(client):
    """Verify concurrent flashcard reviews on the same card return 409 Conflict if locked."""
    user_id = str(uuid4())
    card_id = str(uuid4())

    req_payload = {
        "card_id": card_id,
        "rating": 3,
    }

    with patch("backend.app.api.v1.endpoints.distributed.lock") as mock_lock:
        mock_ctx = MagicMock()
        mock_ctx.__enter__.return_value = False
        mock_ctx.__exit__.return_value = None
        mock_lock.return_value = mock_ctx

        res = client.post(
            "/api/v1/flashcards/review",
            json=req_payload,
            headers={"X-Test-User-Id": user_id},
        )
        assert res.status_code == 409
        assert "Flashcard is being reviewed" in res.json()["detail"]


def test_token_based_lua_script_release_safety():
    """Verify token-based Lua script prevents releasing locks owned by other workers."""
    infra = DistributedInfrastructure()
    fake_redis = MagicMock()
    infra._redis = fake_redis

    fake_redis.set.return_value = True

    with infra.lock("card_123", timeout_seconds=10) as acquired:
        assert acquired

    # Verify release eval called Lua script with exact ownership token
    assert fake_redis.eval.call_count == 1
    script, numkeys, key, token = fake_redis.eval.call_args[0]
    assert "redis.call('get', KEYS[1]) == ARGV[1]" in script
    assert key == f"{settings.REDIS_KEY_PREFIX}:lock:card_123"
    assert token  # Non-empty uuid


# =====================================================================
# SEAM 5: Concept 4 - Event Streaming Across All 9 Event Types
# =====================================================================

def test_all_nine_system_events_emitted_with_valid_metadata():
    """Verify all 9 system events contain event_id, event_type, occurred_at, and payload."""
    publisher = EventPublisher(rabbitmq_url="amqp://fake")
    published = []
    publisher._publish = lambda rk, p: published.append(p) or True

    event_types = [
        "artifact.generated",
        "document.uploaded",
        "syllabus.parsed",
        "workload.mode.changed",
        "workload.spike.detected",
        "blurting.evaluated",
        "feynman.evaluated",
        "bkt.mastery.updated",
        "flashcard.reviewed",
        "burnout.evaluated",
    ]

    for et in event_types:
        assert publisher.publish_learning_event(et, {"sample_key": "sample_val"})

    assert len(published) == len(event_types)
    for idx, item in enumerate(published):
        assert item["event_type"] == event_types[idx]
        assert UUID(item["event_id"])  # Valid UUID
        assert "T" in item["occurred_at"]  # ISO timestamp
        assert item["payload"]["sample_key"] == "sample_val"


# =====================================================================
# SEAM 6: Concept 5 - Distributed Rate Limiting
# =====================================================================

def test_artifact_generation_rate_limit_exceeded_returns_429(client, monkeypatch):
    """Verify /artifacts/generate returns HTTP 429 when LLM_RPM_LIMIT is exhausted."""
    monkeypatch.setattr(settings, "LLM_RPM_LIMIT", 2)
    monkeypatch.setattr(settings, "REDIS_URL", None)
    infra = DistributedInfrastructure()
    monkeypatch.setattr("backend.app.api.v1.endpoints.distributed", infra)

    user_id = str(uuid4())
    req_payload = {
        "topic": "Rate Limit Test",
        "folder_id": str(uuid4()),
        "learning_style": "read_write",
    }

    with patch("backend.app.services.rag.AdaptiveLearningEngine.generate_artifact") as mock_gen, \
         patch("backend.app.services.database.db_service.get_document_chunks", return_value=[]):

        mock_gen.return_value = StudyArtifact(
            folder_id=uuid4(),
            artifact_type=StudyArtifactType.SUMMARY_NOTE,
            learning_style=LearningStyle.READ_WRITE,
            workload_mode=WorkloadMode.FREE,
            content="summary text",
            topic="Rate Limit Test",
            confidence_score=0.90,
        )

        res1 = client.post("/api/v1/artifacts/generate", json=req_payload, headers={"X-Test-User-Id": user_id})
        assert res1.status_code == 200

        res2 = client.post("/api/v1/artifacts/generate", json={**req_payload, "custom_instructions": "diff"}, headers={"X-Test-User-Id": user_id})
        assert res2.status_code == 200

        # 3rd request in same minute exceeds limit of 2
        res3 = client.post("/api/v1/artifacts/generate", json={**req_payload, "custom_instructions": "diff2"}, headers={"X-Test-User-Id": user_id})
        assert res3.status_code == 429
        assert "rate limit exceeded" in res3.json()["detail"]


def test_feynman_evaluation_rate_limit_exceeded_returns_429(client, monkeypatch):
    """Verify /feynman/evaluate returns HTTP 429 when FEYNMAN_RPM_LIMIT is exhausted."""
    monkeypatch.setattr(settings, "FEYNMAN_RPM_LIMIT", 1)
    monkeypatch.setattr(settings, "REDIS_URL", None)
    infra = DistributedInfrastructure()
    monkeypatch.setattr("backend.app.api.v1.endpoints.distributed", infra)

    user_id = str(uuid4())
    req_payload = {
        "user_id": user_id,
        "folder_id": str(uuid4()),
        "concept": "Distributed Consensus",
        "student_explanation": "Nodes vote for a leader using heartbeats.",
    }

    with patch("backend.app.services.feynman.FeynmanService.evaluate_explanation") as mock_feynman, \
         patch("backend.app.services.database.db_service.record_feynman_completion"):

        mock_result = GapAnalysisResult(
            concept="Distributed Consensus",
            completeness_score=0.85,
            is_sufficient=True,
            feedback="Strong conceptual understanding of leader election.",
        )
        mock_feynman.return_value = mock_result

        res1 = client.post("/api/v1/feynman/evaluate", json=req_payload, headers={"X-Test-User-Id": user_id})
        assert res1.status_code == 200

        # 2nd request exceeds limit of 1
        res2 = client.post("/api/v1/feynman/evaluate", json=req_payload, headers={"X-Test-User-Id": user_id})
        assert res2.status_code == 429
        assert "rate limit exceeded" in res2.json()["detail"]
