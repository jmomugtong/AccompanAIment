"""Celery application configuration."""

from celery import Celery

from src.config import settings

celery_app = Celery(
    "accompaniment",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_soft_time_limit=300,  # 5 minutes
    task_time_limit=600,  # 10 minutes
)

celery_app.autodiscover_tasks(["src.workers"])
