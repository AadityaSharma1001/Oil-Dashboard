"""Shipping data ingestion worker."""

import asyncio
from app.workers.celery_app import celery_app
from app.adapters import registry, register_all_adapters
from app.cache.redis_cache import RedisCache
import structlog

logger = structlog.get_logger()


@celery_app.task(name="app.workers.shipping_ingest.fetch_all")
def fetch_all():
    """Fetch all shipping data and cache."""
    cache = RedisCache()
    loop = asyncio.new_event_loop()
    try:
        loop.run_until_complete(cache.connect())
        register_all_adapters()
        for data_type in ["chokepoints", "floating_storage", "vlcc_rates", "fleet_utilization"]:
            result = loop.run_until_complete(
                registry.fetch_with_fallback("shipping_data", {"type": data_type})
            )
            if result.data:
                loop.run_until_complete(
                    cache.set(f"shipping:{data_type}", result.data, ttl_seconds=21600)
                )
        logger.info("shipping_ingest_success")
    except Exception as e:
        logger.error("shipping_ingest_error", error=str(e))
    finally:
        loop.run_until_complete(cache.close())
        loop.close()
