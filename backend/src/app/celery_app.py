"""
Celery Application Configuration.
Uses RabbitMQ as message broker.
"""
from celery import Celery
from app.config.settings import settings

# Create Celery app
celery_app = Celery(
    'magicbox',
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

# Configure Celery
celery_app.conf.update(
    timezone='UTC',
    enable_utc=True,
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    # RabbitMQ specific settings
    broker_connection_retry_on_startup=True,
    broker_connection_retry=True,
    broker_connection_max_retries=10,
)

# Auto-discover tasks
celery_app.autodiscover_tasks(['app.tasks'])
