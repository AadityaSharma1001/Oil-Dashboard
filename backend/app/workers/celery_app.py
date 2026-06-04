"""Celery application configuration and beat schedule."""

from celery import Celery
from celery.schedules import crontab
from app.config import get_settings

settings = get_settings()

celery_app = Celery(
    "oil_desk",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=[
        "app.workers.price_ingest",
        "app.workers.fundamentals_ingest",
        "app.workers.hurricane_ingest",
        "app.workers.news_ingest",
        "app.workers.signal_compute",
        "app.workers.shipping_ingest",
    ],
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
)

celery_app.conf.beat_schedule = {
    "fetch-realtime-prices": {
        "task": "app.workers.price_ingest.fetch_realtime",
        "schedule": 30.0,
    },
    "fetch-forward-curves": {
        "task": "app.workers.price_ingest.fetch_forward_curves",
        "schedule": 60.0,
    },
    "compute-signals": {
        "task": "app.workers.signal_compute.recompute_all",
        "schedule": 300.0,
    },
    "fetch-hurricane-data": {
        "task": "app.workers.hurricane_ingest.fetch_active",
        "schedule": 300.0,
    },
    "fetch-news-and-sentiment": {
        "task": "app.workers.news_ingest.fetch_and_score",
        "schedule": 900.0,
    },
    "fetch-shipping-data": {
        "task": "app.workers.shipping_ingest.fetch_all",
        "schedule": 21600.0,
    },
    "fetch-eia-fundamentals": {
        "task": "app.workers.fundamentals_ingest.fetch_eia",
        "schedule": 3600.0,
    },
}
