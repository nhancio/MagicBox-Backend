"""
AI Worker entrypoint.

Run (example):
  celery -A app.celery_app.celery_app worker -Q ai -l info
"""

from __future__ import annotations

from app.celery_app import celery_app

# Import tasks to ensure registration when worker starts
from app.tasks import publishing_tasks, notification_tasks  # noqa: F401
from app.events import consumer  # noqa: F401


__all__ = ["celery_app"]

