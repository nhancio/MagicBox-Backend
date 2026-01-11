"""
Event Consumer - Celery tasks to process events stored in DB.

This is a production-safe approach:
- Source of truth is DB events table.
- Worker pulls pending events and processes them.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from app.celery_app import celery_app
from app.db.session import SessionLocal
from app.db.models.event import Event, EventStatus, EventType


@celery_app.task(name="events.process_pending", bind=True)
def process_pending_events(self, limit: int = 50):
    db = SessionLocal()
    try:
        events = (
            db.query(Event)
            .filter(Event.status == EventStatus.PENDING)
            .order_by(Event.created_at.asc())
            .limit(limit)
            .all()
        )

        processed = 0
        for evt in events:
            try:
                evt.status = EventStatus.PROCESSING
                db.commit()

                _dispatch_event(db, evt)

                evt.status = EventStatus.PROCESSED
                evt.processed_at = datetime.utcnow()
                evt.error_message = None
                db.commit()
                processed += 1
            except Exception as e:
                evt.status = EventStatus.FAILED
                evt.retry_count = (evt.retry_count or 0) + 1
                evt.error_message = str(e)
                db.commit()

        return {"success": True, "processed": processed}
    finally:
        db.close()


def _dispatch_event(db, evt: Event):
    """
    Add domain-specific handlers here.
    Keep it safe + idempotent.
    """
    if evt.event_type == EventType.POST_PUBLISHED:
        # Example: update analytics materialized views / send notifications / etc.
        return
    if evt.event_type == EventType.ARTIFACT_CREATED:
        return
    # default: no-op
    return

