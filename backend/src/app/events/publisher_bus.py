"""
RabbitMQ publisher (best-effort).

We keep this separate from publisher.py to avoid importing kombu/amqp on app startup
if RabbitMQ isn't configured for local dev.
"""

from __future__ import annotations

import json
from typing import Any, Dict

from kombu import Connection, Exchange, Producer

from app.config.settings import settings


_exchange = Exchange("magicbox.events", type="topic", durable=True)


def publish_to_rabbitmq(routing_key: str, message: Dict[str, Any]) -> None:
    with Connection(settings.CELERY_BROKER_URL) as conn:
        producer = Producer(conn)
        producer.publish(
            message,
            exchange=_exchange,
            routing_key=routing_key,
            serializer="json",
            retry=True,
            retry_policy={"max_retries": 3, "interval_start": 0, "interval_step": 1, "interval_max": 3},
            declare=[_exchange],
            delivery_mode=2,
        )

