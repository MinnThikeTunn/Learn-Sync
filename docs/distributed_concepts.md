# Distributed Concepts Implemented in LearnSync

LearnSync now includes distributed-system infrastructure on top of its existing learning features. The user-facing learning workflow remains the same while the backend gains shared caching, concurrency protection, asynchronous processing, event delivery, and workload protection.

## 1. Asynchronous Message Queue

**Applied to:** Document upload and document parsing

**Implementation:** Celery with RabbitMQ as the broker and Redis as the result backend.

When asynchronous processing is enabled, document uploads create a `pending` document record and enqueue a `learnsync.process_document` task. A Celery worker performs extraction, chunking, embedding, and indexing in the background.

Relevant implementation:

- `backend/app/core/task_queue.py`
- `backend/app/services/document_processor.py`
- `POST /api/v1/documents/upload`
- `GET /api/v1/documents/{document_id}/status`

Document states include `pending`, `parsing`, `indexed`, and `failed`.

The syllabus preview endpoint remains synchronous because it must return staged folders and events immediately. Converting that endpoint to asynchronous processing would require a frontend polling workflow.

**Limitation:** Syllabus preview remains synchronous because it must immediately return staged folders and events.

## 2. Distributed Cache

**Applied to:** Study artifact generation

**Implementation:** Redis cache with TTL expiration.

Artifact cache keys include the topic, folder, learning style, workload mode, instructions, and source chunks. This prevents stale or incorrectly shared artifacts. When Redis is unavailable, a process-local fallback is used for development.

Relevant implementation:

- `backend/app/core/distributed.py`
- `POST /api/v1/artifacts/generate`
- `ARTIFACT_CACHE_TTL_SECONDS`

## 3. Distributed Locking

**Applied to:** BKT mastery updates and flashcard reviews

**Implementation:** Redis ownership locks with expiration and safe token-based release.

The lock prevents two API instances from simultaneously updating the same flashcard or knowledge-component mastery state. BKT state is also persisted using the Supabase uniqueness constraint on `(user_id, kc_id)`.

Relevant implementation:

- `backend/app/core/distributed.py`
- `backend/app/services/database.py`
- `POST /api/v1/bkt/update`
- `POST /api/v1/flashcards/review`

## 4. Event Streaming

**Applied to:** Learning and workload actions

**Implementation:** RabbitMQ event delivery and Redis Streams when Redis is available.

Events contain an event ID, event type, timestamp, and structured payload. Events are emitted for artifact generation, document upload, syllabus parsing, workload changes, blurting, Feynman evaluation, BKT updates, flashcard reviews, and burnout evaluation.

Relevant implementation:

- `backend/app/core/events.py`
- Redis stream: `learnsync:events`
- RabbitMQ exchange: `learnsync.events`

The Redis stream uses bounded retention. Long-term permanent archival would require an additional database sink or object-storage archive.

## 5. Distributed Rate Limiting

**Applied to:** Feynman evaluation and artifact generation

**Implementation:** Shared Redis per-user request limiting.

The limiter applies consistently across API instances. Requests exceeding the configured limit receive HTTP `429`. A process-local fallback is used when Redis is unavailable.

Relevant configuration:

- `LLM_RPM_LIMIT`
- `FEYNMAN_RPM_LIMIT`
- `backend/app/core/distributed.py`

## Supporting Reliability Features

- BKT mastery persistence through Supabase upsert.
- Document processing status tracking.
- Celery retry configuration with exponential backoff.
- Cache-key hashing to avoid oversized Redis keys.
- Correlated event IDs and timestamps.
- Graceful fallback when Redis or RabbitMQ is unavailable.

## Running the Distributed Services

From the repository root:

```powershell
docker compose -f docker-compose.distributed.yml up -d
```

Set these values in `backend/.env`:

```env
REDIS_URL=redis://localhost:6379/0
RABBITMQ_URL=amqp://guest:guest@localhost:5672/
ASYNC_DOCUMENT_PROCESSING=true
```

Start the worker:

```powershell
python -m celery -A backend.app.core.task_queue:celery_app worker --loglevel=INFO --pool=solo
```

## Demonstration Tests

```powershell
python -m pytest backend/tests/test_distributed_compliance_100.py backend/tests/test_distributed_infrastructure.py -v
```

The demonstration suite verifies all 5 distributed concepts:
1. **Asynchronous Queue**: Celery task enqueueing, status polling (`pending` -> `parsing` -> `indexed` / `failed`), and failure state capture.
2. **Distributed Cache**: SHA256 key hashing across 6 dimensions, TTL expiration, and cache-hit bypass.
3. **Distributed Locking**: Concurrency serialization on BKT & Flashcards, HTTP 409 conflict, and token-based safe Lua script release.
4. **Event Streaming**: Emission of all 9 learning/workload events to RabbitMQ and Redis Streams (`xadd`).
5. **Distributed Rate Limiting**: HTTP 429 backpressure on Feynman evaluation and Study Artifact generation.
6. **Zero Hardcoding**: Dynamic configurability via `Settings` and environment variables.

## Limitations and Future Improvements

The distributed modules are implemented for the intended project scope, but the following limitations remain:

- **Syllabus parsing is synchronous.** The syllabus endpoint returns staged folders and events immediately. Making it asynchronous would require a job-status and frontend polling workflow.
- **Redis Streams use bounded retention.** Events are available for replay while retained, but permanent archival would require a PostgreSQL sink or object-storage archive.
- **The rate limiter uses a shared fixed-window counter.** A true token-bucket algorithm could provide smoother traffic shaping.
- **Locking uses a Redis ownership lock on one Redis deployment.** A multi-node Redlock setup or PostgreSQL advisory locks could be added for higher availability requirements.
- **Fallback mode is process-local.** If Redis is unavailable, cache, lock, and rate-limit state is not shared between API instances.
- **Full production verification requires running external services.** End-to-end worker tests require Redis, RabbitMQ, Supabase, and the Celery worker to be available together.

These limitations do not prevent the five distributed concepts from being demonstrated; they identify production-hardening work beyond the current academic project scope.
