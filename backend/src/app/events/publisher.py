"""
Event Publisher - publishes domain events.

Design:
- Persist events to DB for audit/retry (events table).
- Optionally publish to RabbitMQ (best-effort).
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Dict, Optional

from app.config.settings import settings
from app.db.session import SessionLocal
from app.db.models.event import Event, EventStatus, EventType
from app.middleware.request_context import get_context
from app.config.constants import CTX_TENANT_ID


def _default(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    return str(obj)


def publish_event(
    event_type: EventType,
    payload: Dict[str, Any],
    tenant_id: Optional[str] = None,
    extra_metadata: Optional[Dict[str, Any]] = None,
    publish_to_bus: bool = True,
) -> str:
    """
    Persist an event and optionally publish to the message bus.
    Returns event id.
    """
    db = SessionLocal()
    try:
        tenant = tenant_id or get_context(CTX_TENANT_ID)
        evt = Event(
            tenant_id=tenant,
            event_type=event_type,
            status=EventStatus.PENDING,
            payload=payload,
            extra_metadata=extra_metadata,
        )
        db.add(evt)
        db.commit()
        db.refresh(evt)

        if publish_to_bus:
            try:
                from app.events.publisher_bus import publish_to_rabbitmq
                publish_to_rabbitmq(
                    routing_key=event_type.value,
                    message={
                        "id": evt.id,
                        "tenant_id": evt.tenant_id,
                        "event_type": evt.event_type.value,
                        "payload": evt.payload,
                        "created_at": evt.created_at.isoformat() if evt.created_at else None,
                    },
                )
            except Exception:
                # best-effort; DB persistence is source of truth
                pass

        return evt.id
    finally:
        db.close()


