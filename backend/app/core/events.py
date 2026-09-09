import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4
from backend.app.core.config import settings
from backend.app.schemas.workload import ModeTransitionEvent
from backend.app.core.distributed import distributed

logger = logging.getLogger(__name__)


class EventPublisher:
    """
    Publishes workload spike events to RabbitMQ with an in-memory queue fallback
    for offline resilience and deterministic unit testing.
    """
    ROUTING_KEY_WORKLOAD_SPIKE = "workload.spike.detected"

    def __init__(self, rabbitmq_url: Optional[str] = None):
        self.rabbitmq_url = rabbitmq_url or settings.RABBITMQ_URL
        self._memory_queue: List[Dict[str, Any]] = []

    @property
    def EXCHANGE_NAME(self) -> str:
        return settings.RABBITMQ_EXCHANGE

    def publish_workload_spike(self, event: ModeTransitionEvent) -> bool:
        """Publishes `workload.spike.detected` event."""
        payload = event.model_dump(mode="json")
        return self._publish(self.ROUTING_KEY_WORKLOAD_SPIKE, payload)

    def _publish(self, routing_key: str, payload: Dict[str, Any]) -> bool:
        try:
            import pika
            parameters = pika.URLParameters(self.rabbitmq_url)
            parameters.socket_timeout = 1.0
            connection = pika.BlockingConnection(parameters)
            channel = connection.channel()

            channel.exchange_declare(
                exchange=self.EXCHANGE_NAME,
                exchange_type="topic",
                durable=True,
            )

            channel.basic_publish(
                exchange=self.EXCHANGE_NAME,
                routing_key=routing_key,
                body=json.dumps(payload),
                properties=pika.BasicProperties(
                    content_type="application/json",
                    delivery_mode=2,  # Persistent
                ),
            )
            connection.close()
            logger.info("Published %s event to RabbitMQ successfully.", routing_key)
            return True

        except Exception as exc:
            # Fallback to in-memory event store for resilience
            self._memory_queue.append({
                "routing_key": routing_key,
                "payload": payload,
            })
            return False

    def get_in_memory_events(self) -> List[Dict[str, Any]]:
        return list(self._memory_queue)

    def clear_in_memory_events(self) -> None:
        self._memory_queue.clear()

    def publish_learning_event(self, event_type: str, payload: Dict[str, Any]) -> bool:
        """Publish a generic learning event to RabbitMQ and Redis Streams when available."""
        event = {
            "event_id": str(uuid4()),
            "event_type": event_type,
            "occurred_at": datetime.now(timezone.utc).isoformat(),
            "payload": payload,
        }
        published = self._publish(event_type, event)
        client = distributed.redis
        if client:
            try:
                client.xadd(settings.REDIS_STREAM_KEY, {"event": json.dumps(event)}, maxlen=settings.REDIS_STREAM_MAXLEN, approximate=True)
            except Exception as exc:
                logger.warning("Could not append learning event to Redis Stream: %s", exc)
        return published


event_publisher = EventPublisher()
