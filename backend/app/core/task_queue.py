"""Document-processing task queue.

Celery is used when enabled and installed.  The queue remains import-safe in
development environments where a broker/worker is not running.
"""

from __future__ import annotations

import base64
import json
import logging
from typing import Any, Optional
from uuid import UUID

from backend.app.core.config import settings

logger = logging.getLogger(__name__)

try:
    from celery import Celery
except ImportError:  # pragma: no cover - optional dependency in local tests
    Celery = None


celery_app = (
    Celery("learnsync", broker=settings.RABBITMQ_URL, backend=settings.REDIS_URL)
    if Celery
    else None
)


def queue_document_processing(
    *,
    user_id: UUID,
    course_id: UUID,
    folder_id: Optional[UUID],
    file_name: str,
    file_bytes: bytes,
    mime_type: str,
    document_record: Optional[dict[str, Any]] = None,
) -> Optional[str]:
    """Queue a document job and return its task id, or None when unavailable."""
    if not settings.ASYNC_DOCUMENT_PROCESSING or celery_app is None:
        return None
    try:
        result = process_document_task.delay(
            str(user_id),
            str(course_id),
            str(folder_id) if folder_id else None,
            file_name,
            base64.b64encode(file_bytes).decode("ascii"),
            mime_type,
            json.dumps(document_record or {}),
        )
        return result.id
    except Exception as exc:
        logger.warning("Could not enqueue document processing job: %s", exc)
        return None


if celery_app:

    @celery_app.task(
        bind=True,
        name="learnsync.process_document",
        autoretry_for=(Exception,),
        retry_backoff=True,
        retry_kwargs={"max_retries": 3},
    )
    def process_document_task(
        self: Any,
        user_id: str,
        course_id: str,
        folder_id: Optional[str],
        file_name: str,
        encoded_file: str,
        mime_type: str,
        document_record_json: str,
    ) -> dict[str, Any]:
        from backend.app.services.document_processor import document_service

        document_record = json.loads(document_record_json)
        if document_record:
            record, chunks = document_service.process_existing_document(
                doc_record=document_record,
                user_id=UUID(user_id),
                course_id=UUID(course_id),
                folder_id=UUID(folder_id) if folder_id else None,
                file_name=file_name,
                file_bytes=base64.b64decode(encoded_file),
            )
        else:
            record, chunks = document_service.process_and_store_document(
            user_id=UUID(user_id),
            course_id=UUID(course_id),
            folder_id=UUID(folder_id) if folder_id else None,
            file_name=file_name,
            file_bytes=base64.b64decode(encoded_file),
            mime_type=mime_type,
            )
        return {"document_id": str(record.get("id")), "chunks_created": chunks}

else:

    def process_document_task(*args: Any, **kwargs: Any) -> None:
        return None
