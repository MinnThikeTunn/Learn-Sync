import threading
import time
from uuid import uuid4

from backend.app.core.config import settings
from backend.app.core.distributed import DistributedInfrastructure
from backend.app.core.events import EventPublisher
from backend.app.core.task_queue import queue_document_processing


def test_distributed_cache_round_trip_and_ttl_fallback(monkeypatch):
    monkeypatch.setattr(settings, "REDIS_URL", None)
    infrastructure = DistributedInfrastructure()
    key = infrastructure.cache_key("artifact", "recursion", "visual")

    infrastructure.cache_set(key, {"content": "cached"}, ttl_seconds=1)
    assert infrastructure.cache_get(key) == {"content": "cached"}

    time.sleep(1.05)
    assert infrastructure.cache_get(key) is None


def test_distributed_lock_serializes_concurrent_workers(monkeypatch):
    monkeypatch.setattr(settings, "REDIS_URL", None)
    infrastructure = DistributedInfrastructure()
    active = 0
    max_active = 0
    guard = threading.Lock()

    def worker():
        nonlocal active, max_active
        with infrastructure.lock("same-card") as acquired:
            assert acquired
            with guard:
                active += 1
                max_active = max(max_active, active)
            time.sleep(0.02)
            with guard:
                active -= 1

    threads = [threading.Thread(target=worker) for _ in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    assert max_active == 1


def test_distributed_rate_limit_returns_429_equivalent(monkeypatch):
    monkeypatch.setattr(settings, "REDIS_URL", None)
    infrastructure = DistributedInfrastructure()
    assert infrastructure.allow("user-1", limit=2, window_seconds=60)
    assert infrastructure.allow("user-1", limit=2, window_seconds=60)
    assert not infrastructure.allow("user-1", limit=2, window_seconds=60)


def test_learning_event_contains_replayable_event_id(monkeypatch):
    publisher = EventPublisher(rabbitmq_url="amqp://unused")
    published = []
    monkeypatch.setattr(publisher, "_publish", lambda routing_key, payload: published.append(payload) or True)
    assert publisher.publish_learning_event("flashcard.reviewed", {"user_id": str(uuid4())})
    assert published[0]["event_type"] == "flashcard.reviewed"
    assert published[0]["event_id"]
    assert published[0]["occurred_at"]


def test_document_queue_is_safe_when_async_mode_is_disabled(monkeypatch):
    monkeypatch.setattr(settings, "ASYNC_DOCUMENT_PROCESSING", False)
    assert queue_document_processing(
        user_id=uuid4(),
        course_id=uuid4(),
        folder_id=None,
        file_name="notes.txt",
        file_bytes=b"notes",
        mime_type="text/plain",
    ) is None
