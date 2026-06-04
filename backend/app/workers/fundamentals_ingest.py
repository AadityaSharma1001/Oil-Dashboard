"""EIA fundamentals ingestion worker."""

import asyncio
from app.workers.celery_app import celery_app
from app.adapters import registry, register_all_adapters
from app.cache.redis_cache import RedisCache
import structlog

logger = structlog.get_logger()


@celery_app.task(name="app.workers.fundamentals_ingest.fetch_eia")
def fetch_eia():
    """Fetch EIA fundamental data and cache."""
    cache = RedisCache()
    loop = asyncio.new_event_loop()
    try:
        loop.run_until_complete(cache.connect())
        register_all_adapters()
        result = loop.run_until_complete(
            registry.fetch_with_fallback("fundamentals", {"type": "fundamentals"})
        )
        if result.data:
            loop.run_until_complete(cache.set("fundamentals:latest", {
                **result.data,
                "_status": result.status.value,
                "_source": result.source_name,
                "_fetched_at": result.fetched_at.isoformat(),
            }, ttl_seconds=3600))
            logger.info("fundamentals_ingest_success", status=result.status.value)
    except Exception as e:
        logger.error("fundamentals_ingest_error", error=str(e))
    finally:
        loop.run_until_complete(cache.close())
        loop.close()
