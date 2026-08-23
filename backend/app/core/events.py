import json
import logging
from typing import Any, Dict, List, Optional
from backend.app.core.config import settings
from backend.app.schemas.workload import ModeTransitionEvent

logger = logging.getLogger(__name__)


class EventPublisher:
    """
    Publishes workload spike events to RabbitMQ with an in-memory queue fallback
    for offline resilience and deterministic unit testing.
    """
    EXCHANGE_NAME = "learnsync.events"
    ROUTING_KEY_WORKLOAD_SPIKE = "workload.spike.detected"

    def __init__(self, rabbitmq_url: Optional[str] = None):
        self.rabbitmq_url = rabbitmq_url or settings.RABBITMQ_URL
        self._memory_queue: List[Dict[str, Any]] = []

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


event_publisher = EventPublisher()
