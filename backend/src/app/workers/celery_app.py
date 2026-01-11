"""
Celery worker compatibility module.

Some deployment tools expect celery app at app.workers.celery_app:celery_app.
We re-export the main celery_app here.
"""

from __future__ import annotations

from app.celery_app import celery_app

__all__ = ["celery_app"]

