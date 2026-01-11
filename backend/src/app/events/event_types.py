"""
Event type constants for the internal event bus.

We use these to publish events to RabbitMQ AND persist them in DB (events table).
The DB model also defines enums; this module is a lightweight mirror for use outside ORM.
"""

from __future__ import annotations

from enum import Enum


class EventType(str, Enum):
    RUN_COMPLETED = "RUN_COMPLETED"
    ARTIFACT_CREATED = "ARTIFACT_CREATED"
    QUOTA_EXCEEDED = "QUOTA_EXCEEDED"
    POST_PUBLISHED = "POST_PUBLISHED"
    INVOICE_DUE = "INVOICE_DUE"
    USER_CREATED = "USER_CREATED"
    GDPR_DELETE_REQUESTED = "GDPR_DELETE_REQUESTED"
    OTHER = "OTHER"


